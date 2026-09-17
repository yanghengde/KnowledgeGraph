"""Bilingual source metadata retains English revisions independently of models."""
import os
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import event, text

from src.ontology import designer_descriptions as store
from src.graphstudio_sync.config import PROJECT_ROOT, SyncSettings
from src.graphstudio_sync.storage.database import control_engine


def test_source_identity_excludes_passwords_and_separates_databases(monkeypatch):
    monkeypatch.setenv("SRC_DB_HOST", "source")
    monkeypatch.setenv("SRC_DB_NAME", "one")
    first = store.source_key("sqlserver")
    monkeypatch.setenv("SRC_DB_PASSWORD", "changed-secret")
    assert store.source_key("sqlserver") == first
    monkeypatch.setenv("SRC_DB_NAME", "two")
    assert store.source_key("sqlserver") != first


@pytest.mark.skipif(os.getenv("RUN_DESIGNER_POSTGRES_TEST") != "1", reason="PostgreSQL integration opt-in")
def test_bilingual_persistence_and_english_revisions(monkeypatch):
    engine = control_engine(SyncSettings.from_env())
    schema = "designer_test_" + uuid.uuid4().hex
    with engine.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    def rewrite(conn, cursor, statement, parameters, context, executemany):
        return statement.replace("graphsync.", schema + "."), parameters
    event.listen(engine, "before_cursor_execute", rewrite, retval=True)
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql((PROJECT_ROOT / "sql/ontology_authority_postgres.sql").read_text(encoding="utf-8"))
        monkeypatch.setattr(store, "authority_store", lambda: SimpleNamespace(engine=engine))
        row = {"className": "Product", "descriptionEn": "Original\nEnglish", "descriptionZh": "产品说明"}
        store.save_descriptions("sqlserver", [row, {**row, "fieldName": "name"}])
        store.save_descriptions("sqlserver", [{**row, "descriptionZh": ""}])
        assert store.load_descriptions("sqlserver")[("Product", "")]["descriptionZh"] == "产品说明"
        store.save_descriptions("sqlserver", [{**row, "descriptionEn": "Revised English", "descriptionZh": "修订说明"}])
        assert store.load_descriptions("sqlserver")[("Product", "")]["descriptionEn"] == "Revised English"
        with engine.connect() as connection:
            assert connection.execute(text("SELECT count(*) FROM graphsync.designer_description")).scalar_one() == 3
    finally:
        event.remove(engine, "before_cursor_execute", rewrite)
        with engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        engine.dispose()
