"""CSV source-model import and PostgreSQL model status."""
import hashlib
from sqlalchemy import text
from . import ontology_store as store
from .config import PROJECT_ROOT


def import_csv_model(settings, *, classes=None, apply=False, activate=False):
    tables = PROJECT_ROOT / "docs/Database_Tables.csv"
    fields = PROJECT_ROOT / "docs/Database_Fields.csv"
    payload = store.csv_model(tables, fields, classes)
    provenance = {"kind": "csv", "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (tables, fields)}}
    result = {"previewOnly": not apply, "counts": {k: len(v) for k, v in payload.items()}, "contentHash": store.digest(payload), "provenance": provenance}
    if apply:
        with store.engine_for(settings) as engine:
            store.initialize(engine)
            with engine.begin() as conn:
                result.update(store.save_source(conn, payload, provenance, activate=activate))
    return result


def postgres_status(settings):
    with store.engine_for(settings) as engine, engine.connect() as conn:
        source = store.source_payload(settings, conn)
        missing_workspaces = conn.execute(text("SELECT count(*) FROM graphsync.ontology_workspace w LEFT JOIN graphsync.ontology_workspace_document d USING(workspace_id) WHERE d.workspace_id IS NULL")).scalar_one()
        missing_releases = conn.execute(text("SELECT count(*) FROM graphsync.ontology_release r LEFT JOIN graphsync.ontology_release_document d USING(ontology_release_id) WHERE d.ontology_release_id IS NULL")).scalar_one()
        corrupt = sum(store.digest(r["graph"]) != r["document_hash"] for r in conn.execute(text("SELECT graph,document_hash FROM graphsync.ontology_release_document")).mappings())
        return {"backend": "postgres", "ready": not (missing_workspaces or missing_releases or corrupt), "sourceCounts": {k: len(v) for k,v in source.items()}, "missingWorkspaces": missing_workspaces, "missingReleases": missing_releases, "corruptReleases": corrupt}
