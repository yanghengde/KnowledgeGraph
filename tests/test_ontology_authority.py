import copy
import json

import pytest
from fastapi import HTTPException

from src.ontology import authority as a
from web.routers import ontology_authority as api


@pytest.fixture
def library():
    def cls(kind, extra):
        return {"className": "Product", "chineseName": "产品", "description": "可制造的产品定义", "properties": [
            {"name": "materialCategory", "type": kind, "description": "物料类别"}, {"name": extra, "type": "String"}]}
    edge = {"fromClass": "Product", "toClass": "Category", "relationName": "HAS_CATEGORY", "cardinality": "MANY_TO_ONE"}
    return {"curated.json": {"classes": [cls("Navigation", "name")], "relationships": [edge]},
            "import.json": {"classes": [cls("String", "extension")], "relationships": [edge]}}


@pytest.fixture
def physical():
    return {"Product": [{"FieldName": "MaterialCategoryId", "IsForeignKey": "True", "FKTableName": "Category", "IsList": "False", "DataType": "1", "IsPrimaryKey": "False"}]}


def test_merge_requires_explicit_conflict_choice_and_keeps_extensions(library, physical):
    original = copy.deepcopy(library)
    detail = a.class_detail("Product", library, fields=physical)
    with pytest.raises(ValueError, match="明确选择"):
        a.merge_plan(detail, "curated.json", {}, "产品")
    plan = a.merge_plan(detail, "curated.json", {"materialCategory": "curated.json"}, "产品")
    assert not plan["blockers"]
    assert {p["name"] for p in plan["model"]["class"]["properties"]} == {"name", "extension", "materialCategory"}
    assert len(plan["model"]["relationships"]) == 1
    assert library == original
    bad = a.merge_plan(detail, "curated.json", {"materialCategory": "import.json"}, "产品")
    assert any("Navigation" in b for b in bad["blockers"])


def test_fingerprint_detects_source_and_physical_drift(library, physical):
    first = a.class_detail("Product", library, fields=physical)
    library["curated.json"]["classes"][0]["description"] += " changed"
    assert a.class_detail("Product", library, fields=physical)["fingerprint"] != first["fingerprint"]
    physical["Product"][0]["FKTableName"] = "Other"
    assert a.class_detail("Product", library, fields=physical)["fingerprint"] != first["fingerprint"]


def test_loader_view_replaces_duplicates_without_mutating_sources(library, physical):
    detail = a.class_detail("Product", library, fields=physical)
    plan = a.merge_plan(detail, "curated.json", {"materialCategory": "curated.json"}, "产品")
    docs = a.governed_documents(library, {"Product": {"model": plan["model"]}})
    classes = [c for d in docs.values() for c in d["classes"]]
    assert len(classes) == 1
    assert next(p for p in classes[0]["properties"] if p["name"] == "materialCategory")["type"] == "Navigation"
    assert len(library["import.json"]["classes"]) == 1


def test_merge_plan_hash_covers_business_definition(library, physical):
    detail = a.class_detail("Product", library, fields=physical)
    first = a.merge_plan(detail, "curated.json", {"materialCategory": "curated.json"}, "产品", description="一种产品")
    second = a.merge_plan(detail, "curated.json", {"materialCategory": "curated.json"}, "产品", description="另一种产品")
    assert first["planHash"] != second["planHash"]


def test_api_rejects_stale_review(library, physical, monkeypatch):
    detail = a.class_detail("Product", library, fields=physical)
    monkeypatch.setattr(api, "_detail", lambda *args: detail)
    with pytest.raises(HTTPException) as error:
        api.preview("Product", api.Decision(preferredSource="curated.json", domain="产品", fingerprint="0" * 64))
    assert error.value.status_code == 409


def test_new_candidate_without_physical_evidence_is_blocked():
    proposal = {"proposal_id": "p1", "payload": {"classes": [{"className": "Invented", "properties": []}], "relationships": []}}
    detail = a.class_detail("Invented", {}, proposals=[proposal], fields={})
    plan = a.merge_plan(detail, "candidate:p1", {}, "公共核心")
    assert len(plan["blockers"]) == 2


