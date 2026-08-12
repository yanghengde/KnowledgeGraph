import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.qa.graph_retriever import _get_driver

driver = _get_driver()
with driver.session() as session:
    result = session.run("MATCH ()-[r:ONTOLOGY_RELATION]->() RETURN keys(r) as r_keys, r.name as r_name, type(r) as r_type, properties(r) as r_props LIMIT 5")
    for rec in result:
        print("Keys:", rec["r_keys"])
        print("Name:", rec["r_name"])
        print("Type:", rec["r_type"])
        print("Properties:", rec["r_props"])
        print("---")
