import datetime as dt
import zipfile

from rdflib import Graph, URIRef, XSD

from src.graphstudio_sync.preview import (
    _instance_uri,
    _iter_rows,
    _keyset_predicate,
    _validate_preview_policies,
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


def test_graphstudio_zip_has_api_6_3_rdf_directory_layout(tmp_path) -> None:
    shard_dir = tmp_path / "rdf.ttl"
    shard_dir.mkdir()
    (shard_dir / "001_Product.ttl").write_text("<urn:p> <urn:q> <urn:r> .\n", encoding="utf-8")

    archive_path = _write_zip(tmp_path)

    with zipfile.ZipFile(archive_path) as archive:
        assert archive.namelist() == ["rdf.ttl/001_Product.ttl"]


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


def test_sqlserver_composite_keyset_predicate_avoids_offset() -> None:
    sql, parameters = _keyset_predicate(
        ["ResourceId", "TxnId"],
        {"ResourceId": "R1", "TxnId": 42},
        "camstar_sqlserver",
    )

    assert "OFFSET" not in sql
    assert "[ResourceId] > %s" in sql
    assert "[ResourceId] = %s AND [TxnId] > %s" in sql
    assert parameters == ("R1", "R1", 42)


def test_oracle_keyset_predicate_uses_named_parameters() -> None:
    sql, parameters = _keyset_predicate(
        ["HISTORYID"],
        {"HISTORYID": "0002"},
        "camstar_oracle",
    )

    assert sql == ' WHERE ("HISTORYID" > :k0_0)'
    assert parameters == {"k0_0": "0002"}


def test_row_iterator_uses_bounded_keyset_pages() -> None:
    class Cursor:
        description = [("ProductId",), ("ProductName",)]

        def __init__(self):
            self.executions = []
            self.page = []
            self.closed = False

        def execute(self, sql, parameters):
            self.executions.append((sql, parameters))
            self.page = (
                [
                    {"ProductId": "001", "ProductName": "P1"},
                    {"ProductId": "002", "ProductName": "P2"},
                ]
                if len(self.executions) == 1
                else [{"ProductId": "003", "ProductName": "P3"}]
            )

        def fetchmany(self, size):
            result, self.page = self.page[:size], self.page[size:]
            return result

        def close(self):
            self.closed = True

    class Connection:
        def __init__(self):
            self.cursor_instance = Cursor()

        def cursor(self, as_dict=False):
            assert as_dict
            return self.cursor_instance

    connection = Connection()
    rows = list(
        _iter_rows(
            connection,
            kind="camstar_sqlserver",
            schema="CamstarPRD_SCHEMA",
            table="Product",
            columns=["ProductId", "ProductName"],
            primary_keys=["ProductId"],
            fetch_size=2,
        )
    )

    assert [row["ProductId"] for row in rows] == ["001", "002", "003"]
    assert "TOP (2)" in connection.cursor_instance.executions[0][0]
    assert "WHERE ([ProductId] > %s)" in connection.cursor_instance.executions[1][0]
    assert connection.cursor_instance.executions[1][1] == ("002",)
    assert connection.cursor_instance.closed


def test_preview_rejects_unreviewed_large_tables_before_extraction() -> None:
    policies = [
        {
            "class_name": "HistoryMainline",
            "requires_review": True,
            "enabled": True,
            "effective_strategy": None,
        }
    ]

    try:
        _validate_preview_policies(policies)
    except RuntimeError as exc:
        assert "explicit sync policy" in str(exc)
        assert "HistoryMainline" in str(exc)
    else:
        raise AssertionError("Unreviewed large table was not rejected")


def test_preview_never_falls_back_from_cdc_to_full_scan() -> None:
    policies = [
        {
            "class_name": "HistoryMainline",
            "requires_review": False,
            "enabled": True,
            "effective_strategy": "cdc",
        }
    ]

    try:
        _validate_preview_policies(policies)
    except RuntimeError as exc:
        assert "will not fall back to a full scan" in str(exc)
        assert "HistoryMainline=cdc" in str(exc)
    else:
        raise AssertionError("Unsupported CDC policy was allowed to perform a full scan")
