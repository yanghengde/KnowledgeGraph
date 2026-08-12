import os
import re
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

def apply_neo4j_indexes():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    if not all([uri, user, password]):
        print("[Neo4j Index Setup] Error: Missing Neo4j credentials in environment or .env file.")
        return

    # Path to the cypher definition file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cypher_file = os.path.join(current_dir, "neo4j_indexes.cypher")

    if not os.path.exists(cypher_file):
        print(f"[Neo4j Index Setup] Error: Cypher file not found at: {cypher_file}")
        return

    print(f"[Neo4j Index Setup] Connecting to database: {uri}")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Read and parse Cypher statements
    with open(cypher_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split statements by semicolon, removing comments
    statements = []
    # Remove single line comments
    clean_content = re.sub(r"//.*", "", content)
    for part in clean_content.split(";"):
        stmt = part.strip()
        if stmt:
            statements.append(stmt)

    # Execute statements
    with driver.session() as session:
        for index, stmt in enumerate(statements, 1):
            print(f"[Neo4j Index Setup] Executing DDL [{index}/{len(statements)}]:")
            print(f"  {stmt}")
            try:
                session.run(stmt)
                print("  => Success!")
            except Exception as e:
                print(f"  => Error executing statement: {e}")

    driver.close()
    print("[Neo4j Index Setup] Complete.")

if __name__ == "__main__":
    apply_neo4j_indexes()
