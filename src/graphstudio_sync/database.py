"""PostgreSQL control-plane lifecycle and runtime metadata seeding."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL, make_url

from .config import PROJECT_ROOT, SyncSettings


DDL_FILE = PROJECT_ROOT / "sql" / "graphstudio_sync_control_postgres.sql"


def control_engine(settings: SyncSettings) -> Engine:
    if not settings.state_database_url:
        raise RuntimeError("PostgreSQL control plane is not configured")
    return create_engine(
        settings.state_database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"connect_timeout": 10},
    )


def _admin_url(target_url: str) -> URL:
    return make_url(target_url).set(database=os.getenv("PGSQL_ADMIN_DATABASE", "postgres"))


def ensure_database(settings: SyncSettings) -> dict[str, Any]:
    """Create the configured database when the login has CREATEDB permission."""
    if not settings.state_database_url:
        raise RuntimeError("PostgreSQL control plane is not configured")
    target = make_url(settings.state_database_url)
    database = str(target.database or "").strip()
    if not database:
        raise RuntimeError("PostgreSQL database name is empty")
    admin = _admin_url(settings.state_database_url)
    kwargs = {
        "host": admin.host,
        "port": admin.port or 5432,
        "dbname": admin.database,
        "user": admin.username,
        "password": admin.password,
        "connect_timeout": 10,
    }
    if admin.query.get("sslmode"):
        kwargs["sslmode"] = admin.query["sslmode"]
    created = False
    with psycopg.connect(**kwargs, autocommit=True) as connection:
        exists = connection.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = %s)",
            (database,),
        ).fetchone()[0]
        if not exists:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
            created = True
    return {"database": database, "created": created}


def seed_runtime_connections(
    settings: SyncSettings,
    engine: Engine,
    *,
    overwrite: bool = False,
) -> None:
    profiles = [
        {
            "key": "camstar-source",
            "kind": settings.source_kind,
            "name": "Camstar Oracle" if settings.source_kind == "camstar_oracle" else "Camstar SQL Server",
            "endpoint": f"{settings.source_host}:{settings.source_port}",
            "database": settings.source_database,
            "username": settings.source_user,
            "secret_ref": "env://SRC_DB_PASSWORD",
            "config": {
                "role": "business_source",
                "schema": settings.source_schema,
                "oracleConnectMode": settings.source_connect_mode,
            },
        },
        {
            "key": "ontology-neo4j",
            "kind": "ontology_neo4j",
            "name": "Ontology Neo4j",
            "endpoint": settings.neo4j_uri,
            "database": None,
            "username": settings.neo4j_user,
            "secret_ref": "env://NEO4J_PASSWORD",
            "config": {"role": "mapping_source"},
        },
        {
            "key": "graph-studio",
            "kind": "graph_studio",
            "name": "Graph Studio",
            "endpoint": settings.graphstudio_base_url,
            "database": settings.graphmart_uri,
            "username": settings.graphstudio_user,
            "secret_ref": "env://GRAPHSTUDIO_PASSWORD",
            "config": {
                "role": "publish_target",
                "fileConnection": settings.shared_file_connection,
                "filePath": settings.shared_file_path,
            },
        },
    ]
    state_url = make_url(settings.state_database_url or "")
    profiles.append(
        {
            "key": "control-postgresql",
            "kind": "state_postgresql",
            "name": "Sync Control PostgreSQL",
            "endpoint": f"{state_url.host}:{state_url.port or 5432}",
            "database": state_url.database,
            "username": state_url.username,
            "secret_ref": "env://PGSQL_PASSWORD",
            "config": {"role": "control_plane", "schema": "graphsync"},
        }
    )
    conflict_clause = (
        """
        INSERT INTO graphsync.connection_profile
            (connection_key, kind, display_name, endpoint, database_name,
             username, secret_ref, config)
        VALUES
            (:key, :kind, :name, :endpoint, :database, :username, :secret_ref,
             CAST(:config AS jsonb))
        ON CONFLICT (connection_key) DO UPDATE SET
            kind = EXCLUDED.kind,
            display_name = EXCLUDED.display_name,
            endpoint = EXCLUDED.endpoint,
            database_name = EXCLUDED.database_name,
            username = EXCLUDED.username,
            secret_ref = EXCLUDED.secret_ref,
            config = graphsync.connection_profile.config || EXCLUDED.config
        """
        if overwrite
        else """
        INSERT INTO graphsync.connection_profile
            (connection_key, kind, display_name, endpoint, database_name,
             username, secret_ref, config)
        VALUES
            (:key, :kind, :name, :endpoint, :database, :username, :secret_ref,
             CAST(:config AS jsonb))
        ON CONFLICT (connection_key) DO NOTHING
        """
    )
    statement = text(conflict_clause)
    with engine.begin() as connection:
        for profile in profiles:
            connection.execute(statement, {**profile, "config": json.dumps(profile["config"])})


def initialize_control_plane(
    settings: SyncSettings,
    *,
    create_database: bool = True,
    overwrite_connections: bool = False,
) -> dict[str, Any]:
    database_result = ensure_database(settings) if create_database else {
        "database": make_url(settings.state_database_url or "").database,
        "created": False,
    }
    ddl = DDL_FILE.read_text(encoding="utf-8")
    engine = control_engine(settings)
    with engine.begin() as connection:
        connection.exec_driver_sql(ddl)
    seed_runtime_connections(settings, engine, overwrite=overwrite_connections)
    with engine.connect() as connection:
        counts = {
            "tables": connection.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema='graphsync' AND table_type='BASE TABLE'")
            ).scalar_one(),
            "curatedTables": connection.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema='camstar_curated' AND table_type='BASE TABLE'")
            ).scalar_one(),
            "views": connection.execute(
                text("SELECT count(*) FROM information_schema.views WHERE table_schema='graphsync'")
            ).scalar_one(),
            "connections": connection.execute(
                text("SELECT count(*) FROM graphsync.connection_profile")
            ).scalar_one(),
            "menus": connection.execute(text("SELECT count(*) FROM graphsync.menu_item")).scalar_one(),
            "jobs": connection.execute(text("SELECT count(*) FROM graphsync.sync_job")).scalar_one(),
            "settings": connection.execute(text("SELECT count(*) FROM graphsync.app_setting")).scalar_one(),
        }
    engine.dispose()
    return {**database_result, "schema": "graphsync", **counts}
