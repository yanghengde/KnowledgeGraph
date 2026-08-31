"""Environment promotion and blue/green Graph Studio deployment."""

from __future__ import annotations

import json
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

import requests
from rdflib import Dataset, Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef, XSD
from sqlalchemy import text

from .config import PROJECT_ROOT, SyncSettings
from .entity_labels import resolve_entity_label
from .graphstudio_api import require_graphstudio_2026_1_ready
from .materialization import content_hash
from .publish_ontology import active_release as active_ontology_release, release_graph
from .repository import ControlPlaneRepository


DEPLOYMENT_ROOT = PROJECT_ROOT / "outputs" / "graphstudio" / "deployments"
ONT = Namespace("https://opcenter.siemens.com/ontology/camstar/2607/publish#")
GM_SELF = "http://cambridgesemantics.com/ontologies/Graphmarts#Self"


def release_model_uri(ontology_release_id: str | uuid.UUID) -> str:
    """Return an immutable Graph Studio model URI for one ontology release."""
    return f"{str(ONT).rstrip('#')}/releases/{ontology_release_id}"


def _write_graphstudio_rdf_zip(zip_path: Path, ttl_path: Path) -> None:
    """Create the RDF ZIP layout declared by the Graph Studio 6.3 API."""
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(ttl_path, arcname=f"rdf.ttl/{ttl_path.name}")


def _is_graphstudio_rdf_zip(zip_path: Path) -> bool:
    """Return whether an artifact has one FLDS top-level directory."""
    if not zip_path.is_file():
        return False
    try:
        with zipfile.ZipFile(zip_path) as archive:
            if archive.testzip() is not None:
                return False
            members = archive.infolist()
    except (OSError, zipfile.BadZipFile):
        return False
    if not members:
        return False
    data_files = [
        item for item in members
        if not item.is_dir() and item.filename.startswith("rdf.ttl/")
    ]
    return (
        bool(data_files)
        and all(item.filename.casefold().endswith(".ttl") for item in data_files)
        and all(not item.is_dir() for item in members)
        and len(data_files) == len(members)
    )


def _json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text.strip()


def _require(response: requests.Response, action: str) -> Any:
    if not response.ok:
        raise RuntimeError(f"{action} failed: HTTP {response.status_code}: {response.text[:2000]}")
    return _json(response)


def _find_uri(value: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return value
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
                return candidate
        for candidate in value.values():
            found = _find_uri(candidate, keys)
            if found:
                return found
    if isinstance(value, list):
        for candidate in value:
            found = _find_uri(candidate, keys)
            if found:
                return found
    return None


def _deployment_graphmart_uri(deployment: dict[str, Any] | None) -> str | None:
    """Read the immutable target snapshot, with support for legacy records."""
    if not deployment:
        return None
    plan = deployment.get("validation_plan") or {}
    if isinstance(plan, dict) and plan.get("graphmartUri"):
        return str(plan["graphmartUri"])
    result = deployment.get("validation_result") or {}
    reload_status = result.get("reload") if isinstance(result, dict) else None
    if isinstance(reload_status, dict):
        value = reload_status.get("graphmartUri") or reload_status.get("uri")
        if value:
            return str(value)
    return None


def _same_graphmart(left: str | None, right: str | None) -> bool:
    return bool(left and right and left.rstrip("/") == right.rstrip("/"))


def _resolve_previous_layer(
    deployment: dict[str, Any], graphmart_uri: str,
) -> tuple[str | None, str | None, bool]:
    """Keep a previous Layer only when it belongs to the current Graphmart.

    Returns ``(previous_layer_uri, skipped_layer_uri, target_mismatch)``.  A
    legacy deployment without a target snapshot is retained and is verified
    against Graph Studio later, where older servers can report that the Layer
    is absent without blocking a fresh blue/green lineage.
    """
    previous_layer_uri = deployment.get("previous_layer_uri")
    previous_target = _deployment_graphmart_uri({
        "validation_plan": deployment.get("previous_validation_plan"),
        "validation_result": deployment.get("previous_validation_result"),
    })
    target_mismatch = bool(
        previous_layer_uri
        and previous_target
        and not _same_graphmart(previous_target, graphmart_uri)
    )
    if target_mismatch:
        return None, previous_layer_uri, True
    return previous_layer_uri, None, False


def deployment_status(repository: ControlPlaneRepository, profile_key: str) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        targets = [dict(row) for row in connection.execute(
            text(
                """
                SELECT target.target_key, target.title, target.connection_key,
                       target.graphmart_uri, target.description, target.enabled,
                       target.config, target.updated_at
                FROM graphsync.graphstudio_target target
                ORDER BY target.title, target.target_key
                """
            )
        ).mappings()]
        routes = [dict(row) for row in connection.execute(
            text(
                """
                SELECT route.route_key, route.profile_key, route.environment_key,
                       route.target_key, route.title, route.promotion_order,
                       route.apply_enabled, route.requires_approval, route.enabled,
                       route.config, route.updated_at,
                       target.title AS target_title,
                       target.graphmart_uri, target.connection_key
                FROM graphsync.publication_route route
                JOIN graphsync.graphstudio_target target USING (target_key)
                WHERE route.profile_key=:profile_key AND route.enabled AND target.enabled
                ORDER BY route.promotion_order, route.route_key
                """
            ),
            {"profile_key": profile_key},
        ).mappings()]
        deployments = [dict(row) for row in connection.execute(
            text(
                """
                SELECT deployment.deployment_id, deployment.environment_key,
                       deployment.route_key,
                       deployment.curated_release_id, deployment.status,
                       deployment.ontology_release_id,
                       deployment.slot, deployment.artifact_uri,
                       deployment.artifact_hash, deployment.dataset_uri,
                       deployment.layer_uri, deployment.step_uri,
                       deployment.validation_plan, deployment.validation_result,
                       deployment.approved_by,
                       deployment.started_at, deployment.finished_at,
                       deployment.error
                FROM graphsync.deployment_release deployment
                WHERE deployment.profile_key=:profile_key
                ORDER BY deployment.started_at DESC LIMIT 30
                """
            ),
            {"profile_key": profile_key},
        ).mappings()]
        active_release = connection.execute(
            text(
                """
                SELECT release.release_id, release.release_no, release.status,
                       release.content_hash, release.object_count,
                       release.relationship_count
                FROM graphsync.curated_release_activation active
                JOIN graphsync.curated_release release
                  ON release.release_id=active.active_release_id
                WHERE active.profile_key=:profile_key
                """
            ),
            {"profile_key": profile_key},
        ).mappings().one_or_none()
    return {
        # `environments` is retained as a response alias for older clients.
        "environments": routes,
        "routes": routes,
        "targets": targets,
        "deployments": deployments,
        "activeCuratedRelease": dict(active_release) if active_release else None,
        "activeOntologyRelease": active_ontology_release(repository, profile_key),
    }


def update_deployment_environment(
    repository: ControlPlaneRepository,
    *,
    environment_key: str,
    apply_enabled: bool,
) -> dict[str, Any]:
    """Enable or lock Graph Studio writes for one promotion environment.

    This only changes the safety switch. It never prepares or applies a
    deployment, so enabling an environment remains separate from publishing.
    """
    with repository.engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE graphsync.deployment_environment
                SET apply_enabled=:apply_enabled, updated_at=now()
                WHERE environment_key=:environment_key
                RETURNING environment_key, title, promotion_order,
                          graphmart_uri, apply_enabled, requires_approval,
                          config, updated_at
                """
            ),
            {
                "environment_key": environment_key,
                "apply_enabled": apply_enabled,
            },
        ).mappings().one_or_none()
    if row is None:
        raise KeyError(environment_key)
    return dict(row)


def upsert_graphstudio_target(
    repository: ControlPlaneRepository,
    *,
    target_key: str,
    title: str,
    graphmart_uri: str,
    connection_key: str = "graph-studio",
    description: str | None = None,
    enabled: bool = True,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO graphsync.graphstudio_target
                    (target_key, title, connection_key, graphmart_uri,
                     description, enabled, config)
                VALUES (:target_key, :title, :connection_key, :graphmart_uri,
                        :description, :enabled, CAST(:config AS jsonb))
                ON CONFLICT (target_key) DO UPDATE SET
                    title=EXCLUDED.title,
                    connection_key=EXCLUDED.connection_key,
                    graphmart_uri=EXCLUDED.graphmart_uri,
                    description=EXCLUDED.description,
                    enabled=EXCLUDED.enabled,
                    config=EXCLUDED.config,
                    updated_at=now()
                RETURNING target_key, title, connection_key, graphmart_uri,
                          description, enabled, config, updated_at
                """
            ),
            {
                "target_key": target_key,
                "title": title,
                "connection_key": connection_key,
                "graphmart_uri": graphmart_uri,
                "description": description,
                "enabled": enabled,
                "config": json.dumps(config or {}),
            },
        ).mappings().one()
    return dict(row)


