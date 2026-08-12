import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from scratch.test_dijkstra_path import build_local_graph

nodes, adj = build_local_graph()

def find_all_paths(start, end, max_depth=4):
    paths = []
    
    def dfs(curr, target, depth, path_nodes, path_edges):
        if curr == target:
            paths.append((path_nodes, path_edges))
            return
        if depth >= max_depth:
            return
        for neighbor, rel_name, direction in adj.get(curr, []):
            if neighbor not in path_nodes:
                dfs(neighbor, target, depth + 1, path_nodes + [neighbor], path_edges + [rel_name])
                
    dfs(start, end, 0, [start], [])
    return paths

paths = find_all_paths("Spec", "Employee", 4)
print(f"Found {len(paths)} paths between Spec and Employee of length <= 4:")
for idx, (path_n, path_e) in enumerate(sorted(paths, key=lambda x: len(x[0]))[:20]):
    print(f"{idx+1}. {' -> '.join(path_n)} | Edges: {' -> '.join(path_e)}")
