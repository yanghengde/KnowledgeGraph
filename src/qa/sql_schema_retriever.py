"""Read-only physical schema context for the Camstar SQL assistant.

The ontology intentionally hides some infrastructure fields. SQL generation
must instead see the authoritative CSV rows, including primary keys and exact
foreign-key columns.
"""

from __future__ import annotations

import csv
import heapq
import itertools
import re
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TABLES_CSV = PROJECT_ROOT / "docs" / "Database_Tables.csv"
FIELDS_CSV = PROJECT_ROOT / "docs" / "Database_Fields.csv"

_INFRASTRUCTURE_TABLES = {
    "A_SetupAccess",
    "ChangeHistory",
    "ChangeStatus",
    "DocumentSet",
    "Owner",
    "SetupAccess",
    "UOM",
    "WIPMsgDefMgr",
}

_PRIMARY_BRIDGE_TABLES = {
    "Container",
    "HistoryMainline",
    "MfgOrder",
    "Product",
    "ProductFamily",
}

_FIELD_HINTS = {
    "名称": ("name",),
    "编号": ("id", "name"),
    "数量": ("qty", "quantity"),
    "产出": ("qty", "quantity"),
    "产量": ("qty", "quantity"),
    "状态": ("status",),
    "时间": ("date", "time", "timestamp"),
    "日期": ("date", "time"),
    "工单": ("mfgorder", "order"),
    "产品": ("product",),
    "容器": ("container",),
    "批次": ("container", "batch", "lot"),
    "工序": ("operation", "spec", "step"),
    "设备": ("resource", "equipment"),
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


@lru_cache(maxsize=1)
def _schema():
    tables = {
        row["CDOName"]: row
        for row in _read_csv(TABLES_CSV)
        if row.get("CDOName")
    }
    fields_by_table: dict[str, list[dict[str, str]]] = {}
    for row in _read_csv(FIELDS_CSV):
        if row.get("CDOName") and row.get("FieldName"):
            fields_by_table.setdefault(row["CDOName"], []).append(row)
    return tables, fields_by_table


@lru_cache(maxsize=1)
def _physical_fk_graph():
    tables, fields_by_table = _schema()
    adjacency: dict[str, list[tuple[str, dict[str, str]]]] = {
        name: [] for name in tables
    }
    for from_table, fields in fields_by_table.items():
        for field in fields:
            if field.get("IsForeignKey", "").lower() != "true":
                continue
            to_table = field.get("FKTableName", "")
            to_field = field.get("FKFieldName", "")
            if not to_table or not to_field or to_table not in tables:
                continue
            edge = {
                "from_table": from_table,
                "from_field": field["FieldName"],
                "to_table": to_table,
                "to_field": to_field,
            }
            adjacency.setdefault(from_table, []).append((to_table, edge))
            if from_table != to_table:
                adjacency.setdefault(to_table, []).append((from_table, edge))
    return adjacency


def find_physical_join_path(
    start_table: str,
    end_table: str,
    *,
    max_hops: int = 4,
) -> list[dict[str, str]]:
    """Return a low-noise path composed only of verified physical FKs."""
    if start_table == end_table:
        return []
    adjacency = _physical_fk_graph()
    if start_table not in adjacency or end_table not in adjacency:
        return []

    sequence = itertools.count()
    queue = [(0, 0, next(sequence), start_table, [])]
    best: dict[tuple[str, int], int] = {}
    while queue:
        cost, hops, _, table, path = heapq.heappop(queue)
        if table == end_table:
            return path
        if hops >= max_hops:
            continue
        state = (table, hops)
        if best.get(state, cost + 1) <= cost:
            continue
        best[state] = cost
        for neighbor, edge in adjacency.get(table, []):
            if any(
                neighbor in {item["from_table"], item["to_table"]}
                for item in path[-1:]
            ) and hops > 0:
                continue
            penalty = 0
            if neighbor != end_table:
                if neighbor in _INFRASTRUCTURE_TABLES:
                    penalty = 12
                elif neighbor not in _PRIMARY_BRIDGE_TABLES:
                    penalty = 2
            if edge["from_field"].lower() != edge["to_field"].lower():
                penalty += 1
            heapq.heappush(
                queue,
                (
                    cost + 1 + penalty,
                    hops + 1,
                    next(sequence),
                    neighbor,
                    path + [edge],
                ),
            )
    return []


def build_physical_join_plan(
    class_names: list[str],
    *,
    max_tables: int = 8,
    max_hops: int = 4,
) -> dict:
    """Connect requested physical tables into a verified FK tree."""
    tables, _ = _schema()
    anchors = list(dict.fromkeys(
        name for name in class_names if name in tables
    ))
    if not anchors:
        return {"tables": [], "joins": [], "unconnected": []}

    selected = [anchors[0]]
    connected = {anchors[0]}
    joins: list[dict[str, str]] = []
    unconnected: list[str] = []
    seen_joins: set[tuple[str, str, str, str]] = set()

    for anchor in anchors[1:]:
        if anchor in connected:
            continue
        candidates = []
        # Keep the user's selection order as the semantic tie-breaker.  In
        # particular, the first selected object is the query root, so when
        # two verified physical paths are equally short we should keep a
        # direct branch from that root instead of silently rewiring the new
        # object through another selected table.
        connected_in_priority_order = [
            table for table in selected if table in connected
        ]
        for start_priority, start in enumerate(connected_in_priority_order):
            path = find_physical_join_path(
                start,
                anchor,
                max_hops=max_hops,
            )
            if path:
                candidates.append((path, start_priority))
        if not candidates:
            if len(selected) < max_tables:
                selected.append(anchor)
            unconnected.append(anchor)
            continue

        path, _ = min(
            candidates,
            key=lambda candidate: (
                len(candidate[0]),
                candidate[1],
                sum(
                    edge["from_table"] in _INFRASTRUCTURE_TABLES
                    or edge["to_table"] in _INFRASTRUCTURE_TABLES
                    for edge in candidate[0]
                ),
                tuple(
                    (
                        edge["from_table"],
                        edge["from_field"],
                        edge["to_table"],
                        edge["to_field"],
                    )
                    for edge in candidate[0]
                ),
            ),
        )
        path_tables = []
        for edge in path:
            path_tables.extend([edge["from_table"], edge["to_table"]])
        new_tables = [
            table for table in dict.fromkeys(path_tables)
            if table not in selected
        ]
        if len(selected) + len(new_tables) > max_tables:
            unconnected.append(anchor)
            continue

        selected.extend(new_tables)
        connected.update(path_tables)
        for edge in path:
            key = (
                edge["from_table"],
                edge["from_field"],
                edge["to_table"],
                edge["to_field"],
            )
            if key not in seen_joins:
                joins.append(edge)
                seen_joins.add(key)

    # Preserve every direct FK between user-requested tables, even when the
    # minimum connecting tree already linked those anchors through a bridge.
    # These direct facts are often the correct SQL path (for example
    # ResourceThruputHistory -> MfgOrder) and should not be hidden merely
    # because another requested table was connected first.
    anchor_set = set(anchors)
    selected_set = set(selected)
    seen_table_pairs = {
        frozenset((edge["from_table"], edge["to_table"]))
        for edge in joins
        if edge["from_table"] != edge["to_table"]
    }
    for table in anchors:
        if table not in selected_set:
            continue
        for neighbor, edge in _physical_fk_graph().get(table, []):
            table_pair = frozenset((table, neighbor))
            if (
                neighbor == table
                or neighbor not in anchor_set
                or neighbor not in selected_set
                or table_pair in seen_table_pairs
            ):
                continue
            key = (
                edge["from_table"],
                edge["from_field"],
                edge["to_table"],
                edge["to_field"],
            )
            if key not in seen_joins:
                joins.append(edge)
                seen_joins.add(key)
                seen_table_pairs.add(table_pair)

    return {
        "tables": selected,
        "joins": joins,
        "unconnected": unconnected,
    }


def _question_field_hints(question: str) -> set[str]:
    lowered = (question or "").lower()
    hints = set(re.findall(r"[a-z][a-z0-9_]+", lowered))
    for phrase, values in _FIELD_HINTS.items():
        if phrase in question:
            hints.update(values)
    return hints


def build_sql_schema_context(
    class_names: list[str],
    *,
    question: str = "",
    max_tables: int = 8,
    max_fields: int = 560,
) -> str:
    """Format exact physical tables, fields, PKs and FKs for an LLM prompt."""
    tables, fields_by_table = _schema()
    requested = list(class_names)
    from src.qa.sql_domain_context import (
        HISTORY_MAINLINE_TABLES,
        history_mainline_companion_tables,
    )

    history_domain_tables = {"HistoryMainline"}
    for companion_group in HISTORY_MAINLINE_TABLES.values():
        history_domain_tables.update(companion_group)
    if history_domain_tables.intersection(requested):

        # HistoryMainline may be appended after many persisted selections.
        # Prioritize the active transaction domain so the six-table cap cannot
        # discard the table the user is currently asking about.
        requested = (
            ["HistoryMainline"]
            + history_mainline_companion_tables(question)
            + [name for name in requested if name != "HistoryMainline"]
        )

    plan = build_physical_join_plan(
        requested,
        max_tables=max_tables,
    )
    selected = plan["tables"]

    if not selected:
        return "未匹配到物理表。不得猜测表名或字段名，应要求用户指定表或在图中选择节点。"

    lines = [
        "以下内容直接来自 Database_Tables.csv 与 Database_Fields.csv；字段名区分大小写按原样输出。",
    ]
    if plan["joins"]:
        lines.append("\n### 已验证物理 JOIN 路径")
        for edge in plan["joins"]:
            lines.append(
                f"- [{edge['from_table']}].[{edge['from_field']}] = "
                f"[{edge['to_table']}].[{edge['to_field']}]"
            )
    if plan["unconnected"]:
        lines.append(
            "\n### 未连通对象\n- 当前物理外键图无法在限定跳数内连接："
            + "、".join(f"[{name}]" for name in plan["unconnected"])
            + "。不得臆造 JOIN。"
        )

    field_hints = _question_field_hints(question)
    remaining = max_fields
    for table_name in selected:
        table = tables[table_name]
        fields = fields_by_table.get(table_name, [])
        lines.append(
            f"\n### 物理表 [{table_name}] "
            f"(CDODefId={table.get('CDODefId', '')}, Workspace={table.get('Workspace', '')})"
        )

        # Put PK/FK rows first so join evidence is retained if the context cap
        # is reached, then keep the CSV order for ordinary fields.
        ordered = sorted(
            enumerate(fields),
            key=lambda item: (
                item[1].get("IsPrimaryKey", "").lower() != "true",
                item[1].get("IsForeignKey", "").lower() != "true",
                not any(
                    hint in item[1]["FieldName"].lower()
                    for hint in field_hints
                ),
                item[0],
            ),
        )
        table_limit = min(90, remaining)
        for _, field in ordered[:table_limit]:
            flags = []
            if field.get("IsPrimaryKey", "").lower() == "true":
                flags.append("PK")
            if field.get("IsCandidateKey", "").lower() == "true":
                flags.append("候选键")
            if field.get("IsList", "").lower() == "true":
                flags.append("List")
            if (
                field.get("IsForeignKey", "").lower() == "true"
                and field.get("FKTableName")
            ):
                flags.append(
                    f"FK→[{field['FKTableName']}].[{field.get('FKFieldName') or '?'}]"
                )
            flag_text = f" | {'; '.join(flags)}" if flags else ""
            lines.append(
                f"- [{field['FieldName']}] "
                f"(DataTypeCode={field.get('DataType', '')}, "
                f"Precision={field.get('Precision', '')}, "
                f"Scale={field.get('Scale', '')}{flag_text})"
            )
        remaining -= min(len(fields), table_limit)
        if remaining <= 0:
            lines.append("- ……字段上下文达到上限；未显示的字段不得猜测。")
            break

    return "\n".join(lines)
