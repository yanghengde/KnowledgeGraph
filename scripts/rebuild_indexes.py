import os
import sys
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Ensure project root is in path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


# ── Canonical index/constraint definitions ──
# This is the single source of truth for all Neo4j schema objects.
# neo4j_loader.py calls ensure_indexes() from this module.

CONSTRAINTS = [
    {
        "name": "unique_ontology_class_name",
        "cypher": "CREATE CONSTRAINT unique_ontology_class_name IF NOT EXISTS FOR (c:OntologyClass) REQUIRE c.name IS UNIQUE",
        "description": "Unique Class Name",
    },
    {
        "name": "unique_ontology_property",
        "cypher": "CREATE CONSTRAINT unique_ontology_property IF NOT EXISTS FOR (p:OntologyProperty) REQUIRE (p.className, p.name) IS UNIQUE",
        "description": "Unique Property Composite (className + name)",
    },
]

INDEXES = [
    {
        "name": "ontology_class_chinese_name",
        "cypher": "CREATE INDEX ontology_class_chinese_name IF NOT EXISTS FOR (c:OntologyClass) ON (c.chineseName)",
        "description": "Chinese Name Index (keyword query filtering)",
    },
    {
        "name": "ontology_class_layer",
        "cypher": "CREATE INDEX ontology_class_layer IF NOT EXISTS FOR (c:OntologyClass) ON (c.layer)",
        "description": "Layer Index (stats aggregation, layer-based filtering)",
    },
    {
        "name": "ontology_class_module",
        "cypher": "CREATE INDEX ontology_class_module IF NOT EXISTS FOR (c:OntologyClass) ON (c.module)",
        "description": "Module Index (module filtering and focused graph loading)",
    },
    {
        "name": "ontology_class_fulltext",
        "cypher": "CREATE FULLTEXT INDEX ontology_class_fulltext IF NOT EXISTS FOR (c:OntologyClass) ON EACH [c.name, c.chineseName, c.description]",
        "description": "FULLTEXT Name + ChineseName + Description",
    },
    {
        "name": "ontology_property_name",
        "cypher": "CREATE INDEX ontology_property_name IF NOT EXISTS FOR (p:OntologyProperty) ON (p.name)",
        "description": "Property Name Index",
    },
    {
        "name": "ontology_property_class_name",
        "cypher": "CREATE INDEX ontology_property_class_name IF NOT EXISTS FOR (p:OntologyProperty) ON (p.className)",
        "description": "Property ClassName Index (class detail queries)",
    },
    {
        "name": "ontology_property_data_type",
        "cypher": "CREATE INDEX ontology_property_data_type IF NOT EXISTS FOR (p:OntologyProperty) ON (p.dataType)",
        "description": "Property Data Type Index",
    },
    {
        "name": "ontology_property_class_type",
        "cypher": "CREATE INDEX ontology_property_class_type IF NOT EXISTS FOR (p:OntologyProperty) ON (p.className, p.dataType)",
        "description": "Composite Class + Data Type Index",
    },
    {
        "name": "ontology_property_fulltext",
        "cypher": "CREATE FULLTEXT INDEX ontology_property_fulltext IF NOT EXISTS FOR (p:OntologyProperty) ON EACH [p.name, p.description]",
        "description": "FULLTEXT Property Name + Description (RAG property search)",
    },
    {
        "name": "ontology_relation_name",
        "cypher": "CREATE INDEX ontology_relation_name IF NOT EXISTS FOR ()-[r:ONTOLOGY_RELATION]-() ON (r.name)",
        "description": "Relationship Name Index",
    },
    {
        "name": "ontology_relation_cardinality",
        "cypher": "CREATE INDEX ontology_relation_cardinality IF NOT EXISTS FOR ()-[r:ONTOLOGY_RELATION]-() ON (r.cardinality)",
        "description": "Relationship Cardinality Index",
    },
    {
        "name": "ontology_relation_fulltext",
        "cypher": "CREATE FULLTEXT INDEX ontology_relation_fulltext IF NOT EXISTS FOR ()-[r:ONTOLOGY_RELATION]-() ON EACH [r.name, r.description]",
        "description": "FULLTEXT Relationship Name + Description",
    },
]


def ensure_indexes(session=None, verbose=True):
    """
    Ensure all canonical indexes and constraints exist.
    Can be called with an existing session (from neo4j_loader) or standalone.
    Returns True if all operations succeed.
    """
    def _run(sess):
        errors = []
        # Create constraints first (they also create backing indexes)
        for c in CONSTRAINTS:
            try:
                sess.run(c["cypher"]).consume()
                if verbose:
                    print(f"  [OK] Constraint: {c['name']} ({c['description']})")
            except Exception as e:
                errors.append(f"{c['name']}: {e}")
                if verbose:
                    print(f"  [FAIL] Constraint {c['name']}: {e}")

        # Create indexes
        for idx in INDEXES:
            try:
                sess.run(idx["cypher"]).consume()
                if verbose:
                    print(f"  [OK] Index: {idx['name']} ({idx['description']})")
            except Exception as e:
                errors.append(f"{idx['name']}: {e}")
                if verbose:
                    print(f"  [FAIL] Index {idx['name']}: {e}")
        if errors:
            raise RuntimeError("Index creation failed: " + "; ".join(errors))

    if session:
        _run(session)
        session.run("CALL db.awaitIndexes(300)").consume()
    else:
        # Standalone mode: create own driver/session
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as sess:
            _run(sess)
            sess.run("CALL db.awaitIndexes(300)").consume()
        driver.close()

    return True


def rebuild_indexes():
    """Full rebuild: drop all custom indexes/constraints, then recreate them."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    print(f"Connecting to Neo4j at {uri}...")
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        return

    with driver.session() as session:
        print("\n--- [Step 1] Dropping existing custom indexes and constraints ---")
        
        # Drop all custom constraints
        for c in CONSTRAINTS:
            try:
                session.run(f"DROP CONSTRAINT {c['name']} IF EXISTS")
                print(f"  Dropped constraint: {c['name']}")
            except Exception as e:
                print(f"  Error dropping constraint {c['name']}: {e}")

        # Drop all custom indexes
        for idx in INDEXES:
            try:
                session.run(f"DROP INDEX {idx['name']} IF EXISTS")
                print(f"  Dropped index: {idx['name']}")
            except Exception as e:
                print(f"  Error dropping index {idx['name']}: {e}")

        print("\n--- [Step 2] Creating optimized indexes and constraints ---")
        ensure_indexes(session, verbose=True)

        print("\nWaiting 3 seconds for indexes to build and go online...")
        time.sleep(3)

        print("\n--- [Step 3] Fetching current index status from Neo4j ---")
        try:
            result = session.run("SHOW INDEXES")
            print(f"  {'Index Name':<35} | {'Type':<10} | {'Labels/Types':<20} | {'Properties':<30} | {'State':<10}")
            print("  " + "-" * 112)
            for r in result:
                name = r.get("name") or "Unnamed"
                idx_type = r.get("type") or "Unknown"
                labels = str(r.get("labelsOrTypes") or "None")
                properties = str(r.get("properties") or "None")
                state = r.get("state") or "Unknown"
                print(f"  {name:<35} | {idx_type:<10} | {labels:<20} | {properties:<30} | {state:<10}")
        except Exception as e:
            print(f"  Error showing indexes: {e}")

    driver.close()
    print("\nRebuilding and optimization of Neo4j indexes successfully completed!")


if __name__ == "__main__":
    rebuild_indexes()
