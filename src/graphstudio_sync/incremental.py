"""Read-only incremental source discovery and bounded window planning.

This module never extracts business rows and never mutates Graph Studio.  It proves
which database-native change mechanisms are available and freezes an upper bound
before a later extractor is allowed to run.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .config import SyncSettings
from .source_database import (
    ORACLE_KIND,
    SQLSERVER_KIND,
    connect_source,
    fetchmany_dicts,
    quote_identifier,
    source_cursor,
)

if False:  # pragma: no cover - type checking without a runtime import cycle
    from .repository import ControlPlaneRepository


def _json_value(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "0x" + bytes(value).hex()
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _query(connection, kind: str, sql: str, parameters: Any = None) -> list[dict[str, Any]]:
    cursor = source_cursor(connection, kind)
    try:
        cursor.execute(sql, parameters or ({} if kind == ORACLE_KIND else ()))
        rows: list[dict[str, Any]] = []
        while True:
            page = fetchmany_dicts(cursor, 1000)
            if not page:
                break
            rows.extend(page)
        return [{key: _json_value(value) for key, value in row.items()} for row in rows]
    finally:
        cursor.close()


def _query_optional(connection, kind: str, sql: str) -> tuple[list[dict[str, Any]], str | None]:
    try:
        return _query(connection, kind, sql), None
    except Exception as exc:  # permissions and optional database features vary by installation
        return [], str(exc).splitlines()[0][:1000]


def _sqlserver_probe(connection) -> dict[str, Any]:
    database = _query(
        connection,
        SQLSERVER_KIND,
        """
        SELECT DB_NAME() AS database_name,
               d.snapshot_isolation_state_desc,
               d.is_read_committed_snapshot_on,
               d.is_cdc_enabled,
               CHANGE_TRACKING_CURRENT_VERSION() AS change_tracking_current_version
        FROM sys.databases d
        WHERE d.name = DB_NAME()
        """,
    )[0]
    ct_rows, ct_error = _query_optional(
        connection,
        SQLSERVER_KIND,
        """
        SELECT s.name AS schema_name, t.name AS table_name,
               ct.begin_version, ct.cleanup_version, ct.min_valid_version,
               ct.is_track_columns_updated_on
        FROM sys.change_tracking_tables ct
        JOIN sys.tables t ON t.object_id = ct.object_id
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        """,
    )
    cdc_rows: list[dict[str, Any]] = []
    cdc_error: str | None = None
    cdc_max_lsn: Any = None
    if bool(database.get("is_cdc_enabled")):
        cdc_rows, cdc_error = _query_optional(
            connection,
            SQLSERVER_KIND,
            """
            SELECT s.name AS schema_name, t.name AS table_name,
                   ct.capture_instance, ct.start_lsn
            FROM cdc.change_tables ct
            JOIN sys.tables t ON t.object_id = ct.source_object_id
            JOIN sys.schemas s ON s.schema_id = t.schema_id
            """,
        )
        max_rows, max_error = _query_optional(
            connection,
            SQLSERVER_KIND,
            "SELECT sys.fn_cdc_get_max_lsn() AS cdc_max_lsn",
        )
        cdc_error = cdc_error or max_error
        if max_rows:
            cdc_max_lsn = max_rows[0].get("cdc_max_lsn")
    return {
        "sourcePosition": {
            "changeTrackingVersion": database.get("change_tracking_current_version"),
            "cdcMaxLsn": cdc_max_lsn,
        },
        "capabilities": {
            "snapshotIsolation": database.get("snapshot_isolation_state_desc"),
            "readCommittedSnapshot": bool(database.get("is_read_committed_snapshot_on")),
            "changeTrackingEnabled": database.get("change_tracking_current_version") is not None,
            "cdcEnabled": bool(database.get("is_cdc_enabled")),
            "changeTrackingProbeError": ct_error,
            "cdcProbeError": cdc_error,
        },
        "changeTrackingTables": ct_rows,
        "cdcTables": cdc_rows,
    }


def _oracle_probe(connection) -> dict[str, Any]:
    scn_rows, scn_error = _query_optional(
        connection,
        ORACLE_KIND,
        "SELECT DBMS_FLASHBACK.GET_SYSTEM_CHANGE_NUMBER AS current_scn FROM dual",
    )
    undo_rows, undo_error = _query_optional(
        connection,
        ORACLE_KIND,
        "SELECT value AS undo_retention_seconds FROM v$parameter WHERE name = 'undo_retention'",
    )
    dependency_rows, dependency_error = _query_optional(
        connection,
        ORACLE_KIND,
        "SELECT owner AS schema_name, table_name, dependencies FROM all_tables",
    )
    current_scn = scn_rows[0].get("CURRENT_SCN") if scn_rows else None
    if current_scn is None and scn_rows:
        current_scn = scn_rows[0].get("current_scn")
    undo_retention = None
    if undo_rows:
        undo_retention = next(iter(undo_rows[0].values()), None)
    return {
        "sourcePosition": {"scn": current_scn},
        "capabilities": {
            "flashbackScnAvailable": current_scn is not None,
            "flashbackScnProbeError": scn_error,
            "undoRetentionSeconds": int(undo_retention) if str(undo_retention or "").isdigit() else None,
            "undoRetentionProbeError": undo_error,
            "rowDependenciesProbeError": dependency_error,
        },
        "oracleTables": dependency_rows,
    }


def _table_lookup(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("schema_name") or row.get("SCHEMA_NAME") or "").casefold(),
         str(row.get("table_name") or row.get("TABLE_NAME") or "").casefold()): row
        for row in rows
    }


def probe_incremental_capabilities(
    settings: SyncSettings,
    policies: list[dict[str, Any]],
) -> dict[str, Any]:
    connection = connect_source(settings)
    try:
        raw = _oracle_probe(connection) if settings.source_kind == ORACLE_KIND else _sqlserver_probe(connection)
        oracle_flashback_validation: dict[str, str | None] = {}
        if settings.source_kind == ORACLE_KIND and raw["sourcePosition"].get("scn") is not None:
            scn = int(raw["sourcePosition"]["scn"])
            for policy in policies:
                if policy.get("effective_strategy") != "cdc" or not policy.get("enabled", True):
                    continue
                try:
                    _query(
                        connection,
                        ORACLE_KIND,
                        f"SELECT COUNT(*) AS probe_count FROM "
                        f"{quote_identifier(policy['physical_schema'], ORACLE_KIND)}."
                        f"{quote_identifier(policy['physical_table'], ORACLE_KIND)} "
                        f"VERSIONS BETWEEN SCN {scn} AND {scn} WHERE 1=0",
                    )
                    oracle_flashback_validation[policy["class_name"]] = None
                except Exception as exc:
                    oracle_flashback_validation[policy["class_name"]] = str(exc).splitlines()[0][:1000]
    finally:
        connection.close()

    ct_lookup = _table_lookup(raw.pop("changeTrackingTables", []))
    cdc_lookup = _table_lookup(raw.pop("cdcTables", []))
    oracle_lookup = _table_lookup(raw.pop("oracleTables", []))
    tables: list[dict[str, Any]] = []
    for policy in policies:
        key = (str(policy["physical_schema"]).casefold(), str(policy["physical_table"]).casefold())
        ct = ct_lookup.get(key)
        cdc = cdc_lookup.get(key)
        oracle = oracle_lookup.get(key)
        if settings.source_kind == SQLSERVER_KIND:
            adapter = "sqlserver_change_tracking" if ct else "sqlserver_cdc" if cdc else None
            detail = {
                "changeTracking": ct,
                "cdc": cdc,
            }
        else:
            flashback_error = oracle_flashback_validation.get(policy["class_name"])
            flashback_validated = (
                policy.get("effective_strategy") == "cdc"
                and policy["class_name"] in oracle_flashback_validation
                and flashback_error is None
            )
            adapter = "oracle_flashback_scn" if flashback_validated else None
            detail = {
                "rowDependencies": (
                    oracle.get("DEPENDENCIES") if oracle else None
                ),
                "flashbackVersionsValidated": flashback_validated,
                "flashbackVersionsError": flashback_error,
            }
        tables.append(
            {
                "className": policy["class_name"],
                "schema": policy["physical_schema"],
                "table": policy["physical_table"],
                "strategy": policy.get("effective_strategy"),
                "nativeAdapter": adapter,
                "nativeChangeCaptureReady": adapter is not None,
                **detail,
            }
        )
    return {
        "sourceKind": settings.source_kind,
        "capturedAt": datetime.now(timezone.utc).isoformat(),
        "sourcePosition": raw["sourcePosition"],
        "capabilities": raw["capabilities"],
        "tables": tables,
    }


def read_watermark_upper_bound(
    settings: SyncSettings,
    *,
    schema: str,
    table: str,
    watermark_column: str,
) -> Any:
    connection = connect_source(settings)
    try:
        rows = _query(
            connection,
            settings.source_kind,
            f"SELECT MAX({quote_identifier(watermark_column, settings.source_kind)}) AS upper_bound "
            f"FROM {quote_identifier(schema, settings.source_kind)}."
            f"{quote_identifier(table, settings.source_kind)}",
        )
    finally:
        connection.close()
    if not rows:
        return None
    return rows[0].get("upper_bound", rows[0].get("UPPER_BOUND"))


def _hex_before(left: Any, right: Any) -> bool:
    if not isinstance(left, str) or not isinstance(right, str):
        return False
    if not left.startswith("0x") or not right.startswith("0x"):
        return False
    return bytes.fromhex(left[2:]) < bytes.fromhex(right[2:])


def plan_incremental_windows(
    settings: SyncSettings,
    policies: list[dict[str, Any]],
    capability_snapshot: dict[str, Any],
    checkpoints: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    table_capabilities = {item["className"]: item for item in capability_snapshot["tables"]}
    source_position = capability_snapshot["sourcePosition"]
    windows: list[dict[str, Any]] = []
    for policy in policies:
        strategy = policy.get("effective_strategy")
        if not policy.get("enabled", True) or strategy not in {"watermark", "append_only", "cdc"}:
            continue
        class_name = policy["class_name"]
        capability = table_capabilities[class_name]
        checkpoint = checkpoints.get(class_name)
        lower = checkpoint.get("committed_watermark") if checkpoint else None
        adapter: str
        upper: dict[str, Any]
        status = "planned" if lower else "baseline_required"
        reason: str | None = None
        if strategy in {"watermark", "append_only"}:
            adapter = "database_watermark"
            value = read_watermark_upper_bound(
                settings,
                schema=policy["physical_schema"],
                table=policy["physical_table"],
                watermark_column=policy["watermark_column"],
            )
            upper = {"watermark": _json_value(value), "column": policy["watermark_column"]}
        else:
            adapter = capability.get("nativeAdapter") or "unavailable"
            if adapter == "sqlserver_change_tracking":
                upper = {"changeTrackingVersion": source_position.get("changeTrackingVersion")}
                minimum = (capability.get("changeTracking") or {}).get("min_valid_version")
                if lower and minimum is not None and int(lower.get("changeTrackingVersion", -1)) < int(minimum):
                    status, reason = "blocked", "checkpoint_before_min_valid_change_tracking_version"
            elif adapter == "sqlserver_cdc":
                upper = {"cdcLsn": source_position.get("cdcMaxLsn")}
                minimum = (capability.get("cdc") or {}).get("start_lsn")
                if lower and minimum and _hex_before(lower.get("cdcLsn"), minimum):
                    status, reason = "blocked", "checkpoint_before_min_valid_cdc_lsn"
            elif adapter == "oracle_flashback_scn":
                upper = {"scn": source_position.get("scn")}
            else:
                upper = {"unavailable": True}
                status, reason = "blocked", "native_change_capture_not_enabled"
        if not any(value is not None and value is not False for value in upper.values()):
            status, reason = "blocked", reason or "source_upper_bound_unavailable"
        windows.append(
            {
                "class_name": class_name,
                "strategy": strategy,
                "adapter": adapter,
                "status": status,
                "lower_bound": lower,
                "upper_bound": upper,
                "metadata": {"reason": reason} if reason else {},
            }
        )
    return windows


def execute_incremental_probe(
    base_settings: SyncSettings,
    repository: "ControlPlaneRepository",
    *,
    job_name: str,
) -> dict[str, Any]:
    from .connections import resolved_settings

    settings = resolved_settings(base_settings, repository)
    policies = repository.list_table_policies(job_name)
    probe = probe_incremental_capabilities(settings, policies)
    recorded = repository.record_source_capabilities(probe)
    ready_tables = sum(bool(item["nativeChangeCaptureReady"]) for item in probe["tables"])
    return {
        **probe,
        "snapshotId": str(recorded["snapshot_id"]),
        "summary": {
            "mappedTables": len(probe["tables"]),
            "nativeChangeCaptureReady": ready_tables,
            "nativeChangeCaptureUnavailable": len(probe["tables"]) - ready_tables,
        },
    }


def execute_incremental_plan(
    base_settings: SyncSettings,
    repository: "ControlPlaneRepository",
    *,
    job_name: str,
    refresh_capabilities: bool = True,
) -> dict[str, Any]:
    from .connections import resolved_settings

    settings = resolved_settings(base_settings, repository)
    if refresh_capabilities:
        probe = execute_incremental_probe(base_settings, repository, job_name=job_name)
        snapshot_id = probe["snapshotId"]
    else:
        probe = repository.latest_source_capabilities()
        if probe is None:
            raise RuntimeError("No source capability snapshot exists; run probe-incremental first")
        snapshot_id = str(probe["snapshot_id"])
    policies = repository.list_table_policies(job_name)
    checkpoints = repository.checkpoints_by_partition(job_name)
    windows = plan_incremental_windows(settings, policies, probe, checkpoints)
    recorded = repository.record_incremental_windows(job_name, snapshot_id, windows) if windows else []
    statuses: dict[str, int] = {}
    for item in windows:
        statuses[item["status"]] = statuses.get(item["status"], 0) + 1
    return {
        "jobName": job_name,
        "capabilitySnapshotId": snapshot_id,
        "sourceKind": probe["sourceKind"],
        "sourcePosition": probe["sourcePosition"],
        "windows": windows,
        "recordedWindowIds": [str(item["window_id"]) for item in recorded],
        "summary": {"incrementalTables": len(windows), "statuses": statuses},
        "previewOnly": True,
        "graphStudioMutated": False,
    }
