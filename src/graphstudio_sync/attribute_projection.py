"""Generic related-table attributes for governed ontology objects.

The configuration is intentionally relational and declarative: equality joins,
typed fields and a small filter language.  It never accepts raw SQL.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
import datetime as dt
import decimal
from collections import defaultdict
from itertools import islice
from typing import Any, Iterable

from sqlalchemy import text

from .config import SyncSettings
from .connections import resolved_settings
from .preview import _iter_rows
from src.graphstudio_sync.storage.repository import ControlPlaneRepository
from .source_database import (
    ORACLE_KIND,
    connect_source,
    fetch_dicts,
    quote_identifier,
    source_cursor,
)


SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$#]*$")
SUPPORTED_FILTERS = {"eq", "ne", "in", "is_null", "not_null"}
SUPPORTED_TYPES = {"String", "Integer", "Float", "Boolean", "DateTime", "Date", "Navigation"}


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _identifier(value: str, kind: str) -> str:
    if not SAFE_IDENTIFIER.fullmatch(str(value or "")):
        raise ValueError(f"Unsafe projection identifier: {value!r}")
    return quote_identifier(value, kind)


def _path(value: str, kind: str) -> str:
    parts = str(value or "").split(".")
    if len(parts) != 2:
        raise ValueError(f"Projection field path must use alias.column: {value!r}")
    return f"{_identifier(parts[0], kind)}.{_identifier(parts[1], kind)}"


def validate_projection_definition(
    projection: dict[str, Any],
    fields: Iterable[dict[str, Any]],
    target_contract: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    fields = list(fields)
    source_alias = projection.get("source_alias") or "src"
    aliases = {source_alias}

    def path_parts(value: Any) -> tuple[str, str] | None:
        parts = str(value or "").split(".")
        if len(parts) != 2 or not all(SAFE_IDENTIFIER.fullmatch(part) for part in parts):
            return None
        return parts[0], parts[1]

    for key in ("source_schema", "source_table"):
        if not SAFE_IDENTIFIER.fullmatch(str(projection.get(key) or "")):
            errors.append(f"根表缺少合法的 {key}")
    if not SAFE_IDENTIFIER.fullmatch(source_alias):
        errors.append("根表别名不合法")
    joins = list(projection.get("join_plan") or [])
    for index, join in enumerate(joins, start=1):
        alias = str(join.get("alias") or "")
        previous_aliases = set(aliases)
        if not SAFE_IDENTIFIER.fullmatch(alias):
            errors.append(f"第 {index} 个 Join 的别名不合法")
        elif alias in aliases:
            errors.append(f"Join 别名重复：{alias}")
        aliases.add(alias)
        if join.get("joinType", "inner") not in {"inner", "left"}:
            errors.append(f"第 {index} 个 Join 只支持 inner/left")
        for key in ("schema", "table"):
            if not SAFE_IDENTIFIER.fullmatch(str(join.get(key) or "")):
                errors.append(f"第 {index} 个 Join 缺少合法的 {key}")
        left = path_parts(join.get("left"))
        right = path_parts(join.get("right"))
        if not left or not right:
            errors.append(f"第 {index} 个 Join 的关联字段必须是安全的 alias.column")
        elif not (
            (left[0] in previous_aliases and right[0] == alias)
            or (right[0] in previous_aliases and left[0] == alias)
        ):
            errors.append(f"第 {index} 个 Join 必须连接已有别名与当前新别名 {alias}")
    owner_mapping = list(projection.get("owner_mapping") or [])
    if not owner_mapping:
        errors.append("至少配置一个主对象关联键")
    selected = set(target_contract.get("selected_columns") or []) | set(target_contract.get("primary_key_columns") or [])
    for mapping in owner_mapping:
        if mapping.get("targetColumn") not in selected:
            errors.append(f"主对象字段不在数据契约中：{mapping.get('targetColumn')}")
        path = str(mapping.get("sourcePath") or "")
        parts = path_parts(path)
        if not parts or parts[0] not in aliases:
            errors.append(f"关联来源必须使用安全的已声明别名：{path}")
    if not fields:
        errors.append("至少配置一个投影字段")
    target_names: set[str] = set()
    field_keys: set[str] = set()
    for field in fields:
        if field.get("field_key") in field_keys:
            errors.append(f"字段稳定 ID 重复：{field.get('field_key')}")
        field_keys.add(field.get("field_key"))
        target = str(field.get("target_field") or "")
        if not SAFE_IDENTIFIER.fullmatch(target):
            errors.append(f"目标属性名不合法：{target}")
        if target in target_names:
            errors.append(f"目标属性重复：{target}")
        target_names.add(target)
        source_path = str(field.get("source_path") or "")
        parts = path_parts(source_path)
        if not parts or parts[0] not in aliases:
            errors.append(f"投影字段必须使用安全的已声明别名：{source_path}")
        if field.get("data_type", "String") not in SUPPORTED_TYPES:
            errors.append(f"不支持的数据类型：{field.get('data_type')}")
    base_fields = {
        item.get("target_field") for item in target_contract.get("fields") or []
        if item.get("lifecycle_status") != "retired"
    }
    collisions = sorted(target_names & base_fields)
    if collisions and projection.get("collision_policy", "reject") == "reject":
        errors.append(f"投影属性与主契约字段冲突：{', '.join(collisions)}；请显式选择覆盖或空值补齐")
    for row_filter in projection.get("row_filters") or []:
        if row_filter.get("operator") not in SUPPORTED_FILTERS:
            errors.append(f"不支持的过滤操作：{row_filter.get('operator')}")
        path = str(row_filter.get("path") or "")
        parts = path_parts(path)
        if not parts or parts[0] not in aliases:
            errors.append(f"过滤字段必须使用安全的已声明别名：{path}")
        if row_filter.get("operator") == "in" and not isinstance(row_filter.get("value"), list):
            errors.append("in 过滤器的值必须是数组")
    order_by = projection.get("order_by") or []
    if projection.get("multiple_match_policy") in {"first", "latest"} and not order_by:
        errors.append("first/latest 多值策略必须配置确定性的排序字段")
    for order in order_by:
        path = str(order.get("path") or "")
        parts = path_parts(path)
        if not parts or parts[0] not in aliases:
            errors.append(f"排序字段必须使用安全的已声明别名：{path}")
        if str(order.get("direction", "asc")).casefold() not in {"asc", "desc"}:
            errors.append("排序方向只支持 asc/desc")
    return {
        "valid": not errors,
        "errors": errors,
        "aliases": sorted(aliases),
        "fieldCount": len(fields),
        "joinCount": len(joins),
    }


def compile_projection_query(
    projection: dict[str, Any],
    fields: list[dict[str, Any]],
    owner_keys: list[tuple[Any, ...]],
    *,
    kind: str,
) -> tuple[str, Any]:
    if not owner_keys:
        raise ValueError("Projection query requires at least one owner key")
    owner_mapping = projection["owner_mapping"]
    select = [
        f"{_path(mapping['sourcePath'], kind)} AS {_identifier(f'__owner_{index}', kind)}"
        for index, mapping in enumerate(owner_mapping)
    ]
    select.extend(
        f"{_path(field['source_path'], kind)} AS {_identifier(f'__field_{index}', kind)}"
        for index, field in enumerate(fields)
    )
    root = (
        f"{_identifier(projection['source_schema'], kind)}."
        f"{_identifier(projection['source_table'], kind)} "
        f"{_identifier(projection.get('source_alias') or 'src', kind)}"
    )
    joins: list[str] = []
    for join in projection.get("join_plan") or []:
        join_type = "LEFT JOIN" if join.get("joinType", "inner") == "left" else "INNER JOIN"
        joins.append(
            f"{join_type} {_identifier(join['schema'], kind)}.{_identifier(join['table'], kind)} "
            f"{_identifier(join['alias'], kind)} ON {_path(join['left'], kind)} = {_path(join['right'], kind)}"
        )
    parameters: dict[str, Any] | list[Any] = {} if kind == ORACLE_KIND else []
    counter = 0

    def parameter(value: Any) -> str:
        nonlocal counter
        if kind == ORACLE_KIND:
            name = f"p{counter}"
            counter += 1
            parameters[name] = value
            return f":{name}"
        counter += 1
        parameters.append(value)
        return "%s"

    owner_clauses = []
    for owner_key in owner_keys:
        if len(owner_key) != len(owner_mapping):
            raise ValueError("Owner key length does not match owner_mapping")
        owner_clauses.append("(" + " AND ".join(
            f"{_path(mapping['sourcePath'], kind)} = {parameter(value)}"
            for mapping, value in zip(owner_mapping, owner_key, strict=True)
        ) + ")")
    where = ["(" + " OR ".join(owner_clauses) + ")"]
    for row_filter in projection.get("row_filters") or []:
        path = _path(row_filter["path"], kind)
        operator = row_filter["operator"]
        if operator == "is_null":
            where.append(f"{path} IS NULL")
        elif operator == "not_null":
            where.append(f"{path} IS NOT NULL")
        elif operator == "in":
            values = row_filter.get("value") or []
            if not values:
                where.append("1=0")
            else:
                where.append(f"{path} IN ({', '.join(parameter(value) for value in values)})")
        else:
            sql_operator = "=" if operator == "eq" else "<>"
            where.append(f"{path} {sql_operator} {parameter(row_filter.get('value'))}")
    order = [_path(mapping["sourcePath"], kind) for mapping in owner_mapping]
    for item in projection.get("order_by") or []:
        direction = str(item.get("direction", "asc")).upper()
        if projection.get("multiple_match_policy") == "latest":
            direction = "DESC"
        order.append(f"{_path(item['path'], kind)} {direction}")
    sql = (
        f"SELECT {', '.join(select)} FROM {root} "
        + (" ".join(joins) + " " if joins else "")
        + f"WHERE {' AND '.join(where)} ORDER BY {', '.join(order)}"
    )
    return sql, parameters if kind == ORACLE_KIND else tuple(parameters)


def _typed(value: Any, data_type: str) -> Any:
    if value is None:
        return None
    if data_type == "String" or data_type == "Navigation":
        return str(value).rstrip()
    if data_type == "Integer":
        return int(value)
    if data_type == "Float":
        return float(value)
    if data_type == "Boolean":
        if isinstance(value, str):
            lowered = value.strip().casefold()
            if lowered in {"1", "true", "yes", "y"}:
                return True
            if lowered in {"0", "false", "no", "n"}:
                return False
            raise ValueError(f"Cannot convert {value!r} to Boolean")
        return bool(value)
    if data_type in {"DateTime", "Date"}:
        return value.isoformat() if hasattr(value, "isoformat") else str(value)
    return value


def fetch_projection_values(
    connection,
    *,
    kind: str,
    projection: dict[str, Any],
    owner_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    owner_mapping = projection["owner_mapping"]
    fields = [item for item in projection["fields"] if item.get("lifecycle_status") != "retired"]
    owner_keys = [tuple(row.get(item["targetColumn"]) for item in owner_mapping) for row in owner_rows]
    owner_keys = list(dict.fromkeys(owner_keys))
    cursor = source_cursor(connection, kind)
    rows: list[dict[str, Any]] = []
    query_hashes: list[str] = []
    try:
        configured_batch = int((projection.get("config") or {}).get("ownerBatchSize") or 500)
        parameter_budget = 900 if kind == ORACLE_KIND else 1800
        owner_batch_size = max(1, min(configured_batch, parameter_budget // max(1, len(owner_mapping))))
        for start in range(0, len(owner_keys), owner_batch_size):
            sql, parameters = compile_projection_query(
                projection, fields, owner_keys[start:start + owner_batch_size], kind=kind,
            )
            cursor.execute(sql, parameters)
            rows.extend(fetch_dicts(cursor))
            query_hashes.append(hashlib.sha256(sql.encode()).hexdigest())
    finally:
        cursor.close()
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(f"__owner_{index}") for index in range(len(owner_mapping)))].append(row)
    values: dict[tuple[Any, ...], dict[str, Any]] = {}
    missing = 0
    multiples = 0
    for owner_key in owner_keys:
        matches = grouped.get(owner_key, [])
        issues: list[str] = []
        properties: dict[str, Any] = {}
        if not matches:
            missing += 1
            properties.update({field["target_field"]: None for field in fields})
            if projection["missing_policy"] in {"quarantine", "reject"}:
                issues.append(f"projection.{projection['projection_key']}.missing")
        else:
            if len(matches) > 1:
                multiples += 1
                if projection["multiple_match_policy"] == "reject":
                    issues.append(f"projection.{projection['projection_key']}.multiple")
            for index, field in enumerate(fields):
                raw_values = [row.get(f"__field_{index}") for row in matches]
                if projection["multiple_match_policy"] == "array":
                    converted = []
                    for raw in raw_values:
                        value = _typed(raw, field["data_type"])
                        if value not in converted and value is not None:
                            converted.append(value)
                    value = converted
                else:
                    value = _typed(raw_values[0], field["data_type"])
                if field.get("required") and value in (None, "", []):
                    issues.append(f"projection.required.{field['field_key']}")
                properties[field["target_field"]] = value
        values[owner_key] = {"properties": properties, "issues": issues, "matchCount": len(matches)}
    return {
        "values": values,
        "ownerCount": len(owner_keys),
        "matchedRows": len(rows),
        "missingOwners": missing,
        "multipleMatches": multiples,
        "queryHash": content_hash(query_hashes),
    }


def apply_attribute_projections(
    source,
    *,
    kind: str,
    projections: list[dict[str, Any]],
    owner_rows: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    for projection in projections:
        result = fetch_projection_values(
            source, kind=kind, projection=projection, owner_rows=owner_rows
        )
        mapping = projection["owner_mapping"]
        for owner_row, record in zip(owner_rows, records, strict=True):
            owner_key = tuple(owner_row.get(item["targetColumn"]) for item in mapping)
            projected = result["values"].get(owner_key, {"properties": {}, "issues": []})
            projected_issues = list(projected["issues"])
            for target_field, value in projected["properties"].items():
                collision = target_field in record["properties"] and record["properties"][target_field] not in (None, "")
                policy = projection.get("collision_policy", "reject")
                if collision and policy == "reject":
                    projected_issues.append(f"projection.{projection['projection_key']}.collision.{target_field}")
                    continue
                if collision and policy == "coalesce":
                    continue
                record["properties"][target_field] = value
            record["qualityIssues"].extend(projected_issues)
            if projected_issues:
                record["recordStatus"] = "quarantined"
            record["sourceHash"] = content_hash({
                "sourcePrimaryKey": record["sourcePrimaryKey"],
                "businessKey": record["businessKey"],
                "sourceValues": record["sourceValues"],
                "properties": record["properties"],
            })
    return records


def preview_attribute_projection(
    base_settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    projection_key: str,
) -> dict[str, Any]:
    projection = repository.attribute_projection(projection_key)
    target = projection["targetContract"]
    preview_id = uuid.uuid4()
    with repository.engine.begin() as connection:
        connection.execute(
            text("INSERT INTO graphsync.attribute_projection_preview (preview_id, projection_key, projection_version, status) VALUES (:id, :key, :version, 'started')"),
            {"id": preview_id, "key": projection_key, "version": projection["version"]},
        )
    try:
        settings = resolved_settings(base_settings, repository)
        source = connect_source(settings)
        try:
            owner_columns = sorted({
                *(item["targetColumn"] for item in projection["owner_mapping"]),
                *target["primary_key_columns"],
            })
            owner_rows = list(islice(_iter_rows(
                source, kind=settings.source_kind,
                schema=target["source_schema"], table=target["source_table"],
                columns=owner_columns, primary_keys=target["primary_key_columns"],
                fetch_size=int(projection["preview_row_limit"]),
            ), int(projection["preview_row_limit"])))
            result = fetch_projection_values(
                source, kind=settings.source_kind,
                projection=projection, owner_rows=owner_rows,
            ) if owner_rows else {
                "values": {}, "ownerCount": 0, "matchedRows": 0,
                "missingOwners": 0, "multipleMatches": 0,
                "queryHash": None,
            }
        finally:
            source.close()
        sample = [
            {
                "owner": {mapping["targetColumn"]: owner.get(mapping["targetColumn"]) for mapping in projection["owner_mapping"]},
                **result["values"].get(tuple(owner.get(mapping["targetColumn"]) for mapping in projection["owner_mapping"]), {"properties": {}, "issues": [], "matchCount": 0}),
            }
            for owner in owner_rows[:20]
        ]
        with repository.engine.begin() as connection:
            connection.execute(
                text("UPDATE graphsync.attribute_projection_preview SET status='succeeded', owner_rows=:owners, matched_rows=:matches, missing_owners=:missing, multiple_matches=:multiples, sample=CAST(:sample AS jsonb), compiled_query_hash=:hash, finished_at=now() WHERE preview_id=:id"),
                {"id": preview_id, "owners": result["ownerCount"], "matches": result["matchedRows"], "missing": result["missingOwners"], "multiples": result["multipleMatches"], "sample": canonical_json(sample), "hash": result["queryHash"]},
            )
        return {"previewId": str(preview_id), "projectionKey": projection_key, "projectionVersion": projection["version"], "status": "succeeded", **{key: value for key, value in result.items() if key != "values"}, "sample": sample, "sourceMutated": False, "graphStudioMutated": False}
    except Exception as exc:
        with repository.engine.begin() as connection:
            connection.execute(
                text("UPDATE graphsync.attribute_projection_preview SET status='failed', error=CAST(:error AS jsonb), finished_at=now() WHERE preview_id=:id"),
                {"id": preview_id, "error": json.dumps({"message": str(exc)}, ensure_ascii=False)},
            )
        raise
