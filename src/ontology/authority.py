"""Source-backed ontology directory and explicit, non-destructive merge plans."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from src.ontology.physical_naming import relation_name
from src.graphstudio_sync.modeling.semantic_mapping import source_fields

GROUPS = {
    "组织与位置": ["Enterprise", "Site", "Factory", "WorkCenter", "ss_MfgLine", "Organization"],
    "产品与计量": ["Product", "ProductBase", "ProductFamily", "UOM"],
    "人员与职责": ["Employee", "RoleDef", "Team"],
    "设备与资源": ["ResourceDef", "ResourceFamily", "ResourceType"],
    "后续共享对象": ["Vendor", "Customer", "Owner", "Location"],
    "首期业务骨架（不归公共主数据）": ["MfgOrder", "Container", "Workflow", "WorkflowStep", "Spec", "Operation"],
}
from scripts.validate_ontology_vs_csv import canonical_physical_fields, expected_type, normalize_field_name, TYPE_EQUIVALENTS

ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY_DIR = ROOT / "src/ontology/semantic_references"
FIELDS_FILE = ROOT / "docs/Database_Fields.csv"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read_library():
    documents = {}
    for path in sorted(ONTOLOGY_DIR.glob("*_ontology.json")):
        documents[path.name] = json.loads(path.read_text(encoding="utf-8-sig"))
    return documents


def physical_catalog():
    rows = defaultdict(list)
    with FIELDS_FILE.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows[row["CDOName"]].append(row)
    return rows


def sources_for(name, documents, proposals=None):
    sources = []
    for filename, document in documents.items():
        for cls in document.get("classes", []):
            if cls["className"] == name:
                sources.append({"id": filename, "definition": cls})
    for proposal in proposals or []:
        for cls in proposal["payload"].get("classes", []):
            if cls["className"] == name:
                sources.append({"id": "candidate:" + proposal["proposal_id"], "definition": cls})
    return sources


def class_detail(name, documents, authority=None, proposals=None, fields=None):
    sources = sources_for(name, documents, proposals)
    if authority:
        sources.insert(0, {"id": "approved", "definition": authority["model"]["class"]})
    if not sources:
        raise ValueError("本体类不存在")
    fields = physical_catalog() if fields is None else fields
    variants = defaultdict(dict)
    for source in sources:
        for prop in source["definition"].get("properties", []):
            variants[prop["name"]][source["id"]] = prop
    physical = {normalize_field_name(row, name): row for row in canonical_physical_fields(fields.get(name, []), name)}
    conflicts = []
    for key, versions in variants.items():
        if len({v.get("type", "String") for v in versions.values()}) > 1:
            field = physical.get(key)
            conflicts.append({"property": key, "variants": versions,
                              "expectedType": expected_type(field) if field else None,
                              "physicalField": field.get("FieldName") if field else None})
    relations = []
    for filename, doc in documents.items():
        relations.extend({**r, "source": filename} for r in doc.get("relationships", []) if r["fromClass"] == name)
    for proposal in proposals or []:
        relations.extend({**r, "source": "candidate:" + proposal["proposal_id"]} for r in proposal["payload"].get("relationships", []) if r["fromClass"] == name)
    if authority:
        relations = [{**r, "source": "approved"} for r in authority["model"].get("relationships", [])] + relations
    content = {"sources": sources, "relations": relations, "physical": fields.get(name, []), "revision": authority["revision"] if authority else 0}
    library_fingerprint = digest({"sources": [s for s in sources if s["id"] != "approved" and not s["id"].startswith("candidate:")],
                                  "relations": [r for r in relations if r["source"] != "approved" and not r["source"].startswith("candidate:")],
                                  "physical": fields.get(name, [])})
    return {"className": name, "sources": sources, "conflicts": conflicts, "relationships": relations,
            "primaryKeys": [r["FieldName"] for r in fields.get(name, []) if r.get("IsPrimaryKey") == "True"],
            "revision": content["revision"], "fingerprint": digest(content),
            "authority": authority, "physical": physical, "physicalFields": source_fields(name, fields.get(name, [])), "libraryFingerprint": library_fingerprint}


def directory(documents, authorities, proposals):
    names = {c["className"] for d in documents.values() for c in d.get("classes", [])}
    names.update(authorities)
    names.update(c["className"] for p in proposals for c in p["payload"].get("classes", []))
    groups = {name: group for group, classes in GROUPS.items() for name in classes}
    rows = []
    fields = physical_catalog()
    for name in sorted(names):
        authority = authorities.get(name)
        detail = class_detail(name, documents, authority, proposals, fields)
        preferred = authority["model"]["class"] if authority else next((s["definition"] for s in detail["sources"] if s["definition"].get("chineseName")), detail["sources"][0]["definition"])
        source_count = len([s for s in detail["sources"] if s["id"] != "approved"])
        rows.append({"className": name, "chineseName": preferred.get("chineseName") or name,
                     "group": authority.get("domain") if authority else groups.get(name, "其他业务与辅助对象"),
                     "sourceCount": source_count, "conflictCount": len(detail["conflicts"]),
                     "propertyCount": len(preferred.get("properties", [])),
                     "revision": detail["revision"], "status": "changed" if authority and authority["decision"].get("libraryFingerprint") != detail["libraryFingerprint"] else "synced" if authority and authority.get("synced_revision") == authority["revision"] else "approved" if authority else "review",
                     "pendingCandidateCount": sum(s["id"].startswith("candidate:") for s in detail["sources"]),
                     "primaryKeys": detail["primaryKeys"]})
    return {"items": rows, "groups": list(GROUPS) + ["其他业务与辅助对象"],
            "summary": {"classes": len(rows), "duplicates": sum(r["sourceCount"] > 1 for r in rows),
                        "conflicts": sum(r["conflictCount"] > 0 for r in rows), "approved": len(authorities)}}


def merge_plan(detail, preferred_source, choices, domain, chinese_name=None, description=None):
    sources = {s["id"]: s["definition"] for s in detail["sources"]}
    if preferred_source not in sources:
        raise ValueError("请选择当前可用的权威来源")
    if not domain.strip() or len(domain) > 80:
        raise ValueError("请填写不超过 80 字的所属领域")
    base = copy.deepcopy(sources[preferred_source])
    if chinese_name is not None:
        base["chineseName"] = chinese_name.strip()
    if description is not None:
        base["description"] = description.strip()
    # Keep unique properties from all definitions; the selected source owns
    # labels and descriptions, while incompatible types require explicit choices.
    properties = {}
    for key in [k for k in sources if k != preferred_source] + [preferred_source]:
        for prop in sources[key].get("properties", []):
            properties[prop["name"]] = copy.deepcopy(prop)
    # A reviewed source mapping is an allowlist, not another definition to
    # union. New source fields must never resurrect excluded attributes.
    mapping = base.get("_semanticMapping") or sources.get("approved", {}).get("_semanticMapping")
    if mapping is None:
        mapping = next((s.get("_semanticMapping") for s in reversed(list(sources.values())) if s.get("_semanticMapping")), None)
    if mapping:
        base["_semanticMapping"] = copy.deepcopy(mapping)
        allowed = {k for k, role in mapping["fieldRoles"].items() if role in {"property", "relationship"}}
        properties = {k: p for k, p in properties.items() if k in allowed}
    for conflict in detail["conflicts"]:
        key = conflict["property"]
        if mapping and key not in properties:
            continue
        source = choices.get(key)
        if source not in conflict["variants"]:
            raise ValueError(f"请明确选择 {key} 的类型来源")
        properties[key] = copy.deepcopy(conflict["variants"][source])
    blockers = []
    if mapping and mapping.get("sourceFields") != detail["physicalFields"]:
        blockers.append("映射来源与项目 CSV 物理结构不一致，请重新读取结构并评估映射")
    if not detail["physical"]:
        blockers.append("本地物理事实来源未匹配此类字段，请先核实 CSV 来源")
    if not base.get("chineseName", "").strip() or not base.get("description", "").strip():
        blockers.append("请补充业务中文名和业务定义")
    for key, prop in properties.items():
        physical = detail["physical"].get(key)
        if physical:
            expected = expected_type(physical)
            if prop.get("type") not in TYPE_EQUIVALENTS.get(expected, {expected}):
                blockers.append(f"{key} 与物理字段类型不符，应使用 {expected}")
    base["properties"] = sorted(properties.values(), key=lambda p: p["name"])
    edges = {}
    ordered = sorted(detail["relationships"], key=lambda r: r["source"] == preferred_source)
    for rel in ordered:
        rel = {k: v for k, v in rel.items() if k != "source"}
        if mapping:
            relation_fields = {relation_name(k): detail["physical"].get(k, {}).get("FKTableName")
                               for k, role in mapping["fieldRoles"].items() if role == "relationship"}
            if relation_fields.get(rel["relationName"]) != rel["toClass"]:
                continue
        edges[(rel["fromClass"], rel["relationName"], rel["toClass"])] = rel
    previous = (detail.get("authority") or {}).get("model", {}).get("class", sources[preferred_source])
    before = {p["name"]: p for p in previous.get("properties", [])}
    changes = [{"property": k, "before": before.get(k), "after": p} for k, p in properties.items() if before.get(k) != p]
    changes.extend({"property": k, "before": p, "after": None} for k, p in before.items() if k not in properties)
    model = {"class": base, "relationships": list(edges.values())}
    plan = {"className": detail["className"], "preferredSource": preferred_source,
            "domain": domain.strip(), "choices": choices, "fingerprint": detail["fingerprint"],
            "libraryFingerprint": detail["libraryFingerprint"],
            "revision": detail["revision"], "model": model, "changes": changes, "blockers": blockers,
            "extensionProperties": sorted(k for k in properties if k not in detail["physical"]),
            "note": "按来源映射的字段用途生成模型；内部及不纳入字段不会被其他来源重新加入。保存后需同步建模库，再按现有流程发布。" if mapping else "保留各来源独有属性与关系；同类型描述及同名关系元数据以所选来源优先。保存后需同步建模库，再按现有流程发布。"}
    plan["planHash"] = digest(plan)
    return plan


def governed_documents(documents, authorities):
    """Replace duplicate declarations with reviewed snapshots for every loader."""
    result = copy.deepcopy(documents)
    for doc in result.values():
        doc["classes"] = [c for c in doc.get("classes", []) if c["className"] not in authorities]
        doc["relationships"] = [r for r in doc.get("relationships", []) if r["fromClass"] not in authorities]
    result["reviewed_authority"] = {
        "classes": [{**a["model"]["class"], "_authorityDomain": a.get("domain", "reviewed_authority")} for a in authorities.values()],
        "relationships": [r for a in authorities.values() for r in a["model"].get("relationships", [])],
    }
    return result
