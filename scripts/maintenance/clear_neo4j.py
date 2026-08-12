import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def clear_neo4j():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        print("Neo4j configuration is missing in .env")
        return

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        print("Clearing all nodes and relationships from Neo4j...")
        session.run("MATCH (n) DETACH DELETE n")
        print("Neo4j database cleared successfully.")
    driver.close()

if __name__ == "__main__":
    clear_neo4j()
