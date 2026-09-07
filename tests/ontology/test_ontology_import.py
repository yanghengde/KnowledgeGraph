import io
import json

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from web.routers import ontology_import


@pytest.fixture(autouse=True)
def isolate_description_storage(monkeypatch):
    monkeypatch.setattr(ontology_import, "load_descriptions", lambda database: {})
    monkeypatch.setattr(ontology_import, "save_descriptions", lambda database, rows: None)


TABLES = """CDODefId,CDOName,Workspace,
1,Product,csi,
2,NewBusinessObject,csi,
3,AuditHistoryDetail,csi,
"""

FIELDS = """CDODefId,CDOName,FieldID,FieldName,IsList,IsPrimaryKey,IsCandidateKey,IsForeignKey,FKCDODefId,FKTableName,FKFieldName,DataType,Precision,Scale,
1,Product,11,ProductName,False,True,False,False,0,,,12,255,0,
2,NewBusinessObject,21,ProductId,False,False,False,True,1,Product,ProductId,1,16,0,
3,AuditHistoryDetail,31,Description,False,False,False,False,0,,,12,255,0,
"""


def upload(name: str, value: str) -> UploadFile:
    return UploadFile(filename=name, file=io.BytesIO(value.encode("utf-8")))


def test_csv_analysis_preselects_curated_business_cdos(monkeypatch):
    monkeypatch.setattr(ontology_import, "_reviewed_class_names", lambda: {"Product"})
    monkeypatch.setattr(ontology_import, "_curated_business_class_names", lambda: {"Product", "NewBusinessObject"})
    monkeypatch.setattr("web.designer_metadata.load_cdo_description_catalog", lambda database: {
        "product": {"description": "A product."},
        "newbusinessobject": {"description": "A new business object."},
    })
    monkeypatch.setattr(ontology_import, "_load_description_cache", lambda: {
        "A product.": "中文：A product.",
        "A new business object.": "中文：A new business object.",
    })
    monkeypatch.setattr(ontology_import, "_start_description_job", lambda import_id: None)
    ontology_import._sessions.clear()

    result = ontology_import.analyze_import(upload("tables.csv", TABLES), upload("fields.csv", FIELDS), "sqlserver")
    candidates = {item["className"]: item for item in result["candidates"]}

    assert candidates["Product"]["status"] == "approved"
    assert candidates["Product"]["selected"] is True
    assert candidates["NewBusinessObject"]["status"] == "recommended"
    assert candidates["NewBusinessObject"]["selected"] is True
    assert candidates["AuditHistoryDetail"]["status"] == "excluded"
    assert candidates["AuditHistoryDetail"]["selected"] is False
    assert candidates["Product"]["descriptionEn"] == ""
    assert candidates["Product"]["descriptionZh"] == ""
    assert result["database"] == "sqlserver"
    assert result["summary"] == {
        "tables": 3,
        "fields": 3,
        "approved": 1,
        "recommended": 1,
        "review": 0,
        "excluded": 1,
        "defaultSelected": 2,
        "described": 0,
        "translated": 0,
    }
    ontology_import._run_description_job(result["importId"])
    descriptions = ontology_import.translation_status(result["importId"])
    assert descriptions["descriptions"]["Product"] == "A product."
    assert descriptions["translations"]["Product"] == "中文：A product."
    assert descriptions["translation"]["status"] == "completed"


def test_apply_import_stages_selected_objects_without_writing_neo4j(monkeypatch):
    monkeypatch.setattr(ontology_import, "_reviewed_class_names", lambda: {"Product"})
    monkeypatch.setattr(ontology_import, "_start_description_job", lambda import_id: None)
    ontology_import._sessions.clear()
    analysis = ontology_import.analyze_import(upload("tables.csv", TABLES), upload("fields.csv", FIELDS), "sqlserver")
    captured = []
    class Driver:
        def session(self): pytest.fail("CSV candidates must never directly write Neo4j")
    class Store:
        def stage(self, payload):
            captured.append(payload)
            return {"proposalId": "test-proposal", "alreadyAccepted": 0}
    monkeypatch.setattr("src.ontology.authority_store.authority_store", lambda: Store())
    monkeypatch.setattr(ontology_import, "_write_imported_ontology", lambda *a, **k: pytest.fail("Source files must remain unchanged"))
    result = ontology_import.apply_import(ontology_import.ImportApplyRequest(importId=analysis["importId"], selected=["NewBusinessObject"]))
    assert result["status"] == "pending_review"
    assert [c["className"] for c in captured[0]["classes"]] == ["NewBusinessObject"]
    assert captured[0]["relationships"][0]["toClass"] == "Product"


