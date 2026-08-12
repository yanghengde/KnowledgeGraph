import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.qa.graph_retriever import _get_driver

driver = _get_driver()
with driver.session() as session:
    kw1, kw2 = "Spec", "Workflow"
    query = """
    MATCH (start:OntologyClass), (end:OntologyClass)
    WHERE (toLower(start.name) = toLower($kw1) OR toLower(start.chineseName) = toLower($kw1))
      AND (toLower(end.name) = toLower($kw2) OR toLower(end.chineseName) = toLower($kw2))
    WITH start, end LIMIT 1
    MATCH path = shortestPath((start)-[*1..5]-(end))
    RETURN nodes(path) AS path_nodes, relationships(path) AS path_edges
    """
    records = session.run(query, kw1=kw1, kw2=kw2)
    for rec in records:
        print("Nodes:", [n["name"] for n in rec["path_nodes"]])
        print("Edges count:", len(rec["path_edges"]))
        for r in rec["path_edges"]:
            print("Edge rel type:", getattr(r, "type", "N/A"))
            print("Edge properties:", dict(r))
