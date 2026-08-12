"""Read-only inventory and mapping coverage checks for the sync pipeline."""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymssql
import requests
from neo4j import GraphDatabase
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import PROJECT_ROOT, SyncSettings


FIELDS_CSV = PROJECT_ROOT / "docs" / "Database_Fields.csv"


def normalize_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").casefold())


def _physical_candidates(field_name: str, navigation: bool) -> set[str]:
    candidates = {normalize_identifier(field_name)}
    value = field_name
    for prefix in ("ES_", "ss_"):
        if value.casefold().startswith(prefix.casefold()):
            value = value[len(prefix) :]
            candidates.add(normalize_identifier(value))
    if navigation:
        expanded = set(candidates)
        for candidate in candidates:
            for suffix in ("defid", "refid", "id"):
                if candidate.endswith(suffix):
                    expanded.add(candidate[: -len(suffix)])
        candidates = expanded
    return candidates


@dataclass(frozen=True)
class OntologyInventory:
    classes: list[dict[str, Any]]
    properties: list[dict[str, Any]]
    relationship_count: int


def read_ontology(settings: SyncSettings) -> OntologyInventory:
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            classes = [
                dict(record)
                for record in session.run(
                    """
                    MATCH (c:OntologyClass)
                    RETURN c.name AS name, coalesce(c.module, c.layer, 'unassigned') AS module,
                           c.sourceWorkspace AS workspace,
                           c.sourceCDODefId AS sourceCDODefId
                    ORDER BY c.name
                    """
                )
            ]
            properties = [
                dict(record)
                for record in session.run(
                    """
                    MATCH (c:OntologyClass)-[:HAS_PROPERTY]->(p:OntologyProperty)
                    RETURN c.name AS className, p.name AS name,
                           p.dataType AS dataType, p.sourceFieldId AS sourceFieldId
                    ORDER BY c.name, p.name
                    """
                )
            ]
            relationship_count = int(
                session.run("MATCH ()-[r:ONTOLOGY_RELATION]->() RETURN count(r) AS count").single()["count"]
            )
    finally:
        driver.close()
    return OntologyInventory(classes, properties, relationship_count)


def read_source_catalog(settings: SyncSettings) -> dict[str, dict[str, Any]]:
    connection = pymssql.connect(
        server=settings.source_host,
        port=settings.source_port,
        user=settings.source_user,
        password=settings.source_password,
        database=settings.source_database,
        login_timeout=20,
        timeout=120,
    )
    cursor = connection.cursor(as_dict=True)
    try:
        cursor.execute(
            """
            SELECT s.name AS schema_name, t.name AS table_name,
                   SUM(CASE WHEN p.index_id IN (0,1) THEN p.rows ELSE 0 END) AS row_count
            FROM sys.tables t
            JOIN sys.schemas s ON s.schema_id=t.schema_id
            LEFT JOIN sys.partitions p ON p.object_id=t.object_id
            GROUP BY s.name,t.name
            """
        )
        tables = {normalize_identifier(row["table_name"]): dict(row) for row in cursor.fetchall()}
        cursor.execute(
            """
            SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            ORDER BY TABLE_SCHEMA,TABLE_NAME,ORDINAL_POSITION
            """
        )
        columns: dict[tuple[str, str], list[str]] = {}
        for row in cursor.fetchall():
            columns.setdefault((row["TABLE_SCHEMA"], row["TABLE_NAME"]), []).append(row["COLUMN_NAME"])
    finally:
        connection.close()
    for table in tables.values():
        table["columns"] = columns.get((table["schema_name"], table["table_name"]), [])
    return tables


def read_csv_fields() -> dict[str, dict[str, str]]:
    with FIELDS_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return {row["FieldID"]: row for row in csv.DictReader(handle) if row.get("FieldID")}


def _property_has_column(
    prop: dict[str, Any],
    table: dict[str, Any] | None,
    csv_fields: dict[str, dict[str, str]],
) -> bool:
    return resolve_physical_column(prop, table, csv_fields)[0] is not None


def resolve_physical_column(
    prop: dict[str, Any],
    table: dict[str, Any] | None,
    csv_fields: dict[str, dict[str, str]],
) -> tuple[str | None, str | None]:
    if not table:
        return None, None
    columns = table["columns"]
    normalized_columns = {normalize_identifier(column): column for column in columns}
    csv_field = csv_fields.get(str(prop.get("sourceFieldId") or ""))
    if csv_field and normalize_identifier(csv_field.get("FieldName", "")) in normalized_columns:
        return normalized_columns[normalize_identifier(csv_field["FieldName"])], "source_field_id"
    property_name = normalize_identifier(prop["name"])
    if property_name in normalized_columns:
        return normalized_columns[property_name], "property_name"
    if property_name == "name" and normalize_identifier(prop["className"] + "Name") in normalized_columns:
        return normalized_columns[normalize_identifier(prop["className"] + "Name")], "class_name"
    navigation = prop.get("dataType") == "Navigation"
    matches = [
        column
        for column in columns
        if property_name in _physical_candidates(column, navigation)
    ]
    if len(matches) == 1:
        return matches[0], "normalized_name"
    return None, "ambiguous_name" if matches else None


