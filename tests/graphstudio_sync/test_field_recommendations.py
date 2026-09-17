import copy
import csv
import json
from pathlib import Path

import pytest

from src.graphstudio_sync.modeling.field_recommendations import recommend_fields
from src.graphstudio_sync.modeling.field_recommendations import suggested_fields
from src.graphstudio_sync.storage.ontology_store import digest
from src.graphstudio_sync.modeling.semantic_mapping import MappingStore
from src.graphstudio_sync.modeling.semantic_mapping import candidate_preview
from src.graphstudio_sync.modeling.semantic_mapping import source_fields


def row(name, *, primary=False, target="", datatype="12", is_list=False):
    return {"FieldName": name, "FieldID": name, "IsPrimaryKey": str(primary),
            "IsForeignKey": str(bool(target)), "FKTableName": target,
            "FKFieldName": "Id" if target else "", "DataType": datatype,
            "IsList": str(is_list)}


def test_recommendations_use_physical_fk_evidence_and_do_not_select_links():
    fields = source_fields("WorkflowStep", [
        row("WorkflowStepId", primary=True), row("WorkflowStepName"), row("Sequence"),
        row("WorkflowId"), row("SpecId", target="Spec"),
        row("EmailGroupId", target="A_EmailGroup"), row("IconId"), row("ChangeCount"),
        row("CustomValue"), row("Attachment", datatype="-4"),
    ])
    original = copy.deepcopy(fields)
    recommendations = recommend_fields("WorkflowStep", fields)
    assert recommendations["workflowStepId"]["role"] == "internal"
    assert recommendations["name"]["autoSelect"]
    assert recommendations["sequence"]["autoSelect"]
    assert recommendations["spec"]["role"] == "relationship"
    assert "Spec" in recommendations["spec"]["reason"]
    assert not recommendations["spec"]["autoSelect"]
    for name in ("workflowId", "emailGroup", "iconId", "changeCount", "customValue", "attachment"):
        assert not recommendations[name]["autoSelect"]
    assert recommendations["workflowId"]["role"] == "pending"
    assert fields == original


def test_list_binary_and_unknown_types_are_not_recommended_even_with_business_names():
    for options in ({"is_list": True}, {"datatype": "-4"}, {"datatype": "999"}):
        fields = source_fields("Product", [row("ProductName", **options)])
        assert not recommend_fields("Product", fields)["name"]["autoSelect"]
    fields = source_fields("OtherTable", [row("Sequence")])
    assert not recommend_fields("OtherTable", fields)["sequence"]["autoSelect"]


def test_business_target_does_not_recommend_all_historical_or_configuration_links():
    fields = source_fields("Container", [row("ProductId", target="Product"),
        row("PlannedProductId", target="Product"), row("SSMoveOutFromSpecId", target="Spec"),
        row("ParentContainerId", target="Container")])
    recommendations = recommend_fields("Container", fields)
    assert recommendations["product"]["role"] == "relationship"
    assert recommendations["parentContainer"]["role"] == "relationship"
    assert recommendations["plannedProduct"]["role"] == "pending"
    assert recommendations["ssMoveOutFromSpec"]["role"] == "pending"


@pytest.mark.parametrize("saved_role", ["property", "relationship", "internal", "excluded"])
def test_existing_choices_override_all_new_recommendations(saved_role):
    design = {"role": "entity", "fields": {"name": saved_role, "description": "pending"}}
    recommendations = {name: {"role": "property", "autoSelect": True}
                       for name in ("name", "description")}
    original = copy.deepcopy(design)
    suggested = suggested_fields(design, recommendations)
    assert suggested == {"name": saved_role, "description": "property"}
    assert design == original


@pytest.mark.parametrize("source_role", ["event", "relationship", "auxiliary", "excluded"])
def test_complex_sources_are_not_silently_converted(source_role):
    design = {"role": source_role, "fields": {"name": "pending"}}
    assert suggested_fields(design, {"name": {"role": "property", "autoSelect": True}}) == design["fields"]


class Connection:
    def __init__(self):
        payload = {"tables": {"Product": {}}, "fields": {"Product": [
            row("ProductId", primary=True), row("ProductName"), row("Description"), row("ChangeCount"),
        ]}}
        fields = source_fields("Product", payload["fields"]["Product"])
        self.row = {"draft_id": "test", "snapshot_id": digest(payload), "table_name": "Product",
                    "revision": 1, "payload": payload,
                    "design": {"role": "entity", "chineseName": "产品", "description": "制造产品",
                               "fields": {f["name"]: "internal" if f["primaryKey"] else "pending" for f in fields}}}
        self.writes = 0

    def __enter__(self): return self
    def __exit__(self, *args): pass
    def mappings(self): return self
    def one_or_none(self): return copy.deepcopy(self.row)

    def execute(self, statement, params):
        sql = str(statement)
        if sql.startswith("UPDATE graphsync.semantic_mapping_draft"):
            self.row["design"] = json.loads(params["design"])
            self.row["revision"] += 1
            self.writes += 1
        else:
            assert sql.startswith("SELECT d.*")
        return self


def test_read_suggests_without_writing_and_save_reload_preserves_deselection():
    conn = Connection()
    engine = type("Engine", (), {"connect": lambda self: conn, "begin": lambda self: conn})()
    store = MappingStore(engine)
    detail = store.detail("test")
    assert conn.writes == 0
    assert detail["design"]["fields"]["name"] == "pending"
    assert detail["suggestedFields"]["name"] == "property"
    assert detail["suggestedFields"]["changeCount"] == "pending"
    # Merely receiving suggestions does not approve or change a preview.
    assert candidate_preview(detail)["blockers"]
    without_hints = {k: v for k, v in detail.items() if k not in {"recommendations", "suggestedFields"}}
    assert candidate_preview(detail) == candidate_preview(without_hints)
    design = {**detail["design"], "fields": {**detail["suggestedFields"], "name": "excluded", "changeCount": "excluded"}}
    saved = store.save("test", 1, design)
    assert saved["suggestedFields"]["name"] == "excluded"
    assert store.detail("test")["suggestedFields"]["name"] == "excluded"
    with pytest.raises(RuntimeError, match="草稿已被修改"):
        store.save("test", 1, design)
    assert conn.writes == 1
    preview = candidate_preview(saved)
    assert not preview["blockers"]
    assert [p["name"] for p in preview["payload"]["classes"][0]["properties"]] == ["description"]
    assert preview["payload"]["relationships"] == []


def test_real_workflow_step_catalog_keeps_layout_out_and_fk_suggestions_explicit():
    path = Path(__file__).resolve().parents[2] / "docs" / "Database_Fields.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["CDOName"] == "WorkflowStep"]
    fields = source_fields("WorkflowStep", rows)
    recommendations = recommend_fields("WorkflowStep", fields)
    by_physical = {f["physicalName"]: recommendations[f["name"]] for f in fields}
    assert by_physical["WorkflowStepName"]["autoSelect"]
    assert by_physical["WorkflowStepId"]["role"] == "internal"
    for name in ("IconId", "Xlocation", "Ylocation", "WorkflowId"):
        assert not by_physical[name]["autoSelect"]
    assert by_physical["SpecId"]["role"] == "relationship"
    assert not by_physical["SpecId"]["autoSelect"]
