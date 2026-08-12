"""
Step 2: Graph Retriever
───────────────────────
Queries Neo4j ontology graph to get structured context
(classes, properties, relationships) relevant to the user question.
"""
import os
import re
import heapq
import threading
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "")),
        )
    return _driver


def _fulltext_query(keyword: str) -> str:
    """Build a conservative Lucene query for Neo4j fulltext indexes."""
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", keyword or "", flags=re.UNICODE)
    if not tokens:
        return ""

    parts = []
    for token in tokens[:4]:
        if len(token) <= 1:
            parts.append(token)
        else:
            parts.append(f"{token} OR {token}*")
    return " OR ".join(parts)


def _run_class_search(session, keyword: str, max_hops: int):
    fulltext = _fulltext_query(keyword)
    if not fulltext:
        return []

    query = """
        WITH $kw AS kw, $fulltext AS fulltext
        CALL (kw, fulltext) {
            MATCH (exact:OntologyClass {name: kw})
            RETURN exact AS c, 100.0 AS score
            UNION
            CALL db.index.fulltext.queryNodes("ontology_class_fulltext", fulltext, {limit: 8})
            YIELD node, score
            RETURN node AS c, score
        }
        WITH c, max(score) AS score
        ORDER BY score DESC, c.name
        LIMIT 3

        OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p:OntologyProperty)
        WITH c, score, collect(DISTINCT {name: p.name, type: p.dataType, desc: p.description}) AS props

        OPTIONAL MATCH path = (c)-[:ONTOLOGY_RELATION*1..%d]-(neighbor:OntologyClass)
        WITH c, score, props, relationships(path) AS rels
        UNWIND (CASE rels WHEN null THEN [null] ELSE rels END) AS r

        RETURN c.name AS className,
               c.chineseName AS chineseName,
               c.description AS description,
               props,
               collect(DISTINCT CASE WHEN r IS NOT NULL THEN {
                   from: startNode(r).name,
                   rel: r.name,
                   to: endNode(r).name,
                   cardinality: r.cardinality,
                   desc: r.description
               } ELSE null END) AS rels
    """ % max_hops
    return session.run(query, kw=keyword, fulltext=fulltext)


def _run_class_search_fallback(session, keyword: str, max_hops: int):
    query = """
        MATCH (c:OntologyClass)
        WHERE toLower(c.name) CONTAINS toLower($kw)
           OR toLower(c.chineseName) CONTAINS toLower($kw)
        WITH c LIMIT 3

        OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p:OntologyProperty)
        WITH c, collect(DISTINCT {name: p.name, type: p.dataType, desc: p.description}) AS props

        OPTIONAL MATCH path = (c)-[:ONTOLOGY_RELATION*1..%d]-(neighbor:OntologyClass)
        WITH c, props, relationships(path) AS rels
        UNWIND (CASE rels WHEN null THEN [null] ELSE rels END) AS r

        RETURN c.name AS className,
               c.chineseName AS chineseName,
               c.description AS description,
               props,
               collect(DISTINCT CASE WHEN r IS NOT NULL THEN {
                   from: startNode(r).name,
                   rel: r.name,
                   to: endNode(r).name,
                   cardinality: r.cardinality,
                   desc: r.description
               } ELSE null END) AS rels
    """ % max_hops
    return session.run(query, kw=keyword)


def search_graph(keywords: list[str], max_hops: int = 1) -> dict:
    """
    Given a list of entity keywords, find matching OntologyClass nodes
    and expand 1-hop neighbours. Returns structured context dict.
    """
    max_hops = max(1, min(int(max_hops), 3))
    driver = _get_driver()
    results = {
        "matched_classes": [],
        "relationships": [],
        "properties": [],
    }

    with driver.session() as session:
        for kw in keywords:
            if not kw or len(kw) < 2:
                continue

            # Prefer Neo4j fulltext index. Fall back to contains scan for older DBs
            # where the index has not been created yet.
            try:
                records = _run_class_search(session, kw, max_hops)
            except Exception:
                records = _run_class_search_fallback(session, kw, max_hops)

            for rec in records:
                class_info = {
                    "name": rec["className"],
                    "chineseName": rec["chineseName"] or "",
                    "description": rec["description"] or "",
                }
                results["matched_classes"].append(class_info)

                # Properties (filter out nulls)
                for p in rec["props"]:
                    if p["name"]:
                        results["properties"].append({
                            "class": rec["className"],
                            "name": p["name"],
                            "type": p["type"] or "String",
                            "description": p["desc"] or "",
                        })

                # Relationships (filter out nulls)
                for r in rec["rels"]:
                    if r["rel"]:
                        results["relationships"].append({
                            "from": r["from"],
                            "relation": r["rel"],
                            "to": r["to"],
                            "cardinality": r["cardinality"] or "",
                            "description": r["desc"] or "",
                        })

    # Deduplicate
    seen_classes = set()
    results["matched_classes"] = [
        c for c in results["matched_classes"]
        if c["name"] not in seen_classes and not seen_classes.add(c["name"])
    ]

    seen_rels = set()
    results["relationships"] = [
        r for r in results["relationships"]
        if (r["from"], r["relation"], r["to"]) not in seen_rels
        and not seen_rels.add((r["from"], r["relation"], r["to"]))
    ]

    return results


