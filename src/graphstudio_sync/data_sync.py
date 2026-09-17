"""Business-facing data synchronization status and one-click data-lane run."""

from __future__ import annotations

import json
import socket
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from .config import SyncSettings
from .curation import build_curation_preview
from .incremental import execute_incremental_plan
from .incremental_preview import build_incremental_preview
from src.graphstudio_sync.publishing.materialization import execute_materialization
from src.graphstudio_sync.publishing.materialization import materialization_status
from src.graphstudio_sync.storage.repository import ControlPlaneRepository


INCREMENTAL_STRATEGIES = {"watermark", "append_only", "cdc"}


def data_sync_status(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
) -> dict[str, Any]:
    """Return the compact business status for every active ontology class."""

    profile = repository.graph_profile(profile_key)
    governance = repository.governance_profile(profile_key)
    materialization = materialization_status(repository, profile_key)
    plan = materialization["plan"]
    job_name = profile["profile"]["job_name"]
    policy_by_class = {
        item["class_name"]: item
        for item in repository.list_table_policies(job_name)
    }
    checkpoints = repository.checkpoints_by_partition(job_name)
    windows = {
        item["class_name"]: item
        for item in repository.latest_incremental_windows(job_name)
    }
    coverage = (plan.get("ontologyCoverage") or {}).get("classes") or []
    contracts = {item["class_name"]: item for item in governance.get("contracts") or []}
    profile_classes = {item["class_name"]: item for item in profile.get("classes") or []}
    plan_contracts = {item["className"]: item for item in plan.get("contracts") or []}

    with repository.engine.connect() as connection:
        active_release = connection.execute(
            text(
                """
                SELECT release.release_id, release.release_no, release.status,
                       release.object_count, release.relationship_count,
                       release.quarantine_count, release.scope_exclusion_count,
                       release.started_at,
                       release.finished_at
                FROM graphsync.curated_release_activation active
                JOIN graphsync.curated_release release
                  ON release.release_id=active.active_release_id
                WHERE active.profile_key=:profile
                """
            ),
            {"profile": profile_key},
        ).mappings().one_or_none()
        release_counts = connection.execute(
            text(
                """
                SELECT object.class_name,
                       count(*) FILTER (WHERE object.record_status='active') AS object_count,
                       count(*) FILTER (WHERE object.record_status='out_of_scope') AS scope_exclusion_count,
                       count(*) FILTER (WHERE object.record_status='quarantined') AS quarantine_count
                FROM graphsync.curated_release_activation active
                JOIN graphsync.object_version object
                  ON object.release_id=active.active_release_id
                WHERE active.profile_key=:profile
                GROUP BY object.class_name
                """
            ),
            {"profile": profile_key},
        ).mappings().all()
        reconciliations = connection.execute(
            text(
                """
                SELECT contract.class_name, result.mode, result.source_count,
                       result.release_count, result.difference, result.status,
                       result.details, result.created_at
                FROM graphsync.curated_release_activation active
                JOIN graphsync.reconciliation_result result
                  ON result.release_id=active.active_release_id
                JOIN graphsync.data_contract contract
                  ON contract.contract_key=result.contract_key
                WHERE active.profile_key=:profile
                """
            ),
            {"profile": profile_key},
        ).mappings().all()
        inbox = connection.execute(
            text(
                """
                SELECT class_name,
                       count(*) FILTER (WHERE status='captured') AS pending,
                       count(*) FILTER (WHERE status='applied') AS applied
                FROM graphsync.change_event
                WHERE job_name=:job
                GROUP BY class_name
                """
            ),
            {"job": job_name},
        ).mappings().all()
        relationship_summary = connection.execute(
            text(
                """
                SELECT count(*) AS total,
                       count(*) FILTER (WHERE relation.resolution_status='resolved') AS resolved,
                       count(*) FILTER (WHERE relation.resolution_status='pending') AS pending
                FROM graphsync.curated_release_activation active
                JOIN graphsync.relationship_version relation
                  ON relation.release_id=active.active_release_id
                WHERE active.profile_key=:profile
                """
            ),
            {"profile": profile_key},
        ).mappings().one()
        schedule = connection.execute(
            text(
                """
                SELECT profile_key, job_name, enabled, interval_minutes,
                       max_attempts, retry_backoff_seconds, next_run_at,
                       lease_until, last_run_id, updated_at
                FROM graphsync.data_sync_schedule
                WHERE profile_key=:profile
                """
            ),
            {"profile": profile_key},
        ).mappings().one_or_none()
        recent_runs = connection.execute(
            text(
                """
                SELECT run_id, trigger_type, status, attempt, scheduled_for,
                       next_retry_at, actor, release_id, error, metrics,
                       started_at, finished_at, created_at
                FROM graphsync.data_sync_execution
                WHERE profile_key=:profile
                ORDER BY created_at DESC
                LIMIT 12
                """
            ),
            {"profile": profile_key},
        ).mappings().all()
        worker = connection.execute(
            text(
                """
                SELECT worker_id, last_seen_at, metadata,
                       (last_seen_at >= now() - interval '2 minutes') AS online
                FROM graphsync.data_sync_worker_heartbeat
                ORDER BY last_seen_at DESC LIMIT 1
                """
            )
        ).mappings().one_or_none()
        scope_policies = connection.execute(
            text(
                """
                SELECT policy.policy_key, source.class_name AS source_class,
                       anchor.class_name AS anchor_class, policy.source_columns,
                       policy.anchor_columns, policy.reason, policy.enabled,
                       policy.version, policy.config
                FROM graphsync.row_scope_policy policy
                JOIN graphsync.data_contract source
                  ON source.contract_key=policy.source_contract_key
                JOIN graphsync.data_contract anchor
                  ON anchor.contract_key=policy.anchor_contract_key
                WHERE policy.profile_key=:profile
                ORDER BY policy.policy_key
                """
            ),
            {"profile": profile_key},
        ).mappings().all()

    count_by_class = {item["class_name"]: dict(item) for item in release_counts}
    reconciliation_by_class = {
        item["class_name"]: dict(item) for item in reconciliations
    }
    inbox_by_class = {item["class_name"]: dict(item) for item in inbox}
    rows: list[dict[str, Any]] = []
    for item in coverage:
        class_name = item["className"]
        contract = contracts.get(class_name)
        configured = profile_classes.get(class_name)
        policy = policy_by_class.get(class_name) or {}
        contract_plan = plan_contracts.get(class_name) or {}
        rows.append(
            {
                "className": class_name,
                "coverageStatus": item["status"],
                "coverageReason": item.get("reason"),
                "role": (configured or {}).get("role"),
                "sourceSchema": (contract or {}).get("source_schema")
                or (configured or {}).get("physical_schema"),
                "sourceTable": (contract or {}).get("source_table")
                or (configured or {}).get("physical_table"),
                "catalogRows": int((configured or {}).get("approximate_rows") or 0),
                "contractKey": (contract or {}).get("contract_key"),
                "contractVersion": (contract or {}).get("version"),
                "contractStatus": (contract or {}).get("status"),
                "selectedColumns": len((contract or {}).get("selected_columns") or []),
                "strategy": policy.get("effective_strategy") or policy.get("strategy"),
                "strategyExplicit": bool(policy.get("explicitly_configured")),
                "extractionMode": contract_plan.get("extractionMode"),
                "activeObjectCount": int(
                    (count_by_class.get(class_name) or {}).get("object_count") or 0
                ),
                "activeQuarantineCount": int(
                    (count_by_class.get(class_name) or {}).get("quarantine_count") or 0
                ),
                "scopeExclusionCount": int(
                    (count_by_class.get(class_name) or {}).get("scope_exclusion_count") or 0
                ),
                "reconciliation": reconciliation_by_class.get(class_name),
                "checkpoint": checkpoints.get(class_name),
                "incrementalWindow": windows.get(class_name),
                "pendingEvents": int(
                    (inbox_by_class.get(class_name) or {}).get("pending") or 0
                ),
                "appliedEvents": int(
                    (inbox_by_class.get(class_name) or {}).get("applied") or 0
                ),
            }
        )

    coverage_summary = plan.get("ontologyCoverage") or {}
    return {
        "profileKey": profile_key,
        "jobName": job_name,
        "ready": bool(plan.get("ready")),
        "blockers": plan.get("blockers") or [],
        "coverage": coverage_summary,
        "activeRelease": dict(active_release) if active_release else None,
        "classes": rows,
        "summary": {
            "classes": len(rows),
            "synchronized": int(coverage_summary.get("synchronized") or 0),
            "modelOnly": int(coverage_summary.get("modelOnly") or 0),
            "excluded": int(coverage_summary.get("excluded") or 0),
            "missing": int(coverage_summary.get("missing") or 0),
            "activeObjects": sum(item["activeObjectCount"] for item in rows),
            "scopeExclusions": sum(item["scopeExclusionCount"] for item in rows),
            "pendingEvents": sum(item["pendingEvents"] for item in rows),
            "failedReconciliations": sum(
                (item.get("reconciliation") or {}).get("status") == "failed"
                for item in rows
            ),
            "relationships": int(relationship_summary["total"] or 0),
            "resolvedRelationships": int(relationship_summary["resolved"] or 0),
            "pendingRelationships": int(relationship_summary["pending"] or 0),
        },
        "pipeline": [
            "freeze_source_window",
            "capture_idempotently",
            "quality_and_count_reconcile",
            "activate_immutable_release",
        ],
        "automation": {
            "schedule": dict(schedule) if schedule else None,
            "worker": dict(worker) if worker else None,
            "recentRuns": [dict(item) for item in recent_runs],
        },
        "scopePolicies": [dict(item) for item in scope_policies],
    }


