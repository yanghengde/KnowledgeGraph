"""Verified SQL-domain guidance for high-value Camstar table families.

This module does not invent physical schema. Table and column names referenced
here are checked against the read-only Database_*.csv sources by tests and by
``sql_schema_retriever`` before they are exposed to the LLM.
"""

from __future__ import annotations

import re


HISTORY_MAINLINE_TABLES = {
    "move": ("MoveHistory", "MoveInHistory"),
    "track": ("A_TrackInLotHistory", "A_TrackOutLotHistory"),
    "throughput": (
        "ThruputHistory",
        "ThruputHistoryDetail",
        "ResourceThruputHistory",
        "ResourceThruputHistoryDetails",
    ),
    "start": ("StartHistoryDetail",),
    "quantity": ("QtyHistory", "QtyHistoryDetails"),
    "split": ("SplitHistory", "SplitHistoryDetails"),
    "combine": ("CombineHistory", "CombineHistoryDetail"),
    "hold_release": ("HoldReleaseHistory", "HoldReleaseHistoryDetail"),
    "resource_status": ("ResourceStatusHistory",),
}

_MOVE_INTENT = re.compile(
    r"\bmove\b|move\s*记录|移动记录|移动历史|过站|工艺流转|"
    r"流程轨迹|路径|站点|工序流转|历史轨迹",
    re.IGNORECASE,
)
_TRACK_INTENT = re.compile(
    r"track\s*in|track\s*out|trackin|trackout|进站|出站|上机|下机",
    re.IGNORECASE,
)
_THROUGHPUT_INTENT = re.compile(
    r"thruput|throughput|产出|产量|生产数量|良率|yield",
    re.IGNORECASE,
)
_START_INTENT = re.compile(r"开工历史|开工记录|启动批次|\bstart\s+history\b", re.I)
_QUANTITY_INTENT = re.compile(r"数量变更|数量调整|调整数量|\bqty\s*history\b", re.I)
_SPLIT_INTENT = re.compile(r"拆分历史|拆分记录|批次拆分|\bsplit\s+history\b", re.I)
_COMBINE_INTENT = re.compile(r"合并历史|合并记录|批次合并|\bcombine\s+history\b", re.I)
_HOLD_RELEASE_INTENT = re.compile(
    r"(?:暂停|Hold|释放|Release).{0,6}(?:历史|记录)|"
    r"(?:历史|记录).{0,6}(?:暂停|Hold|释放|Release)",
    re.I,
)
_RESOURCE_STATUS_INTENT = re.compile(
    r"(?:设备|资源).{0,6}状态.{0,6}(?:历史|记录)|"
    r"\bresource\s+status\s+history\b",
    re.I,
)


def history_mainline_companion_tables(question: str = "") -> list[str]:
    """Return the smallest useful set of detail tables for the question."""
    groups: list[str] = []
    if _MOVE_INTENT.search(question):
        groups.append("move")
    if _TRACK_INTENT.search(question):
        groups.append("track")
    if _THROUGHPUT_INTENT.search(question):
        groups.append("throughput")
    if _START_INTENT.search(question):
        groups.append("start")
    if _QUANTITY_INTENT.search(question):
        groups.append("quantity")
    if _SPLIT_INTENT.search(question):
        groups.append("split")
    if _COMBINE_INTENT.search(question):
        groups.append("combine")
    if _HOLD_RELEASE_INTENT.search(question):
        groups.append("hold_release")
    if _RESOURCE_STATUS_INTENT.search(question):
        groups.append("resource_status")

    # A broad question about HistoryMainline needs a compact map of the domain.
    if not groups:
        return [
            "MoveHistory",
            "MoveInHistory",
            "ThruputHistory",
            "A_TrackInLotHistory",
            "A_TrackOutLotHistory",
        ]

    tables: list[str] = []
    for group in groups:
        for table in HISTORY_MAINLINE_TABLES[group]:
            if table not in tables:
                tables.append(table)
    return tables


