"""PostgreSQL model review, validation, activation and publication rules."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any

from sqlalchemy import text

from src.qa.sql_query_builder import build_query_builder_plan

from .config import SyncSettings
from .entity_labels import published_scalar_names, suggest_label_template, validate_presentation
from .repository import ControlPlaneRepository


WORKSPACE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,119}$")
ALLOWED_ROLES = {"core", "context", "reference", "on_demand", "excluded"}
ALLOWED_ORPHANS = {"reject", "quarantine", "allow", "referenced_only"}
ALLOWED_USAGE = {"published_link", "projection_only", "context_only", "excluded"}
ALLOWED_STRENGTH = {"core", "context", "weak", "on_demand"}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _relationship_name_from_join(join: dict[str, Any]) -> str:
    field = str(join.get("from_field") or "").strip()
    field = re.sub(r"(?:Def|Ref)?Id$", "", field, flags=re.IGNORECASE)
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+", field)
    suffix = "_".join(word.upper() for word in words if word)
    return f"HAS_{suffix}" if suffix else "RELATED_TO"


def build_discovery_plan(
    settings: SyncSettings,
    selected_classes: list[str],
    *,
    dialect: str = "sqlserver",
) -> dict[str, Any]:
    """Combine verified physical paths with source-ontology semantics.

    This is deliberately read-only.  The result is a proposal that must be
    reviewed in the publish workspace before it becomes part of a release.
    """
    plan = build_query_builder_plan(selected_classes, dialect=dialect)
    planned_names = [str(item["id"]) for item in plan.get("nodes", [])]
    selected = [str(item) for item in plan.get("selected_nodes", [])]
    semantic_rows: list[dict[str, Any]] = []
    neighbor_rows: list[dict[str, Any]] = []
    from .ontology_store import source_payload
    payload = source_payload(settings)
    classes = {c["name"]: c for c in payload["classes"]}
    semantic_rows = [r for r in payload["relationships"] if r["source"] in planned_names and r["target"] in planned_names]
    for r in payload["relationships"]:
        for anchor, target in ((r["source"], r["target"]), (r["target"], r["source"])):
            if anchor in selected and target not in planned_names:
                neighbor_rows.append({"anchor": anchor, "className": target, "chineseName": classes[target].get("chineseName"), "relationship": r["name"], "cardinality": r.get("cardinality")})
    neighbor_rows = neighbor_rows[:80]

    semantic_by_pair: dict[frozenset[str], list[dict[str, Any]]] = {}
    for item in semantic_rows:
        semantic_by_pair.setdefault(
            frozenset((str(item["source"]), str(item["target"]))), [],
        ).append(_json_value(dict(item)))

    enriched_joins = []
    for join in plan.get("joins", []):
        item = dict(join)
        candidates = semantic_by_pair.get(
            frozenset((str(item["from_table"]), str(item["to_table"]))), [],
        )
        physical_name = _relationship_name_from_join(item)
        recommended = next(
            (candidate for candidate in candidates if str(candidate.get("name") or "").upper() == physical_name),
            candidates[0] if candidates else None,
        )
        item["semantic_candidates"] = candidates
        item["recommended_name"] = (
            str(recommended["name"]) if recommended else physical_name
        )
        item["recommended_source"] = (
            str(recommended["source"]) if recommended else str(item["from_table"])
        )
        item["recommended_target"] = (
            str(recommended["target"]) if recommended else str(item["to_table"])
        )
        item["cardinality"] = (
            str(recommended.get("cardinality") or "many-to-one")
            if recommended else "many-to-one"
        )
        enriched_joins.append(item)

    plan["joins"] = enriched_joins
    plan["semantic_relationships"] = [_json_value(dict(item)) for item in semantic_rows]
    plan["neighbor_suggestions"] = [_json_value(dict(item)) for item in neighbor_rows]
    plan["proposal_only"] = True
    return plan


def _workspace_row(repository: ControlPlaneRepository, workspace_key: str) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        row = connection.execute(
            text("SELECT * FROM graphsync.ontology_workspace WHERE workspace_key=:key"),
            {"key": workspace_key},
        ).mappings().one_or_none()
    if not row:
        raise KeyError(workspace_key)
    return dict(row)


def relationship_suggestions(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    workspace_key: str,
    class_uid: str,
    *,
    max_depth: int = 2,
) -> dict[str, Any]:
    """Find reviewable source-ontology paths from one draft class to the draft graph."""
    _workspace_row(repository, workspace_key)
    graph = workspace_graph(settings, workspace_key)
    selected = next((item for item in graph["nodes"] if item["id"] == class_uid), None)
    if not selected:
        raise KeyError(class_uid)
    source_class = selected["data"].get("sourceClass")
    if not source_class:
        return {"classUid": class_uid, "sourceClass": None, "items": [], "reason": "custom_class_has_no_source_ontology"}

    current_by_source = {
        str(item["data"].get("sourceClass") or item["data"].get("targetName")): item
        for item in graph["nodes"]
    }
    existing_names = sorted(name for name in current_by_source if name != source_class)
    if not existing_names:
        return {"classUid": class_uid, "sourceClass": source_class, "items": [], "reason": "workspace_has_no_other_source_classes"}

    depth = max(1, min(int(max_depth), 2))
    from .publish_ontology_postgres import relationship_rows
    rows = relationship_rows(settings, source_class, existing_names, depth)

    existing_edges = {
        (
            next((item["data"].get("sourceClass") or item["data"].get("targetName") for item in graph["nodes"] if item["id"] == edge["source"]), ""),
            str(edge["data"].get("targetName") or edge["data"].get("relationshipKey")),
            next((item["data"].get("sourceClass") or item["data"].get("targetName") for item in graph["nodes"] if item["id"] == edge["target"]), ""),
        )
        for edge in graph["edges"]
    }
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        nodes = [_json_value(dict(item)) for item in row["nodes"]]
        relationships = [_json_value(dict(item)) for item in row["relationships"]]
        signature = "|".join(
            f"{item['sourceClass']}::{item['targetName']}::{item['targetClass']}"
            for item in relationships
        )
        if not signature or signature in seen:
            continue
        seen.add(signature)
        missing_nodes = [item for item in nodes if item["sourceClass"] not in current_by_source]
        missing_relationships = [
            item for item in relationships
            if (item["sourceClass"], item["targetName"], item["targetClass"]) not in existing_edges
        ]
        if not missing_relationships:
            continue
        existing = current_by_source.get(str(row["existingClass"]))
        bridge_names = {item["sourceClass"] for item in missing_nodes}
        score = 100 - 25 * (len(relationships) - 1)
        if existing and existing["data"].get("role") == "core":
            score += 10
        if "WorkflowStep" in bridge_names:
            score += 20
        if any(item["targetName"] == "HAS_SPEC" for item in relationships):
            score += 8
        if any(item["targetName"] == "HAS_FIRST_STEP" for item in relationships):
            score += 15
        elif any(item["targetName"] == "HAS_SUB_WORKFLOW" for item in relationships):
            score += 5
        proposal_id = _hash([workspace_key, class_uid, signature])[:24]
        items.append({
            "id": proposal_id,
            "anchorClass": source_class,
            "existingClass": row["existingClass"],
            "nodes": nodes,
            "relationships": relationships,
            "missingNodes": missing_nodes,
            "missingRelationships": missing_relationships,
            "score": score,
            "summary": f"新增 {len(missing_nodes)} 个对象、{len(missing_relationships)} 条关系",
        })
    items.sort(key=lambda item: (-item["score"], len(item["missingNodes"]), item["existingClass"], item["id"]))
    for index, item in enumerate(items):
        item["recommended"] = index == 0
    return {"classUid": class_uid, "sourceClass": source_class, "items": items[:30], "reason": None}


def validate_workspace(settings: SyncSettings, repository: ControlPlaneRepository, workspace_key: str) -> dict[str, Any]:
    workspace = _workspace_row(repository, workspace_key)
    graph = workspace_graph(settings, workspace_key)
    return validate_graph({**workspace, "workspace_key": workspace_key}, graph)


def validate_graph(workspace, graph):
    workspace_key = workspace["workspace_key"]
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    nodes = graph["nodes"]
    edges = graph["edges"]
    if not nodes:
        errors.append({"code": "model.empty", "message": "发布本体至少需要一个对象"})
    if nodes and not any(item["data"].get("role") == "core" for item in nodes):
        errors.append({"code": "model.no_core", "message": "至少需要一个核心对象"})
    names = [str(item["data"].get("targetName") or "").casefold() for item in nodes]
    if len(names) != len(set(names)):
        errors.append({"code": "class.duplicate_target", "message": "目标对象名称必须唯一"})
    property_names: dict[str, set[str]] = {}
    properties_by_class: dict[str, list[dict[str, Any]]] = {}
    for prop in graph["properties"]:
        if not prop.get("published"):
            continue
        class_uid = prop.get("classUid")
        name = str(prop.get("targetName") or "").strip()
        if not name or not prop.get("dataType"):
            errors.append({"code": "property.incomplete", "message": f"属性 {prop.get('uid')} 缺少名称或类型"})
        seen = property_names.setdefault(class_uid, set())
        properties_by_class.setdefault(class_uid, []).append(prop)
        if name.casefold() in seen:
            errors.append({"code": "property.duplicate_target", "message": f"对象内存在重复属性：{name}"})
        seen.add(name.casefold())
    for item in nodes:
        class_uid = item["id"]
        data = item["data"]
        properties = properties_by_class.get(class_uid, [])
        try:
            validate_presentation({
                "labelMode": data.get("labelMode") or "auto",
                "labelField": data.get("labelField"),
                "labelTemplate": data.get("labelTemplate"),
                "labelFallbacks": data.get("labelFallbacks") or [],
                "searchFields": data.get("searchFields") or [],
                "emitRdfsLabel": data.get("emitRdfsLabel", True),
            }, properties)
        except ValueError as exc:
            errors.append({
                "code": "class.presentation_invalid",
                "message": f"对象 {data.get('targetName')} 的显示配置无效：{exc}",
            })
            continue
        if not published_scalar_names(properties) or (
            (data.get("labelMode") or "auto") == "auto"
            and not suggest_label_template(properties)
        ):
            warnings.append({
                "code": "class.label_fallback_primary_key",
                "message": f"对象 {data.get('targetName')} 没有可用显示属性，将回退到业务键或主键",
            })
    degree = {item["id"]: 0 for item in nodes}
    for edge in edges:
        if edge["data"].get("usage") == "excluded":
            continue
        degree[edge["source"]] = degree.get(edge["source"], 0) + 1
        degree[edge["target"]] = degree.get(edge["target"], 0) + 1
    if len(nodes) > 1:
        for item in nodes:
            if degree.get(item["id"], 0) != 0 or item["data"].get("role") == "excluded":
                continue
            if item["data"].get("role") == "core":
                errors.append({"code": "class.isolated_core", "message": f"核心对象 {item['data'].get('targetName')} 没有上下文关联"})
            else:
                warnings.append({"code": "class.isolated_context", "message": f"发布对象 {item['data'].get('targetName')} 尚未接入当前图谱"})
    for item in nodes:
        if not item["data"].get("sourceClass"):
            warnings.append({"code": "class.custom_without_source", "message": f"自定义对象 {item['data'].get('targetName')} 尚无实例来源"})
    snapshot = {
        "workspace": workspace_key,
        "revision": workspace["revision"],
        "nodes": nodes,
        "edges": edges,
        "properties": graph["properties"],
    }
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "contentHash": _hash(snapshot),
        "counts": {"classes": len(nodes), "properties": len(graph["properties"]), "relationships": len(edges)},
    }


def initialize_governance(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    actor: str,
) -> dict[str, Any]:
    ensure_publish_database(settings)
    with repository.engine.connect() as connection:
        existing = connection.execute(
            text("SELECT workspace_key FROM graphsync.ontology_workspace WHERE profile_key=:profile ORDER BY created_at DESC LIMIT 1"),
            {"profile": profile_key},
        ).scalar_one_or_none()
    if existing:
        return ontology_governance_status(settings, repository, profile_key)
    return create_workspace(
        settings,
        repository,
        profile_key=profile_key,
        workspace_key=f"{profile_key}-draft",
        title="Graph Studio 发布本体",
        actor=actor,
        seed_profile=True,
    )




def activate_release(repository: ControlPlaneRepository, profile_key: str, release_id: uuid.UUID, actor: str) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": "ontology-activate:" + profile_key})
        from .ontology_store import digest
        document = connection.execute(text("SELECT graph,document_hash FROM graphsync.ontology_release_document WHERE ontology_release_id=:id"), {"id": release_id}).mappings().one_or_none()
        if document is None or digest(document["graph"]) != document["document_hash"]:
            raise ValueError("PostgreSQL model release is missing or corrupt; activation blocked")
        release = connection.execute(
            text("SELECT ontology_release_id, status FROM graphsync.ontology_release WHERE ontology_release_id=:id AND profile_key=:profile FOR UPDATE"),
            {"id": release_id, "profile": profile_key},
        ).mappings().one_or_none()
        if not release or release["status"] not in {"approved", "active", "superseded"}:
            raise KeyError(release_id)
        current = connection.execute(
            text("SELECT active_release_id FROM graphsync.ontology_release_activation WHERE profile_key=:profile FOR UPDATE"),
            {"profile": profile_key},
        ).scalar_one_or_none()
        if current == release_id:
            previous = connection.execute(text("SELECT previous_release_id FROM graphsync.ontology_release_activation WHERE profile_key=:profile"), {"profile": profile_key}).scalar_one_or_none()
            return {"profileKey": profile_key, "activeReleaseId": str(release_id), "previousReleaseId": str(previous) if previous else None}
        if current and current != release_id:
            connection.execute(text("UPDATE graphsync.ontology_release SET status='superseded' WHERE ontology_release_id=:id"), {"id": current})
        connection.execute(
            text("UPDATE graphsync.ontology_release SET status='active', activated_at=now() WHERE ontology_release_id=:id"),
            {"id": release_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO graphsync.ontology_release_activation
                    (profile_key, active_release_id, previous_release_id, activated_by)
                VALUES (:profile, :active, :previous, :actor)
                ON CONFLICT (profile_key) DO UPDATE SET
                    previous_release_id=graphsync.ontology_release_activation.active_release_id,
                    active_release_id=EXCLUDED.active_release_id,
                    activated_at=now(), activated_by=EXCLUDED.activated_by
                """
            ),
            {"profile": profile_key, "active": release_id, "previous": current, "actor": actor},
        )
    return {"profileKey": profile_key, "activeReleaseId": str(release_id), "previousReleaseId": str(current) if current else None}


