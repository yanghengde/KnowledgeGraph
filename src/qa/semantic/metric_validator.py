"""Validate SQL against a versioned business metric contract."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from src.qa.sql_validator import extract_sql
from .metric_catalog import get_metric


_TABLE_REF = re.compile(
    r"\b(?:FROM|JOIN)\s+(?:\[([^\]]+)\]|\"([^\"]+)\"|([A-Za-z_][A-Za-z0-9_]*))",
    re.I,
)


@dataclass
class MetricValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def _extract_tables(sql: str) -> set[str]:
    return {
        next(group for group in match.groups() if group)
        for match in _TABLE_REF.finditer(sql)
    }


def validate_metric_sql(
    answer_or_sql: str,
    metric_or_id: dict[str, Any] | str,
    *,
    time_basis: str | None = None,
) -> MetricValidationResult:
    metric = (
        get_metric(metric_or_id)
        if isinstance(metric_or_id, str)
        else metric_or_id
    )
    sql = extract_sql(answer_or_sql) or answer_or_sql
    normalized = _normalize(sql)
    errors = []

    expected_tables = {item["table"] for item in metric.get("tables", [])}
    actual_tables = _extract_tables(sql)
    missing_tables = sorted(expected_tables - actual_tables)
    extra_tables = sorted(actual_tables - expected_tables)
    if missing_tables:
        errors.append(
            f"指标 [{metric['id']}] 缺少合同表：{', '.join(missing_tables)}。"
        )
    if extra_tables:
        errors.append(
            f"指标 [{metric['id']}] 引用了合同外表：{', '.join(extra_tables)}。"
        )

    for item in metric.get("measures", []):
        if _normalize(item["expression"]) not in normalized:
            errors.append(
                f"指标 [{metric['id']}] 缺少度量表达式 {item['expression']}。"
            )
    for join in metric.get("joins", []):
        forward = _normalize(f"{join['left']}={join['right']}")
        reverse = _normalize(f"{join['right']}={join['left']}")
        if forward not in normalized and reverse not in normalized:
            errors.append(
                f"指标 [{metric['id']}] 缺少合同JOIN "
                f"{join['left']} = {join['right']}。"
            )
    for expression in metric.get("groupBy", []):
        group_match = re.search(
            r"\bgroup\s+by\b(?P<body>.*?)(?:\border\s+by\b|\bfetch\b|;|$)",
            sql,
            re.I | re.S,
        )
        if not group_match or _normalize(expression) not in _normalize(
            group_match.group("body")
        ):
            errors.append(
                f"指标 [{metric['id']}] 缺少分组字段 {expression}。"
            )
    if metric.get("requiresTimeRange") and time_basis:
        time_expression = f"{metric['timeAlias']}.{time_basis}"
        if _normalize(f"{time_expression}>=") not in normalized:
            errors.append(f"指标查询缺少 {time_expression} 开始边界。")
        if _normalize(f"{time_expression}<") not in normalized:
            errors.append(f"指标查询缺少 {time_expression} 结束边界。")

    return MetricValidationResult(
        valid=not errors,
        errors=list(dict.fromkeys(errors)),
    )