def format_graph_context(graph_data: dict) -> str:
    """Format graph retrieval results into a readable string for the LLM."""
    lines = []

    if graph_data["matched_classes"]:
        lines.append("### 涉及的本体类")
        for c in graph_data["matched_classes"]:
            cn = f" ({c['chineseName']})" if c['chineseName'] else ""
            lines.append(f"- **{c['name']}**{cn}: {c['description']}")

    if graph_data["relationships"]:
        lines.append("\n### 类间关联链路")
        rel_map = {}
        for r in graph_data["relationships"][:15]:
            from_cls = r['from']
            if from_cls not in rel_map:
                rel_map[from_cls] = []
            rel_map[from_cls].append(r)

        for from_cls, rels in rel_map.items():
            lines.append(f"- **{from_cls}**")
            for r in rels:
                lines.append(f"  └──[{r['relation']}]──→ {r['to']}")

    if graph_data["properties"]:
        lines.append("\n### 关键属性")
        for p in graph_data["properties"][:10]:
            lines.append(f"- {p['class']}.{p['name']} ({p['type']})")

    return "\n".join(lines) if lines else "未找到相关本体信息。"


_ONTOLOGY_GRAPH = {"nodes": set(), "adj": {}, "chinese_map": {}}
_ONTOLOGY_GRAPH_LOCK = threading.Lock()

# Penalties for intermediate nodes to avoid meaningless shortcuts
INFRASTRUCTURE_NODES = {
    "ChangeStatus", "ChangeHistory", "ChangePackage", "WIPMsgDefMgr", "WIPMsgDetails", 
    "WIPMsgCategory", "SetupAccess", "HoldReason", "LossReason", "CategoryMap", 
    "Organization", "OrgNotification", "ESigRequirement", "ESigReqTxnMap", 
    "SignatureRule", "UOM", "isUOMConversion", "isImage", "EmailGroup",
    "ES_DisplayOptions", "ES_MfgOrderReassignPlan", "ES_ToolPlanMatrix", 
    "ES_AddressPool", "ES_CADInstructions"
}

TRANSACTION_NODES = {
    "Container", "MfgLot", "HistoryMainline", "TxnMap", "ProductStockLevel"
}

def _get_cached_graph(refresh: bool = False):
    global _ONTOLOGY_GRAPH
    if _ONTOLOGY_GRAPH["adj"] and not refresh:
        return _ONTOLOGY_GRAPH
        
    with _ONTOLOGY_GRAPH_LOCK:
        if _ONTOLOGY_GRAPH["adj"] and not refresh:
            return _ONTOLOGY_GRAPH
            
        driver = _get_driver()
        nodes = set()
        adj = {}
        chinese_map = {}
        
        with driver.session() as session:
            # 1. Load all classes and their Chinese names
            res_nodes = session.run("MATCH (c:OntologyClass) RETURN c.name AS name, c.chineseName AS chineseName")
            for r in res_nodes:
                name = r["name"]
                nodes.add(name)
                adj[name] = []
                if r["chineseName"]:
                    chinese_map[r["chineseName"].lower()] = name
                    
            # 2. Load all relationships
            res_edges = session.run("""
                MATCH (from:OntologyClass)-[r:ONTOLOGY_RELATION]->(to:OntologyClass)
                RETURN from.name AS source, to.name AS target, r.name AS name
            """)
            for r in res_edges:
                src, tgt, name = r["source"], r["target"], r["name"]
                if src in adj and tgt in adj:
                    adj[src].append((tgt, name, "out"))
                    adj[tgt].append((src, name, "in"))
                    
        _ONTOLOGY_GRAPH = {"nodes": nodes, "adj": adj, "chinese_map": chinese_map}
        return _ONTOLOGY_GRAPH

