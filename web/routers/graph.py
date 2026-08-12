import os
from functools import lru_cache
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from web.shared import driver, _classify_module, _load_module_map, PROJECT_ROOT

router = APIRouter()

# Siemens Color Tokens
COLORS = {
    "workflow": {"fill": "#009999", "stroke": "#00B8B8"},
    "operation": {"fill": "#FF6600", "stroke": "#FF8833"},
    "spec": {"fill": "#862996", "stroke": "#A040B0"},
    "workcenter": {"fill": "#2E86C1", "stroke": "#5DADE2"},
    "factory": {"fill": "#27AE60", "stroke": "#52D68C"},
    "mfgline": {"fill": "#00897B", "stroke": "#4DB6AC"},
    "mfgcalendar": {"fill": "#FF8F00", "stroke": "#FFB74D"},
    "product": {"fill": "#F39C12", "stroke": "#F5B041"},
    "container": {"fill": "#3498DB", "stroke": "#5DADE2"},
    "carrier": {"fill": "#039BE5", "stroke": "#4FC3F7"},
    "businessrule": {"fill": "#6A1B9A", "stroke": "#AB47BC"},
    "datacollection": {"fill": "#9B59B6", "stroke": "#AF7AC5"},
    "quality": {"fill": "#E74C3C", "stroke": "#EC7063"},
    "electronic_procedure": {"fill": "#1ABC9C", "stroke": "#48C9B0"},
    "resource": {"fill": "#F1C40F", "stroke": "#F7DC6F"},
    "material": {"fill": "#16A085", "stroke": "#48C9B0"},
    "bom": {"fill": "#673AB7", "stroke": "#9575CD"},
    "erpbom": {"fill": "#7B1FA2", "stroke": "#BA68C8"},
    "employee": {"fill": "#E67E22", "stroke": "#EB984E"},
    "role": {"fill": "#37474F", "stroke": "#78909C"},
    "mfgorder": {"fill": "#34495E", "stroke": "#5D6D7E"},
    "part": {"fill": "#0277BD", "stroke": "#4FC3F7"},
    "organization": {"fill": "#C62828", "stroke": "#EF5350"},
    "billofprocess": {"fill": "#4527A0", "stroke": "#7E57C2"},
    "team": {"fill": "#BF360C", "stroke": "#FF7043"},
    "salesorder": {"fill": "#1B5E20", "stroke": "#66BB6A"},
    "maintenance": {"fill": "#C0392B", "stroke": "#D98880"},
    "sampling": {"fill": "#9C27B0", "stroke": "#BA68C8"},
    "document": {"fill": "#607D8B", "stroke": "#90A4AE"},
    "label": {"fill": "#FF9800", "stroke": "#FFB74D"},
    "tool": {"fill": "#795548", "stroke": "#A1887F"},
    "change_management": {"fill": "#F44336", "stroke": "#E57373"},
    "recipe": {"fill": "#E91E63", "stroke": "#F06292"},
    "inventory": {"fill": "#8BC34A", "stroke": "#AED581"},
    "rework": {"fill": "#FF5722", "stroke": "#FF8A65"},
    "timer": {"fill": "#00BCD4", "stroke": "#4DD0E1"},
    "checklist": {"fill": "#5C6BC0", "stroke": "#7986CB"},
    "setup": {"fill": "#7E57C2", "stroke": "#9575CD"},
    "packaging": {"fill": "#8D6E63", "stroke": "#A1887F"},
    "supplier": {"fill": "#3F51B5", "stroke": "#5C6BC0"},
    "esignature": {"fill": "#00ACC1", "stroke": "#26C6DA"},
    "alarm": {"fill": "#F50057", "stroke": "#FF4081"},
    "scrap": {"fill": "#546E7A", "stroke": "#78909C"},
    "equipmentstate": {"fill": "#29B6F6", "stroke": "#4FC3F7"},
    "shipping": {"fill": "#827717", "stroke": "#9E9D24"},
    "environment": {"fill": "#00BFA5", "stroke": "#1DE9B6"},
    "rma": {"fill": "#D84315", "stroke": "#F4511E"},
    "consumable": {"fill": "#FFB300", "stroke": "#FFCA28"},
    "spc": {"fill": "#2979FF", "stroke": "#82B1FF"},
    "other": {"fill": "#505050", "stroke": "#707070"}
}

@lru_cache(maxsize=1)
def _graph_overview_cached():
    _load_module_map()
    with driver.session() as session:
        # Nodes
        result = session.run("""
            MATCH (c:OntologyClass)
            RETURN c.name AS name,
                   c.chineseName AS chineseName,
                   c.description AS description,
                   c.layer AS layer
            ORDER BY c.name
        """)
        nodes = []
        combos = set()
        for r in result:
            name = r["name"]
            module = _classify_module(name)
            combos.add(module)
            nodes.append({
                "id": name,
                "data": {
                    "label": name,
                    "chineseName": r["chineseName"] or "",
                    "description": r["description"] or "",
                    "layer": r["layer"] or "Config",
                    "module": module,
                    "type": "class",
                }
            })

        # Edges
        result = session.run("""
            MATCH (from:OntologyClass)-[r:ONTOLOGY_RELATION]->(to:OntologyClass)
            RETURN from.name AS source,
                   to.name   AS target,
                   r.name    AS label,
                   r.cardinality AS cardinality,
                   r.lineStyle   AS lineStyle
        """)
        edges = []
        for r in result:
            edges.append({
                "source": r["source"],
                "target": r["target"],
                "data": {
                    "label": r["label"] or "",
                    "cardinality": r["cardinality"] or "",
                    "lineStyle": r["lineStyle"] or "",
                }
            })

        combo_list = [{"id": c, "data": {"label": c.capitalize()}} for c in combos]

    return {"nodes": nodes, "edges": edges, "combos": combo_list}


