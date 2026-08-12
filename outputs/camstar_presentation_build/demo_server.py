"""Read-only demo server for presentation capture.

It serves the project's real front end and builds the graph API directly from
the checked-in ontology JSON files when Neo4j is unavailable.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = PROJECT_ROOT / "web" / "static"
ONTOLOGY_DIR = PROJECT_ROOT / "src" / "ontology" / "wiki_kb"


def load_graph():
    classes: dict[str, dict] = {}
    class_modules: dict[str, str] = {}
    relationships: dict[tuple[str, str, str], dict] = {}

    for path in sorted(ONTOLOGY_DIR.glob("*_ontology.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue

        module = str(payload.get("module") or path.stem.removesuffix("_ontology"))
        for item in payload.get("classes", []):
            class_name = item.get("className")
            if not class_name:
                continue
            classes[class_name] = item
            class_modules[class_name] = module

        for item in payload.get("relationships", []):
            key = (
                item.get("fromClass"),
                item.get("relationName"),
                item.get("toClass"),
            )
            if all(key):
                relationships[key] = item

    edges = []
    details = {
        name: {
            "className": name,
            "properties": [
                {
                    "name": prop.get("name", ""),
                    "dataType": prop.get("type", "String"),
                    "description": prop.get("description", ""),
                }
                for prop in item.get("properties", [])
            ],
            "outgoing": [],
            "incoming": [],
        }
        for name, item in classes.items()
    }

    for (source, relation, target), item in relationships.items():
        if source not in classes or target not in classes:
            continue
        cardinality = item.get("cardinality", "")
        description = item.get("description", "")
        edges.append(
            {
                "source": source,
                "target": target,
                "data": {
                    "label": relation,
                    "cardinality": cardinality,
                    "lineStyle": item.get("lineStyle", ""),
                },
            }
        )
        details[source]["outgoing"].append(
            {
                "targetClass": target,
                "relName": relation,
                "cardinality": cardinality,
                "description": description,
            }
        )
        details[target]["incoming"].append(
            {
                "sourceClass": source,
                "relName": relation,
                "cardinality": cardinality,
                "description": description,
            }
        )

    nodes = [
        {
            "id": name,
            "data": {
                "label": name,
                "chineseName": item.get("chineseName", ""),
                "description": item.get("description", ""),
                "layer": item.get("layer", "Config"),
                "module": class_modules.get(name, "other"),
                "type": "class",
            },
        }
        for name, item in sorted(classes.items())
    ]
    combos = [
        {"id": module, "data": {"label": module.replace("_", " ").title()}}
        for module in sorted(set(class_modules.values()))
    ]
    for detail in details.values():
        detail["properties"].sort(key=lambda x: x["name"])
        detail["outgoing"].sort(key=lambda x: (x["targetClass"], x["relName"]))
        detail["incoming"].sort(key=lambda x: (x["sourceClass"], x["relName"]))
    return nodes, edges, combos, details


NODES, EDGES, COMBOS, DETAILS = load_graph()
PROPERTY_COUNT = sum(len(detail["properties"]) for detail in DETAILS.values())

app = FastAPI(title="Camstar Ontology Presentation Demo")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/graph/overview")
def graph_overview():
    return JSONResponse({"nodes": NODES, "edges": EDGES, "combos": COMBOS})


@app.get("/api/graph/class/{class_name}")
def graph_class(class_name: str):
    return DETAILS.get(
        class_name,
        {"className": class_name, "properties": [], "outgoing": [], "incoming": []},
    )


@app.get("/api/graph/details")
def graph_details():
    return DETAILS


@app.get("/api/stats")
def stats():
    return {
        "classCount": len(NODES),
        "propertyCount": PROPERTY_COUNT,
        "relationCount": len(EDGES),
    }


@app.get("/api/config")
def config():
    return {"show_layout_switch": False, "wiki_review_required": False}


@app.get("/api/product-lines")
def product_lines():
    path = ONTOLOGY_DIR / "product_lines.json"
    return json.loads(path.read_text(encoding="utf-8-sig"))


@app.get("/api/i18n")
def i18n():
    return {
        "revision": 1,
        "translations": {"nodeDescriptions": {}, "propertyDescriptions": {}},
    }


@app.get("/api/chat/sessions")
def chat_sessions():
    return {"sessions": []}


@app.get("/api/wiki/relationship")
def wiki_relationship():
    return {"content": "", "exists": False}


@app.get("/healthz")
def healthz():
    return {"status": "ok", "source": "ontology-json"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5051)
