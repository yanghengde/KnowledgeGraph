#!/usr/bin/env python3
"""Export the Product/MfgOrder ontology subgraph to RDF and optionally import it.

Credentials are read from the repository-local .env file. Secret values are never
printed. The default mode only builds and validates local RDF artifacts; --upload
performs the Graph Studio API mutations.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import decimal
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
import pymssql
from neo4j import GraphDatabase
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD
from rdflib.namespace import OWL, SKOS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "graphstudio" / "opcenter2607_product_mfgorder"
MODEL_FILE = OUTPUT_DIR / "product_mfgorder_ontology.ttl"
DATA_FILE = OUTPUT_DIR / "product_mfgorder_data.ttl"
ZIP_FILE = OUTPUT_DIR / "product_mfgorder_data.zip"
MANIFEST_FILE = OUTPUT_DIR / "manifest.json"

GRAPHMART_URI = "http://cambridgesemantics.com/Graphmart/fa5ee4d00d9744c996165abcdec9a647"
GRAPHMART_ID = GRAPHMART_URI.rsplit("/", 1)[-1]
ONTOLOGY_URI = URIRef("https://opcenter.siemens.com/ontology/camstar/2607/ProductMfgOrder")
ONT = Namespace(str(ONTOLOGY_URI) + "#")
DATA = Namespace("https://opcenter.siemens.com/data/camstar/2607/ontology/")
GM_SELF = "http://cambridgesemantics.com/ontologies/Graphmarts#Self"
TARGET_CLASSES = ("Product", "MfgOrder")
FIELDS_CSV = ROOT / "docs" / "Database_Fields.csv"


def load_env() -> None:
    env_path = ROOT / ".env"
    for raw in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def fetch_subgraph() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        classes = [
            dict(record["props"])
            for record in session.run(
                """
                MATCH (c:OntologyClass)
                WHERE c.name IN $names
                RETURN properties(c) AS props
                ORDER BY c.name
                """,
                names=list(TARGET_CLASSES),
            )
        ]
        properties = [
            {"className": record["className"], **dict(record["props"])}
            for record in session.run(
                """
                MATCH (c:OntologyClass)-[:HAS_PROPERTY]->(p:OntologyProperty)
                WHERE c.name IN $names
                RETURN c.name AS className, properties(p) AS props
                ORDER BY c.name, p.name
                """,
                names=list(TARGET_CLASSES),
            )
        ]
        relationships = [
            {
                "source": record["source"],
                "target": record["target"],
                **dict(record["props"]),
            }
            for record in session.run(
                """
                MATCH (a:OntologyClass)-[r:ONTOLOGY_RELATION]->(b:OntologyClass)
                WHERE a.name IN $names AND b.name IN $names
                RETURN a.name AS source, b.name AS target, properties(r) AS props
                ORDER BY a.name, r.name, b.name
                """,
                names=list(TARGET_CLASSES),
            )
        ]
    driver.close()
    return classes, properties, relationships


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def load_field_catalog() -> dict[str, dict[str, str]]:
    with FIELDS_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return {row["FieldID"]: row for row in csv.DictReader(handle) if row.get("FieldID")}


def infer_physical_column(property_item: dict[str, Any], columns: list[str], class_name: str) -> str | None:
    prop_name = str(property_item["name"])
    prop_norm = normalize_token(prop_name)
    is_navigation = property_item.get("dataType") == "Navigation"

    exact = [column for column in columns if normalize_token(column) == prop_norm]
    if len(exact) == 1:
        return exact[0]
    if prop_norm == "name":
        class_name_column = normalize_token(class_name + "Name")
        matches = [column for column in columns if normalize_token(column) == class_name_column]
        if len(matches) == 1:
            return matches[0]

    scored: list[tuple[int, str]] = []
    for column in columns:
        candidate = str(column)
        variants: list[tuple[int, str]] = [(10, candidate)]
        if candidate.lower().startswith("es_"):
            variants.append((20, candidate[3:]))
        for prefix in ("ss_",):
            if candidate.lower().startswith(prefix):
                variants.append((20, candidate[len(prefix):]))
        for score, variant in list(variants):
            if is_navigation:
                for suffix in ("DefId", "RefId", "Id"):
                    if variant.lower().endswith(suffix.lower()):
                        variants.append((score + 5, variant[: -len(suffix)]))
        for score, variant in variants:
            if normalize_token(variant) == prop_norm:
                scored.append((score, column))
    if not scored:
        return None
    best_score = min(score for score, _ in scored)
    best = sorted({column for score, column in scored if score == best_score})
    return best[0] if len(best) == 1 else None


def fetch_source_data(
    properties: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[tuple[str, str], dict[str, Any]], dict[str, str]]:
    field_catalog = load_field_catalog()
    connection = pymssql.connect(
        server=os.environ["SRC_DB_HOST"],
        port=int(os.getenv("SRC_DB_PORT", "1433")),
        user=os.environ["SRC_DB_USER"],
        password=os.environ["SRC_DB_PASSWORD"],
        database=os.environ["SRC_DB_NAME"],
        login_timeout=20,
        timeout=120,
    )
    cursor = connection.cursor(as_dict=True)
    rows_by_class: dict[str, list[dict[str, Any]]] = {}
    primary_keys: dict[str, str] = {}
    columns_by_class: dict[str, list[str]] = {}
    for class_name in TARGET_CLASSES:
        cursor.execute(
            """
            SELECT TOP 1 TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME=%s
            ORDER BY CASE WHEN TABLE_SCHEMA='dbo' THEN 0 ELSE 1 END, TABLE_SCHEMA
            """,
            (class_name,),
        )
        table = cursor.fetchone()
        if not table:
            raise RuntimeError(f"Source table not found: {class_name}")
        schema = str(table["TABLE_SCHEMA"])
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$#]*", schema):
            raise RuntimeError(f"Unsafe source schema: {schema}")
        cursor.execute(
            """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION
            """,
            (schema, class_name),
        )
        columns = [str(row["COLUMN_NAME"]) for row in cursor.fetchall()]
        columns_by_class[class_name] = columns
        cursor.execute(
            """
            SELECT kcu.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
              ON tc.CONSTRAINT_NAME=kcu.CONSTRAINT_NAME AND tc.TABLE_SCHEMA=kcu.TABLE_SCHEMA
            WHERE tc.TABLE_SCHEMA=%s AND tc.TABLE_NAME=%s AND tc.CONSTRAINT_TYPE='PRIMARY KEY'
            ORDER BY kcu.ORDINAL_POSITION
            """,
            (schema, class_name),
        )
        pk_rows = cursor.fetchall()
        if len(pk_rows) != 1:
            raise RuntimeError(f"Expected one primary key for {schema}.{class_name}, found {pk_rows!r}")
        primary_keys[class_name] = str(pk_rows[0]["COLUMN_NAME"])
        cursor.execute(f"SELECT * FROM [{schema}].[{class_name}]")
        rows_by_class[class_name] = [dict(row) for row in cursor.fetchall()]
    connection.close()

    property_map: dict[tuple[str, str], dict[str, Any]] = {}
    for item in properties:
        class_name = item["className"]
        source_field_id = str(item.get("sourceFieldId") or "")
        catalog_item = field_catalog.get(source_field_id, {})
        catalog_field = catalog_item.get("FieldName")
        column = None
        if catalog_field:
            column = next(
                (candidate for candidate in columns_by_class[class_name] if candidate.casefold() == catalog_field.casefold()),
                None,
            )
        if not column:
            column = infer_physical_column(item, columns_by_class[class_name], class_name)
        property_map[(class_name, item["name"])] = {
            **item,
            "physicalField": column,
            "fkTableName": catalog_item.get("FKTableName") or "",
            "fkFieldName": catalog_item.get("FKFieldName") or "",
        }
    return rows_by_class, property_map, primary_keys


def safe_segment(value: str) -> str:
    return quote(value, safe="-._~")


def add_literal(graph: Graph, subject: URIRef, predicate: URIRef, value: Any) -> None:
    if value is None or value == "":
        return
    if isinstance(value, bool):
        graph.add((subject, predicate, Literal(value, datatype=XSD.boolean)))
    elif isinstance(value, int):
        graph.add((subject, predicate, Literal(value, datatype=XSD.integer)))
    elif isinstance(value, decimal.Decimal):
        graph.add((subject, predicate, Literal(value, datatype=XSD.decimal)))
    elif isinstance(value, float):
        graph.add((subject, predicate, Literal(value, datatype=XSD.double)))
    elif isinstance(value, dt.datetime):
        graph.add((subject, predicate, Literal(value.isoformat(), datatype=XSD.dateTime)))
    elif isinstance(value, dt.date):
        graph.add((subject, predicate, Literal(value.isoformat(), datatype=XSD.date)))
    elif isinstance(value, bytes):
        graph.add((subject, predicate, Literal(value.hex())))
    else:
        graph.add((subject, predicate, Literal(str(value).rstrip())))


def xsd_type(data_type: str) -> URIRef:
    return {
        "Boolean": XSD.boolean,
        "Integer": XSD.integer,
        "Float": XSD.double,
        "DateTime": XSD.dateTime,
        "Date": XSD.date,
        "Time": XSD.time,
        "String": XSD.string,
        "Array": XSD.string,
        "SubentityList": XSD.string,
    }.get(data_type, XSD.string)


def bind_prefixes(graph: Graph) -> None:
    graph.bind("cam", ONT)
    graph.bind("camdata", DATA)
    graph.bind("owl", OWL)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("skos", SKOS)
    graph.bind("xsd", XSD)


def identifier_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.hex()
    return str(value).rstrip()


def instance_uri(class_name: str, identifier: Any) -> URIRef:
    return URIRef(str(DATA) + safe_segment(class_name) + "/" + safe_segment(identifier_text(identifier)))


def relationship_property_name(relationship_name: str) -> str:
    words = relationship_name.removeprefix("HAS_").lower().split("_")
    return words[0] + "".join(word.title() for word in words[1:])


def build_graphs(
    classes: list[dict[str, Any]],
    properties: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    rows_by_class: dict[str, list[dict[str, Any]]],
    property_map: dict[tuple[str, str], dict[str, Any]],
    primary_keys: dict[str, str],
) -> tuple[Graph, Graph]:
    model = Graph()
    data = Graph()
    bind_prefixes(model)
    bind_prefixes(data)

    model.add((ONTOLOGY_URI, RDF.type, OWL.Ontology))
    model.add((ONTOLOGY_URI, RDFS.label, Literal("Opcenter 2607 Product and MfgOrder Ontology", lang="en")))
    model.add((ONTOLOGY_URI, RDFS.comment, Literal("Subset exported from CamstarOntology Neo4j.")))

    for annotation_name in ("required", "sourceFieldId", "physicalField", "cardinality"):
        model.add((ONT[annotation_name], RDF.type, OWL.AnnotationProperty))
        model.add((ONT[annotation_name], RDFS.label, Literal(annotation_name)))

    for item in classes:
        class_name = item["name"]
        class_uri = ONT[class_name]
        model.add((class_uri, RDF.type, OWL.Class))
        model.add((class_uri, RDFS.label, Literal(class_name, lang="en")))
        if item.get("chineseName"):
            model.add((class_uri, SKOS.prefLabel, Literal(item["chineseName"], lang="zh")))
        if item.get("description"):
            model.add((class_uri, RDFS.comment, Literal(item["description"])))

    for item in properties:
        class_name = item["className"]
        prop_name = item["name"]
        prop_uri = ONT[f"{class_name}_{prop_name}"]
        is_navigation = item.get("dataType") == "Navigation"
        model.add((prop_uri, RDF.type, OWL.ObjectProperty if is_navigation else OWL.DatatypeProperty))
        model.add((prop_uri, RDFS.domain, ONT[class_name]))
        if not is_navigation:
            model.add((prop_uri, RDFS.range, xsd_type(str(item.get("dataType", "String")))))
        model.add((prop_uri, RDFS.label, Literal(prop_name)))
        if item.get("description"):
            model.add((prop_uri, RDFS.comment, Literal(item["description"])))
        add_literal(model, prop_uri, ONT.required, bool(item.get("required", False)))
        add_literal(model, prop_uri, ONT.sourceFieldId, item.get("sourceFieldId"))
        add_literal(model, prop_uri, ONT.physicalField, property_map[(class_name, prop_name)].get("physicalField"))

    for item in relationships:
        rel_name = item["name"]
        rel_uri = ONT[f"REL_{rel_name}"]
        model.add((rel_uri, RDF.type, OWL.ObjectProperty))
        model.add((rel_uri, RDFS.domain, ONT[item["source"]]))
        model.add((rel_uri, RDFS.range, ONT[item["target"]]))
        model.add((rel_uri, RDFS.label, Literal(rel_name)))
        if item.get("description"):
            model.add((rel_uri, RDFS.comment, Literal(item["description"])))
        add_literal(model, rel_uri, ONT.cardinality, item.get("cardinality"))

    included_ids = {
        class_name: {
            identifier_text(row[primary_keys[class_name]])
            for row in rows
            if row.get(primary_keys[class_name]) is not None
        }
        for class_name, rows in rows_by_class.items()
    }
    for class_name, rows in rows_by_class.items():
        pk = primary_keys[class_name]
        class_properties = [item for item in properties if item["className"] == class_name]
        for row in rows:
            if row.get(pk) is None:
                continue
            subject = instance_uri(class_name, row[pk])
            data.add((subject, RDF.type, ONT[class_name]))
            data.add((subject, RDFS.label, Literal(f"{class_name} {identifier_text(row[pk])}")))
            for prop in class_properties:
                mapping = property_map[(class_name, prop["name"])]
                column = mapping.get("physicalField")
                if not column or row.get(column) is None:
                    continue
                prop_uri = ONT[f"{class_name}_{prop['name']}"]
                value = row[column]
                if prop.get("dataType") == "Navigation":
                    fk_table = mapping.get("fkTableName") or prop["name"]
                    target_name = next(
                        (candidate for candidate in TARGET_CLASSES if normalize_token(candidate) == normalize_token(fk_table)),
                        str(fk_table).removeprefix("A_") or prop["name"],
                    )
                    data.add((subject, prop_uri, instance_uri(target_name, value)))
                else:
                    add_literal(data, subject, prop_uri, value)

    for relation in relationships:
        source_class = relation["source"]
        target_class = relation["target"]
        prop_name = relationship_property_name(relation["name"])
        mapping = property_map.get((source_class, prop_name))
        if not mapping or not mapping.get("physicalField"):
            raise RuntimeError(f"Could not map relationship {relation['name']} to a physical field")
        column = mapping["physicalField"]
        for row in rows_by_class[source_class]:
            source_id = row.get(primary_keys[source_class])
            target_id = row.get(column)
            if source_id is None or target_id is None:
                continue
            if identifier_text(target_id) not in included_ids[target_class]:
                continue
            data.add(
                (
                    instance_uri(source_class, source_id),
                    ONT[f"REL_{relation['name']}"],
                    instance_uri(target_class, target_id),
                )
            )

    return model, data


def write_and_validate(model: Graph, data: Graph, summary: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model.serialize(destination=MODEL_FILE, format="turtle")
    data.serialize(destination=DATA_FILE, format="turtle")

    with zipfile.ZipFile(ZIP_FILE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(DATA_FILE, arcname=f"rdf.ttl/{DATA_FILE.name}")

    parsed_model = Graph().parse(MODEL_FILE, format="turtle")
    parsed_data = Graph().parse(DATA_FILE, format="turtle")
    if len(parsed_model) != len(model) or len(parsed_data) != len(data):
        raise RuntimeError("RDF round-trip validation changed the triple count")

    summary.update(
        {
            "ontologyUri": str(ONTOLOGY_URI),
            "modelTriples": len(model),
            "dataTriples": len(data),
            "modelFile": str(MODEL_FILE),
            "dataFile": str(DATA_FILE),
            "zipFile": str(ZIP_FILE),
        }
    )
    MANIFEST_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def response_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text.strip()


def require_ok(response: requests.Response, action: str) -> Any:
    if not response.ok:
        body = response.text[:4000]
        raise RuntimeError(f"{action} failed: HTTP {response.status_code}: {body}")
    return response_json(response)


def find_uri(value: Any, preferred_keys: tuple[str, ...] = ("uri", "datasetUri", "layerUri", "stepUri")) -> str | None:
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return value
    if isinstance(value, dict):
        for key in preferred_keys:
            found = value.get(key)
            if isinstance(found, str) and found.startswith(("http://", "https://")):
                return found
        for nested in value.values():
            found = find_uri(nested, preferred_keys)
            if found:
                return found
    if isinstance(value, list):
        for nested in value:
            found = find_uri(nested, preferred_keys)
            if found:
                return found
    return None


def import_to_graphstudio(summary: dict[str, Any]) -> dict[str, Any]:
    base = os.environ["GRAPHSTUDIO_BASE_URL"].rstrip("/")
    session = requests.Session()
    session.auth = (os.environ["GRAPHSTUDIO_USER"], os.environ["GRAPHSTUDIO_PASSWORD"])
    session.headers.update({"Accept": "application/json", "Accept-Encoding": "identity"})

    encoded_graphmart = quote(GRAPHMART_URI, safe="")
    current = require_ok(session.get(f"{base}/api/graphmarts/{encoded_graphmart}", timeout=60), "Read graphmart")
    if current.get("title") != "Opcenter2607":
        raise RuntimeError(f"Target graphmart mismatch: {current!r}")

    with MODEL_FILE.open("rb") as handle:
        model_result = require_ok(
            session.post(
                f"{base}/api/models",
                files={"modelData": (MODEL_FILE.name, handle, "text/turtle")},
                timeout=180,
            ),
            "Upload model",
        )

    model_uri = str(ONTOLOGY_URI)
    summary["modelUploadResponse"] = model_result
    summary["modelUri"] = model_uri

    datasets = require_ok(
        session.get(f"{base}/api/datasets", params={"limit": 500, "expand": "dataLocation"}, timeout=120),
        "Discover shared file storage",
    )
    shared_connections: dict[str, int] = {}
    for dataset in datasets:
        location = dataset.get("dataLocation") or {}
        if isinstance(location, list):
            location = location[0] if location else {}
        connection_uri = location.get("fileConnection")
        if connection_uri and "DataSources#FileConnection_" not in connection_uri:
            shared_connections[connection_uri] = shared_connections.get(connection_uri, 0) + 1
    if not shared_connections:
        raise RuntimeError("No Graph Lakehouse-accessible shared file connection was found")
    file_connection = max(shared_connections, key=shared_connections.get)

    multipart: list[tuple[str, tuple[Any, ...]]] = [
        ("title", (None, "Opcenter2607 Product MfgOrder Data")),
        ("description", (None, "Product and MfgOrder source records from Camstar SQL Server")),
        ("models", (None, model_uri)),
        ("fileConnection", (None, file_connection)),
        ("filePath", (None, "Opcenter2607/ProductMfgOrder")),
    ]
    with ZIP_FILE.open("rb") as handle:
        multipart.append(("rdfZip", (ZIP_FILE.name, handle, "application/zip")))
        dataset_result = require_ok(
            session.post(f"{base}/api/datasets/from-rdf-zip", files=multipart, timeout=300),
            "Upload RDF dataset",
        )
    dataset_uri = find_uri(dataset_result, ("uri", "datasetUri"))
    if not dataset_uri:
        raise RuntimeError(f"Dataset upload response did not contain a URI: {dataset_result!r}")
    summary["datasetUploadResponse"] = dataset_result
    summary["datasetUri"] = dataset_uri

    dataset_details = require_ok(
        session.get(
            f"{base}/api/datasets/{quote(dataset_uri, safe='')}",
            params={"expand": "catalogEntry"},
            timeout=60,
        ),
        "Read uploaded dataset",
    )
    catalog_entries = dataset_details.get("catalogEntry") or []
    if isinstance(catalog_entries, str):
        catalog_entries = [catalog_entries]
    if not catalog_entries:
        raise RuntimeError(f"Uploaded dataset has no catalogEntry: {dataset_details!r}")
    catalog_entry = catalog_entries[0]
    summary["catalogEntry"] = catalog_entry

    layer_payload = {
        "title": "Product and MfgOrder",
        "description": "Camstar Product and MfgOrder ontology metadata",
        "visible": True,
        "defaultSelected": True,
        "autoDeployOntologyChanges": True,
        "model": [model_uri],
    }
    layer_result = require_ok(
        session.post(
            f"{base}/api/graphmarts/{encoded_graphmart}/layers",
            json=layer_payload,
            timeout=60,
        ),
        "Create graphmart layer",
    )
    layer_uri = find_uri(layer_result, ("uri", "layerUri"))
    if not layer_uri:
        raise RuntimeError(f"Layer creation response did not contain a URI: {layer_result!r}")
    summary["layerUri"] = layer_uri

    step_payload = {
        "title": "Load Product and MfgOrder RDF",
        "type": "LoadDatasetStep",
        "gmLinkedDataset": catalog_entry,
        "source": [GM_SELF],
        "ontology": [model_uri],
        "ignoreLoadErrors": False,
    }
    step_result = require_ok(
        session.post(
            f"{base}/api/layers/{quote(layer_uri, safe='')}/steps",
            json=step_payload,
            timeout=60,
        ),
        "Create load dataset step",
    )
    step_uri = find_uri(step_result, ("uri", "stepUri"))
    if not step_uri:
        raise RuntimeError(f"Step creation response did not contain a URI: {step_result!r}")
    summary["stepUri"] = step_uri

    reload_result = require_ok(
        session.post(
            f"{base}/api/graphmarts/{encoded_graphmart}/reload",
            json={"inDesignMode": True, "deployOnActivation": True},
            timeout=180,
        ),
        "Reload graphmart",
    )
    summary["reloadResponse"] = reload_result

    deadline = time.monotonic() + 180
    status: dict[str, Any] = {}
    while time.monotonic() < deadline:
        status = require_ok(
            session.get(f"{base}/api/graphmarts/{encoded_graphmart}/status", params={"detail": "true"}, timeout=60),
            "Read graphmart status",
        )
        if status.get("isComplete") and not status.get("dirty"):
            break
        time.sleep(2)
    else:
        raise RuntimeError(f"Graphmart reload did not complete within 180 seconds: {status!r}")
    if status.get("failedLayers") or status.get("failedSteps") or status.get("failedDatasets"):
        raise RuntimeError(f"Graphmart reload completed with failures: {status!r}")
    summary["graphmartStatus"] = status

    sparql = """
        PREFIX cam: <https://opcenter.siemens.com/ontology/camstar/2607/ProductMfgOrder#>
        SELECT (COUNT(DISTINCT ?product) AS ?products) (COUNT(DISTINCT ?order) AS ?mfgOrders)
        WHERE {
          OPTIONAL { ?product a cam:Product . }
          OPTIONAL { ?order a cam:MfgOrder . }
        }
    """
    query_response = session.post(
        f"{base}/sparql/graphmart/{quote(GRAPHMART_URI, safe='')}",
        data={"query": sparql},
        headers={"Accept": "application/sparql-results+json"},
        timeout=120,
    )
    summary["sparqlStatus"] = query_response.status_code
    if query_response.ok:
        summary["sparqlResult"] = response_json(query_response)
    else:
        summary["sparqlWarning"] = query_response.text[:1000]

    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", action="store_true", help="Upload and attach artifacts through Graph Studio APIs")
    args = parser.parse_args()
    load_env()
    classes, properties, relationships = fetch_subgraph()
    if {item.get("name") for item in classes} != set(TARGET_CLASSES):
        raise RuntimeError(f"Expected {TARGET_CLASSES}, got {[item.get('name') for item in classes]}")
    rows_by_class, property_map, primary_keys = fetch_source_data(properties)

    summary: dict[str, Any] = {
        "targetGraphmart": GRAPHMART_URI,
        "classes": [item["name"] for item in classes],
        "classCount": len(classes),
        "propertyCount": len(properties),
        "propertiesByClass": {
            class_name: sum(1 for item in properties if item["className"] == class_name)
            for class_name in TARGET_CLASSES
        },
        "relationshipCount": len(relationships),
        "sourceRowCounts": {class_name: len(rows_by_class[class_name]) for class_name in TARGET_CLASSES},
        "primaryKeys": primary_keys,
        "mappedPropertiesByClass": {
            class_name: sum(
                1
                for (mapped_class, _), item in property_map.items()
                if mapped_class == class_name and item.get("physicalField")
            )
            for class_name in TARGET_CLASSES
        },
        "unmappedPropertiesByClass": {
            class_name: sorted(
                name
                for (mapped_class, name), item in property_map.items()
                if mapped_class == class_name and not item.get("physicalField")
            )
            for class_name in TARGET_CLASSES
        },
        "relationships": [
            {key: item.get(key) for key in ("source", "name", "target", "cardinality")}
            for item in relationships
        ],
    }
    model, data = build_graphs(classes, properties, relationships, rows_by_class, property_map, primary_keys)
    write_and_validate(model, data, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.upload:
        summary = import_to_graphstudio(summary)
        MANIFEST_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "modelUri": summary.get("modelUri"),
            "datasetUri": summary.get("datasetUri"),
            "catalogEntry": summary.get("catalogEntry"),
            "layerUri": summary.get("layerUri"),
            "stepUri": summary.get("stepUri"),
            "status": summary.get("graphmartStatus"),
            "sparqlResult": summary.get("sparqlResult"),
            "sparqlWarning": summary.get("sparqlWarning"),
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
