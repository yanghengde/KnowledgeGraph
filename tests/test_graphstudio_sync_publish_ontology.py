from types import SimpleNamespace

from src.graphstudio_sync import publish_ontology


def _workspace():
    return {"workspace_key": "demo", "revision": 3}


def test_governance_status_includes_active_release_graph(monkeypatch):
    class _Rows:
        def mappings(self):
            return self

        def __iter__(self):
            return iter([])

    class _Connection:
        def execute(self, *_args, **_kwargs):
            return _Rows()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    repository = SimpleNamespace(engine=SimpleNamespace(connect=lambda: _Connection()))
    active = {"ontology_release_id": "release-7", "release_no": 7}
    frozen = {"classes": [{"class": {"targetName": "Product"}}], "relationships": []}
    monkeypatch.setattr(publish_ontology, "active_release", lambda *_: active)
    monkeypatch.setattr(publish_ontology, "release_graph", lambda _settings, release_id: frozen if release_id == "release-7" else None)

    result = publish_ontology.ontology_governance_status(SimpleNamespace(
        publish_neo4j_database="publish", neo4j_database="source",
    ), repository, "profile")

    assert result["activeRelease"] == active
    assert result["activeReleaseGraph"] == frozen


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


def test_discovery_plan_combines_physical_and_semantic_relationships(monkeypatch) -> None:
    class Result:
        def __init__(self, rows):
            self.rows = rows

        def data(self):
            return self.rows

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def run(self, query, **_):
            if "NOT t.name IN" in query:
                return Result([{
                    "anchor": "MfgOrder", "className": "Workflow",
                    "chineseName": "工作流", "relationship": "USES_WORKFLOW",
                    "cardinality": "MANY_TO_ONE",
                }])
            return Result([{
                "source": "MfgOrder", "target": "Product",
                "name": "ORDERED_PRODUCT", "cardinality": "MANY_TO_ONE",
                "description": "ordered product",
            }])

    class Driver:
        def session(self, **_):
            return Session()

        def close(self):
            return None

    monkeypatch.setattr(publish_ontology, "_driver", lambda *_args, **_kwargs: Driver())
    monkeypatch.setattr(
        publish_ontology,
        "build_query_builder_plan",
        lambda *_args, **_kwargs: {
            "selected_nodes": ["MfgOrder", "Product"],
            "nodes": [
                {"id": "MfgOrder", "selected": True, "bridge": False},
                {"id": "Product", "selected": True, "bridge": False},
            ],
            "joins": [{
                "from_table": "MfgOrder", "from_field": "ProductId",
                "to_table": "Product", "to_field": "ProductId",
            }],
            "warnings": [],
        },
    )
    settings = SimpleNamespace(neo4j_database="neo4j")

    result = publish_ontology.build_discovery_plan(
        settings, ["MfgOrder", "Product"], dialect="sqlserver",
    )

    assert result["proposal_only"] is True
    assert result["joins"][0]["recommended_name"] == "ORDERED_PRODUCT"
    assert result["joins"][0]["recommended_source"] == "MfgOrder"
    assert result["neighbor_suggestions"][0]["className"] == "Workflow"
