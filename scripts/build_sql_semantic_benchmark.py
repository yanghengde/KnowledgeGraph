#!/usr/bin/env python3
"""Build the reviewed 50-case semantic SQL Golden regression fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.qa.semantic.metric_resolver import resolve_metric
from src.qa.semantic.sql_renderer import render_metric_sql
from src.qa.sql_query_planner import build_sql_query_plan


OUTPUT = PROJECT_ROOT / "src" / "tests" / "fixtures" / "sql_semantic_benchmark.jsonl"


CASES = [
    # Container detail (4)
    ("container_001", "chat_log", "查询状态为0的批次，返回批次名称、状态、当前数量和产品名称", "oracle", "container.current_detail"),
    ("container_002", "chat_log_derived", "按ContainerId查询批次名称、状态、当前数量以及对应产品名称", "sqlserver", "container.current_detail"),
    ("container_003", "schema_grounded_business_scenario", "查询容器名称、状态、Qty和产品名称明细", "oracle", "container.current_detail"),
    ("container_004", "schema_grounded_business_scenario", "用SQL Server列出批次名称、状态、当前数量和产品名称", "sqlserver", "container.current_detail"),
    # Current WIP snapshot (4)
    ("wip_001", "schema_grounded_business_scenario", "查询当前WIP数量", "oracle", "wip.current_qty"),
    ("wip_002", "schema_grounded_business_scenario", "汇总实时在制品Qty", "sqlserver", "wip.current_qty"),
    ("wip_003", "schema_grounded_business_scenario", "当前批次数量合计是多少", "oracle", "wip.current_qty"),
    ("wip_004", "schema_grounded_business_scenario", "用SQL Server统计当前在制容器数量", "sqlserver", "wip.current_qty"),
    # Total throughput (4)
    ("throughput_total_001", "schema_grounded_business_scenario", "按TxnDate统计今日总产出数量", "oracle", "throughput.total_qty"),
    ("throughput_total_002", "schema_grounded_business_scenario", "按TxnDateGMT统计昨日总产量", "sqlserver", "throughput.total_qty"),
    ("throughput_total_003", "schema_grounded_business_scenario", "使用本地交易时间统计近7天总throughput", "oracle", "throughput.total_qty"),
    ("throughput_total_004", "schema_grounded_business_scenario", "使用SystemDate查询今日总产出", "sqlserver", "throughput.total_qty"),
    # Throughput by MfgOrder (5)
    ("throughput_order_001", "chat_log_derived", "请写一个今日工单产出的sql，使用本地交易时间", "oracle", "throughput.by_mfg_order"),
    ("throughput_order_002", "schema_grounded_business_scenario", "按TxnDateGMT统计昨日每个工单的产量", "sqlserver", "throughput.by_mfg_order"),
    ("throughput_order_003", "schema_grounded_business_scenario", "使用TxnDate汇总近7天MfgOrder产出", "oracle", "throughput.by_mfg_order"),
    ("throughput_order_004", "schema_grounded_business_scenario", "按系统时间统计今日制造工单throughput", "sqlserver", "throughput.by_mfg_order"),
    ("throughput_order_005", "schema_grounded_business_scenario", "用SystemDateGMT统计昨日各工单产出数量", "oracle", "throughput.by_mfg_order"),
    # Throughput by resource (4)
    ("throughput_resource_001", "schema_grounded_business_scenario", "按TxnDate统计今日每台设备产出数量", "oracle", "throughput.by_resource"),
    ("throughput_resource_002", "schema_grounded_business_scenario", "按TxnDateGMT查询昨日资源产量", "sqlserver", "throughput.by_resource"),
    ("throughput_resource_003", "schema_grounded_business_scenario", "使用本地交易时间汇总近7天Resource throughput", "oracle", "throughput.by_resource"),
    ("throughput_resource_004", "schema_grounded_business_scenario", "使用SystemDate统计今日设备产出", "sqlserver", "throughput.by_resource"),
    # Throughput by operation (4)
    ("throughput_operation_001", "schema_grounded_business_scenario", "按TxnDate统计今日每个工序产出数量", "oracle", "throughput.by_operation"),
    ("throughput_operation_002", "schema_grounded_business_scenario", "按TxnDateGMT查询昨日Operation产量", "sqlserver", "throughput.by_operation"),
    ("throughput_operation_003", "schema_grounded_business_scenario", "用本地交易时间汇总近7天工序throughput", "oracle", "throughput.by_operation"),
    ("throughput_operation_004", "schema_grounded_business_scenario", "按SystemDateGMT统计今日各工序产出", "sqlserver", "throughput.by_operation"),
    # Track In (3)
    ("track_in_001", "schema_grounded_business_scenario", "按TxnDate统计今日Track In数量", "oracle", "track_in.qty"),
    ("track_in_002", "schema_grounded_business_scenario", "按TxnDateGMT汇总昨日批次进站数量", "sqlserver", "track_in.qty"),
    ("track_in_003", "schema_grounded_business_scenario", "使用本地交易时间查询近7天上机Qty", "oracle", "track_in.qty"),
    # Track Out (3)
    ("track_out_001", "schema_grounded_business_scenario", "按TxnDate统计今日Track Out数量", "oracle", "track_out.qty"),
    ("track_out_002", "schema_grounded_business_scenario", "按TxnDateGMT汇总昨日批次出站数量", "sqlserver", "track_out.qty"),
    ("track_out_003", "schema_grounded_business_scenario", "使用本地交易时间查询近7天下机Qty", "oracle", "track_out.qty"),
    # Move count (4)
    ("move_001", "schema_grounded_business_scenario", "按TxnDate统计今日批次Move次数", "oracle", "move.event_count"),
    ("move_002", "schema_grounded_business_scenario", "按TxnDateGMT查询昨日过站次数", "sqlserver", "move.event_count"),
    ("move_003", "schema_grounded_business_scenario", "使用本地交易时间统计近7天移动多少次", "oracle", "move.event_count"),
    ("move_004", "schema_grounded_business_scenario", "按SystemDate统计今日move count", "sqlserver", "move.event_count"),
    # Start quantity (4)
    ("start_001", "schema_grounded_business_scenario", "按TxnDate统计今日开工数量", "oracle", "start.qty"),
    ("start_002", "schema_grounded_business_scenario", "按TxnDateGMT查询昨日启动批次数量", "sqlserver", "start.qty"),
    ("start_003", "schema_grounded_business_scenario", "使用本地交易时间汇总近7天开工Qty", "oracle", "start.qty"),
    ("start_004", "schema_grounded_business_scenario", "按SystemDate统计今日start数量", "sqlserver", "start.qty"),
    # Quantity change (3)
    ("qty_change_001", "schema_grounded_business_scenario", "按TxnDate统计今日数量调整记录量", "oracle", "quantity_change.recorded_qty"),
    ("qty_change_002", "schema_grounded_business_scenario", "按TxnDateGMT汇总昨日数量变更Qty", "sqlserver", "quantity_change.recorded_qty"),
    ("qty_change_003", "schema_grounded_business_scenario", "使用本地交易时间查询近7天调整数量", "oracle", "quantity_change.recorded_qty"),
    # Split (2)
    ("split_001", "schema_grounded_business_scenario", "按TxnDate统计今日批次拆分数量", "oracle", "split.qty"),
    ("split_002", "schema_grounded_business_scenario", "按TxnDateGMT汇总昨日split Qty", "sqlserver", "split.qty"),
    # Combine (2)
    ("combine_001", "schema_grounded_business_scenario", "按TxnDate统计今日批次合并数量", "oracle", "combine.qty"),
    ("combine_002", "schema_grounded_business_scenario", "按TxnDateGMT汇总昨日combine Qty", "sqlserver", "combine.qty"),
    # Hold duration (2)
    ("hold_001", "schema_grounded_business_scenario", "按TxnDate统计今日Hold持续时间", "oracle", "hold.duration"),
    ("hold_002", "schema_grounded_business_scenario", "按TxnDateGMT汇总昨日暂停时长", "sqlserver", "hold.duration"),
    # Resource status count (2)
    ("resource_status_001", "schema_grounded_business_scenario", "按TxnDate统计今日设备状态变更次数", "oracle", "resource_status.change_count"),
    ("resource_status_002", "schema_grounded_business_scenario", "按TxnDateGMT查询昨日resource状态变化多少次", "sqlserver", "resource_status.change_count"),
]


def main() -> int:
    if len(CASES) != 50:
        raise ValueError(f"Expected 50 benchmark cases, got {len(CASES)}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for case_id, source, question, dialect, expected_metric in CASES:
        metric = resolve_metric(question)
        if not metric or metric["id"] != expected_metric:
            raise ValueError(
                f"{case_id}: resolved {metric and metric['id']}, "
                f"expected {expected_metric}"
            )
        plan = build_sql_query_plan(
            question,
            [item["table"] for item in metric["tables"]],
            dialect,
        )
        if plan.needs_clarification:
            raise ValueError(
                f"{case_id}: benchmark question is ambiguous: "
                f"{plan.clarification_question}"
            )
        golden_sql = render_metric_sql(
            metric,
            dialect=dialect,
            time_scope=plan.time_scope,
            time_basis=plan.time_basis,
            question=question,
        )
        rows.append({
            "id": case_id,
            "source": source,
            "question": question,
            "dialect": dialect,
            "expectedPlan": {
                "metricId": metric["id"],
                "factTable": metric["factTable"],
                "timeScope": plan.time_scope,
                "timeBasis": plan.time_basis,
                "requiresClarification": False,
            },
            "expectedTables": [item["table"] for item in metric["tables"]],
            "expectedJoins": metric.get("joins", []),
            "contractStatus": metric.get("status", "approved"),
            "goldenSql": golden_sql,
        })
    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(f"cases={len(rows)}")
    print(f"output={OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

