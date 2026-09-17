"""PostgreSQL implementation of the existing publish-model API.

Graph edits and their revision changes commit together. Frozen model content
and release metadata also commit together; no distributed transaction is needed.
"""
from copy import deepcopy
import uuid
from sqlalchemy import text
from src.graphstudio_sync.storage import ontology_store as store


def _rules():
    from src.graphstudio_sync.publishing import publish_ontology
    return publish_ontology


def ensure_publish_database(settings):
    with store.engine_for(settings) as engine:
        store.initialize(engine)
    return {"database": "graphsync", "backend": "postgres", "ready": True}


def _source_class(settings, class_name):
    payload = store.source_payload(settings)
    cls = next((c for c in payload["classes"] if c["name"] == class_name), None)
    return {"class": cls, "properties": [p for p in payload["properties"] if p["className"] == class_name]} if cls else None


def source_candidates(settings, query="", limit=100):
    payload = store.source_payload(settings)
    counts = {}
    for prop in payload["properties"]:
        counts[prop["className"]] = counts.get(prop["className"], 0) + 1
    return [{**c, "className": c["name"], "propertyCount": counts.get(c["name"], 0)}
            for c in sorted(payload["classes"], key=lambda c: c["name"])
            if query.strip().casefold() in (c["name"] + " " + str(c.get("chineseName") or "")).casefold()][:max(1, min(limit, 500))]


def workspace_graph(settings, workspace_key):
    with store.engine_for(settings) as engine, engine.connect() as conn:
        return store.workspace(conn, workspace_key)["graph"]


def _node(graph, uid):
    node = next((n for n in graph["nodes"] if n["id"] == uid), None)
    if node is None:
        raise KeyError(uid)
    return node


def _add_class(graph, workspace_key, source, target_name, role, orphan_policy, label=None, description=None):
    rules = _rules()
    if role not in rules.ALLOWED_ROLES or orphan_policy not in rules.ALLOWED_ORPHANS or not target_name.strip():
        raise ValueError("Invalid class governance policy or target name")
    source_name = source["class"]["name"] if source else None
    uid = f"{workspace_key}::{source_name or target_name.strip()}"
    # Idempotent addition must not re-enable properties the user has excluded.
    if any(n["id"] == uid for n in graph["nodes"]):
        return {"workspaceKey": workspace_key, "classUid": uid, "targetName": _node(graph, uid)["data"]["targetName"]}
    meta = source["class"] if source else {}
    props = source["properties"] if source else []
    folded = {p["name"].casefold(): p["name"] for p in props}
    graph["nodes"].append({"id": uid, "data": {"uid": uid, "workspaceKey": workspace_key,
        "sourceClass": source_name, "targetName": target_name.strip(), "role": role, "orphanPolicy": orphan_policy,
        **({"_semanticMapping": deepcopy(meta["_semanticMapping"])} if meta.get("_semanticMapping") else {}),
        "label": label or meta.get("chineseName") or target_name.strip(), "description": description or meta.get("description") or "",
        "origin": "source" if source else "custom", "labelMode": "auto", "emitRdfsLabel": True,
        "labelFallbacks": [folded[k] for k in ("name", "description") if k in folded] + ["$businessKey", "$primaryKey"],
        "searchFields": [folded[k] for k in ("displayname", "name", "description", "revision") if k in folded]}})
    graph["properties"].extend({"uid": f"{uid}::{p['name']}", "classUid": uid, "workspaceKey": workspace_key,
        "sourceName": p["name"], "targetName": p["name"], "sourcePath": f"{source_name}.{p['name']}",
        "dataType": p.get("dataType") or "String", "description": p.get("description") or "", "required": False,
        "published": True, "origin": "source"} for p in props)
    return {"workspaceKey": workspace_key, "classUid": uid, "targetName": target_name.strip()}


