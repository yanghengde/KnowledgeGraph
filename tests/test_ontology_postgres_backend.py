"""Backend parity and no-Neo4j checks. Integration uses a disposable schema only."""
from contextlib import contextmanager
from dataclasses import replace
import os
from pathlib import Path
import re
from types import SimpleNamespace
import uuid

import pytest
from sqlalchemy import event, text
from src.graphstudio_sync import ontology_store as store, publish_ontology as ontology
from src.graphstudio_sync.config import PROJECT_ROOT, SyncSettings
from src.graphstudio_sync.database import control_engine


def test_csv_preserves_distinct_product_foreign_keys_and_provenance():
    model = store.csv_model(PROJECT_ROOT / "docs/Database_Tables.csv", PROJECT_ROOT / "docs/Database_Fields.csv", ["MfgOrder", "Product", "ProductBase"])
    relations = [r for r in model["relationships"] if r["source"] == "MfgOrder" and r["target"] == "Product"]
    assert {r["physicalColumn"] for r in relations} == {"ProductId", "BeginProductId"}
    assert len({r["name"] for r in relations}) == 2
    assert all(r["sourceFieldId"] for r in relations)
    props = {p["name"]: p for p in model["properties"] if p["className"] == "MfgOrder"}
    assert all(props[r["sourceProperty"]]["dataType"] == "Navigation" for r in relations)


def test_postgres_settings_do_not_require_neo4j(monkeypatch, tmp_path):
    monkeypatch.setenv("ONTOLOGY_BACKEND", "postgres")
    for key in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "PUBLISH_NEO4J_URI", "PUBLISH_NEO4J_USER", "PUBLISH_NEO4J_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    for key in ("SRC_DB_HOST", "SRC_DB_NAME", "SRC_DB_USER", "SRC_DB_PASSWORD", "GRAPHSTUDIO_USER", "GRAPHSTUDIO_PASSWORD"):
        monkeypatch.setenv(key, "test")
    monkeypatch.setenv("GRAPHSTUDIO_BASE_URL", "https://example.test")
    monkeypatch.setenv("PGSQL_ENABLED", "false")
    settings = SyncSettings.from_env(tmp_path / "absent.env")
    assert settings.ontology_backend == "postgres"
    assert not hasattr(settings, "neo4j_password")


def test_postgres_read_never_falls_back_to_neo4j(monkeypatch):
    from src.graphstudio_sync.catalog import _ontology_catalog
    from src.graphstudio_sync.inventory import read_ontology
    from src.graphstudio_sync.preview import _load_descriptions
    def missing(*args, **kwargs):
        raise RuntimeError("source not imported")
    monkeypatch.setattr(store, "source_payload", missing)
    settings = SimpleNamespace(ontology_backend="postgres")
    for read in (_ontology_catalog, read_ontology, _load_descriptions):
        with pytest.raises(RuntimeError, match="source not imported"):
            read(settings)


