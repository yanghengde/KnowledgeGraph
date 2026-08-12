"""Deterministic entity resolution for the read-only SQL assistant."""

from __future__ import annotations

import re
from collections.abc import Iterable


_INTENT_RULES: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...] = (
    (
        re.compile(
            r"\bmove\b|过站|移动记录|move\s*记录|移动历史|过站历史|"
            r"工艺流转|流程轨迹|历史轨迹|流转记录",
            re.IGNORECASE,
        ),
        ("HistoryMainline", "MoveHistory"),
    ),
    (
        re.compile(
            r"\b(?:throughput|thruput|yield)\b|产出|产量|良率",
            re.IGNORECASE,
        ),
        ("HistoryMainline", "ThruputHistory"),
    ),
    (
        re.compile(
            r"(?:工单|设备|资源).{0,12}(?:产出|产量|throughput|thruput)|"
            r"(?:产出|产量|throughput|thruput).{0,12}(?:工单|设备|资源)",
            re.IGNORECASE,
        ),
        ("ResourceThruputHistory",),
    ),
    (
        re.compile(
            r"(?:产出|产量|throughput|thruput).{0,8}(?:明细|detail)|"
            r"(?:明细|detail).{0,8}(?:产出|产量|throughput|thruput)",
            re.IGNORECASE,
        ),
        ("ThruputHistoryDetail",),
    ),
    (
        re.compile(
            r"track\s*in|track\s*out|trackin|trackout|进站|出站|上机|下机",
            re.IGNORECASE,
        ),
        (
            "HistoryMainline",
            "A_TrackInLotHistory",
            "A_TrackOutLotHistory",
        ),
    ),
    (
        re.compile(r"\bstart\s+history\b|开工历史|开工记录|启动批次", re.IGNORECASE),
        ("HistoryMainline", "StartHistoryDetail"),
    ),
    (
        re.compile(
            r"\bqty\s*history\b|数量变更|数量调整|调整数量",
            re.IGNORECASE,
        ),
        ("HistoryMainline", "QtyHistory", "QtyHistoryDetails"),
    ),
    (
        re.compile(r"\bsplit\s+history\b|拆分历史|拆分记录|批次拆分", re.IGNORECASE),
        ("HistoryMainline", "SplitHistory", "SplitHistoryDetails"),
    ),
    (
        re.compile(
            r"\bcombine\s+history\b|合并历史|合并记录|批次合并",
            re.IGNORECASE,
        ),
        ("HistoryMainline", "CombineHistory", "CombineHistoryDetail"),
    ),
    (
        re.compile(
            r"\bhold\s*(?:release\s*)?history\b|\brelease\s+history\b|"
            r"(?:暂停|Hold|释放|Release).{0,6}(?:历史|记录)|"
            r"(?:历史|记录).{0,6}(?:暂停|Hold|释放|Release)",
            re.IGNORECASE,
        ),
        ("HistoryMainline", "HoldReleaseHistory", "HoldReleaseHistoryDetail"),
    ),
    (
        re.compile(
            r"(?:设备|资源).{0,6}状态.{0,6}(?:历史|记录)|"
            r"\bresource\s+status\s+history\b",
            re.IGNORECASE,
        ),
        ("HistoryMainline", "ResourceStatusHistory"),
    ),
)


def _append_unique(target: list[str], values: Iterable[str], allowed: set[str]):
    for value in values:
        if value in allowed and value not in target:
            target.append(value)


def resolve_sql_entities(
    question: str,
    class_names: Iterable[str],
    chinese_map: dict[str, str] | None = None,
) -> list[str]:
    """Resolve exact ontology objects without substring collisions.

    Priority is explicit ``[[Class]]``/``@Class`` mentions, exact English class
    names, longest non-overlapping Chinese aliases, then conservative SQL-domain
    intent rules. No arbitrary fallback object is returned.
    """
    question = question or ""
    canonical = {name.lower(): name for name in class_names if name}
    allowed = set(canonical.values())
    result: list[str] = []

    explicit = re.findall(
        r"\[\[([A-Za-z_][A-Za-z0-9_]*)\]\]|"
        r"(?<![\w])@([A-Za-z_][A-Za-z0-9_]*)",
        question,
    )
    for bracketed, at_name in explicit:
        matched = canonical.get((bracketed or at_name).lower())
        if matched:
            _append_unique(result, [matched], allowed)

    occupied: list[tuple[int, int]] = []
    for lowered, name in sorted(
        canonical.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        pattern = re.compile(
            rf"(?<![A-Za-z0-9_]){re.escape(lowered)}"
            rf"(?![A-Za-z0-9_])",
            re.IGNORECASE,
        )
        for match in pattern.finditer(question):
            span = match.span()
            if any(span[0] < end and span[1] > start for start, end in occupied):
                continue
            _append_unique(result, [name], allowed)
            occupied.append(span)

    chinese_occupied: list[tuple[int, int]] = []
    aliases = chinese_map or {}
    for alias, name in sorted(
        aliases.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if not alias or name not in allowed:
            continue
        for match in re.finditer(re.escape(alias), question, re.IGNORECASE):
            span = match.span()
            if any(
                span[0] < end and span[1] > start
                for start, end in chinese_occupied
            ):
                continue
            _append_unique(result, [name], allowed)
            chinese_occupied.append(span)

    for pattern, entities in _INTENT_RULES:
        if pattern.search(question):
            _append_unique(result, entities, allowed)

    return result


def recent_selected_classes(history: list[dict] | None) -> list[str]:
    """Return the last user turn's resolved objects, never assistant prose."""
    for turn in reversed(history or []):
        if turn.get("role") != "user":
            continue
        selected = turn.get("selected_classes") or []
        if selected:
            return list(dict.fromkeys(
                value for value in selected if isinstance(value, str) and value
            ))
    return []
