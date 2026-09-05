"""G6-compatible views from the PostgreSQL model store."""
from src.graphstudio_sync.config import SyncSettings
from src.graphstudio_sync.ontology_store import source_payload


def payload():
    return source_payload(SyncSettings.from_env())


def overview():
    from web.shared import _classify_module
    model = payload()
    counts = {}
    for p in model["properties"]:
        counts[p["className"]] = counts.get(p["className"], 0) + 1
    nodes = [{"id": c["name"], "data": {"label": c["name"], "chineseName": c.get("chineseName") or "",
        "description": c.get("description") or "", "layer": c.get("layer") or "Config", "propertyCount": counts.get(c["name"], 0),
        "module": c.get("module") or _classify_module(c["name"]), "type": "class"}} for c in model["classes"]]
    edges = [{"source": r["source"], "target": r["target"], "data": {"label": r["name"], "cardinality": r.get("cardinality") or "", "lineStyle": r.get("lineStyle") or ""}} for r in model["relationships"]]
    return {"nodes": nodes, "edges": edges, "combos": [{"id": m, "data": {"label": m}} for m in sorted({n["data"]["module"] for n in nodes})]}


def details():
    model = payload()
    result = {c["name"]: {"className": c["name"], "properties": [], "incoming": [], "outgoing": []} for c in model["classes"]}
    for p in model["properties"]:
        result[p["className"]]["properties"].append(p)
    for r in model["relationships"]:
        data = {"relName": r["name"], "cardinality": r.get("cardinality"), "description": r.get("description")}
        result[r["source"]]["outgoing"].append({**data, "targetClass": r["target"]})
        result[r["target"]]["incoming"].append({**data, "sourceClass": r["source"]})
    return result


def documents():
    """Expose imported CSV classes to the existing authority review UI."""
    model = payload()
    grouped = {}
    for p in model["properties"]:
        grouped.setdefault(p["className"], []).append({**p, "type": p.get("dataType", "String")})
    return {"postgres_source": {"classes": [{**c, "className": c["name"], "properties": grouped.get(c["name"], [])} for c in model["classes"]],
        "relationships": [{**r, "fromClass": r["source"], "toClass": r["target"], "relationName": r["name"]} for r in model["relationships"]]}}