def test_directory_reports_source_changes_after_approval(library, physical, monkeypatch):
    monkeypatch.setattr(a, "physical_catalog", lambda: physical)
    detail = a.class_detail("Product", library, fields=physical)
    plan = a.merge_plan(detail, "curated.json", {"materialCategory": "curated.json"}, "产品")
    authority = {"Product": {"model": plan["model"], "revision": 1, "domain": "产品", "decision": plan, "synced_revision": 1}}
    assert a.directory(library, authority, [])["items"][0]["status"] == "synced"
    library["curated.json"]["classes"][0]["description"] = "变更"
    assert a.directory(library, authority, [])["items"][0]["status"] == "changed"


def test_live_library_core_merge_against_physical_facts():
    detail = a.class_detail("Product", a.read_library())
    choices = {c["property"]: next(k for k, p in c["variants"].items() if p["type"] == c["expectedType"]) for c in detail["conflicts"]}
    plan = a.merge_plan(detail, "product_ontology.json", choices, "产品与计量")
    assert not plan["blockers"]
    assert "materialCategory" in choices
    assert len(plan["model"]["class"]["properties"]) >= 158


def test_approval_requires_matching_preview_before_store(library, physical, monkeypatch):
    detail = a.class_detail("Product", library, fields=physical)
    class Conn:
        def execute(self, *args): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Store:
        engine = type("Engine", (), {"begin": lambda self: Conn()})()
        def save(self, *args): pytest.fail("No unreviewed plan may be persisted")
    monkeypatch.setattr(api, "_store", lambda: Store())
    monkeypatch.setattr(api, "_detail", lambda *args: detail)
    with pytest.raises(HTTPException) as error:
        api.approve("Product", api.Decision(preferredSource="curated.json", choices={"materialCategory": "curated.json"}, domain="产品", fingerprint=detail["fingerprint"]))
    assert error.value.status_code == 409


@pytest.mark.parametrize("missing", [True, False])
def test_sync_checks_targets_before_writes_and_marks_only_success(monkeypatch, missing):
    calls = []
    class Conn:
        def execute(self, statement, *args): calls.append(str(statement))
        def __enter__(self): return self
        def __exit__(self, *args): pass
    record = {"revision": 1, "domain": "产品", "model": {"class": {"className": "Product", "properties": []}, "relationships": [{"fromClass": "Product", "toClass": "Category", "relationName": "HAS_CATEGORY"}]}}
    class Store:
        engine = type("Engine", (), {"begin": lambda self: Conn()})()
        def snapshot(self, conn): return {"Product": record}, []
    class Result(list):
        def consume(self): pass
    class Session:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute_write(self, callback): callback(self)
        def run(self, query, **kwargs):
            if "RETURN c.name AS name" in query: return Result([] if missing else [{"name": "Category"}])
            calls.append("neo-write")
            return Result()
    monkeypatch.setattr(api, "_store", lambda: Store())
    monkeypatch.setattr("web.shared.driver", type("Driver", (), {"session": lambda self: Session()})())
    monkeypatch.setattr("web.routers.ontology_import._invalidate_graph_caches", lambda: None)
    if missing:
        with pytest.raises(HTTPException) as error:
            api.sync("Product", api.Revision(revision=1))
        assert error.value.status_code == 422
        assert "neo-write" not in calls
        assert not any("UPDATE graphsync" in c for c in calls)
    else:
        assert api.sync("Product", api.Revision(revision=1))["status"] == "synced"
        assert calls.count("neo-write") == 3
        assert "UPDATE graphsync" in calls[-1]


@pytest.mark.parametrize("fail", [True, False])
def test_bulk_loader_serializes_with_authority_reviews(monkeypatch, fail):
    from src.ontology.loader import neo4j_loader as loader
    calls = []
    class Conn:
        def execute(self, statement, *args): calls.append(str(statement))
        def __enter__(self): return self
        def __exit__(self, *args): pass
    records = {"Example": {"revision": 2}}
    class Store:
        engine = type("Engine", (), {"begin": lambda self: Conn()})()
        def snapshot(self, conn):
            assert "pg_advisory_xact_lock" in calls[0]
            return records, []
    def run(paths, clear, authorities):
        assert authorities is records
        if fail: raise RuntimeError("network interruption")
        return {"classes": 1}
    monkeypatch.setattr("src.ontology.authority_store.authority_store", lambda: Store())
    monkeypatch.setattr(loader, "_load_ontologies_to_neo4j", run)
    if fail:
        with pytest.raises(RuntimeError): loader.load_ontologies_to_neo4j([])
        assert len(calls) == 1
    else:
        assert loader.load_ontologies_to_neo4j([]) == {"classes": 1}
        assert "synced_revision" in calls[-1]
