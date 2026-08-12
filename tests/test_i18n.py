import json
import sys
from pathlib import Path

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web.routers import i18n


def test_catalog_exposes_all_ontology_display_names(monkeypatch):
    catalog = i18n._ontology_catalog()

    assert len(catalog["node"]) >= 500
    assert len(catalog["property"]) >= 8_000
    assert "relationship" not in catalog
    assert any(item["key"] == "Workflow" and item["descriptionZh"] for item in catalog["node"])
    assert any(item["key"] == "Workflow.revision" for item in catalog["property"])
    assert any(item["key"] == "Workflow.revision" for item in catalog["propertiesByNode"]["Workflow"])
    graph_nodes = [
        {"key": "OtherWorkflow", "original": "OtherWorkflow", "owner": "test", "chineseName": "", "descriptionZh": "", "descriptionEn": "", "propertyCount": 0},
        {"key": "Workflow", "original": "Workflow", "owner": "test", "chineseName": "工作流", "descriptionZh": "", "descriptionEn": "", "propertyCount": 1},
    ]
    monkeypatch.setattr(i18n, "_graph_catalog_snapshot", lambda: (graph_nodes, {}))
    search_result = i18n.get_translation_catalog(search="Workflow", offset=0, limit=5)
    assert search_result["items"][0]["key"] == "Workflow"


def test_translation_override_is_persisted_atomically(tmp_path, monkeypatch):
    translation_file = tmp_path / "display_translations.json"
    monkeypatch.setattr(i18n, "I18N_DIR", str(tmp_path))
    monkeypatch.setattr(i18n, "TRANSLATIONS_FILE", str(translation_file))

    result = i18n.update_translation(i18n.TranslationUpdate(
        kind="property_description",
        key="Workflow.revision",
        zh="修订版本字段说明",
        en="Revision field description",
    ))

    assert result["success"] is True
    assert result["revision"] == 1
    saved = json.loads(translation_file.read_text(encoding="utf-8"))
    assert saved["translations"]["propertyDescriptions"]["Workflow.revision"] == {
        "zh": "修订版本字段说明",
        "en": "Revision field description",
    }

    description_result = i18n.update_translation(i18n.TranslationUpdate(
        kind="node_description",
        key="Workflow",
        zh="用于定义制造流程。",
        en="Defines the manufacturing process.",
    ))
    assert description_result["revision"] == 2
    saved = json.loads(translation_file.read_text(encoding="utf-8"))
    assert saved["translations"]["nodeDescriptions"]["Workflow"]["en"] == "Defines the manufacturing process."


def test_identifier_defaults_are_readable():
    assert i18n._default_zh("changeHistory") == "变更历史"
    assert i18n._default_zh("HAS_ACTION_CATEGORY") == "包含操作类别"
    assert i18n._default_en("HAS_ACTION_CATEGORY") == "Has Action Category"
    assert i18n._default_en("changeHistoryId") == "Change History ID"


def test_node_editor_uses_exact_graph_detail_properties(tmp_path, monkeypatch):
    monkeypatch.setattr(i18n, "I18N_DIR", str(tmp_path))
    monkeypatch.setattr(i18n, "TRANSLATIONS_FILE", str(tmp_path / "display_translations.json"))
    graph_node = {
        "key": "MfgOrder", "original": "MfgOrder", "owner": "mfgorder",
        "chineseName": "制造工单", "descriptionZh": "制造工单描述", "descriptionEn": "", "propertyCount": 2,
    }
    graph_details = {
        "MfgOrder": {
            "properties": [
                {"name": "beginProduct", "dataType": "Navigation", "description": "初始产品"},
                {"name": "consumingOrder", "dataType": "String", "description": "父级消耗工单"},
            ]
        }
    }
    monkeypatch.setattr(i18n, "_graph_catalog_snapshot", lambda: ([graph_node], graph_details))

    editor = i18n.get_node_translation_editor("MfgOrder")

    assert [item["original"] for item in editor["properties"]] == ["beginProduct", "consumingOrder"]
    assert editor["properties"][0]["dataType"] == "Navigation"
    assert editor["properties"][0]["sourceDescription"] == "初始产品"
    assert editor["properties"][0]["descriptionZh"] == "初始产品"
    assert editor["properties"][0]["descriptionEn"] == ""


