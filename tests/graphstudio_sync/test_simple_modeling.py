from copy import deepcopy
import pytest
from src.graphstudio_sync.modeling import simple_modeling as simple
from src.graphstudio_sync.modeling.semantic_mapping import source_fields
from src.ontology import authority


def fixture(monkeypatch):
    rows = [{"FieldName": name, "IsPrimaryKey": str(pk), "IsForeignKey": "False", "IsList": "False", "DataType": "12", "FieldID": name} for name, pk in [("ProductId", True), ("ProductName", False), ("Description", False)]]
    monkeypatch.setattr(authority, "physical_catalog", lambda: {"Product": rows})
    draft = {"draftId": "d", "snapshotId": "s", "tableName": "Product", "tableNames": ["Product"], "revision": 1, "fields": source_fields("Product", rows), "design": {"role": "entity", "chineseName": "产品", "description": "可制造的产品", "fields": {"productId": "internal", "name": "property", "description": "excluded"}}}
    workspace = {"workspace_key": "w", "workspace_id": "id", "revision": 1, "status": "draft", "graph": {"nodes": [], "edges": [], "properties": []}}
    source = {"classes": [{"name": "Other"}], "properties": [], "relationships": []}
    return draft, workspace, source


def test_simple_prepare_preserves_other_source_and_freezes_explicit_selection(monkeypatch):
    draft, workspace, source = fixture(monkeypatch)
    original = deepcopy((draft, workspace, source))
    plan = simple.prepare(draft, {}, {}, [], workspace, source)
    assert not plan["blockers"]
    assert plan["graph"]["nodes"][0]["data"]["role"] == "core"
    assert [p["sourceName"] for p in plan["graph"]["properties"]] == ["name"]
    assert plan["graph"]["properties"][0]["dataType"] == "String"
    assert {c["name"] for c in plan["source"]["classes"]} == {"Product", "Other"}
    assert (draft, workspace, source) == original
    workspace["revision"] = 2
    assert simple.prepare(draft, {}, {}, [], workspace, source)["planHash"] != plan["planHash"]


def test_simple_update_reports_removal_and_preserves_custom_fields(monkeypatch):
    draft, workspace, source = fixture(monkeypatch)
    first = simple.prepare(draft, {}, {}, [], workspace, source)
    workspace["graph"] = first["graph"]
    workspace["graph"]["properties"].append({"uid": "custom", "classUid": "w::Product", "sourceName": "custom", "targetName": "custom", "dataType": "String", "origin": "custom", "published": True})
    draft["design"]["fields"].update(name="excluded", description="property")
    updated = simple.prepare(draft, {}, {}, [], workspace, source)
    assert updated["removedFields"] == ["name"]
    assert {p["sourceName"] for p in updated["graph"]["properties"]} == {"custom", "description"}


def test_complex_mapping_cannot_commit(monkeypatch):
    draft, workspace, source = fixture(monkeypatch)
    draft["design"]["role"] = "event"
    prepared = simple.prepare(draft, {}, {}, [], workspace, source)
    with pytest.raises(ValueError):
        simple.commit(None, None, workspace, prepared)


def relationship_fixture(monkeypatch):
    draft, workspace, source = fixture(monkeypatch)
    rows = authority.physical_catalog()["Product"]
    for name in ("CategoryId", "BeginCategoryId"):
        rows.append({"FieldName": name, "IsPrimaryKey": "False", "IsForeignKey": "True",
                     "FKTableName": "Category", "FKFieldName": "CategoryId", "FieldID": name,
                     "DataType": "1", "IsList": "False"})
    draft["fields"] = source_fields("Product", rows)
    draft["tableNames"].append("Category")
    draft["design"]["fields"].update(category="relationship", beginCategory="relationship")
    workspace["graph"]["nodes"].append({"id": "w::Category", "data": {
        "sourceClass": "Category", "targetName": "Category", "role": "context"}})
    source["classes"].append({"name": "Category"})
    return draft, workspace, source


def test_same_target_relations_stay_distinct_and_preserve_reviewed_settings(monkeypatch):
    draft, workspace, source = relationship_fixture(monkeypatch)
    first = simple.prepare(draft, {}, {}, [], workspace, source)
    assert not first["blockers"]
    assert len(first["relationshipChanges"]) == 2
    assert {r["sourceField"] for r in first["relationshipChanges"]} == {"CategoryId", "BeginCategoryId"}
    assert all(r["change"] == "added" for r in first["relationshipChanges"])
    workspace["graph"] = first["graph"]
    edge = workspace["graph"]["edges"][0]
    edge["data"].update(targetName="REVIEWED_CATEGORY", description="已确认业务含义",
                         requiredContext=True, questionEnabled=False, cardinality="one-to-one")
    original = deepcopy(workspace["graph"]["edges"])
    updated = simple.prepare(draft, {}, {}, [], workspace, source)
    assert updated["graph"]["edges"] == original
    assert all(r["change"] == "retained" for r in updated["relationshipChanges"])
    draft["design"]["fields"]["category"] = "excluded"
    removed = simple.prepare(draft, {}, {}, [], workspace, source)
    changes = {r["sourceField"]: r["change"] for r in removed["relationshipChanges"]}
    assert changes == {"CategoryId": "removed", "BeginCategoryId": "retained"}
    assert len(removed["graph"]["edges"]) == 1
    assert removed["planHash"] != updated["planHash"]


@pytest.mark.parametrize("patch", [{"role": "excluded"}, {"published": False}])
def test_selected_relationship_to_excluded_target_blocks_commit(monkeypatch, patch):
    draft, workspace, source = relationship_fixture(monkeypatch)
    workspace["graph"]["nodes"][0]["data"].update(patch)
    prepared = simple.prepare(draft, {}, {}, [], workspace, source)
    assert any("Category" in message for message in prepared["blockers"])
    assert all(not r["targetAvailable"] for r in prepared["relationshipChanges"])
    with pytest.raises(ValueError):
        simple.commit(None, None, workspace, prepared)
