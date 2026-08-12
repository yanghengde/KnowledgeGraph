from src.graphstudio_sync.config import _state_database_url


PGSQL_KEYS = (
    "PGSQL_ENABLED",
    "PGSQL_HOST",
    "PGSQL_PORT",
    "PGSQL_DATABASE",
    "PGSQL_USER",
    "PGSQL_PASSWORD",
    "PGSQL_SSLMODE",
    "SYNC_STATE_DATABASE_URL",
)


def _clear(monkeypatch) -> None:
    for key in PGSQL_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_postgres_is_optional(monkeypatch) -> None:
    _clear(monkeypatch)
    assert _state_database_url() is None


def test_postgres_url_is_built_from_component_settings(monkeypatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("PGSQL_ENABLED", "true")
    monkeypatch.setenv("PGSQL_HOST", "db.internal")
    monkeypatch.setenv("PGSQL_PORT", "5432")
    monkeypatch.setenv("PGSQL_DATABASE", "graphsync")
    monkeypatch.setenv("PGSQL_USER", "sync-user")
    monkeypatch.setenv("PGSQL_PASSWORD", "p@ss/word")
    monkeypatch.setenv("PGSQL_SSLMODE", "require")

    assert _state_database_url() == (
        "postgresql+psycopg://sync-user:p%40ss%2Fword@db.internal:5432/graphsync?sslmode=require"
    )


def test_explicit_url_takes_precedence(monkeypatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("SYNC_STATE_DATABASE_URL", "postgresql+psycopg://override/db")
    monkeypatch.setenv("PGSQL_ENABLED", "false")
    assert _state_database_url() == "postgresql+psycopg://override/db"