def upsert_publication_route(
    repository: ControlPlaneRepository,
    *,
    route_key: str,
    profile_key: str,
    environment_key: str,
    target_key: str,
    title: str,
    promotion_order: int,
    apply_enabled: bool = False,
    requires_approval: bool = True,
    enabled: bool = True,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO graphsync.publication_route
                    (route_key, profile_key, environment_key, target_key, title,
                     promotion_order, apply_enabled, requires_approval, enabled, config)
                VALUES (:route_key, :profile_key, :environment_key, :target_key,
                        :title, :promotion_order, :apply_enabled,
                        :requires_approval, :enabled, CAST(:config AS jsonb))
                ON CONFLICT (route_key) DO UPDATE SET
                    profile_key=EXCLUDED.profile_key,
                    environment_key=EXCLUDED.environment_key,
                    target_key=EXCLUDED.target_key,
                    title=EXCLUDED.title,
                    promotion_order=EXCLUDED.promotion_order,
                    apply_enabled=EXCLUDED.apply_enabled,
                    requires_approval=EXCLUDED.requires_approval,
                    enabled=EXCLUDED.enabled,
                    config=EXCLUDED.config,
                    updated_at=now()
                RETURNING route_key, profile_key, environment_key, target_key,
                          title, promotion_order, apply_enabled,
                          requires_approval, enabled, config, updated_at
                """
            ),
            {
                "route_key": route_key,
                "profile_key": profile_key,
                "environment_key": environment_key,
                "target_key": target_key,
                "title": title,
                "promotion_order": promotion_order,
                "apply_enabled": apply_enabled,
                "requires_approval": requires_approval,
                "enabled": enabled,
                "config": json.dumps(config or {}),
            },
        ).mappings().one()
    return dict(row)


def update_publication_route(
    repository: ControlPlaneRepository,
    *,
    route_key: str,
    apply_enabled: bool,
) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE graphsync.publication_route
                SET apply_enabled=:apply_enabled, updated_at=now()
                WHERE route_key=:route_key
                RETURNING route_key, profile_key, environment_key, target_key,
                          title, promotion_order, apply_enabled,
                          requires_approval, enabled, config, updated_at
                """
            ),
            {"route_key": route_key, "apply_enabled": apply_enabled},
        ).mappings().one_or_none()
    if row is None:
        raise KeyError(route_key)
    return dict(row)


