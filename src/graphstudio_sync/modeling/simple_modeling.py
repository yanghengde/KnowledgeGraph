"""One reviewed operation from a saved field selection to a publish workspace."""
from copy import deepcopy
from sqlalchemy import text

from src.graphstudio_sync.storage import ontology_store as store
from src.graphstudio_sync.modeling.semantic_mapping import candidate_preview
from src.graphstudio_sync.publishing.publish_ontology_postgres import _add_class
from src.graphstudio_sync.publishing.publish_ontology_postgres import _add_relationship
from src.ontology.physical_naming import relation_name


def prepare(draft, documents, authorities, proposals, workspace, source):
    from src.ontology import authority
    preview = candidate_preview(draft)
    proposal_id = "simple-" + draft["draftId"]
    detail = authority.class_detail(draft["tableName"], documents, authorities.get(draft["tableName"]),
                                    [*proposals, {"proposal_id": proposal_id, "payload": preview["payload"]}])
    preferred = "candidate:" + proposal_id
    choices = {c["property"]: preferred for c in detail["conflicts"] if preferred in c["variants"]}
    plan = authority.merge_plan(detail, preferred, choices,
                                (detail.get("authority") or {}).get("domain") or "制造模型")
    blockers = [*preview["blockers"], *plan["blockers"]]
    if not preview["counts"]["properties"] and not preview["counts"]["relationships"]:
        blockers.append("请至少勾选一个业务字段或关联")
    if workspace["status"] == "retired":
        blockers.append("当前发布模型已停用，请选择可用模型")
    graph = deepcopy(workspace["graph"])
    name = draft["tableName"]
    existing = next((n for n in graph["nodes"] if n["data"].get("sourceClass") == name), None)
    targets = {n["data"].get("sourceClass"): n["id"] for n in graph["nodes"]}
    for rel in plan["model"]["relationships"]:
        if rel["toClass"] != name and rel["toClass"] not in targets:
            blockers.append(f"关联表 {rel['toClass']} 尚未加入发布模型；请先完成该表，或暂不勾选此关联")
    uid = existing["id"] if existing else f"{workspace['workspace_key']}::{name}"
    if uid != f"{workspace['workspace_key']}::{name}":
        blockers.append("此对象使用自定义标识，请在高级管理中调整")
    old_props = {p["sourceName"]: p for p in graph["properties"] if p["classUid"] == uid and p.get("sourceName")}
    # This confirmation applies the operator's selected fields. Other classes
    # and custom properties remain intact; old physical links follow selection.
    graph["nodes"] = [n for n in graph["nodes"] if n["id"] != uid]
    graph["properties"] = [p for p in graph["properties"] if p["classUid"] != uid or p.get("origin") == "custom"]
    physical_links = {relation_name(f["name"]) for f in draft["fields"] if f["type"] == "Navigation"}
    graph["edges"] = [e for e in graph["edges"] if not (e["source"] == uid and e["data"].get("sourceRelationship") in physical_links)]
    cls = plan["model"]["class"]
    meta = {**cls, "name": name}
    _add_class(graph, workspace["workspace_key"], {"class": meta, "properties": [{**p, "dataType": p["type"]} for p in cls["properties"]]},
               existing["data"]["targetName"] if existing else name,
               existing["data"]["role"] if existing else "context" if any(n["data"].get("role") == "core" for n in graph["nodes"]) else "core",
               existing["data"]["orphanPolicy"] if existing else "quarantine")
    for p in graph["properties"]:
        if p["classUid"] == uid and p.get("origin") == "source" and p["sourceName"] in old_props:
            p["targetName"] = old_props[p["sourceName"]]["targetName"]
    if existing:
        replacement = next(n for n in graph["nodes"] if n["data"].get("sourceClass") == name)
        for key in ("labelMode", "labelField", "labelTemplate", "labelFallbacks", "searchFields", "emitRdfsLabel"):
            if key in existing["data"]:
                replacement["data"][key] = deepcopy(existing["data"][key])
    targets[name] = uid
    if not blockers:
        for rel in plan["model"]["relationships"]:
            _add_relationship(graph, workspace["workspace_key"], {"sourceUid": uid, "targetUid": targets[rel["toClass"]],
                              "targetName": rel["relationName"], "sourceRelationship": rel["relationName"],
                              "cardinality": rel.get("cardinality", "MANY_TO_ONE").lower().replace("_", "-"), "usage": "published_link"})
    payload = deepcopy(source)
    payload["classes"] = [c for c in source["classes"] if c["name"] != name] + [{**meta, "module": plan["domain"], "layer": "Config", "authorityRevision": plan["revision"] + 1}]
    payload["properties"] = [p for p in source["properties"] if p["className"] != name] + [{**p, "className": name, "dataType": p["type"]} for p in cls["properties"]]
    payload["relationships"] = [r for r in source["relationships"] if r["source"] != name] + [{**r, "source": name, "target": r["toClass"], "name": r["relationName"]} for r in plan["model"]["relationships"]]
    if not blockers:
        store.validate_source(payload)
    result = {"plan": plan, "graph": graph, "source": payload, "blockers": list(dict.fromkeys(blockers)),
              "counts": preview["counts"], "revision": draft["revision"], "workspaceRevision": workspace["revision"],
              "fields": [{"name": p["name"], "type": p["type"]} for p in cls["properties"]],
              "removedFields": [p["sourceName"] for p in old_props.values() if p.get("origin") != "custom" and p["sourceName"] not in {v["name"] for v in cls["properties"]}]}
    result["planHash"] = store.digest(result)
    return result


def commit(conn, authority_store, workspace, prepared):
    if prepared["blockers"]:
        raise ValueError("；".join(prepared["blockers"]))
    result = authority_store.save(conn, {**prepared["plan"], "simplePlanHash": prepared["planHash"]})
    store.save_source(conn, prepared["source"], {"kind": "simple-modeling", "planHash": prepared["planHash"]}, activate=True)
    conn.execute(text("UPDATE graphsync.ontology_authority SET synced_revision=:revision WHERE class_name=:name"),
                 {"revision": result["revision"], "name": prepared["plan"]["className"]})
    conn.execute(text("UPDATE graphsync.ontology_workspace_document SET graph=CAST(:graph AS jsonb),updated_at=now() WHERE workspace_id=:id"),
                 {"graph": store.canonical(prepared["graph"]), "id": workspace["workspace_id"]})
    conn.execute(text("UPDATE graphsync.ontology_workspace SET revision=revision+1,status='draft',reviewed_by=NULL,reviewed_at=NULL,updated_at=now() WHERE workspace_id=:id"), {"id": workspace["workspace_id"]})
    return {"status": "ready", "revision": result["revision"]}
