"""Source design endpoints, separate from ontology approval and publication."""
import copy
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.graphstudio_sync.semantic_mapping import MappingStore, candidate_preview
from src.ontology.authority_store import authority_store

router = APIRouter(prefix="/api/semantic-mapping", tags=["Semantic mapping"])


class SourcesRequest(BaseModel):
    importId: str = Field(min_length=1, max_length=80)
    selected: list[str] = Field(default_factory=list, max_length=5000)


class Design(BaseModel):
    role: Literal["pending", "entity", "event", "relationship", "auxiliary", "excluded"]
    chineseName: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=16000)
    notes: str = Field(default="", max_length=16000)
    fields: dict[str, Literal["pending", "property", "relationship", "internal", "excluded"]] = Field(default_factory=dict)


class SaveRequest(BaseModel):
    revision: int = Field(gt=0)
    design: Design


class SubmitRequest(BaseModel):
    revision: int = Field(gt=0)
    planHash: str = Field(min_length=64, max_length=64)


class RestoreRequest(BaseModel):
    snapshotId: str = Field(min_length=64, max_length=64)
    database: Literal["sqlserver", "oracle"]


class WorkspaceRequest(BaseModel):
    workspaceKey: str = Field(min_length=1, max_length=200)


class ReadyRequest(SubmitRequest, WorkspaceRequest):
    pass


def _store():
    try:
        return MappingStore(authority_store().engine)
    except Exception as exc:
        raise HTTPException(503, "来源建模库暂不可用，请检查 PostgreSQL") from exc


def _run(action):
    try:
        return action()
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/sources")
def add_sources(request: SourcesRequest):
    from web.routers.ontology_import import _import_session, _session_lock
    with _session_lock:
        session = copy.deepcopy(_import_session(request.importId))
    selected = set(request.selected)
    if selected - session["tables"].keys():
        raise HTTPException(422, "请选择当前物理模型中的表")
    return _run(lambda: _store().stage_sources(session, selected))


@router.get("")
def list_drafts():
    return {"items": _store().list()}


@router.get("/physical/versions")
def physical_versions():
    return {"items": _store().snapshots()}


@router.post("/physical/restore")
def restore_physical(request: RestoreRequest):
    import csv
    import io
    from starlette.datastructures import UploadFile
    from web.routers.ontology_import import analyze_import
    payload = _run(lambda: _store().physical(request.snapshotId))
    def upload(name, rows):
        output = io.StringIO()
        columns = list(dict.fromkeys(key for row in rows for key in row))
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return UploadFile(filename=name, file=io.BytesIO(output.getvalue().encode("utf-8")))
    return analyze_import(upload("tables.csv", list(payload["tables"].values())),
                          upload("fields.csv", [r for rows in payload["fields"].values() for r in rows]), request.database, False)


@router.post("/physical/open")
def open_physical():
    from src.graphstudio_sync.config import SyncSettings
    from web.routers.ontology_import import analyze_standard, _import_session
    database = SyncSettings.from_env().source_kind
    database = "oracle" if database == "oracle" else "sqlserver"
    store = _store()
    versions = store.snapshots()
    if versions:
        result = restore_physical(RestoreRequest(snapshotId=versions[0]["snapshotId"], database=database))
        result["snapshotId"] = versions[0]["snapshotId"]
    else:
        result = analyze_standard(database, False)
        result.update(store.stage_sources(_import_session(result["importId"]), set()))
    result["database"] = database
    return result


@router.get("/{draft_id}")
def detail(draft_id: str):
    return _run(lambda: _store().detail(draft_id))


@router.post("/{draft_id}/save")
def save(draft_id: str, request: SaveRequest):
    return _run(lambda: _store().save(draft_id, request.revision, request.design.model_dump()))


@router.post("/{draft_id}/preview")
def preview(draft_id: str):
    return _run(lambda: candidate_preview(_store().detail(draft_id)))


@router.post("/{draft_id}/submit")
def submit(draft_id: str, request: SubmitRequest):
    def apply():
        store = _store()
        with store.engine.begin() as conn:
            current = store.detail(draft_id, conn, lock=True)
            plan = candidate_preview(current)
            if current["revision"] != request.revision or plan["planHash"] != request.planHash:
                raise RuntimeError("来源或设计已变化，请重新预览")
            if plan["blockers"]:
                raise ValueError("；".join(plan["blockers"]))
            # The draft is locked until the immutable candidate is staged.
            return authority_store().stage(plan["payload"])
    return _run(apply)


def _simple(draft_id, request, apply=False):
    from sqlalchemy import text
    from src.graphstudio_sync import ontology_store, simple_modeling
    from web.routers.ontology_authority import _documents
    store = _store()
    authority = authority_store()
    with store.engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(721603051)"))
        draft = store.detail(draft_id, conn, lock=True)
        authorities, proposals = authority.snapshot(conn)
        if apply:
            if request.revision != draft["revision"]:
                raise RuntimeError("内容已修改，请重新检查")
            record = authorities.get(draft["tableName"], {})
            if record.get("decision", {}).get("simplePlanHash") == request.planHash:
                return {"status": "ready", "revision": record["revision"]}
        conn.execute(text("SELECT pg_advisory_xact_lock(721603061)"))
        workspace = ontology_store.workspace(conn, request.workspaceKey, lock=True)
        prepared = simple_modeling.prepare(draft, _documents(), authorities, proposals, workspace, ontology_store.source_payload(None, conn))
        if apply:
            if request.planHash != prepared["planHash"]:
                raise RuntimeError("模型内容已变化，请重新检查")
            result = simple_modeling.commit(conn, authority, workspace, prepared)
        else:
            result = {k: v for k, v in prepared.items() if k not in {"plan", "graph", "source"}}
    if apply:
        from web.routers.graph import invalidate_graph_caches
        invalidate_graph_caches()
    return result


@router.post("/{draft_id}/check")
def check_model(draft_id: str, request: WorkspaceRequest):
    return _run(lambda: _simple(draft_id, request))


@router.post("/{draft_id}/ready")
def ready_model(draft_id: str, request: ReadyRequest):
    return _run(lambda: _simple(draft_id, request, True))
