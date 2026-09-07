import sys
from dataclasses import replace
from types import SimpleNamespace

from src.graphstudio_sync.source_database import connect_source, quote_identifier

from test_graphstudio_sync_connections import _settings


def test_source_identifier_quoting_matches_database_engine() -> None:
    assert quote_identifier("Product", "camstar_sqlserver") == "[Product]"
    assert quote_identifier("PRODUCT", "camstar_oracle") == '"PRODUCT"'


def test_oracle_connection_uses_service_name(monkeypatch) -> None:
    calls = {}
    connection = object()

    def makedsn(host, port, **kwargs):
        calls["dsn"] = (host, port, kwargs)
        return "oracle-dsn"

    def connect(**kwargs):
        calls["connect"] = kwargs
        return connection

    monkeypatch.setitem(sys.modules, "oracledb", SimpleNamespace(makedsn=makedsn, connect=connect))
    settings = replace(
        _settings(),
        source_kind="camstar_oracle",
        source_host="oracle.internal",
        source_port=1521,
        source_database="CAMSTARPDB",
        source_user="camstar",
        source_schema="CAMSTAR_OWNER",
        source_connect_mode="service_name",
    )

    assert connect_source(settings) is connection
    assert calls["dsn"] == (
        "oracle.internal",
        1521,
        {"service_name": "CAMSTARPDB"},
    )
    assert calls["connect"]["dsn"] == "oracle-dsn"
    assert calls["connect"]["user"] == "camstar"
