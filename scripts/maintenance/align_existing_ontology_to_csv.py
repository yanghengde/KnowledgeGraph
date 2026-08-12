#!/usr/bin/env python3
"""Align existing physical ontology classes and relationships to the CSV schema.

The default mode is read-only. Pass --apply to write changes; an automatic
timestamped backup is created first because wiki_kb may be excluded from Git.
Ontology-only logical classes are preserved and are not changed by this tool.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validate_ontology_vs_csv import (
    DEFAULT_FIELDS,
    DEFAULT_ONTOLOGY_DIR,
    DEFAULT_TABLES,
    canonical_physical_fields,
    expected_type,
    is_system_field,
    normalize_field_name,
)


DEFAULT_BACKUP_ROOT = PROJECT_ROOT / "data" / "ontology_backups"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def relation_name(property_name: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", property_name).upper()
    return snake if snake.startswith("HAS_") else f"HAS_{snake}"


def physical_description(field: dict[str, str]) -> str:
    suffix = f" → {field['FKTableName']}" if field.get("FKTableName") else ""
    return f"物理字段 {field['FieldName']}{suffix}"


def load_payloads(ontology_dir: Path) -> dict[Path, dict[str, Any]]:
    payloads: dict[Path, dict[str, Any]] = {}
    for path in sorted(ontology_dir.glob("*_ontology.json")):
        payloads[path] = json.loads(path.read_text(encoding="utf-8-sig"))
    return payloads


def aligned_properties(
    class_item: dict[str, Any],
    fields: list[dict[str, str]],
) -> list[dict[str, Any]]:
    class_name = class_item["className"]
    old_by_name = {
        prop.get("name"): prop
        for prop in class_item.get("properties", [])
        if prop.get("name")
    }
    result: list[dict[str, Any]] = []
    for field in canonical_physical_fields(fields, class_name):
        name = normalize_field_name(field, class_name)
        old = old_by_name.get(name, {})
        prop: dict[str, Any] = {
            "name": name,
            "type": expected_type(field),
            "description": old.get("description") or physical_description(field),
        }
        if old.get("required") is True or name == "name":
            prop["required"] = True
        result.append(prop)
    return result


def align(
    tables_path: Path,
    fields_path: Path,
    ontology_dir: Path,
) -> tuple[dict[Path, dict[str, Any]], dict[str, int]]:
    tables = {row["CDOName"] for row in read_csv(tables_path)}
    fields_by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    for field in read_csv(fields_path):
        fields_by_class[field["CDOName"]].append(field)

    payloads = load_payloads(ontology_dir)
    modeled_classes = {
        item["className"]
        for payload in payloads.values()
        for item in payload.get("classes", [])
        if item.get("className")
    }
    stats = {
        "files_changed": 0,
        "classes_aligned": 0,
        "ontology_only_classes_preserved": 0,
        "properties_before": 0,
        "properties_after": 0,
        "relationships_before": 0,
        "relationships_after": 0,
    }

    for path, payload in payloads.items():
        before = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        physical_classes_in_file: list[str] = []
        for class_item in payload.get("classes", []):
            class_name = class_item.get("className", "")
            if class_name not in tables:
                stats["ontology_only_classes_preserved"] += 1
                continue
            old_props = class_item.get("properties", [])
            new_props = aligned_properties(class_item, fields_by_class[class_name])
            stats["properties_before"] += len(old_props)
            stats["properties_after"] += len(new_props)
            class_item["properties"] = new_props
            physical_classes_in_file.append(class_name)
            stats["classes_aligned"] += 1

        old_relationships = payload.get("relationships", [])
        stats["relationships_before"] += len(old_relationships)
        preserved_logical = [
            rel
            for rel in old_relationships
            if rel.get("fromClass") not in tables
            and rel.get("fromClass") in modeled_classes
            and rel.get("toClass") in modeled_classes
            and rel.get("relationName")
        ]
        generated: list[dict[str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        for class_name in physical_classes_in_file:
            for field in canonical_physical_fields(
                fields_by_class[class_name],
                class_name,
            ):
                target = field.get("FKTableName", "")
                if (
                    field["IsForeignKey"].lower() != "true"
                    or not target
                    or target not in modeled_classes
                ):
                    continue
                prop_name = normalize_field_name(field, class_name)
                name = relation_name(prop_name)
                key = (class_name, target, name)
                if key in seen:
                    continue
                generated.append(
                    {
                        "fromClass": class_name,
                        "toClass": target,
                        "relationName": name,
                        "cardinality": "MANY_TO_ONE",
                        "description": f"{class_name}.{field['FieldName']}",
                    }
                )
                seen.add(key)
        payload["relationships"] = preserved_logical + generated
        stats["relationships_after"] += len(payload["relationships"])
        after = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if before != after:
            stats["files_changed"] += 1

    return payloads, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", type=Path, default=DEFAULT_TABLES)
    parser.add_argument("--fields", type=Path, default=DEFAULT_FIELDS)
    parser.add_argument("--ontology-dir", type=Path, default=DEFAULT_ONTOLOGY_DIR)
    parser.add_argument("--backup-root", type=Path, default=DEFAULT_BACKUP_ROOT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    payloads, stats = align(args.tables, args.fields, args.ontology_dir)
    print(f"mode={'APPLY' if args.apply else 'DRY-RUN'}")
    for key, value in stats.items():
        print(f"{key}={value}")
    if not args.apply:
        return 0

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = args.backup_root / f"pre_csv_alignment_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    for path in payloads:
        shutil.copy2(path, backup_dir / path.name)
    for path, payload in payloads.items():
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"backup={backup_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
