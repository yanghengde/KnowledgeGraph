import json
import asyncio
from pathlib import Path

import pytest

from src.qa.semantic.metric_catalog import (
    get_metric,
    load_metrics,
    validate_metric_catalog,
)
from src.qa.semantic.metric_resolver import resolve_metric
from src.qa.semantic.metric_validator import validate_metric_sql
from src.qa.semantic.sql_renderer import render_metric_answer, render_metric_sql
from src.qa.sql_query_planner import build_sql_query_plan
from src.qa.sql_validator import validate_sql_answer


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "sql_semantic_benchmark.jsonl"
)


def load_cases():
    return [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


CASES = load_cases()


def test_metric_catalog_contains_15_physically_valid_contracts():
    assert len(load_metrics()) == 15
    assert validate_metric_catalog() == []


def test_benchmark_has_50_unique_reviewable_cases():
    assert len(CASES) == 50
    assert len({case["id"] for case in CASES}) == 50
    assert all(case["goldenSql"].strip().endswith(";") for case in CASES)
    assert any(case["source"].startswith("chat_log") for case in CASES)
    assert all(case["expectedPlan"]["requiresClarification"] is False for case in CASES)


@pytest.mark.parametrize("case", CASES, ids=lambda item: item["id"])
def test_semantic_benchmark_matches_plan_and_golden_sql(case):
    metric = resolve_metric(case["question"])
    assert metric is not None
    assert metric["id"] == case["expectedPlan"]["metricId"]
    assert metric["factTable"] == case["expectedPlan"]["factTable"]

    plan = build_sql_query_plan(
        case["question"],
        case["expectedTables"],
        case["dialect"],
    )
    assert plan.needs_clarification is False
    assert plan.metric_id == case["expectedPlan"]["metricId"]
    assert plan.fact_table == case["expectedPlan"]["factTable"]
    assert plan.time_scope == case["expectedPlan"]["timeScope"]
    assert plan.time_basis == case["expectedPlan"]["timeBasis"]

    actual_sql = render_metric_sql(
        metric,
        dialect=case["dialect"],
        time_scope=plan.time_scope,
        time_basis=plan.time_basis,
        question=case["question"],
    )
    assert actual_sql == case["goldenSql"]

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
    assert physical.valid, physical.errors
    assert semantic.valid, semantic.errors
    assert set(physical.tables) == set(case["expectedTables"])


def test_historical_metric_requires_time_scope_then_time_basis():
    metric = get_metric("throughput.by_mfg_order")
    plan = build_sql_query_plan(
        "统计每个工单的产出",
        [item["table"] for item in metric["tables"]],
        "oracle",
    )
    assert plan.clarification_key == "time_scope"

    plan = build_sql_query_plan(
        "今日",
        plan.entities,
        "oracle",
        plan.to_dict(),
    )
    assert plan.clarification_key == "time_basis"

    plan = build_sql_query_plan(
        "使用本地交易时间",
        plan.entities,
        "oracle",
        plan.to_dict(),
    )
    assert plan.needs_clarification is False
    assert plan.time_scope == "今日"
    assert plan.time_basis == "TxnDate"


def test_metric_validator_rejects_wrong_measure():
    metric = get_metric("throughput.by_mfg_order")
    wrong = """```sql
SELECT mo.MfgOrderId, COUNT(rth.ResourceThruputHistoryId) AS ThruputQty
FROM ResourceThruputHistory rth
JOIN HistoryMainline hm
  ON rth.HistoryMainlineId = hm.HistoryMainlineId
JOIN MfgOrder mo
  ON rth.MfgOrderId = mo.MfgOrderId
WHERE hm.TxnDate >= :start_time
  AND hm.TxnDate < :end_time
GROUP BY mo.MfgOrderId, mo.MfgOrderName;
```"""
    result = validate_metric_sql(
        wrong,
        metric,
        time_basis="TxnDate",
    )
    assert result.valid is False
    assert any("度量表达式" in error for error in result.errors)


def test_metric_validator_rejects_table_outside_contract():
    metric = get_metric("wip.current_qty")
    wrong = """```sql
SELECT SUM(c.Qty) AS CurrentQty
FROM Container c
JOIN MfgOrder mo
  ON c.MfgOrderId = mo.MfgOrderId;
```"""
    result = validate_metric_sql(wrong, metric)
    assert result.valid is False
    assert any("合同外表：MfgOrder" in error for error in result.errors)


def test_semantic_metric_query_bypasses_llm(monkeypatch):
    from src.qa import engine

    def fail_if_called():
        raise AssertionError("LLM must not be called for a contracted metric")

    monkeypatch.setattr(engine, "_get_async_llm", fail_if_called)
    question = "请写一个今日工单产出的sql，使用本地交易时间"
    classes = engine.extract_keywords(question, fallback=False)
    plan = build_sql_query_plan(question, classes, "oracle")
    async def collect():
        chunks = []
        async for chunk in engine.query_stream(
            question,
            assistant_mode="sql",
            selected_classes=classes,
            sql_dialect="oracle",
            query_plan=plan.to_dict(),
        ):
            if isinstance(chunk, str):
                chunks.append(chunk)
        return chunks

    chunks = asyncio.run(collect())
    answer = "".join(chunks)
    assert "throughput.by_mfg_order" in answer
    assert "SUM(rth.Qty)" in answer
    assert "rth.MfgOrderId = mo.MfgOrderId" in answer
    assert "不可变 Golden SQL" in answer
    assert "throughput_order_001" in answer


def test_contracted_metric_does_not_generate_sql_without_template(monkeypatch):
    from src.qa import engine
    from src.qa.semantic import example_index

    monkeypatch.setattr(
        example_index,
        "resolve_static_sql_example",
        lambda *args, **kwargs: None,
    )

    def fail_if_called():
        raise AssertionError("LLM must not be called for a contracted metric")

    monkeypatch.setattr(engine, "_get_async_llm", fail_if_called)
    question = "请写一个今日工单产出的sql，使用本地交易时间"
    classes = engine.extract_keywords(question, fallback=False)
    plan = build_sql_query_plan(question, classes, "oracle")

    async def collect():
        chunks = []
        async for chunk in engine.query_stream(
            question,
            assistant_mode="sql",
            selected_classes=classes,
            sql_dialect="oracle",
            query_plan=plan.to_dict(),
        ):
            if isinstance(chunk, str):
                chunks.append(chunk)
        return "".join(chunks)

    answer = asyncio.run(collect())
    assert "未命中标准 SQL 模板" in answer
    assert "```sql" not in answer
