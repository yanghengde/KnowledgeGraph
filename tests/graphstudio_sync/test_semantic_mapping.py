import copy

import pytest
from fastapi import HTTPException

from src.graphstudio_sync.modeling.semantic_mapping import source_fields
from src.graphstudio_sync.modeling.semantic_mapping import candidate_preview
from src.graphstudio_sync.modeling.semantic_mapping import validate_design
from src.graphstudio_sync.modeling.physical_model import physical_fields
from src.ontology import authority
from web.routers import semantic_mapping as api


def row(name, *, primary=False, target=""):
    return {"FieldName": name, "IsPrimaryKey": str(primary), "IsForeignKey": str(bool(target)),
            "FKTableName": target, "FKFieldName": "CategoryId" if target else "", "FieldID": name,
            "DataType": "1" if primary or target else "12", "IsList": "False"}


@pytest.fixture
def draft():
    fields = source_fields("Product", [row("ProductId", primary=True), row("ProductName"), row("ChangeCount"), row("CategoryId", target="Category")])
    return {"draftId": "d1", "snapshotId": "s1", "revision": 2, "tableName": "Product", "tableNames": ["Product", "Category"],
            "fields": fields, "design": {"role": "entity", "chineseName": "产品", "description": "制造产品", "notes": "",
                                         "fields": {"productId": "internal", "name": "property", "changeCount": "excluded", "category": "relationship"}}}


def test_physical_view_retains_identity_technical_fields_and_foreign_keys():
    rows = [row("ProductId", primary=True), row("ChangeCount"), row("CategoryId"), row("CategoryId", target="Category")]
    original = copy.deepcopy(rows)
    fields = source_fields("Product", rows)
    assert len(fields) == 3
    assert fields[0]["primaryKey"]
    assert fields[-1]["type"] == "Navigation"
    assert fields[-1]["target"] == "Category"
    assert len(physical_fields(rows)) == 3
    assert rows == original


def test_entity_preview_explicitly_projects_only_business_fields(draft):
    original = copy.deepcopy(draft)
    plan = candidate_preview(draft)
    assert plan["blockers"] == []
    assert plan["counts"] == {"properties": 1, "relationships": 1, "internal": 1, "excluded": 1}
    cls = plan["payload"]["classes"][0]
    assert {p["name"] for p in cls["properties"]} == {"name", "category"}
    assert cls["_semanticMapping"]["identityColumns"] == ["ProductId"]
    assert plan["payload"]["relationships"][0]["physicalColumn"] == "CategoryId"
    draft["design"]["fields"]["category"] = "internal"
    updated = candidate_preview(draft)
    assert updated["payload"]["relationships"] == []
    assert updated["planHash"] != plan["planHash"]
    assert original["design"]["fields"]["category"] == "relationship"


@pytest.mark.parametrize("role", ["pending", "event", "relationship", "auxiliary", "excluded"])
def test_complex_or_unassessed_source_never_becomes_entity(draft, role):
    draft["design"]["role"] = role
    assert candidate_preview(draft)["blockers"]


def test_unknown_fields_removed_identity_and_scalar_relationship_rejected(draft):
    for name, role in [("missing", "property"), ("productId", "excluded"), ("name", "relationship"), ("category", "property")]:
        design = copy.deepcopy(draft["design"])
        design["fields"][name] = role
        with pytest.raises(ValueError):
            validate_design(design, draft["fields"])


def test_pending_fields_missing_identity_and_missing_targets_block_preview(draft):
    draft["design"]["fields"]["name"] = "pending"
    draft["fields"][0]["primaryKey"] = False
    draft["tableNames"] = ["Product"]
    assert len(candidate_preview(draft)["blockers"]) == 3