def build_deployment_plan(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    environment_key: str,
    route_key: str | None = None,
    release_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    status = deployment_status(repository, profile_key)
    environment = next(
        (item for item in status["routes"]
         if (route_key and item["route_key"] == route_key)
         or (not route_key and item["environment_key"] == environment_key)),
        None,
    )
    if environment is None:
        raise KeyError(environment_key)
    release = status["activeCuratedRelease"]
    blockers: list[str] = []
    if release_id:
        with repository.engine.connect() as connection:
            selected = connection.execute(
                text(
                    """
                    SELECT release_id, release_no, status, content_hash,
                           object_count, relationship_count
                    FROM graphsync.curated_release
                    WHERE release_id=:release_id AND profile_key=:profile_key
                    """
                ),
                {"release_id": release_id, "profile_key": profile_key},
            ).mappings().one_or_none()
        release = dict(selected) if selected else None
    if not release:
        blockers.append("没有可发布的治理快照")
    elif release["status"] not in {"ready", "active", "superseded"}:
        blockers.append("治理快照尚未通过验证")
    ontology_release = status.get("activeOntologyRelease")
    if not ontology_release:
        blockers.append("没有已激活的发布本体版本")
    promotion_lane = (environment.get("config") or {}).get("promotionLane", "default")
    lower = [
        item for item in status["routes"]
        if item["promotion_order"] < environment["promotion_order"]
        and (item.get("config") or {}).get("promotionLane", "default") == promotion_lane
    ]
    previous_deployments = status["deployments"]
    for required in lower:
        promoted = any(
            item.get("route_key") == required["route_key"]
            and item["status"] == "active"
            and release
            and item["curated_release_id"] == release["release_id"]
            and ontology_release
            and item.get("ontology_release_id") == ontology_release["ontology_release_id"]
            for item in previous_deployments
        )
        if not promoted:
            blockers.append(f"同一制品尚未通过前置环境：{required['title']}")
    target_graphmart_uri = environment.get("graphmart_uri")
    active_in_environment = next((
        item for item in previous_deployments
        if item.get("route_key") == environment["route_key"]
        and item["status"] == "active"
        and (
            not target_graphmart_uri
            or not _deployment_graphmart_uri(item)
            or _same_graphmart(_deployment_graphmart_uri(item), target_graphmart_uri)
        )
    ), None)
    slot = "green" if active_in_environment and active_in_environment["slot"] == "blue" else "blue"
    return {
        "profileKey": profile_key,
        "routeKey": environment["route_key"],
        "targetKey": environment["target_key"],
        "environment": environment,
        "release": release,
        "ontologyRelease": ontology_release,
        "slot": slot,
        "ready": not blockers,
        "blockers": blockers,
        "applyEnabled": bool(environment["apply_enabled"]),
        "approvalRequired": bool(environment["requires_approval"]),
        "previousDeploymentId": str(active_in_environment["deployment_id"]) if active_in_environment else None,
        "strategy": "immutable_artifact_blue_green_layer",
    }


def _ontology_release_metadata(
    repository: ControlPlaneRepository,
    profile_key: str,
    ontology_release_id: str | uuid.UUID | None = None,
) -> dict[str, Any] | None:
    """Resolve either the active ontology or one immutable pinned release."""
    if ontology_release_id is None:
        return active_ontology_release(repository, profile_key)
    with repository.engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT ontology_release_id, release_no, status, content_hash,
                       class_count, property_count, relationship_count,
                       approved_by, activated_at
                FROM graphsync.ontology_release
                WHERE ontology_release_id=:release_id AND profile_key=:profile_key
                """
            ),
            {
                "release_id": uuid.UUID(str(ontology_release_id)),
                "profile_key": profile_key,
            },
        ).mappings().one_or_none()
    return dict(row) if row else None


def build_curated_rdf(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    release_id: uuid.UUID,
    ontology_release_id: str | uuid.UUID | None = None,
) -> dict[str, Any]:
    ontology_meta = _ontology_release_metadata(
        repository, profile_key, ontology_release_id,
    )
    if not ontology_meta:
        raise RuntimeError("Pinned publish ontology release does not exist")
    ontology_release_id = str(ontology_meta["ontology_release_id"])
    model = release_graph(repository.settings, ontology_release_id)
    model_graph = Graph()
    data_graph = Graph()
    for graph in (model_graph, data_graph):
        graph.bind("cam", ONT)
        graph.bind("camdata", Namespace("https://opcenter.siemens.com/data/camstar/2607/ontology/"))
        graph.bind("owl", OWL)
        graph.bind("rdfs", RDFS)
    model_uri = release_model_uri(ontology_release_id)
    ontology_uri = URIRef(model_uri)
    model_graph.add((ontology_uri, RDF.type, OWL.Ontology))
    model_graph.add((ontology_uri, RDFS.label, Literal(f"Governed publish ontology release {ontology_meta['release_no']}")))
    model_graph.add((ONT.previewProperty, RDF.type, OWL.AnnotationProperty))
    model_graph.add((ONT.searchProperty, RDF.type, OWL.AnnotationProperty))
    datatype_map = {
        "string": XSD.string, "text": XSD.string, "boolean": XSD.boolean,
        "integer": XSD.int, "int": XSD.int, "long": XSD.long,
        "decimal": XSD.decimal, "double": XSD.double, "float": XSD.float,
        "date": XSD.date, "datetime": XSD.dateTime, "timestamp": XSD.dateTime,
    }
    class_map: dict[str, dict[str, Any]] = {}
    class_by_uid: dict[str, dict[str, Any]] = {}
    property_map: dict[str, list[dict[str, Any]]] = {}
    for entry in model["classes"]:
        ontology_class = entry["class"]
        target_name = ontology_class["targetName"]
        class_by_uid[ontology_class["uid"]] = ontology_class
        if ontology_class.get("sourceClass"):
            class_map[ontology_class["sourceClass"]] = ontology_class
        class_uri = ONT[target_name]
        model_graph.add((class_uri, RDF.type, OWL.Class))
        model_graph.add((class_uri, RDFS.label, Literal(ontology_class.get("label") or target_name)))
        published_properties = [item for item in entry["properties"] if item.get("published")]
        property_map[ontology_class["uid"]] = published_properties
        for prop in published_properties:
            predicate = ONT[f"{target_name}_{prop['targetName']}"]
            model_graph.add((predicate, RDF.type, OWL.DatatypeProperty))
            model_graph.add((predicate, RDFS.domain, class_uri))
            model_graph.add((predicate, RDFS.range, datatype_map.get(str(prop.get("dataType") or "string").casefold(), XSD.string)))
            model_graph.add((predicate, RDFS.label, Literal(prop["targetName"])))
        display_predicate = ONT[f"{target_name}_displayLabel"]
        model_graph.add((display_predicate, RDF.type, OWL.DatatypeProperty))
        model_graph.add((display_predicate, RDFS.domain, class_uri))
        model_graph.add((display_predicate, RDFS.range, XSD.string))
        model_graph.add((display_predicate, RDFS.label, Literal("显示名称", lang="zh")))
        model_graph.add((class_uri, ONT.previewProperty, display_predicate))
        properties_by_name = {
            str(prop.get("targetName") or "").casefold(): prop
            for prop in published_properties
        }
        for search_name in ontology_class.get("searchFields") or []:
            search_property = properties_by_name.get(str(search_name).casefold())
            if search_property:
                model_graph.add((
                    class_uri,
                    ONT.searchProperty,
                    ONT[f"{target_name}_{search_property['targetName']}"],
                ))
    relationship_map: dict[tuple[str, str, str], dict[str, Any]] = {}
    for entry in model["relationships"]:
        relation = entry["relation"]
        if relation.get("usage") != "published_link":
            continue
        source = entry["source"]
        target = entry["target"]
        predicate = ONT[f"REL_{relation['targetName']}"]
        model_graph.add((predicate, RDF.type, OWL.ObjectProperty))
        model_graph.add((predicate, RDFS.domain, ONT[source["targetName"]]))
        model_graph.add((predicate, RDFS.range, ONT[target["targetName"]]))
        model_graph.add((predicate, RDFS.label, Literal(relation["targetName"])))
        relationship_map[(
            str(relation.get("sourceRelationship") or relation["targetName"]),
            str(source.get("sourceClass") or ""),
            str(target.get("sourceClass") or ""),
        )] = {
            "predicate": predicate, "source": source, "target": target,
        }
    model_triple_count = len(model_graph)
    with repository.engine.connect() as connection:
        objects = [dict(row) for row in connection.execute(
            text(
                """
                SELECT class_name, object_uri, source_primary_key,
                       business_key, properties
                FROM graphsync.object_version
                WHERE release_id=:release_id AND profile_key=:profile_key
                  AND record_status='active'
                ORDER BY class_name, object_uri
                """
            ),
            {"release_id": release_id, "profile_key": profile_key},
        ).mappings()]
        relationships = [dict(row) for row in connection.execute(
            text(
                """
                SELECT relationship.relationship_name,
                       relationship.source_object_uri,
                       relationship.target_object_uri,
                       source.class_name AS source_class,
                       target.class_name AS target_class
                FROM graphsync.relationship_version relationship
                JOIN graphsync.data_contract source
                  ON source.contract_key=relationship.source_contract_key
                JOIN graphsync.data_contract target
                  ON target.contract_key=relationship.target_contract_key
                WHERE relationship.release_id=:release_id
                  AND relationship.resolution_status='resolved'
                ORDER BY relationship.relationship_name, relationship.source_object_uri
                """
            ),
            {"release_id": release_id},
        ).mappings()]
    published_objects = 0
    for item in objects:
        ontology_class = class_map.get(item["class_name"])
        if not ontology_class:
            continue
        subject = URIRef(item["object_uri"])
        data_graph.add((subject, RDF.type, ONT[ontology_class["targetName"]]))
        values = item["properties"] or {}
        label = resolve_entity_label(
            ontology_class,
            property_map.get(ontology_class["uid"], []),
            values,
            business_key=item.get("business_key") or {},
            primary_key=item.get("source_primary_key") or {},
        )
        data_graph.add((
            subject,
            ONT[f"{ontology_class['targetName']}_displayLabel"],
            Literal(label),
        ))
        if ontology_class.get("emitRdfsLabel", True):
            data_graph.add((subject, RDFS.label, Literal(label)))
        for prop in property_map.get(ontology_class["uid"], []):
            source_name = prop.get("sourceName") or prop["targetName"]
            value = values.get(source_name, values.get(prop["targetName"]))
            if value in (None, ""):
                continue
            predicate = ONT[f"{ontology_class['targetName']}_{prop['targetName']}"]
            if isinstance(value, list):
                for member in value:
                    data_graph.add((subject, predicate, Literal(member)))
            else:
                data_graph.add((subject, predicate, Literal(value)))
        published_objects += 1
    published_relationships = 0
    for item in relationships:
        mapping = relationship_map.get((item["relationship_name"], item["source_class"], item["target_class"]))
        if not mapping or not item.get("target_object_uri"):
            continue
        data_graph.add((
            URIRef(item["source_object_uri"]),
            mapping["predicate"],
            URIRef(item["target_object_uri"]),
        ))
        published_relationships += 1
    # One curated data snapshot can be deployed repeatedly with different
    # immutable ontology contracts. Keep their artifacts separate so a model
    # activation never overwrites an earlier deployment or rollback asset.
    output_dir = DEPLOYMENT_ROOT / f"{release_id}--{ontology_release_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "curated_model.trig"
    ttl_path = output_dir / "curated_data.ttl"
    zip_path = output_dir / "curated_data.zip"
    model_dataset = Dataset()
    for prefix, namespace in model_graph.namespaces():
        model_dataset.bind(prefix, namespace)
    model_context = model_dataset.graph(ontology_uri)
    for triple in model_graph:
        model_context.add(triple)
    model_dataset.serialize(destination=model_path, format="trig")
    data_graph.serialize(destination=ttl_path, format="turtle")
    parsed_model = Dataset()
    parsed_model.parse(model_path, format="trig")
    parsed_data = Graph().parse(ttl_path, format="turtle")
    if len(parsed_model) != len(model_graph) or len(parsed_data) != len(data_graph):
        raise RuntimeError("Curated RDF round-trip changed the triple count")
    _write_graphstudio_rdf_zip(zip_path, ttl_path)
    artifact_hash = content_hash(model_path.read_bytes().hex() + zip_path.read_bytes().hex())
    return {
        "modelUri": model_uri,
        "modelPath": str(model_path),
        "ttlPath": str(ttl_path),
        "zipPath": str(zip_path),
        "tripleCount": len(model_graph) + len(data_graph),
        "dataTripleCount": len(data_graph),
        "modelTripleCount": model_triple_count,
        "objectCount": published_objects,
        "relationshipCount": published_relationships,
        "publishedClassUris": sorted({
            str(ONT[item["targetName"]]) for item in class_map.values()
        }),
        "publishedRelationshipUris": sorted({
            str(item["predicate"]) for item in relationship_map.values()
        }),
        "ontologyReleaseId": ontology_release_id,
        "ontologyReleaseNo": ontology_meta["release_no"],
        "artifactHash": artifact_hash,
    }


def create_deployment(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    environment_key: str,
    route_key: str | None = None,
    release_id: uuid.UUID | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    plan = build_deployment_plan(
        repository,
        profile_key=profile_key,
        environment_key=environment_key,
        route_key=route_key,
        release_id=release_id,
    )
    if not plan["ready"]:
        raise RuntimeError("Deployment is blocked: " + "; ".join(plan["blockers"]))
    selected_id = plan["release"]["release_id"]
    artifact = build_curated_rdf(
        repository,
        profile_key=profile_key,
        release_id=selected_id,
        ontology_release_id=plan["ontologyRelease"]["ontology_release_id"],
    )
    deployment_id = uuid.uuid4()
    status = "planned" if plan["approvalRequired"] else "approved"
    with repository.engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO graphsync.deployment_release
                    (deployment_id, environment_key, route_key, profile_key,
                     curated_release_id, ontology_release_id,
                     status, slot, artifact_uri,
                     artifact_hash, previous_deployment_id, validation_plan,
                     requested_by)
                VALUES (:deployment_id, :environment_key, :route_key, :profile_key,
                        :release_id, :ontology_release_id,
                        :status, :slot, :artifact_uri,
                        :artifact_hash, :previous_id,
                        CAST(:validation_plan AS jsonb), :actor)
                """
            ),
            {
                "deployment_id": deployment_id,
                "environment_key": environment_key,
                "route_key": plan["routeKey"],
                "profile_key": profile_key,
                "release_id": selected_id,
                "ontology_release_id": uuid.UUID(artifact["ontologyReleaseId"]),
                "status": status,
                "slot": plan["slot"],
                "artifact_uri": artifact["zipPath"],
                "artifact_hash": artifact["artifactHash"],
                "previous_id": plan["previousDeploymentId"],
                "validation_plan": json.dumps({
                    "expectedObjects": artifact["objectCount"],
                    "expectedRelationships": artifact["relationshipCount"],
                    "tripleCount": artifact["tripleCount"],
                    "dataTripleCount": artifact["dataTripleCount"],
                    "modelTripleCount": artifact["modelTripleCount"],
                    "modelUri": artifact["modelUri"],
                    "modelPath": artifact["modelPath"],
                    "ontologyReleaseId": artifact["ontologyReleaseId"],
                    "targetKey": plan["targetKey"],
                    "graphmartUri": plan["environment"].get("graphmart_uri"),
                    "publishedClassUris": artifact["publishedClassUris"],
                    "publishedRelationshipUris": artifact["publishedRelationshipUris"],
                    "checks": ["reload_complete", "no_failed_assets", "sparql_counts"],
                }),
                "actor": actor,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO graphsync.runtime_lineage_event
                    (lineage_event_id, profile_key, run_type, run_id,
                     source_asset, target_asset, field_mappings,
                     row_count, content_hash)
                VALUES (:event_id, :profile_key, 'deployment', :run_id,
                        :source, :target, '{}'::jsonb, :rows, :hash)
                """
            ),
            {
                "event_id": uuid.uuid4(), "profile_key": profile_key,
                "run_id": deployment_id,
                "source": f"graphsync.release:{selected_id}+ontology:{artifact['ontologyReleaseId']}",
                "target": f"rdf_artifact:{artifact['zipPath']}",
                "rows": artifact["objectCount"], "hash": artifact["artifactHash"],
            },
        )
    return {"deploymentId": str(deployment_id), "status": status, "plan": plan, "artifact": artifact}


def approve_deployment(repository: ControlPlaneRepository, deployment_id: uuid.UUID, actor: str | None) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE graphsync.deployment_release
                SET status='approved', approved_by=:actor
                WHERE deployment_id=:deployment_id AND status='planned'
                RETURNING deployment_id, environment_key, status, approved_by
                """
            ),
            {"deployment_id": deployment_id, "actor": actor},
        ).mappings().one_or_none()
    if row is None:
        raise ValueError("Only a planned deployment can be approved")
    return dict(row)


