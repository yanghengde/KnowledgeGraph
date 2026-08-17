from __future__ import annotations

import pytest

from src.qa import manufacturing_session_store as store
from src.qa.graphstudio_assistant import (
    GraphStudioAssistantError,
    validate_readonly_sparql,
)
from src.qa import graphstudio_saved_queries as saved_queries


def test_manufacturing_sessions_are_persisted_separately(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SESSION_DIR", tmp_path / "manufacturing")

    session = store.create_session("制造订单追溯")
    saved = store.append_exchange(
        session["id"],
        question="订单 MO-1 对应什么产品？",
        answer="订单关联 Product-A。",
    )

    assert saved["title"] == "订单 MO-1 对应什么产品？"
    assert len(saved["messages"]) == 2
    assert store.load_session(session["id"])["messages"][1]["role"] == "assistant"
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
