"""Shared row conversion and immutable physical-key catalog."""

from __future__ import annotations

import csv
from functools import lru_cache
from typing import Any


from src.graphstudio_sync.config import PROJECT_ROOT


PLAN_FILE = PROJECT_ROOT / "outputs" / "graphstudio" / "full_sync_plan.json"


def _rows(result) -> list[dict[str, Any]]:
    return [dict(row) for row in result.mappings().all()]


@lru_cache(maxsize=1)
def _physical_key_catalog() -> dict[str, dict[str, list[str]]]:
    """Read the immutable Camstar physical-field fact source for key metadata."""
    result: dict[str, dict[str, list[str]]] = {}
    with (PROJECT_ROOT / "docs" / "Database_Fields.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            class_name = row.get("CDOName") or ""
            field_name = row.get("FieldName") or ""
            if not class_name or not field_name:
                continue
            keys = result.setdefault(class_name, {"primary": [], "business": []})
            if row.get("IsPrimaryKey") == "True":
                keys["primary"].append(field_name)
            if row.get("IsCandidateKey") == "True":
                keys["business"].append(field_name)
    return result


