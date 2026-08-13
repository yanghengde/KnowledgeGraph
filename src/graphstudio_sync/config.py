"""Environment-backed settings for the Graph Studio synchronization tool."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _enabled(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _state_database_url() -> str | None:
    """Build the control-plane URL without requiring a password-bearing URL in .env."""
    explicit_url = os.getenv("SYNC_STATE_DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url
    if not _enabled("PGSQL_ENABLED"):
        return None
    password = _required("PGSQL_PASSWORD")
    url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("PGSQL_USER", "graphsync").strip(),
        password=password,
        host=os.getenv("PGSQL_HOST", "127.0.0.1").strip(),
        port=int(os.getenv("PGSQL_PORT", "5433")),
        database=os.getenv("PGSQL_DATABASE", "graphsync").strip(),
        query={"sslmode": os.getenv("PGSQL_SSLMODE", "prefer").strip()},
    )
    return url.render_as_string(hide_password=False)


@dataclass(frozen=True)
class SyncSettings:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    source_host: str
    source_port: int
    source_database: str
    source_user: str
    source_password: str
    graphstudio_base_url: str
    graphstudio_user: str
    graphstudio_password: str
    graphmart_uri: str
    state_database_url: str | None
    shared_file_connection: str | None
    shared_file_path: str
    source_kind: str = "camstar_sqlserver"
    source_schema: str | None = None
    source_connect_mode: str = "service_name"
    camstar_api_base_url: str | None = None
    camstar_api_user: str | None = None
    camstar_api_password: str | None = None
    camstar_api_token: str | None = None
    action_auth_mode: str = "disabled"
    action_trusted_proxy_secret: str | None = None

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "SyncSettings":
        load_dotenv(env_file or PROJECT_ROOT / ".env", override=False)
        return cls(
            neo4j_uri=_required("NEO4J_URI"),
            neo4j_user=_required("NEO4J_USER"),
            neo4j_password=_required("NEO4J_PASSWORD"),
            source_host=_required("SRC_DB_HOST"),
            source_port=int(
                os.getenv(
                    "SRC_DB_PORT",
                    "1521" if os.getenv("SRC_DB_TYPE", "sqlserver").strip().casefold() == "oracle" else "1433",
                )
            ),
            source_database=_required("SRC_DB_NAME"),
            source_user=_required("SRC_DB_USER"),
            source_password=_required("SRC_DB_PASSWORD"),
            graphstudio_base_url=_required("GRAPHSTUDIO_BASE_URL").rstrip("/"),
            graphstudio_user=_required("GRAPHSTUDIO_USER"),
            graphstudio_password=_required("GRAPHSTUDIO_PASSWORD"),
            graphmart_uri=os.getenv(
                "GRAPHSTUDIO_GRAPHMART_URI",
                "http://cambridgesemantics.com/Graphmart/ba6308d1b3764b8a8ad40d90500ddd56",
            ).strip(),
            state_database_url=_state_database_url(),
            shared_file_connection=os.getenv("GRAPHSTUDIO_FILE_CONNECTION") or None,
            shared_file_path=os.getenv("GRAPHSTUDIO_FILE_PATH", "Opcenter2607/CamstarSync").strip("/"),
            source_kind=(
                "camstar_oracle"
                if os.getenv("SRC_DB_TYPE", "sqlserver").strip().casefold() == "oracle"
                else "camstar_sqlserver"
            ),
            source_schema=os.getenv("SRC_DB_SCHEMA", "").strip() or None,
            source_connect_mode=os.getenv("SRC_DB_ORACLE_MODE", "service_name").strip().casefold(),
            camstar_api_base_url=os.getenv("CAMSTAR_API_BASE_URL", "").strip().rstrip("/") or None,
            camstar_api_user=os.getenv("CAMSTAR_API_USER", "").strip() or None,
            camstar_api_password=os.getenv("CAMSTAR_API_PASSWORD", "").strip() or None,
            camstar_api_token=os.getenv("CAMSTAR_API_TOKEN", "").strip() or None,
            action_auth_mode=os.getenv("ACTION_AUTH_MODE", "disabled").strip().casefold(),
            action_trusted_proxy_secret=os.getenv("ACTION_TRUSTED_PROXY_SECRET", "").strip() or None,
        )
