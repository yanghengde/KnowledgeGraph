import asyncio
import json

import pytest
from rdflib import Dataset, Literal, Namespace, RDF, URIRef

from src.qa import graphstudio_assistant as assistant
from src.qa.query_capabilities import match_capability, retrieve_schema, result_table


NS = Namespace(assistant._PUBLISH_NAMESPACE)
RUNTIME = {"layerUri": "https://example.com/published/r1", "deploymentId": "deployment-1",
           "ontologyReleaseNo": 5, "curatedReleaseNo": 18, "cacheKey": "test"}


@pytest.fixture
def schema():
    rows = []
    for name in ("MfgOrder", "Product", "Workflow", "Container"):
        rows.append({"class": str(NS[name]), "classLabel": name, "property": "", "valueKind": "对象类型"})
        for prop in ("name", "displayLabel", "qty", "description"):
            rows.append({"class": str(NS[name]), "property": str(NS[f"{name}_{prop}"]),
                         "propertyLabel": prop, "valueKind": "属性"})
    rows.append({"class": str(NS.MfgOrder), "property": str(NS.REL_ORDERED_PRODUCT),
                 "targetClass": str(NS.Product), "valueKind": "关系", "relationshipCount": 2})
    return rows


@pytest.fixture
def data():
    dataset = Dataset()
    graph = dataset.graph(URIRef(RUNTIME["layerUri"]))
    for i in range(3):
        subject = URIRef(f"urn:order:{i}")
        graph.add((subject, RDF.type, NS.MfgOrder))
        graph.add((subject, NS.MfgOrder_name, Literal(f"MO-{i}")))
        graph.add((subject, NS.MfgOrder_displayLabel, Literal(f"MO-{i}")))
        if i < 2:
            graph.add((subject, NS.REL_ORDERED_PRODUCT, URIRef("urn:product")))
    graph.add((URIRef("urn:product"), RDF.type, NS.Product))
    graph.add((URIRef("urn:product"), NS.Product_displayLabel, Literal("产品A")))
    old = dataset.graph(URIRef("urn:old-version"))
    old.add((URIRef("urn:old-order"), RDF.type, NS.MfgOrder))
    return dataset


@pytest.mark.parametrize("question,key", [
    ("当前发布了哪些制造订单？", "list"), ("当前有哪些产品？", "list"),
    ("制造订单列表", "list"), ("所有工单有哪些？", "list"),
    ("当前有多少个制造订单？", "count"), ("产品数量", "count"),
    ("每个工单对应的产品是什么", "link"), ("每个制造订单分别关联了什么产品？", "link"),
    ("按产品统计关联的制造订单数量。", "group"),
    ("工单MO-1对应的产品是什么", "link"),
])
def test_capabilities_execute_only_in_published_layer(question, key, schema, data):
    plan = match_capability(question, schema, RUNTIME)
    assert plan is not None and plan.key == key
    rows = list(data.query(plan.sparql))
    assert rows
    assert "urn:old-order" not in str(rows)
    if key == "count" and "订单" in question:
        assert int(rows[0][0]) == 3
    if key == "link" and "MO-1" in question:
        assert len(rows) == 1
        assert plan.parameters["orderName"] == "MO-1"
    if key == "link" and "MO-1" not in question:
        assert len(rows) == 3  # Also show the order whose link was not returned.
    if key == "group":
        assert int(rows[0][-1]) == 2


@pytest.mark.parametrize("question", [
    "今天发布了哪些制造订单？", "只看上海工厂的制造订单", "工单数量大于100的有哪些",
    "这些订单对应的产品是什么", "按产品统计本月订单数量", "删除所有工单",
    '工单MO-1" } UNION { ?s ?p ?o }对应的产品是什么',
    "排除已取消的订单有哪些", "按产品统计订单数量并按工厂分组", "工单有哪些以及为什么延期",
])
def test_unsupported_conditions_never_become_unfiltered_fast_queries(question, schema):
    assert match_capability(question, schema, RUNTIME) is None


