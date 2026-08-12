"""Deterministic query-builder plans backed by the physical Camstar schema."""

from __future__ import annotations

import re

from src.ontology.wiki_manager import _sql_identifier, normalize_sql_dialect
from src.qa.sql_schema_retriever import (
    _physical_fk_graph,
    _schema,
    build_physical_join_plan,
)


MAX_QUERY_OBJECTS = 16
MAX_PLAN_TABLES = 24
REFERENCE_SCHEMA_SOURCE = "docs/Database_Fields.csv"


def _join_key(edge: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        edge["from_table"],
        edge["from_field"],
        edge["to_table"],
        edge["to_field"],
    )


def _join_pair_key(left: str, right: str) -> str:
    return "|".join(sorted((left, right)))


def _physical_join_candidates(left: str, right: str) -> list[dict[str, str]]:
    candidates = {
        _join_key(edge): dict(edge)
        for neighbor, edge in _physical_fk_graph().get(left, [])
        if neighbor == right
    }
    return [candidates[key] for key in sorted(candidates)]


def _join_candidate_groups(joins: list[dict[str, str]]) -> list[dict]:
    groups = []
    seen_pairs: set[str] = set()
    for selected in joins:
        left = selected["from_table"]
        right = selected["to_table"]
        pair_key = _join_pair_key(left, right)
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        groups.append({
            "pair_key": pair_key,
            "tables": sorted((left, right)),
            "selected": dict(selected),
            "candidates": _physical_join_candidates(left, right),
        })
    return groups


def _apply_join_overrides(
    joins: list[dict[str, str]],
    overrides: list[dict[str, str]],
) -> list[dict[str, str]]:
    if not overrides:
        return joins

    known_edges = {
        _join_key(edge)
        for neighbors in _physical_fk_graph().values()
        for _, edge in neighbors
    }
    by_pair: dict[str, dict[str, str]] = {}
    for override in overrides:
        candidate = {
            key: str(override.get(key, "")).strip()
            for key in ("from_table", "from_field", "to_table", "to_field")
        }
        if _join_key(candidate) not in known_edges:
            raise ValueError(
                "所选 JOIN 不是参考 Schema 中的物理外键："
                f"{candidate['from_table']}.{candidate['from_field']} = "
                f"{candidate['to_table']}.{candidate['to_field']}"
            )
        by_pair[_join_pair_key(
            candidate["from_table"], candidate["to_table"]
        )] = candidate

    return [
        by_pair.get(
            _join_pair_key(edge["from_table"], edge["to_table"]),
            edge,
        )
        for edge in joins
    ]


def _table_alias(table_name: str, used: set[str]) -> str:
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+", table_name)
    base = "".join(word[0] for word in words if word).lower()
    if not base:
        base = re.sub(r"[^A-Za-z0-9]", "", table_name).lower()[:2] or "t"
    if base[0].isdigit():
        base = f"t{base}"

    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def _default_select_fields(table_name: str) -> list[str]:
    _, fields_by_table = _schema()
    fields = fields_by_table.get(table_name, [])
    selected: list[str] = []

    def add_matching(predicate, *, limit: int | None = None):
        for field in fields:
            field_name = field["FieldName"]
            if predicate(field) and field_name not in selected:
                selected.append(field_name)
                if limit is not None and len(selected) >= limit:
                    return

    add_matching(lambda row: row.get("IsPrimaryKey", "").lower() == "true")
    preferred_names = {
        "name",
        f"{table_name}name".lower(),
        f"{table_name}revision".lower(),
    }
    add_matching(
        lambda row: row["FieldName"].lower() in preferred_names,
        limit=3,
    )
    if len(selected) < 2:
        add_matching(
            lambda row: row["FieldName"].lower() == "description",
            limit=2,
        )
    if not selected and fields:
        selected.append(fields[0]["FieldName"])
    return selected[:3]


