import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sqlalchemy import text
from src.etl.config.db_config import get_src_engine, get_tgt_engine

load_dotenv()

def test_neo4j():
    print("Testing Neo4j connection...")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("[SUCCESS] Successfully connected to Neo4j.")
        
        # Clearing data (once)
        with driver.session() as session:
            # Check if there's any data
            result = session.run("MATCH (n) RETURN count(n) AS count")
            count = result.single()["count"]
            if count > 0:
                print(f"Found {count} nodes in Neo4j. Clearing database...")
                session.run("MATCH (n) DETACH DELETE n")
                print("[SUCCESS] Neo4j database cleared.")
            else:
                print("Neo4j database is already empty.")
                
        driver.close()
    except Exception as e:
        print(f"[ERROR] Failed to connect to Neo4j: {e}")

def test_src_db():
    print("\nTesting SQL Server (Camstar PRD) connection...")
    try:
        engine = get_src_engine()
        with engine.connect() as conn:
            # Run a simple query
            result = conn.execute(text("SELECT TOP 1 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"))
            row = result.fetchone()
            print(f"[SUCCESS] Successfully connected to Camstar PRD. Sample table found: {row[0] if row else 'None'}")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Camstar PRD: {e}")

def test_tgt_db():
    print("\nTesting SQL Server (Ontology DB) connection...")
    try:
        engine = get_tgt_engine()
        with engine.connect() as conn:
            # Run a simple query
            result = conn.execute(text("SELECT 1 AS res"))
            row = result.fetchone()
            print("[SUCCESS] Successfully connected to Ontology DB.")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Ontology DB: {e}")

if __name__ == "__main__":
    test_neo4j()
    test_src_db()
    test_tgt_db()
