"""Connection profile resolution and safe connectivity tests."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Any
from urllib.parse import quote

import pymssql
import requests
from neo4j import GraphDatabase
from requests.adapters import HTTPAdapter
from sqlalchemy import text
from urllib3.util.retry import Retry

from .config import SyncSettings
from .database import control_engine
from .repository import ControlPlaneRepository


def _host_port(endpoint: str, default_port: int) -> tuple[str, int]:
    value = endpoint.strip()
    if value.startswith("[") and "]:" in value:
        host, port = value[1:].split("]:", 1)
        return host, int(port)
    if value.count(":") == 1:
        host, port = value.rsplit(":", 1)
        return host, int(port)
    return value, default_port


def settings_from_profiles(
    base: SyncSettings,
    profiles: list[dict[str, Any]],
) -> SyncSettings:
    by_key = {item["connection_key"]: item for item in profiles if item.get("enabled", True)}
    values: dict[str, Any] = {}
    source = by_key.get("camstar-source")
    if source:
        values["source_host"], values["source_port"] = _host_port(source["endpoint"], 1433)
        values["source_database"] = source.get("database_name") or base.source_database
        values["source_user"] = source.get("username") or base.source_user
    ontology = by_key.get("ontology-neo4j")
    if ontology:
        values["neo4j_uri"] = ontology["endpoint"]
        values["neo4j_user"] = ontology.get("username") or base.neo4j_user
    graph_studio = by_key.get("graph-studio")
    if graph_studio:
        config = graph_studio.get("config") or {}
        values["graphstudio_base_url"] = graph_studio["endpoint"].rstrip("/")
        values["graphstudio_user"] = graph_studio.get("username") or base.graphstudio_user
        values["graphmart_uri"] = graph_studio.get("database_name") or base.graphmart_uri
        values["shared_file_connection"] = config.get("fileConnection") or base.shared_file_connection
        values["shared_file_path"] = config.get("filePath") or base.shared_file_path
    return replace(base, **values) if values else base


def resolved_settings(base: SyncSettings, repository: ControlPlaneRepository) -> SyncSettings:
    return settings_from_profiles(base, repository.list_connections())


def _test_source(settings: SyncSettings) -> dict[str, Any]:
    connection = pymssql.connect(
        server=settings.source_host,
        port=settings.source_port,
        user=settings.source_user,
        password=settings.source_password,
        database=settings.source_database,
        login_timeout=10,
        timeout=15,
    )
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM sys.tables")
        return {"tables": int(cursor.fetchone()[0])}
    finally:
        connection.close()


def _test_neo4j(settings: SyncSettings) -> dict[str, Any]:
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            count = session.run("MATCH (c:OntologyClass) RETURN count(c) AS count").single()["count"]
        return {"ontologyClasses": int(count)}
    finally:
        driver.close()


def _test_graphstudio(settings: SyncSettings) -> dict[str, Any]:
    session = requests.Session()
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=3,
                connect=3,
                read=3,
                status=3,
                backoff_factor=0.5,
                status_forcelist=(429, 502, 503, 504),
                allowed_methods=frozenset({"GET"}),
            )
        ),
    )
    response = session.get(
        f"{settings.graphstudio_base_url}/api/graphmarts/{quote(settings.graphmart_uri, safe='')}",
        auth=(settings.graphstudio_user, settings.graphstudio_password),
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return {"title": payload.get("title"), "graphmartUri": settings.graphmart_uri}


def _test_postgres(settings: SyncSettings) -> dict[str, Any]:
    engine = control_engine(settings)
    try:
        with engine.connect() as connection:
            schema_version = connection.execute(
                text("SELECT max(version) FROM graphsync.schema_version")
            ).scalar_one()
            database = connection.execute(text("SELECT current_database()")) .scalar_one()
        return {"database": database, "schemaVersion": schema_version}
    finally:
        engine.dispose()


def test_connection(
    base: SyncSettings,
    repository: ControlPlaneRepository,
    key: str,
) -> dict[str, Any]:
    profile = next((item for item in repository.list_connections() if item["connection_key"] == key), None)
    if profile is None:
        raise KeyError(key)
    if not profile["enabled"]:
        repository.update_connection_status(key, status="disabled")
        return {"key": key, "ok": False, "status": "disabled", "error": "Connection is disabled"}
    settings = resolved_settings(base, repository)
    testers = {
        "camstar-source": _test_source,
        "ontology-neo4j": _test_neo4j,
        "graph-studio": _test_graphstudio,
        "control-postgresql": _test_postgres,
    }
    tester = testers.get(key)
    if tester is None:
        raise KeyError(key)
    started = time.perf_counter()
    try:
        details = tester(settings)
        elapsed = round((time.perf_counter() - started) * 1000)
        repository.update_connection_status(key, status="online")
        return {"key": key, "ok": True, "status": "online", "latencyMs": elapsed, "details": details}
    except Exception as exc:  # integration boundary
        elapsed = round((time.perf_counter() - started) * 1000)
        error = str(exc).splitlines()[0][:1000]
        repository.update_connection_status(key, status="offline", error=error)
        return {"key": key, "ok": False, "status": "offline", "latencyMs": elapsed, "error": error}


def test_all_connections(
    base: SyncSettings,
    repository: ControlPlaneRepository,
) -> list[dict[str, Any]]:
    return [
        test_connection(base, repository, item["connection_key"])
        for item in repository.list_connections()
    ]
