import io
import json

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from web.routers import ontology_import


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
