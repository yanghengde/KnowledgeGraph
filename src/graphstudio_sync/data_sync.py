"""Business-facing data synchronization status and one-click data-lane run."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from .config import SyncSettings
from .curation import build_curation_preview
from .incremental import execute_incremental_plan
from .incremental_preview import build_incremental_preview
from .materialization import execute_materialization, materialization_status
from .repository import ControlPlaneRepository


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
                       release.quarantine_count, release.started_at,
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
                       count(*) FILTER (WHERE object.record_status <> 'deleted') AS object_count,
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
    }


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
