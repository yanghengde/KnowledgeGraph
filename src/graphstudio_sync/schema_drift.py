"""Live Camstar schema observation and governed drift recommendations."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections import defaultdict
from typing import Any, Iterable

from sqlalchemy import text

from .config import SyncSettings
from .connections import resolved_settings
from src.graphstudio_sync.storage.repository import ControlPlaneRepository
from .source_database import ORACLE_KIND, connect_source, fetch_dicts, source_cursor


TYPE_FAMILIES = {
    "string": "text", "text": "text", "char": "text", "varchar": "text",
    "nvarchar": "text", "nchar": "text", "clob": "text", "nclob": "text",
    "integer": "integer", "int": "integer", "bigint": "integer", "smallint": "integer",
    "tinyint": "integer", "long": "integer",
    "decimal": "decimal", "numeric": "decimal", "number": "decimal", "float": "decimal",
    "double": "decimal", "real": "decimal", "money": "decimal", "smallmoney": "decimal",
    "boolean": "boolean", "bit": "boolean",
    "date": "date", "datetime": "datetime", "datetime2": "datetime",
    "smalldatetime": "datetime", "timestamp": "binary", "datetimeoffset": "datetime",
    "binary": "binary", "varbinary": "binary", "blob": "binary", "raw": "binary",
    "uniqueidentifier": "identifier", "uuid": "identifier",
}

# Camstar infrastructure columns are intentionally excluded from ontology
# property suggestions. They remain available to extraction/checkpoint logic.
SYSTEM_SOURCE_COLUMNS = {
    "cdotypeid", "changecount", "exportimportkey",
}


def _type_family(value: Any) -> str:
    rendered = str(value or "string").strip().casefold()
    rendered = re.sub(r"\(.*\)$", "", rendered)
    return TYPE_FAMILIES.get(rendered, rendered)


def _ontology_type(source_type: Any) -> str:
    return {
        "text": "String", "integer": "Integer", "decimal": "Decimal",
        "boolean": "Boolean", "date": "Date", "datetime": "DateTime",
        "binary": "Binary", "identifier": "String",
    }.get(_type_family(source_type), "String")


def _types_compatible(contract_type: Any, source_type: Any) -> bool:
    rendered = str(contract_type or "").casefold()
    actual = _type_family(source_type)
    if rendered == "navigation":
        # Camstar navigation properties are stored as scalar FK columns.  Their
        # physical char/int representation is not a semantic type drift.
        return actual in {"text", "identifier", "integer", "decimal"}
    expected = _type_family(contract_type)
    return expected == actual or (expected == "text" and actual == "identifier")


def _target_name(column: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+|_+", column) if part]
    if not parts:
        return column
    return parts[0][:1].lower() + parts[0][1:] + "".join(
        part[:1].upper() + part[1:] for part in parts[1:]
    )


def compare_contract_schema(
    contract: dict[str, Any],
    fields: Iterable[dict[str, Any]],
    observed_columns: Iterable[dict[str, Any]],
    previous_columns: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Compare one versioned contract with the physical table seen right now."""

    fields = list(fields)
    observed_columns = list(observed_columns)
    actual = {str(item["column_name"]).casefold(): item for item in observed_columns}
    previous = {str(item["column_name"]).casefold(): item for item in previous_columns}
    expected = {
        str(item["source_column"]).casefold(): item
        for item in fields
        if item.get("source_column") and item.get("lifecycle_status") != "retired"
    }
    changes: list[dict[str, Any]] = []
    for key, field in expected.items():
        column = actual.get(key)
        if column is None:
            changes.append({
                "kind": "missing_source_column",
                "severity": "blocking",
                "column": field["source_column"],
                "fieldKey": field["field_key"],
                "message": f"契约字段 {field['target_field']} 的物理列 {field['source_column']} 已不存在",
                "suggestedOperation": "deprecate_field",
            })
            continue
        prior_column = previous.get(key)
        physical_type_changed = prior_column is not None and (
            _type_family(prior_column.get("data_type"))
            != _type_family(column.get("data_type"))
        )
        if physical_type_changed:
            changes.append({
                "kind": "type_changed",
                "severity": "blocking",
                "column": column["column_name"],
                "fieldKey": field["field_key"],
                "beforeType": field.get("data_type"),
                "afterType": _ontology_type(column.get("data_type")),
                "physicalType": column.get("data_type"),
                "message": f"物理类型 {column.get('data_type')} 与契约类型 {field.get('data_type')} 不兼容",
                "suggestedOperation": "change_type",
            })
        elif not _types_compatible(field.get("data_type"), column.get("data_type")):
            changes.append({
                "kind": "contract_type_mismatch",
                "severity": "warning",
                "column": column["column_name"],
                "fieldKey": field["field_key"],
                "beforeType": field.get("data_type"),
                "afterType": _ontology_type(column.get("data_type")),
                "physicalType": column.get("data_type"),
                "message": f"当前契约类型 {field.get('data_type')} 与物理类型 {column.get('data_type')} 不同；这是基线对齐提醒，不表示源库刚刚发生变化",
                "suggestedOperation": "change_type",
            })
        if field.get("required") and bool(column.get("nullable")):
            changes.append({
                "kind": "nullable_relaxed",
                "severity": "warning",
                "column": column["column_name"],
                "fieldKey": field["field_key"],
                "message": "契约要求必填，但物理列允许 NULL；发布前需继续执行数据质量门禁",
                "suggestedOperation": None,
            })
    for key, column in actual.items():
        if key in expected or key in SYSTEM_SOURCE_COLUMNS:
            continue
        target = _target_name(str(column["column_name"]))
        changes.append({
            "kind": "candidate_column",
            "severity": "info",
            "column": column["column_name"],
            "fieldKey": f"{contract['contract_key']}:{target}",
            "message": "发现尚未进入发布契约的物理列，可按需添加，不会自动发布",
            "suggestedOperation": "add_field",
            "suggestedAfterState": {
                "source_column": column["column_name"],
                "target_field": target,
                "data_type": _ontology_type(column.get("data_type")),
                "nullable": bool(column.get("nullable", True)),
                "required": False,
            },
        })
    blockers = sum(item["severity"] == "blocking" for item in changes)
    warnings = sum(item["severity"] == "warning" for item in changes)
    candidates = sum(item["kind"] == "candidate_column" for item in changes)
    return {
        "contractKey": contract["contract_key"],
        "className": contract["class_name"],
        "contractVersion": int(contract["version"]),
        "source": f"{contract['source_schema']}.{contract['source_table']}",
        "status": "drifted" if blockers else "stable",
        "blockers": blockers,
        "warnings": warnings,
        "candidates": candidates,
        "changes": changes,
    }


