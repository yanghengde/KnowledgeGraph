"""Database-dialect boundary for the Camstar business source."""

from __future__ import annotations

from typing import Any

import pymssql

from .config import SyncSettings


SQLSERVER_KIND = "camstar_sqlserver"
ORACLE_KIND = "camstar_oracle"
SOURCE_KINDS = {SQLSERVER_KIND, ORACLE_KIND}


def source_default_port(kind: str) -> int:
    return 1521 if kind == ORACLE_KIND else 1433


def connect_source(settings: SyncSettings):
    if settings.source_kind == ORACLE_KIND:
        try:
            import oracledb
        except ImportError as exc:  # pragma: no cover - depends on optional runtime install
            raise RuntimeError(
                "Oracle source requires the 'oracledb' package; install requirements.txt"
            ) from exc
        dsn_options = {
            "sid": settings.source_database,
        } if settings.source_connect_mode == "sid" else {
            "service_name": settings.source_database,
        }
        dsn = oracledb.makedsn(settings.source_host, settings.source_port, **dsn_options)
        return oracledb.connect(
            user=settings.source_user,
            password=settings.source_password,
            dsn=dsn,
        )
    if settings.source_kind != SQLSERVER_KIND:
        raise RuntimeError(f"Unsupported Camstar source kind: {settings.source_kind}")
    return pymssql.connect(
        server=settings.source_host,
        port=settings.source_port,
        user=settings.source_user,
        password=settings.source_password,
        database=settings.source_database,
        login_timeout=20,
        timeout=180,
    )


def source_cursor(connection, kind: str):
    return connection.cursor(as_dict=True) if kind == SQLSERVER_KIND else connection.cursor()


def fetch_dicts(cursor) -> list[dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows:
        return []
    if isinstance(rows[0], dict):
        return [dict(row) for row in rows]
    columns = [str(item[0]) for item in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def fetchmany_dicts(cursor, size: int) -> list[dict[str, Any]]:
    rows = cursor.fetchmany(size)
    if not rows:
        return []
    if isinstance(rows[0], dict):
        return [dict(row) for row in rows]
    columns = [str(item[0]) for item in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def quote_identifier(value: str, kind: str) -> str:
    if kind == ORACLE_KIND:
        return f'"{value}"'
    return f"[{value}]"
