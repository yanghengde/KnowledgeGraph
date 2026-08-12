"""Command-line entry point for the Camstar to Graph Studio sync tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

from .config import SyncSettings
from .inventory import build_plan, check_graphstudio, read_ontology, read_source_catalog


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
            engine = create_engine(settings.state_database_url, pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            checks["stateDatabase"] = {"ok": True, "configured": True}
        except Exception as exc:  # pragma: no cover - integration failure path
            checks["stateDatabase"] = {"ok": False, "configured": True, "error": str(exc).splitlines()[0]}
    else:
        checks["stateDatabase"] = {
            "ok": True,
            "configured": False,
            "warning": "SYNC_STATE_DATABASE_URL is not set; production checkpoints are not durable yet",
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
    args = parser.parse_args(argv)
    settings = SyncSettings.from_env()
    payload = doctor(settings) if args.command == "doctor" else build_plan(settings)
    _write(payload, args.output)
    return 0 if payload.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())

