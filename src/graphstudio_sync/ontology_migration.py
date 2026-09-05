"""Non-destructive CSV bootstrap and legacy model-copy migration."""
from dataclasses import replace
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


def _legacy_source(settings):
    from .publish_ontology import _driver, _json_value
    driver = _driver(settings)
    try:
        with driver.session(database=settings.neo4j_database) as session:
            def read(tx):
                classes = [_json_value(dict(r["data"])) for r in tx.run("MATCH (c:OntologyClass) RETURN properties(c) AS data ORDER BY c.name")]
                properties = [{**_json_value(dict(r["data"])), "className": r["className"]} for r in tx.run("MATCH (c:OntologyClass)-[:HAS_PROPERTY]->(p:OntologyProperty) RETURN c.name AS className,properties(p) AS data ORDER BY c.name,p.name")]
                relationships = [{**_json_value(dict(r["data"])), "source": r["source"], "target": r["target"]} for r in tx.run("MATCH (s:OntologyClass)-[r:ONTOLOGY_RELATION]->(t:OntologyClass) RETURN s.name AS source,t.name AS target,properties(r) AS data ORDER BY s.name,r.name,t.name")]
                return {"classes": classes, "properties": properties, "relationships": relationships}
            return session.execute_read(read)
    finally:
        driver.close()


def migrate_ontology(settings, *, apply=False):
    """Copy all historical model releases, preserving IDs, metadata and pointers.

    Run with model editing paused. Re-running refuses to overwrite a PostgreSQL
    document that has diverged; switching backends is a separate explicit step.
    """
    from . import publish_ontology as legacy
    legacy_settings = replace(settings, ontology_backend="neo4j")
    source = _legacy_source(legacy_settings)
    store.validate_source(source)
    with store.engine_for(settings) as engine:
        with engine.connect() as conn:
            workspaces = [dict(r) for r in conn.execute(text("SELECT workspace_id,workspace_key,revision FROM graphsync.ontology_workspace ORDER BY workspace_key")).mappings()]
            releases = [dict(r) for r in conn.execute(text("SELECT ontology_release_id,class_count,property_count,relationship_count FROM graphsync.ontology_release ORDER BY ontology_release_id")).mappings()]
        graphs = {w["workspace_key"]: legacy.workspace_graph(legacy_settings, w["workspace_key"]) for w in workspaces}
        frozen = {str(r["ontology_release_id"]): legacy.release_graph(legacy_settings, str(r["ontology_release_id"])) for r in releases}
        for r in releases:
            g = frozen[str(r["ontology_release_id"])]
            counts = (len(g["classes"]), sum(len(c["properties"]) for c in g["classes"]), len(g["relationships"]))
            if counts != (r["class_count"], r["property_count"], r["relationship_count"]):
                raise ValueError("Legacy release content is incomplete: " + str(r["ontology_release_id"]))
        result = {"previewOnly": not apply, "sourceCounts": {k: len(v) for k, v in source.items()},
            "sourceHash": store.digest(source), "workspaces": len(graphs), "releases": len(frozen), "legacyDeleted": False,
            "workspaceHashes": {k: store.digest(v) for k,v in graphs.items()}, "releaseHashes": {k: store.digest(v) for k,v in frozen.items()}}
        if not apply:
            return result
        store.initialize(engine)
        with engine.begin() as conn:
            conn.execute(text("SELECT pg_advisory_xact_lock(721603060)"))
            conn.execute(text("SELECT pg_advisory_xact_lock(721603061)"))
            existing_source = conn.execute(text("SELECT s.content_hash FROM graphsync.ontology_source_activation a JOIN graphsync.ontology_source_snapshot s USING(snapshot_id)")).scalar_one_or_none()
            if existing_source is not None and existing_source != store.digest(source):
                raise ValueError("PostgreSQL source has diverged; refusing migration overwrite")
            for w in workspaces:
                revision = conn.execute(text("SELECT revision FROM graphsync.ontology_workspace WHERE workspace_id=:id FOR UPDATE"), {"id": w["workspace_id"]}).scalar_one()
                if revision != w["revision"]:
                    raise ValueError("Workspace changed during migration; retry with model editing paused")
                g = graphs[w["workspace_key"]]
                # Detect a concurrent legacy edit before importing any pointer.
                if store.digest(legacy.workspace_graph(legacy_settings, w["workspace_key"])) != store.digest(g):
                    raise ValueError("Legacy graph changed during migration")
                existing = conn.execute(text("SELECT graph FROM graphsync.ontology_workspace_document WHERE workspace_id=:id"), {"id": w["workspace_id"]}).scalar_one_or_none()
                if existing is not None and store.digest(existing) != store.digest(g):
                    raise ValueError("PostgreSQL workspace has diverged; refusing overwrite")
                conn.execute(text("INSERT INTO graphsync.ontology_workspace_document(workspace_id,graph) VALUES (:id,CAST(:graph AS jsonb)) ON CONFLICT DO NOTHING"), {"id": w["workspace_id"], "graph": store.canonical(g)})
            for r in releases:
                g = frozen[str(r["ontology_release_id"])]
                existing = conn.execute(text("SELECT document_hash FROM graphsync.ontology_release_document WHERE ontology_release_id=:id"), {"id": r["ontology_release_id"]}).scalar_one_or_none()
                if existing is not None and existing != store.digest(g):
                    raise ValueError("PostgreSQL release has diverged; refusing overwrite")
                conn.execute(text("INSERT INTO graphsync.ontology_release_document(ontology_release_id,graph,document_hash,provenance) VALUES (:id,CAST(:graph AS jsonb),:hash,'{\"kind\":\"neo4j_migration\"}'::jsonb) ON CONFLICT DO NOTHING"), {"id": r["ontology_release_id"], "graph": store.canonical(g), "hash": store.digest(g)})
            result.update(store.save_source(conn, source, {"kind": "neo4j_migration", "sourceDatabase": settings.neo4j_database}, activate=True))
        result["nextStep"] = "Verify equivalence, then set ONTOLOGY_BACKEND=postgres and restart; Neo4j remains unchanged."
        return result


def postgres_status(settings):
    with store.engine_for(settings) as engine, engine.connect() as conn:
        source = store.source_payload(settings, conn)
        missing_workspaces = conn.execute(text("SELECT count(*) FROM graphsync.ontology_workspace w LEFT JOIN graphsync.ontology_workspace_document d USING(workspace_id) WHERE d.workspace_id IS NULL")).scalar_one()
        missing_releases = conn.execute(text("SELECT count(*) FROM graphsync.ontology_release r LEFT JOIN graphsync.ontology_release_document d USING(ontology_release_id) WHERE d.ontology_release_id IS NULL")).scalar_one()
        corrupt = sum(store.digest(r["graph"]) != r["document_hash"] for r in conn.execute(text("SELECT graph,document_hash FROM graphsync.ontology_release_document")).mappings())
        return {"backend": "postgres", "ready": not (missing_workspaces or missing_releases or corrupt), "sourceCounts": {k: len(v) for k,v in source.items()}, "missingWorkspaces": missing_workspaces, "missingReleases": missing_releases, "corruptReleases": corrupt}
