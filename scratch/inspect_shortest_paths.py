import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.qa.graph_retriever import _get_driver

pairs = [
    ("Resource", "Product"),
    ("BOM", "Workflow"),
    ("Spec", "Employee"),
    ("Factory", "Role"),
    ("MfgLine", "Tool")
]

driver = _get_driver()
with driver.session() as session:
    for kw1, kw2 in pairs:
        query = """
        MATCH (start:OntologyClass), (end:OntologyClass)
        WHERE (toLower(start.name) = toLower($kw1) OR toLower(start.chineseName) = toLower($kw1))
          AND (toLower(end.name) = toLower($kw2) OR toLower(end.chineseName) = toLower($kw2))
        WITH start, end LIMIT 1
        MATCH path = shortestPath((start)-[*1..5]-(end))
        RETURN nodes(path) AS path_nodes, relationships(path) AS path_edges
        """
        try:
            records = session.run(query, kw1=kw1, kw2=kw2)
            print(f"\n--- Path between {kw1} and {kw2} ---")
            found = False
            for rec in records:
                found = True
                nodes = [n["name"] for n in rec["path_nodes"]]
                edges = [r["name"] for r in rec["path_edges"]]
                print("Nodes:", " -> ".join(nodes))
                print("Edges:", " -> ".join(edges))
            if not found:
                print("No path found.")
        except Exception as e:
            print("Error:", e)
