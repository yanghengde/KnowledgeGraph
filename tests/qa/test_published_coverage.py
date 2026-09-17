from src.query import published_coverage as coverage


def test_coverage_distinguishes_definitions_empty_data_and_unknown(monkeypatch):
    runtime = {"layerUri": "urn:layer:current", "ontologyReleaseNo": 5}
    rows = [
        {"class": "urn:MfgOrder", "instanceCount": 5, "valueKind": "属性", "property": "urn:name"},
        {"class": "urn:MfgOrder", "instanceCount": 5, "valueKind": "关系", "property": "urn:product", "targetClass": "urn:Product", "relationshipCount": 5},
        {"class": "urn:Product", "instanceCount": 1, "valueKind": "关系", "property": "urn:unused", "targetClass": "urn:MfgOrder", "relationshipCount": 0},
        {"class": "urn:Other", "instanceCount": None, "valueKind": "关系", "property": "urn:unknown", "targetClass": "urn:Product", "relationshipCount": None},
    ]
    monkeypatch.setattr(coverage, "resolve_runtime_snapshot", lambda: runtime)
    def discover(snapshot, force_refresh):
        assert snapshot is runtime
        assert force_refresh is True
        return rows
    monkeypatch.setattr(coverage, "discover_schema", discover)
    result = coverage.published_coverage(refresh=True)
    assert result["summary"] == {"definedClasses": 3, "classesWithData": 2, "definedRelationships": 3, "relationshipsWithData": 1, "unknownClassCounts": 1, "unknownRelationshipCounts": 1}
    assert result["classes"][0]["propertyCount"] == 1
    assert result["relationships"][1]["count"] == 0
    assert result["relationships"][2]["count"] is None
