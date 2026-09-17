"""Management API for the Camstar to Graph Studio synchronization center."""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from web.schemas.sync import (
    ConnectionUpdate,
    NavigationUpdate,
    JobUpdate,
    TablePolicyUpdate,
    SettingUpdate,
    PropertyOverrideUpdate,
    RelationshipOverrideUpdate,
    OntologyActorRequest,
    OntologyDiscoveryPlanRequest,
    PublishClassCreate,
    PublishClassUpdate,
    PublishPresentationUpdate,
    PublishPropertyUpdate,
    PublishRelationshipUpdate,
    RelationshipSuggestionApply,
    GraphProfileUpdate,
    ProfileClassUpdate,
    ProfileRelationshipUpdate,
    DataContractUpdate,
    DataContractCreate,
    RelationshipContractUpdate,
    RelationshipContractCreate,
    SchemaChangeOperation,
    SchemaChangeCreate,
    SchemaChangeReview,
    AttributeProjectionFieldInput,
    AttributeProjectionUpdate,
    AttributeProjectionReview,
    MaterializationRequest,
    ContinuousSyncRequest,
    DataSyncRequest,
    DataSyncScheduleRequest,
    ReleaseActivation,
    DeploymentCreate,
    DeploymentEnvironmentUpdate,
    GraphStudioTargetUpdate,
    PublicationRouteUpdate,
    ActorRequest,
    ActionPlanRequest,
    ActionDefinitionUpdate,
    ActionDefinitionReview,
    OpenApiActionImport,
    ActionCompensationRequest,
    SyncClassConfiguration,
)

from src.graphstudio_sync.config import SyncSettings
from src.graphstudio_sync.sync_configuration import configuration_preview, save_configuration
from src.graphstudio_sync.continuous_sync import (
    continuous_sync_status,
    execute_continuous_sync,
)
from src.graphstudio_sync.catalog import compile_catalog
from src.graphstudio_sync.connections import test_all_connections, test_connection
from src.graphstudio_sync.curation import build_curation_preview
from src.graphstudio_sync.data_sync import (
    data_sync_status,
    execute_audited_data_sync,
    update_data_sync_schedule,
)
from src.graphstudio_sync.actions import (
    approve_action,
    execute_action,
    import_openapi_action,
    list_actions,
    openapi_action_candidates,
    openapi_action_sources,
    plan_action,
    plan_compensation,
    review_action_definition,
    upsert_action_definition,
)
from src.graphstudio_sync.action_identity import action_principal, require_action_principal
from src.graphstudio_sync.publishing.deployment import apply_deployment
from src.graphstudio_sync.publishing.deployment import approve_deployment
from src.graphstudio_sync.publishing.deployment import build_deployment_plan
from src.graphstudio_sync.publishing.deployment import create_deployment
from src.graphstudio_sync.publishing.deployment import deployment_status
from src.graphstudio_sync.publishing.deployment import update_publication_route
from src.graphstudio_sync.publishing.deployment import upsert_graphstudio_target
from src.graphstudio_sync.publishing.deployment import upsert_publication_route
from src.graphstudio_sync.publishing.deployment import update_deployment_environment
from src.graphstudio_sync.incremental import execute_incremental_plan, execute_incremental_probe
from src.graphstudio_sync.incremental_preview import build_incremental_preview
from src.graphstudio_sync.graph_profile import plan_context_closure, validate_graph_profile
from src.graphstudio_sync.publishing.materialization import activate_release
from src.graphstudio_sync.publishing.materialization import execute_materialization
from src.graphstudio_sync.publishing.materialization import materialization_status
from src.graphstudio_sync.publishing.materialization import rollback_release
from src.graphstudio_sync.observability import acknowledge_alert, observability_status, run_health_check
from src.graphstudio_sync.storage.repository import ControlPlaneRepository
from src.graphstudio_sync.preview import build_full_preview
from src.graphstudio_sync.publishing.publish_ontology import activate_release as activate_ontology_release
from src.graphstudio_sync.publishing.publish_ontology import add_class as add_publish_class
from src.graphstudio_sync.publishing.publish_ontology import add_relationship as add_publish_relationship
from src.graphstudio_sync.publishing.publish_ontology import apply_relationship_suggestions as apply_publish_relationship_suggestions
from src.graphstudio_sync.publishing.publish_ontology import approve_workspace as approve_ontology_workspace
from src.graphstudio_sync.publishing.publish_ontology import build_discovery_plan as build_ontology_discovery_plan
from src.graphstudio_sync.publishing.publish_ontology import initialize_governance
from src.graphstudio_sync.publishing.publish_ontology import ontology_governance_status
from src.graphstudio_sync.publishing.publish_ontology import remove_class as remove_publish_class
from src.graphstudio_sync.publishing.publish_ontology import remove_relationship as remove_publish_relationship
from src.graphstudio_sync.publishing.publish_ontology import relationship_suggestions as publish_relationship_suggestions
from src.graphstudio_sync.publishing.publish_ontology import review_workspace as review_ontology_workspace
from src.graphstudio_sync.publishing.publish_ontology import source_candidates as ontology_source_candidates
from src.graphstudio_sync.publishing.publish_ontology import update_class as update_publish_class
from src.graphstudio_sync.publishing.publish_ontology import update_presentation as update_publish_presentation
from src.graphstudio_sync.publishing.publish_ontology import undo_relationship_suggestion_batch as undo_publish_relationship_suggestion_batch
from src.graphstudio_sync.publishing.publish_ontology import upsert_property as upsert_publish_property
from src.graphstudio_sync.publishing.publish_ontology import validate_workspace as validate_ontology_workspace
from src.graphstudio_sync.run_manager import execute_dry_run
from src.graphstudio_sync.schema_evolution import (
    analyze_schema_change,
    apply_schema_change,
    rollback_schema_change,
)
from src.graphstudio_sync.schema_drift import latest_schema_drift, scan_schema_drift
from src.graphstudio_sync.attribute_projection import (
    preview_attribute_projection,
    validate_projection_definition,
)


