"""Command-line entry point for the Camstar to Graph Studio sync tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

from .config import SyncSettings
from .catalog import compile_catalog
from .database import initialize_control_plane
from .inventory import build_plan, check_graphstudio, read_ontology, read_source_catalog
from .repository import ControlPlaneRepository
from .preview import build_full_preview
from .run_manager import execute_dry_run


def _write(payload: dict[str, Any], output: Path | None = None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
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
    else:
        repository = ControlPlaneRepository(settings)
        payload = build_full_preview(settings, repository, job_name=args.job)
    _write(payload, args.output)
    return 0 if payload.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
