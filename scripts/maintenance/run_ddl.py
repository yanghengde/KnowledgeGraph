import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sqlalchemy import text
from src.ddl.generator.ddl_generator import generate_ddl_from_ontology
from src.etl.config.db_config import get_tgt_engine

load_dotenv()

def apply_ddl():
    # 1. Connect to Neo4j and generate DDL
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    print("Generating DDL from Neo4j Ontology...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    ddl_script = generate_ddl_from_ontology(driver)
    driver.close()
    
    with open("generated_ontology.sql", "w", encoding="utf-8") as f:
        f.write(ddl_script)
    print("DDL script saved to generated_ontology.sql")
    
    # 2. Connect to OntologyDB and execute DDL
    print("Executing DDL on OntologyDB...")
    engine = get_tgt_engine()
    with engine.connect() as conn:
        # We need to execute the DDL statements one by one or in batches
        statements = ddl_script.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as e:
                # If table already exists, it might throw an error. We just log it.
                print(f"Statement executed with error (might already exist): {e}")
                pass
    print("DDL execution completed.")

if __name__ == "__main__":
    apply_ddl()
