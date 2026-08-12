"""Persistent runtime state for choosing the graph's startup baseline."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GRAPH_STATE_FILE = Path(
    os.getenv("ONTOLOGY_GRAPH_STATE_FILE", str(PROJECT_ROOT / "data" / "ontology_graph_state.json"))
)


def load_graph_state() -> dict[str, Any]:
    if not GRAPH_STATE_FILE.exists():
        return {"version": 1, "baselineMode": "curated"}
    try:
        payload = json.loads(GRAPH_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "baselineMode": "curated"}
    if not isinstance(payload, dict):
        return {"version": 1, "baselineMode": "curated"}
    payload.setdefault("version", 1)
    payload.setdefault("baselineMode", "curated")
    return payload


def save_graph_state(state: dict[str, Any]) -> None:
    GRAPH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = GRAPH_STATE_FILE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(GRAPH_STATE_FILE)


def is_empty_baseline_mode() -> bool:
    return load_graph_state().get("baselineMode") == "empty"


def mark_graph_cleared(*, nodes: int = 0, relationships: int = 0) -> dict[str, Any]:
    state = {
        "version": 1,
        "baselineMode": "empty",
        "clearedAt": int(time.time() * 1000),
        "clearedCounts": {
            "nodes": int(nodes),
            "relationships": int(relationships),
        },
    }
    save_graph_state(state)
    return state


def enable_curated_baseline() -> dict[str, Any]:
    state = {
        "version": 1,
        "baselineMode": "curated",
        "baselineEnabledAt": int(time.time() * 1000),
    }
    save_graph_state(state)
    return state
