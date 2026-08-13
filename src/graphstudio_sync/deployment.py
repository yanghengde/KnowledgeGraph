"""Environment promotion and blue/green Graph Studio deployment."""

from __future__ import annotations

import json
import struct
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef, XSD
from sqlalchemy import text

from .config import PROJECT_ROOT, SyncSettings
from .materialization import content_hash
from .publish_ontology import active_release as active_ontology_release, release_graph
from .repository import ControlPlaneRepository


DEPLOYMENT_ROOT = PROJECT_ROOT / "outputs" / "graphstudio" / "deployments"
ONT = Namespace("https://opcenter.siemens.com/ontology/camstar/2607/publish#")
GM_SELF = "http://cambridgesemantics.com/ontologies/Graphmarts#Self"


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


def deployment_status(repository: ControlPlaneRepository, profile_key: str) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        environments = [dict(row) for row in connection.execute(
            text(
                """
                SELECT environment_key, title, promotion_order, graphmart_uri,
                       apply_enabled, requires_approval, config, updated_at
                FROM graphsync.deployment_environment
                ORDER BY promotion_order
                """
            )
        ).mappings()]
        deployments = [dict(row) for row in connection.execute(
            text(
                """
                SELECT deployment.deployment_id, deployment.environment_key,
                       deployment.curated_release_id, deployment.status,
                       deployment.ontology_release_id,
                       deployment.slot, deployment.artifact_uri,
                       deployment.artifact_hash, deployment.dataset_uri,
                       deployment.layer_uri, deployment.step_uri,
                       deployment.validation_result, deployment.approved_by,
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
        "environments": environments,
        "deployments": deployments,
        "activeCuratedRelease": dict(active_release) if active_release else None,
        "activeOntologyRelease": active_ontology_release(repository, profile_key),
    }


def build_deployment_plan(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    environment_key: str,
    release_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    status = deployment_status(repository, profile_key)
    environment = next(
        (item for item in status["environments"] if item["environment_key"] == environment_key),
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
    lower = [item for item in status["environments"] if item["promotion_order"] < environment["promotion_order"]]
    previous_deployments = status["deployments"]
    for required in lower:
        promoted = any(
            item["environment_key"] == required["environment_key"]
            and item["status"] == "active"
            and release
            and item["curated_release_id"] == release["release_id"]
            for item in previous_deployments
        )
        if not promoted:
            blockers.append(f"同一制品尚未通过前置环境：{required['title']}")
    active_in_environment = next(
        (item for item in previous_deployments if item["environment_key"] == environment_key and item["status"] == "active"),
        None,
    )
    slot = "green" if active_in_environment and active_in_environment["slot"] == "blue" else "blue"
    return {
        "profileKey": profile_key,
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


def build_curated_rdf(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    release_id: uuid.UUID,
) -> dict[str, Any]:
    ontology_meta = active_ontology_release(repository, profile_key)
    if not ontology_meta:
        raise RuntimeError("No active publish ontology release")
    ontology_release_id = str(ontology_meta["ontology_release_id"])
    model = release_graph(repository.settings, ontology_release_id)
    graph = Graph()
    graph.bind("cam", ONT)
    graph.bind("camdata", Namespace("https://opcenter.siemens.com/data/camstar/2607/ontology/"))
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    ontology_uri = URIRef(str(ONT).rstrip("#"))
    graph.add((ontology_uri, RDF.type, OWL.Ontology))
    graph.add((ontology_uri, RDFS.label, Literal(f"Governed publish ontology release {ontology_meta['release_no']}")))
    datatype_map = {
        "string": XSD.string, "text": XSD.string, "boolean": XSD.boolean,
        "integer": XSD.integer, "int": XSD.integer, "long": XSD.long,
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
        graph.add((class_uri, RDF.type, OWL.Class))
        graph.add((class_uri, RDFS.label, Literal(ontology_class.get("label") or target_name)))
        published_properties = [item for item in entry["properties"] if item.get("published")]
        property_map[ontology_class["uid"]] = published_properties
        for prop in published_properties:
            predicate = ONT[f"{target_name}_{prop['targetName']}"]
            graph.add((predicate, RDF.type, OWL.DatatypeProperty))
            graph.add((predicate, RDFS.domain, class_uri))
            graph.add((predicate, RDFS.range, datatype_map.get(str(prop.get("dataType") or "string").casefold(), XSD.string)))
            graph.add((predicate, RDFS.label, Literal(prop["targetName"])))
    relationship_map: dict[tuple[str, str, str], dict[str, Any]] = {}
    for entry in model["relationships"]:
        relation = entry["relation"]
        if relation.get("usage") != "published_link":
            continue
        source = entry["source"]
        target = entry["target"]
        predicate = ONT[f"REL_{relation['targetName']}"]
        graph.add((predicate, RDF.type, OWL.ObjectProperty))
        graph.add((predicate, RDFS.domain, ONT[source["targetName"]]))
        graph.add((predicate, RDFS.range, ONT[target["targetName"]]))
        graph.add((predicate, RDFS.label, Literal(relation["targetName"])))
        relationship_map[(
            str(relation.get("sourceRelationship") or relation["targetName"]),
            str(source.get("sourceClass") or ""),
            str(target.get("sourceClass") or ""),
        )] = {
            "predicate": predicate, "source": source, "target": target,
        }
    model_triple_count = len(graph)
    with repository.engine.connect() as connection:
        objects = [dict(row) for row in connection.execute(
            text(
                """
                SELECT class_name, object_uri, properties
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
        graph.add((subject, RDF.type, ONT[ontology_class["targetName"]]))
        values = item["properties"] or {}
        for prop in property_map.get(ontology_class["uid"], []):
            source_name = prop.get("sourceName") or prop["targetName"]
            value = values.get(source_name, values.get(prop["targetName"]))
            if value in (None, ""):
                continue
            predicate = ONT[f"{ontology_class['targetName']}_{prop['targetName']}"]
            if isinstance(value, list):
                for member in value:
                    graph.add((subject, predicate, Literal(member)))
            else:
                graph.add((subject, predicate, Literal(value)))
        published_objects += 1
    published_relationships = 0
    for item in relationships:
        mapping = relationship_map.get((item["relationship_name"], item["source_class"], item["target_class"]))
        if not mapping or not item.get("target_object_uri"):
            continue
        graph.add((
            URIRef(item["source_object_uri"]),
            mapping["predicate"],
            URIRef(item["target_object_uri"]),
        ))
        published_relationships += 1
    output_dir = DEPLOYMENT_ROOT / str(release_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    ttl_path = output_dir / "curated_data.ttl"
    zip_path = output_dir / "curated_data.zip"
    graph.serialize(destination=ttl_path, format="turtle")
    parsed = Graph().parse(ttl_path, format="turtle")
    if len(parsed) != len(graph):
        raise RuntimeError("Curated RDF round-trip changed the triple count")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(ttl_path, arcname=f"rdf.ttl/{ttl_path.name}")
    data = bytearray(zip_path.read_bytes())
    cursor = 0
    while True:
        cursor = data.find(b"PK\x01\x02", cursor)
        if cursor < 0:
            break
        struct.pack_into("<I", data, cursor + 38, 0)
        cursor += 46
    zip_path.write_bytes(data)
    return {
        "ttlPath": str(ttl_path),
        "zipPath": str(zip_path),
        "tripleCount": len(graph),
        "modelTripleCount": model_triple_count,
        "objectCount": published_objects,
        "relationshipCount": published_relationships,
        "ontologyReleaseId": ontology_release_id,
        "ontologyReleaseNo": ontology_meta["release_no"],
        "artifactHash": content_hash(zip_path.read_bytes().hex()),
    }


def create_deployment(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    environment_key: str,
    release_id: uuid.UUID | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    plan = build_deployment_plan(
        repository,
        profile_key=profile_key,
        environment_key=environment_key,
        release_id=release_id,
    )
    if not plan["ready"]:
        raise RuntimeError("Deployment is blocked: " + "; ".join(plan["blockers"]))
    selected_id = plan["release"]["release_id"]
    artifact = build_curated_rdf(repository, profile_key=profile_key, release_id=selected_id)
    deployment_id = uuid.uuid4()
    status = "planned" if plan["approvalRequired"] else "approved"
    with repository.engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO graphsync.deployment_release
                    (deployment_id, environment_key, profile_key,
                     curated_release_id, ontology_release_id,
                     status, slot, artifact_uri,
                     artifact_hash, previous_deployment_id, validation_plan,
                     requested_by)
                VALUES (:deployment_id, :environment_key, :profile_key,
                        :release_id, :ontology_release_id,
                        :status, :slot, :artifact_uri,
                        :artifact_hash, :previous_id,
                        CAST(:validation_plan AS jsonb), :actor)
                """
            ),
            {
                "deployment_id": deployment_id,
                "environment_key": environment_key,
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
                    "modelTripleCount": artifact["modelTripleCount"],
                    "ontologyReleaseId": artifact["ontologyReleaseId"],
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
                       environment.apply_enabled, release.source_snapshot
                FROM graphsync.deployment_release deployment
                JOIN graphsync.deployment_environment environment USING (environment_key)
                JOIN graphsync.curated_release release
                  ON release.release_id=deployment.curated_release_id
                WHERE deployment_id=:deployment_id
                """
            ),
            {"deployment_id": deployment_id},
        ).mappings().one_or_none()
    if deployment is None:
        raise KeyError(str(deployment_id))
    if deployment["status"] != "approved":
        raise ValueError("Deployment must be approved before apply")
    if not deployment["apply_enabled"]:
        raise RuntimeError("Graph Studio apply is disabled for this environment")
    zip_path = Path(deployment["artifact_uri"])
    if not zip_path.is_file():
        raise RuntimeError(f"Deployment artifact does not exist: {zip_path}")
    if not settings.shared_file_connection:
        raise RuntimeError("GRAPHSTUDIO_FILE_CONNECTION is not configured")

    session = requests.Session()
    session.auth = (settings.graphstudio_user, settings.graphstudio_password)
    session.headers.update({"Accept": "application/json", "Accept-Encoding": "identity"})
    base = settings.graphstudio_base_url
    graphmart_uri = deployment["graphmart_uri"]
    encoded_graphmart = quote(graphmart_uri, safe="")
    with repository.engine.begin() as connection:
        connection.execute(text("UPDATE graphsync.deployment_release SET status='uploading' WHERE deployment_id=:id"), {"id": deployment_id})
    try:
        multipart: list[tuple[str, tuple[Any, ...]]] = [
            ("title", (None, f"{deployment['profile_key']} {deployment['environment_key']} {deployment['slot']}")),
            ("description", (None, f"Immutable curated release {deployment['curated_release_id']}")),
            ("models", (None, str(ONT).rstrip("#"))),
            ("fileConnection", (None, settings.shared_file_connection)),
            ("filePath", (None, f"{settings.shared_file_path}/{deployment_id}")),
        ]
        with zip_path.open("rb") as handle:
            multipart.append(("rdfZip", (zip_path.name, handle, "application/zip")))
            dataset_result = _require(session.post(f"{base}/api/datasets/from-rdf-zip", files=multipart, timeout=600), "Upload RDF dataset")
        dataset_uri = _find_uri(dataset_result, ("uri", "datasetUri"))
        details = _require(session.get(f"{base}/api/datasets/{quote(dataset_uri or '', safe='')}", params={"expand": "catalogEntry"}, timeout=60), "Read dataset")
        catalog = details.get("catalogEntry") or []
        if isinstance(catalog, list):
            catalog = catalog[0] if catalog else None
        if not dataset_uri or not catalog:
            raise RuntimeError("Graph Studio dataset response has no URI/catalog entry")
        layer = _require(session.post(
            f"{base}/api/graphmarts/{encoded_graphmart}/layers",
            json={"title": f"{deployment['profile_key']} {deployment['slot']} {str(deployment_id)[:8]}", "visible": True, "defaultSelected": True, "autoDeployOntologyChanges": False, "model": [str(ONT).rstrip("#")]},
            timeout=60,
        ), "Create blue/green layer")
        layer_uri = _find_uri(layer, ("uri", "layerUri"))
        step = _require(session.post(
            f"{base}/api/layers/{quote(layer_uri or '', safe='')}/steps",
            json={"title": "Load immutable curated RDF", "type": "LoadDatasetStep", "gmLinkedDataset": catalog, "source": [GM_SELF], "ontology": [str(ONT).rstrip("#")], "ignoreLoadErrors": False},
            timeout=60,
        ), "Create load step")
        step_uri = _find_uri(step, ("uri", "stepUri"))
        with repository.engine.begin() as connection:
            connection.execute(text("UPDATE graphsync.deployment_release SET status='loading', dataset_uri=:dataset, catalog_entry=:catalog, layer_uri=:layer, step_uri=:step WHERE deployment_id=:id"), {"id": deployment_id, "dataset": dataset_uri, "catalog": catalog, "layer": layer_uri, "step": step_uri})
        _require(session.post(f"{base}/api/graphmarts/{encoded_graphmart}/reload", json={"inDesignMode": True, "deployOnActivation": True}, timeout=180), "Reload graphmart")
        deadline = time.monotonic() + 600
        graph_status: dict[str, Any] = {}
        while time.monotonic() < deadline:
            graph_status = _require(session.get(f"{base}/api/graphmarts/{encoded_graphmart}/status", params={"detail": "true"}, timeout=60), "Read graphmart status")
            if graph_status.get("isComplete") and not graph_status.get("dirty"):
                break
            time.sleep(2)
        else:
            raise RuntimeError("Graph Studio reload did not finish within 600 seconds")
        if graph_status.get("failedLayers") or graph_status.get("failedSteps") or graph_status.get("failedDatasets"):
            raise RuntimeError(f"Graph Studio reload contains failed assets: {graph_status}")
        sparql = """
            PREFIX cam: <https://opcenter.siemens.com/ontology/camstar/2607/ProductMfgOrder#>
            SELECT (COUNT(DISTINCT ?product) AS ?products)
                   (COUNT(DISTINCT ?order) AS ?mfgOrders)
                   (COUNT(DISTINCT ?linkedOrder) AS ?linkedOrders)
            WHERE {
              OPTIONAL { ?product a cam:Product . }
              OPTIONAL { ?order a cam:MfgOrder . }
              OPTIONAL { ?linkedOrder cam:REL_ORDERED_PRODUCT ?target . }
            }
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
        actual_objects = counts.get("products", 0) + counts.get("mfgOrders", 0)
        if actual_objects < expected_objects:
            raise RuntimeError(f"SPARQL object count {actual_objects} is below expected {expected_objects}")
        validation = {"reload": graph_status, "sparql": counts, "passed": True}
        with repository.engine.begin() as connection:
            connection.execute(text("UPDATE graphsync.deployment_release SET status='active', validation_result=CAST(:validation AS jsonb), finished_at=now() WHERE deployment_id=:id"), {"id": deployment_id, "validation": json.dumps(validation, default=str)})
            if deployment["previous_deployment_id"]:
                connection.execute(text("UPDATE graphsync.deployment_release SET status='rolled_back' WHERE deployment_id=:previous AND status='active'"), {"previous": deployment["previous_deployment_id"]})
            for class_name, snapshot in (deployment["source_snapshot"] or {}).items():
                if not snapshot.get("runId") or not snapshot.get("upperBound"):
                    continue
                connection.execute(
                    text(
                        """
                        INSERT INTO graphsync.checkpoint
                            (job_name, partition_key, committed_watermark,
                             committed_run_id, committed_at)
                        VALUES ('camstar-full', :partition_key,
                                CAST(:watermark AS jsonb), :run_id, now())
                        ON CONFLICT (job_name, partition_key) DO UPDATE SET
                            committed_watermark=EXCLUDED.committed_watermark,
                            committed_run_id=EXCLUDED.committed_run_id,
                            committed_at=now()
                        """
                    ),
                    {"partition_key": class_name, "watermark": json.dumps(snapshot["upperBound"], default=str), "run_id": uuid.UUID(snapshot["runId"])},
                )
                connection.execute(
                    text("UPDATE graphsync.incremental_window SET status='committed' WHERE window_id=:window_id AND status='verified'"),
                    {"window_id": uuid.UUID(snapshot["windowId"])},
                )
            connection.execute(
                text("INSERT INTO graphsync.runtime_lineage_event (lineage_event_id, profile_key, run_type, run_id, source_asset, target_asset, field_mappings, row_count, content_hash) VALUES (:event, :profile, 'deployment', :run, :source, :target, '{}'::jsonb, 0, :hash)"),
                {"event": uuid.uuid4(), "profile": deployment["profile_key"], "run": deployment_id, "source": f"rdf_artifact:{deployment['artifact_uri']}", "target": f"graphstudio:{graphmart_uri}:{layer_uri}", "hash": deployment["artifact_hash"]},
            )
        return {"deploymentId": str(deployment_id), "status": "active", "datasetUri": dataset_uri, "layerUri": layer_uri, "stepUri": step_uri, "validation": validation}
    except Exception as exc:
        with repository.engine.begin() as connection:
            connection.execute(text("UPDATE graphsync.deployment_release SET status='failed', error=CAST(:error AS jsonb), finished_at=now() WHERE deployment_id=:id"), {"id": deployment_id, "error": json.dumps({"message": str(exc)})})
        raise
