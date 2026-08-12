import json
import httpx

url = "http://localhost:5050/api/graph/overview"
res = httpx.get(url)
data = res.json()

print("Total nodes:", len(data["nodes"]))
print("Total edges:", len(data["edges"]))

nodes_of_interest = {'Spec', 'Workflow', 'Product', 'WorkflowStep'}

print("\nEdges between nodes of interest:")
for edge in data["edges"]:
    src = edge["source"]
    tgt = edge["target"]
    label = edge["data"].get("label")
    if src in nodes_of_interest or tgt in nodes_of_interest:
        print(f"{src} -[{label}]-> {tgt}")
