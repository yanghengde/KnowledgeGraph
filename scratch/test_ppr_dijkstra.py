import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.qa.graph_retriever import compute_ppr, find_reasonable_path

def test_ppr_calculation():
    print("\n--- Test: Personalized PageRank (PPR) Calculation ---")
    keywords = {"BOM", "Workflow"}
    scores = compute_ppr(keywords)
    
    assert scores is not None, "Error: PPR scores is None!"
    assert len(scores) > 0, "Error: PPR scores dict is empty!"
    
    # Standardize keywords should have higher scores than average background nodes
    bom_score = scores.get("BOM", 0.0)
    workflow_score = scores.get("Workflow", 0.0)
    mfgorder_score = scores.get("MfgOrder", 0.0)
    setupaccess_score = scores.get("SetupAccess", 0.0)
    
    # Print top 10 nodes by PPR score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print("\nTop 10 nodes by PPR score:")
    for node, score in sorted_scores[:10]:
        print(f"- {node}: {score:.6f}")
        
    supplier_score = scores.get("Supplier", 0.0)
    print(f"Supplier score: {supplier_score:.6f}")
    
    assert bom_score > 0, "Error: BOM score is 0!"
    assert workflow_score > 0, "Error: Workflow score is 0!"
    assert mfgorder_score > supplier_score, "Error: MfgOrder (related) should have higher PPR than Supplier (unrelated)!"
    print("SUCCESS: PPR calculation runs and preserves topological relative weights!")

def test_ppr_dijkstra_path():
    print("\n--- Test: Combined PPR-Dijkstra Path ---")
    # Verify that BOM to Workflow still avoids SetupAccess and finds a correct business path
    p_nodes, p_edges = find_reasonable_path("BOM", "Workflow", {"BOM", "Workflow"})
    print("Path nodes:", " -> ".join(p_nodes))
    print("Path edges:", " -> ".join(p_edges))
    
    assert "SetupAccess" not in p_nodes, "Error: Combined path still traverses SetupAccess!"
    assert "MfgOrder" in p_nodes or "Product" in p_nodes, "Error: Failed to connect BOM and Workflow via MfgOrder/Product!"
    print("SUCCESS: Combined PPR-Dijkstra pathfinding resolves correctly!")

if __name__ == "__main__":
    try:
        test_ppr_calculation()
        test_ppr_dijkstra_path()
        print("\nPPR-DIJKSTRA TEST CASES PASSED SUCCESSFULLY!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\nTEST FAILURE: {e}")
        sys.exit(1)