def test_ambiguous_relationship_and_unpublished_field_fall_through(schema):
    second = {**schema[-1], "property": str(NS.REL_OTHER_PRODUCT)}
    assert match_capability("工单对应的产品是什么", schema + [second], RUNTIME) is None
    no_name = [r for r in schema if r.get("property") != str(NS.MfgOrder_name)]
    assert match_capability("工单MO-1对应的产品是什么", no_name, RUNTIME) is None
    disabled = [*schema[:-1], {**schema[-1], "questionEnabled": False}]
    assert match_capability("工单对应的产品是什么", disabled, RUNTIME) is None


def test_empty_relation_not_mistaken_for_materialized_alternative(schema):
    extra = {**schema[-1], "property": str(NS.REL_BEGIN_PRODUCT), "relationshipCount": 0}
    plan = match_capability("工单对应的产品是什么", schema + [extra], RUNTIME)
    assert "REL_ORDERED_PRODUCT" in plan.sparql
    assert "REL_BEGIN_PRODUCT" not in plan.sparql


def test_constrained_history_is_preserved_by_falling_back(schema):
    history = [{"role": "user", "content": "只看工单MO-1"}]
    assert match_capability("每个工单对应的产品是什么", schema, RUNTIME, history) is None


def test_retrieval_bounds_500_class_schema_and_preserves_relationship_path(schema):
    large = list(schema)
    for i in range(496):
        uri = str(NS[f"Unrelated{i}"])
        large.append({"class": uri, "property": "", "valueKind": "对象类型"})
        large.extend({"class": uri, "property": str(NS[f"Unrelated{i}_field{j}"]), "valueKind": "属性"} for j in range(80))
    selected = retrieve_schema("工单对应的产品是什么", large)
    assert {r["class"] for r in selected} == {str(NS.MfgOrder), str(NS.Product)}
    assert schema[-1] in selected
    assert len(selected) < 40
    assert retrieve_schema("天气怎么样", large) == []


def test_markdown_table_escapes_data_and_keeps_duplicate_name_identifiers():
    rows = [{"object": "urn:1", "name": "同名|<script>"}, {"object": "urn:2", "name": "同名|<script>"}]
    table = result_table(rows, ["object", "name"], {"name": "订单", "object": "标识"})
    assert "<script>" not in table
    assert "\\|" in table and "urn:1" in table and "urn:2" in table


def test_fast_stream_skips_llm_and_records_timings(monkeypatch, schema, data):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(assistant, "discover_schema", lambda *a: schema)
    monkeypatch.setattr(assistant, "_get_llm", lambda: pytest.fail("Fast query must not call LLM"))
    def query(sparql, **kwargs):
        return json.loads(data.query(sparql).serialize(format="json"))
    monkeypatch.setattr(assistant, "_request_sparql", query)
    async def collect():
        return [x async for x in assistant.graphstudio_query_stream("每个工单对应的产品是什么", runtime_snapshot=RUNTIME)]
    chunks = asyncio.run(collect())
    assert "产品A" in next(x for x in chunks if isinstance(x, str))
    metrics = next(x["metrics"] for x in chunks if isinstance(x, dict) and x.get("type") == "metrics")
    assert metrics["capability"] == "link" and metrics["rowCount"] == 3
    assert metrics["summaryMs"] == 0


def test_dynamic_table_precedes_summary_and_survives_summary_failure(monkeypatch, schema):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    monkeypatch.setattr(assistant, "discover_schema", lambda *a: schema)
    async def plan(*args):
        return f"SELECT ?object WHERE {{ ?object a <{NS.MfgOrder}> }} LIMIT 1", "order"
    async def failed_summary(*args):
        raise RuntimeError("LLM offline")
        yield "unreachable"
    monkeypatch.setattr(assistant, "_plan_query", plan)
    monkeypatch.setattr(assistant, "_summarize_evidence", failed_summary)
    monkeypatch.setattr(assistant, "_request_sparql", lambda *a, **k: {
        "head": {"vars": ["object"]}, "results": {"bindings": [{"object": {"value": "urn:order"}}]}})
    async def collect():
        return [x async for x in assistant.graphstudio_query_stream("订单列表", query_mode="dynamic", runtime_snapshot=RUNTIME)]
    chunks = asyncio.run(collect())
    texts = [x for x in chunks if isinstance(x, str)]
    assert "urn:order" in texts[0]
    assert any("文字解读暂未完成" in x for x in texts)
    assert "查询依据" in texts[-1]
