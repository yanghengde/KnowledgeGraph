"""Data access for the Graph Studio synchronization control plane."""

from __future__ import annotations

import csv
import json
import uuid
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import text

from .config import PROJECT_ROOT, SyncSettings
from .database import control_engine


PLAN_FILE = PROJECT_ROOT / "outputs" / "graphstudio" / "full_sync_plan.json"


def _rows(result) -> list[dict[str, Any]]:
    return [dict(row) for row in result.mappings().all()]


@lru_cache(maxsize=1)
def _physical_key_catalog() -> dict[str, dict[str, list[str]]]:
    """Read the immutable Camstar physical-field fact source for key metadata."""
    result: dict[str, dict[str, list[str]]] = {}
    with (PROJECT_ROOT / "docs" / "Database_Fields.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            class_name = row.get("CDOName") or ""
            field_name = row.get("FieldName") or ""
            if not class_name or not field_name:
                continue
            keys = result.setdefault(class_name, {"primary": [], "business": []})
            if row.get("IsPrimaryKey") == "True":
                keys["primary"].append(field_name)
            if row.get("IsCandidateKey") == "True":
                keys["business"].append(field_name)
    return result


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

    def governance_profile(self, profile_key: str) -> dict[str, Any]:
        with self.engine.connect() as connection:
            profile_exists = connection.execute(
                text("SELECT EXISTS(SELECT 1 FROM graphsync.graph_profile WHERE profile_key=:key)"),
                {"key": profile_key},
            ).scalar_one()
            if not profile_exists:
                raise KeyError(profile_key)
            contracts = _rows(
                connection.execute(
                    text(
                        """
                        SELECT contract.contract_key, contract.profile_key,
                               contract.class_name, contract.version, contract.status,
                               contract.source_schema, contract.source_table,
                               contract.primary_key_columns,
                               contract.business_key_columns,
                               contract.selected_columns, contract.required_columns,
                               contract.freshness_column, contract.preview_row_limit,
                               contract.publication_layer, contract.quality_thresholds,
                               contract.config, contract.updated_at,
                               mapping.physical_schema AS mapped_schema,
                               mapping.physical_table AS mapped_table,
                               mapping.approximate_rows, mapping.mapping_status,
                               class.review_status AS class_review_status,
                               class.orphan_policy
                        FROM graphsync.data_contract contract
                        LEFT JOIN graphsync.current_class_mapping mapping
                          ON mapping.class_name=contract.class_name
                        LEFT JOIN graphsync.profile_class class
                          ON class.profile_key=contract.profile_key
                         AND class.class_name=contract.class_name
                        WHERE contract.profile_key=:profile_key
                        ORDER BY contract.class_name
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
            relationships = _rows(
                connection.execute(
                    text(
                        """
                        SELECT relationship.relationship_contract_key,
                               relationship.profile_key,
                               relationship.version,
                               relationship.source_contract_key,
                               source.class_name AS source_class,
                               relationship.relationship_name,
                               relationship.target_contract_key,
                               target.class_name AS target_class,
                               relationship.source_columns,
                               relationship.target_columns,
                               relationship.semantic_role,
                               relationship.required_context,
                               relationship.status, relationship.config,
                               relationship.updated_at
                        FROM graphsync.relationship_contract relationship
                        JOIN graphsync.data_contract source
                          ON source.contract_key=relationship.source_contract_key
                        JOIN graphsync.data_contract target
                          ON target.contract_key=relationship.target_contract_key
                        WHERE relationship.profile_key=:profile_key
                        ORDER BY source.class_name, relationship.relationship_name
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
            latest_run = connection.execute(
                text(
                    """
                    SELECT curation_run_id, profile_key, status, preview_only,
                           started_at, finished_at, source_rows_read,
                           accepted_rows, quarantined_rows, publishable,
                           contract_versions, summary, error
                    FROM graphsync.curation_run
                    WHERE profile_key=:profile_key
                    ORDER BY started_at DESC LIMIT 1
                    """
                ),
                {"profile_key": profile_key},
            ).mappings().one_or_none()
            quality_results: list[dict[str, Any]] = []
            if latest_run is not None:
                quality_results = _rows(
                    connection.execute(
                        text(
                            """
                            SELECT quality_result_id, contract_key,
                                   relationship_contract_key, rule_key,
                                   severity, passed, checked_rows, failed_rows,
                                   message, details, created_at
                            FROM graphsync.data_quality_result
                            WHERE curation_run_id=:run_id
                            ORDER BY passed, severity DESC, rule_key
                            """
                        ),
                        {"run_id": latest_run["curation_run_id"]},
                    )
                )
        return {
            "contracts": contracts,
            "relationships": relationships,
            "latestRun": dict(latest_run) if latest_run else None,
            "qualityResults": quality_results,
        }

    def governance_contract_candidates(self, profile_key: str) -> dict[str, Any]:
        """Return only active profile members that still need governed contracts."""
        with self.engine.connect() as connection:
            classes = _rows(connection.execute(text("""
                SELECT configured.class_name, configured.role,
                       mapping.physical_schema, mapping.physical_table,
                       mapping.mapping_status
                FROM graphsync.profile_class configured
                JOIN graphsync.current_class_mapping mapping
                  ON mapping.class_name=configured.class_name
                LEFT JOIN graphsync.data_contract contract
                  ON contract.profile_key=configured.profile_key
                 AND contract.class_name=configured.class_name
                WHERE configured.profile_key=:profile_key
                  AND configured.enabled AND contract.contract_key IS NULL
                ORDER BY configured.priority, configured.class_name
            """), {"profile_key": profile_key}))
            properties = _rows(connection.execute(text("""
                SELECT property.class_name, property.property_name,
                       property.data_type, property.required,
                       property.physical_column, property.mapping_status
                FROM graphsync.current_property_mapping property
                JOIN graphsync.profile_class configured
                  ON configured.profile_key=:profile_key
                 AND configured.class_name=property.class_name
                 AND configured.enabled
                LEFT JOIN graphsync.data_contract contract
                  ON contract.profile_key=configured.profile_key
                 AND contract.class_name=configured.class_name
                WHERE contract.contract_key IS NULL
                  AND property.physical_column IS NOT NULL
                  AND property.mapping_status IN ('resolved', 'override')
                ORDER BY property.class_name, property.required DESC,
                         property.property_name
            """), {"profile_key": profile_key}))
            relationships = _rows(connection.execute(text("""
                SELECT configured.source_class, configured.relationship_name,
                       configured.target_class, configured.required_context,
                       mapping.mapping_status, mapping.source_property,
                       mapping.physical_column,
                       source.contract_key AS source_contract_key,
                       target.contract_key AS target_contract_key,
                       target.primary_key_columns AS target_columns
                FROM graphsync.profile_relationship configured
                LEFT JOIN graphsync.current_relationship_mapping mapping
                  ON mapping.source_class=configured.source_class
                 AND mapping.relationship_name=configured.relationship_name
                 AND mapping.target_class=configured.target_class
                LEFT JOIN graphsync.data_contract source
                  ON source.profile_key=configured.profile_key
                 AND source.class_name=configured.source_class
                LEFT JOIN graphsync.data_contract target
                  ON target.profile_key=configured.profile_key
                 AND target.class_name=configured.target_class
                LEFT JOIN graphsync.relationship_contract contract
                  ON contract.profile_key=configured.profile_key
                 AND contract.source_contract_key=source.contract_key
                 AND contract.relationship_name=configured.relationship_name
                 AND contract.target_contract_key=target.contract_key
                WHERE configured.profile_key=:profile_key
                  AND configured.enabled
                  AND contract.relationship_contract_key IS NULL
                ORDER BY configured.source_class, configured.relationship_name,
                         configured.target_class
            """), {"profile_key": profile_key}))
        property_groups: dict[str, list[dict[str, Any]]] = {}
        for item in properties:
            property_groups.setdefault(item["class_name"], []).append(item)
        for item in classes:
            physical_keys = _physical_key_catalog().get(item["class_name"], {"primary": [], "business": []})
            resolved = property_groups.get(item["class_name"], [])
            resolved_columns = {property["physical_column"] for property in resolved}
            for column in [*physical_keys["primary"], *physical_keys["business"]]:
                if column not in resolved_columns:
                    resolved.append({
                        "class_name": item["class_name"],
                        "property_name": column,
                        "data_type": "String",
                        "required": column in physical_keys["primary"],
                        "physical_column": column,
                        "mapping_status": "physical_key",
                    })
            item["properties"] = resolved
            item["suggested_primary_key_columns"] = physical_keys["primary"]
            item["suggested_business_key_columns"] = physical_keys["business"]
        return {"classes": classes, "relationships": relationships}

    def create_data_contract(
        self,
        profile_key: str,
        *,
        class_name: str,
        primary_key_columns: list[str],
        business_key_columns: list[str],
        selected_columns: list[str],
        required_columns: list[str],
        freshness_column: str | None,
        preview_row_limit: int,
        publication_layer: str,
    ) -> dict[str, Any]:
        candidates = self.governance_contract_candidates(profile_key)
        candidate = next((item for item in candidates["classes"] if item["class_name"] == class_name), None)
        if candidate is None:
            raise KeyError(class_name)
        available = {item["physical_column"] for item in candidate["properties"]}
        selected = list(dict.fromkeys(selected_columns))
        primary = list(dict.fromkeys(primary_key_columns))
        business = list(dict.fromkeys(business_key_columns))
        required = list(dict.fromkeys([*primary, *required_columns]))
        requested = set(selected) | set(primary) | set(business) | set(required)
        if freshness_column:
            requested.add(freshness_column)
        unknown = sorted(requested - available)
        if unknown:
            raise ValueError(f"Contract columns are not resolved physical columns: {unknown}")
        if not primary:
            raise ValueError("At least one primary key column is required")
        if not set(primary).issubset(selected):
            raise ValueError("Primary key columns must be part of selected columns")
        contract_key = f"{profile_key}:{class_name}:v1".lower()
        property_by_column: dict[str, dict[str, Any]] = {}
        for item in candidate["properties"]:
            property_by_column.setdefault(item["physical_column"], item)
        with self.engine.begin() as connection:
            row = connection.execute(text("""
                INSERT INTO graphsync.data_contract
                    (contract_key, profile_key, class_name, version, status,
                     source_schema, source_table, primary_key_columns,
                     business_key_columns, selected_columns, required_columns,
                     freshness_column, preview_row_limit, publication_layer,
                     quality_thresholds, config)
                VALUES
                    (:contract_key, :profile_key, :class_name, 1, 'draft',
                     :source_schema, :source_table, CAST(:primary AS jsonb),
                     CAST(:business AS jsonb), CAST(:selected AS jsonb),
                     CAST(:required AS jsonb), :freshness, :preview_limit,
                     :publication_layer, '{}'::jsonb,
                     jsonb_build_object('generatedBy', 'advanced-governance-wizard'))
                RETURNING *
            """), {
                "contract_key": contract_key, "profile_key": profile_key,
                "class_name": class_name,
                "source_schema": candidate["physical_schema"],
                "source_table": candidate["physical_table"],
                "primary": json.dumps(primary), "business": json.dumps(business),
                "selected": json.dumps(selected), "required": json.dumps(required),
                "freshness": freshness_column, "preview_limit": preview_row_limit,
                "publication_layer": publication_layer,
            }).mappings().one()
            field_rows = []
            for position, column in enumerate(selected, start=1):
                prop = property_by_column[column]
                role = "primary_key" if column in primary else "business_key" if column in business else "freshness" if column == freshness_column else "navigation" if prop.get("data_type") == "Navigation" else "attribute"
                field_rows.append({
                    "contract_key": contract_key,
                    "field_key": f"{contract_key}:{prop['property_name'].lower()}",
                    "source_column": column,
                    "target_field": prop["property_name"],
                    "data_type": prop.get("data_type") or "String",
                    "nullable": column not in required,
                    "required": column in required,
                    "field_role": role,
                    "position": position * 10,
                    "ontology_property": prop["property_name"],
                })
            connection.execute(text("""
                INSERT INTO graphsync.data_contract_field
                    (contract_key, field_key, source_column, target_field,
                     data_type, nullable, required, field_role,
                     lifecycle_status, ordinal_position, introduced_version,
                     ontology_property, config)
                VALUES
                    (:contract_key, :field_key, :source_column, :target_field,
                     :data_type, :nullable, :required, :field_role,
                     'active', :position, 1, :ontology_property,
                     jsonb_build_object('generatedBy', 'advanced-governance-wizard'))
            """), field_rows)
        return dict(row)

    def create_relationship_contract(
        self,
        profile_key: str,
        *,
        source_class: str,
        relationship_name: str,
        target_class: str,
        semantic_role: str,
        required_context: bool,
    ) -> dict[str, Any]:
        candidates = self.governance_contract_candidates(profile_key)
        candidate = next((item for item in candidates["relationships"] if item["source_class"] == source_class and item["relationship_name"] == relationship_name and item["target_class"] == target_class), None)
        if candidate is None:
            raise KeyError(relationship_name)
        target_columns = list(candidate.get("target_columns") or [])
        if candidate.get("mapping_status") != "resolved" or not candidate.get("physical_column"):
            raise ValueError("Relationship mapping must be resolved before creating its contract")
        if not candidate.get("source_contract_key") or not candidate.get("target_contract_key"):
            raise ValueError("Source and target data contracts must exist first")
        if len(target_columns) != 1:
            raise ValueError("Composite target keys require manual relationship contract configuration")
        key = f"{profile_key}:{source_class}:{relationship_name}:{target_class}:v1".lower()
        with self.engine.begin() as connection:
            row = connection.execute(text("""
                INSERT INTO graphsync.relationship_contract
                    (relationship_contract_key, profile_key, version,
                     source_contract_key, relationship_name,
                     target_contract_key, source_columns, target_columns,
                     semantic_role, required_context, status, config)
                VALUES
                    (:key, :profile_key, 1, :source_contract_key,
                     :relationship_name, :target_contract_key,
                     CAST(:source_columns AS jsonb), CAST(:target_columns AS jsonb),
                     :semantic_role, :required_context, 'draft',
                     jsonb_build_object('generatedBy', 'advanced-governance-wizard'))
                RETURNING *
            """), {
                "key": key, "profile_key": profile_key,
                "source_contract_key": candidate["source_contract_key"],
                "relationship_name": relationship_name,
                "target_contract_key": candidate["target_contract_key"],
                "source_columns": json.dumps([candidate["physical_column"]]),
                "target_columns": json.dumps(target_columns),
                "semantic_role": semantic_role,
                "required_context": required_context,
            }).mappings().one()
        return dict(row)

    def update_data_contract(
        self,
        contract_key: str,
        *,
        status: str,
        business_key_columns: list[str],
        required_columns: list[str],
        freshness_column: str | None,
        preview_row_limit: int,
        publication_layer: str,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            existing = connection.execute(
                text(
                    """
                    SELECT selected_columns
                    FROM graphsync.data_contract
                    WHERE contract_key=:contract_key
                    FOR UPDATE
                    """
                ),
                {"contract_key": contract_key},
            ).mappings().one_or_none()
            if existing is None:
                raise KeyError(contract_key)
            selected = set(existing["selected_columns"] or [])
            requested = set(business_key_columns) | set(required_columns)
            if freshness_column:
                requested.add(freshness_column)
            unknown = sorted(requested - selected)
            if unknown:
                raise ValueError(
                    f"Contract columns are not part of the governed projection: {unknown}"
                )
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.data_contract
                    SET version=version + 1, status=:status,
                        business_key_columns=CAST(:business_keys AS jsonb),
                        required_columns=CAST(:required_columns AS jsonb),
                        freshness_column=:freshness_column,
                        preview_row_limit=:preview_row_limit,
                        publication_layer=:publication_layer
                    WHERE contract_key=:contract_key
                    RETURNING contract_key, profile_key, class_name, version,
                              status, source_schema, source_table,
                              primary_key_columns, business_key_columns,
                              selected_columns, required_columns,
                              freshness_column, preview_row_limit,
                              publication_layer, quality_thresholds, config,
                              updated_at
                    """
                ),
                {
                    "contract_key": contract_key,
                    "status": status,
                    "business_keys": json.dumps(business_key_columns),
                    "required_columns": json.dumps(required_columns),
                    "freshness_column": freshness_column,
                    "preview_row_limit": preview_row_limit,
                    "publication_layer": publication_layer,
                },
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(contract_key)
        return dict(row)

    def update_relationship_contract(
        self,
        relationship_contract_key: str,
        *,
        status: str,
        semantic_role: str,
        required_context: bool,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.relationship_contract
                    SET version=version + 1, status=:status, semantic_role=:semantic_role,
                        required_context=:required_context
                    WHERE relationship_contract_key=:key
                    RETURNING relationship_contract_key, profile_key, version,
                              source_contract_key, relationship_name,
                              target_contract_key, source_columns,
                              target_columns, semantic_role, required_context,
                              status, config, updated_at
                    """
                ),
                {
                    "key": relationship_contract_key,
                    "status": status,
                    "semantic_role": semantic_role,
                    "required_context": required_context,
                },
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(relationship_contract_key)
        return dict(row)

    def contract_schema(self, contract_key: str) -> dict[str, Any]:
        with self.engine.connect() as connection:
            contract = connection.execute(
                text(
                    """
                    SELECT contract_key, profile_key, class_name, version, status,
                           source_schema, source_table, primary_key_columns,
                           business_key_columns, selected_columns, required_columns,
                           freshness_column, publication_layer, config, updated_at
                    FROM graphsync.data_contract
                    WHERE contract_key=:contract_key
                    """
                ),
                {"contract_key": contract_key},
            ).mappings().one_or_none()
            if contract is None:
                raise KeyError(contract_key)
            fields = _rows(
                connection.execute(
                    text(
                        """
                        SELECT contract_key, field_key, source_column, target_field,
                               data_type, nullable, required, field_role,
                               lifecycle_status, ordinal_position,
                               introduced_version, deprecated_version,
                               transform_expression, default_expression,
                               ontology_property, sensitivity, searchable,
                               sortable, config, updated_at
                        FROM graphsync.data_contract_field
                        WHERE contract_key=:contract_key
                        ORDER BY ordinal_position, field_key
                        """
                    ),
                    {"contract_key": contract_key},
                )
            )
            field_keys = [row["field_key"] for row in fields]
            dependencies = []
            if field_keys:
                dependencies = _rows(
                    connection.execute(
                        text(
                            """
                            SELECT dependency_id, profile_key, upstream_type,
                                   upstream_key, downstream_type, downstream_key,
                                   dependency_kind, discovered_by, active, metadata,
                                   first_seen_at, last_seen_at
                            FROM graphsync.asset_dependency
                            WHERE profile_key=:profile_key
                              AND upstream_type='data_contract_field'
                              AND upstream_key = ANY(:field_keys)
                            ORDER BY upstream_key, downstream_type, downstream_key
                            """
                        ),
                        {
                            "profile_key": contract["profile_key"],
                            "field_keys": field_keys,
                        },
                    )
                )
        counts = Counter(row["upstream_key"] for row in dependencies if row["active"])
        for field in fields:
            field["dependency_count"] = counts[field["field_key"]]
        return {
            "contract": dict(contract),
            "fields": fields,
            "dependencies": dependencies,
        }

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
        for change in changes:
            change["items"] = [item for item in items if item["change_id"] == change["change_id"]]
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