def _reachable_tables(root_table: str, joins: list[dict[str, str]]) -> set[str]:
    reachable = {root_table}
    changed = True
    while changed:
        changed = False
        for edge in joins:
            left = edge["from_table"]
            right = edge["to_table"]
            if left in reachable and right not in reachable:
                reachable.add(right)
                changed = True
            elif right in reachable and left not in reachable:
                reachable.add(left)
                changed = True
    return reachable


def _ambiguous_join_warnings(joins: list[dict[str, str]]) -> list[str]:
    warnings = []
    for group in _join_candidate_groups(joins):
        candidates = group["candidates"]
        if len(candidates) <= 1:
            continue
        left, right = group["tables"]
        selected = group["selected"]
        warnings.append(
            f"{left} 与 {right} 存在 {len(candidates)} 个物理外键候选；"
            f"当前使用 {selected['from_table']}.{selected['from_field']} = "
            f"{selected['to_table']}.{selected['to_field']}。"
            "请点击预览图中的橙色关系线选择正确 JOIN。"
        )
    return warnings


def _validate_reference_plan(
    tables: list[str],
    joins: list[dict[str, str]],
    selected_nodes: list[str],
) -> dict:
    """Fail closed unless every generated identifier is backed by the CSV."""
    schema_tables, fields_by_table = _schema()
    errors = []

    for table in tables:
        if table not in schema_tables:
            errors.append(f"参考 Schema 中不存在物理表 {table}")

    for table in selected_nodes:
        known_fields = {row["FieldName"] for row in fields_by_table.get(table, [])}
        for field in _default_select_fields(table):
            if field not in known_fields:
                errors.append(f"参考 Schema 中不存在字段 {table}.{field}")

    for edge in joins:
        from_table = edge["from_table"]
        from_field = edge["from_field"]
        to_table = edge["to_table"]
        to_field = edge["to_field"]
        matching_fk = any(
            row["FieldName"] == from_field
            and row.get("IsForeignKey", "").lower() == "true"
            and row.get("FKTableName") == to_table
            and row.get("FKFieldName") == to_field
            for row in fields_by_table.get(from_table, [])
        )
        if not matching_fk:
            errors.append(
                "JOIN 未匹配参考物理外键："
                f"{from_table}.{from_field} = {to_table}.{to_field}"
            )
        target_fields = {
            row["FieldName"] for row in fields_by_table.get(to_table, [])
        }
        if to_field not in target_fields:
            errors.append(f"参考 Schema 中不存在字段 {to_table}.{to_field}")

    if errors:
        raise ValueError("；".join(errors))
    return {
        "status": "validated",
        "source": REFERENCE_SCHEMA_SOURCE,
        "runtime_database_checked": False,
    }


def _render_sql(
    selected_nodes: list[str],
    tables: list[str],
    joins: list[dict[str, str]],
    unconnected: list[str],
    dialect: str,
) -> tuple[str, str, dict[str, str], list[dict[str, str]]]:
    root_table = selected_nodes[0] if selected_nodes else tables[0]
    used_aliases: set[str] = set()
    aliases = {
        table: _table_alias(table, used_aliases)
        for table in tables
    }
    reachable = _reachable_tables(root_table, joins)
    select_tables = [
        table for table in selected_nodes
        if table in reachable
    ] or [root_table]

    select_expressions = []
    for table in select_tables:
        alias = aliases[table]
        for field in _default_select_fields(table):
            select_expressions.append(
                f"    {alias}.{_sql_identifier(field, dialect)}"
            )
    if not select_expressions:
        select_expressions.append(f"    {aliases[root_table]}.*")

    join_keyword_alias = "" if dialect == "oracle" else " AS"
    sql_lines = [
        "SELECT",
        ",\n".join(select_expressions),
        (
            f"FROM {_sql_identifier(root_table, dialect)}"
            f"{join_keyword_alias} {aliases[root_table]}"
        ),
    ]

    joined_tables = {root_table}
    pending = list(joins)
    rendered_joins: list[dict[str, str]] = []
    while pending:
        selected_edge = None
        new_table = None
        for edge in pending:
            left_joined = edge["from_table"] in joined_tables
            right_joined = edge["to_table"] in joined_tables
            if left_joined ^ right_joined:
                selected_edge = edge
                new_table = (
                    edge["to_table"] if left_joined else edge["from_table"]
                )
                break
        if selected_edge is None or new_table is None:
            break

        sql_lines.extend([
            (
                f"JOIN {_sql_identifier(new_table, dialect)}"
                f"{join_keyword_alias} {aliases[new_table]}"
            ),
            (
                f"    ON {aliases[selected_edge['from_table']]}."
                f"{_sql_identifier(selected_edge['from_field'], dialect)} = "
                f"{aliases[selected_edge['to_table']]}."
                f"{_sql_identifier(selected_edge['to_field'], dialect)}"
            ),
        ])
        rendered_joins.append(selected_edge)
        joined_tables.add(new_table)
        pending.remove(selected_edge)

    sql_lines[-1] += ";"
    if unconnected:
        sql_lines.extend([
            "",
            (
                "-- 未连接对象未加入 SQL："
                + "、".join(unconnected)
            ),
        ])
    return "\n".join(sql_lines), root_table, aliases, rendered_joins


