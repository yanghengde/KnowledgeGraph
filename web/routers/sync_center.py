"""Management API for the Camstar to Graph Studio synchronization center."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from src.graphstudio_sync.config import SyncSettings
from src.graphstudio_sync.catalog import compile_catalog
from src.graphstudio_sync.connections import test_all_connections, test_connection
from src.graphstudio_sync.incremental import execute_incremental_plan, execute_incremental_probe
from src.graphstudio_sync.repository import ControlPlaneRepository
from src.graphstudio_sync.preview import build_full_preview
from src.graphstudio_sync.run_manager import execute_dry_run


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
