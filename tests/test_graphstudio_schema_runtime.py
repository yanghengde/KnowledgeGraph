import pytest
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
    def sparql(query, **kwargs):
        assert 'GRAPH <https://example.com/layer/r5>' in query
        assert kwargs['runtime_snapshot'] is runtime
        return {'results': {'bindings': [
            {k: {'value': v} for k, v in row.items()} for row in rows
        ]}}
    monkeypatch.setattr(assistant, '_request_sparql', sparql)
    monkeypatch.setattr(assistant, '_instance_counts', lambda _: {ns+'MfgOrder': 5})
    monkeypatch.setattr(assistant, '_relationship_counts', lambda _: {(ns+'MfgOrder', ns+'REL_WORKFLOW', ns+'Workflow'): 2})
    result = assistant._discover_schema_uncached(runtime)
    assert result[0]['instanceCount'] == 5
    assert result[1]['instanceCount'] == 0
    assert result[2]['questionEnabled'] is False
    assert result[2]['relationshipCount'] == 2


def test_empty_published_schema_fails_without_switching_source(monkeypatch):
    monkeypatch.setattr(assistant, '_request_sparql', lambda *a, **k: {})
    with pytest.raises(assistant.GraphStudioAssistantError, match='已发布本体'):
        assistant._discover_schema_uncached({'layerUri': 'https://example.com/layer'})


def test_schema_pagination_keeps_classes_after_first_page(monkeypatch):
    calls = []
    def sparql(query, **kwargs):
        calls.append(query)
        offset = 0 if 'OFFSET 0' in query else 2000
        size = 2000 if offset == 0 else 1
        return {'results': {'bindings': [
            {'class': {'value': f'urn:class:{offset+i}'}, 'valueKind': {'value': '对象类型'}}
            for i in range(size)
        ]}}
    monkeypatch.setattr(assistant, '_request_sparql', sparql)
    monkeypatch.setattr(assistant, '_instance_counts', lambda _: None)
    monkeypatch.setattr(assistant, '_relationship_counts', lambda _: None)
    result = assistant._discover_schema_uncached({'layerUri': 'https://example.com/layer'})
    assert len(result) == 2001
    assert result[-1]['class'] == 'urn:class:2000'
    assert result[-1]['instanceCount'] is None
    assert len(calls) == 2


def test_invalid_layer_is_not_interpolated_into_query():
    with pytest.raises(assistant.GraphStudioAssistantError):
        assistant._discover_schema_uncached({'layerUri': 'https://example.com/> } UNION {'})


def test_plan_parser_handles_prose_without_repairing_truncation():
    import json
    query = 'SELECT ?s WHERE { ?s ?p "brace }" } LIMIT 10'
    assert assistant._extract_json('Plan: ' + json.dumps({'sparql': query}) + ' Done {text}')['sparql'] == query
    with pytest.raises(assistant.GraphStudioAssistantError):
        assistant._extract_json('{"sparql": "SELECT')


@pytest.mark.parametrize('bad_content,finish', [
    ('{"sparql": "SELECT', 'stop'),
    ('{"sparql": "SELECT ?s WHERE { ?s ?p ?o }"}', 'length'),
    ('{"sparql": "DELETE WHERE { ?s ?p ?o }"}', 'stop'),
    ('{"sparql": "SELECT ?s WHERE {"}', 'stop'),
    ('{"sparql": {"query": "SELECT * WHERE {}"}}', 'stop'),
])
def test_planner_retries_invalid_output_then_validates(monkeypatch, bad_content, finish):
    import asyncio
    from types import SimpleNamespace
    calls = []
    async def create(**kwargs):
        calls.append(kwargs)
        content = bad_content if len(calls) == 1 else '{"sparql": "SELECT ?s WHERE { ?s ?p ?o }", "understanding": "objects"}'
        return SimpleNamespace(choices=[SimpleNamespace(
            finish_reason=finish if len(calls) == 1 else 'stop',
            message=SimpleNamespace(content=content))])
    monkeypatch.setattr(assistant, '_get_llm', lambda: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    query, _ = asyncio.run(assistant._plan_query('list objects', [], 'schema'))
    assert len(calls) == 2
    assert query.endswith('LIMIT 100')


def test_planner_stops_after_bounded_retries(monkeypatch):
    import asyncio
    from types import SimpleNamespace
    calls = []
    async def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(
            finish_reason='stop', message=SimpleNamespace(content='invalid'))])
    monkeypatch.setattr(assistant, '_get_llm', lambda: SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    with pytest.raises(assistant.GraphStudioAssistantError, match='尚未查询业务数据'):
        asyncio.run(assistant._plan_query('list objects', [], 'schema'))
    assert len(calls) == 3
