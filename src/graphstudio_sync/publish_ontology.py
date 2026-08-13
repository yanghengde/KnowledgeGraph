"""Governed target ontology stored in an isolated Neo4j database.

The source ``neo4j`` database remains the complete Camstar ontology.  This
module owns a smaller editable Graph Studio model, while PostgreSQL owns its
review, approval, activation and audit metadata.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any

from neo4j import GraphDatabase
from sqlalchemy import text

from .config import SyncSettings
from .repository import ControlPlaneRepository


DATABASE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9.-]{2,62}$")
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


def _driver(settings: SyncSettings, *, publish: bool = False):
    if publish:
        return GraphDatabase.driver(
            settings.publish_neo4j_uri,
            auth=(settings.publish_neo4j_user, settings.publish_neo4j_password),
        )
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


def ensure_publish_database(settings: SyncSettings) -> dict[str, Any]:
    """Create the isolated database and its constraints; never alter source Neo4j."""
    database = settings.publish_neo4j_database
    if not DATABASE_NAME.fullmatch(database):
        raise ValueError("Invalid publish Neo4j database name")
    driver = _driver(settings, publish=True)
    try:
        with driver.session(database="system") as session:
            session.run(f"CREATE DATABASE `{database}` IF NOT EXISTS WAIT 30 SECONDS").consume()
        constraints = [
            "CREATE CONSTRAINT publish_workspace_key IF NOT EXISTS FOR (n:PublishWorkspace) REQUIRE n.workspaceKey IS UNIQUE",
            "CREATE CONSTRAINT publish_class_uid IF NOT EXISTS FOR (n:PublishClass) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT publish_property_uid IF NOT EXISTS FOR (n:PublishProperty) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT ontology_release_id IF NOT EXISTS FOR (n:OntologyRelease) REQUIRE n.releaseId IS UNIQUE",
            "CREATE CONSTRAINT release_class_uid IF NOT EXISTS FOR (n:ReleaseClass) REQUIRE n.uid IS UNIQUE",
            "CREATE CONSTRAINT release_property_uid IF NOT EXISTS FOR (n:ReleaseProperty) REQUIRE n.uid IS UNIQUE",
        ]
        with driver.session(database=database) as session:
            for statement in constraints:
                session.run(statement).consume()
        return {"database": database, "ready": True, "constraints": len(constraints)}
    finally:
        driver.close()


def _source_class(settings: SyncSettings, class_name: str) -> dict[str, Any] | None:
    driver = _driver(settings)
    try:
        with driver.session(database=settings.neo4j_database) as session:
            record = session.run(
                """
                MATCH (c:OntologyClass {name:$name})
                OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p:OntologyProperty)
                RETURN properties(c) AS class,
                       collect(properties(p)) AS properties
                """,
                name=class_name,
            ).single()
        if not record:
            return None
        return {"class": dict(record["class"] or {}), "properties": [dict(item) for item in record["properties"] if item]}
    finally:
        driver.close()


def source_candidates(settings: SyncSettings, query: str = "", limit: int = 100) -> list[dict[str, Any]]:
    driver = _driver(settings)
    try:
        with driver.session(database=settings.neo4j_database) as session:
            rows = session.run(
                """
                MATCH (c:OntologyClass)
                WHERE $search='' OR toLower(c.name) CONTAINS toLower($search)
                   OR toLower(coalesce(c.chineseName,'')) CONTAINS toLower($search)
                OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p:OntologyProperty)
                RETURN c.name AS className, c.chineseName AS chineseName,
                       c.description AS description, c.layer AS layer,
                       count(DISTINCT p) AS propertyCount
                ORDER BY c.name LIMIT $limit
                """,
                search=query.strip(),
                limit=max(1, min(limit, 500)),
            ).data()
        return rows
    finally:
        driver.close()


def _workspace_row(repository: ControlPlaneRepository, workspace_key: str) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        row = connection.execute(
            text("SELECT * FROM graphsync.ontology_workspace WHERE workspace_key=:key"),
            {"key": workspace_key},
        ).mappings().one_or_none()
    if not row:
        raise KeyError(workspace_key)
    return dict(row)


def _touch_workspace(repository: ControlPlaneRepository, workspace_key: str) -> None:
    with repository.engine.begin() as connection:
        updated = connection.execute(
            text(
                """
                UPDATE graphsync.ontology_workspace
                SET status='draft', revision=revision+1,
                    reviewed_by=NULL, reviewed_at=NULL
                WHERE workspace_key=:key AND status <> 'retired'
                RETURNING workspace_id
                """
            ),
            {"key": workspace_key},
        ).one_or_none()
    if not updated:
        raise ValueError("Ontology workspace is retired")


def _publish_session(settings: SyncSettings):
    driver = _driver(settings, publish=True)
    return driver, driver.session(database=settings.publish_neo4j_database)


def add_class(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    workspace_key: str,
    source_class: str | None,
    target_name: str,
    role: str = "context",
    orphan_policy: str = "quarantine",
    label: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    _workspace_row(repository, workspace_key)
    if role not in ALLOWED_ROLES or orphan_policy not in ALLOWED_ORPHANS:
        raise ValueError("Invalid class governance policy")
    target_name = target_name.strip()
    if not target_name:
        raise ValueError("target_name is required")
    source = _source_class(settings, source_class) if source_class else None
    if source_class and not source:
        raise KeyError(source_class)
    source_meta = source["class"] if source else {}
    class_key = source_class or target_name
    uid = f"{workspace_key}::{class_key}"
    driver, session = _publish_session(settings)
    try:
        session.run(
            """
            MATCH (w:PublishWorkspace {workspaceKey:$workspaceKey})
            MERGE (c:PublishClass {uid:$uid})
            SET c.workspaceKey=$workspaceKey, c.sourceClass=$sourceClass,
                c.targetName=$targetName, c.label=$label,
                c.description=$description, c.role=$role,
                c.orphanPolicy=$orphanPolicy, c.origin=$origin,
                c.updatedAt=datetime()
            MERGE (w)-[:OWNS_CLASS]->(c)
            """,
            workspaceKey=workspace_key,
            uid=uid,
            sourceClass=source_class,
            targetName=target_name,
            label=label or source_meta.get("chineseName") or target_name,
            description=description or source_meta.get("description") or "",
            role=role,
            orphanPolicy=orphan_policy,
            origin="source" if source_class else "custom",
        ).consume()
        for prop in (source or {}).get("properties", []):
            name = str(prop.get("name") or "").strip()
            if not name:
                continue
            session.run(
                """
                MATCH (c:PublishClass {uid:$classUid})
                MERGE (p:PublishProperty {uid:$uid})
                SET p.workspaceKey=$workspaceKey, p.classUid=$classUid,
                    p.sourceName=$sourceName, p.targetName=$targetName,
                    p.sourcePath=$sourcePath, p.dataType=$dataType,
                    p.description=$description, p.required=false,
                    p.published=true, p.origin='source', p.updatedAt=datetime()
                MERGE (c)-[:HAS_PROPERTY]->(p)
                """,
                classUid=uid,
                uid=f"{uid}::{name}",
                workspaceKey=workspace_key,
                sourceName=name,
                targetName=name,
                sourcePath=f"{source_class}.{name}",
                dataType=prop.get("dataType") or "String",
                description=prop.get("description") or "",
            ).consume()
    finally:
        session.close()
        driver.close()
    _touch_workspace(repository, workspace_key)
    return {"workspaceKey": workspace_key, "classUid": uid, "targetName": target_name}


def remove_class(settings: SyncSettings, repository: ControlPlaneRepository, workspace_key: str, class_uid: str) -> None:
    _workspace_row(repository, workspace_key)
    driver, session = _publish_session(settings)
    try:
        session.run(
            """
            MATCH (c:PublishClass {uid:$uid, workspaceKey:$workspaceKey})
            OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p:PublishProperty)
            DETACH DELETE p, c
            """,
            uid=class_uid,
            workspaceKey=workspace_key,
        ).consume()
    finally:
        session.close()
        driver.close()
    _touch_workspace(repository, workspace_key)


def update_class(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    workspace_key: str,
    class_uid: str,
    values: dict[str, Any],
) -> None:
    role = values.get("role", "context")
    orphan = values.get("orphanPolicy", "quarantine")
    if role not in ALLOWED_ROLES or orphan not in ALLOWED_ORPHANS:
        raise ValueError("Invalid class governance policy")
    if not str(values.get("targetName") or "").strip():
        raise ValueError("targetName is required")
    driver, session = _publish_session(settings)
    try:
        result = session.run(
            """
            MATCH (c:PublishClass {uid:$uid, workspaceKey:$workspaceKey})
            SET c.targetName=$targetName, c.label=$label,
                c.description=$description, c.role=$role,
                c.orphanPolicy=$orphanPolicy, c.updatedAt=datetime()
            RETURN c.uid AS uid
            """,
            uid=class_uid,
            workspaceKey=workspace_key,
            targetName=str(values["targetName"]).strip(),
            label=str(values.get("label") or values["targetName"]).strip(),
            description=str(values.get("description") or ""),
            role=role,
            orphanPolicy=orphan,
        ).single()
        if not result:
            raise KeyError(class_uid)
    finally:
        session.close()
        driver.close()
    _touch_workspace(repository, workspace_key)


def upsert_property(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    workspace_key: str,
    class_uid: str,
    values: dict[str, Any],
) -> dict[str, Any]:
    target_name = str(values.get("targetName") or "").strip()
    if not target_name:
        raise ValueError("targetName is required")
    property_key = str(values.get("propertyKey") or values.get("sourceName") or target_name).strip()
    uid = str(values.get("uid") or f"{class_uid}::{property_key}")
    driver, session = _publish_session(settings)
    try:
        result = session.run(
            """
            MATCH (c:PublishClass {uid:$classUid, workspaceKey:$workspaceKey})
            MERGE (p:PublishProperty {uid:$uid})
            SET p.workspaceKey=$workspaceKey, p.classUid=$classUid,
                p.sourceName=$sourceName, p.targetName=$targetName,
                p.sourcePath=$sourcePath, p.dataType=$dataType,
                p.description=$description, p.required=$required,
                p.published=$published, p.origin=$origin, p.updatedAt=datetime()
            MERGE (c)-[:HAS_PROPERTY]->(p)
            RETURN p.uid AS uid
            """,
            classUid=class_uid,
            workspaceKey=workspace_key,
            uid=uid,
            sourceName=str(values.get("sourceName") or target_name),
            targetName=target_name,
            sourcePath=str(values.get("sourcePath") or ""),
            dataType=str(values.get("dataType") or "String"),
            description=str(values.get("description") or ""),
            required=bool(values.get("required", False)),
            published=bool(values.get("published", True)),
            origin=str(values.get("origin") or "custom"),
        ).single()
        if not result:
            raise KeyError(class_uid)
    finally:
        session.close()
        driver.close()
    _touch_workspace(repository, workspace_key)
    return {"uid": uid}


def add_relationship(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    workspace_key: str,
    values: dict[str, Any],
) -> dict[str, Any]:
    usage = str(values.get("usage") or "published_link")
    strength = str(values.get("strength") or "context")
    if usage not in ALLOWED_USAGE or strength not in ALLOWED_STRENGTH:
        raise ValueError("Invalid relationship governance policy")
    source_uid = str(values.get("sourceUid") or "")
    target_uid = str(values.get("targetUid") or "")
    target_name = str(values.get("targetName") or values.get("name") or "").strip()
    if not source_uid or not target_uid or not target_name:
        raise ValueError("sourceUid, targetUid and targetName are required")
    relationship_key = str(values.get("relationshipKey") or _hash([source_uid, target_name, target_uid])[:24])
    driver, session = _publish_session(settings)
    try:
        result = session.run(
            """
            MATCH (s:PublishClass {uid:$sourceUid, workspaceKey:$workspaceKey})
            MATCH (t:PublishClass {uid:$targetUid, workspaceKey:$workspaceKey})
            MERGE (s)-[r:PUBLISH_RELATION {relationshipKey:$relationshipKey}]->(t)
            SET r.workspaceKey=$workspaceKey, r.sourceRelationship=$sourceRelationship,
                r.targetName=$targetName, r.usage=$usage,
                r.strength=$strength, r.cardinality=$cardinality,
                r.requiredContext=$requiredContext, r.description=$description,
                r.updatedAt=datetime()
            RETURN r.relationshipKey AS key
            """,
            workspaceKey=workspace_key,
            sourceUid=source_uid,
            targetUid=target_uid,
            relationshipKey=relationship_key,
            sourceRelationship=str(values.get("sourceRelationship") or target_name),
            targetName=target_name,
            usage=usage,
            strength=strength,
            cardinality=str(values.get("cardinality") or "many-to-one"),
            requiredContext=bool(values.get("requiredContext", False)),
            description=str(values.get("description") or ""),
        ).single()
        if not result:
            raise KeyError("Relationship endpoint not found")
    finally:
        session.close()
        driver.close()
    _touch_workspace(repository, workspace_key)
    return {"relationshipKey": relationship_key}


def remove_relationship(settings: SyncSettings, repository: ControlPlaneRepository, workspace_key: str, relationship_key: str) -> None:
    driver, session = _publish_session(settings)
    try:
        session.run(
            "MATCH ()-[r:PUBLISH_RELATION {workspaceKey:$workspaceKey, relationshipKey:$key}]->() DELETE r",
            workspaceKey=workspace_key,
            key=relationship_key,
        ).consume()
    finally:
        session.close()
        driver.close()
    _touch_workspace(repository, workspace_key)


def workspace_graph(settings: SyncSettings, workspace_key: str) -> dict[str, Any]:
    driver, session = _publish_session(settings)
    try:
        classes = session.run(
            """
            MATCH (:PublishWorkspace {workspaceKey:$key})-[:OWNS_CLASS]->(c:PublishClass)
            OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p:PublishProperty)
            RETURN properties(c) AS class, collect(properties(p)) AS properties,
                   c.targetName AS sortName
            ORDER BY sortName
            """,
            key=workspace_key,
        ).data()
        relationships = session.run(
            """
            MATCH (s:PublishClass {workspaceKey:$key})-[r:PUBLISH_RELATION]->(t:PublishClass)
            RETURN s.uid AS source, t.uid AS target, properties(r) AS relation
            ORDER BY r.targetName, s.targetName, t.targetName
            """,
            key=workspace_key,
        ).data()
    finally:
        session.close()
        driver.close()
    nodes = []
    properties = []
    for row in classes:
        data = _json_value(dict(row["class"] or {}))
        nodes.append({"id": data["uid"], "data": data})
        properties.extend(_json_value(dict(item)) for item in row["properties"] if item)
    edges = []
    for row in relationships:
        data = _json_value(dict(row["relation"] or {}))
        edges.append({"id": data["relationshipKey"], "source": row["source"], "target": row["target"], "data": data})
    return {"nodes": nodes, "edges": edges, "properties": properties}


def validate_workspace(settings: SyncSettings, repository: ControlPlaneRepository, workspace_key: str) -> dict[str, Any]:
    workspace = _workspace_row(repository, workspace_key)
    graph = workspace_graph(settings, workspace_key)
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
    for prop in graph["properties"]:
        if not prop.get("published"):
            continue
        class_uid = prop.get("classUid")
        name = str(prop.get("targetName") or "").strip()
        if not name or not prop.get("dataType"):
            errors.append({"code": "property.incomplete", "message": f"属性 {prop.get('uid')} 缺少名称或类型"})
        seen = property_names.setdefault(class_uid, set())
        if name.casefold() in seen:
            errors.append({"code": "property.duplicate_target", "message": f"对象内存在重复属性：{name}"})
        seen.add(name.casefold())
    degree = {item["id"]: 0 for item in nodes}
    for edge in edges:
        if edge["data"].get("usage") == "excluded":
            continue
        degree[edge["source"]] = degree.get(edge["source"], 0) + 1
        degree[edge["target"]] = degree.get(edge["target"], 0) + 1
    if len(nodes) > 1:
        for item in nodes:
            if item["data"].get("role") == "core" and degree.get(item["id"], 0) == 0:
                errors.append({"code": "class.isolated_core", "message": f"核心对象 {item['data'].get('targetName')} 没有上下文关联"})
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


def create_workspace(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    workspace_key: str,
    title: str,
    actor: str,
    seed_profile: bool = True,
) -> dict[str, Any]:
    if not WORKSPACE_KEY.fullmatch(workspace_key):
        raise ValueError("Invalid workspace key")
    ensure_publish_database(settings)
    workspace_id = uuid.uuid4()
    with repository.engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO graphsync.ontology_workspace
                    (workspace_id, workspace_key, profile_key, title,
                     graph_database, created_by, config)
                VALUES (:id, :key, :profile, :title, :database, :actor,
                        CAST(:config AS jsonb))
                """
            ),
            {
                "id": workspace_id,
                "key": workspace_key,
                "profile": profile_key,
                "title": title,
                "database": settings.publish_neo4j_database,
                "actor": actor,
                "config": _canonical({"sourceDatabase": settings.neo4j_database}),
            },
        )
        seed_classes = list(connection.execute(
            text(
                """
                SELECT class_name, role, orphan_policy
                FROM graphsync.profile_class
                WHERE profile_key=:profile AND enabled=true AND role <> 'excluded'
                ORDER BY priority, class_name
                """
            ),
            {"profile": profile_key},
        ).mappings()) if seed_profile else []
        seed_relationships = list(connection.execute(
            text(
                """
                SELECT relationship.relationship_name,
                       source.class_name AS source_class,
                       target.class_name AS target_class,
                       coalesce(profile.strength, 'context') AS strength,
                       relationship.required_context,
                       relationship.semantic_role
                FROM graphsync.relationship_contract relationship
                JOIN graphsync.data_contract source
                  ON source.contract_key=relationship.source_contract_key
                JOIN graphsync.data_contract target
                  ON target.contract_key=relationship.target_contract_key
                LEFT JOIN graphsync.profile_relationship profile
                  ON profile.profile_key=relationship.profile_key
                 AND profile.source_class=source.class_name
                 AND profile.relationship_name=relationship.relationship_name
                 AND profile.target_class=target.class_name
                WHERE relationship.profile_key=:profile
                  AND relationship.status <> 'retired'
                ORDER BY relationship.relationship_name
                """
            ),
            {"profile": profile_key},
        ).mappings()) if seed_profile else []
    driver, session = _publish_session(settings)
    try:
        session.run(
            """
            CREATE (w:PublishWorkspace {
                workspaceKey:$key, profileKey:$profile, title:$title,
                status:'draft', revision:1, createdAt:datetime(), updatedAt:datetime()
            })
            """,
            key=workspace_key,
            profile=profile_key,
            title=title,
        ).consume()
    except Exception:
        with repository.engine.begin() as connection:
            connection.execute(text("DELETE FROM graphsync.ontology_workspace WHERE workspace_id=:id"), {"id": workspace_id})
        raise
    finally:
        session.close()
        driver.close()
    for item in seed_classes:
        add_class(
            settings,
            repository,
            workspace_key=workspace_key,
            source_class=item["class_name"],
            target_name=item["class_name"],
            role=item["role"],
            orphan_policy=item["orphan_policy"],
        )
    for item in seed_relationships:
        source_uid = f"{workspace_key}::{item['source_class']}"
        target_uid = f"{workspace_key}::{item['target_class']}"
        if any(source_uid == f"{workspace_key}::{candidate['class_name']}" for candidate in seed_classes) and any(target_uid == f"{workspace_key}::{candidate['class_name']}" for candidate in seed_classes):
            add_relationship(
                settings,
                repository,
                workspace_key,
                {
                    "sourceUid": source_uid,
                    "targetUid": target_uid,
                    "sourceRelationship": item["relationship_name"],
                    "targetName": item["relationship_name"],
                    "usage": "published_link",
                    "strength": item["strength"],
                    "requiredContext": bool(item["required_context"]),
                    "description": item["semantic_role"] or "",
                },
            )
    return ontology_governance_status(settings, repository, profile_key)


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


