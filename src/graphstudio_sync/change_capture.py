"""Bounded, resumable change readers for supported Camstar databases."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Iterator, Literal

from .source_database import ORACLE_KIND, SQLSERVER_KIND, fetchmany_dicts, source_cursor


ChangeOperation = Literal["insert", "update", "upsert", "delete"]


@dataclass(frozen=True)
class ChangeRecord:
    operation: ChangeOperation
    key: dict[str, Any]
    row: dict[str, Any] | None
    position: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_change_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def change_event_identity(
    job_name: str,
    class_name: str,
    record: ChangeRecord | dict[str, Any],
) -> dict[str, str]:
    """Build the stable inbox identity for one at-least-once source event.

    The row payload is deliberately excluded from ``eventKey``. Re-reading the
    same source position must resolve to the same identity; ``payloadHash`` is
    compared separately so a source adapter cannot silently return different
    values for one immutable position.
    """

    data = record.as_dict() if isinstance(record, ChangeRecord) else dict(record)
    identity = {
        "jobName": job_name,
        "className": class_name,
        "operation": data["operation"],
        "key": data["key"],
        "position": data["position"],
    }
    event_key = hashlib.sha256(_canonical_change_json(identity).encode("utf-8")).hexdigest()
    payload_hash = hashlib.sha256(
        _canonical_change_json(data.get("row")).encode("utf-8")
    ).hexdigest()
    return {"eventKey": event_key, "payloadHash": payload_hash}


def _identifier(value: str, kind: str, alias: str | None = None) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$#]*", value):
        raise ValueError(f"Unsafe source identifier: {value!r}")
    quoted = f'"{value}"' if kind == ORACLE_KIND else f"[{value}]"
    return f"{alias}.{quoted}" if alias else quoted


def _table(schema: str, table: str, kind: str) -> str:
    return f"{_identifier(schema, kind)}.{_identifier(table, kind)}"


def _hex(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "0x" + bytes(value).hex()
    return value


def _binary(value: str | bytes) -> bytes:
    if isinstance(value, bytes):
        return value
    if not value.startswith("0x"):
        raise ValueError("SQL Server LSN/seqval must use a 0x-prefixed hex value")
    return bytes.fromhex(value[2:])


def _fetch_page(cursor, size: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    while len(rows) < size:
        page = fetchmany_dicts(cursor, min(size - len(rows), 10_000))
        if not page:
            break
        rows.extend(page)
    return rows


def _sqlserver_tuple_after(
    columns: list[str],
    values: list[Any],
    *,
    aliases: list[str] | None = None,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    parameters: list[Any] = []
    aliases = aliases or [""] * len(columns)
    for index, column in enumerate(columns):
        parts: list[str] = []
        for prior in range(index):
            parts.append(f"{_identifier(columns[prior], SQLSERVER_KIND, aliases[prior] or None)} = %s")
            parameters.append(values[prior])
        parts.append(f"{_identifier(column, SQLSERVER_KIND, aliases[index] or None)} > %s")
        parameters.append(values[index])
        clauses.append("(" + " AND ".join(parts) + ")")
    return "(" + " OR ".join(clauses) + ")", parameters


def _oracle_tuple_after(columns: list[str], values: list[Any], *, alias: str = "T") -> tuple[str, dict[str, Any]]:
    clauses: list[str] = []
    parameters: dict[str, Any] = {}
    for index, column in enumerate(columns):
        parts: list[str] = []
        for prior in range(index):
            name = f"after_{index}_{prior}"
            parts.append(f"{_identifier(columns[prior], ORACLE_KIND, alias)} = :{name}")
            parameters[name] = values[prior]
        name = f"after_{index}_{index}"
        parts.append(f"{_identifier(column, ORACLE_KIND, alias)} > :{name}")
        parameters[name] = values[index]
        clauses.append("(" + " AND ".join(parts) + ")")
    return "(" + " OR ".join(clauses) + ")", parameters


def iter_sqlserver_change_tracking(
    connection,
    *,
    schema: str,
    table: str,
    columns: list[str],
    primary_keys: list[str],
    lower_version: int,
    upper_version: int,
    fetch_size: int,
    start_after: dict[str, Any] | None = None,
) -> Iterator[ChangeRecord]:
    """Read CT keys and current values without ever scanning the base table."""
    cursor = source_cursor(connection, SQLSERVER_KIND)
    selected_non_keys = [column for column in dict.fromkeys(columns) if column not in primary_keys]
    select_keys = ", ".join(
        f"{_identifier(column, SQLSERVER_KIND, 'CT')} AS {_identifier(column, SQLSERVER_KIND)}"
        for column in primary_keys
    )
    select_values = ", ".join(
        f"{_identifier(column, SQLSERVER_KIND, 'T')} AS {_identifier(column, SQLSERVER_KIND)}"
        for column in selected_non_keys
    )
    select_list = ", ".join(
        part for part in [
            "CT.SYS_CHANGE_VERSION AS [__change_version]",
            "CT.SYS_CHANGE_OPERATION AS [__change_operation]",
            select_keys,
            select_values,
        ] if part
    )
    join = " AND ".join(
        f"{_identifier(column, SQLSERVER_KIND, 'T')} = {_identifier(column, SQLSERVER_KIND, 'CT')}"
        for column in primary_keys
    )
    after = dict(start_after) if start_after else None
    try:
        while True:
            predicates = ["CT.SYS_CHANGE_VERSION <= %s"]
            parameters: list[Any] = [int(upper_version)]
            if after:
                tuple_sql, tuple_parameters = _sqlserver_tuple_after(
                    ["SYS_CHANGE_VERSION", *primary_keys],
                    [after["changeTrackingVersion"], *[after["primaryKey"][key] for key in primary_keys]],
                    aliases=["CT"] * (len(primary_keys) + 1),
                )
                predicates.append(tuple_sql)
                parameters.extend(tuple_parameters)
            order = ", ".join(
                ["CT.SYS_CHANGE_VERSION", *[_identifier(key, SQLSERVER_KIND, "CT") for key in primary_keys]]
            )
            sql = (
                f"SELECT TOP ({int(fetch_size)}) {select_list} "
                f"FROM CHANGETABLE(CHANGES {_table(schema, table, SQLSERVER_KIND)}, %s) AS CT "
                f"LEFT JOIN {_table(schema, table, SQLSERVER_KIND)} AS T ON {join} "
                f"WHERE {' AND '.join(predicates)} ORDER BY {order}"
            )
            cursor.execute(sql, (int(lower_version), *parameters))
            page = _fetch_page(cursor, fetch_size)
            if not page:
                break
            last_version = int(page[-1]["__change_version"])
            last_key = {column: page[-1][column] for column in primary_keys}
            for row in page:
                version = int(row.pop("__change_version"))
                raw_operation = str(row.pop("__change_operation")).strip().upper()
                key = {column: row[column] for column in primary_keys}
                position = {"changeTrackingVersion": version, "primaryKey": key}
                operation: ChangeOperation = {"I": "insert", "U": "update", "D": "delete"}[raw_operation]
                yield ChangeRecord(operation, key, None if operation == "delete" else row, position)
            after = {
                "changeTrackingVersion": last_version,
                "primaryKey": last_key,
            }
            if len(page) < fetch_size:
                break
    finally:
        cursor.close()


def iter_sqlserver_cdc(
    connection,
    *,
    capture_instance: str,
    columns: list[str],
    primary_keys: list[str],
    lower_lsn: str,
    upper_lsn: str,
    fetch_size: int,
    start_after: dict[str, Any] | None = None,
) -> Iterator[ChangeRecord]:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", capture_instance):
        raise ValueError(f"Unsafe CDC capture instance: {capture_instance!r}")
    cursor = source_cursor(connection, SQLSERVER_KIND)
    selected = list(dict.fromkeys([*primary_keys, *columns]))
    select_values = ", ".join(_identifier(column, SQLSERVER_KIND, "C") for column in selected)
    after = dict(start_after) if start_after else None
    try:
        while True:
            predicates = ["C.[__$operation] IN (1, 2, 4)"]
            parameters: list[Any] = [_binary(lower_lsn), _binary(upper_lsn)]
            if after:
                tuple_sql, tuple_parameters = _sqlserver_tuple_after(
                    ["__$start_lsn", "__$seqval", "__$operation"],
                    [_binary(after["cdcLsn"]), _binary(after["seqval"]), int(after["operationCode"])],
                    aliases=["C", "C", "C"],
                )
                predicates.append(tuple_sql)
                parameters.extend(tuple_parameters)
            sql = (
                f"SELECT TOP ({int(fetch_size)}) C.[__$start_lsn] AS [__start_lsn], "
                f"C.[__$seqval] AS [__seqval], C.[__$operation] AS [__operation], {select_values} "
                f"FROM cdc.fn_cdc_get_all_changes_{capture_instance}(%s, %s, 'all') AS C "
                f"WHERE {' AND '.join(predicates)} "
                f"ORDER BY C.[__$start_lsn], C.[__$seqval], C.[__$operation]"
            )
            cursor.execute(sql, tuple(parameters))
            page = _fetch_page(cursor, fetch_size)
            if not page:
                break
            last_position: dict[str, Any] | None = None
            for row in page:
                position = {
                    "cdcLsn": _hex(row.pop("__start_lsn")),
                    "seqval": _hex(row.pop("__seqval")),
                    "operationCode": int(row.pop("__operation")),
                }
                key = {column: row[column] for column in primary_keys}
                operation = {1: "delete", 2: "insert", 4: "update"}[position["operationCode"]]
                yield ChangeRecord(operation, key, None if operation == "delete" else row, position)
                last_position = position
            after = last_position
            if len(page) < fetch_size:
                break
    finally:
        cursor.close()


def iter_watermark_changes(
    connection,
    *,
    kind: str,
    schema: str,
    table: str,
    columns: list[str],
    primary_keys: list[str],
    watermark_column: str,
    lower_bound: Any,
    upper_bound: Any,
    fetch_size: int,
    append_only: bool = False,
    start_after: dict[str, Any] | None = None,
) -> Iterator[ChangeRecord]:
    cursor = source_cursor(connection, kind)
    selected = list(dict.fromkeys([*primary_keys, watermark_column, *columns]))
    select_values = ", ".join(_identifier(column, kind, "T") for column in selected)
    after = dict(start_after) if start_after else None
    try:
        while True:
            if kind == SQLSERVER_KIND:
                predicates = [f"{_identifier(watermark_column, kind, 'T')} <= %s"]
                parameters: list[Any] = [upper_bound]
                cursor_value = after or {"watermark": lower_bound}
                if cursor_value.get("primaryKey"):
                    tuple_sql, tuple_parameters = _sqlserver_tuple_after(
                        [watermark_column, *primary_keys],
                        [cursor_value["watermark"], *[cursor_value["primaryKey"][key] for key in primary_keys]],
                        aliases=["T"] * (len(primary_keys) + 1),
                    )
                    predicates.append(tuple_sql)
                    parameters.extend(tuple_parameters)
                else:
                    predicates.append(f"{_identifier(watermark_column, kind, 'T')} > %s")
                    parameters.append(cursor_value["watermark"])
                order = ", ".join(
                    [_identifier(watermark_column, kind, "T"), *[_identifier(key, kind, "T") for key in primary_keys]]
                )
                sql = (
                    f"SELECT TOP ({int(fetch_size)}) {select_values} FROM {_table(schema, table, kind)} AS T "
                    f"WHERE {' AND '.join(predicates)} ORDER BY {order}"
                )
                cursor.execute(sql, tuple(parameters))
            elif kind == ORACLE_KIND:
                predicates = [f"{_identifier(watermark_column, kind, 'T')} <= :upper_bound"]
                parameters_dict: dict[str, Any] = {"upper_bound": upper_bound}
                cursor_value = after or {"watermark": lower_bound}
                if cursor_value.get("primaryKey"):
                    tuple_sql, tuple_parameters = _oracle_tuple_after(
                        [watermark_column, *primary_keys],
                        [cursor_value["watermark"], *[cursor_value["primaryKey"][key] for key in primary_keys]],
                    )
                    predicates.append(tuple_sql)
                    parameters_dict.update(tuple_parameters)
                else:
                    predicates.append(f"{_identifier(watermark_column, kind, 'T')} > :lower_bound")
                    parameters_dict["lower_bound"] = cursor_value["watermark"]
                order = ", ".join(
                    [_identifier(watermark_column, kind, "T"), *[_identifier(key, kind, "T") for key in primary_keys]]
                )
                sql = (
                    f"SELECT {select_values} FROM {_table(schema, table, kind)} T "
                    f"WHERE {' AND '.join(predicates)} ORDER BY {order} "
                    f"FETCH FIRST {int(fetch_size)} ROWS ONLY"
                )
                cursor.execute(sql, parameters_dict)
            else:
                raise RuntimeError(f"Unsupported source kind: {kind}")
            page = _fetch_page(cursor, fetch_size)
            if not page:
                break
            for row in page:
                key = {column: row[column] for column in primary_keys}
                position = {"watermark": row[watermark_column], "primaryKey": key}
                yield ChangeRecord("insert" if append_only else "upsert", key, row, position)
            last = page[-1]
            after = {
                "watermark": last[watermark_column],
                "primaryKey": {column: last[column] for column in primary_keys},
            }
            if len(page) < fetch_size:
                break
    finally:
        cursor.close()


def iter_oracle_flashback_changes(
    connection,
    *,
    schema: str,
    table: str,
    columns: list[str],
    primary_keys: list[str],
    lower_scn: int,
    upper_scn: int,
    fetch_size: int,
    start_after: dict[str, Any] | None = None,
) -> Iterator[ChangeRecord]:
    cursor = source_cursor(connection, ORACLE_KIND)
    selected = list(dict.fromkeys([*primary_keys, *columns]))
    select_values = ", ".join(_identifier(column, ORACLE_KIND, "T") for column in selected)
    after = dict(start_after) if start_after else None
    try:
        while True:
            predicates = ["VERSIONS_STARTSCN > :lower_scn", "VERSIONS_STARTSCN <= :upper_scn"]
            parameters: dict[str, Any] = {"lower_scn": int(lower_scn), "upper_scn": int(upper_scn)}
            if after:
                clauses = ["VERSIONS_STARTSCN > :after_scn"]
                parameters["after_scn"] = int(after["scn"])
                for index, key in enumerate(primary_keys):
                    parts = ["VERSIONS_STARTSCN = :after_scn"]
                    for prior in range(index):
                        name = f"after_pk_{index}_{prior}"
                        parts.append(f"{_identifier(primary_keys[prior], ORACLE_KIND, 'T')} = :{name}")
                        parameters[name] = after["primaryKey"][primary_keys[prior]]
                    name = f"after_pk_{index}_{index}"
                    parts.append(f"{_identifier(key, ORACLE_KIND, 'T')} > :{name}")
                    parameters[name] = after["primaryKey"][key]
                    clauses.append("(" + " AND ".join(parts) + ")")
                predicates.append("(" + " OR ".join(clauses) + ")")
            order = ", ".join(
                ["VERSIONS_STARTSCN", *[_identifier(key, ORACLE_KIND, "T") for key in primary_keys]]
            )
            sql = (
                f"SELECT VERSIONS_OPERATION AS \"__operation\", "
                f"VERSIONS_STARTSCN AS \"__start_scn\", {select_values} "
                f"FROM {_table(schema, table, ORACLE_KIND)} VERSIONS BETWEEN SCN :lower_scn AND :upper_scn T "
                f"WHERE {' AND '.join(predicates)} ORDER BY {order} "
                f"FETCH FIRST {int(fetch_size)} ROWS ONLY"
            )
            cursor.execute(sql, parameters)
            page = _fetch_page(cursor, fetch_size)
            if not page:
                break
            last_scn = int(page[-1].get("__start_scn", page[-1].get("__START_SCN", 0)))
            last_key = {column: page[-1][column] for column in primary_keys}
            for row in page:
                raw_operation = str(row.pop("__operation", row.pop("__OPERATION", ""))).strip().upper()
                scn = int(row.pop("__start_scn", row.pop("__START_SCN", 0)))
                key = {column: row[column] for column in primary_keys}
                position = {"scn": scn, "primaryKey": key}
                operation: ChangeOperation = {"I": "insert", "U": "update", "D": "delete"}[raw_operation]
                yield ChangeRecord(operation, key, None if operation == "delete" else row, position)
            last = page[-1]
            after = {
                "scn": last_scn,
                "primaryKey": last_key,
            }
            if len(page) < fetch_size:
                break
    finally:
        cursor.close()
