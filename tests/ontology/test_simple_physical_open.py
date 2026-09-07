from web.routers import ontology_import as api
from starlette.datastructures import UploadFile
import io


def test_cached_model_open_never_starts_source_connection(monkeypatch):
    monkeypatch.setattr(api, "_reviewed_class_names", lambda: set())
    monkeypatch.setattr(api, "_curated_business_class_names", lambda: set())
    monkeypatch.setattr(api, "_start_description_job", lambda _: (_ for _ in ()).throw(AssertionError("No source connection")))
    monkeypatch.setattr(api, "load_descriptions", lambda _: {("Product", ""): {"descriptionEn": "Product", "descriptionZh": "产品"}})
    tables = b"CDODefId,CDOName,Workspace\n1,Product,csi\n"
    fields = b"CDODefId,CDOName,FieldID,FieldName,IsForeignKey,FKTableName,DataType,IsPrimaryKey,IsList\n1,Product,1,ProductId,False,,1,True,False\n"
    result = api.analyze_import(UploadFile(filename="tables.csv", file=io.BytesIO(tables)), UploadFile(filename="fields.csv", file=io.BytesIO(fields)), "sqlserver", False)
    assert result["candidates"][0]["descriptionZh"] == "产品"
    assert result["translation"]["status"] == "completed"
    assert result["edges"] == []