@pytest.mark.skipif(os.getenv("RUN_MODEL_POSTGRES_TEST") != "1", reason="PostgreSQL integration opt-in")
def test_postgres_model_lifecycle_without_neo4j(monkeypatch):
    settings = SyncSettings.from_env()
    engine = control_engine(settings)
    schema = "model_test_" + uuid.uuid4().hex
    with engine.begin() as conn:
        conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    def rewrite(conn, cursor, statement, parameters, context, executemany):
        return statement.replace("graphsync.", schema + "."), parameters
    event.listen(engine, "before_cursor_execute", rewrite, retval=True)
    @contextmanager
    def test_engine(_settings):
        yield engine
    monkeypatch.setattr(store, "engine_for", test_engine)
    repository = SimpleNamespace(engine=engine, settings=settings)
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE graphsync.graph_profile(profile_key text PRIMARY KEY)"))
            conn.execute(text("INSERT INTO graphsync.graph_profile VALUES ('demo')"))
            # Use the real legacy metadata DDL, not a simplified copy of its constraints.
            ddl = (PROJECT_ROOT / "sql/graphstudio_sync_control_postgres.sql").read_text(encoding="utf-8")
            for name in ("ontology_workspace", "ontology_release", "ontology_release_activation"):
                statement = re.search(r"CREATE TABLE IF NOT EXISTS graphsync\." + name + r" \([\s\S]+?\n\);", ddl).group(0)
                conn.exec_driver_sql(statement)
        store.initialize(engine)
        payload = {"classes": [{"name": "MfgOrder"}, {"name": "Product"}], "properties": [
            {"className": "MfgOrder", "name": "name", "dataType": "String"},
            {"className": "Product", "name": "name", "dataType": "String"}],
            "relationships": [{"source": "MfgOrder", "name": "HAS_PRODUCT", "target": "Product"}]}
        with engine.begin() as conn:
            first = store.save_source(conn, payload, {"kind": "test"}, activate=True)
            assert store.save_source(conn, payload, {"kind": "test"}, activate=True)["snapshotId"] == first["snapshotId"]
        from src.ontology.authority_store import AuthorityStore
        from web.routers import ontology_authority as authority_api
        authority = AuthorityStore(engine)
        authority.initialize()
        with engine.begin() as conn:
            authority.save(conn, {"className": "Product", "revision": 0, "domain": "product", "model": {
                "class": {"className": "Product", "description": "Reviewed product", "properties": [{"name": "name", "type": "String"}]}, "relationships": []}})
        monkeypatch.setenv("ONTOLOGY_BACKEND", "postgres")
        monkeypatch.setattr(authority_api, "_store", lambda: authority)
        monkeypatch.setattr("web.routers.graph.invalidate_graph_caches", lambda: None)
        assert authority_api.sync("Product", authority_api.Revision(revision=1))["status"] == "synced"
        assert next(c for c in store.source_payload(settings)["classes"] if c["name"] == "Product")["description"] == "Reviewed product"
        ontology.create_workspace(settings, repository, profile_key="demo", workspace_key="demo-draft", title="Demo", actor="test", seed_profile=False)
        for name, role in (("MfgOrder", "core"), ("Product", "context")):
            ontology.add_class(settings, repository, workspace_key="demo-draft", source_class=name, target_name=name, role=role)
        suggestions = ontology.relationship_suggestions(settings, repository, "demo-draft", "demo-draft::MfgOrder")
        assert len(suggestions["items"]) == 1
        applied = ontology.apply_relationship_suggestions(settings, repository, "demo-draft", "demo-draft::MfgOrder", [suggestions["items"][0]["id"]])
        assert len(applied["addedRelationshipKeys"]) == 1
        assert ontology.validate_workspace(settings, repository, "demo-draft")["valid"]
        ontology.review_workspace(settings, repository, "demo-draft", "test")
        release = ontology.approve_workspace(settings, repository, "demo-draft", "test")
        frozen = ontology.release_graph(settings, release["releaseId"])
        assert len(frozen["relationships"]) == 1
        assert len(frozen["classes"]) == 2
        ontology.activate_release(repository, "demo", uuid.UUID(release["releaseId"]), "test")
        repeated = ontology.activate_release(repository, "demo", uuid.UUID(release["releaseId"]), "test")
        assert repeated["previousReleaseId"] is None
        ontology.update_class(settings, repository, "demo-draft", "demo-draft::MfgOrder", {"targetName": "ManufacturingOrder", "role": "core"})
        assert ontology.release_graph(settings, release["releaseId"]) == frozen
        assert any(n["data"]["targetName"] == "ManufacturingOrder" for n in ontology.workspace_graph(settings, "demo-draft")["nodes"])
        # Failed edit rolls back the graph AND revision.
        with engine.connect() as conn:
            before = store.workspace(conn, "demo-draft")
        def broken(g):
            g["nodes"].clear()
            raise RuntimeError("interrupted")
        with pytest.raises(RuntimeError, match="interrupted"):
            store.edit_graph(repository, "demo-draft", broken)
        with engine.connect() as conn:
            after = store.workspace(conn, "demo-draft")
        assert (after["graph"], after["revision"]) == (before["graph"], before["revision"])
        undone = ontology.undo_relationship_suggestion_batch(settings, repository, "demo-draft", applied["batchId"])
        assert undone["removedRelationships"] == 1
        # No implicit legacy fallback for a missing immutable version.
        with pytest.raises(RuntimeError, match="未迁移"):
            ontology.release_graph(settings, str(uuid.uuid4()))
        with engine.begin() as conn:
            conn.execute(text("UPDATE graphsync.ontology_release_document SET document_hash='corrupt' WHERE ontology_release_id=:id"), {"id": uuid.UUID(release["releaseId"])})
        with pytest.raises(ValueError, match="corrupt"):
            ontology.activate_release(repository, "demo", uuid.UUID(release["releaseId"]), "test")
    finally:
        event.remove(engine, "before_cursor_execute", rewrite)
        with engine.begin() as conn:
            conn.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        engine.dispose()
