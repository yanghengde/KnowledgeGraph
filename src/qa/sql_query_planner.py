"""Deterministic business-intent planning for the read-only SQL assistant."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


_MOVE = re.compile(r"(?:move|移动|过站|移站|move\s*记录|移动记录|移动历史)", re.I)
_THROUGHPUT = re.compile(r"(?:产出|产量|throughput|thruput)", re.I)
_YIELD = re.compile(r"(?:良率|直通率|一次通过率|\byield\b)", re.I)
_START_HISTORY = re.compile(r"(?:开工历史|开工记录|启动批次|\bstart\s+history\b)", re.I)
_QUANTITY_HISTORY = re.compile(r"(?:数量变更|数量调整|调整数量|\bqty\s*history\b)", re.I)
_SPLIT_HISTORY = re.compile(r"(?:拆分历史|拆分记录|批次拆分|\bsplit\s+history\b)", re.I)
_COMBINE_HISTORY = re.compile(r"(?:合并历史|合并记录|批次合并|\bcombine\s+history\b)", re.I)
_HOLD_RELEASE_HISTORY = re.compile(
    r"(?:暂停|Hold|释放|Release).{0,6}(?:历史|记录)|"
    r"(?:历史|记录).{0,6}(?:暂停|Hold|释放|Release)",
    re.I,
)
_RESOURCE_STATUS_HISTORY = re.compile(
    r"(?:设备|资源).{0,6}状态.{0,6}(?:历史|记录)|"
    r"\bresource\s+status\s+history\b",
    re.I,
)
_WIP = re.compile(r"(?:在制品|\bWIP\b|当前批次|当前在制)", re.I)
_FIELD_LIST = re.compile(r"(?:字段|列名|schema|结构|有哪些列)", re.I)
_TODAY = re.compile(r"(?:今天|今日|\btoday\b)", re.I)
_YESTERDAY = re.compile(r"(?:昨天|昨日|\byesterday\b)", re.I)
_RANGE = re.compile(
    r"(?:时间范围|日期范围|开始时间|结束时间|从.+?到|近\s*\d+\s*(?:天|小时)|"
    r"\blast\s+\d+\s+(?:days?|hours?)\b)",
    re.I,
)

_DIMENSIONS = (
    ("MfgOrder", ("工单", "制造工单", "MfgOrder")),
    ("Operation", ("工序", "Operation")),
    ("ResourceDef", ("设备", "资源", "Resource", "ResourceDef")),
    ("ProductFamily", ("产品族", "ProductFamily")),
    ("Product", ("产品", "物料", "Product")),
    ("Container", ("批次", "容器", "Container")),
)


@dataclass
class SqlQueryPlan:
    version: int = 1
    original_question: str = ""
    effective_question: str = ""
    entities: list[str] = field(default_factory=list)
    dialect: str = "oracle"
    intent: str = "detail_query"
    metric: str = "明细记录"
    metric_id: str | None = None
    fact_table: str | None = None
    metric_status: str | None = None
    dimensions: list[str] = field(default_factory=list)
    grain: str = "明细记录"
    time_scope: str = "未指定"
    time_basis: str | None = None
    filters: list[str] = field(default_factory=list)
    business_definition: str | None = None
    ambiguities: list[str] = field(default_factory=list)
    clarification_key: str | None = None
    clarification_question: str | None = None
    needs_clarification: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "SqlQueryPlan | None":
        if not value:
            return None
        allowed = cls.__dataclass_fields__
        return cls(**{key: item for key, item in value.items() if key in allowed})


def _contains_alias(question: str, alias: str) -> bool:
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", alias):
        return bool(re.search(rf"\b{re.escape(alias)}\b", question, re.I))
    return alias in question


def _dimensions(question: str, entities: list[str]) -> list[str]:
    result = []
    for class_name, aliases in _DIMENSIONS:
        if class_name in entities or any(
            _contains_alias(question, alias) for alias in aliases
        ):
            result.append(class_name)
    return result


def _time_scope(question: str) -> str:
    if _TODAY.search(question):
        return "今日"
    if _YESTERDAY.search(question):
        return "昨日"
    if _RANGE.search(question):
        return "用户指定范围"
    return "未指定"


def _explicit_time_basis(question: str) -> str | None:
    if re.search(r"(?:SystemDateGMT|系统\s*(?:GMT|UTC)\s*时间)", question, re.I):
        return "SystemDateGMT"
    if re.search(r"(?:TxnDateGMT|交易\s*(?:GMT|UTC)\s*时间)", question, re.I):
        return "TxnDateGMT"
    if re.search(r"(?:SystemDate|系统时间)", question, re.I):
        return "SystemDate"
    if re.search(r"(?:TxnDate|本地交易时间|交易时间|本地时间)", question, re.I):
        return "TxnDate"
    if re.search(r"\b(?:GMT|UTC)\b", question, re.I):
        return "TxnDateGMT"
    return None


def _resolve_followup(plan: SqlQueryPlan, answer: str) -> bool:
    key = plan.clarification_key
    if key == "time_scope":
        selected = _time_scope(answer)
        if selected != "未指定":
            plan.time_scope = selected
            plan.time_basis = _explicit_time_basis(answer) or plan.time_basis
            return True
        return False
    if key == "time_basis":
        selected = _explicit_time_basis(answer)
        if selected:
            plan.time_basis = selected
            return True
        return False
    if key == "yield_definition":
        compact = " ".join(answer.split())
        if len(compact) >= 4:
            plan.business_definition = compact
            return True
        return False
    if key == "wip_scope":
        if re.search(r"(?:当前|实时|现状|current)", answer, re.I):
            plan.business_definition = "当前在制状态"
            return True
        if re.search(r"(?:历史|时间范围|history)", answer, re.I):
            plan.business_definition = "历史在制变化"
            return True
        return False
    return False


def _set_next_ambiguity(plan: SqlQueryPlan) -> None:
    plan.ambiguities = []
    plan.clarification_key = None
    plan.clarification_question = None

    metric_contract = None
    if plan.metric_id:
        from src.qa.semantic.metric_catalog import get_metric
        metric_contract = get_metric(plan.metric_id)

    if (
        metric_contract
        and metric_contract.get("requiresTimeRange")
        and plan.time_scope == "未指定"
    ):
        plan.ambiguities.append("尚未指定统计时间范围")
        plan.clarification_key = "time_scope"
        plan.clarification_question = (
            "请指定统计时间范围，例如“今日”“昨日”“近7天”，"
            "或给出明确的开始和结束时间。"
        )
    elif (
        metric_contract
        and metric_contract.get("requiresTimeRange")
        and not plan.time_basis
    ):
        plan.ambiguities.append("尚未确定时间字段口径")
        plan.clarification_key = "time_basis"
        plan.clarification_question = (
            "这次时间范围使用本地交易时间 `TxnDate`，"
            "还是 GMT/UTC 交易时间 `TxnDateGMT`？"
        )
    elif (
        plan.intent in {
            "throughput",
            "move_history",
            "start_history",
            "quantity_history",
            "split_history",
            "combine_history",
            "hold_release_history",
            "resource_status_history",
        }
        and plan.time_scope != "未指定"
        and not plan.time_basis
    ):
        plan.ambiguities.append("尚未确定时间字段口径")
        plan.clarification_key = "time_basis"
        plan.clarification_question = (
            "这次时间范围使用本地交易时间 `TxnDate`，"
            "还是 GMT/UTC 交易时间 `TxnDateGMT`？"
        )
    elif plan.intent == "yield" and not plan.business_definition:
        plan.ambiguities.append("尚未确定良率的分子和分母")
        plan.clarification_key = "yield_definition"
        plan.clarification_question = (
            "请确认良率口径，例如“合格产出数量 ÷ 总产出数量”；"
            "如果你们已有固定分子、分母字段，也请直接说明。"
        )
    elif (
        plan.intent == "current_wip"
        and not plan.metric_id
        and not plan.business_definition
    ):
        plan.ambiguities.append("尚未确定查询当前快照还是历史变化")
        plan.clarification_key = "wip_scope"
        plan.clarification_question = (
            "你要查询“当前实时在制状态”，还是“某个时间范围内的在制变化历史”？"
        )

    plan.needs_clarification = bool(plan.clarification_key)


def build_sql_query_plan(
    question: str,
    entities: list[str],
    dialect: str = "oracle",
    pending_plan: dict[str, Any] | None = None,
) -> SqlQueryPlan:
    """Build a plan, or resolve the pending plan from one clarification answer."""
    pending = SqlQueryPlan.from_dict(pending_plan)
    if (
        pending
        and entities
        and set(entities) != set(pending.entities)
    ):
        # An explicit new object selection starts a new request instead of
        # being consumed as the answer to an older clarification.
        pending = None
    if pending and pending.needs_clarification:
        resolved = _resolve_followup(pending, question)
        pending.effective_question = (
            f"{pending.original_question}\n用户补充确认：{question}"
        )
        if resolved:
            _set_next_ambiguity(pending)
        return pending

    intent = "detail_query"
    metric = "明细记录"
    if _MOVE.search(question):
        intent, metric = "move_history", "移动/过站记录"
    elif _YIELD.search(question):
        intent, metric = "yield", "良率"
    elif _THROUGHPUT.search(question):
        intent, metric = "throughput", "产出数量"
    elif _START_HISTORY.search(question):
        intent, metric = "start_history", "开工记录"
    elif _QUANTITY_HISTORY.search(question):
        intent, metric = "quantity_history", "数量变更记录"
    elif _SPLIT_HISTORY.search(question):
        intent, metric = "split_history", "拆分记录"
    elif _COMBINE_HISTORY.search(question):
        intent, metric = "combine_history", "合并记录"
    elif _HOLD_RELEASE_HISTORY.search(question):
        intent, metric = "hold_release_history", "暂停/释放记录"
    elif _RESOURCE_STATUS_HISTORY.search(question):
        intent, metric = "resource_status_history", "资源状态变更记录"
    elif _WIP.search(question):
        intent, metric = "current_wip", "在制数量/状态"
    elif _FIELD_LIST.search(question):
        intent, metric = "describe_fields", "物理字段清单"

    dimensions = _dimensions(question, entities)
    if dimensions:
        grain = "每个" + "、".join(
            {
                "MfgOrder": "工单",
                "Operation": "工序",
                "ResourceDef": "设备",
                "ProductFamily": "产品族",
                "Product": "产品",
                "Container": "批次",
            }.get(item, item)
            for item in dimensions
        )
    else:
        grain = "明细记录"

    from src.qa.semantic.metric_resolver import resolve_metric
    metric_contract = resolve_metric(question, dialect=dialect)
    if metric_contract:
        intent = metric_contract["intent"]
        metric = metric_contract["nameZh"]

    plan = SqlQueryPlan(
        original_question=question,
        effective_question=question,
        entities=list(dict.fromkeys(entities)),
        dialect=(dialect or "oracle").lower(),
        intent=intent,
        metric=metric,
        metric_id=metric_contract["id"] if metric_contract else None,
        fact_table=metric_contract["factTable"] if metric_contract else None,
        metric_status=metric_contract.get("status") if metric_contract else None,
        dimensions=dimensions,
        grain=grain,
        time_scope=_time_scope(question),
        time_basis=_explicit_time_basis(question),
    )
    _set_next_ambiguity(plan)
    return plan


def format_query_plan_context(plan: SqlQueryPlan | dict[str, Any] | None) -> str:
    value = plan if isinstance(plan, SqlQueryPlan) else SqlQueryPlan.from_dict(plan)
    if not value:
        return ""
    lines = [
        f"- 查询意图：{value.intent}",
        f"- 业务对象：{'、'.join(value.entities) or '未识别'}",
        f"- 指标：{value.metric}",
        f"- 维度：{'、'.join(value.dimensions) or '无明确分组维度'}",
        f"- 结果粒度：{value.grain}",
        f"- 时间范围：{value.time_scope}",
        f"- 时间字段：{value.time_basis or '未确认'}",
    ]
    if value.metric_id:
        lines.insert(3, f"- 指标合同：{value.metric_id}")
        lines.insert(4, f"- 事实表：{value.fact_table}")
    if value.business_definition:
        lines.append(f"- 业务口径：{value.business_definition}")
    if value.time_scope != "未指定" and value.time_basis:
        lines.append(
            "- 时间过滤要求：使用半开区间 `时间字段 >= :start_time AND "
            "时间字段 < :end_time`（SQL Server 改用 @ 参数）；"
            "不要对时间字段使用 TRUNC、CAST 或 CONVERT。"
        )
    return "\n".join(lines)


def format_query_plan_markdown(
    plan: SqlQueryPlan | dict[str, Any] | None,
) -> str:
    value = plan if isinstance(plan, SqlQueryPlan) else SqlQueryPlan.from_dict(plan)
    if not value:
        return ""
    rows = [
        f"- 业务对象：{'、'.join(f'`{item}`' for item in value.entities) or '未识别'}",
        f"- 指标：{value.metric}",
        f"- 粒度：{value.grain}",
        f"- 时间范围：{value.time_scope}",
        f"- 时间字段：`{value.time_basis}`" if value.time_basis else "- 时间字段：待确认",
    ]
    if value.metric_id:
        rows.insert(2, f"- 指标合同：`{value.metric_id}`")
        rows.insert(3, f"- 事实表：`{value.fact_table}`")
    if value.business_definition:
        rows.append(f"- 业务口径：{value.business_definition}")
    output = "### 查询理解\n\n" + "\n".join(rows)
    if value.clarification_question:
        output += f"\n\n### 需要你确认\n\n{value.clarification_question}"
    return output
