from __future__ import annotations

import pytest

from src.qa import manufacturing_session_store as store
from src.qa import graphstudio_assistant as assistant
from src.qa.graphstudio_assistant import (
    GraphStudioAssistantError,
    _schema_inventory_sparql,
    _schema_rows_from_release,
    discover_schema,
    resolve_runtime_snapshot,
    validate_readonly_sparql,
)
from src.qa import graphstudio_saved_queries as saved_queries


def test_manufacturing_sessions_are_persisted_separately(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SESSION_DIR", tmp_path / "manufacturing")

    session = store.create_session("制造订单追溯")
    runtime = {"cacheKey": "ontology-4::data-5", "ontologyReleaseNo": 4}
    saved = store.append_exchange(
        session["id"],
        question="订单 MO-1 对应什么产品？",
        answer="订单关联 Product-A。",
        runtime_snapshot=runtime,
    )

    assert saved["title"] == "订单 MO-1 对应什么产品？"
    assert len(saved["messages"]) == 2
    assert store.load_session(session["id"])["messages"][1]["role"] == "assistant"
    assert store.load_session(session["id"])["runtime"] == runtime
    assert store.load_session(session["id"])["messages"][1]["runtime"] == runtime
    assert store.list_sessions()[0]["id"] == session["id"]
    assert store.delete_session(session["id"]) is True


def test_readonly_sparql_adds_result_limit():
    query = validate_readonly_sparql(
        """
        PREFIX cam: <https://example.com/cam#>
        SELECT ?order WHERE { ?order a cam:MfgOrder . }
        """
    )
    assert query.endswith("LIMIT 100")


@pytest.mark.parametrize(
    "query",
    [
        "INSERT DATA { <x> <y> <z> }",
        "DELETE WHERE { ?s ?p ?o }",
        "SELECT * WHERE { SERVICE <https://outside.example/sparql> { ?s ?p ?o } }",
        "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }",
    ],
)
def test_readonly_sparql_rejects_writes_and_external_queries(query):
    with pytest.raises(GraphStudioAssistantError):
        validate_readonly_sparql(query)


def test_saved_query_catalog_keeps_only_safe_selects(monkeypatch):
    payload = {
        "results": {
            "bindings": [
                {
                    "query": {"value": "http://example.com/Query/orders"},
                    "title": {"value": "manufacturing-orders"},
                    "description": {"value": "制造订单清单"},
                    "sparql": {"value": "SELECT ?order WHERE { ?order a <urn:MfgOrder> . }"},
                },
                {
                    "query": {"value": "http://example.com/Query/write"},
                    "title": {"value": "unsafe"},
                    "sparql": {"value": "DELETE WHERE { ?s ?p ?o }"},
                },
            ]
        }
    }

    catalog = saved_queries._parse_catalog(payload)

    assert [item["title"] for item in catalog] == ["manufacturing-orders"]
    assert catalog[0]["sparql"].endswith("LIMIT 100")


def test_public_query_catalog_does_not_expose_sparql(monkeypatch):
    monkeypatch.setattr(saved_queries, "list_saved_queries", lambda **_: [{
        "uri": "http://example.com/Query/orders",
        "title": "orders",
        "description": "制造订单",
        "sparql": "SELECT * WHERE { ?s ?p ?o } LIMIT 10",
        "modified": "2026-08-17T00:00:00Z",
        "forced_limit": "500",
    }])

    public = saved_queries.public_query_catalog()

    assert public[0]["title"] == "orders"
    assert "sparql" not in public[0]


def test_saved_query_compatibility_rejects_removed_publish_uris():
    namespace = "https://opcenter.siemens.com/ontology/camstar/2607/publish#"
    queries = [{
        "uri": "urn:query:legacy",
        "title": "legacy",
        "sparql": f"PREFIX cam: <{namespace}> SELECT * WHERE {{ ?s a cam:RemovedClass . }} LIMIT 10",
    }]
    runtime = {"ontologyReleaseId": "r4", "ontologyReleaseNo": 4}

    annotated = saved_queries._annotate_compatibility(
        queries,
        [{"class": namespace + "MfgOrder", "property": ""}],
        runtime,
    )

    assert annotated[0]["compatible"] is False
    assert annotated[0]["missing_uris"] == [namespace + "RemovedClass"]


def test_release_schema_includes_classes_without_instances_and_all_relationships():
    model = {
        "classes": [
            {"class": {"uid": "a", "targetName": "MfgOrder", "role": "core"}, "properties": []},
            {"class": {"uid": "b", "targetName": "Workflow", "role": "context"}, "properties": []},
            {"class": {"uid": "c", "targetName": "Spec", "role": "context"}, "properties": []},
        ],
        "relationships": [
            {"source": {"targetName": "MfgOrder"}, "target": {"targetName": "Workflow"}, "relation": {"targetName": "HAS_WORKFLOW", "usage": "published_link"}},
            {"source": {"targetName": "Workflow"}, "target": {"targetName": "Spec"}, "relation": {"targetName": "HAS_SPEC", "usage": "published_link"}},
        ],
    }

    rows = _schema_rows_from_release(model, {
        "https://opcenter.siemens.com/ontology/camstar/2607/publish#MfgOrder": 5,
    })

    base_classes = {row["class"] for row in rows if row["valueKind"] == "对象类型"}
    relationships = [row for row in rows if row["valueKind"] == "关系"]
    assert {uri.rsplit("#", 1)[-1] for uri in base_classes} == {"MfgOrder", "Workflow", "Spec"}
    assert next(row for row in rows if row["class"].endswith("#Spec"))["instanceCount"] == 0
    assert [row["propertyLabel"] for row in relationships] == ["HAS_WORKFLOW", "HAS_SPEC"]
    assert "VALUES ?class" in _schema_inventory_sparql(rows)


def test_schema_context_marks_empty_and_disabled_relationships_as_unusable():
    namespace = "https://opcenter.siemens.com/ontology/camstar/2607/publish#"
    model = {
        "classes": [
            {"class": {"targetName": "MfgOrder"}, "properties": []},
            {"class": {"targetName": "Product"}, "properties": []},
            {"class": {"targetName": "Workflow"}, "properties": []},
        ],
        "relationships": [
            {
                "source": {"targetName": "MfgOrder"},
                "target": {"targetName": "Workflow"},
                "relation": {
                    "targetName": "HAS_IS_WORKFLOW",
                    "usage": "published_link",
                },
            },
            {
                "source": {"targetName": "MfgOrder"},
                "target": {"targetName": "Product"},
                "relation": {
                    "targetName": "ORDERED_PRODUCT",
                    "usage": "published_link",
                },
            },
            {
                "source": {"targetName": "Product"},
                "target": {"targetName": "Workflow"},
                "relation": {
                    "targetName": "LEGACY_WORKFLOW",
                    "usage": "published_link",
                    "questionEnabled": False,
                },
            },
        ],
    }
    rows = _schema_rows_from_release(model, {}, {
        namespace + "REL_HAS_IS_WORKFLOW": 0,
        namespace + "REL_ORDERED_PRODUCT": 5,
        namespace + "REL_LEGACY_WORKFLOW": 8,
    })

    context = assistant._schema_context(rows)

    assert "ORDERED_PRODUCT" in context
    assert "当前关系实例数：5；问答可用：是" in context
    assert "禁止用于查询连接的关系" in context
    assert "HAS_IS_WORKFLOW" in context
    assert "当前关系实例数：0；问答可用：否" in context
    assert "LEGACY_WORKFLOW" in context


def test_relationship_counts_reads_only_materialized_publish_edges(monkeypatch):
    namespace = "https://opcenter.siemens.com/ontology/camstar/2607/publish#"
    captured = {}

    def fake_request(query, *, runtime_snapshot):
        captured["query"] = query
        captured["runtime"] = runtime_snapshot
        return {"results": {"bindings": [{
            "relationship": {"value": namespace + "REL_ORDERED_PRODUCT"},
            "relationshipCount": {"value": "5"},
        }]}}

    monkeypatch.setattr(assistant, "_request_sparql", fake_request)

    counts = assistant._relationship_counts({"cacheKey": "release-15"})

    assert counts == {namespace + "REL_ORDERED_PRODUCT": 5}
    assert "REL_" in captured["query"]
    assert captured["runtime"]["cacheKey"] == "release-15"


def test_relationship_count_probe_failure_does_not_turn_unknown_into_zero(monkeypatch):
    def fail_request(*_args, **_kwargs):
        raise GraphStudioAssistantError("temporary failure")

    monkeypatch.setattr(assistant, "_request_sparql", fail_request)

    assert assistant._relationship_counts({"cacheKey": "release-15"}) is None


def test_schema_cache_is_invalidated_by_runtime_version(monkeypatch):
    calls = []
    monkeypatch.setattr(assistant, "_schema_cache", None)
    monkeypatch.setattr(assistant, "_persist_schema", lambda *_: None)
    monkeypatch.setattr(
        assistant,
        "_discover_schema_uncached",
        lambda runtime: calls.append(runtime["cacheKey"]) or [{"class": runtime["cacheKey"]}],
    )
    first = {"cacheKey": "deployment-1"}
    second = {"cacheKey": "deployment-2"}

    assert discover_schema(first)[0]["class"] == "deployment-1"
    assert discover_schema(first)[0]["class"] == "deployment-1"
    assert discover_schema(second)[0]["class"] == "deployment-2"
    assert calls == ["deployment-1", "deployment-2"]


def test_runtime_snapshot_pins_active_data_ontology_and_deployment(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(assistant.SyncSettings, "from_env", lambda: SimpleNamespace(graphmart_uri="urn:fallback"))
    monkeypatch.setattr(assistant, "ControlPlaneRepository", lambda settings: SimpleNamespace(settings=settings))
    monkeypatch.setattr(assistant, "deployment_status", lambda _repo, _profile: {
        "activeCuratedRelease": {"release_id": "00000000-0000-0000-0000-000000000005", "release_no": 5, "object_count": 6, "relationship_count": 5},
        "activeOntologyRelease": {"ontology_release_id": "00000000-0000-0000-0000-000000000004", "release_no": 4, "class_count": 6, "relationship_count": 19},
        "routes": [{"route_key": "core-dev", "graphmart_uri": "urn:graphmart"}],
        "deployments": [{
            "deployment_id": "00000000-0000-0000-0000-000000000748",
            "route_key": "core-dev", "environment_key": "dev", "status": "active",
            "curated_release_id": "00000000-0000-0000-0000-000000000005",
            "ontology_release_id": "00000000-0000-0000-0000-000000000004",
            "layer_uri": "urn:layer:green", "artifact_hash": "abc",
            "validation_plan": {"modelUri": "urn:model:r4", "graphmartUri": "urn:graphmart"},
        }],
    })

    runtime = resolve_runtime_snapshot()

    assert runtime["ontologyReleaseNo"] == 4
    assert runtime["curatedReleaseNo"] == 5
    assert runtime["deploymentId"].endswith("0748")
    assert "00000000-0000-0000-0000-000000000004" in runtime["cacheKey"]
