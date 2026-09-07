from dataclasses import replace

from src.graphstudio_sync.config import SyncSettings
from src.graphstudio_sync.connections import _host_port, settings_from_profiles
from src.graphstudio_sync.repository import ControlPlaneRepository


def _settings() -> SyncSettings:
    return SyncSettings(
        source_host="sql-old",
        source_port=1433,
        source_database="CamstarOld",
        source_user="sa",
        source_password="sql-secret",
        graphstudio_base_url="https://graph-old.example",
        graphstudio_user="graph-user",
        graphstudio_password="graph-secret",
        graphmart_uri="urn:graphmart:old",
        state_database_url="postgresql+psycopg://state/db",
        shared_file_connection=None,
        shared_file_path="old/path",
    )


def test_host_port_supports_explicit_and_default_ports() -> None:
    assert _host_port("sql.example:1444", 1433) == ("sql.example", 1444)
    assert _host_port("sql.example", 1433) == ("sql.example", 1433)


def test_profiles_preserve_environment_addresses_and_secrets() -> None:
    resolved = settings_from_profiles(
        _settings(),
        [
            {
                "connection_key": "camstar-source",
                "enabled": True,
                "endpoint": "sql-new:1434",
                "database_name": "CamstarNew",
                "username": "reader",
            },
            {
                "connection_key": "graph-studio",
                "enabled": True,
                "endpoint": "https://graph-new.example/",
                "database_name": "urn:graphmart:new",
                "username": "publisher",
                "config": {"fileConnection": "urn:file:shared", "filePath": "sync/data"},
            },
        ],
    )

    assert resolved.source_host == "sql-old"
    assert resolved.source_port == 1433
    assert resolved.source_database == "CamstarNew"
    assert resolved.source_password == "sql-secret"
    assert resolved.graphstudio_base_url == "https://graph-old.example"
    assert resolved.graphstudio_password == "graph-secret"
    assert resolved.graphmart_uri == "urn:graphmart:new"
    assert resolved.shared_file_connection == "urn:file:shared"


def test_oracle_source_profile_preserves_runtime_endpoint_and_schema() -> None:
    resolved = settings_from_profiles(
        replace(_settings(), source_host="oracle-env", source_port=1521, source_kind="camstar_oracle"),
        [
            {
                "connection_key": "camstar-source",
                "kind": "camstar_oracle",
                "enabled": True,
                "endpoint": "oracle.internal",
                "database_name": "CAMSTARPDB",
                "username": "camstar",
                "config": {"schema": "CAMSTAR_OWNER", "oracleConnectMode": "service_name"},
            }
        ],
    )

    assert resolved.source_kind == "camstar_oracle"
    assert resolved.source_host == "oracle-env"
    assert resolved.source_port == 1521
    assert resolved.source_database == "CAMSTARPDB"
    assert resolved.source_schema == "CAMSTAR_OWNER"
    assert resolved.source_connect_mode == "service_name"
    assert resolved.source_password == "sql-secret"


class _UpdateResult:
    def __init__(self, *, row=None, rowcount=0):
        self._row = row
        self.rowcount = rowcount

    def mappings(self):
        return self

    def one_or_none(self):
        return self._row


class _UpdateConnection:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement, params):
        sql = str(statement)
        self.calls.append((sql, params))
        if "SELECT database_name" in sql:
            return _UpdateResult(row={"database_name": "urn:graphmart:old"})
        if "UPDATE graphsync.connection_profile" in sql:
            return _UpdateResult(row={
                "connection_key": "graph-studio",
                "database_name": "urn:graphmart:new",
            })
        if "UPDATE graphsync.graphstudio_target" in sql:
            return _UpdateResult(rowcount=1)
        if "UPDATE graphsync.deployment_environment" in sql:
            return _UpdateResult(rowcount=3)
        if "UPDATE graphsync.sync_job" in sql:
            return _UpdateResult(rowcount=1)
        raise AssertionError(sql)


class _UpdateEngine:
    def __init__(self):
        self.connection = _UpdateConnection()

    def begin(self):
        return self.connection


def test_graphstudio_connection_update_synchronizes_matching_default_references() -> None:
    repository = ControlPlaneRepository.__new__(ControlPlaneRepository)
    repository.engine = _UpdateEngine()

    result = repository.update_connection(
        "graph-studio",
        kind="graph_studio",
        display_name="Graph Studio",
        endpoint="https://graph-new.example",
        database_name="urn:graphmart:new",
        username="publisher",
        enabled=True,
        config={},
    )

    assert result["synchronized_references"] == {
        "targets": 1,
        "environments": 3,
        "jobs": 1,
    }
    cascade_calls = repository.engine.connection.calls[2:]
    assert all(call[1]["old_uri"] == "urn:graphmart:old" for call in cascade_calls)
    assert all(call[1]["new_uri"] == "urn:graphmart:new" for call in cascade_calls)


def test_runtime_addresses_replace_stale_rows_without_mutating_history():
    repository = object.__new__(ControlPlaneRepository)
    repository.settings = replace(_settings(), state_database_url="postgresql+psycopg://user:secret@pg-env:5434/db")
    rows = [{"connection_key": key, "endpoint": "stale:1", "status": "online", "last_tested_at": "yesterday", "last_error": "old"}
            for key in ("camstar-source", "graph-studio", "control-postgresql")]
    result = repository._runtime_connections(rows)
    assert [item["endpoint"] for item in result] == ["sql-old:1433", "https://graph-old.example", "pg-env:5434"]
    assert all(item["status"] == "unknown" and item["last_tested_at"] is None and item["last_error"] is None for item in result)
    assert all(item["endpoint"] == "stale:1" and item["status"] == "online" for item in rows)
    assert "secret" not in str(result)


def test_matching_runtime_address_keeps_latest_test_status():
    repository = object.__new__(ControlPlaneRepository)
    repository.settings = _settings()
    row = {"connection_key": "camstar-source", "endpoint": "sql-old:1433", "status": "online", "last_tested_at": "today"}
    assert repository._runtime_connections([row]) == [row]


def test_connection_test_records_the_runtime_address_with_its_status():
    repository = object.__new__(ControlPlaneRepository)
    repository.settings = _settings()
    repository.engine = _UpdateEngine()
    repository.update_connection_status("camstar-source", status="online")
    statement, parameters = repository.engine.connection.calls[0]
    assert "endpoint=COALESCE(:endpoint, endpoint)" in statement
    assert parameters["endpoint"] == "sql-old:1433"
    assert parameters["status"] == "online"


def test_environment_address_cannot_be_changed_through_api(monkeypatch):
    import pytest
    from fastapi import HTTPException
    from web.routers import sync_center
    monkeypatch.setattr(sync_center, "_settings", _settings)
    request = sync_center.ConnectionUpdate(kind="camstar_sqlserver", display_name="Camstar", endpoint="wrong:1", database_name="db", username="user", enabled=True)
    with pytest.raises(HTTPException) as error:
        sync_center.update_connection("camstar-source", request)
    assert error.value.status_code == 409
