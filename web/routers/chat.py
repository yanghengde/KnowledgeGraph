import os
import json
from typing import Literal
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from web.shared import _get_vector_collection, PROJECT_ROOT
from src.qa.session_store import (
    append_exchange,
    create_session,
    delete_session,
    get_or_create_session,
    list_sessions,
    load_session,
    set_known_classes,
    set_pending_sql_plan,
    update_context,
)

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None
    product_line: str = "general"
    history: list[dict] | None = None
    assistant_mode: str = "sql"
    selected_classes: list[str] | None = None
    sql_dialect: Literal["oracle", "sqlserver"] = "oracle"


class ClearRequest(BaseModel):
    session_id: str


class SessionCreateRequest(BaseModel):
    title: str = "新建 SQL 会话"
    assistant_mode: str = "sql"
    product_line: str = "general"


class SessionContextUpdateRequest(BaseModel):
    known_classes: list[str] = Field(default_factory=list)


@router.post("/api/chat/sessions")
async def chat_session_create(req: SessionCreateRequest):
    return create_session(
        title=req.title,
        assistant_mode=req.assistant_mode,
        product_line=req.product_line,
    )


@router.get("/api/chat/sessions")
async def chat_session_list(limit: int = 100):
    return {"items": list_sessions(limit=limit)}


@router.get("/api/chat/sessions/{session_id}")
async def chat_session_get(session_id: str):
    try:
        session = load_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.put("/api/chat/sessions/{session_id}/context")
async def chat_session_context_update(
    session_id: str,
    req: SessionContextUpdateRequest,
):
    from src.qa.engine import _get_class_names

    known_class_names = set(_get_class_names())
    normalized = list(dict.fromkeys(
        class_name.strip()
        for class_name in req.known_classes
        if class_name and class_name.strip()
    ))
    if len(normalized) > 8:
        raise HTTPException(status_code=400, detail="最多可添加 8 个已知对象")
    invalid = [name for name in normalized if name not in known_class_names]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"未知本体对象: {', '.join(invalid)}",
        )
    try:
        return set_known_classes(session_id, normalized)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Chat session not found") from exc


@router.delete("/api/chat/sessions/{session_id}")
async def chat_session_delete(session_id: str):
    try:
        deleted = delete_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "deleted" if deleted else "not_found"}