def add_class(settings, repository, *, workspace_key, source_class, target_name, role="context", orphan_policy="quarantine", label=None, description=None, touch_workspace=True):
    source = _source_class(settings, source_class) if source_class else None
    if source_class and not source:
        raise KeyError(source_class)
    return store.edit_graph(repository, workspace_key, lambda g: _add_class(g, workspace_key, source, target_name, role, orphan_policy, label, description))


def remove_class(settings, repository, workspace_key, class_uid):
    def edit(g):
        _node(g, class_uid)
        g["nodes"] = [n for n in g["nodes"] if n["id"] != class_uid]
        g["properties"] = [p for p in g["properties"] if p["classUid"] != class_uid]
        g["edges"] = [e for e in g["edges"] if class_uid not in (e["source"], e["target"])]
    return store.edit_graph(repository, workspace_key, edit)


def update_class(settings, repository, workspace_key, class_uid, values):
    rules = _rules()
    if values.get("role", "context") not in rules.ALLOWED_ROLES or values.get("orphanPolicy", "quarantine") not in rules.ALLOWED_ORPHANS:
        raise ValueError("Invalid class governance policy")
    if not str(values.get("targetName") or "").strip():
        raise ValueError("targetName is required")
    def edit(g):
        _node(g, class_uid)["data"].update({"targetName": values["targetName"].strip(), "label": values.get("label") or values["targetName"],
            "description": values.get("description") or "", "role": values.get("role", "context"), "orphanPolicy": values.get("orphanPolicy", "quarantine")})
    return store.edit_graph(repository, workspace_key, edit)


def update_presentation(settings, repository, workspace_key, class_uid, values):
    def edit(g):
        node = _node(g, class_uid)
        config = _rules().validate_presentation(values, [p for p in g["properties"] if p["classUid"] == class_uid])
        node["data"].update(config)
        return config
    return store.edit_graph(repository, workspace_key, edit)


def upsert_property(settings, repository, workspace_key, class_uid, values):
    target = str(values.get("targetName") or "").strip()
    if not target:
        raise ValueError("targetName is required")
    uid = str(values.get("uid") or f"{class_uid}::{values.get('propertyKey') or values.get('sourceName') or target}")
    def edit(g):
        _node(g, class_uid)
        current = next((p for p in g["properties"] if p["uid"] == uid), None)
        if current and current["classUid"] != class_uid:
            raise ValueError("Property belongs to another class")
        prop = {"uid": uid, "classUid": class_uid, "workspaceKey": workspace_key,
            "targetName": target, "sourceName": values.get("sourceName") or target, "sourcePath": values.get("sourcePath") or "",
            "dataType": values.get("dataType") or "String", "description": values.get("description") or "",
            "published": bool(values.get("published", True)), "required": bool(values.get("required", False)), "origin": values.get("origin") or "custom"}
        if current:
            current.update(prop)
        else:
            g["properties"].append(prop)
        return {"uid": uid}
    return store.edit_graph(repository, workspace_key, edit)


def _add_relationship(g, key, values):
    rules = _rules()
    usage, strength = values.get("usage") or "published_link", values.get("strength") or "context"
    if usage not in rules.ALLOWED_USAGE or strength not in rules.ALLOWED_STRENGTH:
        raise ValueError("Invalid relationship governance policy")
    source, target = values.get("sourceUid"), values.get("targetUid")
    name = str(values.get("targetName") or values.get("name") or "").strip()
    if not name:
        raise ValueError("targetName is required")
    _node(g, source)
    _node(g, target)
    rid = values.get("relationshipKey") or store.digest([source, name, target])[:24]
    data = {"relationshipKey": rid, "workspaceKey": key, "targetName": name,
        "sourceRelationship": values.get("sourceRelationship") or name, "usage": usage, "strength": strength,
        "cardinality": values.get("cardinality") or "many-to-one", "requiredContext": bool(values.get("requiredContext", False)),
        "questionEnabled": bool(values.get("questionEnabled", True)), "description": values.get("description") or ""}
    current = next((e for e in g["edges"] if e["id"] == rid), None)
    if current:
        if (current["source"], current["target"]) != (source, target):
            raise ValueError("Relationship identity cannot change endpoints")
        current["data"].update(data)
    else:
        g["edges"].append({"id": rid, "source": source, "target": target, "data": data})
    return {"relationshipKey": rid}


