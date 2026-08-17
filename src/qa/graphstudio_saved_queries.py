"""Read-only catalog access for Graph Studio Query Playground bookmarks."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

import requests
import urllib3

from src.qa.graphstudio_assistant import (
    GraphStudioAssistantError,
    _binding_rows,
    _configuration,
    validate_readonly_sparql,
)


_ALL_NAMED_GRAPHS = "http://openanzo.org/namedGraphs/reserved/graphs/ALL"
_CATALOG_TTL_SECONDS = 60
_CATALOG_CACHE_PATH = Path(
    os.getenv(
        "MANUFACTURING_QUERY_CACHE",
        Path(__file__).resolve().parents[2] / "data" / "manufacturing_saved_queries.json",
    )
)
_catalog_lock = threading.Lock()
_catalog_cache: tuple[float, list[dict[str, str]]] | None = None


def _journal_endpoint() -> str:
    configured = os.getenv("GRAPHSTUDIO_JOURNAL_URL", "").strip()
    if configured:
        return configured.rstrip("/")
    return f"{_configuration()['base_url']}/sparql"


def _verify_tls() -> bool | str:
    value = os.getenv("GRAPHSTUDIO_VERIFY_TLS", "true").strip()
    if value.lower() in {"0", "false", "no", "off"}:
        return False
    if value.lower() in {"1", "true", "yes", "on", ""}:
        return True
    return value


def _request_journal(query: str, *, timeout: float = 30) -> dict[str, Any]:
    config = _configuration()
    verify_tls = _verify_tls()
    if verify_tls is False:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = None
    last_error: requests.RequestException | None = None
    for attempt in range(3):
        try:
            response = requests.post(
                _journal_endpoint(),
                data={
                    "query": query,
                    "format": "text/json",
                    "default-named-graph-uri": _ALL_NAMED_GRAPHS,
                    "named-graph-uri": _ALL_NAMED_GRAPHS,
                },
                headers={
                    "Accept": "application/sparql-results+json",
                    "User-Agent": "Opcenter-Manufacturing-QA/1.0",
                },
                auth=(config["username"], config["password"]),
                verify=verify_tls,
                timeout=timeout,
            )
            if response.status_code not in {502, 503, 504}:
                break
        except (requests.ConnectionError, requests.Timeout, requests.SSLError) as exc:
            last_error = exc
        if attempt < 2:
            time.sleep(0.35 * (2**attempt))
    if response is None:
        raise GraphStudioAssistantError(
            "无法读取 Graph Studio 已保存 Queries，已自动重试 3 次。"
        ) from last_error
    if not response.ok:
        detail = response.text.strip().replace("\n", " ")[:400]
        raise GraphStudioAssistantError(
            f"读取 Graph Studio Queries 失败（HTTP {response.status_code}）：{detail}"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise GraphStudioAssistantError("Graph Studio Queries 返回格式无法识别") from exc
    if not isinstance(payload, dict):
        raise GraphStudioAssistantError("Graph Studio Queries 返回格式不正确")
    return payload


def _catalog_query(graphmart_uri: str) -> str:
    return f"""
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX anzo: <http://openanzo.org/ontologies/2008/07/Anzo#>
        PREFIX qp: <http://cambridgesemantics.com/ontologies/QueryPlayground#>
        PREFIX system: <http://openanzo.org/ontologies/2008/07/System#>

        SELECT ?query ?title ?description ?sparql ?modified ?forcedLimit
        WHERE {{
          GRAPH <{graphmart_uri}> {{
            <{graphmart_uri}_queries> qp:children ?orderedItem .
            ?orderedItem anzo:orderedValue ?query .
            ?query dc:title ?title ;
                   system:query ?sparql .
            OPTIONAL {{ ?query dc:description ?description . }}
            OPTIONAL {{ ?query dct:modified ?modified . }}
            OPTIONAL {{ ?query qp:forcedLimit ?forcedLimit . }}
          }}
        }}
        ORDER BY LCASE(STR(?title))
        LIMIT 500
    """


def _parse_catalog(payload: dict[str, Any]) -> list[dict[str, str]]:
    queries: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in _binding_rows(payload):
        query_uri = row.get("query", "").strip()
        sparql = row.get("sparql", "").strip()
        if not query_uri or query_uri in seen or not sparql:
            continue
        try:
            safe_sparql = validate_readonly_sparql(sparql)
        except GraphStudioAssistantError:
            continue
        seen.add(query_uri)
        queries.append({
            "uri": query_uri,
            "title": row.get("title", "未命名 Query").strip() or "未命名 Query",
            "description": row.get("description", "").strip(),
            "sparql": safe_sparql,
            "modified": row.get("modified", "").strip(),
            "forced_limit": row.get("forcedLimit", "").strip(),
        })
    return queries


def _load_persisted_catalog() -> list[dict[str, str]]:
    try:
        payload = json.loads(_CATALOG_CACHE_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return []
    try:
        graphmart_uri = _configuration()["graphmart_uri"]
    except GraphStudioAssistantError:
        return []
    rows = payload.get("queries")
    if payload.get("graphmart_uri") != graphmart_uri or not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _persist_catalog(queries: list[dict[str, str]]) -> None:
    try:
        _CATALOG_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CATALOG_CACHE_PATH.write_text(
            json.dumps(
                {
                    "graphmart_uri": _configuration()["graphmart_uri"],
                    "saved_at": time.time(),
                    "queries": queries,
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def list_saved_queries(*, force_refresh: bool = False) -> list[dict[str, str]]:
    """Return safe SELECT bookmarks from the active Graphmart configuration graph."""
    global _catalog_cache
    now = time.monotonic()
    if not force_refresh and _catalog_cache and now - _catalog_cache[0] < _CATALOG_TTL_SECONDS:
        return _catalog_cache[1]
    with _catalog_lock:
        now = time.monotonic()
        if not force_refresh and _catalog_cache and now - _catalog_cache[0] < _CATALOG_TTL_SECONDS:
            return _catalog_cache[1]
        config = _configuration()
        try:
            queries = _parse_catalog(_request_journal(_catalog_query(config["graphmart_uri"])))
            _persist_catalog(queries)
        except GraphStudioAssistantError:
            queries = _load_persisted_catalog()
            if not queries:
                raise
        _catalog_cache = (now, queries)
        return queries


def public_query_catalog(*, force_refresh: bool = False) -> list[dict[str, str]]:
    """Return browser-safe Query metadata without exposing the complete SPARQL body."""
    return [
        {
            "uri": item["uri"],
            "title": item["title"],
            "description": item.get("description", ""),
            "modified": item.get("modified", ""),
            "forced_limit": item.get("forced_limit", ""),
        }
        for item in list_saved_queries(force_refresh=force_refresh)
    ]
