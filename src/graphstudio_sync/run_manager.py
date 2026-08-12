"""Durable run lifecycle for planning and future publish operations."""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import text

from .config import PROJECT_ROOT, SyncSettings
from .connections import resolved_settings
from .inventory import build_plan
from .repository import ControlPlaneRepository


PLAN_RUN_DIR = PROJECT_ROOT / "outputs" / "graphstudio" / "plans"


def execute_dry_run(
    base: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    job_name: str,
) -> dict[str, Any]:
    """Inventory sources under a durable run record without mutating Graph Studio."""
    run_id = uuid.uuid4()
    lock_name = f"graphsync:{job_name}"
    with repository.engine.connect() as connection:
        acquired = connection.execute(
            text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"),
            {"name": lock_name},
        ).scalar_one()
        if not acquired:
            raise RuntimeError(f"Sync job is already running: {job_name}")
        try:
            job_exists = connection.execute(
                text("SELECT EXISTS(SELECT 1 FROM graphsync.sync_job WHERE job_name=:job_name)"),
                {"job_name": job_name},
            ).scalar_one()
            if not job_exists:
                raise KeyError(job_name)
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.sync_run (run_id, job_name, status, trigger_type)
                    VALUES (:run_id, :job_name, 'extracting', 'dry_run')
                    """
                ),
                {"run_id": run_id, "job_name": job_name},
            )
            connection.commit()
            try:
                settings = resolved_settings(base, repository)
                plan = build_plan(settings)
                rendered = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
                digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
                PLAN_RUN_DIR.mkdir(parents=True, exist_ok=True)
                plan_file = PLAN_RUN_DIR / f"{run_id}.json"
                plan_file.write_text(rendered, encoding="utf-8")
                source = plan["source"]
                mapping = plan["mapping"]
                connection.execute(
                    text(
                        """
                        UPDATE graphsync.sync_run
                        SET status='succeeded', finished_at=now(), row_count=:rows,
                            manifest_hash=:manifest_hash,
                            metrics=CAST(:metrics AS jsonb)
                        WHERE run_id=:run_id
                        """
                    ),
                    {
                        "run_id": run_id,
                        "rows": source["approximateRows"],
                        "manifest_hash": digest,
                        "metrics": json.dumps(
                            {
                                "ontologyClasses": plan["ontology"]["classes"],
                                "ontologyProperties": plan["ontology"]["properties"],
                                "ontologyRelationships": plan["ontology"]["relationships"],
                                "propertyCoveragePercent": mapping["propertyCoveragePercent"],
                                "propertiesUnmapped": mapping["propertiesUnmapped"],
                            }
                        ),
                    },
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO graphsync.artifact
                            (artifact_id, run_id, artifact_type, storage_path, sha256, byte_size, metadata)
                        VALUES
                            (:artifact_id, :run_id, 'manifest', :path, :sha256, :size,
                             CAST(:metadata AS jsonb))
                        """
                    ),
                    {
                        "artifact_id": uuid.uuid4(),
                        "run_id": run_id,
                        "path": str(plan_file),
                        "sha256": digest,
                        "size": len(rendered.encode("utf-8")),
                        "metadata": json.dumps({"mode": "dry_run", "jobName": job_name}),
                    },
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO graphsync.validation_result
                            (validation_id, run_id, phase, rule_key, severity, passed, message, details)
                        VALUES
                            (:validation_id, :run_id, 'mapping', 'physical-column-coverage',
                             :severity, :passed, :message, CAST(:details AS jsonb))
                        """
                    ),
                    {
                        "validation_id": uuid.uuid4(),
                        "run_id": run_id,
                        "severity": "info" if mapping["propertiesUnmapped"] == 0 else "warning",
                        "passed": mapping["propertiesUnmapped"] == 0,
                        "message": (
                            "All ontology properties map to physical columns"
                            if mapping["propertiesUnmapped"] == 0
                            else f"{mapping['propertiesUnmapped']} properties require explicit review"
                        ),
                        "details": json.dumps(
                            {"coveragePercent": mapping["propertyCoveragePercent"]}
                        ),
                    },
                )
                connection.commit()
                return {"runId": str(run_id), "status": "succeeded", "plan": plan, "artifact": str(plan_file)}
            except Exception as exc:
                connection.rollback()
                connection.execute(
                    text(
                        """
                        UPDATE graphsync.sync_run
                        SET status='failed', finished_at=now(), error=CAST(:error AS jsonb)
                        WHERE run_id=:run_id
                        """
                    ),
                    {
                        "run_id": run_id,
                        "error": json.dumps({"type": type(exc).__name__, "message": str(exc)[:4000]}),
                    },
                )
                connection.commit()
                raise
        finally:
            connection.execute(
                text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"),
                {"name": lock_name},
            )
            connection.commit()
