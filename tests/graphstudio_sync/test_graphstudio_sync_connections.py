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


def test_postgres_connection_profiles_override_metadata_not_secrets() -> None:
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

    assert resolved.source_host == "sql-new"
    assert resolved.source_port == 1434
    assert resolved.source_database == "CamstarNew"
    assert resolved.source_password == "sql-secret"
    assert resolved.graphstudio_base_url == "https://graph-new.example"
    assert resolved.graphstudio_password == "graph-secret"
    assert resolved.graphmart_uri == "urn:graphmart:new"
    assert resolved.shared_file_connection == "urn:file:shared"


def test_oracle_source_profile_selects_driver_defaults_and_schema() -> None:
    resolved = settings_from_profiles(
        _settings(),
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
    assert resolved.source_host == "oracle.internal"
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
