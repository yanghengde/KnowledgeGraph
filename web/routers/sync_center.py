"""Management API for the Camstar to Graph Studio synchronization center."""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator

from src.graphstudio_sync.config import SyncSettings
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
from src.graphstudio_sync.deployment import (
    apply_deployment,
    approve_deployment,
    build_deployment_plan,
    create_deployment,
    deployment_status,
    update_publication_route,
    upsert_graphstudio_target,
    upsert_publication_route,
    update_deployment_environment,
)
from src.graphstudio_sync.incremental import execute_incremental_plan, execute_incremental_probe
from src.graphstudio_sync.incremental_preview import build_incremental_preview
from src.graphstudio_sync.graph_profile import plan_context_closure, validate_graph_profile
from src.graphstudio_sync.materialization import (
    activate_release,
    execute_materialization,
    materialization_status,
    rollback_release,
)
from src.graphstudio_sync.observability import acknowledge_alert, observability_status, run_health_check
from src.graphstudio_sync.repository import ControlPlaneRepository
from src.graphstudio_sync.preview import build_full_preview
from src.graphstudio_sync.publish_ontology import (
    activate_release as activate_ontology_release,
    add_class as add_publish_class,
    add_relationship as add_publish_relationship,
    apply_relationship_suggestions as apply_publish_relationship_suggestions,
    approve_workspace as approve_ontology_workspace,
    build_discovery_plan as build_ontology_discovery_plan,
    initialize_governance,
    ontology_governance_status,
    remove_class as remove_publish_class,
    remove_relationship as remove_publish_relationship,
    relationship_suggestions as publish_relationship_suggestions,
    review_workspace as review_ontology_workspace,
    source_candidates as ontology_source_candidates,
    update_class as update_publish_class,
    update_presentation as update_publish_presentation,
    undo_relationship_suggestion_batch as undo_publish_relationship_suggestion_batch,
    upsert_property as upsert_publish_property,
    validate_workspace as validate_ontology_workspace,
)
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


class ConnectionUpdate(BaseModel):
    kind: Literal[
        "camstar_sqlserver", "camstar_oracle", "ontology_neo4j",
        "publish_ontology_neo4j", "graph_studio", "state_postgresql",
    ]
    display_name: str = Field(min_length=1, max_length=120)
    endpoint: str = Field(min_length=1, max_length=500)
    database_name: str | None = Field(default=None, max_length=500)
    username: str | None = Field(default=None, max_length=200)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class NavigationUpdate(BaseModel):
    label_zh: str = Field(min_length=1, max_length=80)
    label_en: str = Field(min_length=1, max_length=80)
    sort_order: int = Field(ge=0, le=10000)
    enabled: bool = True


class JobUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    mode: Literal["atomic_snapshot", "partitioned_incremental"]
    schedule: str | None = Field(default=None, max_length=100)
    timezone: str = Field(default="Asia/Shanghai", min_length=1, max_length=100)
    enabled: bool = True
    retention_success: int = Field(default=3, ge=1, le=100)


class TablePolicyUpdate(BaseModel):
    strategy: Literal["snapshot", "watermark", "append_only", "cdc", "excluded"]
    watermark_column: str | None = Field(default=None, max_length=200)
    partition_column: str | None = Field(default=None, max_length=200)
    batch_rows: int = Field(default=10000, ge=100, le=1000000)
    target_shard_bytes: int = Field(default=67108864, ge=1048576, le=4294967296)
    hot_window_days: int | None = Field(default=None, ge=1, le=36500)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_incremental_cursor(self):
        if self.strategy in {"watermark", "append_only"} and not self.watermark_column:
            raise ValueError("watermark_column is required for watermark and append_only strategies")
        return self


class SettingUpdate(BaseModel):
    value: Any


class PropertyOverrideUpdate(BaseModel):
    physical_table: str = Field(min_length=1, max_length=200)
    physical_column: str | None = Field(default=None, max_length=200)
    mapping_kind: Literal["property", "relationship", "computed", "ignored"] = "property"
    expression: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=2000)


class RelationshipOverrideUpdate(BaseModel):
    source_property: str = Field(min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)


