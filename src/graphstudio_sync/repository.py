"""Data access for the Graph Studio synchronization control plane."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import text

from .config import PROJECT_ROOT, SyncSettings
from .database import control_engine


PLAN_FILE = PROJECT_ROOT / "outputs" / "graphstudio" / "full_sync_plan.json"


def _rows(result) -> list[dict[str, Any]]:
    return [dict(row) for row in result.mappings().all()]


class ControlPlaneRepository:
    def __init__(self, settings: SyncSettings):
        self.settings = settings
        self.engine = control_engine(settings)

    def overview(self) -> dict[str, Any]:
        with self.engine.connect() as connection:
            summary = dict(
                connection.execute(text("SELECT * FROM graphsync.dashboard_summary")).mappings().one()
            )
            connections = _rows(
                connection.execute(
                    text(
                        """
                        SELECT connection_key, kind, display_name, endpoint, database_name,
                               enabled, status, last_tested_at, last_error
                        FROM graphsync.connection_profile ORDER BY connection_key
                        """
                    )
                )
            )
            jobs = _rows(
                connection.execute(
                    text(
                        """
                        SELECT j.job_name, j.title, j.mode, j.schedule, j.timezone, j.enabled,
                               r.status AS last_status, r.started_at AS last_started_at,
                               r.finished_at AS last_finished_at, r.row_count, r.triple_count
                        FROM graphsync.sync_job j
                        LEFT JOIN graphsync.latest_job_run r ON r.job_name = j.job_name
                        ORDER BY j.job_name
                        """
                    )
                )
            )
            recent_runs = _rows(
                connection.execute(
                    text(
                        """
                        SELECT run_id, job_name, status, trigger_type, started_at, finished_at,
                               row_count, triple_count
                        FROM graphsync.sync_run ORDER BY started_at DESC LIMIT 8
                        """
                    )
                )
            )
        return {"summary": summary, "connections": connections, "jobs": jobs, "recentRuns": recent_runs}

    def list_connections(self) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            return _rows(
                connection.execute(
                    text(
                        """
                        SELECT connection_key, kind, display_name, endpoint, database_name,
                               username, secret_ref, enabled, status, last_tested_at,
                               last_error, config, updated_at
                        FROM graphsync.connection_profile ORDER BY connection_key
                        """
                    )
                )
            )

    def update_connection_status(self, key: str, *, status: str, error: str | None = None) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE graphsync.connection_profile
                    SET status=:status, last_error=:error, last_tested_at=now()
                    WHERE connection_key=:key
                    """
                ),
                {"key": key, "status": status, "error": error},
            )

    def update_connection(
        self,
        key: str,
        *,
        kind: str,
        display_name: str,
        endpoint: str,
        database_name: str | None,
        username: str | None,
        enabled: bool,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.connection_profile
                    SET kind=:kind, display_name=:display_name, endpoint=:endpoint,
                        database_name=:database_name, username=:username,
                        enabled=:enabled, config=CAST(:config AS jsonb),
                        status=CASE WHEN :enabled THEN 'unknown' ELSE 'disabled' END,
                        last_error=NULL
                    WHERE connection_key=:key
                    RETURNING connection_key, kind, display_name, endpoint, database_name,
                              username, secret_ref, enabled, status, config, updated_at
                    """
                ),
                {
                    "key": key,
                    "kind": kind,
                    "display_name": display_name,
                    "endpoint": endpoint,
                    "database_name": database_name,
                    "username": username,
                    "enabled": enabled,
                    "config": json.dumps(config, ensure_ascii=False),
                },
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(key)
        return dict(row)

    def list_navigation(self, *, include_disabled: bool = False) -> list[dict[str, Any]]:
        predicate = "" if include_disabled else "WHERE enabled"
        with self.engine.connect() as connection:
            return _rows(
                connection.execute(
                    text(
                        f"""
                        SELECT menu_key, parent_key, label_zh, label_en, route, icon,
                               sort_order, enabled, capability
                        FROM graphsync.menu_item {predicate}
                        ORDER BY sort_order, menu_key
                        """
                    )
                )
            )

    def update_navigation(
        self,
        key: str,
        *,
        label_zh: str,
        label_en: str,
        sort_order: int,
        enabled: bool,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.menu_item
                    SET label_zh=:label_zh, label_en=:label_en,
                        sort_order=:sort_order, enabled=:enabled
                    WHERE menu_key=:key
                    RETURNING menu_key, label_zh, label_en, route, icon, sort_order, enabled
                    """
                ),
                {
                    "key": key,
                    "label_zh": label_zh,
                    "label_en": label_en,
                    "sort_order": sort_order,
                    "enabled": enabled,
                },
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(key)
        return dict(row)

    def list_jobs(self) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            jobs = _rows(
                connection.execute(
                    text(
                        """
                        SELECT job_name, title, description, graphmart_uri, mode, schedule,
                               timezone, enabled, retention_success, config, updated_at
                        FROM graphsync.sync_job ORDER BY job_name
                        """
                    )
                )
            )
            scopes = _rows(
                connection.execute(
                    text(
                        """
                        SELECT job_name, scope_key, class_pattern, layer_title,
                               enabled, sort_order, config
                        FROM graphsync.sync_scope ORDER BY job_name, sort_order
                        """
                    )
                )
            )
        for job in jobs:
            job["scopes"] = [scope for scope in scopes if scope["job_name"] == job["job_name"]]
        return jobs

    def update_job(
        self,
        name: str,
        *,
        title: str,
        mode: str,
        schedule: str | None,
        timezone: str,
        enabled: bool,
        retention_success: int,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.sync_job
                    SET title=:title, mode=:mode, schedule=:schedule, timezone=:timezone,
                        enabled=:enabled, retention_success=:retention_success
                    WHERE job_name=:name
                    RETURNING job_name, title, mode, schedule, timezone, enabled, retention_success
                    """
                ),
                locals(),
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(name)
        return dict(row)

    def list_table_policies(self, job_name: str) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            job_exists = connection.execute(
                text("SELECT EXISTS(SELECT 1 FROM graphsync.sync_job WHERE job_name=:job_name)"),
                {"job_name": job_name},
            ).scalar_one()
            if not job_exists:
                raise KeyError(job_name)
            settings = {
                row["setting_key"]: row["value"]
                for row in connection.execute(
                    text(
                        """
                        SELECT setting_key, value FROM graphsync.app_setting
                        WHERE setting_key IN (
                            'sync.snapshot_row_threshold', 'sync.default_batch_rows',
                            'sync.target_shard_bytes'
                        )
                        """
                    )
                ).mappings()
            }
            rows = _rows(
                connection.execute(
                    text(
                        """
                        SELECT mapping.class_name, mapping.physical_schema,
                               mapping.physical_table, mapping.approximate_rows,
                               policy.strategy, policy.watermark_column,
                               policy.partition_column, policy.batch_rows,
                               policy.target_shard_bytes, policy.hot_window_days,
                               policy.enabled, policy.config, policy.updated_at,
                               (policy.class_name IS NOT NULL) AS explicitly_configured
                        FROM graphsync.current_class_mapping mapping
                        LEFT JOIN graphsync.table_sync_policy policy
                          ON policy.job_name=:job_name
                         AND policy.class_name=mapping.class_name
                        WHERE mapping.mapping_status='resolved'
                        ORDER BY mapping.approximate_rows DESC, mapping.class_name
                        """
                    ),
                    {"job_name": job_name},
                )
            )
        threshold = int(settings.get("sync.snapshot_row_threshold", 5_000_000))
        default_batch = int(settings.get("sync.default_batch_rows", 10_000))
        default_shard_bytes = int(settings.get("sync.target_shard_bytes", 67_108_864))
        for row in rows:
            approximate_rows = int(row.get("approximate_rows") or 0)
            high_volume = approximate_rows > threshold
            name = str(row["class_name"]).casefold()
            recommended = (
                "append_only"
                if high_volume and any(token in name for token in ("history", "log", "event", "audit"))
                else "cdc" if high_volume else "snapshot"
            )
            row["recommended_strategy"] = recommended
            row["requires_review"] = high_volume and not row["explicitly_configured"]
            row["effective_strategy"] = row["strategy"] or (None if high_volume else "snapshot")
            row["batch_rows"] = int(row["batch_rows"] or default_batch)
            row["target_shard_bytes"] = int(row["target_shard_bytes"] or default_shard_bytes)
            row["enabled"] = True if row["enabled"] is None else row["enabled"]
        return rows

    def upsert_table_policy(
        self,
        job_name: str,
        class_name: str,
        *,
        strategy: str,
        watermark_column: str | None,
        partition_column: str | None,
        batch_rows: int,
        target_shard_bytes: int,
        hot_window_days: int | None,
        enabled: bool,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            mapping = connection.execute(
                text(
                    """
                    SELECT physical_schema, physical_table
                    FROM graphsync.current_class_mapping
                    WHERE class_name=:class_name AND mapping_status='resolved'
                    """
                ),
                {"class_name": class_name},
            ).mappings().one_or_none()
            if mapping is None:
                raise KeyError(class_name)
            row = connection.execute(
                text(
                    """
                    INSERT INTO graphsync.table_sync_policy
                        (job_name, class_name, physical_schema, physical_table,
                         strategy, watermark_column, partition_column, batch_rows,
                         target_shard_bytes, hot_window_days, enabled, config)
                    VALUES
                        (:job_name, :class_name, :physical_schema, :physical_table,
                         :strategy, :watermark_column, :partition_column, :batch_rows,
                         :target_shard_bytes, :hot_window_days, :enabled,
                         CAST(:config AS jsonb))
                    ON CONFLICT (job_name, class_name) DO UPDATE SET
                        physical_schema=EXCLUDED.physical_schema,
                        physical_table=EXCLUDED.physical_table,
                        strategy=EXCLUDED.strategy,
                        watermark_column=EXCLUDED.watermark_column,
                        partition_column=EXCLUDED.partition_column,
                        batch_rows=EXCLUDED.batch_rows,
                        target_shard_bytes=EXCLUDED.target_shard_bytes,
                        hot_window_days=EXCLUDED.hot_window_days,
                        enabled=EXCLUDED.enabled,
                        config=EXCLUDED.config
                    RETURNING job_name, class_name, physical_schema, physical_table,
                              strategy, watermark_column, partition_column, batch_rows,
                              target_shard_bytes, hot_window_days, enabled, config, updated_at
                    """
                ),
                {
                    "job_name": job_name,
                    "class_name": class_name,
                    "physical_schema": mapping["physical_schema"],
                    "physical_table": mapping["physical_table"],
                    "strategy": strategy,
                    "watermark_column": watermark_column,
                    "partition_column": partition_column,
                    "batch_rows": batch_rows,
                    "target_shard_bytes": target_shard_bytes,
                    "hot_window_days": hot_window_days,
                    "enabled": enabled,
                    "config": json.dumps(config, ensure_ascii=False),
                },
            ).mappings().one()
        return dict(row)

    def record_source_capabilities(
        self,
        payload: dict[str, Any],
        *,
        connection_key: str = "camstar-source",
    ) -> dict[str, Any]:
        snapshot_id = uuid.uuid4()
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO graphsync.source_capability_snapshot
                        (snapshot_id, connection_key, source_kind, captured_at,
                         source_position, capabilities, table_capabilities, success)
                    VALUES
                        (:snapshot_id, :connection_key, :source_kind,
                         CAST(:captured_at AS timestamptz), CAST(:source_position AS jsonb),
                         CAST(:capabilities AS jsonb), CAST(:tables AS jsonb), true)
                    RETURNING snapshot_id, connection_key, source_kind, captured_at,
                              source_position, capabilities, table_capabilities, success
                    """
                ),
                {
                    "snapshot_id": snapshot_id,
                    "connection_key": connection_key,
                    "source_kind": payload["sourceKind"],
                    "captured_at": payload["capturedAt"],
                    "source_position": json.dumps(payload["sourcePosition"], ensure_ascii=False),
                    "capabilities": json.dumps(payload["capabilities"], ensure_ascii=False),
                    "tables": json.dumps(payload["tables"], ensure_ascii=False),
                },
            ).mappings().one()
        return dict(row)

    def latest_source_capabilities(
        self,
        *,
        connection_key: str = "camstar-source",
    ) -> dict[str, Any] | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT snapshot_id, connection_key, source_kind, captured_at,
                           source_position, capabilities, table_capabilities, success, error
                    FROM graphsync.source_capability_snapshot
                    WHERE connection_key=:connection_key
                    ORDER BY captured_at DESC LIMIT 1
                    """
                ),
                {"connection_key": connection_key},
            ).mappings().one_or_none()
        if row is None:
            return None
        result = dict(row)
        result["tables"] = result.pop("table_capabilities")
        result["sourceKind"] = result.pop("source_kind")
        result["sourcePosition"] = result.pop("source_position")
        result["capturedAt"] = result.pop("captured_at")
        return result

    def checkpoints_by_partition(self, job_name: str) -> dict[str, dict[str, Any]]:
        with self.engine.connect() as connection:
            rows = _rows(
                connection.execute(
                    text(
                        """
                        SELECT partition_key, committed_watermark, source_schema_hash,
                               committed_run_id, committed_at
                        FROM graphsync.checkpoint
                        WHERE job_name=:job_name
                        """
                    ),
                    {"job_name": job_name},
                )
            )
        return {row["partition_key"]: row for row in rows}

    def record_incremental_windows(
        self,
        job_name: str,
        capability_snapshot_id: uuid.UUID | str,
        windows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        recorded: list[dict[str, Any]] = []
        with self.engine.begin() as connection:
            for window in windows:
                row = connection.execute(
                    text(
                        """
                        INSERT INTO graphsync.incremental_window
                            (window_id, job_name, class_name, strategy, adapter, status,
                             lower_bound, upper_bound, capability_snapshot_id, metadata)
                        VALUES
                            (:window_id, :job_name, :class_name, :strategy, :adapter, :status,
                             CAST(:lower_bound AS jsonb), CAST(:upper_bound AS jsonb),
                             :capability_snapshot_id, CAST(:metadata AS jsonb))
                        ON CONFLICT (job_name, class_name, upper_bound) DO UPDATE SET
                            strategy=EXCLUDED.strategy,
                            adapter=EXCLUDED.adapter,
                            status=EXCLUDED.status,
                            lower_bound=EXCLUDED.lower_bound,
                            capability_snapshot_id=EXCLUDED.capability_snapshot_id,
                            metadata=EXCLUDED.metadata
                        RETURNING window_id, job_name, class_name, strategy, adapter,
                                  status, lower_bound, upper_bound, metadata, created_at
                        """
                    ),
                    {
                        "window_id": uuid.uuid4(),
                        "job_name": job_name,
                        "class_name": window["class_name"],
                        "strategy": window["strategy"],
                        "adapter": window["adapter"],
                        "status": window["status"],
                        "lower_bound": json.dumps(window.get("lower_bound"), ensure_ascii=False, default=str),
                        "upper_bound": json.dumps(window["upper_bound"], ensure_ascii=False, default=str),
                        "capability_snapshot_id": capability_snapshot_id,
                        "metadata": json.dumps(window.get("metadata") or {}, ensure_ascii=False),
                    },
                ).mappings().one()
                recorded.append(dict(row))
        return recorded

    def latest_incremental_windows(self, job_name: str) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            return _rows(
                connection.execute(
                    text(
                        """
                        SELECT DISTINCT ON (class_name)
                               window_id, job_name, class_name, strategy, adapter, status,
                               lower_bound, upper_bound, capability_snapshot_id, run_id,
                               row_count, tombstone_count, error, metadata, created_at, updated_at
                        FROM graphsync.incremental_window
                        WHERE job_name=:job_name
                        ORDER BY class_name, created_at DESC
                        """
                    ),
                    {"job_name": job_name},
                )
            )

    def list_runs(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            return _rows(
                connection.execute(
                    text(
                        """
                        SELECT run_id, job_name, status, trigger_type, started_at, finished_at,
                               row_count, triple_count, ontology_hash, source_schema_hash,
                               manifest_hash, error, metrics
                        FROM graphsync.sync_run ORDER BY started_at DESC LIMIT :limit
                        """
                    ),
                    {"limit": min(max(limit, 1), 500)},
                )
            )

    def list_mapping_overrides(self) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            return _rows(
                connection.execute(
                    text(
                        """
                        SELECT class_name, property_name, physical_schema, physical_table,
                               physical_column, target_class, mapping_kind, expression,
                               enabled, notes, updated_at
                        FROM graphsync.mapping_override ORDER BY class_name, property_name
                        """
                    )
                )
            )

    def upsert_property_override(
        self,
        *,
        class_name: str,
        property_name: str,
        physical_table: str,
        physical_column: str | None,
        mapping_kind: str,
        expression: str | None,
        notes: str | None,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO graphsync.mapping_override
                        (class_name, property_name, physical_table, physical_column,
                         mapping_kind, expression, notes)
                    VALUES
                        (:class_name, :property_name, :physical_table, :physical_column,
                         :mapping_kind, :expression, :notes)
                    ON CONFLICT (class_name, property_name) DO UPDATE SET
                        physical_table=EXCLUDED.physical_table,
                        physical_column=EXCLUDED.physical_column,
                        mapping_kind=EXCLUDED.mapping_kind,
                        expression=EXCLUDED.expression,
                        notes=EXCLUDED.notes,
                        enabled=true
                    RETURNING class_name, property_name, physical_table, physical_column,
                              mapping_kind, expression, enabled, notes, updated_at
                    """
                ),
                locals(),
            ).mappings().one()
        return dict(row)

    def upsert_relationship_override(
        self,
        *,
        source_class: str,
        relationship_name: str,
        target_class: str,
        source_property: str,
        notes: str | None,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO graphsync.relationship_override
                        (source_class, relationship_name, target_class, source_property, notes)
                    VALUES
                        (:source_class, :relationship_name, :target_class, :source_property, :notes)
                    ON CONFLICT (source_class, relationship_name, target_class) DO UPDATE SET
                        source_property=EXCLUDED.source_property,
                        notes=EXCLUDED.notes,
                        enabled=true
                    RETURNING source_class, relationship_name, target_class,
                              source_property, enabled, notes, updated_at
                    """
                ),
                locals(),
            ).mappings().one()
        return dict(row)

    def inventory(self) -> dict[str, Any]:
        if not PLAN_FILE.exists():
            return {"available": False}
        return {"available": True, **json.loads(PLAN_FILE.read_text(encoding="utf-8"))}

    def mapping_catalog(self) -> dict[str, Any]:
        with self.engine.connect() as connection:
            snapshot = connection.execute(
                text("SELECT * FROM graphsync.current_catalog_snapshot")
            ).mappings().one_or_none()
            if snapshot is None:
                return {"available": False, "unresolvedProperties": [], "relationshipStatus": {}}
            unresolved = _rows(
                connection.execute(
                    text(
                        """
                        SELECT class_name AS "className", property_name AS "propertyName",
                               data_type AS "dataType", source_field_id AS "sourceFieldId",
                               physical_table AS "physicalTable", mapping_status AS "mappingStatus"
                        FROM graphsync.current_property_mapping
                        WHERE mapping_status = 'unresolved'
                        ORDER BY class_name, property_name
                        """
                    )
                )
            )
            relationship_status = {
                row["mapping_status"]: row["count"]
                for row in connection.execute(
                    text(
                        """
                        SELECT mapping_status, count(*) AS count
                        FROM graphsync.current_relationship_mapping GROUP BY mapping_status
                        """
                    )
                ).mappings()
            }
            relationship_review = _rows(
                connection.execute(
                    text(
                        """
                        SELECT source_class AS "sourceClass",
                               relationship_name AS "relationshipName",
                               target_class AS "targetClass", cardinality,
                               candidate_properties AS "candidateProperties",
                               mapping_status AS "mappingStatus",
                               candidate_count AS "candidateCount"
                        FROM graphsync.current_relationship_mapping
                        WHERE mapping_status <> 'resolved'
                        ORDER BY mapping_status, source_class, relationship_name, target_class
                        """
                    )
                )
            )
        return {
            "available": True,
            "snapshot": dict(snapshot),
            "unresolvedProperties": unresolved,
            "relationshipStatus": relationship_status,
            "relationshipReview": relationship_review,
        }

    def list_settings(self) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            return _rows(
                connection.execute(
                    text(
                        """
                        SELECT setting_key, value, description, editable, updated_at
                        FROM graphsync.app_setting ORDER BY setting_key
                        """
                    )
                )
            )

    def list_graph_profiles(self) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            profiles = _rows(
                connection.execute(
                    text(
                        """
                        SELECT profile_key, title, description, job_name, enabled,
                               max_depth, max_context_nodes_per_seed,
                               max_total_nodes_per_run, config, updated_at
                        FROM graphsync.graph_profile
                        ORDER BY profile_key
                        """
                    )
                )
            )
            counts = _rows(
                connection.execute(
                    text(
                        """
                        SELECT profile_key, role, count(*) AS count
                        FROM graphsync.profile_class
                        WHERE enabled
                        GROUP BY profile_key, role
                        """
                    )
                )
            )
        for profile in profiles:
            profile["class_counts"] = {
                row["role"]: row["count"]
                for row in counts
                if row["profile_key"] == profile["profile_key"]
            }
        return profiles

    def graph_profile(self, profile_key: str) -> dict[str, Any]:
        with self.engine.connect() as connection:
            profile = connection.execute(
                text(
                    """
                    SELECT profile_key, title, description, job_name, enabled,
                           max_depth, max_context_nodes_per_seed,
                           max_total_nodes_per_run, config, updated_at
                    FROM graphsync.graph_profile WHERE profile_key=:profile_key
                    """
                ),
                {"profile_key": profile_key},
            ).mappings().one_or_none()
            if profile is None:
                raise KeyError(profile_key)
            classes = _rows(
                connection.execute(
                    text(
                        """
                        SELECT configured.profile_key, configured.class_name,
                               configured.role, configured.orphan_policy,
                               configured.seed_enabled, configured.max_instances_per_run,
                               configured.priority, configured.enabled,
                               configured.review_status, configured.config,
                               mapping.physical_schema, mapping.physical_table,
                               mapping.approximate_rows, mapping.mapping_status
                        FROM graphsync.profile_class configured
                        LEFT JOIN graphsync.current_class_mapping mapping
                          ON mapping.class_name=configured.class_name
                        WHERE configured.profile_key=:profile_key
                        ORDER BY configured.priority, configured.class_name
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
            relationships = _rows(
                connection.execute(
                    text(
                        """
                        SELECT configured.profile_key, configured.source_class,
                               configured.relationship_name, configured.target_class,
                               configured.strength, configured.required_context,
                               configured.traverse, configured.direction,
                               configured.max_depth, configured.max_targets_per_source,
                               configured.enabled, configured.review_status,
                               configured.config,
                               mapping.mapping_status, mapping.cardinality,
                               mapping.source_property, mapping.physical_column
                        FROM graphsync.profile_relationship configured
                        LEFT JOIN graphsync.current_relationship_mapping mapping
                          ON mapping.source_class=configured.source_class
                         AND mapping.relationship_name=configured.relationship_name
                         AND mapping.target_class=configured.target_class
                        WHERE configured.profile_key=:profile_key
                        ORDER BY configured.source_class,
                                 configured.relationship_name, configured.target_class
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
        return {"profile": dict(profile), "classes": classes, "relationships": relationships}

    def graph_profile_candidates(self, profile_key: str) -> dict[str, list[dict[str, Any]]]:
        with self.engine.connect() as connection:
            exists = connection.execute(
                text("SELECT EXISTS(SELECT 1 FROM graphsync.graph_profile WHERE profile_key=:key)"),
                {"key": profile_key},
            ).scalar_one()
            if not exists:
                raise KeyError(profile_key)
            classes = _rows(
                connection.execute(
                    text(
                        """
                        SELECT mapping.class_name, mapping.chinese_name,
                               mapping.physical_schema, mapping.physical_table,
                               mapping.approximate_rows, mapping.mapping_status,
                               (configured.class_name IS NOT NULL) AS configured
                        FROM graphsync.current_class_mapping mapping
                        LEFT JOIN graphsync.profile_class configured
                          ON configured.profile_key=:profile_key
                         AND configured.class_name=mapping.class_name
                        ORDER BY configured DESC, mapping.approximate_rows DESC,
                                 mapping.class_name
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
            relationships = _rows(
                connection.execute(
                    text(
                        """
                        SELECT mapping.source_class, mapping.relationship_name,
                               mapping.target_class, mapping.cardinality,
                               mapping.mapping_status, mapping.source_property,
                               mapping.physical_column,
                               (configured.relationship_name IS NOT NULL) AS configured
                        FROM graphsync.current_relationship_mapping mapping
                        JOIN graphsync.profile_class source_class
                          ON source_class.profile_key=:profile_key
                         AND source_class.class_name=mapping.source_class
                         AND source_class.enabled
                        LEFT JOIN graphsync.profile_relationship configured
                          ON configured.profile_key=:profile_key
                         AND configured.source_class=mapping.source_class
                         AND configured.relationship_name=mapping.relationship_name
                         AND configured.target_class=mapping.target_class
                        ORDER BY configured DESC, mapping.source_class,
                                 mapping.relationship_name, mapping.target_class
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
        return {"classes": classes, "relationships": relationships}

    def update_graph_profile(
        self,
        profile_key: str,
        *,
        title: str,
        description: str | None,
        enabled: bool,
        max_depth: int,
        max_context_nodes_per_seed: int,
        max_total_nodes_per_run: int,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.graph_profile
                    SET title=:title, description=:description, enabled=:enabled,
                        max_depth=:max_depth,
                        max_context_nodes_per_seed=:max_context_nodes_per_seed,
                        max_total_nodes_per_run=:max_total_nodes_per_run
                    WHERE profile_key=:profile_key
                    RETURNING profile_key, title, description, job_name, enabled,
                              max_depth, max_context_nodes_per_seed,
                              max_total_nodes_per_run, config, updated_at
                    """
                ),
                locals(),
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(profile_key)
        return dict(row)

    def upsert_profile_class(
        self,
        profile_key: str,
        class_name: str,
        *,
        role: str,
        orphan_policy: str,
        seed_enabled: bool,
        max_instances_per_run: int | None,
        priority: int,
        enabled: bool,
        review_status: str,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            mapped = connection.execute(
                text("SELECT EXISTS(SELECT 1 FROM graphsync.current_class_mapping WHERE class_name=:class_name)"),
                {"class_name": class_name},
            ).scalar_one()
            if not mapped:
                raise KeyError(class_name)
            row = connection.execute(
                text(
                    """
                    INSERT INTO graphsync.profile_class
                        (profile_key, class_name, role, orphan_policy, seed_enabled,
                         max_instances_per_run, priority, enabled, review_status)
                    VALUES
                        (:profile_key, :class_name, :role, :orphan_policy, :seed_enabled,
                         :max_instances_per_run, :priority, :enabled, :review_status)
                    ON CONFLICT (profile_key, class_name) DO UPDATE SET
                        role=EXCLUDED.role, orphan_policy=EXCLUDED.orphan_policy,
                        seed_enabled=EXCLUDED.seed_enabled,
                        max_instances_per_run=EXCLUDED.max_instances_per_run,
                        priority=EXCLUDED.priority, enabled=EXCLUDED.enabled,
                        review_status=EXCLUDED.review_status
                    RETURNING profile_key, class_name, role, orphan_policy,
                              seed_enabled, max_instances_per_run, priority,
                              enabled, review_status, config, updated_at
                    """
                ),
                locals(),
            ).mappings().one()
        return dict(row)

    def upsert_profile_relationship(
        self,
        profile_key: str,
        source_class: str,
        relationship_name: str,
        target_class: str,
        *,
        strength: str,
        required_context: bool,
        traverse: bool,
        direction: str,
        max_depth: int | None,
        max_targets_per_source: int,
        enabled: bool,
        review_status: str,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            candidate = connection.execute(
                text(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM graphsync.current_relationship_mapping
                        WHERE source_class=:source_class
                          AND relationship_name=:relationship_name
                          AND target_class=:target_class
                    )
                    """
                ),
                locals(),
            ).scalar_one()
            if not candidate:
                raise KeyError(relationship_name)
            row = connection.execute(
                text(
                    """
                    INSERT INTO graphsync.profile_relationship
                        (profile_key, source_class, relationship_name, target_class,
                         strength, required_context, traverse, direction, max_depth,
                         max_targets_per_source, enabled, review_status)
                    VALUES
                        (:profile_key, :source_class, :relationship_name, :target_class,
                         :strength, :required_context, :traverse, :direction, :max_depth,
                         :max_targets_per_source, :enabled, :review_status)
                    ON CONFLICT (profile_key, source_class, relationship_name, target_class)
                    DO UPDATE SET strength=EXCLUDED.strength,
                        required_context=EXCLUDED.required_context,
                        traverse=EXCLUDED.traverse, direction=EXCLUDED.direction,
                        max_depth=EXCLUDED.max_depth,
                        max_targets_per_source=EXCLUDED.max_targets_per_source,
                        enabled=EXCLUDED.enabled, review_status=EXCLUDED.review_status
                    RETURNING profile_key, source_class, relationship_name,
                              target_class, strength, required_context, traverse,
                              direction, max_depth, max_targets_per_source,
                              enabled, review_status, config, updated_at
                    """
                ),
                locals(),
            ).mappings().one()
        return dict(row)

    def update_setting(self, key: str, value: Any) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.app_setting
                    SET value=CAST(:value AS jsonb), updated_at=now()
                    WHERE setting_key=:key AND editable
                    RETURNING setting_key, value, description, editable, updated_at
                    """
                ),
                {"key": key, "value": json.dumps(value, ensure_ascii=False)},
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(key)
        return dict(row)