def _standardize_node_name(name: str) -> str | None:
    if not name:
        return None
    graph_data = _get_cached_graph()
    nodes = graph_data["nodes"]
    chinese_map = graph_data["chinese_map"]
    for canonical in nodes:
        if canonical.lower() == name.lower():
            return canonical
    if name.lower() in chinese_map:
        return chinese_map[name.lower()]
    return None

def compute_ppr(keywords: set[str], alpha: float = 0.15, max_iter: int = 20, tol: float = 1e-4) -> dict[str, float]:
    """
    Compute Personalized PageRank scores for all nodes in the cached graph.
    Personalized on the provided keywords.
    """
    graph_data = _get_cached_graph()
    adj = graph_data["adj"]
    nodes = graph_data["nodes"]
    
    if not nodes:
        return {}
        
    n_nodes = len(nodes)
    
    # Standardize keywords to canonical names
    canonical_kws = set()
    for k in keywords:
        canonical_name = _standardize_node_name(k)
        if canonical_name and canonical_name in adj:
            canonical_kws.add(canonical_name)
            
    # Initialize personalization vector
    if not canonical_kws:
        personalization = {node: 1.0 / n_nodes for node in nodes}
    else:
        personalization = {node: 1.0 / len(canonical_kws) if node in canonical_kws else 0.0 for node in nodes}
        
    # Initialize PageRank vector
    pr = personalization.copy()
    
    # Precompute out-degrees and transition list for undirected representation
    deg = {}
    neighbors_map = {}
    for node in nodes:
        unique_neighbors = list(set(nbr for nbr, _, _ in adj.get(node, [])))
        deg[node] = len(unique_neighbors)
        neighbors_map[node] = unique_neighbors
        
    # Power iteration
    for _ in range(max_iter):
        next_pr = {node: 0.0 for node in nodes}
        for node in nodes:
            score = pr[node]
            if score == 0.0:
                continue
            nbrs = neighbors_map[node]
            if nbrs:
                share = score / len(nbrs)
                for nbr in nbrs:
                    next_pr[nbr] += share
            else:
                for k, v in personalization.items():
                    next_pr[k] += score * v
                    
        diff = 0.0
        for node in nodes:
            val = (1.0 - alpha) * next_pr[node] + alpha * personalization.get(node, 0.0)
            diff += abs(val - pr[node])
            pr[node] = val
            
        if diff < tol:
            break
            
    return pr

def find_reasonable_path(start: str, end: str, keywords_set: set[str]) -> tuple[list[str], list[str]]:
    """
    Find lowest-cost path from start to end using Dijkstra's algorithm.
    Penalizes generic infrastructure and transactional nodes, and uses
    Personalized PageRank (PPR) scores to dynamically discount edge costs.
    """
    graph_data = _get_cached_graph()
    adj = graph_data["adj"]
    
    s_node = _standardize_node_name(start)
    e_node = _standardize_node_name(end)
    
    if not s_node or not e_node or s_node not in adj or e_node not in adj:
        return [], []
        
    if s_node == e_node:
        return [s_node], []

    # 1. Compute PPR personalized on keywords_set
    ppr_scores = compute_ppr(keywords_set)
    
    # 2. Get canonical keywords list
    canonical_keywords = set()
    for kw in keywords_set:
        c_kw = _standardize_node_name(kw)
        if c_kw:
            canonical_keywords.add(c_kw)
            
    # 3. Find max PPR score of non-keyword nodes to normalize relative scores
    non_kw_scores = [score for node, score in ppr_scores.items() if node not in canonical_keywords]
    max_other_score = max(non_kw_scores) if non_kw_scores else 0.0
    
    # Queue: (cost, current_node, path_nodes, path_edges)
    pq = [(0.0, s_node, [s_node], [])]
    visited = {}
    
    while pq:
        cost, curr, path_nodes, path_edges = heapq.heappop(pq)
        
        if curr == e_node:
            return path_nodes, path_edges
            
        if curr in visited and visited[curr] <= cost:
            continue
        visited[curr] = cost
        
        for neighbor, rel_name, direction in adj.get(curr, []):
            penalty = 0
            is_kw = neighbor in canonical_keywords or neighbor == e_node
            
            if not is_kw:
                if neighbor in INFRASTRUCTURE_NODES:
                    penalty = 100
                elif neighbor in TRANSACTION_NODES:
                    penalty = 20
            
            # Compute PPR-based cost discount
            if is_kw:
                relative_score = 1.0
            else:
                ppr_score = ppr_scores.get(neighbor, 0.0)
                relative_score = ppr_score / max_other_score if max_other_score > 0.0 else 0.0
                relative_score = min(1.0, relative_score)
                
            ppr_discount = 1.0 - 0.5 * relative_score
            
            # Dijkstra edge cost = (1 + penalty) * ppr_discount
            edge_weight = (1 + penalty) * ppr_discount
            new_cost = cost + edge_weight
            
            if neighbor not in visited or visited[neighbor] > new_cost:
                heapq.heappush(pq, (new_cost, neighbor, path_nodes + [neighbor], path_edges + [rel_name]))
                
    return [], []