@router.post("/api/chat")
async def chat(req: ChatRequest):
    question = req.question.strip()

    if not question:
        return JSONResponse(status_code=400, content={"error": "question is required"})

    try:
        session = get_or_create_session(
            req.session_id,
            assistant_mode=req.assistant_mode,
            product_line=req.product_line,
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    session_id = session["id"]
    history = session.get("messages", [])

    # SQL generation relies on the authoritative physical CSV schema and
    # ontology joins. Skip ChromaDB to reduce latency and avoid irrelevant
    # modeling prose influencing table/column selection.
    vec_col = None if req.assistant_mode == "sql" else _get_vector_collection()

    from src.qa.logger import ChatTrace, CHAT_LOG_ENABLED
    trace = ChatTrace(session_id, question) if CHAT_LOG_ENABLED else None

    async def generate():
        from src.qa.engine import query_stream, extract_keywords, extract_class_links
        from src.qa.graph_retriever import search_graph, find_path_highlight
        from src.qa.sql_entity_resolver import recent_selected_classes
        from src.qa.sql_query_planner import (
            build_sql_query_plan,
            format_query_plan_markdown,
        )

        # 1. Extract keywords from the current question and the persisted
        # conversation context. Referenced tables accumulate across turns.
        known_classes = list(
            session.get("context", {}).get("known_classes", [])
        )
        selected_classes = req.selected_classes or []
        question_classes = extract_keywords(question, fallback=False)
        keywords = list(
            dict.fromkeys(
                question_classes
                + known_classes
                + selected_classes
            )
        )

        # Only fall back to recent history when the current request and the
        # user-managed context provide no objects. This keeps a removed known
        # object from silently becoming active again on the next unrelated
        # question, while still supporting pronoun-style follow-ups.
        history_classes = recent_selected_classes(history) if not keywords else []

        # Combine, keeping current keywords first
        all_classes = list(dict.fromkeys(keywords + history_classes))

        query_plan = None
        if req.assistant_mode == "sql":
            query_plan = build_sql_query_plan(
                question,
                all_classes,
                req.sql_dialect,
                session.get("context", {}).get("pending_sql_plan"),
            )
            if query_plan.metric_id:
                from src.qa.semantic.metric_catalog import get_metric
                metric_contract = get_metric(query_plan.metric_id)
                metric_tables = [
                    item["table"]
                    for item in (metric_contract or {}).get("tables", [])
                ]
                query_plan.entities = list(dict.fromkeys(metric_tables))
            # A clarification answer inherits the original request's objects,
            # even if the answer itself only says "本地交易时间".
            if query_plan.metric_id:
                all_classes = list(query_plan.entities)
            else:
                all_classes = list(dict.fromkeys(
                    query_plan.entities + all_classes
                ))
        update_context(
            session_id,
            selected_classes=all_classes,
            product_line=req.product_line,
        )

        # 3. Detect if the user is asking about relations (supports Chinese & English)
        is_rel_query = any(k in question.lower() for k in [
            "关系", "关联", "联系", "链路", "流转", "到", "连接", "沟通", "通路", "最短路径",
            "relationship", "relation", "connect", "link", "path", "flow", "between"
        ])

        highlight_data = None
        if len(all_classes) >= 2:
            # Always query relationship paths when multiple classes are active to connect them in multi-turn Q&A
            highlight_data = find_path_highlight(all_classes)
        elif len(all_classes) == 1:
            highlight_data = {"nodes": all_classes, "edges": []}

        full_answer = ""
        error_msg = None
        if query_plan and query_plan.needs_clarification:
            set_pending_sql_plan(session_id, query_plan.to_dict())
            full_answer = format_query_plan_markdown(query_plan)
            if trace:
                trace.finalize(answer=full_answer)
            saved_session = append_exchange(
                session_id,
                question=question,
                answer=full_answer,
                selected_classes=all_classes,
            )
            yield (
                "data: "
                + json.dumps(
                    {"type": "chunk", "content": full_answer},
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "done",
                        "session_id": session_id,
                        "session_title": saved_session.get("title"),
                        "session_context": saved_session.get("context", {}),
                        "keywords": keywords,
                        "class_links": [],
                        "highlight": highlight_data,
                        "trace_id": trace.trace_id if trace else None,
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            return
        if query_plan:
            set_pending_sql_plan(session_id, None)

        try:
            async for chunk in query_stream(
                question,
                history,
                vec_col,
                trace=trace,
                product_line=req.product_line,
                assistant_mode=req.assistant_mode,
                selected_classes=all_classes,
                known_classes=known_classes,
                sql_dialect=req.sql_dialect,
                query_plan=query_plan.to_dict() if query_plan else None,
            ):
                if isinstance(chunk, dict) and chunk.get("type") == "status":
                    yield f"data: {json.dumps({'type': 'status', 'content': chunk['content']}, ensure_ascii=False)}\n\n"
                else:
                    full_answer += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_msg = str(e)
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"

        if trace:
            trace.finalize(answer=full_answer, error=error_msg)

        saved_session = append_exchange(
            session_id,
            question=question,
            answer=full_answer,
            selected_classes=all_classes,
            error=error_msg,
        )

        class_links = extract_class_links(full_answer)

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'session_title': saved_session.get('title'), 'session_context': saved_session.get('context', {}), 'keywords': keywords, 'class_links': class_links, 'highlight': highlight_data, 'trace_id': trace.trace_id if trace else None}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/chat/clear")
async def chat_clear(req: ClearRequest):
    try:
        deleted = delete_session(req.session_id)
    except ValueError:
        deleted = False
    return {"status": "cleared", "deleted": deleted}


@router.get("/logs")
def logs_page():
    return FileResponse(os.path.join(PROJECT_ROOT, "web", "static", "logs.html"))


@router.get("/api/logs/dates")
def log_dates():
    from src.qa.logger import list_available_dates
    return {"dates": list_available_dates(), "enabled": True}


@router.get("/api/logs")
def api_list_logs(date: str = None, limit: int = 50, offset: int = 0,
                  keyword: str = None, session_id: str = None):
    from src.qa.logger import list_logs
    result = list_logs(
        date_str=date,
        limit=limit,
        offset=offset,
        keyword=keyword,
        session_id=session_id,
    )
    return result


@router.get("/api/logs/{trace_id}")
def api_get_log(trace_id: str, date: str = None):
    from src.qa.logger import get_log
    rec = get_log(trace_id, date_str=date)
    if rec is None:
        return JSONResponse(status_code=404, content={"error": "Log not found"})
    return rec
