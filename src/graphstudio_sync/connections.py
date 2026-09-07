"""Connection profile resolution and safe connectivity tests."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Any
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from sqlalchemy import text
from urllib3.util.retry import Retry

from .config import SyncSettings
from .transport import configure_graphstudio_tls
from .database import control_engine
from .graphstudio_api import require_graphstudio_2026_1_ready
from .repository import ControlPlaneRepository
from .source_database import ORACLE_KIND, connect_source, fetch_dicts, source_cursor


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
        source_kind = source.get("kind") or base.source_kind
        source_config = source.get("config") or {}
        values["source_kind"] = source_kind
        values["source_database"] = source.get("database_name") or base.source_database
        values["source_user"] = source.get("username") or base.source_user
        values["source_schema"] = source_config.get("schema") or base.source_schema
        values["source_connect_mode"] = source_config.get("oracleConnectMode") or base.source_connect_mode
    graph_studio = by_key.get("graph-studio")
    if graph_studio:
        config = graph_studio.get("config") or {}
        values["graphstudio_user"] = graph_studio.get("username") or base.graphstudio_user
        values["graphmart_uri"] = graph_studio.get("database_name") or base.graphmart_uri
        values["shared_file_connection"] = config.get("fileConnection") or base.shared_file_connection
        values["shared_file_path"] = config.get("filePath") or base.shared_file_path
    return replace(base, **values) if values else base


def resolved_settings(base: SyncSettings, repository: ControlPlaneRepository) -> SyncSettings:
    return settings_from_profiles(base, repository.list_connections())


def _test_source(settings: SyncSettings) -> dict[str, Any]:
    connection = connect_source(settings)
    try:
        cursor = source_cursor(connection, settings.source_kind)
        if settings.source_kind == ORACLE_KIND:
            owner = (settings.source_schema or settings.source_user).upper()
            cursor.execute(
                'SELECT COUNT(*) AS "table_count" FROM ALL_TABLES WHERE OWNER=:owner',
                {"owner": owner},
            )
            count = fetch_dicts(cursor)[0]["table_count"]
            return {"engine": "oracle", "schema": owner, "tables": int(count)}
        cursor.execute("SELECT COUNT(*) AS table_count FROM sys.tables")
        count = fetch_dicts(cursor)[0]["table_count"]
        return {"engine": "sqlserver", "tables": int(count)}
    finally:
        connection.close()






def _test_graphstudio(settings: SyncSettings) -> dict[str, Any]:
    session = requests.Session()
    session.auth = (settings.graphstudio_user, settings.graphstudio_password)
    session.headers.update({"Accept": "application/json", "Accept-Encoding": "identity"})
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
    configure_graphstudio_tls(session, settings.graphstudio_base_url, settings.graphstudio_tls_fingerprint)
    server = require_graphstudio_2026_1_ready(
        session,
        settings.graphstudio_base_url,
        graphmart_uri=settings.graphmart_uri,
        file_connection=settings.shared_file_connection if settings.graphstudio_publish_transport == "shared_store" else None,
        file_path=settings.shared_file_path,
    )
    response = session.get(
        f"{settings.graphstudio_base_url}/api/graphmarts/{quote(settings.graphmart_uri, safe='')}",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return {
        "title": payload.get("title"),
        "graphmartUri": settings.graphmart_uri,
        "serverVersion": server["version"],
    }


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
    if key not in {"camstar-source", "graph-studio", "control-postgresql"}:
        raise KeyError(key)
    if not profile["enabled"]:
        repository.update_connection_status(key, status="disabled")
        return {"key": key, "ok": False, "status": "disabled", "error": "Connection is disabled"}
    settings = resolved_settings(base, repository)
    testers = {
        "camstar-source": _test_source,
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
