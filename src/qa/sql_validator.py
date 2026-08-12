"""Deterministic validation for LLM-generated read-only SQL."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from src.qa.sql_schema_retriever import _schema


_IDENTIFIER = (
    r'(?:\[[^\]]+\]|"[^"]+"|[A-Za-z_][A-Za-z0-9_$#]*)'
)
_QUALIFIED_IDENTIFIER = rf"{_IDENTIFIER}(?:\s*\.\s*{_IDENTIFIER})?"
_TABLE_REF = re.compile(
    rf"\b(?P<kind>FROM|JOIN)\s+"
    rf"(?P<identifier>{_QUALIFIED_IDENTIFIER})"
    rf"(?:\s+(?:AS\s+)?(?P<alias>{_IDENTIFIER}))?",
    re.IGNORECASE,
)
_COLUMN_REF = re.compile(
    rf"(?P<alias>{_IDENTIFIER})\s*\.\s*"
    rf"(?P<column>{_IDENTIFIER}|\*)",
    re.IGNORECASE,
)
_COLUMN_EQUALITY = re.compile(
    rf"(?P<left_alias>{_IDENTIFIER})\s*\.\s*"
    rf"(?P<left_column>{_IDENTIFIER})\s*=\s*"
    rf"(?P<right_alias>{_IDENTIFIER})\s*\.\s*"
    rf"(?P<right_column>{_IDENTIFIER})",
    re.IGNORECASE,
)
_SQL_BLOCK = re.compile(
    r"```(?:sql)?\s*\n(?P<sql>.*?)```",
    re.IGNORECASE | re.DOTALL,
)
_UNSAFE = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|MERGE|TRUNCATE|DROP|ALTER|CREATE|"
    r"EXEC(?:UTE)?|GRANT|REVOKE)\b|"
    r"\bSELECT\s+.+?\s+INTO\s+",
    re.IGNORECASE | re.DOTALL,
)
_RESERVED_ALIAS_WORDS = {
    "CROSS",
    "FETCH",
    "FULL",
    "GROUP",
    "HAVING",
    "INNER",
    "JOIN",
    "LEFT",
    "LIMIT",
    "OFFSET",
    "ON",
    "ORDER",
    "OUTER",
    "RIGHT",
    "UNION",
    "WHERE",
}


@dataclass
class SqlValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    sql: str = ""
    tables: list[str] = field(default_factory=list)


def _unquote(identifier: str) -> str:
    identifier = re.sub(r"\s+", "", identifier or "")
    part = identifier.split(".")[-1]
    if (
        len(part) >= 2
        and (
            (part[0] == "[" and part[-1] == "]")
            or (part[0] == '"' and part[-1] == '"')
            or (part[0] == "`" and part[-1] == "`")
        )
    ):
        return part[1:-1]
    return part


def extract_sql(answer: str) -> str:
    match = _SQL_BLOCK.search(answer or "")
    return match.group("sql").strip() if match else ""


def _without_comments_and_strings(sql: str) -> str:
    cleaned = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    cleaned = re.sub(r"--[^\r\n]*", " ", cleaned)
    cleaned = re.sub(r"'(?:''|[^'])*'", "''", cleaned)
    return cleaned


def _physical_fk_pairs() -> set[frozenset[tuple[str, str]]]:
    tables, fields_by_table = _schema()
    pairs: set[frozenset[tuple[str, str]]] = set()
    for table, fields in fields_by_table.items():
        for item in fields:
            target = item.get("FKTableName", "")
            target_field = item.get("FKFieldName", "")
            if (
                item.get("IsForeignKey", "").lower() == "true"
                and target in tables
                and target_field
            ):
                pairs.add(frozenset({
                    (table.lower(), item["FieldName"].lower()),
                    (target.lower(), target_field.lower()),
                }))
    return pairs


def validate_sql_answer(
    answer: str,
    *,
    dialect: str = "oracle",
    query_plan: dict[str, Any] | None = None,
) -> SqlValidationResult:
    """Validate one SQL code block against the immutable physical CSV schema."""
    sql = extract_sql(answer)
    if not sql:
        # Clarification and informational answers legitimately contain no SQL.
        return SqlValidationResult(valid=True)

    errors: list[str] = []
    scrubbed = _without_comments_and_strings(sql)
    dialect = (dialect or "oracle").lower()
    if _UNSAFE.search(scrubbed):
        errors.append("SQL 包含非只读或结构修改语句。")
    if len([part for part in scrubbed.split(";") if part.strip()]) > 1:
        errors.append("一次回答只能包含一条 SQL 语句。")
    if not re.match(r"^\s*(?:SELECT\b|WITH\b)", scrubbed, re.IGNORECASE):
        errors.append("SQL 必须以 SELECT 或 CTE（WITH）开始。")

    if dialect == "oracle":
        if re.search(r"\bTOP\s*(?:\(|\d)", scrubbed, re.IGNORECASE):
            errors.append("Oracle SQL 不能使用 TOP。")
        if re.search(r"\[[^\]]+\]", scrubbed):
            errors.append("Oracle SQL 不能使用 SQL Server 方括号标识符。")
        if re.search(r"@\w+", scrubbed):
            errors.append("Oracle 参数必须使用 :参数名，不能使用 @参数名。")
        if re.search(r"\b(?:GETDATE|ISNULL)\s*\(", scrubbed, re.IGNORECASE):
            errors.append("SQL 中混入了 SQL Server 函数。")
    elif dialect == "sqlserver":
        if re.search(r"\bFETCH\s+FIRST\b", scrubbed, re.IGNORECASE):
            errors.append("SQL Server SQL 不能使用 FETCH FIRST。")
        if re.search(r"\b(?:ROWNUM|NVL|SYSDATE)\b", scrubbed, re.IGNORECASE):
            errors.append("SQL 中混入了 Oracle 语法或函数。")
        if re.search(r"(?<!:):[A-Za-z_]\w*", scrubbed):
            errors.append("SQL Server 参数必须使用 @参数名，不能使用 :参数名。")

    if query_plan:
        time_basis = query_plan.get("time_basis")
        time_scope = query_plan.get("time_scope")
        if time_basis and time_scope and time_scope != "未指定":
            field = re.escape(str(time_basis))
            qualified_field = (
                rf"(?:{_IDENTIFIER}\s*\.\s*)?"
                rf"(?:{field}|\"{field}\"|\[{field}\])"
            )
            if not re.search(qualified_field, scrubbed, re.IGNORECASE):
                errors.append(
                    f"查询计划要求使用时间字段 [{time_basis}]。"
                )
            if re.search(
                rf"\b(?:TRUNC|CAST|CONVERT)\s*\([^)]*{qualified_field}",
                scrubbed,
                re.IGNORECASE,
            ):
                errors.append(
                    f"时间字段 [{time_basis}] 不能先经过 TRUNC、CAST 或 CONVERT。"
                )
            if not re.search(
                rf"{qualified_field}\s*>=",
                scrubbed,
                re.IGNORECASE,
            ) or not re.search(
                rf"{qualified_field}\s*<(?!=)",
                scrubbed,
                re.IGNORECASE,
            ):
                errors.append(
                    f"时间范围必须使用 [{time_basis}] >= 开始参数 AND "
                    f"[{time_basis}] < 结束参数的半开区间。"
                )

    tables, fields_by_table = _schema()
    canonical_tables = {name.lower(): name for name in tables}
    table_refs = []
    aliases: dict[str, str] = {}
    table_spans = []
    cte_names = {
        match.group(1).lower()
        for match in re.finditer(
            rf"\bWITH\s+({_IDENTIFIER})\s+AS\s*\(",
            scrubbed,
            re.IGNORECASE,
        )
    }
    cte_aliases = set(cte_names)
    for match in _TABLE_REF.finditer(scrubbed):
        raw_table = _unquote(match.group("identifier"))
        if raw_table.lower() in cte_names:
            raw_alias = _unquote(match.group("alias") or "")
            if raw_alias and raw_alias.upper() not in _RESERVED_ALIAS_WORDS:
                cte_aliases.add(raw_alias.lower())
            continue
        table = canonical_tables.get(raw_table.lower())
        if not table:
            errors.append(f"物理表不存在：[{raw_table}]。")
            continue
        raw_alias = _unquote(match.group("alias") or "")
        if raw_alias.upper() in _RESERVED_ALIAS_WORDS:
            raw_alias = ""
        alias = raw_alias or table
        aliases[alias.lower()] = table
        aliases[table.lower()] = table
        table_refs.append(table)
        table_spans.append(match.span("identifier"))

    canonical_fields = {
        table: {
            field["FieldName"].lower(): field["FieldName"]
            for field in fields_by_table.get(table, [])
        }
        for table in set(table_refs)
    }
    for match in _COLUMN_REF.finditer(scrubbed):
        if any(
            match.start() >= start and match.end() <= end
            for start, end in table_spans
        ):
            continue
        alias = _unquote(match.group("alias"))
        column = _unquote(match.group("column"))
        if alias.lower() in cte_aliases:
            continue
        table = aliases.get(alias.lower())
        if not table:
            errors.append(f"SQL 使用了未定义的表别名：[{alias}]。")
            continue
        if column != "*" and column.lower() not in canonical_fields[table]:
            errors.append(f"物理字段不存在：[{table}].[{column}]。")

    valid_fk_pairs = _physical_fk_pairs()
    valid_join_tables: set[str] = set()
    for match in _COLUMN_EQUALITY.finditer(scrubbed):
        left_alias = _unquote(match.group("left_alias")).lower()
        right_alias = _unquote(match.group("right_alias")).lower()
        left_table = aliases.get(left_alias)
        right_table = aliases.get(right_alias)
        if not left_table or not right_table or left_table == right_table:
            continue
        pair = frozenset({
            (
                left_table.lower(),
                _unquote(match.group("left_column")).lower(),
            ),
            (
                right_table.lower(),
                _unquote(match.group("right_column")).lower(),
            ),
        })
        if pair in valid_fk_pairs:
            valid_join_tables.update([left_table, right_table])
        else:
            errors.append(
                "JOIN 条件不是已登记的物理外键："
                f"[{left_table}].[{_unquote(match.group('left_column'))}] = "
                f"[{right_table}].[{_unquote(match.group('right_column'))}]。"
            )

    distinct_tables = list(dict.fromkeys(table_refs))
    if len(distinct_tables) > 1:
        for table in distinct_tables:
            if table not in valid_join_tables:
                errors.append(f"表 [{table}] 没有经过物理外键验证的 JOIN。")

    return SqlValidationResult(
        valid=not errors,
        errors=list(dict.fromkeys(errors)),
        sql=sql,
        tables=distinct_tables,
    )


def format_validation_feedback(result: SqlValidationResult) -> str:
    return "\n".join(f"- {error}" for error in result.errors)