@router.get("/api/graph/overview")
def graph_overview(refresh: bool = False):
    if refresh:
        _graph_overview_cached.cache_clear()
    response = JSONResponse(content=_graph_overview_cached())
    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
    return response


CLASS_DETAIL_QUERY = """
    MATCH (c:OntologyClass {name: $name})
    RETURN c.name AS className,
           [(c)-[:HAS_PROPERTY]->(p:OntologyProperty) |
             {name: p.name, dataType: p.dataType, description: p.description}
           ] AS properties,
           [(c)-[r:ONTOLOGY_RELATION]->(target:OntologyClass) |
             {targetClass: target.name, relName: r.name,
              cardinality: r.cardinality, description: r.description}
           ] AS outgoing,
           [(source:OntologyClass)-[r:ONTOLOGY_RELATION]->(c) |
             {sourceClass: source.name, relName: r.name,
              cardinality: r.cardinality, description: r.description}
           ] AS incoming
"""


def _normalize_class_detail(record, class_name: str):
    if record is None:
        return {
            "className": class_name,
            "properties": [],
            "outgoing": [],
            "incoming": [],
        }
    return {
        "className": record["className"],
        "properties": sorted(record["properties"], key=lambda item: item["name"] or ""),
        "outgoing": sorted(
            record["outgoing"],
            key=lambda item: (item["targetClass"] or "", item["relName"] or ""),
        ),
        "incoming": sorted(
            record["incoming"],
            key=lambda item: (item["sourceClass"] or "", item["relName"] or ""),
        ),
    }


@lru_cache(maxsize=512)
def _graph_class_detail_cached(class_name: str):
    with driver.session() as session:
        record = session.run(CLASS_DETAIL_QUERY, name=class_name).single()
    return _normalize_class_detail(record, class_name)


@lru_cache(maxsize=1)
def _all_class_details_cached():
    query = CLASS_DETAIL_QUERY.replace(
        "MATCH (c:OntologyClass {name: $name})",
        "MATCH (c:OntologyClass)",
    )
    with driver.session() as session:
        return {
            record["className"]: _normalize_class_detail(
                record,
                record["className"],
            )
            for record in session.run(query)
        }


@router.get("/api/graph/class/{class_name}")
def graph_class_detail(class_name: str, refresh: bool = False):
    if refresh:
        _graph_class_detail_cached.cache_clear()
        _all_class_details_cached.cache_clear()

    response = JSONResponse(content=_graph_class_detail_cached(class_name))
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@router.get("/api/graph/details")
def all_graph_details(refresh: bool = False):
    """Return every class detail once for idle client-side prefetch."""
    if refresh:
        _graph_class_detail_cached.cache_clear()
        _all_class_details_cached.cache_clear()
    response = JSONResponse(content=_all_class_details_cached())
    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
    return response


@lru_cache(maxsize=1)
def _stats_cached():
    query = """
    MATCH (c:OntologyClass)
    WITH count(c) AS classCount
    MATCH (p:OntologyProperty)
    WITH classCount, count(p) AS propCount
    MATCH ()-[r:ONTOLOGY_RELATION]->()
    RETURN classCount, propCount, count(r) AS relationCount
    """
    with driver.session() as session:
        return dict(session.run(query).single())


@router.get("/api/stats")
def stats(refresh: bool = False):
    if refresh:
        _stats_cached.cache_clear()
    record = _stats_cached()
    return {
        "classCount": record["classCount"],
        "propertyCount": record["propCount"],
        "relationCount": record["relationCount"],
    }


@router.get("/api/config")
def get_config():
    return {
        "show_layout_switch": os.getenv("SHOW_LAYOUT_SWITCH", "false").lower() == "true",
        "wiki_review_required": os.getenv("WIKI_REVIEW_REQUIRED", "false").lower() == "true",
    }


@router.get("/api/product-lines")
def list_product_lines():
    from src.ontology.wiki_manager import load_product_lines
    return {"product_lines": load_product_lines()}


class ProductLineModel(BaseModel):
    id: str
    name: str
    description: str = ""
    icon: str = "package"
    color: str = "#999999"


class SaveProductLinesRequest(BaseModel):
    product_lines: list[ProductLineModel]


@router.post("/api/product-lines")
def save_product_lines_endpoint(req: SaveProductLinesRequest):
    from src.ontology.wiki_manager import save_product_lines
    lines_list = [line.dict() for line in req.product_lines]
    success = save_product_lines(lines_list)
    return {"success": success}