def _catalog_entry(details: dict[str, Any]) -> str | None:
    catalog = details.get("catalogEntry") or []
    if isinstance(catalog, list):
        catalog = catalog[0] if catalog else None
    if isinstance(catalog, dict):
        return _find_uri(catalog, ("uri", "catalogEntry"))
    return catalog if isinstance(catalog, str) else None


def _deployment_dataset(
    session: requests.Session,
    base: str,
    deployment_id: uuid.UUID,
) -> dict[str, Any] | None:
    datasets = _require(session.get(f"{base}/api/datasets", timeout=60), "List datasets")
    if not isinstance(datasets, list):
        return None
    marker = str(deployment_id)
    return next(
        (
            item for item in datasets
            if marker in str(((item.get("dataLocation") or {}).get("filePath") or ""))
        ),
        None,
    )


def _ensure_model(
    session: requests.Session,
    base: str,
    *,
    model_uri: str,
    model_path: Path,
) -> None:
    models = _require(session.get(f"{base}/api/models", timeout=60), "List models")
    if isinstance(models, list) and model_uri in models:
        return
    try:
        with model_path.open("rb") as handle:
            _require(
                session.post(
                    f"{base}/api/models",
                    files={"modelData": (model_path.name, handle, "application/trig")},
                    timeout=180,
                ),
                "Register ontology model",
            )
    except Exception as exc:
        raise RuntimeError(
            "Graph Studio 本体注册失败；请确认 API 账号拥有 Manage Models 权限。"
            f" 原始错误：{exc}"
        ) from exc
    models = _require(session.get(f"{base}/api/models", timeout=60), "Verify model registration")
    if not isinstance(models, list) or model_uri not in models:
        raise RuntimeError(f"Graph Studio 本体注册后不可见：{model_uri}")