def add_relationship(settings, repository, workspace_key, values, *, touch_workspace=True):
    return store.edit_graph(repository, workspace_key, lambda g: _add_relationship(g, workspace_key, values))


def remove_relationship(settings, repository, workspace_key, relationship_key):
    def edit(g):
        g["edges"] = [e for e in g["edges"] if e["id"] != relationship_key]
    return store.edit_graph(repository, workspace_key, edit)


def create_workspace(settings, repository, *, profile_key, workspace_key, title, actor, seed_profile=True):
    if not _rules().WORKSPACE_KEY.fullmatch(workspace_key):
        raise ValueError("Invalid workspace key")
    graph = {"nodes": [], "edges": [], "properties": []}
    with repository.engine.begin() as conn:
        # Seed and revision metadata are one transaction, unlike the legacy path.
        payload = store.source_payload(settings, conn)
        if seed_profile:
            classes = conn.execute(text("SELECT class_name,role,orphan_policy FROM graphsync.profile_class WHERE profile_key=:profile AND enabled AND role <> 'excluded' ORDER BY priority,class_name"), {"profile": profile_key}).mappings().all()
            for row in classes:
                source = next((c for c in payload["classes"] if c["name"] == row["class_name"]), None)
                if source is None:
                    raise ValueError("Seed class missing from PostgreSQL source: " + row["class_name"])
                _add_class(graph, workspace_key, {"class": source, "properties": [p for p in payload["properties"] if p["className"] == source["name"]]}, source["name"], row["role"], row["orphan_policy"])
            relations = conn.execute(text("""SELECT r.relationship_name,s.class_name AS source,t.class_name AS target,r.required_context,r.semantic_role
                FROM graphsync.relationship_contract r JOIN graphsync.data_contract s ON s.contract_key=r.source_contract_key
                JOIN graphsync.data_contract t ON t.contract_key=r.target_contract_key WHERE r.profile_key=:profile AND r.status <> 'retired'"""), {"profile": profile_key}).mappings()
            ids = {n["id"] for n in graph["nodes"]}
            for rel in relations:
                source, target = f"{workspace_key}::{rel['source']}", f"{workspace_key}::{rel['target']}"
                if source in ids and target in ids:
                    _add_relationship(graph, workspace_key, {"sourceUid": source, "targetUid": target, "targetName": rel["relationship_name"], "requiredContext": rel["required_context"], "description": rel["semantic_role"]})
        wid = uuid.uuid4()
        conn.execute(text("""INSERT INTO graphsync.ontology_workspace(workspace_id,workspace_key,profile_key,title,graph_database,created_by,config)
            VALUES (:id,:key,:profile,:title,'graphsync',:actor,CAST(:config AS jsonb))"""),
            {"id": wid, "key": workspace_key, "profile": profile_key, "title": title, "actor": actor, "config": store.canonical({"backend": "postgres", "sourceHash": store.digest(payload)})})
        conn.execute(text("INSERT INTO graphsync.ontology_workspace_document(workspace_id,graph) VALUES (:id,CAST(:graph AS jsonb))"), {"id": wid, "graph": store.canonical(graph)})
    return _rules().ontology_governance_status(settings, repository, profile_key)


