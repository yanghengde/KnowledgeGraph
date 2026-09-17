"""sync runs persistence for the control plane."""
from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text


from .repository_support import _rows


class SyncRunsRepository:
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
                               committed_run_id, committed_release_id, validation,
                               committed_at
                        FROM graphsync.checkpoint
                        WHERE job_name=:job_name
                        """
                    ),
                    {"job_name": job_name},
                )
            )
        return {row["partition_key"]: row for row in rows}


    def stage_change_events(
        self,
        *,
        job_name: str,
        class_name: str,
        window_id: uuid.UUID | str,
        events: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Idempotently persist captured changes and reject identity drift."""

        if not events:
            return {"received": 0, "inserted": 0, "duplicates": 0}
        unique_events: dict[str, dict[str, Any]] = {}
        for event in events:
            event_key = str(event["event_key"])
            previous = unique_events.get(event_key)
            if previous and previous.get("payload_hash") != event.get("payload_hash"):
                raise RuntimeError(
                    f"Captured source position returned different payloads in one batch: {event_key}"
                )
            unique_events[event_key] = event
        payload = json.dumps(list(unique_events.values()), ensure_ascii=False, default=str)
        with self.engine.begin() as connection:
            conflicts = connection.execute(
                text(
                    """
                    WITH incoming AS (
                        SELECT * FROM jsonb_to_recordset(CAST(:events AS jsonb)) AS item(
                            event_key text, payload_hash text
                        )
                    )
                    SELECT existing.event_key
                    FROM incoming
                    JOIN graphsync.change_event existing USING (event_key)
                    WHERE existing.payload_hash <> incoming.payload_hash
                    LIMIT 20
                    """
                ),
                {"events": payload},
            ).scalars().all()
            if conflicts:
                raise RuntimeError(
                    "Captured source position returned a different payload: "
                    + ", ".join(conflicts)
                )
            inserted = connection.execute(
                text(
                    """
                    WITH incoming AS (
                        SELECT * FROM jsonb_to_recordset(CAST(:events AS jsonb)) AS item(
                            event_key text, operation text,
                            source_primary_key jsonb, source_position jsonb,
                            row_payload jsonb, payload_hash text
                        )
                    )
                    INSERT INTO graphsync.change_event
                        (event_key, job_name, class_name, window_id, operation,
                         source_primary_key, source_position, row_payload,
                         payload_hash)
                    SELECT event_key, :job_name, :class_name, :window_id,
                           operation, source_primary_key, source_position,
                           row_payload, payload_hash
                    FROM incoming
                    ON CONFLICT (event_key) DO NOTHING
                    RETURNING event_key
                    """
                ),
                {
                    "events": payload,
                    "job_name": job_name,
                    "class_name": class_name,
                    "window_id": uuid.UUID(str(window_id)),
                },
            ).scalars().all()
        inserted_count = len(inserted)
        return {
            "received": len(events),
            "inserted": inserted_count,
            "duplicates": len(events) - inserted_count,
        }


    def mark_change_events_applied(
        self,
        *,
        release_id: uuid.UUID | str,
        window_ids: list[uuid.UUID | str],
    ) -> int:
        if not window_ids:
            return 0
        with self.engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    UPDATE graphsync.change_event
                    SET status='applied', applied_release_id=:release_id,
                        applied_at=now()
                    WHERE window_id=ANY(CAST(:window_ids AS uuid[]))
                      AND status='captured'
                    """
                ),
                {
                    "release_id": uuid.UUID(str(release_id)),
                    "window_ids": [str(item) for item in window_ids],
                },
            )
        return int(result.rowcount or 0)


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

