"""Transactional control-plane metadata; source files and releases stay immutable."""
import json
import uuid
from functools import lru_cache

from sqlalchemy import text
from src.graphstudio_sync.config import SyncSettings
from src.graphstudio_sync.database import control_engine
from .authority import ROOT, digest


class AuthorityStore:
    def __init__(self, engine):
        self.engine = engine

    def initialize(self):
        with self.engine.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(721603050)"))
            connection.exec_driver_sql((ROOT / "sql/ontology_authority_postgres.sql").read_text(encoding="utf-8"))

    def snapshot(self, connection=None):
        if connection is None:
            with self.engine.connect() as conn:
                return self.snapshot(conn)
        authorities = {r["class_name"]: dict(r) for r in connection.execute(text("SELECT * FROM graphsync.ontology_authority ORDER BY class_name")).mappings()}
        proposals = []
        for row in connection.execute(text("SELECT * FROM graphsync.ontology_import_proposal ORDER BY created_at")).mappings():
            entry = dict(row)
            accepted = set(entry["accepted_classes"])
            entry["payload"] = {**entry["payload"],
                "classes": [c for c in entry["payload"]["classes"] if c["className"] not in accepted],
                "relationships": [r for r in entry["payload"].get("relationships", []) if r["fromClass"] not in accepted]}
            if entry["payload"]["classes"]:
                proposals.append(entry)
        return authorities, proposals

    def stage(self, payload):
        key = digest(payload)
        with self.engine.begin() as conn:
            conn.execute(text("SELECT pg_advisory_xact_lock(721603051)"))
            row = conn.execute(text("""
                INSERT INTO graphsync.ontology_import_proposal(proposal_id,content_hash,payload)
                VALUES (:id,:hash,CAST(:payload AS jsonb))
                ON CONFLICT(content_hash) DO UPDATE SET content_hash=EXCLUDED.content_hash
                RETURNING proposal_id,accepted_classes
            """), {"id": uuid.uuid4().hex, "hash": key, "payload": json.dumps(payload, ensure_ascii=False)}).mappings().one()
            return {"proposalId": row["proposal_id"], "alreadyAccepted": len(row["accepted_classes"])}

    def save(self, connection, plan):
        revision = plan["revision"] + 1
        snapshot = {"domain": plan["domain"], "model": plan["model"], "decision": {k:v for k,v in plan.items() if k != "model"}}
        connection.execute(text("""
            INSERT INTO graphsync.ontology_authority(class_name,revision,domain,model,decision)
            VALUES (:name,:revision,:domain,CAST(:model AS jsonb),CAST(:decision AS jsonb))
            ON CONFLICT(class_name) DO UPDATE SET revision=EXCLUDED.revision, domain=EXCLUDED.domain,
                model=EXCLUDED.model, decision=EXCLUDED.decision, updated_at=now()
        """), {"name": plan["className"], "revision": revision, "domain": plan["domain"],
                "model": json.dumps(plan["model"], ensure_ascii=False), "decision": json.dumps(snapshot["decision"], ensure_ascii=False)})
        connection.execute(text("INSERT INTO graphsync.ontology_authority_revision(class_name,revision,snapshot) VALUES (:name,:revision,CAST(:snapshot AS jsonb))"),
                           {"name": plan["className"], "revision": revision, "snapshot": json.dumps(snapshot, ensure_ascii=False)})
        for row in connection.execute(text("SELECT proposal_id,payload,accepted_classes FROM graphsync.ontology_import_proposal FOR UPDATE")).mappings():
            if any(c["className"] == plan["className"] for c in row["payload"]["classes"]):
                accepted = sorted(set(row["accepted_classes"]) | {plan["className"]})
                connection.execute(text("UPDATE graphsync.ontology_import_proposal SET accepted_classes=CAST(:accepted AS jsonb) WHERE proposal_id=:id"),
                                   {"id": row["proposal_id"], "accepted": json.dumps(accepted)})
        return {"revision": revision, "status": "approved"}

    def history(self, name):
        with self.engine.connect() as conn:
            return [dict(r) for r in conn.execute(text("SELECT revision, snapshot, created_at FROM graphsync.ontology_authority_revision WHERE class_name=:name ORDER BY revision DESC LIMIT 30"), {"name": name}).mappings()]


@lru_cache(maxsize=1)
def authority_store():
    store = AuthorityStore(control_engine(SyncSettings.from_env()))
    store.initialize()
    return store