def test_description_translation_falls_back_to_english_without_provider(monkeypatch):
    monkeypatch.setenv("IMPORT_TRANSLATION_PROVIDER", "auto")
    monkeypatch.delenv("TRANSLATION_API_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    assert ontology_import._configured_translation_provider() == "none"


def test_a_prefix_uses_designer_base_description():
    catalog = {"joborder": {"description": "Designer description."}}
    assert ontology_import._designer_description_for("A_JobOrder", catalog) == "Designer description."


def test_database_description_failure_does_not_block_csv_review(monkeypatch):
    monkeypatch.setattr(ontology_import, "_reviewed_class_names", lambda: {"Product"})
    monkeypatch.setattr("web.designer_metadata.load_cdo_description_catalog", lambda database: (_ for _ in ()).throw(RuntimeError("offline")))
    monkeypatch.setattr(ontology_import, "_start_description_job", lambda import_id: None)

    result = ontology_import.analyze_import(upload("tables.csv", TABLES), upload("fields.csv", FIELDS), "oracle")
    ontology_import._run_description_job(result["importId"])
    status = ontology_import.translation_status(result["importId"])

    assert result["database"] == "oracle"
    assert result["summary"]["tables"] == 3
    assert "Oracle" in status["translation"]["warning"]
    assert status["translation"]["metadataStatus"] == "failed"
    assert all(not item["descriptionEn"] for item in result["candidates"])


def test_analysis_returns_before_uncached_translation(monkeypatch):
    monkeypatch.setattr(ontology_import, "_reviewed_class_names", lambda: {"Product"})
    monkeypatch.setattr("web.designer_metadata.load_cdo_description_catalog", lambda database: {
        "product": {"description": "A product."},
    })
    monkeypatch.setattr(ontology_import, "_configured_translation_provider", lambda: "api")
    started = []
    monkeypatch.setattr(ontology_import, "_start_description_job", lambda import_id: started.append(import_id))
    ontology_import._sessions.clear()

    result = ontology_import.analyze_import(upload("tables.csv", TABLES), upload("fields.csv", FIELDS), "sqlserver")

    assert result["translation"] == {
        "status": "waiting", "metadataStatus": "pending", "provider": "api", "total": 0, "completed": 0, "warning": "",
    }
    product = next(item for item in result["candidates"] if item["className"] == "Product")
    assert product["descriptionZh"] == ""
    assert started == [result["importId"]]


def test_background_translation_updates_progress_and_candidates(monkeypatch):
    session_id = "background-job"
    ontology_import._sessions.clear()
    ontology_import._sessions[session_id] = {
        "createdAt": 1e20,
        "database": "sqlserver",
        "candidates": {
            "Product": {"descriptionEn": "A product.", "descriptionZh": ""},
            "Factory": {"descriptionEn": "A factory.", "descriptionZh": ""},
        },
        "translation": {
            "status": "pending", "metadataStatus": "completed", "provider": "api", "total": 2, "completed": 0,
            "pending": ["A product.", "A factory."], "warning": "",
        },
    }
    monkeypatch.setattr(ontology_import, "_build_batch_translator", lambda provider: (
        lambda batch: [f"中文：{value}" for value in batch], 1,
    ))
    monkeypatch.setattr(ontology_import, "_load_description_cache", lambda: {})
    monkeypatch.setattr(ontology_import, "_save_description_cache", lambda cache: None)

    ontology_import._run_translation_job(session_id)
    result = ontology_import.translation_status(session_id)

    assert result["translation"]["status"] == "completed"
    assert result["translation"]["completed"] == 2
    assert result["translations"] == {"Product": "中文：A product.", "Factory": "中文：A factory."}








def test_first_import_after_clear_drops_stale_generated_classes(monkeypatch, tmp_path):
    generated = tmp_path / "csv_business_import_ontology.json"
    generated.write_text(json.dumps({
        "module": "csv_business_import",
        "classes": [{"className": "BadPreviousImport", "properties": []}],
        "relationships": [{
            "fromClass": "BadPreviousImport", "toClass": "Product",
            "relationName": "BAD_RELATION", "cardinality": "MANY_TO_ONE",
        }],
    }), encoding="utf-8")
    monkeypatch.setattr(ontology_import, "IMPORTED_ONTOLOGY", generated)

    ontology_import._write_imported_ontology(
        [{"className": "CleanImport", "properties": []}],
        [],
        allowed_class_names={"CleanImport"},
    )

    payload = json.loads(generated.read_text(encoding="utf-8"))
    assert [item["className"] for item in payload["classes"]] == ["CleanImport"]
    assert payload["relationships"] == []


def test_explorer_follows_incoming_and_outgoing_foreign_keys(monkeypatch):
    monkeypatch.setattr(ontology_import, "_reviewed_class_names", lambda: set())
    monkeypatch.setattr(ontology_import, "_start_description_job", lambda _: None)
    analysis = ontology_import.analyze_import(upload("tables.csv", TABLES), upload("fields.csv", FIELDS), "sqlserver")
    source = ontology_import.import_object(analysis["importId"], "NewBusinessObject")
    target = ontology_import.import_object(analysis["importId"], "Product")
    assert source["outgoing"] == target["incoming"]
    assert source["outgoing"][0]["source"] == "NewBusinessObject"
    assert source["outgoing"][0]["target"] == "Product"
    assert source["outgoing"][0]["fieldName"] == "ProductId"
    assert source["fields"][0]["type"] == "Navigation"
    assert target["candidate"]["incomingCount"] == 1
    assert target["outgoing"] == []
    with pytest.raises(HTTPException) as error:
        ontology_import.import_object(analysis["importId"], "Absent")
    assert error.value.status_code == 404


def test_explorer_preserves_multiple_edges_self_links_and_missing_targets(monkeypatch):
    monkeypatch.setattr(ontology_import, "_reviewed_class_names", lambda: set())
    monkeypatch.setattr(ontology_import, "_start_description_job", lambda _: None)
    extra = FIELDS + "2,NewBusinessObject,22,OtherProductId,False,False,False,True,1,Product,ProductId,1,16,0,\n" + "1,Product,12,ParentProductId,False,False,False,True,1,Product,ProductId,1,16,0,\n" + "1,Product,13,MissingId,False,False,False,True,9,Missing,Id,1,16,0,\n"
    analysis = ontology_import.analyze_import(upload("tables.csv", TABLES), upload("fields.csv", extra), "sqlserver")
    obj = ontology_import.import_object(analysis["importId"], "Product")
    assert len(obj["incoming"]) == 3
    assert len(obj["outgoing"]) == 2
    assert next(r for r in obj["outgoing"] if r["target"] == "Missing")["available"] is False


def test_english_is_saved_before_translation_and_both_languages_are_staged(monkeypatch):
    monkeypatch.setattr(ontology_import, "_reviewed_class_names", lambda: set())
    monkeypatch.setattr(ontology_import, "_start_description_job", lambda _: None)
    monkeypatch.setattr("web.designer_metadata.load_cdo_description_catalog", lambda _: {"product": {"description": "Original\nEnglish."}})
    monkeypatch.setattr(ontology_import, "_load_description_cache", lambda: {})
    monkeypatch.setattr(ontology_import, "_save_description_cache", lambda _: None)
    saved = []
    monkeypatch.setattr(ontology_import, "save_descriptions", lambda db, rows: saved.extend(dict(r) for r in rows))
    monkeypatch.setattr(ontology_import, "_configured_translation_provider", lambda: "api")
    def translate(batch):
        assert any(row.get("descriptionEn") == "Original\nEnglish." and row.get("descriptionZh") == "" for row in saved)
        return ["中文说明" for _ in batch]
    monkeypatch.setattr(ontology_import, "_build_batch_translator", lambda _: (translate, 10))
    analysis = ontology_import.analyze_import(upload("tables.csv", TABLES), upload("fields.csv", FIELDS), "sqlserver")
    ontology_import._run_description_job(analysis["importId"])
    captured = []
    from types import SimpleNamespace
    monkeypatch.setattr("src.ontology.authority_store.authority_store", lambda: SimpleNamespace(stage=lambda payload: captured.append(payload) or {}))
    ontology_import.apply_import(ontology_import.ImportApplyRequest(importId=analysis["importId"], selected=["Product"]))
    row = captured[0]["classes"][0]
    assert row["descriptionEn"] == "Original\nEnglish."
    assert row["descriptionZh"] == "中文说明"
    assert row["description"] == "中文说明"
    assert saved[-1]["descriptionZh"] == "中文说明"


def test_stored_translation_is_reused_in_new_import(monkeypatch):
    monkeypatch.setattr(ontology_import, "_reviewed_class_names", lambda: set())
    monkeypatch.setattr(ontology_import, "_start_description_job", lambda _: None)
    monkeypatch.setattr("web.designer_metadata.load_cdo_description_catalog", lambda _: {"product": {"description": "A product."}})
    monkeypatch.setattr(ontology_import, "_load_description_cache", lambda: {})
    monkeypatch.setattr(ontology_import, "load_descriptions", lambda _: {("Product", ""): {"descriptionEn": "A product.", "descriptionZh": "产品"}})
    monkeypatch.setattr(ontology_import, "_build_batch_translator", lambda _: pytest.fail("Persisted translations should be reused"))
    analysis = ontology_import.analyze_import(upload("tables.csv", TABLES), upload("fields.csv", FIELDS), "sqlserver")
    ontology_import._run_description_job(analysis["importId"])
    assert ontology_import.translation_status(analysis["importId"])["translations"]["Product"] == "产品"


def test_field_descriptions_are_persisted_and_used_in_candidate(monkeypatch):
    monkeypatch.setattr(ontology_import, "_reviewed_class_names", lambda: set())
    monkeypatch.setattr(ontology_import, "_start_description_job", lambda _: None)
    monkeypatch.setattr("web.designer_metadata.get_cdo_metadata", lambda *args: {
        "fields": {"productid": {"description": "Referenced product."}}})
    monkeypatch.setattr(ontology_import, "_load_description_cache", lambda: {})
    monkeypatch.setattr(ontology_import, "_save_description_cache", lambda _: None)
    monkeypatch.setattr(ontology_import, "_configured_translation_provider", lambda: "api")
    monkeypatch.setattr(ontology_import, "_build_batch_translator", lambda _: (lambda batch: ["产品名称" for _ in batch], 10))
    saved = []
    monkeypatch.setattr(ontology_import, "save_descriptions", lambda db, rows: saved.extend(dict(r) for r in rows))
    analysis = ontology_import.analyze_import(upload("tables.csv", TABLES), upload("fields.csv", FIELDS), "sqlserver")
    detail = ontology_import.enrich_object(analysis["importId"], "NewBusinessObject")
    assert detail["fields"][0]["descriptionEn"] == "Referenced product."
    assert detail["fields"][0]["descriptionZh"] == "产品名称"
    assert detail["fields"][0]["description"] == "产品名称"
    assert saved[0]["descriptionZh"] == ""
    assert saved[-1]["descriptionZh"] == "产品名称"
    assert saved[-1]["fieldName"] == "productid"


def test_source_outage_keeps_persisted_bilingual_descriptions(monkeypatch):
    monkeypatch.setattr(ontology_import, "_reviewed_class_names", lambda: set())
    monkeypatch.setattr(ontology_import, "_start_description_job", lambda _: None)
    monkeypatch.setattr(ontology_import, "load_descriptions", lambda _: {("Product", ""): {"descriptionEn": "Product", "descriptionZh": "saved translation"}})
    def offline(_):
        raise ConnectionError("source unavailable")
    monkeypatch.setattr("web.designer_metadata.load_cdo_description_catalog", offline)
    analysis = ontology_import.analyze_import(upload("tables.csv", TABLES), upload("fields.csv", FIELDS), "sqlserver")
    ontology_import._run_description_job(analysis["importId"])
    result = ontology_import.translation_status(analysis["importId"])
    assert result["descriptions"]["Product"] == "Product"
    assert result["translations"]["Product"] == "saved translation"
    assert result["translation"]["metadataStatus"] == "failed"