def update_data_sync_schedule(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    enabled: bool,
    interval_minutes: int,
    max_attempts: int,
    retry_backoff_seconds: int,
) -> dict[str, Any]:
    """Configure the durable data-lane clock without enabling publication."""

    if not 1 <= interval_minutes <= 10080:
        raise ValueError("interval_minutes must be between 1 and 10080")
    if not 1 <= max_attempts <= 10:
        raise ValueError("max_attempts must be between 1 and 10")
    if not 5 <= retry_backoff_seconds <= 86400:
        raise ValueError("retry_backoff_seconds must be between 5 and 86400")
    profile = repository.graph_profile(profile_key)["profile"]
    with repository.engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO graphsync.data_sync_schedule
                    (profile_key, job_name, enabled, interval_minutes,
                     max_attempts, retry_backoff_seconds, next_run_at, updated_at)
                VALUES (:profile, :job, :enabled, :interval, :attempts, :backoff,
                        CASE WHEN :enabled THEN now() ELSE NULL END, now())
                ON CONFLICT (profile_key) DO UPDATE SET
                    job_name=EXCLUDED.job_name,
                    enabled=EXCLUDED.enabled,
                    interval_minutes=EXCLUDED.interval_minutes,
                    max_attempts=EXCLUDED.max_attempts,
                    retry_backoff_seconds=EXCLUDED.retry_backoff_seconds,
                    next_run_at=CASE
                        WHEN EXCLUDED.enabled AND NOT graphsync.data_sync_schedule.enabled
                        THEN now()
                        WHEN EXCLUDED.enabled THEN coalesce(graphsync.data_sync_schedule.next_run_at, now())
                        ELSE NULL END,
                    lease_token=CASE WHEN EXCLUDED.enabled THEN graphsync.data_sync_schedule.lease_token ELSE NULL END,
                    lease_until=CASE WHEN EXCLUDED.enabled THEN graphsync.data_sync_schedule.lease_until ELSE NULL END,
                    updated_at=now()
                RETURNING profile_key, job_name, enabled, interval_minutes,
                          max_attempts, retry_backoff_seconds, next_run_at,
                          lease_until, last_run_id, updated_at
                """
            ),
            {
                "profile": profile_key,
                "job": profile["job_name"],
                "enabled": enabled,
                "interval": interval_minutes,
                "attempts": max_attempts,
                "backoff": retry_backoff_seconds,
            },
        ).mappings().one()
    return dict(row)


def _create_manual_execution(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    actor: str | None,
) -> uuid.UUID:
    profile = repository.graph_profile(profile_key)["profile"]
    run_id = uuid.uuid4()
    with repository.engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO graphsync.data_sync_schedule (profile_key, job_name)
                VALUES (:profile, :job)
                ON CONFLICT (profile_key) DO NOTHING
                """
            ),
            {"profile": profile_key, "job": profile["job_name"]},
        )
        connection.execute(
            text(
                """
                INSERT INTO graphsync.data_sync_execution
                    (run_id, profile_key, job_name, trigger_type, status,
                     attempt, scheduled_for, actor)
                VALUES (:run, :profile, :job, 'manual', 'queued', 1, now(), :actor)
                """
            ),
            {"run": run_id, "profile": profile_key, "job": profile["job_name"], "actor": actor},
        )
    return run_id


