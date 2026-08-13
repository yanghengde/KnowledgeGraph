from dataclasses import replace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.graphstudio_sync.action_identity import action_principal, require_action_principal
from src.graphstudio_sync.actions import openapi_action_candidates, openapi_action_sources
from src.graphstudio_sync.database import DDL_FILE

from test_graphstudio_sync_connections import _settings


def _request(headers: dict[str, str] | None = None) -> Request:
    encoded = [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()]
    return Request({"type": "http", "method": "GET", "path": "/", "headers": encoded})


def test_disabled_identity_allows_preview_identity_but_blocks_real_action() -> None:
    principal = action_principal(
        _request(), replace(_settings(), action_auth_mode="disabled"),
    )

    assert principal.subject == "local-preview"
    assert principal.authenticated is False
    with pytest.raises(HTTPException, match="trusted proxy identity"):
        require_action_principal(principal)


def test_trusted_proxy_identity_is_server_derived() -> None:
    settings = replace(
        _settings(), action_auth_mode="trusted_headers",
        action_trusted_proxy_secret="server-secret",
    )
    principal = action_principal(_request({
        "x-action-proxy-secret": "server-secret",
        "x-authenticated-user": "planner-1",
        "x-authenticated-roles": "camstar_planner, camstar_operator",
    }), settings)

    assert principal.subject == "planner-1"
    assert principal.roles == ("camstar_operator", "camstar_planner")
    assert principal.authenticated is True


def test_trusted_proxy_rejects_untrusted_headers() -> None:
    settings = replace(
        _settings(), action_auth_mode="trusted_headers",
        action_trusted_proxy_secret="server-secret",
    )

    with pytest.raises(HTTPException, match="identity is missing"):
        action_principal(_request({"x-authenticated-user": "spoofed"}), settings)


def test_openapi_import_is_selective_and_only_lists_mutating_operations() -> None:
    assert any(item["sourceFile"] == "Products.json" for item in openapi_action_sources())

    candidates = openapi_action_candidates("Products.json")

    assert candidates
    assert {item["httpMethod"] for item in candidates} <= {"POST", "PUT", "PATCH", "DELETE"}
    update = next(item for item in candidates if item["httpMethod"] == "PUT" and "{key}" in item["endpointPath"])
    assert "key" in update["inputSchema"]["required"]
    assert update["pathParameters"] == ["key"]


def test_v15_ddl_drops_proof_of_concept_tables_and_has_no_seed_actions() -> None:
    ddl = DDL_FILE.read_text(encoding="utf-8")

    assert "DROP TABLE IF EXISTS camstar_curated.product" in ddl
    assert "DROP TABLE IF EXISTS camstar_curated.mfg_order" in ddl
    assert "CREATE TABLE IF NOT EXISTS camstar_curated.product" not in ddl
    assert "camstar.mfgorder.release" in ddl  # explicit cleanup target
    assert "INSERT INTO graphsync.action_definition" not in ddl