def _ensure_dataset(
    session: requests.Session,
    base: str,
    *,
    deployment_id: uuid.UUID,
    deployment: dict[str, Any],
    zip_path: Path,
    model_uri: str,
    settings: SyncSettings,
    reuse_existing: bool,
) -> tuple[str, str]:
    existing = _deployment_dataset(session, base, deployment_id)
    if existing and not reuse_existing:
        existing_uri = _find_uri(existing, ("uri", "datasetUri"))
        if existing_uri:
            _require(
                session.delete(
                    f"{base}/api/datasets/{quote(existing_uri, safe='')}",
                    params={"force": "true"},
                    timeout=60,
                ),
                "Remove obsolete deployment dataset",
            )
        existing = None
    dataset_uri = _find_uri(existing, ("uri", "datasetUri")) if existing else None
    if not dataset_uri:
        multipart: list[tuple[str, tuple[Any, ...]]] = [
            ("title", (None, f"{deployment['profile_key']} {deployment['environment_key']} {deployment['slot']}")),
            ("description", (None, f"Immutable curated release {deployment['curated_release_id']}")),
            ("models", (None, model_uri)),
            ("fileConnection", (None, settings.shared_file_connection)),
            ("filePath", (None, f"{settings.shared_file_path}/{deployment_id}")),
        ]
        with zip_path.open("rb") as handle:
            multipart.append(("rdfZip", (zip_path.name, handle, "application/zip")))
            result = _require(
                session.post(f"{base}/api/datasets/from-rdf-zip", files=multipart, timeout=600),
                "Upload RDF dataset",
            )
        dataset_uri = _find_uri(result, ("uri", "datasetUri"))
    if not dataset_uri:
        raise RuntimeError("Graph Studio dataset response has no URI")
    details = _require(
        session.get(
            f"{base}/api/datasets/{quote(dataset_uri, safe='')}",
            params={"expand": "catalogEntry"}, timeout=60,
        ),
        "Read dataset",
    )
    catalog = _catalog_entry(details) if isinstance(details, dict) else None
    if not catalog:
        raise RuntimeError("Graph Studio dataset response has no catalog entry")
    return dataset_uri, catalog


def _requires_dataset_replacement(
    validation_plan: dict[str, Any], previous_error: Any,
) -> bool:
    if not validation_plan.get("modelUri") or validation_plan.get("replaceExistingDataset"):
        return True
    previous_error_message = (
        str(previous_error.get("message") or "")
        if isinstance(previous_error, dict)
        else str(previous_error or "")
    )
    return "Remove obsolete deployment dataset failed" in previous_error_message


def _ensure_layer(
    session: requests.Session,
    base: str,
    *,
    encoded_graphmart: str,
    title: str,
    model_uri: str,
) -> str:
    layers = _require(
        session.get(f"{base}/api/graphmarts/{encoded_graphmart}/layers", timeout=60),
        "List graphmart layers",
    )
    existing = next((item for item in layers if item.get("title") == title), None) if isinstance(layers, list) else None
    if existing:
        layer_uri = _find_uri(existing, ("uri", "layerUri"))
    else:
        result = _require(
            session.post(
                f"{base}/api/graphmarts/{encoded_graphmart}/layers",
                json={
                    "title": title,
                    "visible": True,
                    "defaultSelected": True,
                    "autoDeployOntologyChanges": False,
                    "model": [model_uri],
                },
                timeout=60,
            ),
            "Create blue/green layer",
        )
        layer_uri = _find_uri(result, ("uri", "layerUri"))
    if not layer_uri:
        raise RuntimeError("Graph Studio layer response has no URI")
    return layer_uri


def _ensure_load_step(
    session: requests.Session,
    base: str,
    *,
    layer_uri: str,
    catalog: str,
    model_uri: str,
) -> str:
    encoded_layer = quote(layer_uri, safe="")
    steps = _require(session.get(f"{base}/api/layers/{encoded_layer}/steps", timeout=60), "List layer steps")
    title = "Load immutable curated RDF"
    existing = next((item for item in steps if item.get("title") == title), None) if isinstance(steps, list) else None
    if existing:
        step_uri = _find_uri(existing, ("uri", "stepUri"))
    else:
        result = _require(
            session.post(
                f"{base}/api/layers/{encoded_layer}/steps",
                json={
                    "title": title,
                    "type": "LoadDatasetStep",
                    "gmLinkedDataset": catalog,
                    "source": [GM_SELF],
                    "ontology": [model_uri],
                    "ignoreLoadErrors": False,
                },
                timeout=60,
            ),
            "Create load step",
        )
        step_uri = _find_uri(result, ("uri", "stepUri"))
    if not step_uri:
        raise RuntimeError("Graph Studio load step response has no URI")
    return step_uri


