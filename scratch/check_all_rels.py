import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.qa.graph_retriever import _get_driver

driver = _get_driver()
with driver.session() as session:
    result = session.run("MATCH ()-[r:ONTOLOGY_RELATION]->() RETURN count(r) as total, count(r.name) as with_name")
    for rec in result:
        print("Total relationships:", rec["total"])
        print("Relationships with name property:", rec["with_name"])