router = APIRouter(prefix="/api/sync", tags=["Graph Studio Sync"])


@lru_cache(maxsize=1)
def _settings() -> SyncSettings:
    return SyncSettings.from_env()


@lru_cache(maxsize=1)
def _repository() -> ControlPlaneRepository:
    return ControlPlaneRepository(_settings())


def _repo() -> ControlPlaneRepository:
    try:
        repository = _repository()
        with repository.engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return repository
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"PostgreSQL control plane unavailable: {exc}") from exc


@router.get("/overview")
def overview():
    return _repo().overview()


@router.get("/navigation")
def navigation(include_disabled: bool = Query(default=False)):
    return {"items": _repo().list_navigation(include_disabled=include_disabled)}


@router.put("/navigation/{menu_key}")
def update_navigation(menu_key: str, request: NavigationUpdate):
    try:
        return _repo().update_navigation(menu_key, **request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Menu item not found") from exc


@router.get("/connections")
def connections():
    items = _repo().list_connections()
    items = [item for item in items if item["connection_key"] in {"camstar-source", "graph-studio", "control-postgresql"}]
    for item in items:
        item["editable"] = item["connection_key"] != "control-postgresql"
        item["secret_configured"] = bool(item.get("secret_ref"))
    return {"items": items}


@router.put("/connections/{connection_key}")
def update_connection(connection_key: str, request: ConnectionUpdate):
    if connection_key == "control-postgresql":
        raise HTTPException(
            status_code=409,
            detail="The control PostgreSQL connection is environment-managed to prevent self-disconnection",
        )
    from src.graphstudio_sync.config import connection_endpoints

    endpoint = connection_endpoints(_settings()).get(connection_key)
    if endpoint is not None and request.endpoint != endpoint:
        raise HTTPException(status_code=409, detail="服务地址由运行环境配置，请修改 .env 并重启服务")
    allowed_kinds = {
        "camstar-source": {"camstar_sqlserver", "camstar_oracle"},
        "graph-studio": {"graph_studio"},
    }
    if request.kind not in allowed_kinds.get(connection_key, set()):
        raise HTTPException(status_code=422, detail="Connection type is not valid for this profile")
    try:
        return _repo().update_connection(connection_key, **request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Connection not found") from exc


@router.post("/connections/test-all")
def test_connections():
    results = test_all_connections(_settings(), _repo())
    return {"ok": all(item["ok"] for item in results), "items": results}


@router.post("/connections/{connection_key}/test")
def test_one_connection(connection_key: str):
    try:
        return test_connection(_settings(), _repo(), connection_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Connection not found") from exc


@router.get("/jobs")
def jobs():
    return {"items": _repo().list_jobs()}


@router.put("/jobs/{job_name}")
def update_job(job_name: str, request: JobUpdate):
    try:
        return _repo().update_job(job_name, **request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job not found") from exc


@router.get("/jobs/{job_name}/table-policies")
def table_policies(job_name: str):
    try:
        return {"items": _repo().list_table_policies(job_name)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job not found") from exc


@router.put("/jobs/{job_name}/table-policies/{class_name}")
def update_table_policy(job_name: str, class_name: str, request: TablePolicyUpdate):
    try:
        return _repo().upsert_table_policy(
            job_name,
            class_name,
            **request.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Mapped ontology class not found") from exc


@router.get("/jobs/{job_name}/incremental-capabilities")
def incremental_capabilities(job_name: str):
    try:
        _repo().list_table_policies(job_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job not found") from exc
    latest = _repo().latest_source_capabilities()
    return latest or {"available": False}


@router.post("/jobs/{job_name}/incremental-capabilities/probe")
def probe_incremental(job_name: str):
    try:
        return execute_incremental_probe(_settings(), _repo(), job_name=job_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Incremental capability probe failed: {exc}") from exc


@router.post("/jobs/{job_name}/incremental-plan")
def incremental_plan(job_name: str):
    try:
        return execute_incremental_plan(_settings(), _repo(), job_name=job_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Incremental window planning failed: {exc}") from exc


@router.post("/jobs/{job_name}/incremental-preview")
def incremental_preview(job_name: str):
    try:
        return build_incremental_preview(_settings(), _repo(), job_name=job_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Incremental preview failed: {exc}") from exc


@router.get("/jobs/{job_name}/continuous-status")
def get_continuous_sync_status(
    job_name: str,
    profile_key: str = Query(default="opcenter2607-core"),
    environment_key: Literal["dev", "uat", "prod"] = Query(default="dev"),
    route_key: str | None = Query(default=None),
):
    try:
        return continuous_sync_status(
            _repo(), job_name=job_name, profile_key=profile_key,
            environment_key=environment_key,
            route_key=route_key,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job, profile or environment not found") from exc


@router.post("/jobs/{job_name}/continuous-sync")
def run_continuous_sync(job_name: str, request: ContinuousSyncRequest):
    try:
        return execute_continuous_sync(
            _settings(), _repo(), job_name=job_name,
            profile_key=request.profile_key,
            environment_key=request.environment_key,
            route_key=request.route_key,
            actor=request.actor, apply=request.apply,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job, profile or environment not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/jobs/{job_name}/dry-run")
def dry_run_job(job_name: str):
    try:
        result = execute_dry_run(_settings(), _repo(), job_name=job_name)
        return {"runId": result["runId"], "status": result["status"], "artifact": result["artifact"]}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/jobs/{job_name}/preview")
def preview_job(job_name: str):
    try:
        manifest = build_full_preview(_settings(), _repo(), job_name=job_name)
        return {
            "runId": manifest["runId"],
            "previewOnly": manifest["previewOnly"],
            "graphStudioMutated": manifest["graphStudioMutated"],
            "instances": manifest["data"]["instances"],
            "modelTriples": manifest["model"]["triples"],
            "dataTriples": manifest["data"]["dataTriples"],
            "report": manifest["files"]["report"],
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/runs")
def runs(limit: int = Query(default=100, ge=1, le=500)):
    return {"items": _repo().list_runs(limit=limit)}


@router.get("/profiles")
def graph_profiles():
    return {"items": _repo().list_graph_profiles()}


@router.get("/profiles/{profile_key}")
def graph_profile(profile_key: str):
    try:
        payload = _repo().graph_profile(profile_key)
        payload["issues"] = validate_graph_profile(
            payload["profile"], payload["classes"], payload["relationships"]
        )
        return payload
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc


@router.get("/profiles/{profile_key}/candidates")
def graph_profile_candidates(profile_key: str):
    try:
        return _repo().graph_profile_candidates(profile_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc


@router.put("/profiles/{profile_key}")
def update_graph_profile(profile_key: str, request: GraphProfileUpdate):
    try:
        return _repo().update_graph_profile(profile_key, **request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc


@router.put("/profiles/{profile_key}/classes/{class_name}")
def update_profile_class(profile_key: str, class_name: str, request: ProfileClassUpdate):
    try:
        return _repo().upsert_profile_class(
            profile_key, class_name, **request.model_dump()
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Mapped ontology class not found") from exc


@router.put(
    "/profiles/{profile_key}/relationships/{source_class}/{relationship_name}/{target_class}"
)
def update_profile_relationship(
    profile_key: str,
    source_class: str,
    relationship_name: str,
    target_class: str,
    request: ProfileRelationshipUpdate,
):
    try:
        return _repo().upsert_profile_relationship(
            profile_key,
            source_class,
            relationship_name,
            target_class,
            **request.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Ontology relationship candidate not found") from exc


@router.post("/profiles/{profile_key}/closure-plan")
def context_closure_plan(profile_key: str):
    try:
        payload = _repo().graph_profile(profile_key)
        return plan_context_closure(
            payload["profile"], payload["classes"], payload["relationships"]
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc


@router.get("/profiles/{profile_key}/governance")
def governance_profile(profile_key: str):
    try:
        return _repo().governance_profile(profile_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc


@router.get("/profiles/{profile_key}/contract-candidates")
def governance_contract_candidates(profile_key: str):
    return _repo().governance_contract_candidates(profile_key)


@router.post("/profiles/{profile_key}/data-contracts")
def create_data_contract(profile_key: str, request: DataContractCreate):
    try:
        return _repo().create_data_contract(profile_key, **request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Missing data contract candidate not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/profiles/{profile_key}/relationship-contracts")
def create_relationship_contract(profile_key: str, request: RelationshipContractCreate):
    try:
        return _repo().create_relationship_contract(profile_key, **request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Missing relationship contract candidate not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/data-contracts/{contract_key}")
def update_data_contract(contract_key: str, request: DataContractUpdate):
    try:
        return _repo().update_data_contract(contract_key, **request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data contract not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/relationship-contracts/{relationship_contract_key}")
def update_relationship_contract(
    relationship_contract_key: str,
    request: RelationshipContractUpdate,
):
    try:
        return _repo().update_relationship_contract(
            relationship_contract_key, **request.model_dump()
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Relationship contract not found") from exc


@router.post("/profiles/{profile_key}/curation-preview")
def curation_preview(profile_key: str):
    try:
        return build_curation_preview(_settings(), _repo(), profile_key=profile_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Curation preview failed: {exc}") from exc


@router.get("/data-contracts/{contract_key}/schema")
def contract_schema(contract_key: str):
    try:
        return _repo().contract_schema(contract_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data contract not found") from exc


@router.get("/profiles/{profile_key}/schema-changes")
def schema_changes(profile_key: str, limit: int = Query(default=100, ge=1, le=500)):
    return {"items": _repo().list_schema_changes(profile_key, limit=limit)}


@router.get("/profiles/{profile_key}/schema-drift")
def schema_drift_status(profile_key: str):
    return latest_schema_drift(_repo(), profile_key=profile_key)


@router.post("/profiles/{profile_key}/schema-drift/scan")
def scan_contract_schema_drift(profile_key: str):
    try:
        return scan_schema_drift(_settings(), _repo(), profile_key=profile_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Graph profile not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/profiles/{profile_key}/schema-changes")
def create_schema_change(profile_key: str, request: SchemaChangeCreate):
    repository = _repo()
    try:
        schema = repository.contract_schema(request.contract_key)
        if schema["contract"]["profile_key"] != profile_key:
            raise HTTPException(status_code=422, detail="Data contract does not belong to this graph profile")
        analysis = analyze_schema_change(
            schema["contract"],
            schema["fields"],
            [item.model_dump() for item in request.operations],
            schema["dependencies"],
            migration_strategy=request.migration_strategy,
            rollback_strategy=request.rollback_strategy,
        )
        return repository.record_schema_change(
            profile_key=profile_key,
            contract_key=request.contract_key,
            title=request.title,
            description=request.description,
            migration_strategy=request.migration_strategy,
            rollback_strategy=request.rollback_strategy,
            requested_by=request.requested_by,
            analysis=analysis,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data contract not found") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/schema-changes/{change_id}/review")
def review_schema_change(change_id: str, request: SchemaChangeReview):
    try:
        return _repo().review_schema_change(
            uuid.UUID(change_id),
            status=request.status,
            actor=request.actor,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Schema change request not found") from exc


@router.post("/schema-changes/{change_id}/apply")
def apply_contract_schema_change(change_id: str, request: ActorRequest):
    try:
        return apply_schema_change(
            _repo(), change_id=uuid.UUID(change_id), actor=request.actor,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Schema change request not found") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/schema-changes/{change_id}/rollback")
def rollback_contract_schema_change(change_id: str, request: ActorRequest):
    try:
        return rollback_schema_change(
            _repo(), change_id=uuid.UUID(change_id), actor=request.actor,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Schema change request not found") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/profiles/{profile_key}/attribute-projections")
def attribute_projections(profile_key: str):
    return {"items": _repo().list_attribute_projections(profile_key)}


@router.get("/attribute-projections/{projection_key}")
def attribute_projection(projection_key: str):
    try:
        return _repo().attribute_projection(projection_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Attribute projection not found") from exc


@router.put("/profiles/{profile_key}/attribute-projections/{projection_key}")
def update_attribute_projection(
    profile_key: str,
    projection_key: str,
    request: AttributeProjectionUpdate,
):
    repository = _repo()
    try:
        schema = repository.contract_schema(request.target_contract_key)
        if schema["contract"]["profile_key"] != profile_key:
            raise HTTPException(status_code=422, detail="Data contract does not belong to this graph profile")
        payload = request.model_dump()
        validation = validate_projection_definition(
            payload,
            payload["fields"],
            {**schema["contract"], "fields": schema["fields"]},
        )
        if not validation["valid"]:
            raise HTTPException(status_code=422, detail="；".join(validation["errors"]))
        return repository.upsert_attribute_projection(
            projection_key=projection_key,
            profile_key=profile_key,
            **payload,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data contract not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/attribute-projections/{projection_key}/preview")
def preview_projection(projection_key: str):
    try:
        return preview_attribute_projection(
            _settings(), _repo(), projection_key=projection_key,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Attribute projection not found") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Projection source preview failed: {exc}") from exc


@router.put("/attribute-projections/{projection_key}/review")
def review_projection(projection_key: str, request: AttributeProjectionReview):
    try:
        return _repo().review_attribute_projection(
            projection_key, status=request.status, actor=request.actor,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Attribute projection not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/profiles/{profile_key}/materialization")
def get_materialization_status(profile_key: str):
    try:
        return materialization_status(_repo(), profile_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc


@router.get("/profiles/{profile_key}/data-sync")
def get_data_sync_status(profile_key: str):
    try:
        return data_sync_status(_repo(), profile_key=profile_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc


@router.get("/profiles/{profile_key}/data-sync/classes/{class_name}/configuration")
def preview_sync_class_configuration(profile_key: str, class_name: str):
    try:
        return configuration_preview(_repo(), profile_key, class_name)
    except (ValueError, KeyError) as exc:
        raise HTTPException(422, str(exc)) from exc


@router.put("/profiles/{profile_key}/data-sync/classes/{class_name}/configuration")
def configure_sync_class(profile_key: str, class_name: str, request: SyncClassConfiguration):
    try:
        return save_configuration(_repo(), profile_key, class_name, **request.model_dump())
    except (ValueError, KeyError) as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/profiles/{profile_key}/data-sync")
def run_data_sync(profile_key: str, request: DataSyncRequest):
    try:
        return execute_audited_data_sync(
            _settings(), _repo(), profile_key=profile_key, actor=request.actor,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/profiles/{profile_key}/data-sync/schedule")
def configure_data_sync_schedule(profile_key: str, request: DataSyncScheduleRequest):
    try:
        return {
            "ok": True,
            "schedule": update_data_sync_schedule(
                _repo(), profile_key=profile_key, **request.model_dump(),
            ),
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/profiles/{profile_key}/materialization")
def materialize_profile(profile_key: str, request: MaterializationRequest):
    try:
        return execute_materialization(
            _settings(), _repo(), profile_key=profile_key,
            apply=request.apply, activate=request.activate, actor=request.actor,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Business graph profile not found") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/profiles/{profile_key}/releases/{release_id}/activate")
def activate_curated_release(profile_key: str, release_id: str, request: ReleaseActivation):
    try:
        return activate_release(
            _repo(), profile_key=profile_key,
            release_id=uuid.UUID(release_id), actor=request.actor,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Curated release not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/profiles/{profile_key}/releases/rollback")
def rollback_curated_release(profile_key: str, request: ReleaseActivation):
    try:
        return rollback_release(_repo(), profile_key=profile_key, actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/profiles/{profile_key}/deployments")
def get_deployments(profile_key: str):
    return deployment_status(_repo(), profile_key)


@router.get("/graphstudio-targets")
def get_graphstudio_targets(profile_key: str = Query(default="opcenter2607-core")):
    status = deployment_status(_repo(), profile_key)
    return {"items": status["targets"], "routes": status["routes"]}


@router.put("/graphstudio-targets/{target_key}")
def put_graphstudio_target(target_key: str, request: GraphStudioTargetUpdate):
    try:
        return upsert_graphstudio_target(
            _repo(), target_key=target_key, **request.model_dump(),
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/publication-routes/{route_key}")
def put_publication_route(route_key: str, request: PublicationRouteUpdate):
    try:
        return upsert_publication_route(
            _repo(), route_key=route_key, **request.model_dump(),
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/publication-routes/{route_key}")
def patch_publication_route(route_key: str, request: DeploymentEnvironmentUpdate):
    try:
        return update_publication_route(
            _repo(), route_key=route_key, apply_enabled=request.apply_enabled,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publication route not found") from exc


@router.get("/profiles/{profile_key}/deployments/plan/{environment_key}")
def get_deployment_plan(
    profile_key: str,
    environment_key: str,
    route_key: str | None = Query(default=None),
):
    try:
        return build_deployment_plan(
            _repo(), profile_key=profile_key, environment_key=environment_key,
            route_key=route_key or None,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Deployment environment not found") from exc


@router.put("/deployment-environments/{environment_key}")
def configure_deployment_environment(
    environment_key: Literal["dev", "uat", "prod"],
    request: DeploymentEnvironmentUpdate,
):
    try:
        return update_deployment_environment(
            _repo(),
            environment_key=environment_key,
            apply_enabled=request.apply_enabled,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Deployment environment not found") from exc


@router.post("/profiles/{profile_key}/deployments")
def prepare_deployment(profile_key: str, request: DeploymentCreate):
    try:
        return create_deployment(
            _repo(), profile_key=profile_key,
            environment_key=request.environment_key,
            route_key=request.route_key,
            release_id=request.release_id, actor=request.actor,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Deployment environment or release not found") from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/deployments/{deployment_id}/approve")
def approve_graph_deployment(deployment_id: str, request: ActorRequest):
    try:
        return approve_deployment(_repo(), uuid.UUID(deployment_id), request.actor)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/deployments/{deployment_id}/apply")
def apply_graph_deployment(deployment_id: str):
    try:
        return apply_deployment(_settings(), _repo(), deployment_id=uuid.UUID(deployment_id))
    except ValueError as exc:
        # UUID parsing and deployment-state errors are actionable client
        # feedback, not opaque server failures.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Deployment not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # Keep unexpected preflight/database failures visible in the console.
        # apply_deployment itself records failures once the external write stage
        # begins, so this principally covers failures before Graph Studio is
        # mutated.
        raise HTTPException(status_code=422, detail=f"发布预检失败：{exc}") from exc


@router.get("/profiles/{profile_key}/observability")
def get_observability(profile_key: str):
    return observability_status(_repo(), profile_key)


@router.post("/profiles/{profile_key}/health-check")
def execute_health_check(profile_key: str):
    try:
        return run_health_check(_repo(), profile_key)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_health_alert(alert_id: str, request: ActorRequest):
    try:
        return acknowledge_alert(_repo(), uuid.UUID(alert_id), request.actor)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/actions")
def actions():
    payload = list_actions(_repo())
    payload["identityMode"] = _settings().action_auth_mode
    return payload


@router.put("/actions/definitions/{action_key}")
def update_action_definition(action_key: str, request: ActionDefinitionUpdate):
    try:
        return upsert_action_definition(_repo(), action_key=action_key, **request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/actions/definitions/{action_key}/review")
def review_action(action_key: str, payload: ActionDefinitionReview, request: Request):
    principal = action_principal(request, _settings())
    require_action_principal(principal)
    try:
        return review_action_definition(
            _repo(), action_key, status=payload.status, actor=principal.subject,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Action definition not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/actions/openapi-candidates")
def action_openapi_candidates(source_file: str | None = Query(default=None)):
    try:
        return {"items": openapi_action_candidates(source_file)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="OpenAPI source file not found") from exc


@router.get("/actions/openapi-sources")
def action_openapi_sources():
    return {"items": openapi_action_sources()}


@router.post("/actions/openapi-import")
def import_action_from_openapi(request: OpenApiActionImport):
    try:
        return import_openapi_action(_repo(), **request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="OpenAPI operation not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/actions/{action_key}/plan")
def plan_camstar_action(action_key: str, payload: ActionPlanRequest, request: Request):
    principal = action_principal(request, _settings())
    if not payload.dry_run:
        require_action_principal(principal)
    try:
        return plan_action(
            _repo(), action_key=action_key, payload=payload.payload,
            idempotency_key=payload.idempotency_key, dry_run=payload.dry_run,
            actor=principal.subject, actor_roles=list(principal.roles),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Action definition not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/actions/invocations/{invocation_id}/approve")
def approve_camstar_action(invocation_id: str, request: Request):
    principal = action_principal(request, _settings())
    require_action_principal(principal)
    try:
        return approve_action(
            _repo(), uuid.UUID(invocation_id), principal.subject,
            list(principal.roles),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Action invocation not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/actions/invocations/{invocation_id}/execute")
def execute_camstar_action(invocation_id: str, request: Request):
    principal = action_principal(request, _settings())
    require_action_principal(principal)
    try:
        return execute_action(
            _settings(), _repo(), invocation_id=uuid.UUID(invocation_id),
            actor=principal.subject, actor_roles=list(principal.roles),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Action invocation not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/actions/invocations/{invocation_id}/compensate")
def compensate_camstar_action(
    invocation_id: str,
    payload: ActionCompensationRequest,
    request: Request,
):
    principal = action_principal(request, _settings())
    require_action_principal(principal)
    try:
        return plan_compensation(
            _repo(), original_invocation_id=uuid.UUID(invocation_id),
            payload=payload.payload, actor=principal.subject,
            actor_roles=list(principal.roles),
            idempotency_key=payload.idempotency_key,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Action invocation not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/ontology-governance")
def get_ontology_governance(profile_key: str = Query(default="opcenter2607-core")):
    try:
        return ontology_governance_status(_settings(), _repo(), profile_key)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Publish ontology unavailable: {exc}") from exc


@router.post("/ontology-governance/initialize")
def initialize_ontology_governance(
    payload: OntologyActorRequest,
    profile_key: str = Query(default="opcenter2607-core"),
):
    try:
        return initialize_governance(_settings(), _repo(), profile_key=profile_key, actor=payload.actor)
    except (KeyError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/ontology-governance/source-candidates")
def get_ontology_source_candidates(q: str = Query(default="", max_length=200), limit: int = Query(default=100, ge=1, le=500)):
    try:
        return {"items": ontology_source_candidates(_settings(), q, limit)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Source ontology unavailable: {exc}") from exc


@router.post("/ontology-governance/discovery-plan")
def get_ontology_discovery_plan(payload: OntologyDiscoveryPlanRequest):
    try:
        return build_ontology_discovery_plan(
            _settings(), payload.selected_classes, dialect=payload.dialect,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ontology discovery unavailable: {exc}") from exc


@router.post("/ontology-governance/workspaces/{workspace_key}/classes")
def create_publish_class(workspace_key: str, payload: PublishClassCreate):
    try:
        return add_publish_class(
            _settings(), _repo(), workspace_key=workspace_key,
            **payload.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Source class or workspace not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/ontology-governance/workspaces/{workspace_key}/classes/{class_uid}")
def edit_publish_class(workspace_key: str, class_uid: str, payload: PublishClassUpdate):
    try:
        update_publish_class(_settings(), _repo(), workspace_key, class_uid, payload.model_dump())
        return {"ok": True}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publish class not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/ontology-governance/workspaces/{workspace_key}/classes/{class_uid}")
def delete_publish_class(workspace_key: str, class_uid: str):
    try:
        remove_publish_class(_settings(), _repo(), workspace_key, class_uid)
        return {"ok": True}
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/ontology-governance/workspaces/{workspace_key}/classes/{class_uid}/presentation")
def edit_publish_presentation(
    workspace_key: str, class_uid: str, payload: PublishPresentationUpdate,
):
    try:
        return update_publish_presentation(
            _settings(), _repo(), workspace_key, class_uid, payload.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publish class not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/ontology-governance/workspaces/{workspace_key}/classes/{class_uid}/properties")
def edit_publish_property(workspace_key: str, class_uid: str, payload: PublishPropertyUpdate):
    try:
        return upsert_publish_property(
            _settings(), _repo(), workspace_key, class_uid, payload.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publish class not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/ontology-governance/workspaces/{workspace_key}/relationships")
def create_publish_relationship(workspace_key: str, payload: PublishRelationshipUpdate):
    try:
        return add_publish_relationship(
            _settings(), _repo(), workspace_key, payload.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/ontology-governance/workspaces/{workspace_key}/classes/{class_uid}/relationship-suggestions")
def get_publish_relationship_suggestions(workspace_key: str, class_uid: str):
    try:
        return publish_relationship_suggestions(
            _settings(), _repo(), workspace_key, class_uid, max_depth=2,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publish class or workspace not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/ontology-governance/workspaces/{workspace_key}/relationship-suggestions/apply")
def apply_publish_relation_suggestions(workspace_key: str, payload: RelationshipSuggestionApply):
    try:
        return apply_publish_relationship_suggestions(
            _settings(), _repo(), workspace_key, payload.classUid, payload.suggestionIds,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publish class or workspace not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/ontology-governance/workspaces/{workspace_key}/relationship-suggestion-batches/{batch_id}")
def undo_publish_relation_suggestions(workspace_key: str, batch_id: str):
    try:
        return undo_publish_relationship_suggestion_batch(
            _settings(), _repo(), workspace_key, batch_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Publish workspace not found") from exc


@router.delete("/ontology-governance/workspaces/{workspace_key}/relationships/{relationship_key}")
def delete_publish_relationship(workspace_key: str, relationship_key: str):
    remove_publish_relationship(_settings(), _repo(), workspace_key, relationship_key)
    return {"ok": True}


@router.post("/ontology-governance/workspaces/{workspace_key}/validate")
def validate_publish_workspace(workspace_key: str):
    try:
        return validate_ontology_workspace(_settings(), _repo(), workspace_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Ontology workspace not found") from exc


@router.post("/ontology-governance/workspaces/{workspace_key}/review")
def review_publish_workspace(workspace_key: str, payload: OntologyActorRequest):
    try:
        return review_ontology_workspace(_settings(), _repo(), workspace_key, payload.actor)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/ontology-governance/workspaces/{workspace_key}/approve")
def approve_publish_workspace(workspace_key: str, payload: OntologyActorRequest):
    try:
        return approve_ontology_workspace(_settings(), _repo(), workspace_key, payload.actor)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/ontology-governance/releases/{release_id}/activate")
def activate_publish_ontology_release(
    release_id: str,
    payload: OntologyActorRequest,
    profile_key: str = Query(default="opcenter2607-core"),
):
    try:
        return activate_ontology_release(_repo(), profile_key, uuid.UUID(release_id), payload.actor)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/mappings")
def mappings():
    repository = _repo()
    return {
        "catalog": repository.mapping_catalog(),
        "overrides": repository.list_mapping_overrides(),
    }


@router.post("/mappings/compile")
def compile_mappings():
    return compile_catalog(_settings(), _repo())


@router.put("/mappings/properties/{class_name}/{property_name}/override")
def override_property(class_name: str, property_name: str, request: PropertyOverrideUpdate):
    return _repo().upsert_property_override(
        class_name=class_name,
        property_name=property_name,
        **request.model_dump(),
    )


@router.put("/mappings/relationships/{source_class}/{relationship_name}/{target_class}/override")
def override_relationship(
    source_class: str,
    relationship_name: str,
    target_class: str,
    request: RelationshipOverrideUpdate,
):
    return _repo().upsert_relationship_override(
        source_class=source_class,
        relationship_name=relationship_name,
        target_class=target_class,
        **request.model_dump(),
    )


@router.get("/settings")
def settings():
    return {"items": _repo().list_settings()}


@router.put("/settings/{setting_key}")
def update_setting(setting_key: str, request: SettingUpdate):
    try:
        return _repo().update_setting(setting_key, request.value)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Editable setting not found") from exc