def _set_layer_enabled(
    session: requests.Session,
    base: str,
    *,
    encoded_graphmart: str,
    layer_uri: str,
    enabled: bool,
) -> str:
    """Select one layer through the Graph Studio 6.3 Run Configuration API."""
    graphmart_uri = unquote(encoded_graphmart)
    configured_layers = _require(
        session.get(f"{base}/api/graphmarts/{encoded_graphmart}/layers", timeout=60),
        "List Graphmart layers",
    )
    configured = any(
        isinstance(item, dict)
        and (item.get("uri") or item.get("layerUri")) == layer_uri
        for item in (configured_layers or [])
    )
    if not configured and not enabled:
        return "layer_not_in_target"
    if not configured:
        raise RuntimeError(f"Layer {layer_uri} 不属于当前目标 Graphmart，无法启用。")

    run_configuration = f"{graphmart_uri}_RunConfiguration-Design"
    run_config_url = f"{base}/api/runconfigs/{quote(run_configuration, safe='')}"
    current = _require(
        session.get(run_config_url, timeout=60),
        "Read Design Run Configuration",
    )
    if not isinstance(current, dict):
        raise RuntimeError("Graph Studio 6.3 Design Run Configuration 返回格式不正确")
    assume_disabled = bool(current.get("runConfigurationAssumeDisabled", False))
    toggled = set(current.get("toggledLayer") or [])
    should_toggle = enabled if assume_disabled else not enabled
    if should_toggle:
        toggled.add(layer_uri)
    else:
        toggled.discard(layer_uri)
    updated = _require(
        session.patch(
            run_config_url,
            json={"toggledLayer": sorted(toggled)},
            timeout=60,
        ),
        "Update Design Run Configuration",
    )
    if not isinstance(updated, dict):
        updated = _require(
            session.get(run_config_url, timeout=60),
            "Verify Design Run Configuration",
        )
    actual_toggled = set((updated or {}).get("toggledLayer") or [])
    actual = layer_uri in actual_toggled if assume_disabled else layer_uri not in actual_toggled
    if actual is not enabled:
        raise RuntimeError("Graph Studio 6.3 Run Configuration 更新后状态未生效")
    return "run_configuration_rest"


def _require_enabled_layer(graph_status: dict[str, Any], layer_uri: str) -> dict[str, Any]:
    """Verify that the deployment Layer is online after Graphmart reload."""
    layers = graph_status.get("childLayer") if isinstance(graph_status, dict) else None
    layer_status = next(
        (
            item for item in (layers or [])
            if isinstance(item, dict)
            and (item.get("uri") or item.get("layerUri")) == layer_uri
        ),
        None,
    )
    if layer_status is None:
        raise RuntimeError(f"Graph Studio Reload 后未返回发布 Layer 状态：{layer_uri}")
    if layer_status.get("enabled") is not True:
        raise RuntimeError(f"Graph Studio Reload 后发布 Layer 仍未启用：{layer_uri}")
    if layer_status.get("childFailed") is True:
        raise RuntimeError(f"Graph Studio Reload 后发布 Layer 加载失败：{layer_uri}")
    return layer_status


def _require_disabled_layer(graph_status: dict[str, Any], layer_uri: str) -> dict[str, Any] | None:
    """Verify that the predecessor Layer is no longer active after reload."""
    layers = graph_status.get("childLayer") if isinstance(graph_status, dict) else None
    layer_status = next(
        (
            item for item in (layers or [])
            if isinstance(item, dict)
            and (item.get("uri") or item.get("layerUri")) == layer_uri
        ),
        None,
    )
    # Legacy status responses may omit disabled layers entirely.
    if layer_status is None:
        return None
    if layer_status.get("enabled") is not False:
        raise RuntimeError(f"Graph Studio Reload 后上一 Layer 仍处于启用状态：{layer_uri}")
    return layer_status


