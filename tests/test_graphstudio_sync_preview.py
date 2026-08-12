import datetime as dt
import zipfile

from rdflib import Graph, URIRef, XSD

from src.graphstudio_sync.preview import (
    _instance_uri,
    _literal,
    _serialize_deterministic_turtle,
    _write_zip,
)


def test_literal_does_not_emit_invalid_integer_lexical_form() -> None:
    valid = _literal("00123", "Integer")
    camstar_id = _literal("00071c8000000002", "Integer")

    assert valid.datatype == XSD.integer
    assert camstar_id.datatype == XSD.string


def test_literal_normalizes_declared_types() -> None:
    assert _literal(1, "Boolean").datatype == XSD.boolean
    assert _literal(dt.date(2026, 8, 12), "Date").datatype == XSD.date
    assert _literal("not-a-date", "Date").datatype == XSD.string


def test_composite_instance_uri_is_stable() -> None:
    uri = _instance_uri("ResourceLogs", ["ResourceId", "TxnId"], {"TxnId": 7, "ResourceId": "A B"})

    assert str(uri).endswith("/ResourceLogs/ResourceId=A%20B/TxnId=7")


def test_graphstudio_zip_has_stable_layout_and_zero_external_attributes(tmp_path) -> None:
    shard_dir = tmp_path / "rdf.ttl"
    shard_dir.mkdir()
    (shard_dir / "001_Product.ttl").write_text("<urn:p> <urn:q> <urn:r> .\n", encoding="utf-8")

    archive_path = _write_zip(tmp_path)

    with zipfile.ZipFile(archive_path) as archive:
        assert archive.namelist() == ["rdf.ttl/001_Product.ttl"]
        assert archive.getinfo("rdf.ttl/001_Product.ttl").external_attr == 0


def test_turtle_serialization_is_deterministic_and_round_trips(tmp_path) -> None:
    graph = Graph()
    graph.add((URIRef("urn:z"), URIRef("urn:p"), URIRef("urn:o")))
    graph.add((URIRef("urn:a"), URIRef("urn:p"), URIRef("urn:o")))
    first = tmp_path / "first.ttl"
    second = tmp_path / "second.ttl"

    _serialize_deterministic_turtle(graph, first)
    _serialize_deterministic_turtle(graph, second)

    assert first.read_bytes() == second.read_bytes()
    assert len(Graph().parse(first, format="turtle")) == 2
