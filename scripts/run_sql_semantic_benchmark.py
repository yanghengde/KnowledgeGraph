#!/usr/bin/env python3
"""Run the 50-case semantic SQL benchmark and write a compact report."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.qa.semantic.metric_catalog import validate_metric_catalog
from src.qa.semantic.metric_resolver import resolve_metric
from src.qa.semantic.metric_validator import validate_metric_sql
from src.qa.semantic.sql_renderer import render_metric_answer, render_metric_sql
from src.qa.sql_query_planner import build_sql_query_plan
from src.qa.sql_validator import validate_sql_answer


FIXTURE = PROJECT_ROOT / "src" / "tests" / "fixtures" / "sql_semantic_benchmark.jsonl"
REPORT = PROJECT_ROOT / "docs" / "sql_semantic_benchmark_report.md"


def main() -> int:
    cases = [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    counters = {
        "total": len(cases),
        "metric": 0,
        "plan": 0,
        "golden": 0,
        "physical": 0,
        "semantic": 0,
        "passed": 0,
    }
    failures = []
    catalog_errors = validate_metric_catalog()

    for case in cases:
        errors = []
        metric = resolve_metric(case["question"])
        expected = case["expectedPlan"]
        if metric and metric["id"] == expected["metricId"]:
            counters["metric"] += 1
        else:
            errors.append(
                f"metric={metric and metric['id']}, expected={expected['metricId']}"
            )
            failures.append((case["id"], errors))
            continue

        plan = build_sql_query_plan(
            case["question"],
            case["expectedTables"],
            case["dialect"],
        )
        if (
            not plan.needs_clarification
            and plan.metric_id == expected["metricId"]
            and plan.fact_table == expected["factTable"]
            and plan.time_scope == expected["timeScope"]
            and plan.time_basis == expected["timeBasis"]
        ):
            counters["plan"] += 1
        else:
            errors.append("query plan differs")

        sql = render_metric_sql(
            metric,
            dialect=case["dialect"],
            time_scope=plan.time_scope,
            time_basis=plan.time_basis,
            question=case["question"],
        )
        if sql == case["goldenSql"]:
            counters["golden"] += 1
        else:
            errors.append("SQL differs from Golden")

        answer = render_metric_answer(
            metric,
            dialect=case["dialect"],
            time_scope=plan.time_scope,
            time_basis=plan.time_basis,
            question=case["question"],
        )
        physical = validate_sql_answer(
            answer,
            dialect=case["dialect"],
            query_plan=plan.to_dict(),
        )
        semantic = validate_metric_sql(
            answer,
            metric,
            time_basis=plan.time_basis,
        )
        if physical.valid and set(physical.tables) == set(case["expectedTables"]):
            counters["physical"] += 1
        else:
            errors.extend(physical.errors or ["physical table set differs"])
        if semantic.valid:
            counters["semantic"] += 1
        else:
            errors.extend(semantic.errors)
        if not errors:
            counters["passed"] += 1
        else:
            failures.append((case["id"], errors))

    lines = [
        "# SQL业务指标语义层回归报告",
        "",
        f"- Golden问题总数：{counters['total']}",
        f"- 指标合同数：15",
        f"- 指标目录物理错误：{len(catalog_errors)}",
        "",
        "| 检查项 | 通过 | 总数 | 准确率 |",
        "|---|---:|---:|---:|",
    ]
    for key, label in [
        ("metric", "指标识别"),
        ("plan", "查询计划"),
        ("golden", "Golden SQL精确匹配"),
        ("physical", "物理Schema与JOIN"),
        ("semantic", "业务指标合同"),
        ("passed", "整条用例"),
    ]:
        value = counters[key]
        rate = value / counters["total"] * 100 if counters["total"] else 0
        lines.append(f"| {label} | {value} | {counters['total']} | {rate:.1f}% |")
    lines += ["", "## 失败明细", ""]
    if failures:
        for case_id, errors in failures:
            lines.append(f"- `{case_id}`：" + "；".join(errors))
    else:
        lines.append("_无。_")
    lines += [
        "",
        "本报告只验证固定SQL模板、物理Schema和指标合同，不连接或查询业务数据库。",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(counters, ensure_ascii=False))
    print(f"catalog_errors={len(catalog_errors)}")
    print(f"report={REPORT}")
    return 0 if counters["passed"] == counters["total"] and not catalog_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
