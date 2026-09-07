import json
from contextlib import contextmanager
from types import SimpleNamespace
import uuid

import pytest
import requests
from src.graphstudio_sync import deployment


def test_tls_failure_records_retryable_failure_without_committing_checkpoint(monkeypatch):
    calls = []
    class Session:
        def close(self):
            calls.append("closed")
    class Connection:
        def execute(self, statement, params):
            calls.append((str(statement), params))
    @contextmanager
    def begin():
        yield Connection()
    def fail(*args, **kwargs):
        raise requests.exceptions.SSLError("TLS EOF")
    monkeypatch.setattr(deployment, "require_graphstudio_2026_1_ready", fail)
    settings = SimpleNamespace(graphstudio_base_url="https://example.test", shared_file_connection=None, shared_file_path="test")
    with pytest.raises(requests.exceptions.SSLError, match="TLS EOF"):
        deployment._publication_preflight(Session(), settings, SimpleNamespace(engine=SimpleNamespace(begin=begin)), uuid.uuid4(), "urn:graphmart", "inline_query")
    assert calls[0] == "closed"
    assert len(calls) == 2
    sql, params = calls[1]
    assert "status='failed'" in sql
    assert "status IN ('approved','failed')" in sql
    assert "checkpoint" not in sql
    assert json.loads(params["error"]) == {"stage": "graphstudio_preflight", "message": "TLS EOF", "retryable": True, "remoteMutated": False}


def test_successful_preflight_keeps_session_open_for_publication(monkeypatch):
    calls = []
    monkeypatch.setattr(deployment, "require_graphstudio_2026_1_ready", lambda *args, **kwargs: calls.append(kwargs))
    settings = SimpleNamespace(graphstudio_base_url="https://example.test", shared_file_connection="urn:files", shared_file_path="test")
    deployment._publication_preflight(SimpleNamespace(), settings, None, uuid.uuid4(), "urn:graphmart", "inline_query")
    assert calls[0]["file_connection"] is None