def test_camstar_description_sync_preserves_manual_edits(monkeypatch, tmp_path):
    translation_file = tmp_path / "display_translations.json"
    monkeypatch.setattr(i18n, "I18N_DIR", str(tmp_path))
    monkeypatch.setattr(i18n, "TRANSLATIONS_FILE", str(translation_file))
    graph_node = {
        "kind": "node", "key": "Product", "owner": "product", "original": "Product",
        "chineseName": "产品", "descriptionZh": "", "descriptionEn": "", "propertyCount": 2,
    }
    graph_details = {"Product": {"properties": [
        {"name": "name", "dataType": "String", "description": ""},
        {"name": "description", "dataType": "String", "description": ""},
    ]}}
    monkeypatch.setattr(i18n, "_graph_catalog_snapshot", lambda: ([graph_node], graph_details))
    monkeypatch.setattr(i18n, "_physical_field_names", lambda _: {"name": "ProductName", "description": "Description"})
    monkeypatch.setattr(i18n, "_designer_descriptions", lambda _, database: {
        "cdoDefId": "10", "cdoName": "Product", "description": "A manufactured product.",
        "fields": {
            "productname": {"fieldId": "1", "description": "Name of the product."},
            "description": {"fieldId": "2", "description": "Description of the product."},
        },
    })
    monkeypatch.setattr(i18n, "_translate_descriptions", lambda values: {value: f"中文：{value}" for value in values})
    store = i18n._empty_store()
    store["translations"]["propertyDescriptions"]["Product.description"] = {"zh": "人工中文", "en": "Manual English"}
    store["manualEdits"]["propertyDescriptions"]["Product.description"] = 1
    i18n._save_store(store)

    result = i18n.sync_descriptions(i18n.DescriptionSyncRequest(className="Product", database="sqlserver"))
    saved = i18n._load_store()

    assert result["matched"] == 3
    assert result["updated"] == 2
    assert result["manualPreserved"] == 1
    assert result["database"] == "sqlserver"
    assert saved["translations"]["nodeDescriptions"]["Product"]["en"] == "A manufactured product."
    assert saved["translations"]["propertyDescriptions"]["Product.description"]["zh"] == "人工中文"


def test_description_sync_keeps_english_when_translation_is_offline(monkeypatch, tmp_path):
    monkeypatch.setattr(i18n, "I18N_DIR", str(tmp_path))
    monkeypatch.setattr(i18n, "TRANSLATIONS_FILE", str(tmp_path / "display_translations.json"))
    graph_node = {"key": "Product", "original": "Product", "owner": "product", "descriptionZh": "", "descriptionEn": "", "propertyCount": 0}
    monkeypatch.setattr(i18n, "_graph_catalog_snapshot", lambda: ([graph_node], {"Product": {"properties": []}}))
    monkeypatch.setattr(i18n, "_designer_descriptions", lambda _, database: {
        "cdoDefId": "10", "cdoName": "Product", "description": "A manufactured product.", "fields": {},
    })
    monkeypatch.setattr(i18n, "_physical_field_names", lambda _: {})
    monkeypatch.setattr(i18n, "_translate_descriptions", lambda _: (_ for _ in ()).throw(HTTPException(503, "offline")))

    result = i18n.sync_descriptions(i18n.DescriptionSyncRequest(className="Product", database="oracle"))
    saved = i18n._load_store()["translations"]["nodeDescriptions"]["Product"]

    assert result["success"] is True
    assert "英文原文" in result["warning"]
    assert saved == {"zh": "A manufactured product.", "en": "A manufactured product."}
