"""Compile Neo4j ontology and Camstar SQL metadata into PostgreSQL."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from neo4j import GraphDatabase
from sqlalchemy import text

from .config import SyncSettings
from .inventory import (
    normalize_identifier,
    read_csv_fields,
    read_source_catalog,
    resolve_physical_column,
)
from .repository import ControlPlaneRepository


def _ontology_catalog(settings: SyncSettings) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    from .ontology_backend import backend
    if backend(settings) == "postgres":
        from .ontology_store import source_payload
        payload = source_payload(settings)
        return payload["classes"], payload["properties"], payload["relationships"]
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        driver.verify_connectivity()
        with driver.session(database=settings.neo4j_database) as session:
            classes = [
                dict(record)
                for record in session.run(
                    """
                    MATCH (c:OntologyClass)
                    RETURN c.name AS name, c.chineseName AS chineseName,
                           c.layer AS layer, c.sourceWorkspace AS sourceWorkspace,
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
                    RETURN c.name AS className, p.name AS name, p.dataType AS dataType,
                           coalesce(p.required, false) AS required,
                           p.sourceFieldId AS sourceFieldId
                    ORDER BY c.name, p.name
                    """
                )
            ]
            relationships = [
                dict(record)
                for record in session.run(
                    """
                    MATCH (source:OntologyClass)-[r:ONTOLOGY_RELATION]->(target:OntologyClass)
                    RETURN source.name AS source, r.name AS name, target.name AS target,
                           r.cardinality AS cardinality
                    ORDER BY source.name, r.name, target.name
                    """
                )
            ]
    finally:
        driver.close()
    return classes, properties, relationships


def _class_tokens(value: str) -> set[str]:
    tokens = {normalize_identifier(value)}
    stripped = value[2:] if value.casefold().startswith("a_") else value
    tokens.add(normalize_identifier(stripped))
    return tokens


def compile_catalog(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
) -> dict[str, Any]:
    snapshot_id = uuid.uuid4()
    with repository.engine.begin() as connection:
        connection.execute(
            text("INSERT INTO graphsync.catalog_snapshot (snapshot_id, status) VALUES (:id, 'compiling')"),
            {"id": snapshot_id},
        )
    try:
        classes, properties, relationships = _ontology_catalog(settings)
        source = read_source_catalog(settings)
        csv_fields = read_csv_fields()
        with repository.engine.connect() as connection:
            overrides = {
                (row["class_name"], row["property_name"]): dict(row)
                for row in connection.execute(
                    text("SELECT * FROM graphsync.mapping_override WHERE enabled")
                ).mappings()
            }
            relationship_overrides = {
                (row["source_class"], row["relationship_name"], row["target_class"]): dict(row)
                for row in connection.execute(
                    text("SELECT * FROM graphsync.relationship_override WHERE enabled")
                ).mappings()
            }

        class_rows: list[dict[str, Any]] = []
        class_tables: dict[str, dict[str, Any] | None] = {}
        for item in classes:
            table = source.get(normalize_identifier(item["name"]))
            class_tables[item["name"]] = table
            class_rows.append(
                {
                    "snapshot_id": snapshot_id,
                    "class_name": item["name"],
                    "chinese_name": item.get("chineseName"),
                    "ontology_layer": item.get("layer"),
                    "source_workspace": item.get("sourceWorkspace"),
                    "source_cdo_def_id": item.get("sourceCDODefId"),
                    "physical_schema": table.get("schema_name") if table else None,
                    "physical_table": table.get("table_name") if table else None,
                    "approximate_rows": int(table.get("row_count") or 0) if table else 0,
                    "mapping_status": "resolved" if table else "unresolved",
                }
            )

        property_rows: list[dict[str, Any]] = []
        for item in properties:
            table = class_tables.get(item["className"])
            field = csv_fields.get(str(item.get("sourceFieldId") or ""), {})
            column, method = resolve_physical_column(item, table, csv_fields)
            override = overrides.get((item["className"], item["name"]))
            status = "resolved" if column else "unresolved"
            physical_table = table
            if override:
                kind = override["mapping_kind"]
                physical_table = source.get(normalize_identifier(override["physical_table"])) or table
                if kind in {"property", "relationship"}:
                    requested = normalize_identifier(override.get("physical_column") or "")
                    matching_column = next(
                        (
                            candidate
                            for candidate in (physical_table.get("columns", []) if physical_table else [])
                            if normalize_identifier(candidate) == requested
                        ),
                        None,
                    )
                    column = matching_column
                    status = "override" if matching_column else "unresolved"
                    method = "mapping_override" if matching_column else "invalid_mapping_override"
                else:
                    column = None
                    status = kind
                    method = "mapping_override"
            property_rows.append(
                {
                    "snapshot_id": snapshot_id,
                    "class_name": item["className"],
                    "property_name": item["name"],
                    "data_type": item.get("dataType"),
                    "required": bool(item.get("required")),
                    "source_field_id": str(item.get("sourceFieldId") or "") or None,
                    "physical_schema": physical_table.get("schema_name") if physical_table else None,
                    "physical_table": physical_table.get("table_name") if physical_table else None,
                    "physical_column": column,
                    "fk_table_name": field.get("FKTableName") or None,
                    "fk_field_name": field.get("FKFieldName") or None,
                    "mapping_status": status,
                    "resolution_method": method,
                }
            )

        properties_by_class: dict[str, list[dict[str, Any]]] = {}
        for item in property_rows:
            properties_by_class.setdefault(item["class_name"], []).append(item)
        relationship_rows: list[dict[str, Any]] = []
        for item in relationships:
            target_tokens = _class_tokens(item["target"])
            candidates = [
                prop
                for prop in properties_by_class.get(item["source"], [])
                if prop.get("fk_table_name")
                and _class_tokens(str(prop["fk_table_name"])) & target_tokens
                and prop["mapping_status"] in {"resolved", "override"}
            ]
            # CSV-backed relationships carry an exact field identity. Do not
            # collapse ProductId and BeginProductId merely because both target Product.
            if item.get("sourceFieldId"):
                candidates = [p for p in candidates if str(p.get("source_field_id")) == str(item["sourceFieldId"])]
            if len(candidates) == 1:
                candidate = candidates[0]
                status = "resolved"
                method = "foreign_key_target"
            else:
                candidate = None
                status = "ambiguous" if candidates else "unresolved"
                method = None
            relationship_override = relationship_overrides.get(
                (item["source"], item["name"], item["target"])
            )
            if relationship_override:
                selected = next(
                    (
                        prop
                        for prop in properties_by_class.get(item["source"], [])
                        if prop["property_name"] == relationship_override["source_property"]
                        and prop["mapping_status"] in {"resolved", "override"}
                    ),
                    None,
                )
                candidate = selected
                status = "resolved" if selected else "unresolved"
                method = "relationship_override" if selected else "invalid_relationship_override"
            relationship_rows.append(
                {
                    "snapshot_id": snapshot_id,
                    "source_class": item["source"],
                    "relationship_name": item["name"],
                    "target_class": item["target"],
                    "cardinality": item.get("cardinality"),
                    "source_property": candidate.get("property_name") if candidate else None,
                    "source_field_id": candidate.get("source_field_id") if candidate else None,
                    "physical_column": candidate.get("physical_column") if candidate else None,
                    "candidate_properties": json.dumps(
                        [prop["property_name"] for prop in candidates], ensure_ascii=False
                    ),
                    "mapping_status": status,
                    "candidate_count": len(candidates),
                    "resolution_method": method,
                }
            )

        hash_payload = json.dumps(
            {
                "classes": [{key: value for key, value in row.items() if key != "snapshot_id"} for row in class_rows],
                "properties": [{key: value for key, value in row.items() if key != "snapshot_id"} for row in property_rows],
                "relationships": [{key: value for key, value in row.items() if key != "snapshot_id"} for row in relationship_rows],
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        catalog_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()
        resolved_properties = sum(row["mapping_status"] != "unresolved" for row in property_rows)
        coverage = round(resolved_properties * 100 / max(1, len(property_rows)), 3)
        with repository.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.class_mapping
                        (snapshot_id, class_name, chinese_name, ontology_layer, source_workspace,
                         source_cdo_def_id, physical_schema, physical_table, approximate_rows, mapping_status)
                    VALUES
                        (:snapshot_id, :class_name, :chinese_name, :ontology_layer, :source_workspace,
                         :source_cdo_def_id, :physical_schema, :physical_table, :approximate_rows, :mapping_status)
                    """
                ),
                class_rows,
            )
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.property_mapping
                        (snapshot_id, class_name, property_name, data_type, required, source_field_id,
                         physical_schema, physical_table, physical_column, fk_table_name, fk_field_name,
                         mapping_status, resolution_method)
                    VALUES
                        (:snapshot_id, :class_name, :property_name, :data_type, :required, :source_field_id,
                         :physical_schema, :physical_table, :physical_column, :fk_table_name, :fk_field_name,
                         :mapping_status, :resolution_method)
                    """
                ),
                property_rows,
            )
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.relationship_mapping
                        (snapshot_id, source_class, relationship_name, target_class, cardinality,
                         source_property, source_field_id, physical_column, candidate_properties,
                         mapping_status, candidate_count, resolution_method)
                    VALUES
                        (:snapshot_id, :source_class, :relationship_name, :target_class, :cardinality,
                         :source_property, :source_field_id, :physical_column,
                         CAST(:candidate_properties AS jsonb), :mapping_status, :candidate_count,
                         :resolution_method)
                    """
                ),
                relationship_rows,
            )
            connection.execute(
                text(
                    """
                    UPDATE graphsync.catalog_snapshot
                    SET status='ready', finished_at=now(), ontology_class_count=:classes,
                        ontology_property_count=:properties, relationship_count=:relationships,
                        physical_table_count=:tables, approximate_row_count=:rows,
                        mapping_coverage=:coverage, catalog_hash=:hash
                    WHERE snapshot_id=:snapshot_id
                    """
                ),
                {
                    "snapshot_id": snapshot_id,
                    "classes": len(class_rows),
                    "properties": len(property_rows),
                    "relationships": len(relationship_rows),
                    "tables": sum(row["mapping_status"] == "resolved" for row in class_rows),
                    "rows": sum(row["approximate_rows"] for row in class_rows),
                    "coverage": coverage,
                    "hash": catalog_hash,
                },
            )
            retention_value = connection.execute(
                text("SELECT value FROM graphsync.app_setting WHERE setting_key='catalog.retention_ready'")
            ).scalar_one_or_none()
            retention = max(1, int(retention_value or 5))
            pruned = connection.execute(
                text(
                    """
                    DELETE FROM graphsync.catalog_snapshot
                    WHERE snapshot_id IN (
                        SELECT snapshot_id FROM graphsync.catalog_snapshot
                        WHERE status='ready'
                        ORDER BY finished_at DESC
                        OFFSET :retention
                    )
                    """
                ),
                {"retention": retention},
            ).rowcount
        return {
            "snapshotId": str(snapshot_id),
            "classes": len(class_rows),
            "properties": len(property_rows),
            "relationships": len(relationship_rows),
            "propertiesResolved": resolved_properties,
            "propertiesUnresolved": len(property_rows) - resolved_properties,
            "relationshipResolved": sum(row["mapping_status"] == "resolved" for row in relationship_rows),
            "relationshipAmbiguous": sum(row["mapping_status"] == "ambiguous" for row in relationship_rows),
            "relationshipUnresolved": sum(row["mapping_status"] == "unresolved" for row in relationship_rows),
            "coveragePercent": coverage,
            "catalogHash": catalog_hash,
            "snapshotsPruned": pruned,
        }
    except Exception as exc:
        with repository.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE graphsync.catalog_snapshot
                    SET status='failed', finished_at=now(), error=CAST(:error AS jsonb)
                    WHERE snapshot_id=:snapshot_id
                    """
                ),
                {
                    "snapshot_id": snapshot_id,
                    "error": json.dumps({"type": type(exc).__name__, "message": str(exc)[:4000]}),
                },
            )
        raise
