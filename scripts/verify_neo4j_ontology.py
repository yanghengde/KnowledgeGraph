#!/usr/bin/env python3
"""Verify that Neo4j exactly matches the generated ontology JSON artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = PROJECT_ROOT / "src" / "ontology" / "wiki_kb"


def expected_sets():
    classes: set[str] = set()
    properties: set[tuple[str, str]] = set()
    relationships: set[tuple[str, str, str]] = set()
    for path in ONTOLOGY_DIR.glob("*_ontology.json"):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        for item in payload.get("classes", []):
            class_name = item["className"]
            classes.add(class_name)
            properties.update(
                (class_name, prop["name"])
                for prop in item.get("properties", [])
            )
        relationships.update(
            (
                rel["fromClass"],
                rel["relationName"],
                rel["toClass"],
            )
            for rel in payload.get("relationships", [])
        )
    return classes, properties, relationships


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    if not all([uri, user, password]):
        raise RuntimeError("Neo4j configuration is missing in .env")

    expected_classes, expected_properties, expected_relationships = expected_sets()
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            actual_classes = {
                record["name"]
                for record in session.run(
                    "MATCH (c:OntologyClass) RETURN c.name AS name"
                )
            }
            actual_properties = {
                (record["className"], record["name"])
                for record in session.run("""
                    MATCH (c:OntologyClass)-[:HAS_PROPERTY]->(p:OntologyProperty)
                    RETURN c.name AS className, p.name AS name
                """)
            }
            actual_relationships = {
                (record["source"], record["relation"], record["target"])
                for record in session.run("""
                    MATCH (source:OntologyClass)-[r:ONTOLOGY_RELATION]->
                          (target:OntologyClass)
                    RETURN source.name AS source, r.name AS relation,
                           target.name AS target
                """)
            }
            orphan_properties = session.run("""
                MATCH (p:OntologyProperty)
                WHERE NOT (:OntologyClass)-[:HAS_PROPERTY]->(p)
                RETURN count(p) AS count
            """).single()["count"]
    finally:
        driver.close()

    checks = {
        "classes": (expected_classes, actual_classes),
        "properties": (expected_properties, actual_properties),
        "relationships": (expected_relationships, actual_relationships),
    }
    failed = False
    for name, (expected, actual) in checks.items():
        missing = expected - actual
        extra = actual - expected
        print(
            f"{name}: expected={len(expected)} actual={len(actual)} "
            f"missing={len(missing)} extra={len(extra)}"
        )
        if missing or extra:
            failed = True
            for item in sorted(missing)[:10]:
                print(f"  missing {item}")
            for item in sorted(extra)[:10]:
                print(f"  extra {item}")
    print(f"orphan_properties={orphan_properties}")
    return 1 if failed or orphan_properties else 0


if __name__ == "__main__":
    raise SystemExit(main())
