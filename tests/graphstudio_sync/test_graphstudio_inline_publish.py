import requests
import pytest
from rdflib import Dataset, URIRef

from src.graphstudio_sync.config import normalize_graphstudio_url
from src.graphstudio_sync.publishing.deployment import _inline_rdf_query
from src.graphstudio_sync.publishing.deployment import _write_graphstudio_rdf_zip
from src.graphstudio_sync.publishing.deployment import _ensure_load_step
from src.graphstudio_sync.transport import configure_graphstudio_tls


def test_browser_url_becomes_api_base():
    assert normalize_graphstudio_url('https://example.com:8443/sdl/index.html#/main/home/-') == 'https://example.com:8443'
    with pytest.raises(ValueError):
        normalize_graphstudio_url('https://user:secret@example.com')


def test_inline_replay_is_idempotent_and_keeps_template_literals(tmp_path):
    ttl = tmp_path / 'data.ttl'
    ttl.write_text('<urn:s> <urn:p> [ <urn:text> "${targetGraph}" ] .', encoding='utf-8')
    archive = tmp_path / 'data.zip'
    _write_graphstudio_rdf_zip(archive, ttl)
    query = _inline_rdf_query(archive, 10000)
    assert query == _inline_rdf_query(archive, 10000)
    assert query.count('${targetGraph}') == 1
    dataset = Dataset()
    graph = dataset.graph(URIRef('urn:target'))
    update = query.replace('${targetGraph}', '<urn:target>')
    dataset.update(update)
    count = len(graph)
    assert count == 2
    dataset.update(update)
    assert len(graph) == count
    assert any(str(value) == '${targetGraph}' for value in graph.objects())
    with pytest.raises(ValueError, match='上限'):
        _inline_rdf_query(archive, 10)


def test_certificate_pin_is_host_scoped():
    session = requests.Session()
    configure_graphstudio_tls(session, 'https://example.com:8443', 'ab' * 32)
    adapter = session.get_adapter('https://example.com:8443/api/models')
    assert adapter.poolmanager.connection_pool_kw['assert_fingerprint'] == 'ab' * 32
    assert session.get_adapter('https://example.com:8443.evil.test/') is not adapter
    assert session.verify is True


def test_inline_step_must_be_read_back_before_activation():
    class Response:
        ok = True
        def __init__(self, data): self.data = data
        def json(self): return self.data

    class Session:
        def get(self, url, **kwargs):
            return Response([] if url.endswith('/steps') else {'type': 'QueryStep', 'transformQuery': 'truncated'})
        def post(self, url, **kwargs):
            assert kwargs['json']['type'] == 'QueryStep'
            assert 'gmLinkedDataset' not in kwargs['json']
            return Response({'uri': 'https://example.com/step'})

    with pytest.raises(RuntimeError, match='完整保存'):
        _ensure_load_step(Session(), 'https://example.com', layer_uri='urn:layer', catalog=None,
                          model_uri='urn:model', inline_query='INSERT {} WHERE {}')


@pytest.mark.parametrize('acquired', [True, False])
def test_publication_lock_blocks_overlap_and_releases_on_failure(monkeypatch, acquired):
    from types import SimpleNamespace
    from src.graphstudio_sync.publishing import deployment

    calls = []
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, sql):
            calls.append(str(sql))
            return SimpleNamespace(scalar=lambda: acquired)

    def fail(*args, **kwargs):
        calls.append('publish')
        raise RuntimeError('test failure')

    monkeypatch.setattr(deployment, '_apply_deployment', fail)
    repo = SimpleNamespace(engine=SimpleNamespace(connect=lambda: Connection()))
    with pytest.raises(RuntimeError):
        deployment.apply_deployment(None, repo, deployment_id='test')
    assert ('publish' in calls) is acquired
    assert any('pg_advisory_unlock' in call for call in calls) is acquired
