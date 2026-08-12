"""
Chat Logger — Dify-style structured trace logging
──────────────────────────────────────────────────
Logs each Q&A turn as a JSON trace record with step-by-step
timing breakdown, stored as daily files under CHAT_LOG_DIR.

Output format (one JSON object per line = JSONL for easy append):
  {"trace_id":"...","session_id":"...","timestamp":"...","question":"...",
   "total_elapsed_ms":2345,"steps":[...],"answer":"...","error":null}
"""
import os
import json
import time
import uuid
import threading
from datetime import datetime, timezone
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

CHAT_LOG_ENABLED = os.getenv("CHAT_LOG_ENABLED", "true").lower() == "true"
CHAT_LOG_DIR = os.getenv("CHAT_LOG_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "logs", "chat"))
CHAT_LOG_LEVEL = os.getenv("CHAT_LOG_LEVEL", "info").lower()

_write_lock = threading.Lock()


def _ensure_log_dir():
    os.makedirs(CHAT_LOG_DIR, exist_ok=True)


def _log_file_path(date_str: str = None) -> str:
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _ensure_log_dir()
    return os.path.join(CHAT_LOG_DIR, f"chat-{date_str}.jsonl")


class TraceStep:
    """A single step within a trace."""

    def __init__(self, name: str):
        self.name = name
        self.status = "running"
        self.elapsed_ms = 0.0
        self.input = None
        self.output = None
        self._start = time.perf_counter()

    def done(self, output=None, status: str = "success"):
        self.elapsed_ms = round((time.perf_counter() - self._start) * 1000, 2)
        self.status = status
        if output is not None:
            self.output = output
        return self

    def fail(self, error: str):
        self.elapsed_ms = round((time.perf_counter() - self._start) * 1000, 2)
        self.status = "error"
        self.output = {"error": str(error)}
        return self

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "elapsed_ms": self.elapsed_ms,
            "input": self.input,
            "output": self.output,
        }


class ChatTrace:
    """Tracks a full Q&A turn from question to answer."""

    __slots__ = (
        "trace_id", "session_id", "timestamp", "question",
        "steps", "answer", "error", "total_elapsed_ms", "_start", "_ended",
    )

    def __init__(self, session_id: str, question: str):
        self.trace_id = uuid.uuid4().hex[:16]
        self.session_id = session_id
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.question = question
        self.steps: list[TraceStep] = []
        self.answer = ""
        self.error = None
        self.total_elapsed_ms = 0.0
        self._start = time.perf_counter()
        self._ended = False

    def add_step(self, name: str) -> TraceStep:
        step = TraceStep(name)
        self.steps.append(step)
        return step

    @contextmanager
    def step(self, name: str):
        """Context-manager style step tracking."""
        s = TraceStep(name)
        self.steps.append(s)
        try:
            yield s
            if s.status == "running":
                s.done()
        except Exception as e:
            s.fail(str(e))
            if self.error is None:
                self.error = str(e)
            raise

    def finalize(self, answer: str = "", error: str = None):
        if self._ended:
            return
        self._ended = True
        self.total_elapsed_ms = round((time.perf_counter() - self._start) * 1000, 2)
        self.answer = answer
        if error:
            self.error = error
        self._persist()

    def _persist(self):
        if not CHAT_LOG_ENABLED:
            return
        record = self.to_dict()
        with _write_lock:
            try:
                _ensure_log_dir()
                with open(_log_file_path(), "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"[ChatLog] Failed to write log: {e}")

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "question": self.question,
            "total_elapsed_ms": self.total_elapsed_ms,
            "steps": [s.to_dict() for s in self.steps],
            "answer": self.answer[:2000],  # truncate long answers
            "error": self.error,
        }


# ── Log query helpers (used by API) ──

def list_logs(date_str: str = None, limit: int = 50, offset: int = 0,
               keyword: str = None, session_id: str = None) -> dict:
    """Read logs from disk, newest first. Supports pagination and filtering."""
    if not CHAT_LOG_ENABLED:
        return {"total": 0, "items": []}

    path = _log_file_path(date_str)
    if not os.path.exists(path):
        return {"total": 0, "items": []}

    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Filters
            if session_id and rec.get("session_id") != session_id:
                continue
            if keyword:
                kw = keyword.lower()
                if kw not in rec.get("question", "").lower() and kw not in rec.get("answer", "").lower():
                    continue
            # Summary view (strip heavy answer for list)
            items.append({
                "trace_id": rec.get("trace_id"),
                "session_id": rec.get("session_id"),
                "timestamp": rec.get("timestamp"),
                "question": rec.get("question", "")[:100],
                "total_elapsed_ms": rec.get("total_elapsed_ms"),
                "step_count": len(rec.get("steps", [])),
                "has_error": bool(rec.get("error")),
            })

    total = len(items)
    items = items[::-1]  # newest first
    items = items[offset:offset + limit]

    return {"total": total, "items": items}


def get_log(trace_id: str, date_str: str = None) -> dict | None:
    """Retrieve a single log entry by trace_id."""
    if not CHAT_LOG_ENABLED:
        return None
    path = _log_file_path(date_str)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("trace_id") == trace_id:
                return rec
    return None


def list_available_dates() -> list[str]:
    """Return list of dates that have log files (newest first)."""
    if not CHAT_LOG_ENABLED or not os.path.exists(CHAT_LOG_DIR):
        return []
    dates = []
    for f in os.listdir(CHAT_LOG_DIR):
        if f.startswith("chat-") and f.endswith(".jsonl"):
            dates.append(f[5:-6])  # extract YYYY-MM-DD
    return sorted(dates, reverse=True)


def clear_logs(date_str: str = None) -> int:
    """Delete log files. Returns number of files deleted."""
    if date_str:
        path = _log_file_path(date_str)
        if os.path.exists(path):
            os.remove(path)
            return 1
        return 0
    count = 0
    if os.path.exists(CHAT_LOG_DIR):
        for f in os.listdir(CHAT_LOG_DIR):
            if f.endswith(".jsonl"):
                os.remove(os.path.join(CHAT_LOG_DIR, f))
                count += 1
    return count