def find_path_highlight(keywords: list[str]) -> dict:
    """
    Find shortest path between consecutive key entities in the ontology to highlight on the UI.
    Uses custom Dijkstra pathfinder with PPR integration.
    """
    highlight = {"nodes": set(keywords), "edges": set()}
    if len(keywords) < 2:
        return {"nodes": list(keywords), "edges": []}
        
    # Convert keywords to canonical forms to ensure they can be found
    canonical_keywords = []
    for k in keywords:
        std = _standardize_node_name(k)
        canonical_keywords.append(std if std else k)
        
    keywords_set = set(canonical_keywords)
    
    # Loop over consecutive pairs of keywords (limit to first 4 classes to prevent query overload)
    for i in range(min(len(canonical_keywords) - 1, 3)):
        kw1, kw2 = canonical_keywords[i], canonical_keywords[i+1]
        p_nodes, p_edges = find_reasonable_path(kw1, kw2, keywords_set)
        for n in p_nodes:
            highlight["nodes"].add(n)
        for e in p_edges:
            highlight["edges"].add(e)
            
    return {
        "nodes": list(highlight["nodes"]),
        "edges": list(highlight["edges"])
    }

def get_all_class_names() -> list[str]:
    """Return all OntologyClass names for entity matching."""
    driver = _get_driver()
    with driver.session() as session:
        result = session.run("MATCH (c:OntologyClass) RETURN c.name AS name")
        return [r["name"] for r in result]


def get_shortest_path_details(c1: str, c2: str) -> dict | None:
    """
    Query Neo4j for nodes and relationships along the reasonable path between c1 and c2.
    Returns: {"nodes": [NodeName1, ...], "relationships": [{"from": ..., "to": ..., "rel": ..., "cardinality": ..., "description": ...}, ...]} or None.
    """
    path_nodes, _ = find_reasonable_path(c1, c2, {c1, c2})
    if not path_nodes or len(path_nodes) < 2:
        if path_nodes:
            return {"nodes": path_nodes, "relationships": []}
        return None

    # We have a path of nodes. Query details of relationships between consecutive pairs.
    driver = _get_driver()
    pairs = [{"from_node": path_nodes[i], "to_node": path_nodes[i+1]} for i in range(len(path_nodes) - 1)]
    
    query = """
    UNWIND $pairs AS pair
    MATCH (n1:OntologyClass {name: pair.from_node})-[r:ONTOLOGY_RELATION]-(n2:OntologyClass {name: pair.to_node})
    RETURN startNode(r).name as from, endNode(r).name as to, r.name as rel, r.cardinality as cardinality, r.description as description
    """
    try:
        with driver.session() as session:
            result = session.run(query, pairs=pairs)
            rel_map = {}
            for r in result:
                frm, to, rel_name = r["from"], r["to"], r["rel"]
                desc = r["description"] or ""
                try:
                    desc = desc.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                except Exception:
                    desc = ""
                # Map by the pair key (order-independent)
                key = frozenset([frm, to])
                rel_map[key] = {
                    "from": frm,
                    "to": to,
                    "rel": rel_name,
                    "cardinality": r["cardinality"] or "",
                    "description": desc
                }
            
            # Construct the relationship details in path order
            relationship_details = []
            for pair in pairs:
                key = frozenset([pair["from_node"], pair["to_node"]])
                if key in rel_map:
                    relationship_details.append(rel_map[key])
                else:
                    # Fallback default if Neo4j query didn't return
                    relationship_details.append({
                        "from": pair["from_node"],
                        "to": pair["to_node"],
                        "rel": "ONTOLOGY_RELATION",
                        "cardinality": "",
                        "description": ""
                    })
                    
            return {
                "nodes": path_nodes,
                "relationships": relationship_details
            }
    except Exception as e:
        print(f"Error getting shortest path details: {e}")
        return None
