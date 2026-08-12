import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.qa.graph_retriever import find_reasonable_path, find_path_highlight

def test_bom_to_workflow():
    print("\n--- Test: BOM to Workflow ---")
    p_nodes, p_edges = find_reasonable_path("BOM", "Workflow", {"BOM", "Workflow"})
    print("Path nodes:", " -> ".join(p_nodes))
    print("Path edges:", " -> ".join(p_edges))
    
    assert "SetupAccess" not in p_nodes, "Error: Path went through SetupAccess hub!"
    assert len(p_nodes) > 0, "Error: No path found!"
    print("SUCCESS: BOM -> Workflow path did not use SetupAccess!")

def test_spec_to_employee():
    print("\n--- Test: Spec to Employee ---")
    p_nodes, p_edges = find_reasonable_path("Spec", "Employee", {"Spec", "Employee"})
    print("Path nodes:", " -> ".join(p_nodes))
    print("Path edges:", " -> ".join(p_edges))
    
    assert "ES_DisplayOptions" not in p_nodes, "Error: Path went through ES_DisplayOptions hub!"
    assert "ChangeStatus" not in p_nodes, "Error: Path went through ChangeStatus hub!"
    assert "SetupAccess" not in p_nodes, "Error: Path went through SetupAccess hub!"
    assert len(p_nodes) > 0, "Error: No path found!"
    print("SUCCESS: Spec -> Employee path is reasonable!")

def test_mfgline_to_tool():
    print("\n--- Test: MfgLine to Tool ---")
    p_nodes, p_edges = find_reasonable_path("MfgLine", "Tool", {"MfgLine", "Tool"})
    print("Path nodes:", " -> ".join(p_nodes))
    print("Path edges:", " -> ".join(p_edges))
    
    assert "Container" not in p_nodes, "Error: Path went through Container runtime table!"
    assert len(p_nodes) > 0, "Error: No path found!"
    print("SUCCESS: MfgLine -> Tool path did not use Container!")

def test_find_path_highlight():
    print("\n--- Test: find_path_highlight ---")
    highlight = find_path_highlight(["BOM", "Workflow"])
    print("Nodes:", highlight["nodes"])
    print("Edges:", highlight["edges"])
    assert "BOM" in highlight["nodes"]
    assert "Workflow" in highlight["nodes"]
    assert len(highlight["edges"]) > 0
    print("SUCCESS: find_path_highlight returned non-empty edges!")

def test_get_shortest_path_details():
    print("\n--- Test: get_shortest_path_details ---")
    from src.qa.graph_retriever import get_shortest_path_details
    details = get_shortest_path_details("BOM", "Workflow")
    print("Details:", details)
    assert details is not None
    assert "nodes" in details
    assert "relationships" in details
    assert "SetupAccess" not in details["nodes"], "Error: Path went through SetupAccess!"
    print("SUCCESS: get_shortest_path_details returned correct path details!")

if __name__ == "__main__":
    try:
        test_bom_to_workflow()
        test_spec_to_employee()
        test_mfgline_to_tool()
        test_find_path_highlight()
        test_get_shortest_path_details()
        print("\nALL TEST CASES PASSED SUCCESSFULLY!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\nTEST FAILURE: {e}")
        sys.exit(1)
