"""Standalone Manufacturing Knowledge Q&A HTTP API."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.qa.graphstudio_assistant import (
    GraphStudioAssistantError,
    graphstudio_connection_status,
    graphstudio_query_stream,
)
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


@router.get("/status")
async def status():
    return graphstudio_connection_status()


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
    history = session.get("messages", [])

    async def generate():
        full_answer = ""
        error_message = None
        try:
            async for chunk in graphstudio_query_stream(question, history):
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
        )
        yield "data: " + json.dumps({
            "type": "done",
            "session_id": saved["id"],
            "session_title": saved["title"],
        }, ensure_ascii=False) + "\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