class OntologyActorRequest(BaseModel):
    actor: str = Field(min_length=2, max_length=200)


class OntologyDiscoveryPlanRequest(BaseModel):
    selected_classes: list[str] = Field(default_factory=list, max_length=16)
    dialect: Literal["sqlserver", "oracle"] = "sqlserver"


class PublishClassCreate(BaseModel):
    source_class: str | None = Field(default=None, max_length=200)
    target_name: str = Field(min_length=1, max_length=200)
    label: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    role: Literal["core", "context", "reference", "on_demand", "excluded"] = "context"
    orphan_policy: Literal["reject", "quarantine", "allow", "referenced_only"] = "quarantine"


class PublishClassUpdate(BaseModel):
    targetName: str = Field(min_length=1, max_length=200)
    label: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    role: Literal["core", "context", "reference", "on_demand", "excluded"] = "context"
    orphanPolicy: Literal["reject", "quarantine", "allow", "referenced_only"] = "quarantine"


class PublishPresentationUpdate(BaseModel):
    labelMode: Literal["auto", "field", "template"] = "auto"
    labelField: str | None = Field(default=None, max_length=300)
    labelTemplate: str | None = Field(default=None, max_length=500)
    labelFallbacks: list[str] = Field(default_factory=list, max_length=12)
    searchFields: list[str] = Field(default_factory=list, max_length=24)
    emitRdfsLabel: bool = True


class PublishPropertyUpdate(BaseModel):
    uid: str | None = Field(default=None, max_length=600)
    propertyKey: str | None = Field(default=None, max_length=300)
    sourceName: str | None = Field(default=None, max_length=300)
    targetName: str = Field(min_length=1, max_length=300)
    sourcePath: str | None = Field(default=None, max_length=1000)
    dataType: str = Field(default="String", min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=4000)
    required: bool = False
    published: bool = True
    origin: Literal["source", "custom", "projection"] = "custom"


class PublishRelationshipUpdate(BaseModel):
    relationshipKey: str | None = Field(default=None, max_length=300)
    sourceUid: str = Field(min_length=1, max_length=600)
    targetUid: str = Field(min_length=1, max_length=600)
    sourceRelationship: str | None = Field(default=None, max_length=300)
    targetName: str = Field(min_length=1, max_length=300)
    usage: Literal["published_link", "projection_only", "context_only", "excluded"] = "published_link"
    strength: Literal["core", "context", "weak", "on_demand"] = "context"
    cardinality: str = Field(default="many-to-one", max_length=100)
    requiredContext: bool = False
    questionEnabled: bool = True
    description: str | None = Field(default=None, max_length=4000)


class RelationshipSuggestionApply(BaseModel):
    classUid: str = Field(min_length=1, max_length=600)
    suggestionIds: list[str] = Field(min_length=1, max_length=12)


class GraphProfileUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    enabled: bool = True
    max_depth: int = Field(default=2, ge=0, le=8)
    max_context_nodes_per_seed: int = Field(default=200, ge=1, le=100000)
    max_total_nodes_per_run: int = Field(default=1000000, ge=1, le=1000000000)


class ProfileClassUpdate(BaseModel):
    role: Literal["core", "context", "reference", "on_demand", "excluded"]
    orphan_policy: Literal["reject", "quarantine", "allow", "referenced_only"] = "quarantine"
    seed_enabled: bool = False
    max_instances_per_run: int | None = Field(default=None, ge=1, le=1000000000)
    priority: int = Field(default=100, ge=0, le=10000)
    enabled: bool = True
    review_status: Literal["draft", "reviewed", "approved"] = "draft"

    @model_validator(mode="after")
    def validate_seed_role(self):
        if self.seed_enabled and self.role != "core":
            raise ValueError("Only a core class may be used as a context seed")
        return self


