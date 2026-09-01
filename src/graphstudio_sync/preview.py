"""Build a complete, read-only RDF preview for Camstar and its ontology."""

from __future__ import annotations

import base64
import datetime as dt
import decimal
import hashlib
import json
import stat
import re
import uuid
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

from neo4j import GraphDatabase
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD
from rdflib.namespace import OWL, SKOS
from sqlalchemy import text

from .config import PROJECT_ROOT, SyncSettings
from .connections import resolved_settings
from .repository import ControlPlaneRepository
from .source_database import (
    ORACLE_KIND,
    connect_source,
    fetch_dicts,
    fetchmany_dicts,
    quote_identifier,
    source_cursor,
)


ONTOLOGY_URI = URIRef("https://opcenter.siemens.com/ontology/camstar/2607/full")
SCHEMA = Namespace(str(ONTOLOGY_URI) + "/schema/")
DATA = Namespace("https://opcenter.siemens.com/data/camstar/2607/")
PREVIEW_ROOT = PROJECT_ROOT / "outputs" / "graphstudio" / "previews"
SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$#]*$")


def _bind(graph: Graph) -> None:
    graph.bind("cam", SCHEMA)
    graph.bind("camdata", DATA)
    graph.bind("owl", OWL)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("skos", SKOS)
    graph.bind("xsd", XSD)


def _class_uri(class_name: str) -> URIRef:
    return URIRef(f"{SCHEMA}class/{quote(class_name, safe='-._~')}")


def _property_uri(class_name: str, property_name: str) -> URIRef:
    return URIRef(
        f"{SCHEMA}class/{quote(class_name, safe='-._~')}/property/"
        f"{quote(property_name, safe='-._~')}"
    )


def _relationship_uri(source: str, name: str, target: str) -> URIRef:
    return URIRef(
        f"{SCHEMA}class/{quote(source, safe='-._~')}/relationship/"
        f"{quote(name, safe='-._~')}/{quote(target, safe='-._~')}"
    )


def _identifier_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return format(value, "f")
    return str(value).rstrip()


def _instance_uri(class_name: str, pk_columns: list[str], row_or_value: Any) -> URIRef:
    if isinstance(row_or_value, dict):
        segments = [
            f"{quote(column, safe='-._~')}={quote(_identifier_text(row_or_value[column]), safe='-._~')}"
            for column in pk_columns
        ]
    else:
        if len(pk_columns) != 1:
            raise ValueError(f"Composite primary key requires a complete row: {class_name}")
        segments = [
            f"{quote(pk_columns[0], safe='-._~')}={quote(_identifier_text(row_or_value), safe='-._~')}"
        ]
    return URIRef(f"{DATA}{quote(class_name, safe='-._~')}/{'/'.join(segments)}")


def _literal(value: Any, data_type: str | None = None) -> Literal:
    declared = str(data_type or "")
    lexical = str(value).rstrip()
    if declared == "Boolean":
        normalized = lexical.casefold()
        if normalized in {"1", "true", "yes", "y"}:
            return Literal(True, datatype=XSD.boolean)
        if normalized in {"0", "false", "no", "n"}:
            return Literal(False, datatype=XSD.boolean)
        return Literal(lexical, datatype=XSD.string)
    if declared == "Integer":
        if isinstance(value, int) and not isinstance(value, bool):
            return Literal(value, datatype=XSD.integer)
        if isinstance(value, decimal.Decimal) and value == value.to_integral_value():
            return Literal(format(value, "f"), datatype=XSD.integer)
        if re.fullmatch(r"[+-]?\d+", lexical):
            return Literal(lexical, datatype=XSD.integer)
        return Literal(lexical, datatype=XSD.string)
    if declared == "Float":
        try:
            decimal.Decimal(lexical)
        except decimal.InvalidOperation:
            return Literal(lexical, datatype=XSD.string)
        return Literal(lexical, datatype=XSD.double)
    if declared == "DateTime":
        if isinstance(value, dt.datetime):
            return Literal(value.isoformat(), datatype=XSD.dateTime)
        try:
            dt.datetime.fromisoformat(lexical.replace("Z", "+00:00"))
        except ValueError:
            return Literal(lexical, datatype=XSD.string)
        return Literal(lexical, datatype=XSD.dateTime)
    if declared == "Date":
        if isinstance(value, dt.datetime):
            value = value.date()
        if isinstance(value, dt.date):
            return Literal(value.isoformat(), datatype=XSD.date)
        try:
            dt.date.fromisoformat(lexical)
        except ValueError:
            return Literal(lexical, datatype=XSD.string)
        return Literal(lexical, datatype=XSD.date)
    if declared == "Time":
        if isinstance(value, dt.time):
            return Literal(value.isoformat(), datatype=XSD.time)
        try:
            dt.time.fromisoformat(lexical)
        except ValueError:
            return Literal(lexical, datatype=XSD.string)
        return Literal(lexical, datatype=XSD.time)
    if isinstance(value, bytes):
        return Literal(base64.b64encode(value).decode("ascii"), datatype=XSD.base64Binary)
    return Literal(lexical, datatype=XSD.string)


def _xsd_type(data_type: str | None) -> URIRef:
    return {
        "Boolean": XSD.boolean,
        "Integer": XSD.integer,
        "Float": XSD.double,
        "DateTime": XSD.dateTime,
        "Date": XSD.date,
        "Time": XSD.time,
    }.get(str(data_type or ""), XSD.string)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _semantic_sha256(graph: Graph) -> str:
    digest = hashlib.sha256()
    for subject, predicate, obj in sorted(
        graph,
        key=lambda triple: tuple(term.n3() for term in triple),
    ):
        digest.update(f"{subject.n3()} {predicate.n3()} {obj.n3()} .\n".encode("utf-8"))
    return digest.hexdigest()


