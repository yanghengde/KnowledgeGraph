"""Versioned model documents in the existing PostgreSQL control plane."""
from contextlib import contextmanager
from copy import deepcopy
import csv
import hashlib
import json
import uuid

from sqlalchemy import text
from src.graphstudio_sync.config import PROJECT_ROOT
from src.graphstudio_sync.storage.database import control_engine


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@contextmanager
def engine_for(settings):
    engine = control_engine(settings)
    try:
        yield engine
    finally:
        engine.dispose()


def initialize(engine):
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(721603060)"))
        conn.exec_driver_sql((PROJECT_ROOT / "sql/ontology_model_postgres.sql").read_text(encoding="utf-8"))


def source_payload(settings, connection=None):
    if connection is None:
        with engine_for(settings) as engine, engine.connect() as conn:
            return source_payload(settings, conn)
    row = connection.execute(text("""
        SELECT snapshot.payload, snapshot.content_hash FROM graphsync.ontology_source_activation active
        JOIN graphsync.ontology_source_snapshot snapshot USING (snapshot_id)
        WHERE active.singleton
    """)).mappings().one_or_none()
    if row is None:
        raise RuntimeError("PostgreSQL 本体尚未初始化；请先运行 import-csv-model 或 migrate-ontology --apply")
    if digest(row["payload"]) != row["content_hash"]:
        raise RuntimeError("PostgreSQL source model integrity check failed")
    return row["payload"]


def save_source(connection, payload, provenance, *, activate=False):
    validate_source(payload)
    key = digest(payload)
    row = connection.execute(text("""
        INSERT INTO graphsync.ontology_source_snapshot(snapshot_id,content_hash,payload,provenance)
        VALUES (:id,:hash,CAST(:payload AS jsonb),CAST(:provenance AS jsonb))
        ON CONFLICT(content_hash) DO UPDATE SET content_hash=EXCLUDED.content_hash
        RETURNING snapshot_id
    """), {"id": uuid.uuid4(), "hash": key, "payload": canonical(payload), "provenance": canonical(provenance)}).scalar_one()
    if activate:
        connection.execute(text("SELECT pg_advisory_xact_lock(721603061)"))
        connection.execute(text("""
            INSERT INTO graphsync.ontology_source_activation(singleton,snapshot_id) VALUES (true,:id)
            ON CONFLICT(singleton) DO UPDATE SET previous_snapshot_id=ontology_source_activation.snapshot_id,
                snapshot_id=EXCLUDED.snapshot_id, activated_at=now()
            WHERE ontology_source_activation.snapshot_id <> EXCLUDED.snapshot_id
        """), {"id": row})
    return {"snapshotId": str(row), "contentHash": key, "activated": activate}


def validate_source(payload):
    names = [c["name"] for c in payload["classes"]]
    if len(names) != len(set(names)) or not names:
        raise ValueError("Source model requires unique, nonempty classes")
    known = set(names)
    keys = [(p["className"], p["name"]) for p in payload["properties"]]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate source property identity")
    if any(p["className"] not in known for p in payload["properties"]):
        raise ValueError("Property class is missing")
    if any(r["source"] not in known or r["target"] not in known for r in payload["relationships"]):
        raise ValueError("Relationship endpoint is missing")


def csv_model(tables_path, fields_path, selected=None):
    """Physical facts only; business semantics are never inferred as approved."""
    from scripts.validate_ontology_vs_csv import canonical_physical_fields, expected_type, normalize_field_name, is_system_field
    from src.ontology.physical_naming import relation_name
    def read(path):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    tables = read(tables_path)
    rows = read(fields_path)
    table_by_name = {r["CDOName"]: r for r in tables if r.get("CDOName")}
    names = set(selected) if selected else set(table_by_name)
    if names - table_by_name.keys():
        raise ValueError("Unknown CSV classes: " + ", ".join(sorted(names - table_by_name.keys())))
    grouped = {}
    for row in rows:
        if row["CDOName"] in names:
            grouped.setdefault(row["CDOName"], []).append(row)
    payload = {"classes": [], "properties": [], "relationships": []}
    for name in sorted(names):
        table = table_by_name[name]
        payload["classes"].append({"name": name, "chineseName": "", "description": table.get("Description", ""),
            "module": "csv", "layer": "Config", "sourceCDODefId": table.get("CDODefId"), "sourceWorkspace": "csv"})
        fields = canonical_physical_fields(grouped.get(name, []), name)
        for field in fields:
            if is_system_field(field, name):
                continue
            prop = normalize_field_name(field, name)
            payload["properties"].append({"className": name, "name": prop, "dataType": expected_type(field),
                "sourceFieldId": field.get("FieldID"), "physicalColumn": field["FieldName"],
                "required": False, "description": field.get("Description", ""), "origin": "csv"})
            if field.get("IsForeignKey") == "True" and field.get("FKTableName") in names:
                payload["relationships"].append({"source": name, "target": field["FKTableName"],
                    "name": relation_name(prop), "sourceProperty": prop, "sourceFieldId": field.get("FieldID"),
                    "physicalColumn": field["FieldName"], "targetColumn": field.get("FKFieldName"),
                    "cardinality": "many-to-one", "description": "CSV physical foreign key; business semantics require review"})
    validate_source(payload)
    return payload


def workspace(connection, key, *, lock=False):
    row = connection.execute(text("""
        SELECT w.*, d.graph FROM graphsync.ontology_workspace w
        JOIN graphsync.ontology_workspace_document d USING (workspace_id)
        WHERE w.workspace_key=:key
    """ + (" FOR UPDATE OF w, d" if lock else "")), {"key": key}).mappings().one_or_none()
    if row is None:
        raise RuntimeError("工作区未迁移到 PostgreSQL：" + key)
    return dict(row)


def edit_graph(repository, key, operation):
    with repository.engine.begin() as conn:
        row = workspace(conn, key, lock=True)
        if row["status"] == "retired":
            raise ValueError("Ontology workspace is retired")
        graph = deepcopy(row["graph"])
        result = operation(graph)
        conn.execute(text("UPDATE graphsync.ontology_workspace_document SET graph=CAST(:graph AS jsonb),updated_at=now() WHERE workspace_id=:id"),
                     {"id": row["workspace_id"], "graph": canonical(graph)})
        conn.execute(text("UPDATE graphsync.ontology_workspace SET status='draft',revision=revision+1,reviewed_by=NULL,reviewed_at=NULL,updated_at=now() WHERE workspace_id=:id"), {"id": row["workspace_id"]})
        return result


def frozen_graph(graph, release_id):
    classes = []
    by_uid = {}
    for node in graph["nodes"]:
        data = {**node["data"], "sourceUid": node["id"], "uid": f"{release_id}::{node['id']}", "releaseId": release_id}
        by_uid[node["id"]] = data
        props = [{**p, "sourceUid": p["uid"], "uid": f"{release_id}::{p['uid']}", "classUid": data["uid"], "releaseId": release_id}
                 for p in graph["properties"] if p["classUid"] == node["id"]]
        classes.append({"class": data, "properties": props})
    return {"classes": classes, "relationships": [{"source": by_uid[e["source"]], "target": by_uid[e["target"]],
        "relation": {**e["data"], "releaseId": release_id}} for e in graph["edges"]]}
