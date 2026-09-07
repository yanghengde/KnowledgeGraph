"""Configuration guardrails and an opt-in transaction test in an isolated schema."""
import os
import uuid

import pytest
from sqlalchemy import event, text

from src.graphstudio_sync import sync_configuration as configuration


def test_configuration_requires_keys_and_foreign_keys():
    plan = {"className": "Spec", "blockers": [], "primaryKeys": ["Id"], "businessKeys": [],
            "fields": [{"physical_column": "Id", "required": True}, {"physical_column": "OperationId", "required": False}],
            "relationships": [{"source": "Spec", "column": "OperationId"}]}
    with pytest.raises(ValueError, match="关系外键"):
        configuration.validate_selection(plan, "data", ["Id"])
    with pytest.raises(ValueError, match="未知字段"):
        configuration.validate_selection(plan, "data", ["Id", "OperationId", "unknown"])
    configuration.validate_selection(plan, "data", ["Id", "OperationId"])


def test_model_only_does_not_require_physical_mapping_but_preserves_existing_contract():
    plan = {"modelOnlyAllowed": True, "blockers": ["missing mapping"]}
    configuration.validate_selection(plan, "model_only", [])
    with pytest.raises(ValueError, match="missing mapping"):
        configuration.validate_selection(plan, "data", [])
    plan["modelOnlyAllowed"] = False
    with pytest.raises(ValueError, match="已有数据契约"):
        configuration.validate_selection(plan, "model_only", [])


@pytest.mark.skipif(os.getenv("RUN_SYNC_CONFIG_PG_TESTS") != "1", reason="requires PostgreSQL metadata fixture")
def test_configuration_atomic_save_retry_and_rollback(monkeypatch):
    from src.graphstudio_sync.config import SyncSettings
    from src.graphstudio_sync.repository import ControlPlaneRepository
    from src.graphstudio_sync.ontology_store import digest
    repo = ControlPlaneRepository(SyncSettings.from_env())
    engine = repo.engine
    schema = "sync_config_test_" + uuid.uuid4().hex
    # Copy metadata only. No source business rows, credentials, or live mutations.
    tables = ["graph_profile", "profile_class", "profile_relationship", "data_contract", "data_contract_field",
              "relationship_contract", "table_sync_policy", "ontology_release_activation", "ontology_release_document", "curation_run"]
    views = ["current_class_mapping", "current_property_mapping", "current_relationship_mapping"]
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
            for table in tables:
                conn.exec_driver_sql(f'CREATE TABLE "{schema}".{table} (LIKE graphsync.{table} INCLUDING ALL)')
                if table != "curation_run":
                    conn.exec_driver_sql(f'INSERT INTO "{schema}".{table} SELECT * FROM graphsync.{table}')
            for view in views:
                conn.exec_driver_sql(f'CREATE TABLE "{schema}".{view} AS SELECT * FROM graphsync.{view}')
        def rewrite(conn, cursor, statement, parameters, context, executemany):
            return statement.replace("graphsync.", schema + "."), parameters
        event.listen(engine, "before_cursor_execute", rewrite, retval=True)
        profile = "opcenter2607-core"
        graph = {"classes": [{"class": {"sourceClass": n, "targetName": n, "role": "context"}, "properties": []} for n in ["Spec", "Operation"]],
                 "relationships": [{"source": {"sourceClass": "Spec"}, "target": {"sourceClass": "Operation"}, "relation": {"targetName": "HAS_OPERATION"}}]}
        import json
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM graphsync.relationship_contract WHERE source_contract_key IN (SELECT contract_key FROM graphsync.data_contract WHERE class_name='Operation') OR target_contract_key IN (SELECT contract_key FROM graphsync.data_contract WHERE class_name='Operation')"))
            conn.execute(text("DELETE FROM graphsync.data_contract_field WHERE contract_key IN (SELECT contract_key FROM graphsync.data_contract WHERE class_name='Operation')"))
            conn.execute(text("DELETE FROM graphsync.data_contract WHERE class_name='Operation'"))
            conn.execute(text("DELETE FROM graphsync.profile_class WHERE class_name='Operation'"))
            conn.execute(text("DELETE FROM graphsync.profile_relationship WHERE source_class='Operation' OR target_class='Operation'"))
            conn.execute(text("DELETE FROM graphsync.table_sync_policy WHERE class_name='Operation'"))
            conn.execute(text("UPDATE graphsync.ontology_release_document SET graph=CAST(:graph AS jsonb),document_hash=:hash WHERE ontology_release_id=(SELECT active_release_id FROM graphsync.ontology_release_activation WHERE profile_key=:profile)"),
                         {"graph": json.dumps(graph), "hash": digest(graph), "profile": profile})
        plan = configuration.configuration_preview(repo, profile, "Operation")
        assert not plan["blockers"]
        assert plan["primaryKeys"] == ["OperationId"]
        configuration.save_configuration(repo, profile, "Operation", mode="model_only", selected_columns=[],
                                         fingerprint=plan["fingerprint"], actor="test")
        plan = configuration.configuration_preview(repo, profile, "Operation")
        assert plan["currentMode"] == "model_only" and not plan["hasContract"]
        arguments = dict(mode="data", selected_columns=[f["physical_column"] for f in plan["fields"]], fingerprint=plan["fingerprint"], actor="test")
        original = ControlPlaneRepository.upsert_table_policy
        def fail(*args, **kwargs):
            raise RuntimeError("injected policy failure")
        monkeypatch.setattr(ControlPlaneRepository, "upsert_table_policy", fail)
        with pytest.raises(RuntimeError, match="injected"):
            configuration.save_configuration(repo, profile, "Operation", **arguments)
        assert configuration.configuration_preview(repo, profile, "Operation")["fingerprint"] == plan["fingerprint"]
        monkeypatch.setattr(ControlPlaneRepository, "upsert_table_policy", original)
        configuration.save_configuration(repo, profile, "Operation", **arguments)
        with pytest.raises(ValueError, match="已变化"):
            configuration.save_configuration(repo, profile, "Operation", **arguments)
        governance = repo.governance_profile(profile)
        assert next(c for c in governance["contracts"] if c["class_name"] == "Operation")["status"] == "approved"
        relation = next(r for r in governance["relationships"] if r["source_class"] == "Spec" and r["target_class"] == "Operation")
        assert relation["source_columns"] == ["OperationId"] and relation["status"] == "approved"
    finally:
        if "rewrite" in locals():
            event.remove(engine, "before_cursor_execute", rewrite)
        with engine.begin() as conn:
            conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        engine.dispose()
