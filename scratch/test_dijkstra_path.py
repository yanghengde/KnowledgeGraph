import os
import sys
import heapq
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.qa.graph_retriever import _get_driver

# Define penalties for intermediate nodes
INFRASTRUCTURE_NODES = {
    "ChangeStatus", "ChangeHistory", "WIPMsgDefMgr", "WIPMsgDetails", "SetupAccess",
    "HoldReason", "LossReason", "CategoryMap", "Organization", "OrgNotification",
    "ESigRequirement", "ESigReqTxnMap", "SignatureRule", "UOM", "isUOMConversion",
    "User", "isImage", "EmailGroup", "HoldReason"
}

TRANSACTION_NODES = {
    "Container", "MfgLot", "HistoryMainline", "TxnMap", "ProductStockLevel"
}

def build_local_graph():
    driver = _get_driver()
    nodes = set()
    adj = {} # node -> list of (neighbor, rel_name, direction)
    
    with driver.session() as session:
        # Load all nodes
        res_nodes = session.run("MATCH (c:OntologyClass) RETURN c.name AS name")
        for r in res_nodes:
            nodes.add(r["name"])
            adj[r["name"]] = []
            
        # Load all edges
        res_edges = session.run("""
            MATCH (from:OntologyClass)-[r:ONTOLOGY_RELATION]->(to:OntologyClass)
            RETURN from.name AS source, to.name AS target, r.name AS name
        """)
        for r in res_edges:
            src, tgt, name = r["source"], r["target"], r["name"]
            # Add directed connections
            if src in adj and tgt in adj:
                adj[src].append((tgt, name, "out"))
                adj[tgt].append((src, name, "in"))
                
    return nodes, adj

def find_reasonable_path(adj, start, end, keywords_set):
    # Dijkstra's algorithm to find the lowest-cost path from start to end
    # Priority queue stores (cost, current_node, path_nodes, path_edges)
    pq = [(0, start, [start], [])]
    visited = {} # node -> min_cost
    
    while pq:
        cost, node, path_nodes, path_edges = heapq.heappop(pq)
        
        if node == end:
            return path_nodes, path_edges
            
        if node in visited and visited[node] <= cost:
            continue
        visited[node] = cost
        
        # Traverse neighbors
        for neighbor, rel_name, direction in adj.get(node, []):
            # Calculate node penalty for neighbor (if it's not the end node and not in keywords)
            penalty = 0
            if neighbor != end and neighbor not in keywords_set:
                if neighbor in INFRASTRUCTURE_NODES:
                    penalty = 50 # severe penalty to avoid generic system/metadata hubs
                elif neighbor in TRANSACTION_NODES:
                    penalty = 10 # moderate penalty to avoid dynamic transaction hubs
                else:
                    penalty = 0
            
            # Base edge weight is 1
            edge_weight = 1
            # Add small penalty if we traverse in opposite direction of standard modeling relationships
            # (e.g. going from WorkflowStep back to Workflow is 'in' direction, which is fine, but let's keep base weight small)
            
            new_cost = cost + edge_weight + penalty
            if neighbor not in visited or visited[neighbor] > new_cost:
                heapq.heappush(pq, (new_cost, neighbor, path_nodes + [neighbor], path_edges + [rel_name]))
                
    return None, None

def test():
    nodes, adj = build_local_graph()
    pairs = [
        ("BOM", "Workflow"),
        ("Spec", "Employee"),
        ("Resource", "Product"),
        ("MfgLine", "Tool")
    ]
    
    for kw1, kw2 in pairs:
        print(f"\n--- Dijkstra Path between {kw1} and {kw2} ---")
        keywords_set = {kw1, kw2}
        path_nodes, path_edges = find_reasonable_path(adj, kw1, kw2, keywords_set)
        if path_nodes:
            print("Dijkstra Nodes:", " -> ".join(path_nodes))
            print("Dijkstra Edges:", " -> ".join(path_edges))
        else:
            print("No path found.")
            
test()
