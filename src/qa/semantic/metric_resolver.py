"""Deterministically resolve natural-language questions to metric contracts."""

from __future__ import annotations

import re
from typing import Any

from .metric_catalog import get_metric


_THROUGHPUT = re.compile(r"(?:产出|产量|throughput|thruput)", re.I)
_QUANTITY_WORD = re.compile(r"(?:数量|总量|多少|汇总|统计|合计|qty)", re.I)
_SEMANTIC_QUERY = re.compile(
    r"(?:查询|查看|列出|统计|汇总|合计|多少|报表|趋势|数量|时长|"
    r"\bselect\b|\bsql\b)",
    re.I,
)
_UNSAFE_OR_SCHEMA_ONLY = re.compile(
    r"(?:删除|修改|更新|插入|建表|删表|truncate|drop|delete|update|insert|"
    r"字段|列名|schema|表结构)",
    re.I,
)


def resolve_metric(
    question: str,
    *,
    dialect: str | None = None,
) -> dict[str, Any] | None:
    text = question or ""

    if re.search(r"(?:良率|直通率|一次通过率|\byield\b)", text, re.I):
        return None

    metric_id = None
    if re.search(r"(?:当前|实时).{0,8}(?:WIP|在制|批次|容器).{0,8}(?:数量|Qty)|"
                 r"(?:WIP|在制).{0,8}(?:数量|Qty)", text, re.I):
        metric_id = "wip.current_qty"
    elif (
        re.search(r"(?:批次|容器|Container)", text, re.I)
        and re.search(r"(?:名称|状态|当前数量|明细|ContainerName|Status)", text, re.I)
        and not re.search(r"(?:历史|产出|产量|move|拆分|合并)", text, re.I)
    ):
        metric_id = "container.current_detail"
    elif _THROUGHPUT.search(text):
        if re.search(r"(?:工单|MfgOrder)", text, re.I):
            metric_id = "throughput.by_mfg_order"
        elif re.search(r"(?:设备|资源|Resource)", text, re.I):
            metric_id = "throughput.by_resource"
        elif re.search(r"(?:工序|Operation)", text, re.I):
            metric_id = "throughput.by_operation"
        else:
            metric_id = "throughput.total_qty"
    elif re.search(r"(?:track\s*in|trackin|进站|上机)", text, re.I) and _QUANTITY_WORD.search(text):
        metric_id = "track_in.qty"
    elif re.search(r"(?:track\s*out|trackout|出站|下机)", text, re.I) and _QUANTITY_WORD.search(text):
        metric_id = "track_out.qty"
    elif (
        re.search(r"(?:move|移动|过站)", text, re.I)
        and re.search(r"(?:次数|多少次|计数|count)", text, re.I)
    ):
        metric_id = "move.event_count"
    elif re.search(r"(?:开工|启动批次|start)", text, re.I) and _QUANTITY_WORD.search(text):
        metric_id = "start.qty"
    elif re.search(r"(?:数量变更|数量调整|调整数量|qty\s*history)", text, re.I):
        metric_id = "quantity_change.recorded_qty"
    elif re.search(r"(?:拆分|split)", text, re.I) and _QUANTITY_WORD.search(text):
        metric_id = "split.qty"
    elif re.search(r"(?:合并|combine)", text, re.I) and _QUANTITY_WORD.search(text):
        metric_id = "combine.qty"
    elif (
        re.search(r"(?:hold|暂停|冻结)", text, re.I)
        and re.search(r"(?:持续时间|时长|duration)", text, re.I)
    ):
        metric_id = "hold.duration"
    elif (
        re.search(r"(?:设备|资源|resource).{0,8}状态", text, re.I)
        and re.search(r"(?:变更次数|次数|多少次|count)", text, re.I)
    ):
        metric_id = "resource_status.change_count"

    if metric_id:
        return get_metric(metric_id)

    if (
        _SEMANTIC_QUERY.search(text)
        and not _UNSAFE_OR_SCHEMA_ONLY.search(text)
    ):
        from .example_index import resolve_metric_id_semantically

        return get_metric(resolve_metric_id_semantically(
            text,
            dialect=dialect,
        ))
    return None