def review_workspace(settings, repository, workspace_key, actor):
    with repository.engine.begin() as conn:
        row = store.workspace(conn, workspace_key, lock=True)
        if row["status"] != "draft":
            raise ValueError("Only a draft workspace may be reviewed")
        validation = _rules().validate_graph(row, row["graph"])
        if not validation["valid"]:
            raise ValueError("Ontology validation failed")
        conn.execute(text("UPDATE graphsync.ontology_workspace SET status='reviewed',reviewed_by=:actor,reviewed_at=now() WHERE workspace_id=:id"), {"actor": actor, "id": row["workspace_id"]})
        return validation


def approve_workspace(settings, repository, workspace_key, actor):
    with repository.engine.begin() as conn:
        # Serializes numbering across workspaces; row locks serialize editing.
        conn.execute(text("SELECT pg_advisory_xact_lock(721603062)"))
        row = store.workspace(conn, workspace_key, lock=True)
        if row["status"] not in {"draft", "reviewed"}:
            raise ValueError("Only a draft workspace may be frozen")
        validation = _rules().validate_graph(row, row["graph"])
        if not validation["valid"]:
            raise ValueError("Ontology validation failed")
        duplicate = conn.execute(text("SELECT ontology_release_id,release_no,status FROM graphsync.ontology_release WHERE profile_key=:profile AND content_hash=:hash"), {"profile": row["profile_key"], "hash": validation["contentHash"]}).mappings().one_or_none()
        if duplicate:
            rid, number, status = str(duplicate["ontology_release_id"]), duplicate["release_no"], duplicate["status"]
        else:
            number = conn.execute(text("SELECT coalesce(max(release_no),0)+1 FROM graphsync.ontology_release WHERE profile_key=:profile"), {"profile": row["profile_key"]}).scalar_one()
            rid, status = str(uuid.uuid4()), "approved"
            counts = validation["counts"]
            conn.execute(text("""INSERT INTO graphsync.ontology_release(ontology_release_id,workspace_id,profile_key,release_no,graph_database,content_hash,class_count,property_count,relationship_count,approved_by,config)
                VALUES (:id,:wid,:profile,:number,'graphsync',:hash,:classes,:properties,:relationships,:actor,CAST(:config AS jsonb))"""),
                {"id": uuid.UUID(rid), "wid": row["workspace_id"], "profile": row["profile_key"], "number": number, "hash": validation["contentHash"], **counts, "actor": actor, "config": store.canonical({"workspaceRevision": row["revision"], "backend": "postgres"})})
            frozen = store.frozen_graph(row["graph"], rid)
            conn.execute(text("INSERT INTO graphsync.ontology_release_document(ontology_release_id,graph,document_hash) VALUES (:id,CAST(:graph AS jsonb),:hash)"), {"id": uuid.UUID(rid), "graph": store.canonical(frozen), "hash": store.digest(frozen)})
        conn.execute(text("UPDATE graphsync.ontology_workspace SET status='frozen' WHERE workspace_id=:id"), {"id": row["workspace_id"]})
    return {"releaseId": rid, "releaseNo": number, "status": status, "duplicate": bool(duplicate)}


def release_graph(settings, release_id):
    with store.engine_for(settings) as engine, engine.connect() as conn:
        row = conn.execute(text("SELECT graph,document_hash FROM graphsync.ontology_release_document WHERE ontology_release_id=:id"), {"id": uuid.UUID(str(release_id))}).mappings().one_or_none()
        if row is None:
            raise RuntimeError("发布模型版本未迁移到 PostgreSQL：" + str(release_id))
        if store.digest(row["graph"]) != row["document_hash"]:
            raise RuntimeError("PostgreSQL model release integrity check failed")
        return row["graph"]


