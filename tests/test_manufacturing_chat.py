from __future__ import annotations

import pytest

from src.qa import manufacturing_session_store as store
from src.qa.graphstudio_assistant import (
    GraphStudioAssistantError,
    validate_readonly_sparql,
)


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