def review_workspace(settings: SyncSettings, repository: ControlPlaneRepository, workspace_key: str, actor: str) -> dict[str, Any]:
    validation = validate_workspace(settings, repository, workspace_key)
    if not validation["valid"]:
        raise ValueError("Ontology validation failed: " + "; ".join(item["message"] for item in validation["errors"]))
    with repository.engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE graphsync.ontology_workspace
                SET status='reviewed', reviewed_by=:actor, reviewed_at=now()
                WHERE workspace_key=:key AND status='draft'
                RETURNING workspace_id
                """
            ),
            {"key": workspace_key, "actor": actor},
        ).one_or_none()
    if not row:
        raise ValueError("Only a draft workspace may be reviewed")
    return validation


def _freeze_graph(settings: SyncSettings, workspace_key: str, release_id: str, release_no: int, snapshot: dict[str, Any]) -> None:
    driver, session = _publish_session(settings)
    try:
        session.run(
            """
            CREATE (r:OntologyRelease {
                releaseId:$releaseId, workspaceKey:$workspaceKey,
                releaseNo:$releaseNo, contentHash:$contentHash,
                createdAt:datetime()
            })
            """,
            releaseId=release_id,
            workspaceKey=workspace_key,
            releaseNo=release_no,
            contentHash=snapshot["contentHash"],
        ).consume()
        for node in snapshot["graph"]["nodes"]:
            data = dict(node["data"])
            data["releaseId"] = release_id
            data["sourceUid"] = data.pop("uid")
            data["uid"] = f"{release_id}::{data['sourceUid']}"
            session.run(
                """
                MATCH (r:OntologyRelease {releaseId:$releaseId})
                CREATE (c:ReleaseClass)
                SET c=$data
                CREATE (r)-[:INCLUDES_CLASS]->(c)
                """,
                releaseId=release_id,
                data=data,
            ).consume()
        for prop in snapshot["graph"]["properties"]:
            data = dict(prop)
            source_uid = data["uid"]
            source_class_uid = data["classUid"]
            data["releaseId"] = release_id
            data["sourceUid"] = source_uid
            data["uid"] = f"{release_id}::{source_uid}"
            data["classUid"] = f"{release_id}::{source_class_uid}"
            session.run(
                """
                MATCH (c:ReleaseClass {releaseId:$releaseId, uid:$classUid})
                CREATE (p:ReleaseProperty)
                SET p=$data
                CREATE (c)-[:HAS_PROPERTY]->(p)
                """,
                releaseId=release_id,
                classUid=data["classUid"],
                data=data,
            ).consume()
        for edge in snapshot["graph"]["edges"]:
            data = dict(edge["data"])
            data["releaseId"] = release_id
            session.run(
                """
                MATCH (s:ReleaseClass {releaseId:$releaseId, uid:$sourceUid})
                MATCH (t:ReleaseClass {releaseId:$releaseId, uid:$targetUid})
                CREATE (s)-[rel:RELEASE_RELATION]->(t)
                SET rel=$data
                """,
                releaseId=release_id,
                sourceUid=f"{release_id}::{edge['source']}",
                targetUid=f"{release_id}::{edge['target']}",
                data=data,
            ).consume()
    finally:
        session.close()
        driver.close()


def approve_workspace(settings: SyncSettings, repository: ControlPlaneRepository, workspace_key: str, actor: str) -> dict[str, Any]:
    workspace = _workspace_row(repository, workspace_key)
    if workspace["status"] != "reviewed":
        raise ValueError("Workspace must be reviewed before approval")
    if not workspace.get("reviewed_by") or workspace["reviewed_by"] == actor:
        raise ValueError("Reviewer and approver must be different people")
    validation = validate_workspace(settings, repository, workspace_key)
    if not validation["valid"]:
        raise ValueError("Ontology validation failed")
    graph = workspace_graph(settings, workspace_key)
    snapshot = {**validation, "graph": graph}
    release_id = str(uuid.uuid4())
    with repository.engine.begin() as connection:
        release_no = int(connection.execute(
            text("SELECT coalesce(max(release_no),0)+1 FROM graphsync.ontology_release WHERE profile_key=:profile"),
            {"profile": workspace["profile_key"]},
        ).scalar_one())
        duplicate = connection.execute(
            text("SELECT ontology_release_id, release_no, status FROM graphsync.ontology_release WHERE profile_key=:profile AND content_hash=:hash"),
            {"profile": workspace["profile_key"], "hash": validation["contentHash"]},
        ).mappings().one_or_none()
    if duplicate:
        return {"releaseId": str(duplicate["ontology_release_id"]), "releaseNo": duplicate["release_no"], "status": duplicate["status"], "duplicate": True}
    _freeze_graph(settings, workspace_key, release_id, release_no, snapshot)
    try:
        with repository.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.ontology_release
                        (ontology_release_id, workspace_id, profile_key, release_no,
                         graph_database, content_hash, class_count, property_count,
                         relationship_count, approved_by, config)
                    VALUES (:id, :workspace_id, :profile, :release_no, :database,
                            :hash, :classes, :properties, :relationships, :actor,
                            CAST(:config AS jsonb))
                    """
                ),
                {
                    "id": uuid.UUID(release_id),
                    "workspace_id": workspace["workspace_id"],
                    "profile": workspace["profile_key"],
                    "release_no": release_no,
                    "database": settings.publish_neo4j_database,
                    "hash": validation["contentHash"],
                    "classes": validation["counts"]["classes"],
                    "properties": validation["counts"]["properties"],
                    "relationships": validation["counts"]["relationships"],
                    "actor": actor,
                    "config": _canonical({"workspaceRevision": workspace["revision"]}),
                },
            )
            connection.execute(
                text("UPDATE graphsync.ontology_workspace SET status='frozen' WHERE workspace_key=:key"),
                {"key": workspace_key},
            )
    except Exception:
        driver, session = _publish_session(settings)
        try:
            session.run("MATCH (r:OntologyRelease {releaseId:$id}) DETACH DELETE r", id=release_id).consume()
            session.run("MATCH (n {releaseId:$id}) DETACH DELETE n", id=release_id).consume()
        finally:
            session.close()
            driver.close()
        raise
    return {"releaseId": release_id, "releaseNo": release_no, "status": "approved", "duplicate": False}