def build_sql_domain_context(class_names: list[str], question: str = "") -> str:
    """Build cautious business guidance for HistoryMainline SQL generation."""
    names = set(class_names)
    history_tables = {"HistoryMainline"}
    for tables in HISTORY_MAINLINE_TABLES.values():
        history_tables.update(tables)
    if not names.intersection(history_tables):
        return ""

    companions = history_mainline_companion_tables(question)
    lines = ["""### HistoryMainline 交易域（已核对物理字段与外键）
- [HistoryMainline] 是 WIP 交易历史主线/公共上下文，不应理解为“所有 Move 细节都只存在这一张表”。
"""]
    if "MoveHistory" in companions:
        lines.append(
            "- 容器事务时间线可从 [HistoryMainline] 查询；精确过站的 From/To 工序、步骤和路径细节，应通过\n"
            "  [MoveHistory].[HistoryMainlineId] = [HistoryMainline].[HistoryMainlineId] 获取。\n"
            "- Move-In 补充信息在 [MoveInHistory]，同样以 [HistoryMainlineId] 连接主线。"
        )
    if "A_TrackInLotHistory" in companions:
        lines.append(
            "- 半导体 Track In/Track Out 数量分别在 [A_TrackInLotHistory] 与 "
            "[A_TrackOutLotHistory]，均以 [HistoryMainlineId] 连接主线。"
        )
    if "ThruputHistory" in companions:
        throughput = (
            "- 产出/吞吐数量优先从 [ThruputHistory] 聚合，不能用 "
            "COUNT(HistoryMainlineId) 代替产量。"
        )
        if "ThruputHistoryDetail" in companions:
            throughput += (
                "需要拆分到明细容器时再连接 "
                "[ThruputHistoryDetail].[ThruputHistoryId] = "
                "[ThruputHistory].[ThruputHistoryId]。"
            )
        if "ResourceThruputHistory" in companions:
            throughput += "资源级产出使用 [ResourceThruputHistory]。"
        lines.append(throughput)
    if "StartHistoryDetail" in companions:
        lines.append(
            "- 开工事务的工单、产品、批次、数量、工艺步骤和资源快照在 "
            "[StartHistoryDetail]，通过 [HistoryMainlineId] 连接交易主线。"
        )
    if "QtyHistory" in companions:
        lines.append(
            "- 数量变更主记录在 [QtyHistory]；容器、产品、工序和UOM拆分明细在 "
            "[QtyHistoryDetails]，通过 [QtyHistoryId] 连接。"
        )
    if "SplitHistory" in companions:
        lines.append(
            "- 拆分事务主记录在 [SplitHistory]；目标容器和拆分数量明细在 "
            "[SplitHistoryDetails]，通过 [SplitHistoryId] 连接。"
        )
    if "CombineHistory" in companions:
        lines.append(
            "- 合并事务主记录在 [CombineHistory]；参与合并的源容器明细在 "
            "[CombineHistoryDetail]，通过 [CombineHistoryId] 连接。"
        )
    if "HoldReleaseHistory" in companions:
        lines.append(
            "- Hold/Release原因和位置在 [HoldReleaseHistory]；受影响容器在 "
            "[HoldReleaseHistoryDetail]，通过 [HoldReleaseHistoryId] 连接。"
        )
    if "ResourceStatusHistory" in companions:
        lines.append(
            "- 设备状态、原因、位置、产品、设置和预留变化在 "
            "[ResourceStatusHistory]，通过 [HistoryMainlineId] 连接交易主线。"
        )
    lines.append("""
- [TxnType]、[BaseTxnType]、[CompoundTxnType] 的枚举值未由当前物理 CSV 给出。不得猜测数值含义；
  在获得现场权威映射前，优先展示/参数化 [TxnServiceName]，并用相应子历史表是否存在来确认事件类型。
- 时间口径必须让用户确认：[TxnDate]/[TxnDateGMT] 与 [SystemDate]/[SystemDateGMT] 均存在。
  未确认工厂时区和报表口径时，不得擅自混用本地时间与 GMT。
- 做产量或次数统计前，要明确反冲/撤销、复合事务、拆分合并、返工和批次子容器的去重口径；
  当前仅能看到 [ReversalStatus]、[CompoundTxnType]、[InRework] 等字段，不能臆造其枚举规则。
""")
    return "\n".join(lines)