def build_plan(settings: SyncSettings) -> dict[str, Any]:
    ontology = read_ontology(settings)
    source = read_source_catalog(settings)
    csv_fields = read_csv_fields()

    matched_tables: dict[str, dict[str, Any]] = {}
    missing_tables: list[str] = []
    for item in ontology.classes:
        table = source.get(normalize_identifier(item["name"]))
        if table:
            matched_tables[item["name"]] = table
        else:
            missing_tables.append(item["name"])

    property_results = [
        (
            prop,
            _property_has_column(prop, matched_tables.get(prop["className"]), csv_fields),
        )
        for prop in ontology.properties
    ]
    mapped_properties = sum(matched for _, matched in property_results)
    unmapped_properties = [
        {
            "className": prop["className"],
            "propertyName": prop["name"],
            "dataType": prop.get("dataType"),
            "sourceFieldId": prop.get("sourceFieldId"),
        }
        for prop, matched in property_results
        if not matched
    ]
    row_counts = {name: int(table.get("row_count") or 0) for name, table in matched_tables.items()}
    nonempty = {name: count for name, count in row_counts.items() if count > 0}
    modules = Counter(str(item.get("module") or "unassigned") for item in ontology.classes)
    total_rows = sum(row_counts.values())
    recommended_mode = "atomic_snapshot" if total_rows <= 5_000_000 else "partitioned_incremental"

    return {
        "ontology": {
            "classes": len(ontology.classes),
            "properties": len(ontology.properties),
            "relationships": ontology.relationship_count,
            "modules": dict(sorted(modules.items())),
        },
        "source": {
            "tablesMatched": len(matched_tables),
            "tablesMissing": missing_tables,
            "nonemptyTables": len(nonempty),
            "emptyTables": len(matched_tables) - len(nonempty),
            "approximateRows": total_rows,
            "largestMappedTables": [
                {"className": name, "rows": count}
                for name, count in sorted(nonempty.items(), key=lambda item: item[1], reverse=True)[:20]
            ],
        },
        "mapping": {
            "propertiesMappedToPhysicalColumns": mapped_properties,
            "propertiesUnmapped": len(ontology.properties) - mapped_properties,
            "propertyCoveragePercent": round(mapped_properties * 100 / max(1, len(ontology.properties)), 2),
            "unmappedProperties": unmapped_properties,
        },
        "recommendation": {
            "initialLoadMode": "atomic_snapshot",
            "steadyStateMode": recommended_mode,
            "stateStore": "postgresql_control_plane",
            "scheduler": "external_cronjob_with_concurrency_lock",
            "graphStudioTransport": "rdf_batches_on_shared_file_store",
        },
    }


def check_graphstudio(settings: SyncSettings) -> dict[str, Any]:
    session = requests.Session()
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=3,
                connect=3,
                read=3,
                status=3,
                backoff_factor=0.5,
                status_forcelist=(429, 502, 503, 504),
                allowed_methods=frozenset({"GET"}),
            )
        ),
    )
    session.auth = (settings.graphstudio_user, settings.graphstudio_password)
    session.headers.update({"Accept": "application/json", "Accept-Encoding": "identity"})
    graphmart_url = f"{settings.graphstudio_base_url}/api/graphmarts/{requests.utils.quote(settings.graphmart_uri, safe='')}"
    graphmart = session.get(graphmart_url, timeout=60)
    graphmart.raise_for_status()
    status = session.get(graphmart_url + "/status", params={"detail": "true"}, timeout=60)
    status.raise_for_status()
    datasets = session.get(
        f"{settings.graphstudio_base_url}/api/datasets",
        params={"limit": 500, "expand": "dataLocation"},
        timeout=120,
    )
    datasets.raise_for_status()
    connections: Counter[str] = Counter()
    for dataset in datasets.json():
        location = dataset.get("dataLocation") or {}
        if isinstance(location, list):
            location = location[0] if location else {}
        if location.get("fileConnection"):
            connections[location["fileConnection"]] += 1
    return {
        "graphmart": graphmart.json(),
        "status": status.json(),
        "fileConnections": dict(connections),
    }