def relationship_rows(settings, source_class, existing_names, depth):
    payload = store.source_payload(settings)
    classes = {c["name"]: c for c in payload["classes"]}
    adjacency = {}
    for r in sorted(payload["relationships"], key=lambda r: (r["source"], r["name"], r["target"])):
        adjacency.setdefault(r["source"], []).append((r["target"], r))
        adjacency.setdefault(r["target"], []).append((r["source"], r))
    rows, queue = [], [([source_class], [])]
    while queue and len(rows) < 100:
        names, relations = queue.pop(0)
        # Direct neighbors are useful next steps even for a one-object draft.
        # Longer paths remain limited to bridges back into the existing model.
        if relations and (len(relations) == 1 or names[-1] in existing_names):
            rows.append({"nodes": [{"sourceClass": n, "label": classes[n].get("chineseName") or n, "description": classes[n].get("description") or ""} for n in names],
                "relationships": [{"sourceClass": r["source"], "targetClass": r["target"], "targetName": r["name"], "cardinality": r.get("cardinality") or "many-to-one", "description": r.get("description") or "", "physicalColumn": r.get("physicalColumn"), "sourceFieldId": r.get("sourceFieldId")} for r in relations], "existingClass": names[-1]})
        if len(relations) < depth:
            for target, rel in adjacency.get(names[-1], []):
                if target not in names:
                    queue.append((names + [target], relations + [rel]))
    return rows


def apply_relationship_suggestions(settings, repository, workspace_key, class_uid, suggestion_ids):
    # Recompute server proposals, then require the same graph revision under lock.
    before = workspace_graph(settings, workspace_key)
    proposals = _rules().relationship_suggestions(settings, repository, workspace_key, class_uid)
    chosen = [p for p in proposals["items"] if p["id"] in set(suggestion_ids)]
    if not chosen or len(chosen) != len(set(suggestion_ids)):
        raise ValueError("关联建议已变化，请刷新")
    payload = store.source_payload(settings)
    batch = str(uuid.uuid4())
    def edit(g):
        if store.digest(g) != store.digest(before):
            raise ValueError("工作区已变化，请刷新关联建议")
        added, edges = [], []
        by_source = {n["data"].get("sourceClass") or n["data"]["targetName"]: n["id"] for n in g["nodes"]}
        for p in chosen:
            for n in p["missingNodes"]:
                name = n["sourceClass"]
                if name not in by_source:
                    cls = next(c for c in payload["classes"] if c["name"] == name)
                    result = _add_class(g, workspace_key, {"class": cls, "properties": [a for a in payload["properties"] if a["className"] == name]}, name, "context", "quarantine")
                    uid = result["classUid"]
                    by_source[name] = uid
                    _node(g, uid)["data"]["suggestionBatchId"] = batch
                    added.append(uid)
            for r in p["missingRelationships"]:
                source, target = by_source[r["sourceClass"]], by_source[r["targetClass"]]
                if any(e["source"] == source and e["target"] == target and e["data"]["targetName"] == r["targetName"] for e in g["edges"]):
                    continue
                rid = _add_relationship(g, workspace_key, {**r, "sourceUid": source, "targetUid": target})["relationshipKey"]
                next(e for e in g["edges"] if e["id"] == rid)["data"]["suggestionBatchId"] = batch
                edges.append(rid)
        return {"batchId": batch, "addedNodeUids": added, "addedRelationshipKeys": edges, "appliedSuggestionIds": [p["id"] for p in chosen]}
    return store.edit_graph(repository, workspace_key, edit)


def undo_relationship_suggestion_batch(settings, repository, workspace_key, batch_id):
    def edit(g):
        old = len(g["edges"])
        g["edges"] = [e for e in g["edges"] if e["data"].get("suggestionBatchId") != batch_id]
        connected = {uid for e in g["edges"] for uid in (e["source"], e["target"])}
        removed = {n["id"] for n in g["nodes"] if n["data"].get("suggestionBatchId") == batch_id and n["id"] not in connected}
        g["nodes"] = [n for n in g["nodes"] if n["id"] not in removed]
        g["properties"] = [p for p in g["properties"] if p["classUid"] not in removed]
        return {"batchId": batch_id, "removedRelationships": old - len(g["edges"]), "removedNodes": len(removed)}
    return store.edit_graph(repository, workspace_key, edit)