def claim_due_data_sync(
    repository: ControlPlaneRepository,
    *,
    worker_id: str,
) -> dict[str, Any] | None:
    """Claim exactly one due retry/window using row locks and a renewable lease."""

    lease_token = uuid.uuid4()
    with repository.engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO graphsync.data_sync_worker_heartbeat (worker_id, last_seen_at, metadata)
                VALUES (:worker, now(), CAST(:metadata AS jsonb))
                ON CONFLICT (worker_id) DO UPDATE SET
                    last_seen_at=now(), metadata=EXCLUDED.metadata
                """
            ),
            {"worker": worker_id, "metadata": json.dumps({"host": socket.gethostname()})},
        )
        retry = connection.execute(
            text(
                """
                SELECT failed.profile_key, failed.job_name, failed.scheduled_for,
                       failed.attempt + 1 AS attempt, schedule.retry_backoff_seconds
                FROM graphsync.data_sync_execution failed
                JOIN graphsync.data_sync_schedule schedule USING (profile_key)
                WHERE schedule.enabled
                  AND failed.status='failed'
                  AND failed.next_retry_at <= now()
                  AND failed.attempt < schedule.max_attempts
                  AND NOT EXISTS (
                      SELECT 1 FROM graphsync.data_sync_execution later
                      WHERE later.profile_key=failed.profile_key
                        AND later.scheduled_for=failed.scheduled_for
                        AND later.attempt > failed.attempt
                  )
                  AND (schedule.lease_until IS NULL OR schedule.lease_until < now())
                ORDER BY failed.next_retry_at
                FOR UPDATE OF failed, schedule SKIP LOCKED
                LIMIT 1
                """
            )
        ).mappings().one_or_none()
        trigger = "retry"
        claim = retry
        if claim is None:
            claim = connection.execute(
                text(
                    """
                    SELECT profile_key, job_name, next_run_at AS scheduled_for,
                           1 AS attempt, retry_backoff_seconds
                    FROM graphsync.data_sync_schedule
                    WHERE enabled AND next_run_at <= now()
                      AND (lease_until IS NULL OR lease_until < now())
                    ORDER BY next_run_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """
                )
            ).mappings().one_or_none()
            trigger = "scheduled"
        if claim is None:
            return None
        run_id = uuid.uuid4()
        connection.execute(
            text(
                """
                UPDATE graphsync.data_sync_schedule
                SET lease_token=:token, lease_until=now() + interval '10 minutes',
                    last_run_id=:run,
                    next_run_at=CASE WHEN :trigger='scheduled'
                        THEN now() + make_interval(mins => interval_minutes)
                        ELSE next_run_at END,
                    updated_at=now()
                WHERE profile_key=:profile
                """
            ),
            {"token": lease_token, "run": run_id, "trigger": trigger, "profile": claim["profile_key"]},
        )
        connection.execute(
            text(
                """
                INSERT INTO graphsync.data_sync_execution
                    (run_id, profile_key, job_name, trigger_type, status,
                     attempt, scheduled_for, actor)
                VALUES (:run, :profile, :job, :trigger, 'queued',
                        :attempt, :scheduled_for, :actor)
                """
            ),
            {
                "run": run_id, "profile": claim["profile_key"], "job": claim["job_name"],
                "trigger": trigger, "attempt": claim["attempt"],
                "scheduled_for": claim["scheduled_for"], "actor": f"worker:{worker_id}",
            },
        )
    return {**dict(claim), "runId": str(run_id), "leaseToken": str(lease_token), "triggerType": trigger}


def execute_data_sync_execution(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    run_id: uuid.UUID,
    lease_token: uuid.UUID | None = None,
) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        execution = connection.execute(
            text("SELECT * FROM graphsync.data_sync_execution WHERE run_id=:run FOR UPDATE"),
            {"run": run_id},
        ).mappings().one_or_none()
        if execution is None:
            raise KeyError(str(run_id))
        if execution["status"] not in {"queued", "running"}:
            raise ValueError(f"Data sync execution is already {execution['status']}")
        connection.execute(
            text("UPDATE graphsync.data_sync_execution SET status='running', started_at=coalesce(started_at, now()) WHERE run_id=:run"),
            {"run": run_id},
        )
    try:
        result = execute_data_sync(
            settings, repository, profile_key=execution["profile_key"], actor=execution["actor"],
        )
        release = (result.get("status") or {}).get("activeRelease") or {}
        metrics = {
            "activeObjects": ((result.get("status") or {}).get("summary") or {}).get("activeObjects", 0),
            "pendingRelationships": ((result.get("status") or {}).get("summary") or {}).get("pendingRelationships", 0),
            "graphStudioMutated": False,
        }
        with repository.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE graphsync.data_sync_execution
                    SET status='succeeded', release_id=:release,
                        metrics=CAST(:metrics AS jsonb), next_retry_at=NULL,
                        finished_at=now()
                    WHERE run_id=:run
                    """
                ),
                {"run": run_id, "release": release.get("release_id"), "metrics": json.dumps(metrics)},
            )
        return {**result, "executionId": str(run_id)}
    except Exception as exc:
        overlap = "already active" in str(exc).casefold()
        with repository.engine.begin() as connection:
            retry = connection.execute(
                text("SELECT max_attempts, retry_backoff_seconds FROM graphsync.data_sync_schedule WHERE profile_key=:profile"),
                {"profile": execution["profile_key"]},
            ).mappings().one()
            next_retry = (
                None if overlap or int(execution["attempt"]) >= int(retry["max_attempts"])
                else datetime.now(timezone.utc)
            )
            connection.execute(
                text(
                    """
                    UPDATE graphsync.data_sync_execution
                    SET status=:status, error=CAST(:error AS jsonb),
                        next_retry_at=CASE WHEN :retry_due IS NULL THEN NULL
                            ELSE now() + make_interval(secs => :backoff * power(2, :attempt - 1)::integer) END,
                        finished_at=now()
                    WHERE run_id=:run
                    """
                ),
                {
                    "run": run_id, "status": "skipped" if overlap else "failed",
                    "error": json.dumps({"type": type(exc).__name__, "message": str(exc)}),
                    "retry_due": next_retry, "backoff": int(retry["retry_backoff_seconds"]),
                    "attempt": int(execution["attempt"]),
                },
            )
        raise
    finally:
        if lease_token:
            with repository.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        UPDATE graphsync.data_sync_schedule
                        SET lease_token=NULL, lease_until=NULL, updated_at=now()
                        WHERE profile_key=:profile AND lease_token=:token
                        """
                    ),
                    {"profile": execution["profile_key"], "token": lease_token},
                )


def execute_audited_data_sync(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    actor: str | None,
) -> dict[str, Any]:
    run_id = _create_manual_execution(repository, profile_key=profile_key, actor=actor)
    return execute_data_sync_execution(settings, repository, run_id=run_id)


def run_due_data_sync(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    worker_id: str,
) -> dict[str, Any]:
    claim = claim_due_data_sync(repository, worker_id=worker_id)
    if claim is None:
        return {"ok": True, "claimed": False}
    result = execute_data_sync_execution(
        settings, repository, run_id=uuid.UUID(claim["runId"]),
        lease_token=uuid.UUID(claim["leaseToken"]),
    )
    return {"ok": True, "claimed": True, "claim": claim, "result": result}


def execute_data_sync(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    actor: str | None,
) -> dict[str, Any]:
    """Run the PostgreSQL data lane without publishing to Graph Studio."""

    before = data_sync_status(repository, profile_key=profile_key)
    if int((before.get("coverage") or {}).get("missing") or 0):
        raise RuntimeError("Data synchronization coverage is incomplete: " + "; ".join(before["blockers"]))
    lock_name = f"graphsync:data-lane:{profile_key}"
    with repository.engine.connect() as lock_connection:
        acquired = lock_connection.execute(
            text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"),
            {"name": lock_name},
        ).scalar_one()
        if not acquired:
            raise RuntimeError(f"A data synchronization run is already active for {profile_key}")
        try:
            profile = repository.graph_profile(profile_key)["profile"]
            job_name = profile["job_name"]
            governed_classes = {
                item["className"] for item in before.get("classes") or []
                if item.get("coverageStatus") == "synchronized"
            }
            incremental_policies = [
                item for item in repository.list_table_policies(job_name)
                if item["class_name"] in governed_classes
                and item.get("enabled", True)
                and (item.get("effective_strategy") or item.get("strategy"))
                in INCREMENTAL_STRATEGIES
            ]
            incremental_plan = None
            incremental_preview = None
            if incremental_policies:
                incremental_plan = execute_incremental_plan(
                    settings, repository, job_name=job_name,
                    refresh_capabilities=True,
                )
                incremental_preview = build_incremental_preview(
                    settings, repository, job_name=job_name,
                )
            quality = build_curation_preview(
                settings, repository, profile_key=profile_key,
            )
            if not quality.get("publishable"):
                raise RuntimeError("Data synchronization quality gate failed")
            materialized = execute_materialization(
                settings,
                repository,
                profile_key=profile_key,
                apply=True,
                activate=True,
                actor=actor,
            )
            after = data_sync_status(repository, profile_key=profile_key)
            return {
                "ok": True,
                "profileKey": profile_key,
                "graphStudioMutated": False,
                "incrementalPlan": incremental_plan,
                "incrementalPreview": incremental_preview,
                "quality": quality,
                "materialization": materialized,
                "status": after,
            }
        finally:
            lock_connection.execute(
                text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"),
                {"name": lock_name},
            )
