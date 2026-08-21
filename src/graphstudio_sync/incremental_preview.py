"""Build auditable incremental change packages without publishing or checkpointing."""

from __future__ import annotations

import hashlib
import json
import uuid
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator

from sqlalchemy import text

from .change_capture import (
    ChangeRecord,
    change_event_identity,
    iter_oracle_flashback_changes,
    iter_sqlserver_cdc,
    iter_sqlserver_change_tracking,
    iter_watermark_changes,
)
from .config import PROJECT_ROOT, SyncSettings
from .connections import resolved_settings
from .preview import _load_catalog, _source_metadata
from .repository import ControlPlaneRepository
from .source_database import connect_source


INCREMENTAL_PREVIEW_ROOT = PROJECT_ROOT / "outputs" / "graphstudio" / "incremental_previews"


def _json_default(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "0x" + bytes(value).hex()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _change_iterator(
    connection,
    settings: SyncSettings,
    window: dict[str, Any],
    policy: dict[str, Any],
    table_metadata: dict[str, Any],
    columns: list[str],
) -> Iterator[ChangeRecord]:
    adapter = window["adapter"]
    lower = window["lower_bound"] or {}
    upper = window["upper_bound"]
    common = {
        "schema": table_metadata["schema"],
        "table": table_metadata["table"],
        "columns": columns,
        "primary_keys": table_metadata["primaryKeys"],
        "fetch_size": int(policy["batch_rows"]),
    }
    if adapter == "sqlserver_change_tracking":
        return iter_sqlserver_change_tracking(
            connection,
            **common,
            lower_version=int(lower["changeTrackingVersion"]),
            upper_version=int(upper["changeTrackingVersion"]),
        )
    if adapter == "sqlserver_cdc":
        capture_instance = (window.get("metadata") or {}).get("captureInstance")
        if not capture_instance:
            raise RuntimeError(f"CDC capture instance is missing for {window['class_name']}")
        return iter_sqlserver_cdc(
            connection,
            capture_instance=capture_instance,
            columns=columns,
            primary_keys=table_metadata["primaryKeys"],
            lower_lsn=lower["cdcLsn"],
            upper_lsn=upper["cdcLsn"],
            fetch_size=int(policy["batch_rows"]),
        )
    if adapter == "oracle_flashback_scn":
        return iter_oracle_flashback_changes(
            connection,
            **common,
            lower_scn=int(lower["scn"]),
            upper_scn=int(upper["scn"]),
        )
    if adapter == "database_watermark":
        return iter_watermark_changes(
            connection,
            kind=settings.source_kind,
            **common,
            watermark_column=policy["watermark_column"],
            lower_bound=lower["watermark"],
            upper_bound=upper["watermark"],
            append_only=window["strategy"] == "append_only",
            start_after=lower if lower.get("primaryKey") else None,
        )
    raise RuntimeError(f"Unsupported incremental adapter: {adapter}")


def _write_change_archive(directory: Path, files: list[Path]) -> Path:
    archive_path = directory / "camstar_incremental_changes.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            info = zipfile.ZipInfo(f"changes/{path.name}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Incremental change archive CRC validation failed")
    return archive_path


def build_incremental_preview(
    base_settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    job_name: str = "camstar-full",
) -> dict[str, Any]:
    windows = repository.latest_incremental_windows(job_name)
    if not windows:
        return {
            "jobName": job_name,
            "windows": 0,
            "events": 0,
            "tombstones": 0,
            "status": "no_incremental_windows",
            "previewOnly": True,
            "graphStudioMutated": False,
            "checkpointCommitted": False,
        }
    baseline_windows = [
        window for window in windows if window["status"] == "baseline_required"
    ]
    no_change_windows = [
        window for window in windows if window["status"] == "no_changes"
    ]
    unsafe = [
        window for window in windows
        if window["status"] not in {"planned", "baseline_required", "no_changes"}
    ]
    if unsafe:
        details = ", ".join(f"{item['class_name']}={item['status']}" for item in unsafe[:20])
        raise RuntimeError(f"Incremental preview requires planned windows only: {details}")
    windows = [window for window in windows if window["status"] == "planned"]
    if not windows:
        return {
            "jobName": job_name,
            "windows": 0,
            "events": 0,
            "tombstones": 0,
            "status": "baseline_required" if baseline_windows else "no_changes",
            "baselineClasses": [item["class_name"] for item in baseline_windows],
            "noChangeClasses": [item["class_name"] for item in no_change_windows],
            "previewOnly": True,
            "graphStudioMutated": False,
            "checkpointCommitted": False,
        }

    settings = resolved_settings(base_settings, repository)
    policies = {item["class_name"]: item for item in repository.list_table_policies(job_name)}
    catalog = _load_catalog(repository)
    selected_names = {window["class_name"] for window in windows}
    selected_classes = [item for item in catalog["classes"] if item["class_name"] in selected_names]
    metadata = _source_metadata(settings, selected_classes)
    columns_by_class: dict[str, set[str]] = defaultdict(set)
    for prop in catalog["properties"]:
        if prop["class_name"] in selected_names and prop.get("physical_column"):
            columns_by_class[prop["class_name"]].add(prop["physical_column"])
    for relation in catalog["relationships"]:
        if relation["source_class"] in selected_names and relation.get("physical_column"):
            columns_by_class[relation["source_class"]].add(relation["physical_column"])

    run_id = uuid.uuid4()
    directory = INCREMENTAL_PREVIEW_ROOT / str(run_id)
    directory.mkdir(parents=True, exist_ok=False)
    lock_name = f"graphsync:incremental-preview:{job_name}"
    with repository.engine.connect() as control:
        acquired = control.execute(
            text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"), {"name": lock_name}
        ).scalar_one()
        if not acquired:
            raise RuntimeError(f"An incremental preview is already running for {job_name}")
        try:
            control.execute(
                text(
                    """
                    INSERT INTO graphsync.sync_run (run_id, job_name, status, trigger_type)
                    VALUES (:run_id, :job_name, 'extracting', 'dry_run')
                    """
                ),
                {"run_id": run_id, "job_name": job_name},
            )
            control.commit()
            source = None
            try:
                source = connect_source(settings)
                event_total = 0
                tombstone_total = 0
                staged_event_total = 0
                duplicate_event_total = 0
                event_files: list[Path] = []
                window_results: list[dict[str, Any]] = []
                for window in windows:
                    class_name = window["class_name"]
                    path = directory / f"{class_name}.jsonl"
                    operations: Counter[str] = Counter()
                    last_position: dict[str, Any] | None = None
                    stage_buffer: list[dict[str, Any]] = []

                    def flush_stage_buffer() -> None:
                        nonlocal staged_event_total, duplicate_event_total
                        if not stage_buffer:
                            return
                        staged = repository.stage_change_events(
                            job_name=job_name,
                            class_name=class_name,
                            window_id=window["window_id"],
                            events=list(stage_buffer),
                        )
                        staged_event_total += int(staged["inserted"])
                        duplicate_event_total += int(staged["duplicates"])
                        stage_buffer.clear()

                    with path.open("w", encoding="utf-8", newline="\n") as stream:
                        for record in _change_iterator(
                            source,
                            settings,
                            window,
                            policies[class_name],
                            metadata[class_name],
                            sorted(columns_by_class[class_name]),
                        ):
                            identity = change_event_identity(job_name, class_name, record)
                            envelope = {
                                "className": class_name,
                                "eventId": identity["eventKey"],
                                "payloadHash": identity["payloadHash"],
                                **record.as_dict(),
                            }
                            stream.write(json.dumps(envelope, ensure_ascii=False, default=_json_default) + "\n")
                            stage_buffer.append({
                                "event_key": identity["eventKey"],
                                "operation": record.operation,
                                "source_primary_key": record.key,
                                "source_position": record.position,
                                "row_payload": record.row,
                                "payload_hash": identity["payloadHash"],
                            })
                            if len(stage_buffer) >= 1000:
                                flush_stage_buffer()
                            operations[record.operation] += 1
                            event_total += 1
                            tombstone_total += int(record.operation == "delete")
                            last_position = record.position
                        flush_stage_buffer()
                    with path.open("r", encoding="utf-8") as stream:
                        for line in stream:
                            json.loads(line)
                    event_files.append(path)
                    result = {
                        "windowId": str(window["window_id"]),
                        "className": class_name,
                        "adapter": window["adapter"],
                        "events": sum(operations.values()),
                        "tombstones": operations["delete"],
                        "operations": dict(operations),
                        "lastPosition": last_position,
                        "file": str(path),
                        "sha256": _sha256(path),
                    }
                    window_results.append(result)
                    control.execute(
                        text(
                            """
                            UPDATE graphsync.incremental_window
                            SET status='verified', run_id=:run_id, row_count=:rows,
                                tombstone_count=:tombstones,
                                metadata=metadata || CAST(:metadata AS jsonb)
                            WHERE window_id=:window_id
                            """
                        ),
                        {
                            "run_id": run_id,
                            "rows": result["events"],
                            "tombstones": result["tombstones"],
                            "metadata": json.dumps(
                                {"lastPosition": last_position, "changeFile": str(path)},
                                ensure_ascii=False,
                                default=_json_default,
                            ),
                            "window_id": window["window_id"],
                        },
                    )
                archive_path = _write_change_archive(directory, event_files)
                manifest = {
                    "runId": str(run_id),
                    "jobName": job_name,
                    "sourceKind": settings.source_kind,
                    "windows": window_results,
                    "baselineClasses": [item["class_name"] for item in baseline_windows],
                    "noChangeClasses": [item["class_name"] for item in no_change_windows],
                    "events": event_total,
                    "tombstones": tombstone_total,
                    "stagedEvents": staged_event_total,
                    "duplicateEvents": duplicate_event_total,
                    "archive": str(archive_path),
                    "archiveSha256": _sha256(archive_path),
                    "previewOnly": True,
                    "graphStudioMutated": False,
                    "checkpointCommitted": False,
                }
                manifest_path = directory / "manifest.json"
                manifest_path.write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2, default=_json_default) + "\n",
                    encoding="utf-8",
                )
                control.execute(
                    text(
                        """
                        UPDATE graphsync.sync_run
                        SET status='succeeded', finished_at=now(), row_count=:rows,
                            metrics=CAST(:metrics AS jsonb), manifest_hash=:manifest_hash,
                            source_high_watermark=CAST(:source_high_watermark AS jsonb)
                        WHERE run_id=:run_id
                        """
                    ),
                    {
                        "run_id": run_id,
                        "rows": event_total,
                        "manifest_hash": _sha256(manifest_path),
                        "source_high_watermark": json.dumps(
                            {window["class_name"]: window["upper_bound"] for window in windows},
                            ensure_ascii=False,
                            default=_json_default,
                        ),
                        "metrics": json.dumps(
                            {
                                "operation": "incremental_change_preview",
                                "events": event_total,
                                "tombstones": tombstone_total,
                                "stagedEvents": staged_event_total,
                                "duplicateEvents": duplicate_event_total,
                                "graphStudioMutated": False,
                                "checkpointCommitted": False,
                            }
                        ),
                    },
                )
                control.execute(
                    text(
                        """
                        INSERT INTO graphsync.artifact
                            (artifact_id, run_id, artifact_type, storage_path,
                             sha256, byte_size, metadata)
                        VALUES
                            (:artifact_id, :run_id, 'manifest', :storage_path,
                             :sha256, :byte_size, CAST(:metadata AS jsonb))
                        """
                    ),
                    {
                        "artifact_id": uuid.uuid4(),
                        "run_id": run_id,
                        "storage_path": str(manifest_path),
                        "sha256": _sha256(manifest_path),
                        "byte_size": manifest_path.stat().st_size,
                        "metadata": json.dumps(
                            {
                                "mode": "incremental_change_preview",
                                "archive": str(archive_path),
                                "archiveSha256": manifest["archiveSha256"],
                                "checkpointCommitted": False,
                            },
                            ensure_ascii=False,
                        ),
                    },
                )
                control.commit()
                return manifest
            except Exception as exc:
                control.rollback()
                control.execute(
                    text(
                        """
                        UPDATE graphsync.sync_run SET status='failed', finished_at=now(),
                            error=CAST(:error AS jsonb) WHERE run_id=:run_id
                        """
                    ),
                    {
                        "run_id": run_id,
                        "error": json.dumps({"type": type(exc).__name__, "message": str(exc)[:4000]}),
                    },
                )
                for window in windows:
                    control.execute(
                        text(
                            """
                            UPDATE graphsync.incremental_window SET status='failed',
                                run_id=:run_id, error=CAST(:error AS jsonb)
                            WHERE window_id=:window_id
                            """
                        ),
                        {
                            "run_id": run_id,
                            "window_id": window["window_id"],
                            "error": json.dumps(
                                {"type": type(exc).__name__, "message": str(exc)[:4000]}
                            ),
                        },
                    )
                control.commit()
                raise
            finally:
                if source is not None:
                    source.close()
        finally:
            control.execute(
                text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"), {"name": lock_name}
            )
            control.commit()