def activate_release(repository: ControlPlaneRepository, profile_key: str, release_id: uuid.UUID, actor: str) -> dict[str, Any]:
    with repository.engine.begin() as connection:
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


def release_graph(settings: SyncSettings, release_id: str) -> dict[str, Any]:
    driver, session = _publish_session(settings)
    try:
        classes = session.run(
            """
            MATCH (:OntologyRelease {releaseId:$id})-[:INCLUDES_CLASS]->(c:ReleaseClass)
            OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p:ReleaseProperty)
            RETURN properties(c) AS class, collect(properties(p)) AS properties,
                   c.targetName AS sortName
            ORDER BY sortName
            """,
            id=release_id,
        ).data()
        relations = session.run(
            """
            MATCH (s:ReleaseClass {releaseId:$id})-[r:RELEASE_RELATION]->(t:ReleaseClass)
            RETURN properties(s) AS source, properties(t) AS target, properties(r) AS relation
            ORDER BY r.targetName
            """,
            id=release_id,
        ).data()
    finally:
        session.close()
        driver.close()
    return {
        "classes": [{"class": _json_value(dict(row["class"])), "properties": [_json_value(dict(item)) for item in row["properties"] if item]} for row in classes],
        "relationships": [{"source": _json_value(dict(row["source"])), "target": _json_value(dict(row["target"])), "relation": _json_value(dict(row["relation"]))} for row in relations],
    }


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
    return {
        "database": settings.publish_neo4j_database,
        "sourceDatabase": settings.neo4j_database,
        "workspaces": workspaces,
        "currentWorkspace": current,
        "graph": graph,
        "releases": releases,
        "activeRelease": active_release(repository, profile_key),
    }
