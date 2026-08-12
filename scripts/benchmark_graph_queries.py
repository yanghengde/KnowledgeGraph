#!/usr/bin/env python3
"""Benchmark graph UI queries and verify that key Neo4j indexes are used."""

from __future__ import annotations

import os
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DETAIL_QUERY = """
MATCH (c:OntologyClass {name: $name})
RETURN c.name AS className,
       [(c)-[:HAS_PROPERTY]->(p:OntologyProperty) |
         {name: p.name, dataType: p.dataType, description: p.description}
       ] AS properties,
       [(c)-[r:ONTOLOGY_RELATION]->(target:OntologyClass) |
         {targetClass: target.name, relName: r.name,
          cardinality: r.cardinality, description: r.description}
       ] AS outgoing,
       [(source:OntologyClass)-[r:ONTOLOGY_RELATION]->(c) |
         {sourceClass: source.name, relName: r.name,
          cardinality: r.cardinality, description: r.description}
       ] AS incoming
"""

OVERVIEW_QUERY = """
MATCH (c:OntologyClass)
WITH collect(c {
  .name, .chineseName, .description, .layer, .module
}) AS classes
MATCH (source:OntologyClass)-[r:ONTOLOGY_RELATION]->(target:OntologyClass)
RETURN classes,
       collect({
         source: source.name, target: target.name, name: r.name,
         cardinality: r.cardinality, lineStyle: r.lineStyle
       }) AS relationships
"""


def operators(plan) -> set[str]:
    if isinstance(plan, dict):
        operator = plan.get("operatorType", "").split("@", 1)[0]
        children = plan.get("children", [])
    else:
        operator = plan.operator_type
        children = plan.children
    result = {operator}
    for child in children:
        result.update(operators(child))
    return result


def benchmark(session, label, query, parameters=None, iterations=30):
    parameters = parameters or {}
    session.run(query, **parameters).consume()
    timings = []
    for _ in range(iterations):
        start = time.perf_counter()
        list(session.run(query, **parameters))
        timings.append((time.perf_counter() - start) * 1000)
    timings.sort()
    p95_index = min(len(timings) - 1, int(len(timings) * 0.95))
    print(
        f"{label}: median_ms={statistics.median(timings):.3f} "
        f"p95_ms={timings[p95_index]:.3f}"
    )


def assert_plan(session, label, query, parameters, expected):
    summary = session.run("EXPLAIN " + query, **parameters).consume()
    found = operators(summary.plan)
    print(f"{label}_operators={','.join(sorted(found))}")
    if not any(operator in found for operator in expected):
        raise RuntimeError(
            f"{label} did not use one of {sorted(expected)}; got {sorted(found)}"
        )


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            sample = session.run("""
                MATCH (c:OntologyClass)
                OPTIONAL MATCH (c)-[r:ONTOLOGY_RELATION]->()
                RETURN c.name AS className, c.module AS module,
                       r.name AS relationName
                ORDER BY count { (c)-[:HAS_PROPERTY]->() } DESC
                LIMIT 1
            """).single()
            class_name = sample["className"]
            module = sample["module"]
            relation_name = sample["relationName"]

            assert_plan(
                session,
                "class_detail",
                "MATCH (c:OntologyClass {name: $name}) RETURN c.name",
                {"name": class_name},
                {"NodeUniqueIndexSeek"},
            )
            assert_plan(
                session,
                "module_filter",
                "MATCH (c:OntologyClass {module: $module}) RETURN c.name",
                {"module": module},
                {"NodeIndexSeek"},
            )
            assert_plan(
                session,
                "property_filter",
                "MATCH (p:OntologyProperty {className: $name, dataType: $type}) "
                "RETURN p.name",
                {"name": class_name, "type": "Navigation"},
                {"NodeIndexSeek"},
            )
            if relation_name:
                assert_plan(
                    session,
                    "relationship_filter",
                    "MATCH ()-[r:ONTOLOGY_RELATION]->() "
                    "WHERE r.name = $name RETURN r.name",
                    {"name": relation_name},
                    {
                        "DirectedRelationshipIndexSeek",
                        "UndirectedRelationshipIndexSeek",
                    },
                )

            benchmark(
                session,
                "class_detail",
                DETAIL_QUERY,
                {"name": class_name},
                iterations=50,
            )
            benchmark(
                session,
                "graph_overview",
                OVERVIEW_QUERY,
                iterations=20,
            )
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
