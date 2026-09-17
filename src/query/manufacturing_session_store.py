"""Independent persistent conversations for Manufacturing Knowledge Q&A."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSION_DIR = Path(
    os.getenv(
        "MANUFACTURING_CHAT_SESSION_DIR",
        PROJECT_ROOT / "data" / "manufacturing_chat_sessions",
    )
)
SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{8,80}$")
_lock = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_id(session_id: str) -> str:
    if not SESSION_ID_PATTERN.fullmatch(session_id or ""):
        raise ValueError("Invalid manufacturing chat session id")
    return session_id


def _path(session_id: str) -> Path:
    return SESSION_DIR / f"{_validate_id(session_id)}.json"


def _write(payload: dict[str, Any]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    path = _path(payload["id"])
    temporary = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for attempt in range(5):
        try:
            os.replace(temporary, path)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.02 * (attempt + 1))


def create_session(title: str = "新建制造问答") -> dict[str, Any]:
    now = _now()
    payload = {
        "version": 1,
        "id": uuid.uuid4().hex,
        "title": (title or "新建制造问答").strip()[:80],
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }
    with _lock:
        _write(payload)
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
    payload.setdefault("messages", [])
    return payload


def list_sessions(limit: int = 200) -> list[dict[str, Any]]:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    with _lock:
        for path in SESSION_DIR.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            messages = payload.get("messages", [])
            preview = next(
                (str(item.get("content") or "") for item in reversed(messages) if item.get("content")),
                "",
            )
            items.append({
                "id": payload.get("id", path.stem),
                "title": payload.get("title", "制造知识问答"),
                "created_at": payload.get("created_at", ""),
                "updated_at": payload.get("updated_at", ""),
                "message_count": len(messages),
                "preview": " ".join(preview.split())[:100],
            })
    return sorted(items, key=lambda item: item["updated_at"], reverse=True)[: max(1, min(limit, 500))]


def append_exchange(
    session_id: str,
    *,
    question: str,
    answer: str,
    error: str | None = None,
    runtime_snapshot: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with _lock:
        payload = load_session(session_id)
        if payload is None:
            raise FileNotFoundError(session_id)
        payload["messages"].extend([
            {"role": "user", "content": question, "timestamp": _now()},
            {
                "role": "assistant", "content": answer, "timestamp": _now(),
                "error": error, "runtime": runtime_snapshot,
                "metrics": metrics,
            },
        ])
        if runtime_snapshot:
            payload["runtime"] = runtime_snapshot
        if len(payload["messages"]) == 2:
            compact = " ".join(question.split())
            payload["title"] = compact[:36] + ("…" if len(compact) > 36 else "")
        payload["updated_at"] = _now()
        _write(payload)
        return payload


def delete_session(session_id: str) -> bool:
    path = _path(session_id)
    with _lock:
        if not path.exists():
            return False
        path.unlink()
        return True
