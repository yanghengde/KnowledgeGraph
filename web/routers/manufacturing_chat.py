"""Standalone Manufacturing Knowledge Q&A HTTP API."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.qa.graphstudio_assistant import (
    GraphStudioAssistantError,
    graphstudio_connection_status,
    graphstudio_query_stream,
    resolve_runtime_snapshot,
)
from src.qa.graphstudio_saved_queries import public_query_catalog
from src.qa.manufacturing_session_store import (
    append_exchange,
    create_session,
    delete_session,
    list_sessions,
    load_session,
)


router = APIRouter(prefix="/api/manufacturing-chat", tags=["Manufacturing Knowledge Q&A"])


class SessionCreateRequest(BaseModel):
    title: str = "新建制造问答"


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    session_id: str
    query_mode: str = Field(default="auto", pattern="^(auto|dynamic)$")
    query_uri: str | None = None


@router.get("/status")
async def status(refresh: bool = False):
    return await asyncio.to_thread(
        graphstudio_connection_status, force_refresh=refresh,
    )


@router.get("/queries")
async def queries(refresh: bool = False):
    try:
        runtime_snapshot = await asyncio.to_thread(resolve_runtime_snapshot)
        items = await asyncio.to_thread(
            public_query_catalog,
            force_refresh=refresh,
            runtime_snapshot=runtime_snapshot,
        )
    except GraphStudioAssistantError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items, "count": len(items)}


@router.get("/sessions")
async def sessions(limit: int = 200):
    return {"items": list_sessions(limit=limit)}


@router.post("/sessions")
async def session_create(request: SessionCreateRequest):
    return create_session(request.title)


@router.get("/sessions/{session_id}")
async def session_get(session_id: str):
    try:
        session = load_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if session is None:
        raise HTTPException(status_code=404, detail="Manufacturing chat session not found")
    return session


@router.delete("/sessions/{session_id}")
async def session_delete(session_id: str):
    try:
        deleted = delete_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "deleted" if deleted else "not_found"}


@router.post("/ask")
async def ask(request: AskRequest):
    question = request.question.strip()
    try:
        session = load_session(request.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if session is None:
        raise HTTPException(status_code=404, detail="Manufacturing chat session not found")
    try:
        runtime_snapshot = await asyncio.to_thread(resolve_runtime_snapshot)
    except GraphStudioAssistantError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    previous_runtime = session.get("runtime") or {}
    version_changed = bool(
        previous_runtime
        and previous_runtime.get("cacheKey") != runtime_snapshot.get("cacheKey")
    )
    # Do not let answers grounded in an older deployment influence planning
    # against the new ontology/data contract.
    history = [] if version_changed else session.get("messages", [])

    async def generate():
        full_answer = ""
        error_message = None
        try:
            if version_changed:
                yield "data: " + json.dumps({
                    "type": "status",
                    "content": (
                        f"图谱已更新到本体 R{runtime_snapshot['ontologyReleaseNo']} / "
                        f"数据 R{runtime_snapshot['curatedReleaseNo']}，已切换到最新证据。"
                    ),
                }, ensure_ascii=False) + "\n\n"
            async for chunk in graphstudio_query_stream(
                question,
                history,
                query_mode=request.query_mode,
                query_uri=request.query_uri,
                runtime_snapshot=runtime_snapshot,
            ):
                if isinstance(chunk, dict):
                    payload = chunk
                else:
                    full_answer += str(chunk)
                    payload = {"type": "chunk", "content": str(chunk)}
                yield "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"
        except GraphStudioAssistantError as exc:
            error_message = str(exc)
        except Exception as exc:
            error_message = f"制造知识问答暂时不可用：{exc}"

        if error_message:
            full_answer = f"### 问答未完成\n\n{error_message}"
            yield "data: " + json.dumps(
                {"type": "error", "content": error_message},
                ensure_ascii=False,
            ) + "\n\n"

        saved = append_exchange(
            request.session_id,
            question=question,
            answer=full_answer,
            error=error_message,
            runtime_snapshot=runtime_snapshot,
        )
        yield "data: " + json.dumps({
            "type": "done",
            "session_id": saved["id"],
            "session_title": saved["title"],
            "runtime": runtime_snapshot,
        }, ensure_ascii=False) + "\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