def _serialize_deterministic_turtle(graph: Graph, path: Path) -> None:
    lines = [
        f"{subject.n3()} {predicate.n3()} {obj.n3()} ."
        for subject, predicate, obj in sorted(
            graph,
            key=lambda triple: tuple(term.n3() for term in triple),
        )
    ]
    path.write_text(
        "# Deterministic Turtle; the N-Triples grammar below is a valid Turtle subset.\n"
        + "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )


def _safe_sql_identifier(value: str, kind: str) -> str:
    if not SAFE_IDENTIFIER.fullmatch(value):
        raise RuntimeError(f"Unsafe SQL identifier: {value!r}")
    return quote_identifier(value, kind)


def _load_catalog(repository: ControlPlaneRepository) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        snapshot = connection.execute(
            text("SELECT * FROM graphsync.current_catalog_snapshot")
        ).mappings().one_or_none()
        if snapshot is None:
            raise RuntimeError("No ready PostgreSQL mapping catalog; run compile-catalog first")
        classes = [
            dict(row)
            for row in connection.execute(
                text("SELECT * FROM graphsync.current_class_mapping ORDER BY class_name")
            ).mappings()
        ]
        properties = [
            dict(row)
            for row in connection.execute(
                text(
                    """
                    SELECT * FROM graphsync.current_property_mapping
                    ORDER BY class_name, property_name
                    """
                )
            ).mappings()
        ]
        relationships = [
            dict(row)
            for row in connection.execute(
                text(
                    """
                    SELECT * FROM graphsync.current_relationship_mapping
                    ORDER BY source_class, relationship_name, target_class
                    """
                )
            ).mappings()
        ]
    return {
        "snapshot": dict(snapshot),
        "classes": classes,
        "properties": properties,
        "relationships": relationships,
    }


def _load_descriptions(settings: SyncSettings) -> dict[str, dict[Any, dict[str, Any]]]:
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            classes = {
                record["name"]: dict(record)
                for record in session.run(
                    """
                    MATCH (c:OntologyClass)
                    RETURN c.name AS name, c.description AS description,
                           c.chineseName AS chineseName
                    """
                )
            }
            properties = {
                (record["className"], record["name"]): dict(record)
                for record in session.run(
                    """
                    MATCH (c:OntologyClass)-[:HAS_PROPERTY]->(p:OntologyProperty)
                    RETURN c.name AS className, p.name AS name,
                           p.description AS description
                    """
                )
            }
            relationships = {
                (record["source"], record["name"], record["target"]): dict(record)
                for record in session.run(
                    """
                    MATCH (source:OntologyClass)-[r:ONTOLOGY_RELATION]->(target:OntologyClass)
                    RETURN source.name AS source, r.name AS name, target.name AS target,
                           r.description AS description
                    """
                )
            }
    finally:
        driver.close()
    return {"classes": classes, "properties": properties, "relationships": relationships}


def _source_metadata(settings: SyncSettings, class_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    connection = connect_source(settings)
    cursor = source_cursor(connection, settings.source_kind)
    try:
        if settings.source_kind == ORACLE_KIND:
            owner = (settings.source_schema or settings.source_user).upper()
            cursor.execute(
                """
                SELECT cols.OWNER AS "TABLE_SCHEMA", cols.TABLE_NAME AS "TABLE_NAME",
                       cols.COLUMN_NAME AS "COLUMN_NAME", cols.POSITION AS "ORDINAL_POSITION"
                FROM ALL_CONSTRAINTS constraints
                JOIN ALL_CONS_COLUMNS cols
                  ON cols.OWNER=constraints.OWNER
                 AND cols.CONSTRAINT_NAME=constraints.CONSTRAINT_NAME
                WHERE constraints.CONSTRAINT_TYPE='P' AND constraints.OWNER=:owner
                ORDER BY cols.OWNER,cols.TABLE_NAME,cols.POSITION
                """,
                {"owner": owner},
            )
        else:
            cursor.execute(
                """
                SELECT tc.TABLE_SCHEMA, tc.TABLE_NAME, kcu.COLUMN_NAME, kcu.ORDINAL_POSITION
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                  ON kcu.CONSTRAINT_SCHEMA=tc.CONSTRAINT_SCHEMA
                 AND kcu.CONSTRAINT_NAME=tc.CONSTRAINT_NAME
                 AND kcu.TABLE_NAME=tc.TABLE_NAME
                WHERE tc.CONSTRAINT_TYPE='PRIMARY KEY'
                ORDER BY tc.TABLE_SCHEMA,tc.TABLE_NAME,kcu.ORDINAL_POSITION
                """
            )
        pk_by_table: dict[tuple[str, str], list[str]] = defaultdict(list)
        for row in fetch_dicts(cursor):
            pk_by_table[(row["TABLE_SCHEMA"], row["TABLE_NAME"])].append(row["COLUMN_NAME"])
        if settings.source_kind == ORACLE_KIND:
            cursor.execute(
                """
                SELECT OWNER AS "TABLE_SCHEMA", TABLE_NAME AS "TABLE_NAME",
                       COLUMN_NAME AS "COLUMN_NAME"
                FROM ALL_TAB_COLUMNS
                WHERE OWNER=:owner
                ORDER BY OWNER,TABLE_NAME,COLUMN_ID
                """,
                {"owner": owner},
            )
        else:
            cursor.execute(
                """
                SELECT TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                ORDER BY TABLE_SCHEMA,TABLE_NAME,ORDINAL_POSITION
                """
            )
        columns_by_table: dict[tuple[str, str], list[str]] = defaultdict(list)
        for row in fetch_dicts(cursor):
            columns_by_table[(row["TABLE_SCHEMA"], row["TABLE_NAME"])].append(row["COLUMN_NAME"])
    finally:
        connection.close()
    result: dict[str, dict[str, Any]] = {}
    for item in class_rows:
        key = (item["physical_schema"], item["physical_table"])
        result[item["class_name"]] = {
            "schema": item["physical_schema"],
            "table": item["physical_table"],
            "primaryKeys": pk_by_table.get(key, []),
            "columns": columns_by_table.get(key, []),
        }
    missing = [name for name, item in result.items() if not item["primaryKeys"]]
    if missing:
        raise RuntimeError(f"Mapped source tables without primary keys: {missing}")
    return result


def _build_model(
    catalog: dict[str, Any],
    descriptions: dict[str, dict[Any, dict[str, Any]]],
) -> Graph:
    graph = Graph()
    _bind(graph)
    graph.add((ONTOLOGY_URI, RDF.type, OWL.Ontology))
    graph.add((ONTOLOGY_URI, RDFS.label, Literal("Opcenter 2607 Camstar Full Ontology", lang="en")))
    graph.add((ONTOLOGY_URI, RDFS.label, Literal("Opcenter 2607 Camstar 全量本体", lang="zh")))
    graph.add((ONTOLOGY_URI, RDFS.comment, Literal("Compiled from the reviewed Neo4j ontology and PostgreSQL mapping catalog.")))

    annotations = {
        "sourceTable": "Camstar physical source table",
        "sourceColumn": "Camstar physical source column",
        "sourceFieldId": "Camstar Designer field identifier",
        "sourceCDODefId": "Camstar Designer CDO identifier",
        "mappingStatus": "Mapping review status",
        "cardinality": "Relationship cardinality",
        "required": "Required ontology property",
        "catalogHash": "Mapping catalog SHA-256",
    }
    for name, label in annotations.items():
        graph.add((SCHEMA[name], RDF.type, OWL.AnnotationProperty))
        graph.add((SCHEMA[name], RDFS.label, Literal(label, lang="en")))
    graph.add((ONTOLOGY_URI, SCHEMA.catalogHash, Literal(catalog["snapshot"]["catalog_hash"])))

    for item in catalog["classes"]:
        uri = _class_uri(item["class_name"])
        detail = descriptions["classes"].get(item["class_name"], {})
        graph.add((uri, RDF.type, OWL.Class))
        graph.add((uri, RDFS.label, Literal(item["class_name"], lang="en")))
        chinese = detail.get("chineseName") or item.get("chinese_name")
        if chinese:
            graph.add((uri, SKOS.prefLabel, Literal(chinese, lang="zh")))
        if detail.get("description"):
            graph.add((uri, RDFS.comment, Literal(detail["description"])))
        graph.add((uri, SCHEMA.sourceTable, Literal(f"{item['physical_schema']}.{item['physical_table']}")))
        if item.get("source_cdo_def_id"):
            graph.add((uri, SCHEMA.sourceCDODefId, Literal(item["source_cdo_def_id"])))
        graph.add((uri, SCHEMA.mappingStatus, Literal(item["mapping_status"])))

    class_by_table = {
        str(item["physical_table"]).casefold(): item["class_name"]
        for item in catalog["classes"]
    }
    for item in catalog["properties"]:
        uri = _property_uri(item["class_name"], item["property_name"])
        navigation = item["data_type"] == "Navigation"
        graph.add((uri, RDF.type, OWL.ObjectProperty if navigation else OWL.DatatypeProperty))
        graph.add((uri, RDFS.domain, _class_uri(item["class_name"])))
        if navigation:
            target = class_by_table.get(str(item.get("fk_table_name") or "").casefold())
            if target:
                graph.add((uri, RDFS.range, _class_uri(target)))
        else:
            graph.add((uri, RDFS.range, _xsd_type(item.get("data_type"))))
        graph.add((uri, RDFS.label, Literal(item["property_name"])))
        detail = descriptions["properties"].get((item["class_name"], item["property_name"]), {})
        if detail.get("description"):
            graph.add((uri, RDFS.comment, Literal(detail["description"])))
        graph.add((uri, SCHEMA.required, Literal(bool(item["required"]), datatype=XSD.boolean)))
        graph.add((uri, SCHEMA.mappingStatus, Literal(item["mapping_status"])))
        if item.get("source_field_id"):
            graph.add((uri, SCHEMA.sourceFieldId, Literal(item["source_field_id"])))
        if item.get("physical_column"):
            graph.add((uri, SCHEMA.sourceColumn, Literal(item["physical_column"])))

    for item in catalog["relationships"]:
        uri = _relationship_uri(item["source_class"], item["relationship_name"], item["target_class"])
        graph.add((uri, RDF.type, OWL.ObjectProperty))
        graph.add((uri, RDFS.domain, _class_uri(item["source_class"])))
        graph.add((uri, RDFS.range, _class_uri(item["target_class"])))
        graph.add((uri, RDFS.label, Literal(item["relationship_name"])))
        detail = descriptions["relationships"].get(
            (item["source_class"], item["relationship_name"], item["target_class"]), {}
        )
        if detail.get("description"):
            graph.add((uri, RDFS.comment, Literal(detail["description"])))
        if item.get("cardinality"):
            graph.add((uri, SCHEMA.cardinality, Literal(item["cardinality"])))
        graph.add((uri, SCHEMA.mappingStatus, Literal(item["mapping_status"])))
        if item.get("source_field_id"):
            graph.add((uri, SCHEMA.sourceFieldId, Literal(item["source_field_id"])))
        if item.get("physical_column"):
            graph.add((uri, SCHEMA.sourceColumn, Literal(item["physical_column"])))
    return graph


def _label_for_row(
    class_name: str,
    row: dict[str, Any],
    properties: list[dict[str, Any]],
    primary_keys: list[str],
) -> str:
    preferred = next(
        (
            item["physical_column"]
            for item in properties
            if item["property_name"] == "name" and item.get("physical_column")
        ),
        None,
    )
    if preferred and row.get(preferred) not in (None, ""):
        return str(row[preferred]).rstrip()
    values = ", ".join(_identifier_text(row[column]) for column in primary_keys)
    return f"{class_name} {values}"


def _iter_rows(
    connection,
    *,
    kind: str,
    schema: str,
    table: str,
    columns: list[str],
    primary_keys: list[str],
    fetch_size: int,
    start_after: dict[str, Any] | None = None,
):
    selected = sorted(set(columns), key=lambda value: (value not in primary_keys, value.casefold()))
    sql_columns = ", ".join(_safe_sql_identifier(column, kind) for column in selected)
    order_by = ", ".join(_safe_sql_identifier(column, kind) for column in primary_keys)
    cursor = source_cursor(connection, kind)
    last_key = dict(start_after) if start_after else None
    try:
        while True:
            predicate, parameters = _keyset_predicate(primary_keys, last_key, kind)
            table_name = f"{_safe_sql_identifier(schema, kind)}.{_safe_sql_identifier(table, kind)}"
            if kind == ORACLE_KIND:
                sql = (
                    f"SELECT {sql_columns} FROM {table_name}{predicate} "
                    f"ORDER BY {order_by} FETCH FIRST {int(fetch_size)} ROWS ONLY"
                )
            else:
                sql = (
                    f"SELECT TOP ({int(fetch_size)}) {sql_columns} FROM {table_name}{predicate} "
                    f"ORDER BY {order_by}"
                )
            cursor.execute(sql, parameters)
            page: list[dict[str, Any]] = []
            while len(page) < fetch_size:
                rows = fetchmany_dicts(cursor, min(fetch_size - len(page), 10_000))
                if not rows:
                    break
                page.extend(rows)
            if not page:
                break
            yield from page
            last_key = {column: page[-1][column] for column in primary_keys}
            if len(page) < fetch_size:
                break
    finally:
        cursor.close()


def _keyset_predicate(
    primary_keys: list[str],
    last_key: dict[str, Any] | None,
    kind: str,
) -> tuple[str, Any]:
    if not last_key:
        return "", {} if kind == ORACLE_KIND else ()
    clauses: list[str] = []
    if kind == ORACLE_KIND:
        parameters: dict[str, Any] = {}
        for index, column in enumerate(primary_keys):
            parts: list[str] = []
            for prior in range(index):
                name = f"k{index}_{prior}"
                parts.append(f"{_safe_sql_identifier(primary_keys[prior], kind)} = :{name}")
                parameters[name] = last_key[primary_keys[prior]]
            name = f"k{index}_{index}"
            parts.append(f"{_safe_sql_identifier(column, kind)} > :{name}")
            parameters[name] = last_key[column]
            clauses.append("(" + " AND ".join(parts) + ")")
        return " WHERE " + " OR ".join(clauses), parameters
    parameters_list: list[Any] = []
    for index, column in enumerate(primary_keys):
        parts = []
        for prior in range(index):
            parts.append(f"{_safe_sql_identifier(primary_keys[prior], kind)} = %s")
            parameters_list.append(last_key[primary_keys[prior]])
        parts.append(f"{_safe_sql_identifier(column, kind)} > %s")
        parameters_list.append(last_key[column])
        clauses.append("(" + " AND ".join(parts) + ")")
    return " WHERE " + " OR ".join(clauses), tuple(parameters_list)


def _estimated_triple_bytes(triple: tuple[Any, Any, Any]) -> int:
    return sum(len(term.n3().encode("utf-8")) for term in triple) + 4


def _add_triple(graph: Graph, triple: tuple[Any, Any, Any]) -> int:
    if triple in graph:
        return 0
    graph.add(triple)
    return _estimated_triple_bytes(triple)


def _policy_by_class(policies: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["class_name"]: item for item in policies}


def _validate_preview_policies(policies: list[dict[str, Any]]) -> None:
    unreviewed = [item["class_name"] for item in policies if item.get("requires_review")]
    if unreviewed:
        raise RuntimeError(
            "Large tables require an explicit sync policy before extraction: "
            + ", ".join(unreviewed[:20])
        )
    unsupported = [
        f"{item['class_name']}={item.get('effective_strategy')}"
        for item in policies
        if item.get("enabled", True)
        and item.get("effective_strategy") in {"watermark", "append_only", "cdc"}
    ]
    if unsupported:
        raise RuntimeError(
            "Incremental source adapters are not enabled; preview will not fall back to a full scan: "
            + ", ".join(unsupported[:20])
        )


def _load_reference_subjects(
    settings: SyncSettings,
    catalog: dict[str, Any],
    metadata: dict[str, dict[str, Any]],
    policies: dict[str, dict[str, Any]],
    *,
    row_limit: int,
) -> tuple[set[str], set[str], set[str]]:
    referenced_classes = {
        item["target_class"]
        for item in catalog["relationships"]
        if item["mapping_status"] == "resolved"
    }
    class_by_table = {
        str(item["physical_table"]).casefold(): item["class_name"]
        for item in catalog["classes"]
    }
    referenced_classes.update(
        target
        for item in catalog["properties"]
        if item["data_type"] == "Navigation"
        for target in [class_by_table.get(str(item.get("fk_table_name") or "").casefold())]
        if target
    )
    class_rows = {item["class_name"]: int(item.get("approximate_rows") or 0) for item in catalog["classes"]}
    candidates = sorted(referenced_classes, key=lambda name: (class_rows.get(name, 0), name))
    subjects: set[str] = set()
    validated: set[str] = set()
    skipped: set[str] = set()
    source = connect_source(settings)
    try:
        for class_name in candidates:
            policy = policies[class_name]
            if not policy.get("enabled", True) or policy.get("effective_strategy") == "excluded":
                skipped.add(class_name)
                continue
            remaining = row_limit - len(subjects)
            if remaining <= 0 or class_rows.get(class_name, 0) > remaining:
                skipped.add(class_name)
                continue
            table_meta = metadata[class_name]
            class_subjects: set[str] = set()
            row_iterator = _iter_rows(
                source,
                kind=settings.source_kind,
                schema=table_meta["schema"],
                table=table_meta["table"],
                columns=table_meta["primaryKeys"],
                primary_keys=table_meta["primaryKeys"],
                fetch_size=min(10_000, max(1, remaining + 1)),
            )
            overflow = False
            try:
                for row in row_iterator:
                    class_subjects.add(str(_instance_uri(class_name, table_meta["primaryKeys"], row)))
                    if len(class_subjects) > remaining:
                        overflow = True
                        break
            finally:
                row_iterator.close()
            if overflow:
                skipped.add(class_name)
                continue
            subjects.update(class_subjects)
            validated.add(class_name)
    finally:
        source.close()
    return subjects, validated, skipped


def _record_batch(
    repository: ControlPlaneRepository,
    *,
    run_id: uuid.UUID,
    job_name: str,
    class_name: str,
    sequence_no: int,
    source_from: dict[str, Any],
    source_to: dict[str, Any],
    row_count: int,
    triple_count: int,
    path: Path,
) -> None:
    with repository.engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO graphsync.sync_batch
                    (batch_id, run_id, job_name, class_name, partition_key,
                     sequence_no, status, source_from, source_to, row_count,
                     triple_count, byte_size, sha256, storage_path,
                     attempt_count, started_at, finished_at)
                VALUES
                    (:batch_id, :run_id, :job_name, :class_name, :partition_key,
                     :sequence_no, 'verified', CAST(:source_from AS jsonb),
                     CAST(:source_to AS jsonb), :row_count, :triple_count,
                     :byte_size, :sha256, :storage_path, 1, now(), now())
                """
            ),
            {
                "batch_id": uuid.uuid4(),
                "run_id": run_id,
                "job_name": job_name,
                "class_name": class_name,
                "partition_key": class_name,
                "sequence_no": sequence_no,
                "source_from": json.dumps(source_from, ensure_ascii=False, default=str),
                "source_to": json.dumps(source_to, ensure_ascii=False, default=str),
                "row_count": row_count,
                "triple_count": triple_count,
                "byte_size": path.stat().st_size,
                "sha256": _sha256(path),
                "storage_path": str(path),
            },
        )


def _write_data_shards(
    settings: SyncSettings,
    preview_dir: Path,
    catalog: dict[str, Any],
    metadata: dict[str, dict[str, Any]],
    policies: list[dict[str, Any]],
    repository: ControlPlaneRepository,
    run_id: uuid.UUID,
    job_name: str,
    reference_validation_row_limit: int,
) -> dict[str, Any]:
    shard_dir = preview_dir / "rdf.ttl"
    shard_dir.mkdir(parents=True, exist_ok=True)
    properties_by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in catalog["properties"]:
        properties_by_class[item["class_name"]].append(item)
    relationships_by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in catalog["relationships"]:
        if item["mapping_status"] == "resolved":
            relationships_by_class[item["source_class"]].append(item)
    class_by_table = {
        str(item["physical_table"]).casefold(): item["class_name"]
        for item in catalog["classes"]
    }
    policies_by_class = _policy_by_class(policies)
    _validate_preview_policies(policies)
    reference_subjects, validated_target_classes, skipped_target_classes = _load_reference_subjects(
        settings,
        catalog,
        metadata,
        policies_by_class,
        row_limit=reference_validation_row_limit,
    )
    source = connect_source(settings)
    try:
        triple_count = 0
        instance_count = 0
        object_reference_count = 0
        dangling_references: list[dict[str, str]] = []
        dangling_reference_total = 0
        skipped_reference_total = 0
        datatype_fallbacks: Counter[tuple[str, str, str, str]] = Counter()
        semantic_digest = hashlib.sha256()
        sample_instances: list[dict[str, Any]] = []
        sample_relationships: list[dict[str, str]] = []
        class_stats: list[dict[str, Any]] = []
        for index, class_item in enumerate(catalog["classes"], start=1):
            class_name = class_item["class_name"]
            policy = policies_by_class[class_name]
            if not policy.get("enabled", True) or policy.get("effective_strategy") == "excluded":
                class_stats.append({"className": class_name, "instances": 0, "triples": 0, "shards": 0, "excluded": True})
                continue
            table_meta = metadata[class_name]
            class_properties = properties_by_class[class_name]
            mapped_columns = [
                item["physical_column"]
                for item in class_properties
                if item["mapping_status"] in {"resolved", "override"} and item.get("physical_column")
            ]
            relationship_columns = [
                item["physical_column"]
                for item in relationships_by_class[class_name]
                if item.get("physical_column")
            ]
            graph = Graph()
            _bind(graph)
            estimated_bytes = 0
            rows_in_shard = 0
            class_instances = 0
            class_triples = 0
            shard_sequence = 0
            first_pk: dict[str, Any] | None = None
            last_pk: dict[str, Any] | None = None
            previous_uri: str | None = None

            def flush_shard() -> None:
                nonlocal graph, estimated_bytes, rows_in_shard, shard_sequence
                nonlocal class_triples, first_pk, last_pk
                if rows_in_shard == 0 or first_pk is None or last_pk is None:
                    return
                shard_sequence += 1
                shard_path = shard_dir / (
                    f"{index:03d}_{re.sub(r'[^A-Za-z0-9_.-]', '_', class_name)}"
                    f".part{shard_sequence:06d}.ttl"
                )
                _serialize_deterministic_turtle(graph, shard_path)
                parsed = Graph().parse(shard_path, format="turtle")
                if len(parsed) != len(graph):
                    raise RuntimeError(f"RDF round-trip changed triples for {class_name} shard {shard_sequence}")
                semantic_digest.update(_semantic_sha256(graph).encode("ascii"))
                class_triples += len(graph)
                _record_batch(
                    repository,
                    run_id=run_id,
                    job_name=job_name,
                    class_name=class_name,
                    sequence_no=shard_sequence,
                    source_from=first_pk,
                    source_to=last_pk,
                    row_count=rows_in_shard,
                    triple_count=len(graph),
                    path=shard_path,
                )
                graph = Graph()
                _bind(graph)
                estimated_bytes = 0
                rows_in_shard = 0
                first_pk = None
                last_pk = None

            rows = _iter_rows(
                source,
                kind=settings.source_kind,
                schema=table_meta["schema"],
                table=table_meta["table"],
                columns=table_meta["primaryKeys"] + mapped_columns + relationship_columns,
                primary_keys=table_meta["primaryKeys"],
                fetch_size=int(policy["batch_rows"]),
            )
            for row in rows:
                subject = _instance_uri(class_name, table_meta["primaryKeys"], row)
                subject_text = str(subject)
                if subject_text == previous_uri:
                    raise RuntimeError(f"Duplicate instance URI: {subject_text}")
                previous_uri = subject_text
                pk_value = {column: _identifier_text(row[column]) for column in table_meta["primaryKeys"]}
                if first_pk is None:
                    first_pk = pk_value
                last_pk = pk_value
                estimated_bytes += _add_triple(graph, (subject, RDF.type, _class_uri(class_name)))
                estimated_bytes += _add_triple(
                    graph,
                    (subject, RDFS.label, Literal(_label_for_row(class_name, row, class_properties, table_meta["primaryKeys"]))),
                )
                exported_values = 0
                for prop in class_properties:
                    if prop["mapping_status"] not in {"resolved", "override"}:
                        continue
                    column = prop.get("physical_column")
                    value = row.get(column) if column else None
                    if value in (None, ""):
                        continue
                    predicate = _property_uri(class_name, prop["property_name"])
                    if prop["data_type"] == "Navigation":
                        target_class = class_by_table.get(str(prop.get("fk_table_name") or "").casefold())
                        if not target_class or len(metadata[target_class]["primaryKeys"]) != 1:
                            continue
                        target = _instance_uri(target_class, metadata[target_class]["primaryKeys"], value)
                        estimated_bytes += _add_triple(graph, (subject, predicate, target))
                        object_reference_count += 1
                        if target_class in validated_target_classes and str(target) not in reference_subjects:
                            dangling_reference_total += 1
                            if len(dangling_references) < 200:
                                dangling_references.append(
                                    {"source": str(subject), "predicate": str(predicate), "target": str(target)}
                                )
                        elif target_class not in validated_target_classes:
                            skipped_reference_total += 1
                    else:
                        literal = _literal(value, prop.get("data_type"))
                        expected_datatype = _xsd_type(prop.get("data_type"))
                        if literal.datatype != expected_datatype:
                            datatype_fallbacks[
                                (
                                    class_name,
                                    prop["property_name"],
                                    str(expected_datatype),
                                    str(literal.datatype),
                                )
                            ] += 1
                        estimated_bytes += _add_triple(graph, (subject, predicate, literal))
                    exported_values += 1
                for relation in relationships_by_class[class_name]:
                    value = row.get(relation.get("physical_column"))
                    target_class = relation["target_class"]
                    if value in (None, "") or len(metadata[target_class]["primaryKeys"]) != 1:
                        continue
                    target = _instance_uri(target_class, metadata[target_class]["primaryKeys"], value)
                    predicate = _relationship_uri(
                        relation["source_class"], relation["relationship_name"], relation["target_class"]
                    )
                    estimated_bytes += _add_triple(graph, (subject, predicate, target))
                    object_reference_count += 1
                    if target_class in validated_target_classes and str(target) not in reference_subjects:
                        dangling_reference_total += 1
                        if len(dangling_references) < 200:
                            dangling_references.append(
                                {"source": str(subject), "predicate": str(predicate), "target": str(target)}
                            )
                    elif target_class not in validated_target_classes:
                        skipped_reference_total += 1
                    if len(sample_relationships) < 20:
                        sample_relationships.append(
                            {
                                "sourceClass": class_name,
                                "relationship": relation["relationship_name"],
                                "targetClass": target_class,
                                "source": str(subject),
                                "target": str(target),
                            }
                        )
                if len(sample_instances) < 20 or class_name in {"Product", "MfgOrder"}:
                    if len([item for item in sample_instances if item["className"] == class_name]) < 3:
                        sample_instances.append(
                            {
                                "className": class_name,
                                "uri": str(subject),
                                "label": _label_for_row(class_name, row, class_properties, table_meta["primaryKeys"]),
                                "exportedValues": exported_values,
                            }
                        )
                rows_in_shard += 1
                class_instances += 1
                instance_count += 1
                if (
                    rows_in_shard >= int(policy["batch_rows"])
                    or estimated_bytes >= int(policy["target_shard_bytes"])
                ):
                    flush_shard()
            flush_shard()
            triple_count += class_triples
            class_stats.append(
                {
                    "className": class_name,
                    "instances": class_instances,
                    "triples": class_triples,
                    "shards": shard_sequence,
                    "strategy": policy.get("effective_strategy"),
                }
            )
    finally:
        source.close()
    return {
        "dataTriples": triple_count,
        "instances": instance_count,
        "objectReferences": object_reference_count,
        "danglingReferencesTotal": dangling_reference_total,
        "danglingReferences": dangling_references,
        "referenceValidation": {
            "rowLimit": reference_validation_row_limit,
            "validatedTargetClasses": sorted(validated_target_classes),
            "skippedTargetClasses": sorted(skipped_target_classes),
            "skippedReferences": skipped_reference_total,
        },
        "datatypeFallbacks": [
            {
                "className": key[0],
                "propertyName": key[1],
                "expectedDatatype": key[2],
                "actualDatatype": key[3],
                "instances": count,
            }
            for key, count in sorted(datatype_fallbacks.items())
        ],
        "semanticSha256": semantic_digest.hexdigest(),
        "classStats": class_stats,
        "sampleInstances": sample_instances,
        "sampleRelationships": sample_relationships,
        "shardFiles": len(list(shard_dir.glob("*.ttl"))),
    }


def _write_zip(preview_dir: Path) -> Path:
    zip_path = preview_dir / "camstar_full_data.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        directory = zipfile.ZipInfo("rdf.ttl/", date_time=(1980, 1, 1, 0, 0, 0))
        directory.create_system = 3
        directory.external_attr = ((stat.S_IFDIR | 0o755) << 16) | 0x10
        archive.writestr(directory, b"")
        for file_path in sorted((preview_dir / "rdf.ttl").glob("*.ttl")):
            info = zipfile.ZipInfo(
                filename=f"rdf.ttl/{file_path.name}",
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, file_path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(zip_path) as archive:
        invalid = [
            name for name in archive.namelist()
            if name != "rdf.ttl/"
            and (not name.startswith("rdf.ttl/") or not name.endswith(".ttl"))
        ]
        if invalid:
            raise RuntimeError(f"Invalid Graph Studio RDF ZIP members: {invalid}")
        if archive.testzip() is not None:
            raise RuntimeError("RDF ZIP CRC validation failed")
    return zip_path


def _report_markdown(manifest: dict[str, Any]) -> str:
    top_classes = sorted(
        (item for item in manifest["data"]["classStats"] if item["instances"]),
        key=lambda item: item["instances"],
        reverse=True,
    )[:20]
    lines = [
        "# Camstar 全量 RDF 预览报告",
        "",
        f"- Run ID: `{manifest['runId']}`",
        f"- 目标 Graphmart: `{manifest['targetGraphmart']}`",
        f"- 映射目录: `{manifest['catalog']['snapshotId']}`",
        f"- 映射覆盖率: **{manifest['catalog']['coveragePercent']}%**",
        f"- 本体三元组: **{manifest['model']['triples']:,}**",
        f"- 实例: **{manifest['data']['instances']:,}**",
        f"- 数据三元组: **{manifest['data']['dataTriples']:,}**",
        f"- RDF 数据分片: **{manifest['data']['shardFiles']}**",
        f"- 最大驻留批次: **{manifest['policies']['maximumBatchRows']:,} 行**",
        "",
        "## 发布门禁",
        "",
        "本预览未调用 Graph Studio 写接口。以下待审项未自动猜测：",
        "",
        f"- 未解析属性: **{manifest['catalog']['unresolvedProperties']}**",
        f"- 多候选关系: **{manifest['catalog']['ambiguousRelationships']}**",
        f"- 未解析关系: **{manifest['catalog']['unresolvedRelationships']}**",
        f"- 引用到未导出实例: **{manifest['data']['danglingReferencesTotal']}**",
        f"- 因目标类过大跳过精确校验的引用: **{manifest['data']['referenceValidation']['skippedReferences']}**",
        f"- 数据类型回退: **{sum(item['instances'] for item in manifest['data']['datatypeFallbacks'])}** 个值 / **{len(manifest['data']['datatypeFallbacks'])}** 个属性",
        "",
        "## 非空类 Top 20",
        "",
        "| 本体类 | 实例 | 三元组 |",
        "|---|---:|---:|",
    ]
    lines.extend(
        f"| {item['className']} | {item['instances']:,} | {item['triples']:,} |"
        for item in top_classes
    )
    lines.extend(
        [
            "",
            "## 产物",
            "",
            f"- Model: `{manifest['files']['model']}`",
            f"- Data ZIP: `{manifest['files']['dataZip']}`",
            f"- Samples: `{manifest['files']['samples']}`",
            f"- Manifest: `{manifest['files']['manifest']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _record_validation(
    connection,
    *,
    run_id: uuid.UUID,
    rule: str,
    passed: bool,
    message: str,
    severity: str = "error",
    details: dict[str, Any] | None = None,
) -> None:
    connection.execute(
        text(
            """
            INSERT INTO graphsync.validation_result
                (validation_id, run_id, phase, rule_key, severity, passed, message, details)
            VALUES
                (:id, :run_id, 'preview', :rule, :severity, :passed, :message,
                 CAST(:details AS jsonb))
            """
        ),
        {
            "id": uuid.uuid4(),
            "run_id": run_id,
            "rule": rule,
            "severity": severity,
            "passed": passed,
            "message": message,
            "details": json.dumps(details or {}, ensure_ascii=False),
        },
    )


def build_full_preview(
    base_settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    job_name: str = "camstar-full",
) -> dict[str, Any]:
    """Build and validate the full RDF package without contacting Graph Studio APIs."""
    run_id = uuid.uuid4()
    preview_dir = PREVIEW_ROOT / str(run_id)
    preview_dir.mkdir(parents=True, exist_ok=False)
    lock_name = f"graphsync:preview:{job_name}"
    with repository.engine.connect() as control:
        acquired = control.execute(
            text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"), {"name": lock_name}
        ).scalar_one()
        if not acquired:
            raise RuntimeError(f"A preview is already running for {job_name}")
        try:
            job_exists = control.execute(
                text("SELECT EXISTS(SELECT 1 FROM graphsync.sync_job WHERE job_name=:job_name)"),
                {"job_name": job_name},
            ).scalar_one()
            if not job_exists:
                raise KeyError(job_name)
            control.execute(
                text(
                    """
                    INSERT INTO graphsync.sync_run (run_id, job_name, status, trigger_type)
                    VALUES (:run_id, :job_name, 'extracting', 'dry_run')
                    """
                ),
                {"run_id": run_id, "job_name": job_name},
            )
            control.commit()
            try:
                settings = resolved_settings(base_settings, repository)
                catalog = _load_catalog(repository)
                policies = repository.list_table_policies(job_name)
                reference_validation_row_limit = int(
                    control.execute(
                        text(
                            """
                            SELECT coalesce(
                                (SELECT (value #>> '{}')::bigint FROM graphsync.app_setting
                                 WHERE setting_key='sync.reference_validation_row_limit'),
                                1000000
                            )
                            """
                        )
                    ).scalar_one()
                )
                descriptions = _load_descriptions(settings)
                metadata = _source_metadata(settings, catalog["classes"])

                model = _build_model(catalog, descriptions)
                model_path = preview_dir / "camstar_full_ontology.ttl"
                _serialize_deterministic_turtle(model, model_path)
                parsed_model = Graph().parse(model_path, format="turtle")
                if len(parsed_model) != len(model):
                    raise RuntimeError("Ontology RDF round-trip changed the triple count")

                data_result = _write_data_shards(
                    settings,
                    preview_dir,
                    catalog,
                    metadata,
                    policies,
                    repository,
                    run_id,
                    job_name,
                    reference_validation_row_limit,
                )
                zip_path = _write_zip(preview_dir)
                samples_path = preview_dir / "samples.json"
                samples_path.write_text(
                    json.dumps(
                        {
                            "instances": data_result["sampleInstances"],
                            "relationships": data_result["sampleRelationships"],
                            "danglingReferences": data_result["danglingReferences"],
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                snapshot = catalog["snapshot"]
                property_status = Counter(item["mapping_status"] for item in catalog["properties"])
                relationship_status = Counter(item["mapping_status"] for item in catalog["relationships"])
                manifest_path = preview_dir / "manifest.json"
                report_path = preview_dir / "preview_report.md"
                manifest: dict[str, Any] = {
                    "previewOnly": True,
                    "graphStudioMutated": False,
                    "runId": str(run_id),
                    "jobName": job_name,
                    "targetGraphmart": settings.graphmart_uri,
                    "ontologyUri": str(ONTOLOGY_URI),
                    "policies": {
                        "explicitlyConfigured": sum(bool(item["explicitly_configured"]) for item in policies),
                        "requiresReview": sum(bool(item["requires_review"]) for item in policies),
                        "maximumBatchRows": max((int(item["batch_rows"]) for item in policies), default=0),
                        "strategyCounts": dict(
                            Counter(item.get("effective_strategy") or "review_required" for item in policies)
                        ),
                    },
                    "catalog": {
                        "snapshotId": str(snapshot["snapshot_id"]),
                        "catalogHash": snapshot["catalog_hash"],
                        "coveragePercent": float(snapshot["mapping_coverage"]),
                        "classes": len(catalog["classes"]),
                        "properties": len(catalog["properties"]),
                        "relationships": len(catalog["relationships"]),
                        "resolvedProperties": property_status["resolved"] + property_status["override"],
                        "unresolvedProperties": property_status["unresolved"],
                        "resolvedRelationships": relationship_status["resolved"],
                        "ambiguousRelationships": relationship_status["ambiguous"],
                        "unresolvedRelationships": relationship_status["unresolved"],
                    },
                    "model": {
                        "triples": len(model),
                        "classes": len(set(model.subjects(RDF.type, OWL.Class))),
                        "objectProperties": len(set(model.subjects(RDF.type, OWL.ObjectProperty))),
                        "datatypeProperties": len(set(model.subjects(RDF.type, OWL.DatatypeProperty))),
                        "semanticSha256": _semantic_sha256(model),
                    },
                    "data": data_result,
                    "files": {
                        "model": str(model_path),
                        "dataZip": str(zip_path),
                        "samples": str(samples_path),
                        "manifest": str(manifest_path),
                        "report": str(report_path),
                    },
                    "hashes": {
                        "modelSha256": _sha256(model_path),
                        "dataZipSha256": _sha256(zip_path),
                        "samplesSha256": _sha256(samples_path),
                    },
                }
                manifest_path.write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n",
                    encoding="utf-8",
                )
                report_path.write_text(_report_markdown(manifest), encoding="utf-8")

                validations = [
                    ("model-class-count", manifest["model"]["classes"] == manifest["catalog"]["classes"], "Ontology class count matches the catalog"),
                    ("rdf-round-trip", True, "Ontology and every data shard parsed successfully"),
                    ("zip-layout", True, "Every ZIP member is a Turtle file below rdf.ttl/"),
                    ("unique-instance-uri", True, "All exported instance URIs are unique"),
                    ("no-graphstudio-mutation", True, "Preview module does not invoke Graph Studio APIs"),
                ]
                failed = [rule for rule, passed, _ in validations if not passed]
                for rule, passed, message in validations:
                    _record_validation(control, run_id=run_id, rule=rule, passed=passed, message=message)
                policy_lookup = _policy_by_class(policies)
                expected_instances = sum(
                    int(item.get("approximate_rows") or 0)
                    for item in catalog["classes"]
                    if policy_lookup[item["class_name"]].get("effective_strategy") != "excluded"
                    and policy_lookup[item["class_name"]].get("enabled", True)
                )
                _record_validation(
                    control,
                    run_id=run_id,
                    rule="instance-row-count",
                    passed=data_result["instances"] == expected_instances,
                    message="Exported instances match the catalog source row estimate",
                    severity="warning",
                    details={"expected": expected_instances, "actual": data_result["instances"]},
                )
                _record_validation(
                    control,
                    run_id=run_id,
                    rule="mapping-review-queue",
                    passed=not (
                        manifest["catalog"]["unresolvedProperties"]
                        or manifest["catalog"]["ambiguousRelationships"]
                        or manifest["catalog"]["unresolvedRelationships"]
                    ),
                    message="Unresolved mappings are excluded from instance data and require review",
                    severity="warning",
                    details={
                        "unresolvedProperties": manifest["catalog"]["unresolvedProperties"],
                        "ambiguousRelationships": manifest["catalog"]["ambiguousRelationships"],
                        "unresolvedRelationships": manifest["catalog"]["unresolvedRelationships"],
                    },
                )
                _record_validation(
                    control,
                    run_id=run_id,
                    rule="reference-integrity",
                    passed=not data_result["danglingReferencesTotal"],
                    message="Object references resolve to exported subjects",
                    severity="warning",
                    details={"danglingReferences": data_result["danglingReferencesTotal"]},
                )
                _record_validation(
                    control,
                    run_id=run_id,
                    rule="reference-validation-coverage",
                    passed=not data_result["referenceValidation"]["skippedReferences"],
                    message="All object references were eligible for exact in-memory validation",
                    severity="warning",
                    details=data_result["referenceValidation"],
                )
                _record_validation(
                    control,
                    run_id=run_id,
                    rule="datatype-compatibility",
                    passed=not data_result["datatypeFallbacks"],
                    message="Source values are compatible with declared ontology datatypes",
                    severity="warning",
                    details={"fallbacks": data_result["datatypeFallbacks"]},
                )
                if failed:
                    raise RuntimeError(f"Preview validation failed: {failed}")

                total_triples = len(model) + data_result["dataTriples"]
                control.execute(
                    text(
                        """
                        UPDATE graphsync.sync_run
                        SET status='succeeded', finished_at=now(), row_count=:rows,
                            triple_count=:triples, ontology_hash=:ontology_hash,
                            source_schema_hash=:schema_hash, manifest_hash=:manifest_hash,
                            metrics=CAST(:metrics AS jsonb)
                        WHERE run_id=:run_id
                        """
                    ),
                    {
                        "run_id": run_id,
                        "rows": data_result["instances"],
                        "triples": total_triples,
                        "ontology_hash": manifest["hashes"]["modelSha256"],
                        "schema_hash": snapshot["catalog_hash"],
                        "manifest_hash": _sha256(manifest_path),
                        "metrics": json.dumps(
                            {
                                "operation": "full_rdf_preview",
                                "previewOnly": True,
                                "modelTriples": len(model),
                                "dataTriples": data_result["dataTriples"],
                                "shardFiles": data_result["shardFiles"],
                                "streaming": True,
                                "maximumBatchRows": manifest["policies"]["maximumBatchRows"],
                                "danglingReferences": data_result["danglingReferencesTotal"],
                                "datatypeFallbacks": sum(
                                    item["instances"] for item in data_result["datatypeFallbacks"]
                                ),
                            }
                        ),
                    },
                )
                artifacts = [
                    ("model", model_path, str(ONTOLOGY_URI)),
                    ("rdf_archive", zip_path, None),
                    ("manifest", manifest_path, None),
                    ("verification", report_path, None),
                ]
                for artifact_type, path, uri in artifacts:
                    control.execute(
                        text(
                            """
                            INSERT INTO graphsync.artifact
                                (artifact_id, run_id, artifact_type, uri, storage_path,
                                 sha256, byte_size, metadata)
                            VALUES
                                (:id, :run_id, :type, :uri, :path, :sha256, :size,
                                 CAST(:metadata AS jsonb))
                            """
                        ),
                        {
                            "id": uuid.uuid4(),
                            "run_id": run_id,
                            "type": artifact_type,
                            "uri": uri,
                            "path": str(path),
                            "sha256": _sha256(path),
                            "size": path.stat().st_size,
                            "metadata": json.dumps({"previewOnly": True}),
                        },
                    )
                control.commit()
                return manifest
            except Exception as exc:
                control.rollback()
                control.execute(
                    text(
                        """
                        UPDATE graphsync.sync_run
                        SET status='failed', finished_at=now(),
                            error=CAST(:error AS jsonb)
                        WHERE run_id=:run_id
                        """
                    ),
                    {
                        "run_id": run_id,
                        "error": json.dumps({"type": type(exc).__name__, "message": str(exc)[:4000]}),
                    },
                )
                control.commit()
                raise
        finally:
            control.execute(
                text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"), {"name": lock_name}
            )
            control.commit()