def test_mapping_allowlist_survives_source_merge_and_reports_removals(draft):
    payload = candidate_preview(draft)["payload"]
    previous = {"className": "Product", "properties": [{"name": "name", "type": "String"}, {"name": "secret", "type": "String"}]}
    docs = {"old": {"classes": [previous], "relationships": [{"fromClass": "Product", "toClass": "Unwanted", "relationName": "HAS_OTHER"}]}}
    physical = {"Product": [row("ProductId", primary=True), row("ProductName"), row("ChangeCount"), row("CategoryId", target="Category")]}
    approved = {"model": {"class": previous, "relationships": docs["old"]["relationships"]}, "revision": 1}
    detail = authority.class_detail("Product", docs, approved, [{"proposal_id": "p", "payload": payload}], fields=physical)
    plan = authority.merge_plan(detail, "candidate:p", {}, "产品")
    assert not plan["blockers"]
    assert {p["name"] for p in plan["model"]["class"]["properties"]} == {"name", "category"}
    assert len(plan["model"]["relationships"]) == 1
    assert {"property": "secret", "before": previous["properties"][1], "after": None} in plan["changes"]
    approved["model"] = plan["model"]
    detail = authority.class_detail("Product", docs, approved, fields=physical)
    assert {p["name"] for p in authority.merge_plan(detail, "approved", {}, "产品")["model"]["class"]["properties"]} == {"name", "category"}
    physical["Product"][0]["FieldName"] = "ChangedIdentity"
    detail = authority.class_detail("Product", docs, approved, fields=physical)
    assert any("物理结构不一致" in b for b in authority.merge_plan(detail, "approved", {}, "产品")["blockers"])


def test_submit_rejects_stale_preview_and_event_design(draft, monkeypatch):
    class Conn:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Store:
        engine = type("Engine", (), {"begin": lambda self: Conn()})()
        def detail(self, *args, **kwargs): return draft
    monkeypatch.setattr(api, "_store", lambda: Store())
    monkeypatch.setattr(api, "authority_store", lambda: pytest.fail("Blocked draft must not be staged"))
    with pytest.raises(HTTPException) as error:
        api.submit("d1", api.SubmitRequest(revision=1, planHash="0" * 64))
    assert error.value.status_code == 409
    draft["design"]["role"] = "event"
    with pytest.raises(HTTPException) as error:
        api.submit("d1", api.SubmitRequest(revision=2, planHash=candidate_preview(draft)["planHash"]))
    assert error.value.status_code == 422


def test_mapping_provenance_is_frozen_and_excluded_fields_cannot_be_republished(draft):
    from src.graphstudio_sync.publishing.publish_ontology_postgres import _add_class
    from src.graphstudio_sync.publishing.publish_ontology import validate_graph
    from src.graphstudio_sync.storage.ontology_store import frozen_graph
    cls = candidate_preview(draft)["payload"]["classes"][0]
    graph = {"nodes": [], "edges": [], "properties": []}
    _add_class(graph, "test", {"class": {**cls, "name": "Product"}, "properties": cls["properties"]}, "Product", "core", "quarantine")
    frozen = frozen_graph(graph, "release-test")
    assert frozen["classes"][0]["class"]["_semanticMapping"] == cls["_semanticMapping"]
    graph["properties"].append({"classUid": "test::Product", "uid": "test::Product::changeCount", "sourceName": "changeCount", "targetName": "changeCount", "dataType": "Integer", "published": True})
    result = validate_graph({"workspace_key": "test", "revision": 1}, graph)
    assert any(e["code"] == "property.excluded_by_mapping" for e in result["errors"])


def test_delete_draft_checks_revision_and_preserves_design():
    import json
    from src.graphstudio_sync.modeling.semantic_mapping import MappingStore
    class Connection:
        def __init__(self):
            self.row = {"revision": 3, "design": {"role": "entity", "fields": {"name": "property"}}}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, sql, params):
            if str(sql).startswith("UPDATE"):
                self.row["design"] = json.loads(params["design"])
                self.row["revision"] += 1
            return self
        def mappings(self): return self
        def one_or_none(self): return self.row
    conn = Connection()
    store = MappingStore(type("Engine", (), {"begin": lambda self: conn})())
    with pytest.raises(RuntimeError):
        store.set_deleted("draft", 2, True)
    assert "deleted" not in conn.row["design"]
    store.set_deleted("draft", 3, True)
    assert conn.row["design"]["deleted"] is True
    assert conn.row["design"]["fields"] == {"name": "property"}
    store.set_deleted("draft", 4, False)
    assert conn.row["design"]["deleted"] is False
