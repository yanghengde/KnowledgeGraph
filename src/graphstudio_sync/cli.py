"""Command-line entry point for the Camstar to Graph Studio sync tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

from .config import SyncSettings
from .continuous_sync import execute_continuous_sync
from .catalog import compile_catalog
from .curation import build_curation_preview
from .deployment import create_deployment, deployment_status
from .database import initialize_control_plane
from .inventory import build_plan, check_graphstudio, read_ontology, read_source_catalog
from .incremental import execute_incremental_plan, execute_incremental_probe
from .incremental_preview import build_incremental_preview
from .materialization import execute_materialization, materialization_status, rollback_release
from .observability import observability_status, run_health_check
from .repository import ControlPlaneRepository
from .preview import build_full_preview
from .run_manager import execute_dry_run


def _write(payload: dict[str, Any], output: Path | None = None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def doctor(settings: SyncSettings) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    try:
        ontology = read_ontology(settings)
        checks["neo4j"] = {"ok": True, "classes": len(ontology.classes)}
    except Exception as exc:  # pragma: no cover - integration failure path
        checks["neo4j"] = {"ok": False, "error": str(exc).splitlines()[0]}
    try:
        source = read_source_catalog(settings)
        checks["sourceDatabase"] = {"ok": True, "tables": len(source)}
    except Exception as exc:  # pragma: no cover - integration failure path
        checks["sourceDatabase"] = {"ok": False, "error": str(exc).splitlines()[0]}
    try:
        graphstudio = check_graphstudio(settings)
        shared = [
            uri
            for uri in graphstudio["fileConnections"]
            if "DataSources#FileConnection_" not in uri
        ]
        checks["graphStudio"] = {
            "ok": True,
            "title": graphstudio["graphmart"].get("title"),
            "status": graphstudio["status"].get("status"),
            "sharedFileConnections": shared,
        }
    except Exception as exc:  # pragma: no cover - integration failure path
        checks["graphStudio"] = {"ok": False, "error": str(exc).splitlines()[0]}
    if settings.state_database_url:
        try:
            engine = create_engine(
                settings.state_database_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 10},
            )
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            checks["stateDatabase"] = {"ok": True, "configured": True}
        except Exception as exc:  # pragma: no cover - integration failure path
            checks["stateDatabase"] = {"ok": False, "configured": True, "error": str(exc).splitlines()[0]}
    else:
        checks["stateDatabase"] = {
            "ok": True,
            "configured": False,
            "warning": (
                "PostgreSQL control plane is disabled; set PGSQL_ENABLED=true and PGSQL_PASSWORD, "
                "or provide SYNC_STATE_DATABASE_URL"
            ),
        }
    return {
        "ok": all(item.get("ok") for item in checks.values()),
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="graphstudio-sync")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor_parser = subparsers.add_parser("doctor", help="Run read-only connectivity and dependency checks")
    doctor_parser.add_argument("--output", type=Path)
    plan_parser = subparsers.add_parser("plan", help="Build a read-only full synchronization inventory")
    plan_parser.add_argument("--output", type=Path)
    init_parser = subparsers.add_parser("init-db", help="Create and initialize the PostgreSQL control plane")
    init_parser.add_argument("--output", type=Path)
    init_parser.add_argument(
        "--no-create-database",
        action="store_true",
        help="Initialize the configured database without attempting CREATE DATABASE",
    )
    init_parser.add_argument(
        "--sync-connections",
        action="store_true",
        help="Overwrite existing connection metadata from environment variables",
    )
    dry_run_parser = subparsers.add_parser("dry-run", help="Record a full source and mapping inventory run")
    dry_run_parser.add_argument("--job", default="camstar-full")
    dry_run_parser.add_argument("--output", type=Path)
    catalog_parser = subparsers.add_parser(
        "compile-catalog",
        help="Compile Neo4j and Camstar physical mappings into PostgreSQL",
    )
    catalog_parser.add_argument("--output", type=Path)
    preview_parser = subparsers.add_parser(
        "preview",
        help="Build and validate a complete RDF preview without mutating Graph Studio",
    )
    preview_parser.add_argument("--job", default="camstar-full")
    preview_parser.add_argument("--output", type=Path)
    probe_parser = subparsers.add_parser(
        "probe-incremental",
        help="Probe SQL Server CT/CDC or Oracle SCN capabilities without extracting rows",
    )
    probe_parser.add_argument("--job", default="camstar-full")
    probe_parser.add_argument("--output", type=Path)
    incremental_plan_parser = subparsers.add_parser(
        "plan-incremental",
        help="Freeze safe incremental windows without extracting rows or mutating Graph Studio",
    )
    incremental_plan_parser.add_argument("--job", default="camstar-full")
    incremental_plan_parser.add_argument("--output", type=Path)
    incremental_plan_parser.add_argument("--no-refresh", action="store_true")
    incremental_preview_parser = subparsers.add_parser(
        "preview-incremental",
        help="Extract planned change windows into an audited JSONL package without publishing",
    )
    incremental_preview_parser.add_argument("--job", default="camstar-full")
    incremental_preview_parser.add_argument("--output", type=Path)
    curation_preview_parser = subparsers.add_parser(
        "preview-curation",
        help="Evaluate governed Camstar data contracts without materializing business rows",
    )
    curation_preview_parser.add_argument("--profile", default="opcenter2607-core")
    curation_preview_parser.add_argument("--output", type=Path)
    curation_cycle_parser = subparsers.add_parser(
        "curation-cycle",
        help="Run quality gates and optionally materialize/activate one governed release",
    )
    curation_cycle_parser.add_argument("--profile", default="opcenter2607-core")
    curation_cycle_parser.add_argument("--apply", action="store_true")
    curation_cycle_parser.add_argument("--actor", default="scheduler")
    curation_cycle_parser.add_argument("--output", type=Path)
    continuous_parser = subparsers.add_parser(
        "continuous-cycle",
        help="Probe/plan/extract incremental changes, refresh quality evidence and optionally activate a curated release",
    )
    continuous_parser.add_argument("--job", default="camstar-full")
    continuous_parser.add_argument("--profile", default="opcenter2607-core")
    continuous_parser.add_argument("--apply", action="store_true")
    continuous_parser.add_argument("--actor", default="scheduler")
    continuous_parser.add_argument("--output", type=Path)
    publish_cycle_parser = subparsers.add_parser(
        "continuous-publish",
        help="Run the complete data lane through a blue-green Graph Studio deployment",
    )
    publish_cycle_parser.add_argument("--job", default="camstar-full")
    publish_cycle_parser.add_argument("--profile", default="opcenter2607-core")
    publish_cycle_parser.add_argument("--environment", choices=("dev", "uat", "prod"), default="dev")
    publish_cycle_parser.add_argument("--apply", action="store_true")
    publish_cycle_parser.add_argument("--actor", default="scheduler")
    publish_cycle_parser.add_argument("--output", type=Path)
    materialize_parser = subparsers.add_parser(
        "materialize-curated",
        help="Plan or build an immutable curated release; writes require --apply",
    )
    materialize_parser.add_argument("--profile", default="opcenter2607-core")
    materialize_parser.add_argument("--apply", action="store_true")
    materialize_parser.add_argument("--activate", action="store_true")
    materialize_parser.add_argument("--actor")
    materialize_parser.add_argument("--output", type=Path)
    release_status_parser = subparsers.add_parser("release-status", help="Show curated release state")
    release_status_parser.add_argument("--profile", default="opcenter2607-core")
    release_status_parser.add_argument("--output", type=Path)
    rollback_parser = subparsers.add_parser("rollback-curated", help="Restore the previous curated release pointer")
    rollback_parser.add_argument("--profile", default="opcenter2607-core")
    rollback_parser.add_argument("--actor")
    rollback_parser.add_argument("--output", type=Path)
    deployment_parser = subparsers.add_parser("prepare-deployment", help="Build an immutable Graph Studio deployment artifact")
    deployment_parser.add_argument("--profile", default="opcenter2607-core")
    deployment_parser.add_argument("--environment", choices=("dev", "uat", "prod"), default="dev")
    deployment_parser.add_argument("--actor")
    deployment_parser.add_argument("--output", type=Path)
    deployment_status_parser = subparsers.add_parser("deployment-status", help="Show environment promotion state")
    deployment_status_parser.add_argument("--profile", default="opcenter2607-core")
    deployment_status_parser.add_argument("--output", type=Path)
    health_parser = subparsers.add_parser("health-check", help="Collect lineage and release health metrics")
    health_parser.add_argument("--profile", default="opcenter2607-core")
    health_parser.add_argument("--output", type=Path)
    health_status_parser = subparsers.add_parser("health-status", help="Show latest health metrics and alerts")
    health_status_parser.add_argument("--profile", default="opcenter2607-core")
    health_status_parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    settings = SyncSettings.from_env()
    if args.command == "doctor":
        payload = doctor(settings)
    elif args.command == "plan":
        payload = build_plan(settings)
    elif args.command == "init-db":
        payload = {
            "ok": True,
            "controlPlane": initialize_control_plane(
                settings,
                create_database=not args.no_create_database,
                overwrite_connections=args.sync_connections,
            ),
        }
    elif args.command == "dry-run":
        repository = ControlPlaneRepository(settings)
        payload = execute_dry_run(settings, repository, job_name=args.job)
    elif args.command == "compile-catalog":
        repository = ControlPlaneRepository(settings)
        payload = {"ok": True, "catalog": compile_catalog(settings, repository)}
    elif args.command == "preview":
        repository = ControlPlaneRepository(settings)
        payload = build_full_preview(settings, repository, job_name=args.job)
    elif args.command == "probe-incremental":
        repository = ControlPlaneRepository(settings)
        payload = execute_incremental_probe(settings, repository, job_name=args.job)
    elif args.command == "plan-incremental":
        repository = ControlPlaneRepository(settings)
        payload = execute_incremental_plan(
            settings,
            repository,
            job_name=args.job,
            refresh_capabilities=not args.no_refresh,
        )
    elif args.command == "preview-incremental":
        repository = ControlPlaneRepository(settings)
        payload = build_incremental_preview(settings, repository, job_name=args.job)
    elif args.command == "preview-curation":
        repository = ControlPlaneRepository(settings)
        payload = build_curation_preview(settings, repository, profile_key=args.profile)
    elif args.command == "curation-cycle":
        repository = ControlPlaneRepository(settings)
        preview_result = build_curation_preview(settings, repository, profile_key=args.profile)
        materialized = None
        if args.apply and preview_result.get("publishable"):
            materialized = execute_materialization(
                settings, repository, profile_key=args.profile,
                apply=True, activate=True, actor=args.actor,
            )
        payload = {
            "ok": bool(preview_result.get("publishable")) if args.apply else True,
            "previewOnly": not args.apply,
            "curation": preview_result,
            "materialization": materialized,
        }
    elif args.command == "continuous-cycle":
        repository = ControlPlaneRepository(settings)
        probe_result = execute_incremental_probe(settings, repository, job_name=args.job)
        plan_result = execute_incremental_plan(
            settings, repository, job_name=args.job, refresh_capabilities=False,
        )
        incremental_result = build_incremental_preview(settings, repository, job_name=args.job)
        curation_result = build_curation_preview(settings, repository, profile_key=args.profile)
        materialized = None
        if args.apply and curation_result.get("publishable"):
            materialized = execute_materialization(
                settings, repository, profile_key=args.profile,
                apply=True, activate=True, actor=args.actor,
            )
        payload = {
            "ok": bool(curation_result.get("publishable")) if args.apply else True,
            "previewOnly": not args.apply,
            "incrementalProbe": probe_result,
            "incrementalPlan": plan_result,
            "incrementalPreview": incremental_result,
            "curation": curation_result,
            "materialization": materialized,
        }
    elif args.command == "continuous-publish":
        repository = ControlPlaneRepository(settings)
        payload = execute_continuous_sync(
            settings, repository, job_name=args.job, profile_key=args.profile,
            environment_key=args.environment, actor=args.actor, apply=args.apply,
        )
    elif args.command == "materialize-curated":
        repository = ControlPlaneRepository(settings)
        payload = execute_materialization(
            settings, repository, profile_key=args.profile,
            apply=args.apply, activate=args.activate, actor=args.actor,
        )
    elif args.command == "release-status":
        repository = ControlPlaneRepository(settings)
        payload = materialization_status(repository, args.profile)
    elif args.command == "rollback-curated":
        repository = ControlPlaneRepository(settings)
        payload = rollback_release(repository, profile_key=args.profile, actor=args.actor)
    elif args.command == "prepare-deployment":
        repository = ControlPlaneRepository(settings)
        payload = create_deployment(
            repository, profile_key=args.profile,
            environment_key=args.environment, actor=args.actor,
        )
    elif args.command == "deployment-status":
        repository = ControlPlaneRepository(settings)
        payload = deployment_status(repository, args.profile)
    elif args.command == "health-check":
        repository = ControlPlaneRepository(settings)
        payload = run_health_check(repository, args.profile)
    else:
        repository = ControlPlaneRepository(settings)
        payload = observability_status(repository, args.profile)
    _write(payload, args.output)
    return 0 if payload.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
