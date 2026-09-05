import pytest
from neo4j import GraphDatabase
from src.qa import graphstudio_assistant as assistant


def test_published_schema_reads_graphstudio_without_neo4j(monkeypatch):
    ns = assistant._PUBLISH_NAMESPACE
    runtime = {'layerUri': 'https://example.com/layer/r5', 'ontologyReleaseNo': 5}
    rows = [
        {'class': ns+'MfgOrder', 'valueKind': '对象类型', 'property': ''},
        {'class': ns+'Workflow', 'valueKind': '对象类型', 'property': ''},
        {'class': ns+'MfgOrder', 'valueKind': '关系', 'property': ns+'REL_WORKFLOW',
         'targetClass': ns+'Workflow', 'questionEnabled': 'false'},
    ]
    def no_neo4j(*args, **kwargs):
        pytest.fail('Question runtime must not open Neo4j')
    monkeypatch.setattr(GraphDatabase, 'driver', no_neo4j)
    def sparql(query, **kwargs):
        assert 'GRAPH <https://example.com/layer/r5>' in query
        assert kwargs['runtime_snapshot'] is runtime
        return {'results': {'bindings': [
            {k: {'value': v} for k, v in row.items()} for row in rows
        ]}}
    monkeypatch.setattr(assistant, '_request_sparql', sparql)
    monkeypatch.setattr(assistant, '_instance_counts', lambda _: {ns+'MfgOrder': 5})
    monkeypatch.setattr(assistant, '_relationship_counts', lambda _: {ns+'REL_WORKFLOW': 2})
    result = assistant._discover_schema_uncached(runtime)
    assert result[0]['instanceCount'] == 5
    assert result[1]['instanceCount'] == 0
    assert result[2]['questionEnabled'] is False
    assert result[2]['relationshipCount'] == 2


def test_empty_published_schema_fails_without_switching_source(monkeypatch):
    monkeypatch.setattr(assistant, '_request_sparql', lambda *a, **k: {})
    with pytest.raises(assistant.GraphStudioAssistantError, match='已发布本体'):
        assistant._discover_schema_uncached({'layerUri': 'https://example.com/layer'})


def test_invalid_layer_is_not_interpolated_into_query():
    with pytest.raises(assistant.GraphStudioAssistantError):
        assistant._discover_schema_uncached({'layerUri': 'https://example.com/> } UNION {'})