def active_release(repository: ControlPlaneRepository, profile_key: str) -> dict[str, Any] | None:
    with repository.engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT release.ontology_release_id, release.release_no,
                       release.status, release.content_hash,
                       release.class_count, release.property_count,
                       release.relationship_count, release.approved_by,
                       release.activated_at
                FROM graphsync.ontology_release_activation active
                JOIN graphsync.ontology_release release
                  ON release.ontology_release_id=active.active_release_id
                WHERE active.profile_key=:profile
                """
            ),
            {"profile": profile_key},
        ).mappings().one_or_none()
    return dict(row) if row else None


def ontology_governance_status(settings: SyncSettings, repository: ControlPlaneRepository, profile_key: str) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        workspaces = [dict(row) for row in connection.execute(
            text("SELECT * FROM graphsync.ontology_workspace WHERE profile_key=:profile ORDER BY updated_at DESC"),
            {"profile": profile_key},
        ).mappings()]
        releases = [dict(row) for row in connection.execute(
            text("SELECT * FROM graphsync.ontology_release WHERE profile_key=:profile ORDER BY release_no DESC"),
            {"profile": profile_key},
        ).mappings()]
    current = workspaces[0] if workspaces else None
    graph = workspace_graph(settings, current["workspace_key"]) if current else {"nodes": [], "edges": [], "properties": []}
    current_active = active_release(repository, profile_key)
    active_graph = (
        release_graph(settings, str(current_active["ontology_release_id"]))
        if current_active else {"classes": [], "relationships": []}
    )
    return {
        "database": "graphsync",
        "sourceDatabase": "graphsync",
        "backend": "postgres",
        "workspaces": workspaces,
        "currentWorkspace": current,
        "graph": graph,
        "releases": releases,
        "activeRelease": current_active,
        "activeReleaseGraph": active_graph,
    }

# Public model operations use the PostgreSQL transactional implementation.
from .publish_ontology_postgres import (
    ensure_publish_database,
    _source_class,
    source_candidates,
    add_class,
    remove_class,
    update_class,
    update_presentation,
    upsert_property,
    add_relationship,
    remove_relationship,
    apply_relationship_suggestions,
    undo_relationship_suggestion_batch,
    workspace_graph,
    create_workspace,
    review_workspace,
    approve_workspace,
    release_graph,
)
