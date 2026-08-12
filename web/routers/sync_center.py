"""Management API for the Camstar to Graph Studio synchronization center."""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from src.graphstudio_sync.config import SyncSettings
from src.graphstudio_sync.catalog import compile_catalog
from src.graphstudio_sync.connections import test_all_connections, test_connection
from src.graphstudio_sync.curation import build_curation_preview
from src.graphstudio_sync.incremental import execute_incremental_plan, execute_incremental_probe
from src.graphstudio_sync.incremental_preview import build_incremental_preview
from src.graphstudio_sync.graph_profile import plan_context_closure, validate_graph_profile
from src.graphstudio_sync.repository import ControlPlaneRepository
from src.graphstudio_sync.preview import build_full_preview
from src.graphstudio_sync.run_manager import execute_dry_run
from src.graphstudio_sync.schema_evolution import analyze_schema_change


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
        "graph_studio", "state_postgresql",
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


class RelationshipContractUpdate(BaseModel):
    status: Literal["draft", "reviewed", "approved", "retired"] = "draft"
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