def build_query_builder_plan(
    selected_nodes: list[str],
    *,
    dialect: str = "oracle",
    join_overrides: list[dict[str, str]] | None = None,
) -> dict:
    """Build a transient visual join plan and read-only SQL skeleton."""
    normalized_dialect = normalize_sql_dialect(dialect)
    normalized_nodes = list(dict.fromkeys(
        name.strip()
        for name in selected_nodes
        if isinstance(name, str) and name.strip()
    ))
    if len(normalized_nodes) > MAX_QUERY_OBJECTS:
        raise ValueError(f"最多可选择 {MAX_QUERY_OBJECTS} 个查询对象")

    schema_tables, _ = _schema()
    invalid = [name for name in normalized_nodes if name not in schema_tables]
    if invalid:
        raise ValueError(f"未知物理对象: {', '.join(invalid)}")
    if not normalized_nodes:
        return {
            "selected_nodes": [],
            "nodes": [],
            "joins": [],
            "unconnected": [],
            "root_table": None,
            "aliases": {},
            "sql": "",
            "dialect": normalized_dialect,
            "join_candidates": [],
            "warnings": [],
        }

    physical_plan = build_physical_join_plan(
        normalized_nodes,
        max_tables=MAX_PLAN_TABLES,
    )
    planned_joins = _apply_join_overrides(
        physical_plan["joins"],
        join_overrides or [],
    )
    sql, root_table, aliases, rendered_joins = _render_sql(
        normalized_nodes,
        physical_plan["tables"],
        planned_joins,
        physical_plan["unconnected"],
        normalized_dialect,
    )
    reference_validation = _validate_reference_plan(
        physical_plan["tables"],
        rendered_joins,
        normalized_nodes,
    )
    selected_set = set(normalized_nodes)
    unconnected_set = set(physical_plan["unconnected"])
    node_payload = [
        {
            "id": table,
            "selected": table in selected_set,
            "bridge": table not in selected_set,
            "unconnected": table in unconnected_set,
            "alias": aliases.get(table, ""),
            "default_fields": (
                _default_select_fields(table) if table in selected_set else []
            ),
        }
        for table in physical_plan["tables"]
    ]
    warnings = []
    if physical_plan["unconnected"]:
        warnings.append(
            "以下对象无法通过限定范围内的物理外键连接，未加入 SQL："
            + "、".join(physical_plan["unconnected"])
        )
    warnings.extend(_ambiguous_join_warnings(rendered_joins))

    return {
        "selected_nodes": normalized_nodes,
        "nodes": node_payload,
        "joins": rendered_joins,
        "unconnected": physical_plan["unconnected"],
        "root_table": root_table,
        "aliases": aliases,
        "sql": sql,
        "dialect": normalized_dialect,
        "join_candidates": _join_candidate_groups(rendered_joins),
        "warnings": warnings,
        "reference_validation": reference_validation,
    }
