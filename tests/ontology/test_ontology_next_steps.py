from src.graphstudio_sync import ontology_store, publish_ontology, publish_ontology_postgres


def setup_model(monkeypatch, *, connected=False):
    source = {
        "classes": [{"name": name, "chineseName": name} for name in ("Spec", "Operation", "WorkflowStep", "Other")],
        "properties": [],
        "relationships": [
            {"source": "Spec", "target": "Operation", "name": "HAS_OPERATION", "physicalColumn": "OperationId"},
            {"source": "WorkflowStep", "target": "Spec", "name": "HAS_SPEC"},
            {"source": "Operation", "target": "Other", "name": "HAS_OTHER"},
        ],
    }
    graph = {"nodes": [{"id": "w::Spec", "data": {"sourceClass": "Spec", "targetName": "ProcessSpecification", "role": "core"}}], "edges": [], "properties": []}
    if connected:
        graph["nodes"].append({"id": "w::Operation", "data": {"sourceClass": "Operation", "targetName": "Operation", "role": "context"}})
        graph["edges"].append({"id": "r", "source": "w::Spec", "target": "w::Operation", "data": {"targetName": "HAS_OPERATION"}})
    monkeypatch.setattr(ontology_store, "source_payload", lambda *_: source)
    monkeypatch.setattr(publish_ontology, "_workspace_row", lambda *_: {"status": "frozen"})
    monkeypatch.setattr(publish_ontology, "workspace_graph", lambda *_: graph)
    return graph


def test_single_node_offers_unmodeled_direct_neighbors_and_preserves_direction(monkeypatch):
    graph = setup_model(monkeypatch)
    result = publish_ontology.relationship_suggestions(None, None, "w", "w::Spec")
    assert {p["existingClass"] for p in result["items"]} == {"Operation", "WorkflowStep"}
    incoming = next(p for p in result["items"] if p["existingClass"] == "WorkflowStep")
    assert incoming["relationships"][0]["sourceClass"] == "WorkflowStep"
    assert incoming["relationships"][0]["targetClass"] == "Spec"
    assert incoming["missingNodes"][0]["sourceClass"] == "WorkflowStep"
    outgoing = next(p for p in result["items"] if p["existingClass"] == "Operation")
    assert outgoing["relationships"][0]["physicalColumn"] == "OperationId"
    assert len(graph["nodes"]) == 1  # Frozen workspaces can be explored without writes.


def test_existing_relationship_is_not_offered_again(monkeypatch):
    setup_model(monkeypatch, connected=True)
    result = publish_ontology.relationship_suggestions(None, None, "w", "w::Spec")
    assert [p["existingClass"] for p in result["items"]] == ["WorkflowStep"]


def test_two_hop_expansion_does_not_flood_with_unconnected_leaf_objects(monkeypatch):
    setup_model(monkeypatch)
    rows = publish_ontology_postgres.relationship_rows(None, "Spec", [], 2)
    assert all(len(row["relationships"]) == 1 for row in rows)
    rows = publish_ontology_postgres.relationship_rows(None, "Spec", ["Other"], 2)
    assert any(row["existingClass"] == "Other" and len(row["relationships"]) == 2 for row in rows)


def test_direct_outgoing_reference_ranks_before_incoming_history(monkeypatch):
    setup_model(monkeypatch)
    source = ontology_store.source_payload(None)
    source["classes"].append({"name": "SpecHistory", "chineseName": "History"})
    source["relationships"][1] = {"source": "SpecHistory", "target": "Spec", "name": "HAS_SPEC"}
    result = publish_ontology.relationship_suggestions(None, None, "w", "w::Spec")
    assert result["items"][0]["existingClass"] == "Operation"
    assert result["items"][0]["recommended"]
