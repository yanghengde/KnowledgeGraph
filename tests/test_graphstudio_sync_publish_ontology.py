from types import SimpleNamespace

from src.graphstudio_sync import publish_ontology


def _workspace():
    return {"workspace_key": "demo", "revision": 3}


def test_publish_ontology_requires_a_core_object(monkeypatch) -> None:
    monkeypatch.setattr(publish_ontology, "_workspace_row", lambda *_: _workspace())
    monkeypatch.setattr(
        publish_ontology,
        "workspace_graph",
        lambda *_: {
            "nodes": [{"id": "demo::Product", "data": {"targetName": "Product", "role": "context", "sourceClass": "Product"}}],
            "edges": [],
            "properties": [],
        },
    )

    result = publish_ontology.validate_workspace(SimpleNamespace(), SimpleNamespace(), "demo")

    assert result["valid"] is False
    assert {item["code"] for item in result["errors"]} == {"model.no_core"}


def test_publish_ontology_rejects_isolated_core_in_multi_object_model(monkeypatch) -> None:
    monkeypatch.setattr(publish_ontology, "_workspace_row", lambda *_: _workspace())
    monkeypatch.setattr(
        publish_ontology,
        "workspace_graph",
        lambda *_: {
            "nodes": [
                {"id": "demo::Product", "data": {"targetName": "Product", "role": "core", "sourceClass": "Product"}},
                {"id": "demo::MfgOrder", "data": {"targetName": "MfgOrder", "role": "core", "sourceClass": "MfgOrder"}},
            ],
            "edges": [],
            "properties": [],
        },
    )

    result = publish_ontology.validate_workspace(SimpleNamespace(), SimpleNamespace(), "demo")

    assert result["valid"] is False
    assert [item["code"] for item in result["errors"]].count("class.isolated_core") == 2


def test_projection_only_relation_provides_context_but_is_not_a_published_link(monkeypatch) -> None:
    monkeypatch.setattr(publish_ontology, "_workspace_row", lambda *_: _workspace())
    monkeypatch.setattr(
        publish_ontology,
        "workspace_graph",
        lambda *_: {
            "nodes": [
                {"id": "demo::Product", "data": {"targetName": "Product", "role": "core", "sourceClass": "Product"}},
                {"id": "demo::Attribute", "data": {"targetName": "ProductAttribute", "role": "context", "sourceClass": "ProductAttribute"}},
            ],
            "edges": [{"id": "projection", "source": "demo::Product", "target": "demo::Attribute", "data": {"usage": "projection_only"}}],
            "properties": [{"uid": "p1", "classUid": "demo::Product", "targetName": "displayGroup", "dataType": "String", "published": True}],
        },
    )

    result = publish_ontology.validate_workspace(SimpleNamespace(), SimpleNamespace(), "demo")

    assert result["valid"] is True
    assert result["counts"] == {"classes": 2, "properties": 1, "relationships": 1}
