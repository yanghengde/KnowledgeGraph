"""model changes persistence for the control plane."""
from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text


from .repository_support import _rows


class ModelChangesRepository:
    def list_schema_changes(self, profile_key: str, *, limit: int = 100) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            changes = _rows(
                connection.execute(
                    text(
                        """
                        SELECT change_id, profile_key, contract_key, base_version,
                               target_version, title, description, status,
                               compatibility, migration_strategy,
                               rollback_strategy, impact_summary, requested_by,
                               approved_by, created_at, updated_at, approved_at,
                               applied_at
                        FROM graphsync.schema_change_request
                        WHERE profile_key=:profile_key
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"profile_key": profile_key, "limit": min(max(limit, 1), 500)},
                )
            )
            if not changes:
                return []
            change_ids = [row["change_id"] for row in changes]
            items = _rows(
                connection.execute(
                    text(
                        """
                        SELECT item_id, change_id, sequence_no, operation,
                               field_key, before_state, after_state,
                               compatibility, migration_required,
                               backfill_required, dependency_count, notes,
                               created_at
                        FROM graphsync.schema_change_item
                        WHERE change_id = ANY(:change_ids)
                        ORDER BY change_id, sequence_no
                        """
                    ),
                    {"change_ids": change_ids},
                )
            )
            migrations = _rows(
                connection.execute(
                    text(
                        """
                        SELECT migration_run_id, change_id, status, preview_only,
                               started_at, finished_at, affected_rows, checkpoint,
                               verification, error
                        FROM graphsync.schema_migration_run
                        WHERE change_id = ANY(:change_ids)
                        ORDER BY change_id, started_at DESC
                        """
                    ),
                    {"change_ids": change_ids},
                )
            )
        for change in changes:
            change["items"] = [item for item in items if item["change_id"] == change["change_id"]]
            change["migrations"] = [
                item for item in migrations if item["change_id"] == change["change_id"]
            ]
        return changes


    def record_schema_change(
        self,
        *,
        profile_key: str,
        contract_key: str,
        title: str,
        description: str | None,
        migration_strategy: str | None,
        rollback_strategy: str | None,
        requested_by: str | None,
        analysis: dict[str, Any],
    ) -> dict[str, Any]:
        change_id = uuid.uuid4()
        status = "analysis_ready" if analysis["readyForReview"] else "draft"
        with self.engine.begin() as connection:
            current_version = connection.execute(
                text(
                    "SELECT version FROM graphsync.data_contract WHERE contract_key=:contract_key FOR UPDATE"
                ),
                {"contract_key": contract_key},
            ).scalar_one_or_none()
            if current_version is None:
                raise KeyError(contract_key)
            if int(current_version) != int(analysis["baseVersion"]):
                raise RuntimeError("Data contract changed while the schema request was being analyzed")
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.schema_change_request
                        (change_id, profile_key, contract_key, base_version,
                         target_version, title, description, status,
                         compatibility, migration_strategy, rollback_strategy,
                         impact_summary, requested_by)
                    VALUES
                        (:change_id, :profile_key, :contract_key, :base_version,
                         :target_version, :title, :description, :status,
                         :compatibility, :migration_strategy,
                         :rollback_strategy, CAST(:impact_summary AS jsonb),
                         :requested_by)
                    """
                ),
                {
                    "change_id": change_id,
                    "profile_key": profile_key,
                    "contract_key": contract_key,
                    "base_version": analysis["baseVersion"],
                    "target_version": analysis["targetVersion"],
                    "title": title,
                    "description": description,
                    "status": status,
                    "compatibility": analysis["compatibility"],
                    "migration_strategy": migration_strategy,
                    "rollback_strategy": rollback_strategy,
                    "impact_summary": json.dumps(
                        {
                            key: value
                            for key, value in analysis.items()
                            if key != "items"
                        },
                        ensure_ascii=False,
                    ),
                    "requested_by": requested_by,
                },
            )
            rows = []
            for item in analysis["items"]:
                rows.append(
                    {
                        "item_id": uuid.uuid4(),
                        "change_id": change_id,
                        "sequence_no": item["sequenceNo"],
                        "operation": item["operation"],
                        "field_key": item["fieldKey"],
                        "before_state": json.dumps(item["beforeState"], ensure_ascii=False, default=str) if item["beforeState"] else None,
                        "after_state": json.dumps(item["afterState"], ensure_ascii=False, default=str) if item["afterState"] else None,
                        "compatibility": item["compatibility"],
                        "migration_required": item["migrationRequired"],
                        "backfill_required": item["backfillRequired"],
                        "dependency_count": item["dependencyCount"],
                        "notes": item.get("notes"),
                    }
                )
            if rows:
                connection.execute(
                    text(
                        """
                        INSERT INTO graphsync.schema_change_item
                            (item_id, change_id, sequence_no, operation,
                             field_key, before_state, after_state,
                             compatibility, migration_required,
                             backfill_required, dependency_count, notes)
                        VALUES
                            (:item_id, :change_id, :sequence_no, :operation,
                             :field_key, CAST(:before_state AS jsonb),
                             CAST(:after_state AS jsonb), :compatibility,
                             :migration_required, :backfill_required,
                             :dependency_count, :notes)
                        """
                    ),
                    rows,
                )
        return {
            "changeId": str(change_id),
            "status": status,
            **analysis,
        }


    def review_schema_change(
        self,
        change_id: uuid.UUID,
        *,
        status: str,
        actor: str | None,
    ) -> dict[str, Any]:
        allowed = {"reviewed", "approved", "rejected"}
        if status not in allowed:
            raise ValueError(f"Unsupported schema review status: {status}")
        with self.engine.begin() as connection:
            existing = connection.execute(
                text(
                    """
                    SELECT status, impact_summary, migration_strategy,
                           rollback_strategy, compatibility
                    FROM graphsync.schema_change_request
                    WHERE change_id=:change_id FOR UPDATE
                    """
                ),
                {"change_id": change_id},
            ).mappings().one_or_none()
            if existing is None:
                raise KeyError(str(change_id))
            blockers = list((existing["impact_summary"] or {}).get("blockers") or [])
            if status in {"reviewed", "approved"} and blockers:
                raise ValueError(f"Schema change still has blockers: {blockers}")
            if status == "approved" and existing["status"] != "reviewed":
                raise ValueError("Schema change must be reviewed before approval")
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.schema_change_request
                    SET status=:status,
                        approved_by=CASE WHEN :status='approved' THEN :actor ELSE approved_by END,
                        approved_at=CASE WHEN :status='approved' THEN now() ELSE approved_at END
                    WHERE change_id=:change_id
                    RETURNING change_id, profile_key, contract_key,
                              base_version, target_version, title, status,
                              compatibility, impact_summary, requested_by,
                              approved_by, updated_at, approved_at
                    """
                ),
                {"change_id": change_id, "status": status, "actor": actor},
            ).mappings().one()
        return dict(row)


    def list_attribute_projections(self, profile_key: str) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            rows = _rows(
                connection.execute(
                    text(
                        """
                        SELECT projection.projection_key, projection.profile_key,
                               projection.target_contract_key, contract.class_name,
                               projection.title, projection.description,
                               projection.version, projection.status, projection.enabled,
                               projection.source_schema, projection.source_table,
                               projection.source_alias, projection.owner_mapping,
                               projection.join_plan, projection.row_filters,
                               projection.cardinality,
                               projection.multiple_match_policy,
                               projection.missing_policy, projection.collision_policy,
                               projection.order_by,
                               projection.preview_row_limit, projection.config,
                               projection.updated_at, projection.approved_by,
                               projection.approved_at,
                               preview.status AS preview_status,
                               preview.owner_rows AS preview_owner_rows,
                               preview.matched_rows AS preview_matched_rows,
                               preview.missing_owners AS preview_missing_owners,
                               preview.multiple_matches AS preview_multiple_matches,
                               preview.finished_at AS preview_at
                        FROM graphsync.attribute_projection_contract projection
                        JOIN graphsync.data_contract contract
                          ON contract.contract_key=projection.target_contract_key
                        LEFT JOIN LATERAL (
                            SELECT * FROM graphsync.attribute_projection_preview item
                            WHERE item.projection_key=projection.projection_key
                              AND item.projection_version=projection.version
                            ORDER BY item.started_at DESC LIMIT 1
                        ) preview ON true
                        WHERE projection.profile_key=:profile_key
                        ORDER BY contract.class_name, projection.title
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
            if not rows:
                return []
            keys = [row["projection_key"] for row in rows]
            fields = _rows(
                connection.execute(
                    text(
                        """
                        SELECT projection_key, field_key, source_path,
                               target_field, data_type, required,
                               ontology_property, lifecycle_status,
                               ordinal_position, config, updated_at
                        FROM graphsync.attribute_projection_field
                        WHERE projection_key=ANY(:keys)
                        ORDER BY projection_key, ordinal_position, field_key
                        """
                    ),
                    {"keys": keys},
                )
            )
        for row in rows:
            row["fields"] = [item for item in fields if item["projection_key"] == row["projection_key"]]
        return rows


    def attribute_projection(self, projection_key: str) -> dict[str, Any]:
        with self.engine.connect() as connection:
            projection = connection.execute(
                text(
                    """
                    SELECT projection_key, profile_key, target_contract_key,
                           title, description, version, status, enabled,
                           source_schema, source_table, source_alias,
                           owner_mapping, join_plan, row_filters, cardinality,
                           multiple_match_policy, missing_policy, collision_policy,
                           order_by,
                           preview_row_limit, config, updated_at, approved_by,
                           approved_at
                    FROM graphsync.attribute_projection_contract
                    WHERE projection_key=:projection_key
                    """
                ),
                {"projection_key": projection_key},
            ).mappings().one_or_none()
            if projection is None:
                raise KeyError(projection_key)
            fields = _rows(
                connection.execute(
                    text(
                        """
                        SELECT projection_key, field_key, source_path,
                               target_field, data_type, required,
                               ontology_property, lifecycle_status,
                               ordinal_position, config, updated_at
                        FROM graphsync.attribute_projection_field
                        WHERE projection_key=:projection_key
                        ORDER BY ordinal_position, field_key
                        """
                    ),
                    {"projection_key": projection_key},
                )
            )
            target = connection.execute(
                text(
                    """
                    SELECT contract_key, profile_key, class_name, version,
                           status, source_schema, source_table,
                           primary_key_columns, business_key_columns,
                           selected_columns, required_columns,
                           freshness_column, config
                    FROM graphsync.data_contract
                    WHERE contract_key=:contract_key
                    """
                ),
                {"contract_key": projection["target_contract_key"]},
            ).mappings().one()
        result = dict(projection)
        result["fields"] = fields
        result["targetContract"] = dict(target)
        return result


    def upsert_attribute_projection(
        self,
        *,
        projection_key: str,
        profile_key: str,
        target_contract_key: str,
        title: str,
        description: str | None,
        source_schema: str,
        source_table: str,
        source_alias: str,
        owner_mapping: list[dict[str, Any]],
        join_plan: list[dict[str, Any]],
        row_filters: list[dict[str, Any]],
        cardinality: str,
        multiple_match_policy: str,
        missing_policy: str,
        collision_policy: str,
        order_by: list[dict[str, Any]],
        preview_row_limit: int,
        enabled: bool,
        fields: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            target = connection.execute(
                text("SELECT class_name FROM graphsync.data_contract WHERE contract_key=:contract_key AND profile_key=:profile_key"),
                {"contract_key": target_contract_key, "profile_key": profile_key},
            ).mappings().one_or_none()
            if target is None:
                raise ValueError("Target data contract does not belong to this graph profile")
            existing = connection.execute(
                text("SELECT version FROM graphsync.attribute_projection_contract WHERE projection_key=:projection_key FOR UPDATE"),
                {"projection_key": projection_key},
            ).scalar_one_or_none()
            version = int(existing or 0) + 1
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.attribute_projection_contract
                        (projection_key, profile_key, target_contract_key,
                         title, description, version, status, enabled,
                         source_schema, source_table, source_alias,
                         owner_mapping, join_plan, row_filters, cardinality,
                         multiple_match_policy, missing_policy, collision_policy,
                         order_by,
                         preview_row_limit, config)
                    VALUES (:projection_key, :profile_key, :target_contract_key,
                            :title, :description, :version, 'draft', :enabled,
                            :source_schema, :source_table, :source_alias,
                            CAST(:owner_mapping AS jsonb), CAST(:join_plan AS jsonb),
                            CAST(:row_filters AS jsonb), :cardinality,
                            :multiple_match_policy, :missing_policy, :collision_policy,
                            CAST(:order_by AS jsonb), :preview_row_limit,
                            CAST(:config AS jsonb))
                    ON CONFLICT (projection_key) DO UPDATE SET
                        target_contract_key=EXCLUDED.target_contract_key,
                        title=EXCLUDED.title, description=EXCLUDED.description,
                        version=EXCLUDED.version, status='draft',
                        enabled=EXCLUDED.enabled,
                        source_schema=EXCLUDED.source_schema,
                        source_table=EXCLUDED.source_table,
                        source_alias=EXCLUDED.source_alias,
                        owner_mapping=EXCLUDED.owner_mapping,
                        join_plan=EXCLUDED.join_plan,
                        row_filters=EXCLUDED.row_filters,
                        cardinality=EXCLUDED.cardinality,
                        multiple_match_policy=EXCLUDED.multiple_match_policy,
                        missing_policy=EXCLUDED.missing_policy,
                        collision_policy=EXCLUDED.collision_policy,
                        order_by=EXCLUDED.order_by,
                        preview_row_limit=EXCLUDED.preview_row_limit,
                        config=EXCLUDED.config, approved_by=NULL,
                        approved_at=NULL
                    """
                ),
                {
                    "projection_key": projection_key,
                    "profile_key": profile_key,
                    "target_contract_key": target_contract_key,
                    "title": title,
                    "description": description,
                    "version": version,
                    "enabled": enabled,
                    "source_schema": source_schema,
                    "source_table": source_table,
                    "source_alias": source_alias,
                    "owner_mapping": json.dumps(owner_mapping, ensure_ascii=False),
                    "join_plan": json.dumps(join_plan, ensure_ascii=False),
                    "row_filters": json.dumps(row_filters, ensure_ascii=False),
                    "cardinality": cardinality,
                    "multiple_match_policy": multiple_match_policy,
                    "missing_policy": missing_policy,
                    "collision_policy": collision_policy,
                    "order_by": json.dumps(order_by, ensure_ascii=False),
                    "preview_row_limit": preview_row_limit,
                    "config": json.dumps(config or {}, ensure_ascii=False),
                },
            )
            connection.execute(
                text("DELETE FROM graphsync.attribute_projection_field WHERE projection_key=:projection_key"),
                {"projection_key": projection_key},
            )
            connection.execute(
                text("UPDATE graphsync.asset_dependency SET active=false, last_seen_at=now() WHERE profile_key=:profile_key AND upstream_type IN ('attribute_projection','attribute_projection_field') AND (upstream_key=:projection_key OR metadata->>'projectionKey'=:projection_key)"),
                {"profile_key": profile_key, "projection_key": projection_key},
            )
            for index, field in enumerate(fields, start=1):
                connection.execute(
                    text(
                        """
                        INSERT INTO graphsync.attribute_projection_field
                            (projection_key, field_key, source_path,
                             target_field, data_type, required,
                             ontology_property, lifecycle_status,
                             ordinal_position, config)
                        VALUES (:projection_key, :field_key, :source_path,
                                :target_field, :data_type, :required,
                                :ontology_property, :lifecycle_status,
                                :ordinal_position, CAST(:config AS jsonb))
                        """
                    ),
                    {
                        "projection_key": projection_key,
                        "field_key": field["field_key"],
                        "source_path": field["source_path"],
                        "target_field": field["target_field"],
                        "data_type": field.get("data_type", "String"),
                        "required": bool(field.get("required")),
                        "ontology_property": field.get("ontology_property"),
                        "lifecycle_status": field.get("lifecycle_status", "active"),
                        "ordinal_position": int(field.get("ordinal_position") or index * 10),
                        "config": json.dumps(field.get("config") or {}, ensure_ascii=False),
                    },
                )
                dependency_key = f"graphsync.object_version.properties.{field['target_field']}"
                connection.execute(
                    text(
                        """
                        INSERT INTO graphsync.asset_dependency
                            (dependency_id, profile_key, upstream_type,
                             upstream_key, downstream_type, downstream_key,
                             dependency_kind, discovered_by, metadata)
                        VALUES (:id, :profile_key, 'attribute_projection_field',
                                :field_key, 'curated_column', :downstream,
                                'hard', 'compiler', CAST(:metadata AS jsonb))
                        ON CONFLICT (profile_key, upstream_type, upstream_key,
                                     downstream_type, downstream_key)
                        DO UPDATE SET active=true, last_seen_at=now(),
                                      metadata=EXCLUDED.metadata
                        """
                    ),
                    {
                        "id": uuid.uuid4(), "profile_key": profile_key,
                        "field_key": field["field_key"],
                        "downstream": dependency_key,
                        "metadata": json.dumps({"projectionKey": projection_key, "targetContractKey": target_contract_key}),
                    },
                )
        return self.attribute_projection(projection_key)


    def review_attribute_projection(
        self,
        projection_key: str,
        *,
        status: str,
        actor: str | None,
    ) -> dict[str, Any]:
        if status not in {"reviewed", "approved", "retired"}:
            raise ValueError(f"Unsupported projection review status: {status}")
        with self.engine.begin() as connection:
            projection = connection.execute(
                text("SELECT status, version FROM graphsync.attribute_projection_contract WHERE projection_key=:key FOR UPDATE"),
                {"key": projection_key},
            ).mappings().one_or_none()
            if projection is None:
                raise KeyError(projection_key)
            if status == "reviewed" and projection["status"] != "draft":
                raise ValueError("Only a draft projection can be reviewed")
            if status == "approved" and projection["status"] != "reviewed":
                raise ValueError("Projection must be reviewed before approval")
            if status in {"reviewed", "approved"}:
                preview = connection.execute(
                    text("SELECT status FROM graphsync.attribute_projection_preview WHERE projection_key=:key AND projection_version=:version ORDER BY started_at DESC LIMIT 1"),
                    {"key": projection_key, "version": projection["version"]},
                ).scalar_one_or_none()
                if preview != "succeeded":
                    raise ValueError("Projection requires a successful source preview before review or approval")
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.attribute_projection_contract
                    SET status=:status,
                        approved_by=CASE WHEN :status='approved' THEN :actor ELSE approved_by END,
                        approved_at=CASE WHEN :status='approved' THEN now() ELSE approved_at END
                    WHERE projection_key=:key
                    RETURNING projection_key, status, version,
                              approved_by, approved_at, updated_at
                    """
                ),
                {"key": projection_key, "status": status, "actor": actor},
            ).mappings().one()
        return dict(row)

