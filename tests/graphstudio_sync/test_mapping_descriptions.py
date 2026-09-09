from types import SimpleNamespace

import pytest

from src.graphstudio_sync.config import SyncSettings
from src.ontology import designer_descriptions
from web import designer_metadata
from web.routers import semantic_mapping as api
from web.routers import ontology_import


@pytest.fixture
def description_sources(monkeypatch):
    draft = {"tableName": "Product", "fields": [{"physicalName": "ProductName"}, {"physicalName": "Description"}]}
    monkeypatch.setattr(api, "_store", lambda: SimpleNamespace(detail=lambda _: draft))
    monkeypatch.setattr(SyncSettings, "from_env", lambda: SimpleNamespace(source_kind="sqlserver"))
    monkeypatch.setattr(designer_metadata, "get_cdo_metadata", lambda *_: pytest.fail("Unexpected CDO fallback"))
    monkeypatch.setattr(ontology_import, "_load_description_cache", lambda: {})
    monkeypatch.setattr(ontology_import, "_configured_translation_provider", lambda: "none")
    monkeypatch.setattr(designer_descriptions, "save_descriptions", lambda *_: None)
    return draft


def test_cached_designer_descriptions_match_physical_names_and_table_case(description_sources, monkeypatch):
    monkeypatch.setattr(designer_descriptions, "load_descriptions", lambda _: {
        ("PRODUCT", "productname"): {"descriptionEn": "Product name", "descriptionZh": "产品名称"},
        ("Product", "Description"): {"descriptionEn": "Description", "descriptionZh": "说明"},
        ("Other", "ProductName"): {"descriptionEn": "Wrong table"},
        ("Product", "NotInCsv"): {"descriptionEn": "Not a physical field"},
    })
    monkeypatch.setattr(designer_metadata, "load_physical_description_catalog", lambda _: pytest.fail("Cache is complete"))
    result = api.field_descriptions("test")
    assert set(result["fields"]) == {"productname", "description"}
    assert result["fields"]["productname"]["descriptionZh"] == "产品名称"
    assert result["warning"] == ""


def test_missing_descriptions_use_designer_without_overwriting_saved_chinese(description_sources, monkeypatch):
    monkeypatch.setattr(designer_descriptions, "load_descriptions", lambda _: {
        ("Product", "ProductName"): {"descriptionEn": "Product name", "descriptionZh": "产品名称"},
    })
    monkeypatch.setattr(designer_metadata, "load_physical_description_catalog", lambda _: {
        "product": {"fields": {"ProductName": "Name", "DESCRIPTION": "Designer field help", "extra": "Ignore"}},
    })
    result = api.field_descriptions("test")
    assert result["fields"]["productname"]["descriptionZh"] == "产品名称"
    assert result["fields"]["description"]["descriptionEn"] == "Designer field help"
    assert "extra" not in result["fields"]


def test_source_failure_keeps_available_descriptions_and_returns_safe_warning(description_sources, monkeypatch):
    monkeypatch.setattr(designer_descriptions, "load_descriptions", lambda _: {
        ("Product", "ProductName"): {"descriptionEn": "Product name", "descriptionZh": ""},
    })
    def fail(_):
        raise RuntimeError("connection details must not be exposed")
    monkeypatch.setattr(designer_metadata, "load_physical_description_catalog", fail)
    result = api.field_descriptions("test")
    assert result["fields"]["productname"]["descriptionEn"] == "Product name"
    assert result["warning"]
    assert "connection details" not in result["warning"]


def test_cdo_fallback_and_oracle_source(description_sources, monkeypatch):
    seen = []
    monkeypatch.setattr(SyncSettings, "from_env", lambda: SimpleNamespace(source_kind="oracle"))
    monkeypatch.setattr(designer_descriptions, "load_descriptions", lambda db: seen.append(db) or {})
    monkeypatch.setattr(designer_metadata, "load_physical_description_catalog", lambda db: seen.append(db) or {})
    monkeypatch.setattr(designer_metadata, "get_cdo_metadata", lambda db, table: {
        "fields": {"productname": {"description": "Inherited Designer name"}}})
    result = api.field_descriptions("test")
    assert seen == ["oracle", "oracle"]
    assert result["fields"]["productname"]["descriptionEn"] == "Inherited Designer name"


def test_reuses_chinese_from_other_fields_and_translation_cache(description_sources, monkeypatch):
    saved = []
    monkeypatch.setattr(designer_descriptions, "load_descriptions", lambda _: {
        ("Product", "ProductName"): {"descriptionEn": "Product name", "descriptionZh": " "},
        ("Product", "Description"): {"descriptionEn": "Help text", "descriptionZh": ""},
        ("Other", "Name"): {"descriptionEn": "Product name", "descriptionZh": "产品名称"},
    })
    monkeypatch.setattr(ontology_import, "_load_description_cache", lambda: {"Help text": "帮助说明"})
    monkeypatch.setattr(ontology_import, "_build_batch_translator", lambda _: pytest.fail("All translations are cached"))
    monkeypatch.setattr(designer_descriptions, "save_descriptions", lambda db, rows: saved.extend(rows))
    result = api.field_descriptions("test")
    assert result["fields"]["productname"]["descriptionZh"] == "产品名称"
    assert result["fields"]["description"]["descriptionZh"] == "帮助说明"
    assert not result["warning"]
    assert {r["fieldName"] for r in saved} == {"productname", "description"}
    assert all(r["className"] == "Product" for r in saved)


def test_translates_only_missing_text_once_and_preserves_existing_chinese(description_sources, monkeypatch):
    fields = {
        "one": {"descriptionEn": "Created date", "descriptionZh": ""},
        "two": {"descriptionEn": "Created date", "descriptionZh": ""},
        "manual": {"descriptionEn": "Existing", "descriptionZh": "已有中文"},
    }
    calls, saved = [], []
    def translate(batch):
        calls.append(batch)
        return ["创建日期"]
    monkeypatch.setattr(ontology_import, "_configured_translation_provider", lambda: "api")
    monkeypatch.setattr(ontology_import, "_build_batch_translator", lambda _: (translate, 20))
    monkeypatch.setattr(designer_descriptions, "save_descriptions", lambda db, rows: saved.extend(rows))
    assert api._prefer_chinese_descriptions("sqlserver", "Product", fields, {}) == []
    assert calls == [["Created date"]]
    assert fields["one"]["descriptionZh"] == fields["two"]["descriptionZh"] == "创建日期"
    assert fields["manual"]["descriptionZh"] == "已有中文"
    assert len(saved) == 2
    assert fields["one"]["descriptionEn"] == "Created date"


def test_translation_failure_preserves_english_and_cached_chinese(description_sources, monkeypatch):
    fields = {"one": {"descriptionEn": "Cached"}, "two": {"descriptionEn": "Untranslated"}}
    monkeypatch.setattr(ontology_import, "_load_description_cache", lambda: {"Cached": "缓存中文"})
    monkeypatch.setattr(ontology_import, "_configured_translation_provider", lambda: "api")
    monkeypatch.setattr(ontology_import, "_build_batch_translator", lambda _: (lambda batch: [], 20))
    warnings = api._prefer_chinese_descriptions("sqlserver", "Product", fields, {})
    assert warnings
    assert fields["one"]["descriptionZh"] == "缓存中文"
    assert fields["two"]["descriptionEn"] == "Untranslated"
    assert not fields["two"].get("descriptionZh")
