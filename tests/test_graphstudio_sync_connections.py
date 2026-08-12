from src.graphstudio_sync.config import SyncSettings
from src.graphstudio_sync.connections import _host_port, settings_from_profiles


def _settings() -> SyncSettings:
    return SyncSettings(
        neo4j_uri="bolt://neo4j:7687",
        neo4j_user="neo4j",
        neo4j_password="neo-secret",
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
