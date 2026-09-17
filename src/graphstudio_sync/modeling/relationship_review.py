"""Review evidence is tied to an immutable source and the current object definition."""
from copy import deepcopy
from datetime import datetime, timezone

from src.graphstudio_sync.storage.ontology_store import digest


def fingerprint(draft, field):
    design = draft["design"]
    return digest({"snapshot": draft["snapshotId"], "table": draft["tableName"], "field": field,
                   "role": design.get("role"), "name": design.get("chineseName"),
                   "definition": design.get("description"),
                   "selection": design["fields"].get(field["name"])})


def current_review(draft, field):
    record = draft["design"].get("relationshipReviews", {}).get(field["name"])
    return record if record and record.get("fingerprint") == fingerprint(draft, field) else None


def confirm(draft, field_name, meaning, actor):
    field = next((f for f in draft["fields"] if f["name"] == field_name), None)
    if not field or field["type"] != "Navigation" or draft["design"]["fields"].get(field_name) != "relationship":
        raise ValueError("请先选择有物理依据的业务关系并保存")
    if draft["design"]["role"] != "entity":
        raise ValueError("只有实体来源可确认业务关系")
    if not meaning.strip() or not actor.strip():
        raise ValueError("请填写关系业务含义和确认人")
    design = deepcopy(draft["design"])
    record = {"field": field_name, "meaning": meaning.strip(), "actor": actor.strip(),
              "confirmedAt": datetime.now(timezone.utc).isoformat(),
              "fingerprint": fingerprint(draft, field), "sourceRevision": draft["revision"],
              "snapshotId": draft["snapshotId"], "sourceTable": draft["tableName"],
              "sourceField": field["physicalName"], "targetTable": field["target"],
              "targetField": field.get("targetField", "")}
    design.setdefault("relationshipReviews", {})[field_name] = record
    design.setdefault("relationshipReviewHistory", []).append(record)
    return design


def preserve_records(current, design):
    """Ordinary draft saves cannot fabricate, replace or erase review history."""
    result = deepcopy(design)
    result["relationshipReviewHistory"] = deepcopy(current["design"].get("relationshipReviewHistory", []))
    draft = {**current, "design": result}
    result["relationshipReviews"] = {
        field["name"]: deepcopy(record) for field in current["fields"]
        if (record := current["design"].get("relationshipReviews", {}).get(field["name"]))
        and record.get("fingerprint") == fingerprint(draft, field)
    }
    return result
