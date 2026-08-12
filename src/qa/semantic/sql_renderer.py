"""Render reviewed metric contracts into deterministic read-only SQL."""

from __future__ import annotations

import re
from typing import Any

from .metric_catalog import get_metric


def _parameter(name: str, dialect: str) -> str:
    return f"@{name}" if dialect == "sqlserver" else f":{name}"


def _question_filters(metric: dict[str, Any], question: str) -> list[tuple[str, str]]:
    filters = []
    available = metric.get("availableFilters", {})
    if "status" in available and re.search(
        r"(?:状态|Status)\s*(?:为|=|等于|\bis\b)\s*"
        r"(?:\d+|参数|[:@][A-Za-z_][A-Za-z0-9_]*)",
        question,
        re.I,
    ):
        item = available["status"]
        filters.append((item["expression"], item["parameter"]))
    if "container_id" in available and re.search(
        r"(?:ContainerId|容器ID|批次ID|@ContainerId|:ContainerId)",
        question,
        re.I,
    ):
        item = available["container_id"]
        filters.append((item["expression"], item["parameter"]))
    return filters


def render_metric_sql(
    metric_or_id: dict[str, Any] | str,
    *,
    dialect: str = "oracle",
    time_scope: str = "未指定",
    time_basis: str | None = None,
    question: str = "",
) -> str:
    metric = (
        get_metric(metric_or_id)
        if isinstance(metric_or_id, str)
        else metric_or_id
    )
    if not metric:
        raise ValueError("Unknown metric contract")
    dialect = (dialect or "oracle").lower()
    if dialect not in {"oracle", "sqlserver"}:
        raise ValueError(f"Unsupported SQL dialect: {dialect}")
    if metric.get("requiresTimeRange") and (
        time_scope == "未指定" or not time_basis
    ):
        raise ValueError("Historical metric requires time scope and time basis")
    if time_basis and time_basis not in metric.get("allowedTimeFields", []):
        raise ValueError(
            f"Metric {metric['id']} does not allow time field {time_basis}"
        )

    select_items = [
        item["expression"]
        + (f" AS {item['alias']}" if item.get("alias") else "")
        for item in metric.get("select", [])
    ]
    select_items += [
        item["expression"] + f" AS {item['alias']}"
        for item in metric.get("measures", [])
    ]
    limit = metric.get("limit")
    select_head = "SELECT"
    if dialect == "sqlserver" and limit:
        select_head += f" TOP ({int(limit)})"
    lines = [select_head]
    for index, item in enumerate(select_items):
        comma = "," if index < len(select_items) - 1 else ""
        lines.append(f"    {item}{comma}")

    tables = metric["tables"]
    first = tables[0]
    lines.append(f"FROM {first['table']} {first['alias']}")
    joined_aliases = {first["alias"]}
    remaining_joins = list(metric.get("joins", []))
    for table in tables[1:]:
        alias = table["alias"]
        selected_join = None
        for join in remaining_joins:
            left_alias = join["left"].split(".", 1)[0]
            right_alias = join["right"].split(".", 1)[0]
            if alias in {left_alias, right_alias} and (
                left_alias in joined_aliases or right_alias in joined_aliases
            ):
                selected_join = join
                break
        if not selected_join:
            raise ValueError(
                f"Metric {metric['id']} cannot connect table alias {alias}"
            )
        lines.append(f"JOIN {table['table']} {alias}")
        lines.append(
            f"    ON {selected_join['left']} = {selected_join['right']}"
        )
        remaining_joins.remove(selected_join)
        joined_aliases.add(alias)

    predicates = []
    if metric.get("requiresTimeRange"):
        time_expression = f"{metric['timeAlias']}.{time_basis}"
        predicates.extend([
            f"{time_expression} >= {_parameter('start_time', dialect)}",
            f"{time_expression} < {_parameter('end_time', dialect)}",
        ])
    for expression, parameter in _question_filters(metric, question):
        predicates.append(f"{expression} = {_parameter(parameter, dialect)}")
    if predicates:
        lines.append("WHERE " + predicates[0])
        lines.extend(f"  AND {predicate}" for predicate in predicates[1:])

    if metric.get("groupBy"):
        lines.append("GROUP BY")
        for index, expression in enumerate(metric["groupBy"]):
            comma = "," if index < len(metric["groupBy"]) - 1 else ""
            lines.append(f"    {expression}{comma}")
    if metric.get("orderBy"):
        lines.append("ORDER BY " + ", ".join(metric["orderBy"]))
    if dialect == "oracle" and limit:
        lines.append(f"FETCH FIRST {int(limit)} ROWS ONLY")
    lines[-1] += ";"
    return "\n".join(lines)


def render_metric_answer(
    metric_or_id: dict[str, Any] | str,
    *,
    dialect: str,
    time_scope: str,
    time_basis: str | None,
    question: str,
) -> str:
    metric = (
        get_metric(metric_or_id)
        if isinstance(metric_or_id, str)
        else metric_or_id
    )
    sql = render_metric_sql(
        metric,
        dialect=dialect,
        time_scope=time_scope,
        time_basis=time_basis,
        question=question,
    )
    joins = metric.get("joins", [])
    rules = metric.get("businessRules", [])
    lines = [
        "### SQL",
        "",
        "```sql",
        sql,
        "```",
        "",
        "### 指标口径",
        "",
        f"- 指标合同：`{metric['id']}`（{metric['nameZh']}）",
        f"- 事实表：`{metric['factTable']}`",
        f"- 合同状态：`{metric.get('status', 'approved')}`",
        f"- 定义：{metric['description']}",
        "",
        "### 使用的表与连接",
        "",
    ]
    if joins:
        lines.extend(
            f"- `{item['left']} = {item['right']}`"
            for item in joins
        )
    else:
        lines.append("- 单表查询，无 JOIN。")
    lines += ["", "### 注意事项", ""]
    lines.extend(f"- {rule}" for rule in rules)
    lines.append("- SQL仅供审核和复制，本系统不连接业务数据库执行查询。")
    return "\n".join(lines)


def render_static_metric_answer(
    metric_or_id: dict[str, Any] | str,
    *,
    sql: str,
    example_id: str,
    distance: float,
) -> str:
    """Wrap an immutable SQL template without modifying any SQL character."""
    metric = (
        get_metric(metric_or_id)
        if isinstance(metric_or_id, str)
        else metric_or_id
    )
    joins = metric.get("joins", [])
    rules = metric.get("businessRules", [])
    lines = [
        "### SQL",
        "",
        "```sql",
        sql,
        "```",
        "",
        "### 标准模板",
        "",
        f"- 标准问题：`{example_id}`",
        f"- 语义距离：`{distance:.4f}`",
        "- SQL来源：向量库绑定的不可变 Golden SQL，未经过模型改写。",
        "",
        "### 指标口径",
        "",
        f"- 指标合同：`{metric['id']}`（{metric['nameZh']}）",
        f"- 事实表：`{metric['factTable']}`",
        f"- 合同状态：`{metric.get('status', 'approved')}`",
        f"- 定义：{metric['description']}",
        "",
        "### 使用的表与连接",
        "",
    ]
    if joins:
        lines.extend(
            f"- `{item['left']} = {item['right']}`"
            for item in joins
        )
    else:
        lines.append("- 单表查询，无 JOIN。")
    lines += ["", "### 注意事项", ""]
    lines.extend(f"- {rule}" for rule in rules)
    lines.append("- SQL仅供审核和复制，本系统不连接业务数据库执行查询。")
    return "\n".join(lines)
