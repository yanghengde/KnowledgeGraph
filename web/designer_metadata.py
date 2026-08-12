"""Read Camstar Designer CDO metadata from SQL Server or Oracle."""

from __future__ import annotations

import os
import re
import threading
import time
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import URL


DATABASES = {"oracle", "sqlserver"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)
_catalog_cache: dict[str, tuple[float, dict[str, dict[str, str]]]] = {}
_catalog_cache_lock = threading.RLock()


def _normalize_database(database: str) -> str:
    value = str(database or "").strip().lower()
    if value not in DATABASES:
        raise ValueError("database must be oracle or sqlserver")
    return value


def _sqlserver_engine():
    import pyodbc

    installed = pyodbc.drivers()
    configured = os.getenv("DB_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    driver_name = configured if configured in installed else next(
        (name for name in reversed(installed) if "SQL Server" in name), configured
    )
    return create_engine(URL.create(
        "mssql+pyodbc",
        username=os.getenv("SRC_DB_USER"), password=os.getenv("SRC_DB_PASSWORD"),
        host=os.getenv("SRC_DB_HOST"), port=int(os.getenv("SRC_DB_PORT", "1433")),
        database=os.getenv("SRC_DB_NAME"),
        query={"driver": driver_name, "TrustServerCertificate": os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")},
    ), pool_pre_ping=True)


def _oracle_engine():
    # SQLAlchemy loads python-oracledb lazily. A missing package or connection
    # configuration is returned to the UI as a non-blocking description warning.
    return create_engine(URL.create(
        "oracle+oracledb",
        username=os.getenv("ORACLE_DB_USER"), password=os.getenv("ORACLE_DB_PASSWORD"),
        host=os.getenv("ORACLE_DB_HOST"), port=int(os.getenv("ORACLE_DB_PORT", "1521")),
        query={"service_name": os.getenv("ORACLE_DB_SERVICE", "")},
    ), pool_pre_ping=True)


def source_engine(database: str):
    return _oracle_engine() if _normalize_database(database) == "oracle" else _sqlserver_engine()


def _safe_identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$#]*", str(value or "")):
        raise RuntimeError(f"Invalid database identifier: {value}")
    return str(value)


@lru_cache(maxsize=2)
def designer_schema(database: str) -> str:
    database = _normalize_database(database)
    engine = source_engine(database)
    with engine.connect() as connection:
        if database == "sqlserver":
            row = connection.execute(text("""
                SELECT TOP 1 TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = 'CDODefinition'
                ORDER BY CASE WHEN TABLE_SCHEMA = 'dbo' THEN 0 ELSE 1 END, TABLE_SCHEMA
            """)).first()
        else:
            preferred = (os.getenv("ORACLE_DB_SCHEMA") or os.getenv("ORACLE_DB_USER") or "").upper()
            rows = connection.execute(text("""
                SELECT OWNER FROM ALL_TABLES WHERE TABLE_NAME = 'CDODEFINITION'
            """)).fetchall()
            row = next((item for item in rows if str(item[0]).upper() == preferred), rows[0] if rows else None)
    if not row:
        raise RuntimeError("Camstar Designer table CDODefinition was not found")
    return _safe_identifier(str(row[0]))


def _table(database: str, schema: str, name: str) -> str:
    schema = _safe_identifier(schema)
    name = _safe_identifier(name)
    return f"[{schema}].[{name}]" if database == "sqlserver" else f'"{schema}"."{name.upper()}"'


def load_cdo_description_catalog(database: str) -> dict[str, dict[str, str]]:
    """Return all CDO English descriptions keyed by case-insensitive CDOName."""
    database = _normalize_database(database)
    ttl = max(0, int(os.getenv("DESIGNER_CATALOG_CACHE_SECONDS", "300")))
    with _catalog_cache_lock:
        cached = _catalog_cache.get(database)
        if cached and time.monotonic() - cached[0] < ttl:
            return cached[1]
        schema = designer_schema(database)
        definition = _table(database, schema, "CDODefinition")
        query = text(f'''SELECT CDODefID AS "CDODefID", CDOName AS "CDOName", CDODescription AS "CDODescription"
                         FROM {definition}''')
        with source_engine(database).connect() as connection:
            rows = connection.execute(query).mappings().all()
        result = {}
        for row in rows:
            name = str(row.get("CDOName") or "").strip()
            description = " ".join(str(row.get("CDODescription") or "").replace("\r", " ").replace("\n", " ").split())
            if name:
                result[name.casefold()] = {
                    "cdoDefId": str(row.get("CDODefID") or ""),
                    "cdoName": name,
                    "description": description[:5000],
                }
        _catalog_cache[database] = (time.monotonic(), result)
        return result


def get_cdo_metadata(database: str, class_name: str) -> dict:
    """Return one CDO description plus inherited field descriptions."""
    database = _normalize_database(database)
    schema = designer_schema(database)
    definition = _table(database, schema, "CDODefinition")
    fields_table = _table(database, schema, "CDOFields")
    candidates = [class_name]
    if class_name.startswith("A_"):
        candidates.append(class_name[2:])
    engine = source_engine(database)
    with engine.connect() as connection:
        rows = connection.execute(
            text(f'''SELECT CDODefID AS "CDODefID", ParentCDOID AS "ParentCDOID",
                            CDOName AS "CDOName", CDODescription AS "CDODescription"
                     FROM {definition} WHERE LOWER(CDOName) IN :names''').bindparams(bindparam("names", expanding=True)),
            {"names": [value.casefold() for value in candidates]},
        ).mappings().all()
        row = next((item for item in rows if str(item.get("CDOName") or "").casefold() == class_name.casefold()), rows[0] if rows else None)
        if not row:
            raise LookupError(f"Camstar Designer CDO not found: {class_name}")
        hierarchy = []
        current = dict(row)
        for _ in range(40):
            hierarchy.append(current)
            parent_id = int(current.get("ParentCDOID") or 0)
            if not parent_id:
                break
            parent = connection.execute(
                text(f'''SELECT CDODefID AS "CDODefID", ParentCDOID AS "ParentCDOID",
                                CDOName AS "CDOName", CDODescription AS "CDODescription"
                         FROM {definition} WHERE CDODefID=:id'''),
                {"id": parent_id},
            ).mappings().first()
            if not parent:
                break
            current = dict(parent)
        hierarchy_ids = [int(item["CDODefID"]) for item in hierarchy]
        field_rows = connection.execute(
            text(f'''SELECT FieldID AS "FieldID", CDODefID AS "CDODefID",
                            FieldName AS "FieldName", FieldDescription AS "FieldDescription"
                     FROM {fields_table} WHERE CDODefID IN :ids''').bindparams(bindparam("ids", expanding=True)),
            {"ids": hierarchy_ids},
        ).mappings().all()
    depth = {cdo_id: index for index, cdo_id in enumerate(hierarchy_ids)}
    field_map = {}
    for field in sorted(field_rows, key=lambda item: depth.get(int(item["CDODefID"]), 999)):
        key = str(field.get("FieldName") or "").casefold()
        description = " ".join(str(field.get("FieldDescription") or "").replace("\r", " ").replace("\n", " ").split())
        if key and description and key not in field_map:
            field_map[key] = {"fieldId": str(field.get("FieldID") or ""), "description": description[:5000]}
    return {
        "cdoDefId": str(row.get("CDODefID") or ""),
        "cdoName": str(row.get("CDOName") or class_name),
        "description": " ".join(str(row.get("CDODescription") or "").replace("\r", " ").replace("\n", " ").split())[:5000],
        "fields": field_map,
    }
