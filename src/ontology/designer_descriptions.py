"""Persist bilingual source metadata independently of approved ontology models."""

import hashlib
import json
import os

from sqlalchemy import text

from .authority_store import authority_store


def source_key(database: str) -> str:
    keys = ("SRC_DB_HOST", "SRC_DB_PORT", "SRC_DB_NAME") if database == "sqlserver" else (
        "ORACLE_DB_HOST", "ORACLE_DB_PORT", "ORACLE_DB_SERVICE", "ORACLE_DB_SCHEMA")
    identity = [database, *(os.getenv(key, "") for key in keys)]
    return hashlib.sha256(json.dumps(identity).encode()).hexdigest()


def save_descriptions(database: str, rows: list[dict]) -> None:
    values = [{
        "source": source_key(database), "class": row["className"],
        "field": row.get("fieldName", ""), "en": row["descriptionEn"],
        "zh": row.get("descriptionZh", ""),
        "hash": hashlib.sha256(row["descriptionEn"].encode()).hexdigest(),
    } for row in rows if row.get("descriptionEn")]
    if not values:
        return
    with authority_store().engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO graphsync.designer_description
                (source_key,class_name,field_name,content_hash,description_en,description_zh)
            VALUES (:source,:class,:field,:hash,:en,:zh)
            ON CONFLICT (source_key,class_name,field_name,content_hash) DO UPDATE SET
                description_zh=CASE WHEN EXCLUDED.description_zh <> '' THEN EXCLUDED.description_zh
                    ELSE graphsync.designer_description.description_zh END,
                updated_at=now()
        """), values)


def load_descriptions(database: str) -> dict[tuple[str, str], dict]:
    with authority_store().engine.connect() as connection:
        rows = connection.execute(text("""
            SELECT DISTINCT ON (class_name,field_name) class_name,field_name,description_en,description_zh
            FROM graphsync.designer_description WHERE source_key=:source
            ORDER BY class_name,field_name,updated_at DESC
        """), {"source": source_key(database)}).mappings()
        return {(row["class_name"], row["field_name"]): {
            "descriptionEn": row["description_en"], "descriptionZh": row["description_zh"],
        } for row in rows}
