"""Read-only coverage of the exact Graph Studio deployment serving questions."""

from src.query.graphstudio_assistant import discover_schema
from src.query.graphstudio_assistant import resolve_runtime_snapshot
from src.query.query_capabilities import ALIASES
from src.query.query_capabilities import local


def published_coverage(*, refresh=False):
    runtime = resolve_runtime_snapshot()
    rows = discover_schema(runtime, force_refresh=refresh)
    classes = {}
    relations = {}
    for row in rows:
        uri = row["class"]
        classes.setdefault(uri, {
            "uri": uri, "name": ALIASES.get(local(uri), (row.get("classLabel") or local(uri),))[0],
            "count": row.get("instanceCount"), "properties": set(),
        })
        if row.get("valueKind") == "属性":
            classes[uri]["properties"].add(row["property"])
        if row.get("valueKind") == "关系":
            key = (uri, row["property"], row.get("targetClass"))
            relations[key] = {
                "uri": row["property"], "name": row.get("propertyLabel") or local(row["property"]),
                "source": uri, "target": row.get("targetClass"),
                "count": row.get("relationshipCount"),
                "questionEnabled": row.get("questionEnabled", True),
            }
    items = [{**value, "propertyCount": len(value["properties"])} for value in classes.values()]
    for value in items:
        value.pop("properties")
    links = list(relations.values())
    return {
        "runtime": runtime, "classes": items, "relationships": links,
        "summary": {
            "definedClasses": len(classes), "classesWithData": sum((x["count"] or 0) > 0 for x in items),
            "definedRelationships": len(links), "relationshipsWithData": sum((x["count"] or 0) > 0 for x in links),
            "unknownClassCounts": sum(x["count"] is None for x in items),
            "unknownRelationshipCounts": sum(x["count"] is None for x in links),
        },
    }