def _read_source_columns(settings: SyncSettings) -> list[dict[str, Any]]:
    source = connect_source(settings)
    cursor = source_cursor(source, settings.source_kind)
    try:
        if settings.source_kind == ORACLE_KIND:
            cursor.execute(
                """
                SELECT OWNER AS "schema_name", TABLE_NAME AS "table_name",
                       COLUMN_NAME AS "column_name", DATA_TYPE AS "data_type",
                       CASE WHEN NULLABLE='Y' THEN 1 ELSE 0 END AS "nullable",
                       DATA_DEFAULT AS "default_expression", COLUMN_ID AS "ordinal_position"
                FROM ALL_TAB_COLUMNS
                WHERE OWNER=:owner
                ORDER BY TABLE_NAME, COLUMN_ID
                """,
                {"owner": (settings.source_schema or settings.source_user).upper()},
            )
        else:
            cursor.execute(
                """
                SELECT TABLE_SCHEMA AS schema_name, TABLE_NAME AS table_name,
                       COLUMN_NAME AS column_name, DATA_TYPE AS data_type,
                       CASE WHEN IS_NULLABLE='YES' THEN 1 ELSE 0 END AS nullable,
                       COLUMN_DEFAULT AS default_expression,
                       ORDINAL_POSITION AS ordinal_position
                FROM INFORMATION_SCHEMA.COLUMNS
                ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
                """
            )
        return fetch_dicts(cursor)
    finally:
        cursor.close()
        source.close()


def scan_schema_drift(
    base_settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
) -> dict[str, Any]:
    settings = resolved_settings(base_settings, repository)
    governance = repository.governance_profile(profile_key)
    columns = _read_source_columns(settings)
    by_table: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in columns:
        by_table[(str(item["schema_name"]).casefold(), str(item["table_name"]).casefold())].append(item)
    observations: list[dict[str, Any]] = []
    with repository.engine.begin() as connection:
        for contract in governance.get("contracts") or []:
            schema = repository.contract_schema(contract["contract_key"])
            table_columns = by_table.get((
                str(contract["source_schema"]).casefold(),
                str(contract["source_table"]).casefold(),
            ), [])
            previous_columns = connection.execute(
                text(
                    """
                    SELECT columns FROM graphsync.source_schema_observation
                    WHERE profile_key=:profile AND contract_key=:contract
                    ORDER BY observed_at DESC LIMIT 1
                    """
                ),
                {"profile": profile_key, "contract": contract["contract_key"]},
            ).scalar_one_or_none() or []
            result = compare_contract_schema(
                contract, schema["fields"], table_columns, previous_columns,
            )
            canonical = json.dumps(table_columns, ensure_ascii=False, sort_keys=True, default=str)
            schema_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            observation_id = uuid.uuid4()
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.source_schema_observation
                        (observation_id, profile_key, contract_key, source_schema,
                         source_table, schema_hash, status, columns, drift)
                    VALUES (:id, :profile, :contract, :schema, :table, :hash,
                            :status, CAST(:columns AS jsonb), CAST(:drift AS jsonb))
                    """
                ),
                {
                    "id": observation_id, "profile": profile_key,
                    "contract": contract["contract_key"],
                    "schema": contract["source_schema"], "table": contract["source_table"],
                    "hash": schema_hash, "status": result["status"],
                    "columns": canonical,
                    "drift": json.dumps(result, ensure_ascii=False, default=str),
                },
            )
            observations.append({"observationId": str(observation_id), **result})
    return _drift_summary(observations)


def latest_schema_drift(
    repository: ControlPlaneRepository, *, profile_key: str,
) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        rows = [dict(row) for row in connection.execute(
            text(
                """
                SELECT DISTINCT ON (contract_key)
                       observation_id, observed_at, drift
                FROM graphsync.source_schema_observation
                WHERE profile_key=:profile
                ORDER BY contract_key, observed_at DESC
                """
            ),
            {"profile": profile_key},
        ).mappings()]
    observations = [
        {"observationId": str(row["observation_id"]), "observedAt": row["observed_at"], **dict(row["drift"] or {})}
        for row in rows
    ]
    return _drift_summary(observations)


def _drift_summary(observations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scanned": bool(observations),
        "summary": {
            "contracts": len(observations),
            "stable": sum(item.get("status") == "stable" for item in observations),
            "drifted": sum(item.get("status") == "drifted" for item in observations),
            "blockers": sum(int(item.get("blockers") or 0) for item in observations),
            "warnings": sum(int(item.get("warnings") or 0) for item in observations),
            "candidates": sum(int(item.get("candidates") or 0) for item in observations),
        },
        "items": observations,
    }
