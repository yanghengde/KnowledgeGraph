"""Load and physically validate reviewed business metric contracts."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.qa.sql_schema_retriever import _schema


CATALOG_PATH = Path(__file__).with_name("metrics.json")
DIMENSIONS_PATH = Path(__file__).with_name("dimensions.json")
_COLUMN_REF = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b")


@lru_cache(maxsize=1)
def load_metrics() -> dict[str, dict[str, Any]]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8-sig"))
    return {item["id"]: item for item in payload.get("metrics", [])}


@lru_cache(maxsize=1)
def load_dimensions() -> dict[str, dict[str, Any]]:
    payload = json.loads(DIMENSIONS_PATH.read_text(encoding="utf-8-sig"))
    return {item["id"]: item for item in payload.get("dimensions", [])}


def get_metric(metric_id: str | None) -> dict[str, Any] | None:
    return load_metrics().get(metric_id or "")


def _physical_fk_pairs() -> set[frozenset[tuple[str, str]]]:
    tables, fields_by_table = _schema()
    pairs = set()
    for table, fields in fields_by_table.items():
        for field in fields:
            target = field.get("FKTableName", "")
            target_field = field.get("FKFieldName", "")
            if (
                field.get("IsForeignKey", "").lower() == "true"
                and target in tables
                and target_field
            ):
                pairs.add(frozenset({
                    (table, field["FieldName"]),
                    (target, target_field),
                }))
    return pairs


def validate_metric_catalog() -> list[str]:
    """Return catalog errors; an empty list means every contract is physical."""
    tables, fields_by_table = _schema()
    errors: list[str] = []
    seen_ids: set[str] = set()
    valid_fk_pairs = _physical_fk_pairs()

    for metric in load_metrics().values():
        metric_id = metric.get("id", "")
        if metric_id in seen_ids:
            errors.append(f"重复指标ID：{metric_id}")
        seen_ids.add(metric_id)

        alias_to_table: dict[str, str] = {}
        for item in metric.get("tables", []):
            table = item.get("table", "")
            alias = item.get("alias", "")
            if table not in tables:
                errors.append(f"{metric_id}: 物理表不存在 [{table}]")
            if not alias:
                errors.append(f"{metric_id}: 表 [{table}] 缺少别名")
            elif alias in alias_to_table:
                errors.append(f"{metric_id}: 重复别名 [{alias}]")
            alias_to_table[alias] = table

        if metric.get("factTable") not in {
            item.get("table") for item in metric.get("tables", [])
        }:
            errors.append(f"{metric_id}: factTable未包含在tables中")

        expressions = [
            item.get("expression", "")
            for item in metric.get("select", [])
            + metric.get("measures", [])
        ]
        expressions += metric.get("groupBy", [])
        expressions += metric.get("orderBy", [])
        for item in metric.get("availableFilters", {}).values():
            expressions.append(item.get("expression", ""))
        for expression in expressions:
            for alias, column in _COLUMN_REF.findall(expression):
                table = alias_to_table.get(alias)
                if not table:
                    errors.append(
                        f"{metric_id}: 表达式使用未定义别名 [{alias}]"
                    )
                    continue
                physical_fields = {
                    field["FieldName"]
                    for field in fields_by_table.get(table, [])
                }
                if column not in physical_fields:
                    errors.append(
                        f"{metric_id}: 物理字段不存在 [{table}].[{column}]"
                    )

        for join in metric.get("joins", []):
            left = _COLUMN_REF.fullmatch(join.get("left", ""))
            right = _COLUMN_REF.fullmatch(join.get("right", ""))
            if not left or not right:
                errors.append(f"{metric_id}: JOIN格式无效 {join}")
                continue
            left_table = alias_to_table.get(left.group(1))
            right_table = alias_to_table.get(right.group(1))
            pair = frozenset({
                (left_table, left.group(2)),
                (right_table, right.group(2)),
            })
            if None in {left_table, right_table} or pair not in valid_fk_pairs:
                errors.append(
                    f"{metric_id}: JOIN不是物理外键 "
                    f"{join.get('left')} = {join.get('right')}"
                )

        if metric.get("requiresTimeRange"):
            time_alias = metric.get("timeAlias", "")
            time_table = alias_to_table.get(time_alias)
            if not time_table:
                errors.append(f"{metric_id}: timeAlias未定义")
            physical_fields = {
                field["FieldName"]
                for field in fields_by_table.get(time_table, [])
            }
            for field in metric.get("allowedTimeFields", []):
                if field not in physical_fields:
                    errors.append(
                        f"{metric_id}: 时间字段不存在 [{time_table}].[{field}]"
                    )

    return list(dict.fromkeys(errors))
