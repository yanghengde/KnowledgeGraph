"""One safe, schedulable data-only synchronization and publication cycle."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text

from .config import SyncSettings
from .curation import build_curation_preview
from .deployment import apply_deployment, create_deployment, deployment_status
from .incremental import execute_incremental_plan, execute_incremental_probe
from .incremental_preview import build_incremental_preview
from .materialization import execute_materialization, materialization_status
from .repository import ControlPlaneRepository
from .schema_drift import latest_schema_drift, scan_schema_drift


def continuous_sync_status(
    repository: ControlPlaneRepository,
    *,
    job_name: str,
    profile_key: str,
    environment_key: str,
    route_key: str | None = None,
) -> dict[str, Any]:
    jobs = {item["job_name"]: item for item in repository.list_jobs()}
    job = jobs.get(job_name)
    if job is None:
        raise KeyError(job_name)
    materialization = materialization_status(repository, profile_key)
    deployments = deployment_status(repository, profile_key)
    environment = next(
        (item for item in deployments["routes"]
         if (route_key and item["route_key"] == route_key)
         or (not route_key and item["environment_key"] == environment_key)),
        None,
    )
    if environment is None:
        raise KeyError(environment_key)
    with repository.engine.connect() as connection:
        pending_schema = int(connection.execute(
            text(
                """
                SELECT count(*) FROM graphsync.schema_change_request
                WHERE profile_key=:profile
                  AND status IN ('draft','analysis_ready','reviewed','approved','applying','failed')
                """
            ),
            {"profile": profile_key},
        ).scalar_one())
    drift = latest_schema_drift(repository, profile_key=profile_key)
    refreshable_prefixes = (
        "尚未运行治理质量预览", "最近治理质量预览", "最近质量预览",
    )
    blockers = [
        item for item in (materialization["plan"].get("blockers") or [])
        if not str(item).startswith(refreshable_prefixes)
        and "没有已验证的增量变更包" not in str(item)
        and "最新增量窗口已被活动治理版本消费" not in str(item)
    ]
    if not job.get("enabled"):
        blockers.append("持续同步任务已停用")
    if not job.get("schedule"):
        blockers.append("尚未配置 Cron 表达式")
    if pending_schema:
        blockers.append(f"存在 {pending_schema} 个尚未闭环的模型/字段变更")
    if drift.get("scanned") and int((drift.get("summary") or {}).get("blockers") or 0):
        blockers.append(
            f"物理结构检测存在 {drift['summary']['blockers']} 项破坏性变化"
        )
    if not environment.get("apply_enabled"):
        blockers.append(f"{environment['title']} 的 Graph Studio 写入开关未启用")
    latest_deployment = next(
        (item for item in deployments["deployments"]
         if item.get("route_key") == environment["route_key"]),
        None,
    )
    return {
        "job": job,
        "profileKey": profile_key,
        "environment": environment,
        "ready": not blockers,
        "blockers": blockers,
        "activeOntologyRelease": deployments.get("activeOntologyRelease"),
        "activeCuratedRelease": deployments.get("activeCuratedRelease"),
        "latestDeployment": latest_deployment,
        "pendingSchemaChanges": pending_schema,
        "schemaDrift": drift.get("summary") or {},
        "pipeline": [
            "freeze_source_window", "extract_changes", "quality_gate",
            "materialize_immutable_release", "publish_blue_green", "commit_checkpoint",
        ],
    }


def _execute_continuous_sync_unlocked(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    job_name: str,
    profile_key: str,
    environment_key: str = "dev",
    route_key: str | None = None,
    actor: str | None = "scheduler",
    apply: bool = False,
) -> dict[str, Any]:
    """Run the data lane while pinning the active ontology for the whole cycle."""

    drift = None
    if apply:
        drift = scan_schema_drift(settings, repository, profile_key=profile_key)
    before = continuous_sync_status(
        repository, job_name=job_name, profile_key=profile_key,
        environment_key=environment_key, route_key=route_key,
    )
    if not apply:
        return {"ok": True, "previewOnly": True, "status": before}
    if drift and int((drift.get("summary") or {}).get("blockers") or 0):
        raise RuntimeError(
            f"Continuous sync is blocked by {drift['summary']['blockers']} physical schema changes; review them in 模型变更"
        )
    if not before["ready"]:
        raise RuntimeError("Continuous sync is blocked: " + "; ".join(before["blockers"]))
    pinned_ontology = before.get("activeOntologyRelease") or {}
    if not pinned_ontology.get("ontology_release_id"):
        raise RuntimeError("Continuous sync requires an active immutable ontology release")

    probe = execute_incremental_probe(settings, repository, job_name=job_name)
    plan = execute_incremental_plan(
        settings, repository, job_name=job_name, refresh_capabilities=False,
    )
    incremental = build_incremental_preview(settings, repository, job_name=job_name)
    curation = build_curation_preview(settings, repository, profile_key=profile_key)
    if not curation.get("publishable"):
        raise RuntimeError("Continuous sync quality gate failed")
    materialized = execute_materialization(
        settings, repository, profile_key=profile_key,
        apply=True, activate=True, actor=actor,
    )

    after_materialization = deployment_status(repository, profile_key)
    current_ontology = after_materialization.get("activeOntologyRelease") or {}
    if str(current_ontology.get("ontology_release_id")) != str(pinned_ontology["ontology_release_id"]):
        raise RuntimeError(
            "The active ontology changed during data synchronization; the new data release was retained but Graph Studio publication was stopped"
        )
    existing = next((
        item for item in after_materialization["deployments"]
        if item.get("route_key") == before["environment"]["route_key"]
        and str(item["curated_release_id"]) == str(materialized["releaseId"])
        and str(item.get("ontology_release_id")) == str(pinned_ontology["ontology_release_id"])
        and item["status"] == "active"
    ), None)
    if existing:
        published = {"deploymentId": str(existing["deployment_id"]), "status": "active", "reused": True}
    else:
        prepared = create_deployment(
            repository, profile_key=profile_key, environment_key=environment_key,
            route_key=before["environment"]["route_key"],
            release_id=uuid.UUID(materialized["releaseId"]), actor=actor,
        )
        if prepared["status"] != "approved":
            published = {
                "deploymentId": prepared["deploymentId"],
                "status": prepared["status"],
                "awaitingExternalApproval": True,
            }
        else:
            published = apply_deployment(
                settings, repository,
                deployment_id=uuid.UUID(prepared["deploymentId"]),
            )
    return {
        "ok": published.get("status") in {"active", "planned"},
        "previewOnly": False,
        "ontologyReleaseId": str(pinned_ontology["ontology_release_id"]),
        "incrementalProbe": probe,
        "incrementalPlan": plan,
        "incrementalPreview": incremental,
        "curation": curation,
        "materialization": materialized,
        "deployment": published,
    }


def execute_continuous_sync(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    job_name: str,
    profile_key: str,
    environment_key: str = "dev",
    route_key: str | None = None,
    actor: str | None = "scheduler",
    apply: bool = False,
) -> dict[str, Any]:
    if not apply:
        return _execute_continuous_sync_unlocked(
            settings, repository, job_name=job_name, profile_key=profile_key,
            environment_key=environment_key, actor=actor, apply=False,
            route_key=route_key,
        )
    lock_name = f"graphsync:continuous:{job_name}:{route_key or environment_key}"
    with repository.engine.connect() as lock_connection:
        acquired = lock_connection.execute(
            text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"),
            {"name": lock_name},
        ).scalar_one()
        if not acquired:
            raise RuntimeError(f"A continuous sync cycle is already running: {job_name}/{environment_key}")
        try:
            return _execute_continuous_sync_unlocked(
                settings, repository, job_name=job_name, profile_key=profile_key,
                environment_key=environment_key, actor=actor, apply=True,
                route_key=route_key,
            )
        finally:
            lock_connection.execute(
                text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"),
                {"name": lock_name},
            )
            lock_connection.commit()