def _reload_graphmart(
    session: requests.Session,
    base: str,
    *,
    encoded_graphmart: str,
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    graphmart_uri = unquote(encoded_graphmart)
    _require(
        session.post(
            f"{base}/api/graphmarts/{encoded_graphmart}/reload",
            json={
                "inDesignMode": True,
                "deployOnActivation": True,
                "runConfiguration": f"{graphmart_uri}_RunConfiguration-Design",
            },
            timeout=180,
        ),
        "Reload graphmart",
    )
    deadline = time.monotonic() + timeout_seconds
    graph_status: dict[str, Any] = {}
    while time.monotonic() < deadline:
        graph_status = _require(
            session.get(
                f"{base}/api/graphmarts/{encoded_graphmart}/status",
                params={"detail": "true"},
                timeout=60,
            ),
            "Read graphmart status",
        )
        if graph_status.get("isComplete") and not graph_status.get("dirty"):
            break
        time.sleep(2)
    else:
        raise RuntimeError(f"Graph Studio reload did not finish within {timeout_seconds} seconds")
    if (
        graph_status.get("failedLayers")
        or graph_status.get("failedSteps")
        or graph_status.get("failedDatasets")
    ):
        raise RuntimeError(f"Graph Studio reload contains failed assets: {graph_status}")
    return graph_status


def apply_deployment(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    deployment_id: uuid.UUID,
) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        deployment = connection.execute(
            text(
                """
                SELECT deployment.*, environment.graphmart_uri,
                       route.apply_enabled, release.source_snapshot,
                       previous.layer_uri AS previous_layer_uri,
                       previous.validation_plan AS previous_validation_plan,
                       previous.validation_result AS previous_validation_result
                FROM graphsync.deployment_release deployment
                JOIN graphsync.publication_route route
                  ON route.route_key=deployment.route_key
                JOIN graphsync.graphstudio_target environment
                  ON environment.target_key=route.target_key
                JOIN graphsync.curated_release release
                  ON release.release_id=deployment.curated_release_id
                LEFT JOIN graphsync.deployment_release previous
                  ON previous.deployment_id=deployment.previous_deployment_id
                WHERE deployment.deployment_id=:deployment_id
                """
            ),
            {"deployment_id": deployment_id},
        ).mappings().one_or_none()
    if deployment is None:
        raise KeyError(str(deployment_id))
    deployment = dict(deployment)
    if deployment["status"] not in {"approved", "failed"}:
        raise ValueError("Deployment must be approved or failed before apply/retry")
    if not deployment["apply_enabled"]:
        raise RuntimeError("Graph Studio apply is disabled for this environment")
    validation_plan = dict(deployment.get("validation_plan") or {})
    legacy_artifact = not validation_plan.get("modelUri")
    replace_existing_dataset = _requires_dataset_replacement(
        validation_plan, deployment.get("error"),
    )
    if replace_existing_dataset:
        # Keep this marker until the replacement upload succeeds.  Without it, a
        # failed cleanup followed by another retry could reuse the legacy ZIP
        # dataset, which still contains the ontology triples we now register as
        # an immutable Graph Studio model.
        validation_plan["replaceExistingDataset"] = True
    model_path_value = validation_plan.get("modelPath")
    artifact_path_value = deployment.get("artifact_uri")
    if (
        legacy_artifact
        or not validation_plan.get("publishedClassUris")
        or not model_path_value
        or not Path(model_path_value).is_file()
        or not artifact_path_value
        or not _is_graphstudio_rdf_zip(Path(artifact_path_value))
    ):
        artifact = build_curated_rdf(
            repository,
            profile_key=deployment["profile_key"],
            release_id=deployment["curated_release_id"],
            ontology_release_id=deployment["ontology_release_id"],
        )
        validation_plan.update({
            "expectedObjects": artifact["objectCount"],
            "expectedRelationships": artifact["relationshipCount"],
            "tripleCount": artifact["tripleCount"],
            "dataTripleCount": artifact["dataTripleCount"],
            "modelTripleCount": artifact["modelTripleCount"],
            "modelUri": artifact["modelUri"],
            "modelPath": artifact["modelPath"],
            "ontologyReleaseId": artifact["ontologyReleaseId"],
            "publishedClassUris": artifact["publishedClassUris"],
            "publishedRelationshipUris": artifact["publishedRelationshipUris"],
            "checks": ["model_registered", "reload_complete", "no_failed_assets", "sparql_counts"],
        })
        deployment["artifact_uri"] = artifact["zipPath"]
        deployment["artifact_hash"] = artifact["artifactHash"]
        deployment["ontology_release_id"] = uuid.UUID(artifact["ontologyReleaseId"])
        deployment["validation_plan"] = validation_plan
        with repository.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE graphsync.deployment_release
                    SET artifact_uri=:artifact_uri,
                        artifact_hash=:artifact_hash,
                        ontology_release_id=:ontology_release_id,
                        validation_plan=CAST(:validation_plan AS jsonb)
                    WHERE deployment_id=:deployment_id
                    """
                ),
                {
                    "deployment_id": deployment_id,
                    "artifact_uri": deployment["artifact_uri"],
                    "artifact_hash": deployment["artifact_hash"],
                    "ontology_release_id": deployment["ontology_release_id"],
                    "validation_plan": json.dumps(validation_plan),
                },
            )
    zip_path = Path(deployment["artifact_uri"])
    if not zip_path.is_file():
        raise RuntimeError(f"Deployment artifact does not exist: {zip_path}")
    model_path = Path(validation_plan["modelPath"])
    if not model_path.is_file():
        raise RuntimeError(f"Deployment model artifact does not exist: {model_path}")
    if not settings.shared_file_connection:
        raise RuntimeError("GRAPHSTUDIO_FILE_CONNECTION is not configured")

    session = requests.Session()
    session.auth = (settings.graphstudio_user, settings.graphstudio_password)
    session.headers.update({"Accept": "application/json", "Accept-Encoding": "identity"})
    base = settings.graphstudio_base_url
    require_graphstudio_2026_1_ready(session, base)
    graphmart_uri = deployment["graphmart_uri"]
    encoded_graphmart = quote(graphmart_uri, safe="")
    previous_layer_uri, skipped_previous_layer_uri, previous_target_mismatch = (
        _resolve_previous_layer(deployment, graphmart_uri)
    )
    with repository.engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE graphsync.deployment_release
                SET status='uploading', error='{}'::jsonb, finished_at=NULL,
                    validation_plan=CAST(:validation_plan AS jsonb)
                WHERE deployment_id=:id
                """
            ),
            {"id": deployment_id, "validation_plan": json.dumps(validation_plan)},
        )
    dataset_uri = deployment.get("dataset_uri")
    layer_uri = deployment.get("layer_uri")
    step_uri = deployment.get("step_uri")
    layer_switched = False
    try:
        model_uri = validation_plan["modelUri"]
        _ensure_model(session, base, model_uri=model_uri, model_path=model_path)
        dataset_uri, catalog = _ensure_dataset(
            session, base,
            deployment_id=deployment_id,
            deployment=deployment,
            zip_path=zip_path,
            model_uri=model_uri,
            settings=settings,
            reuse_existing=not replace_existing_dataset,
        )
        validation_plan["replaceExistingDataset"] = False
        deployment["validation_plan"] = validation_plan
        with repository.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE graphsync.deployment_release
                    SET dataset_uri=:dataset, catalog_entry=:catalog,
                        validation_plan=CAST(:validation_plan AS jsonb)
                    WHERE deployment_id=:id
                    """
                ),
                {
                    "id": deployment_id,
                    "dataset": dataset_uri,
                    "catalog": catalog,
                    "validation_plan": json.dumps(validation_plan),
                },
            )
        layer_title = f"{deployment['profile_key']} {deployment['slot']} {str(deployment_id)[:8]}"
        layer_uri = _ensure_layer(
            session, base,
            encoded_graphmart=encoded_graphmart,
            title=layer_title,
            model_uri=model_uri,
        )
        with repository.engine.begin() as connection:
            connection.execute(
                text("UPDATE graphsync.deployment_release SET layer_uri=:layer WHERE deployment_id=:id"),
                {"id": deployment_id, "layer": layer_uri},
            )
        step_uri = _ensure_load_step(
            session, base,
            layer_uri=layer_uri,
            catalog=catalog,
            model_uri=model_uri,
        )
        with repository.engine.begin() as connection:
            connection.execute(
                text("UPDATE graphsync.deployment_release SET status='loading', step_uri=:step WHERE deployment_id=:id"),
                {"id": deployment_id, "step": step_uri},
            )
        _set_layer_enabled(
            session, base, encoded_graphmart=encoded_graphmart,
            layer_uri=layer_uri, enabled=True,
        )
        previous_layer_in_target = not previous_target_mismatch
        if previous_layer_uri and previous_layer_uri != layer_uri:
            disabled_switch_mode = _set_layer_enabled(
                session, base, encoded_graphmart=encoded_graphmart,
                layer_uri=previous_layer_uri, enabled=False,
            )
            previous_layer_in_target = disabled_switch_mode != "layer_not_in_target"
            layer_switched = previous_layer_in_target
            if not previous_layer_in_target:
                skipped_previous_layer_uri = previous_layer_uri
        graph_status = _reload_graphmart(
            session, base, encoded_graphmart=encoded_graphmart,
        )
        _require_enabled_layer(graph_status, layer_uri)
        if previous_layer_uri and previous_layer_in_target:
            _require_disabled_layer(graph_status, previous_layer_uri)
        class_uris = list(validation_plan.get("publishedClassUris") or [])
        relationship_uris = list(validation_plan.get("publishedRelationshipUris") or [])
        if not class_uris:
            raise RuntimeError("Deployment validation plan has no published class URIs")
        class_values = " ".join(f"<{value}>" for value in class_uris)
        relationship_select = (
            "{ SELECT (COUNT(*) AS ?relationships) WHERE { "
            f"VALUES ?predicate {{ {' '.join(f'<{value}>' for value in relationship_uris)} }} "
            "?source ?predicate ?target . } }"
            if relationship_uris else "BIND(0 AS ?relationships)"
        )
        sparql = f"""
            SELECT ?objects ?relationships WHERE {{
              {{ SELECT (COUNT(DISTINCT ?subject) AS ?objects) WHERE {{
                  VALUES ?type {{ {class_values} }}
                  ?subject a ?type .
              }} }}
              {relationship_select}
            }}
        """
        query_response = session.post(
            f"{base}/sparql/graphmart/{encoded_graphmart}",
            data={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
            timeout=120,
        )
        sparql_result = _require(query_response, "Run SPARQL acceptance")
        bindings = ((sparql_result.get("results") or {}).get("bindings") or []) if isinstance(sparql_result, dict) else []
        if not bindings:
            raise RuntimeError("SPARQL acceptance returned no aggregate row")
        counts = {key: int(value.get("value", 0)) for key, value in bindings[0].items()}
        expected_objects = int((deployment["validation_plan"] or {}).get("expectedObjects", 0))
        actual_objects = counts.get("objects", 0)
        expected_relationships = int((deployment["validation_plan"] or {}).get("expectedRelationships", 0))
        actual_relationships = counts.get("relationships", 0)
        if actual_objects < expected_objects:
            raise RuntimeError(f"SPARQL object count {actual_objects} is below expected {expected_objects}")
        if actual_relationships < expected_relationships:
            raise RuntimeError(
                f"SPARQL relationship count {actual_relationships} is below expected {expected_relationships}"
            )
        validation = {
            "reload": graph_status,
            "sparql": counts,
            "layerSwitch": {
                "enabled": layer_uri,
                "disabled": previous_layer_uri if layer_switched else None,
                "mode": (
                    "target_reset"
                    if skipped_previous_layer_uri
                    else "run_configuration_rest"
                ),
                "skippedPreviousLayer": skipped_previous_layer_uri,
            },
            "passed": True,
        }
        with repository.engine.begin() as connection:
            connection.execute(text("UPDATE graphsync.deployment_release SET status='active', validation_result=CAST(:validation AS jsonb), finished_at=now() WHERE deployment_id=:id"), {"id": deployment_id, "validation": json.dumps(validation, default=str)})
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.target_release_activation
                        (route_key, ontology_release_id, curated_release_id,
                         deployment_id, activated_at, activated_by)
                    VALUES (:route_key, :ontology_release_id, :curated_release_id,
                            :deployment_id, now(), :actor)
                    ON CONFLICT (route_key) DO UPDATE SET
                        ontology_release_id=EXCLUDED.ontology_release_id,
                        curated_release_id=EXCLUDED.curated_release_id,
                        deployment_id=EXCLUDED.deployment_id,
                        activated_at=EXCLUDED.activated_at,
                        activated_by=EXCLUDED.activated_by
                    """
                ),
                {
                    "route_key": deployment["route_key"],
                    "ontology_release_id": deployment["ontology_release_id"],
                    "curated_release_id": deployment["curated_release_id"],
                    "deployment_id": deployment_id,
                    "actor": deployment.get("approved_by") or deployment.get("requested_by"),
                },
            )
            if deployment["previous_deployment_id"] and previous_layer_in_target:
                connection.execute(text("UPDATE graphsync.deployment_release SET status='rolled_back' WHERE deployment_id=:previous AND status='active'"), {"previous": deployment["previous_deployment_id"]})
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.publication_checkpoint
                        (route_key, deployment_id, ontology_release_id,
                         curated_release_id, artifact_hash, validation,
                         committed_at)
                    VALUES (:route_key, :deployment_id, :ontology_release_id,
                            :curated_release_id, :artifact_hash,
                            CAST(:validation AS jsonb), now())
                    ON CONFLICT (route_key) DO UPDATE SET
                        deployment_id=EXCLUDED.deployment_id,
                        ontology_release_id=EXCLUDED.ontology_release_id,
                        curated_release_id=EXCLUDED.curated_release_id,
                        artifact_hash=EXCLUDED.artifact_hash,
                        validation=EXCLUDED.validation,
                        committed_at=EXCLUDED.committed_at
                    """
                ),
                {
                    "route_key": deployment["route_key"],
                    "deployment_id": deployment_id,
                    "ontology_release_id": deployment["ontology_release_id"],
                    "curated_release_id": deployment["curated_release_id"],
                    "artifact_hash": deployment["artifact_hash"],
                    "validation": json.dumps(validation, default=str),
                },
            )
            connection.execute(
                text("INSERT INTO graphsync.runtime_lineage_event (lineage_event_id, profile_key, run_type, run_id, source_asset, target_asset, field_mappings, row_count, content_hash) VALUES (:event, :profile, 'deployment', :run, :source, :target, '{}'::jsonb, 0, :hash)"),
                {"event": uuid.uuid4(), "profile": deployment["profile_key"], "run": deployment_id, "source": f"rdf_artifact:{deployment['artifact_uri']}", "target": f"graphstudio:{graphmart_uri}:{layer_uri}", "hash": deployment["artifact_hash"]},
            )
        return {"deploymentId": str(deployment_id), "status": "active", "datasetUri": dataset_uri, "layerUri": layer_uri, "stepUri": step_uri, "validation": validation}
    except Exception as exc:
        message = str(exc)
        compensation: dict[str, Any] = {"attempted": False}
        if layer_switched and previous_layer_uri and layer_uri:
            compensation["attempted"] = True
            try:
                _set_layer_enabled(
                    session, base, encoded_graphmart=encoded_graphmart,
                    layer_uri=previous_layer_uri, enabled=True,
                )
                _set_layer_enabled(
                    session, base, encoded_graphmart=encoded_graphmart,
                    layer_uri=layer_uri, enabled=False,
                )
                compensation["reload"] = _reload_graphmart(
                    session, base, encoded_graphmart=encoded_graphmart,
                )
                compensation["restored"] = True
            except Exception as compensation_exc:  # pragma: no cover - external recovery path
                compensation.update({"restored": False, "error": str(compensation_exc)})
        if "acl limited predicate" in message and "Graphmarts#model" in message:
            message = (
                "Graph Studio 拒绝关联本体模型：API 账号缺少目标 Graphmart 的 Modify（Add/Edit）权限，"
                "或缺少 Manage Models 权限。请在 Opcenter2607 → Sharing → Configuration 为该账号授予 Modify。"
                f" 原始错误：{message}"
            )
        with repository.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE graphsync.deployment_release
                    SET status='failed',
                        dataset_uri=COALESCE(:dataset, dataset_uri),
                        layer_uri=COALESCE(:layer, layer_uri),
                        step_uri=COALESCE(:step, step_uri),
                        error=CAST(:error AS jsonb), finished_at=now()
                    WHERE deployment_id=:id
                    """
                ),
                {
                    "id": deployment_id,
                    "dataset": dataset_uri,
                    "layer": layer_uri,
                    "step": step_uri,
                    "error": json.dumps({
                        "message": message,
                        "retryable": True,
                        "stage": "graphstudio_apply",
                        "compensation": compensation,
                        "resources": {
                            "datasetUri": dataset_uri,
                            "layerUri": layer_uri,
                            "stepUri": step_uri,
                            "modelUri": validation_plan.get("modelUri"),
                        },
                    }),
                },
            )
        raise RuntimeError(message) from exc