class ProfileRelationshipUpdate(BaseModel):
    strength: Literal["core", "context", "weak", "on_demand"]
    required_context: bool = False
    traverse: bool = False
    direction: Literal["outgoing", "incoming", "both"] = "outgoing"
    max_depth: int | None = Field(default=None, ge=1, le=8)
    max_targets_per_source: int = Field(default=50, ge=1, le=100000)
    enabled: bool = True
    review_status: Literal["draft", "reviewed", "approved"] = "draft"

    @model_validator(mode="after")
    def validate_traversal_strength(self):
        if self.strength == "weak" and self.traverse:
            raise ValueError("Weak relationships cannot drive context traversal")
        if self.required_context and self.strength not in {"core", "context"}:
            raise ValueError("Required context must use a core or context relationship")
        return self


class DataContractUpdate(BaseModel):
    status: Literal["draft", "reviewed", "approved", "retired"] = "draft"
    business_key_columns: list[str] = Field(default_factory=list, max_length=20)
    required_columns: list[str] = Field(default_factory=list, max_length=100)
    freshness_column: str | None = Field(default=None, max_length=200)
    preview_row_limit: int = Field(default=100000, ge=1, le=1000000)
    publication_layer: Literal["core", "context", "reference", "quarantine"] = "core"


class DataContractCreate(BaseModel):
    class_name: str = Field(min_length=1, max_length=200)
    primary_key_columns: list[str] = Field(min_length=1, max_length=10)
    business_key_columns: list[str] = Field(default_factory=list, max_length=20)
    selected_columns: list[str] = Field(min_length=1, max_length=1000)
    required_columns: list[str] = Field(default_factory=list, max_length=100)
    freshness_column: str | None = Field(default=None, max_length=200)
    preview_row_limit: int = Field(default=100000, ge=1, le=1000000)
    publication_layer: Literal["core", "context", "reference", "quarantine"] = "core"


class RelationshipContractUpdate(BaseModel):
    status: Literal["draft", "reviewed", "approved", "retired"] = "draft"
    semantic_role: str = Field(min_length=1, max_length=200)
    required_context: bool = False


class RelationshipContractCreate(BaseModel):
    source_class: str = Field(min_length=1, max_length=200)
    relationship_name: str = Field(min_length=1, max_length=300)
    target_class: str = Field(min_length=1, max_length=200)
    semantic_role: str = Field(min_length=1, max_length=200)
    required_context: bool = False


class SchemaChangeOperation(BaseModel):
    operation: Literal[
        "add_field", "deprecate_field", "retire_field", "rename_field",
        "change_type", "change_required", "change_key", "change_source",
        "change_transform",
    ]
    field_key: str = Field(min_length=1, max_length=300)
    after_state: dict[str, Any] | None = None
    notes: str | None = Field(default=None, max_length=2000)


class SchemaChangeCreate(BaseModel):
    contract_key: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    migration_strategy: str | None = Field(default=None, max_length=8000)
    rollback_strategy: str | None = Field(default=None, max_length=8000)
    requested_by: str | None = Field(default=None, max_length=200)
    operations: list[SchemaChangeOperation] = Field(min_length=1, max_length=100)


class SchemaChangeReview(BaseModel):
    status: Literal["reviewed", "approved", "rejected"]
    actor: str | None = Field(default=None, max_length=200)


class AttributeProjectionFieldInput(BaseModel):
    field_key: str = Field(min_length=1, max_length=300)
    source_path: str = Field(min_length=3, max_length=400)
    target_field: str = Field(min_length=1, max_length=200)
    data_type: Literal["String", "Integer", "Float", "Boolean", "DateTime", "Date", "Navigation"] = "String"
    required: bool = False
    ontology_property: str | None = Field(default=None, max_length=500)
    lifecycle_status: Literal["active", "deprecated", "retired"] = "active"
    ordinal_position: int = Field(default=10, ge=0, le=100000)
    config: dict[str, Any] = Field(default_factory=dict)


