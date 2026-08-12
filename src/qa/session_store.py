"""Persistent, file-per-conversation storage for the SQL assistant."""

from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSION_DIR = Path(
    os.getenv("CHAT_SESSION_DIR", PROJECT_ROOT / "data" / "chat_sessions")
)
SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{8,80}$")
_lock = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_session_id(session_id: str) -> str:
    if not SESSION_ID_PATTERN.fullmatch(session_id or ""):
        raise ValueError("Invalid chat session id")
    return session_id


def _path(session_id: str) -> Path:
    return SESSION_DIR / f"{_validate_session_id(session_id)}.json"


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temp_path, path)


def create_session(
    *,
    title: str = "新建 SQL 会话",
    assistant_mode: str = "sql",
    product_line: str = "general",
    session_id: str | None = None,
) -> dict[str, Any]:
    session_id = _validate_session_id(session_id) if session_id else uuid.uuid4().hex
    now = _now()
    payload = {
        "version": 1,
        "id": session_id,
        "title": (title or "新建 SQL 会话").strip()[:80],
        "created_at": now,
        "updated_at": now,
        "assistant_mode": assistant_mode,
        "product_line": product_line,
        "context": {
            "selected_classes": [],
            "known_classes": [],
            "pending_sql_plan": None,
        },
        "messages": [],
    }
    with _lock:
        _write_atomic(_path(session_id), payload)
    return payload


def load_session(session_id: str) -> dict[str, Any] | None:
    path = _path(session_id)
    with _lock:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return None
    context = payload.setdefault("context", {})
    context.setdefault("selected_classes", [])
    context.setdefault("known_classes", [])
    context.setdefault("pending_sql_plan", None)
    payload.setdefault("messages", [])
    return payload


def get_or_create_session(
    session_id: str | None,
    *,
    assistant_mode: str,
    product_line: str,
) -> dict[str, Any]:
    if session_id:
        existing = load_session(session_id)
        if existing is not None:
            return existing
    return create_session(
        assistant_mode=assistant_mode,
        product_line=product_line,
        session_id=session_id,
    )


def update_context(
    session_id: str,
    *,
    selected_classes: list[str] | None = None,
    product_line: str | None = None,
) -> dict[str, Any]:
    with _lock:
        payload = load_session(session_id)
        if payload is None:
            raise FileNotFoundError(session_id)
        context = payload.setdefault("context", {})
        accumulated = context.setdefault("selected_classes", [])
        for class_name in selected_classes or []:
            if class_name and class_name not in accumulated:
                accumulated.append(class_name)
        if product_line:
            payload["product_line"] = product_line
        payload["updated_at"] = _now()
        _write_atomic(_path(session_id), payload)
        return payload


def set_known_classes(
    session_id: str,
    known_classes: list[str],
) -> dict[str, Any]:
    """Replace the user-managed known-object list for one conversation."""
    with _lock:
        payload = load_session(session_id)
        if payload is None:
            raise FileNotFoundError(session_id)
        context = payload.setdefault("context", {})
        context.setdefault("selected_classes", [])
        context["known_classes"] = list(dict.fromkeys(
            class_name for class_name in known_classes if class_name
        ))
        payload["updated_at"] = _now()
        _write_atomic(_path(session_id), payload)
        return payload


def set_pending_sql_plan(
    session_id: str,
    plan: dict[str, Any] | None,
) -> dict[str, Any]:
    """Persist or clear the structured plan awaiting user clarification."""
    with _lock:
        payload = load_session(session_id)
        if payload is None:
            raise FileNotFoundError(session_id)
        context = payload.setdefault("context", {})
        context["pending_sql_plan"] = plan
        payload["updated_at"] = _now()
        _write_atomic(_path(session_id), payload)
        return payload


def append_exchange(
    session_id: str,
    *,
    question: str,
    answer: str,
    selected_classes: list[str] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    with _lock:
        payload = load_session(session_id)
        if payload is None:
            raise FileNotFoundError(session_id)
        now = _now()
        payload["messages"].append(
            {
                "role": "user",
                "content": question,
                "timestamp": now,
                "selected_classes": selected_classes or [],
            }
        )
        payload["messages"].append(
            {
                "role": "assistant",
                "content": answer,
                "timestamp": _now(),
                "error": error,
            }
        )
        if len(payload["messages"]) == 2:
            compact_title = " ".join(question.split())
            payload["title"] = compact_title[:36] + (
                "…" if len(compact_title) > 36 else ""
            )
        context = payload.setdefault("context", {})
        accumulated = context.setdefault("selected_classes", [])
        for class_name in selected_classes or []:
            if class_name and class_name not in accumulated:
                accumulated.append(class_name)
        payload["updated_at"] = _now()
        _write_atomic(_path(session_id), payload)
        return payload


def list_sessions(limit: int = 100) -> list[dict[str, Any]]:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    with _lock:
        for path in SESSION_DIR.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            messages = payload.get("messages", [])
            last_message = next(
                (
                    item.get("content", "")
                    for item in reversed(messages)
                    if item.get("content")
                ),
                "",
            )
            items.append(
                {
                    "id": payload.get("id", path.stem),
                    "title": payload.get("title", "未命名会话"),
                    "created_at": payload.get("created_at", ""),
                    "updated_at": payload.get("updated_at", ""),
                    "message_count": len(messages),
                    "selected_classes": payload.get("context", {}).get(
                        "selected_classes", []
                    ),
                    "known_classes": payload.get("context", {}).get(
                        "known_classes", []
                    ),
                    "preview": " ".join(last_message.split())[:100],
                }
            )
    return sorted(
        items,
        key=lambda item: item.get("updated_at", ""),
        reverse=True,
    )[: max(1, min(limit, 500))]


def delete_session(session_id: str) -> bool:
    path = _path(session_id)
    with _lock:
        if not path.exists():
            return False
        path.unlink()
        return True