class AttributeProjectionUpdate(BaseModel):
    target_contract_key: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    source_schema: str = Field(min_length=1, max_length=200)
    source_table: str = Field(min_length=1, max_length=200)
    source_alias: str = Field(default="src", min_length=1, max_length=80)
    owner_mapping: list[dict[str, Any]] = Field(min_length=1, max_length=20)
    join_plan: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    row_filters: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    cardinality: Literal["one", "many"] = "one"
    multiple_match_policy: Literal["reject", "first", "latest", "array"] = "reject"
    missing_policy: Literal["null", "quarantine", "reject"] = "null"
    collision_policy: Literal["reject", "overwrite", "coalesce"] = "reject"
    order_by: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    preview_row_limit: int = Field(default=200, ge=1, le=10000)
    enabled: bool = True
    fields: list[AttributeProjectionFieldInput] = Field(min_length=1, max_length=200)
    config: dict[str, Any] = Field(default_factory=dict)


class AttributeProjectionReview(BaseModel):
    status: Literal["reviewed", "approved", "retired"]
    actor: str | None = Field(default=None, max_length=200)


class MaterializationRequest(BaseModel):
    apply: bool = False
    activate: bool = False
    actor: str | None = Field(default=None, max_length=200)


class ContinuousSyncRequest(BaseModel):
    apply: bool = False
    profile_key: str = Field(default="opcenter2607-core", min_length=1, max_length=200)
    environment_key: Literal["dev", "uat", "prod"] = "dev"
    route_key: str | None = Field(default=None, max_length=300)
    actor: str | None = Field(default="local-console", max_length=200)


class DataSyncRequest(BaseModel):
    actor: str = Field(default="local-console", min_length=2, max_length=200)


class DataSyncScheduleRequest(BaseModel):
    enabled: bool
    interval_minutes: int = Field(default=15, ge=1, le=10080)
    max_attempts: int = Field(default=3, ge=1, le=10)
    retry_backoff_seconds: int = Field(default=60, ge=5, le=86400)


class ReleaseActivation(BaseModel):
    actor: str | None = Field(default=None, max_length=200)


class DeploymentCreate(BaseModel):
    environment_key: Literal["dev", "uat", "prod"] = "dev"
    route_key: str | None = Field(default=None, max_length=300)
    release_id: uuid.UUID | None = None
    actor: str | None = Field(default=None, max_length=200)


class DeploymentEnvironmentUpdate(BaseModel):
    apply_enabled: bool


class GraphStudioTargetUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    graphmart_uri: str = Field(min_length=1, max_length=1000)
    connection_key: str = Field(default="graph-studio", min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class PublicationRouteUpdate(BaseModel):
    profile_key: str = Field(min_length=1, max_length=200)
    environment_key: Literal["dev", "uat", "prod"]
    target_key: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=300)
    promotion_order: int = Field(ge=1, le=10000)
    apply_enabled: bool = False
    requires_approval: bool = True
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class ActorRequest(BaseModel):
    actor: str | None = Field(default=None, max_length=200)


class ActionPlanRequest(BaseModel):
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=8, max_length=300)
    dry_run: bool = True


class ActionDefinitionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    object_class: str = Field(min_length=1, max_length=200)
    endpoint_path: str = Field(min_length=1, max_length=1000)
    http_method: Literal["POST", "PUT", "PATCH", "DELETE"]
    input_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    allowed_roles: list[str] = Field(min_length=1, max_length=100)
    approval_required: bool = True
    timeout_seconds: int = Field(default=60, ge=1, le=600)
    retry_policy: dict[str, Any] = Field(default_factory=lambda: {"maxAttempts": 1})
    compensation_action_key: str | None = Field(default=None, max_length=300)
    config: dict[str, Any] = Field(default_factory=dict)


class ActionDefinitionReview(BaseModel):
    status: Literal["reviewed", "approved", "retired"]


class OpenApiActionImport(BaseModel):
    source_file: str = Field(min_length=6, max_length=300)
    operation_id: str = Field(min_length=1, max_length=1000)


class ActionCompensationRequest(BaseModel):
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=8, max_length=300)


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
    from src.graphstudio_sync.ontology_backend import backend
    if backend() == "postgres":
        items = [item for item in items if item["connection_key"] not in {"ontology-neo4j", "publish-ontology-neo4j"}]
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
    allowed_kinds = {
        "camstar-source": {"camstar_sqlserver", "camstar_oracle"},
        "ontology-neo4j": {"ontology_neo4j"},
        "publish-ontology-neo4j": {"publish_ontology_neo4j"},
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
