#!/usr/bin/env python3
"""Apply the reviewed SQL-learning scope to ontology JSON artifacts.

The command is a dry run by default. With --apply it creates a timestamped
backup and removes excluded classes plus every relationship incident to them.
Properties on surviving classes are intentionally left unchanged.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ONTOLOGY_DIR = PROJECT_ROOT / "src" / "ontology" / "wiki_kb"
DEFAULT_SCOPE = PROJECT_ROOT / "src" / "ontology" / "sql_learning_scope.json"
DEFAULT_BACKUP_ROOT = PROJECT_ROOT / "data" / "ontology_backups"


def load_scope(path: Path) -> tuple[dict[str, Any], set[str]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    excluded = {
        class_name
        for category in payload.get("categories", [])
        for class_name in category.get("classes", [])
    }
    if not excluded:
        raise ValueError(f"No excluded classes found in {path}")
    return payload, excluded


def apply_scope(
    ontology_dir: Path = DEFAULT_ONTOLOGY_DIR,
    scope_path: Path = DEFAULT_SCOPE,
    *,
    write: bool = False,
    backup_root: Path = DEFAULT_BACKUP_ROOT,
) -> dict[str, Any]:
    scope, excluded = load_scope(scope_path)
    files = sorted(ontology_dir.glob("*_ontology.json"))
    before_classes: set[str] = set()
    after_classes: set[str] = set()
    removed_classes: set[str] = set()
    before_properties = 0
    after_properties = 0
    before_relationships = 0
    after_relationships = 0
    changed_payloads: list[tuple[Path, dict[str, Any]]] = []

    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        classes = payload.get("classes", [])
        relationships = payload.get("relationships", [])
        before_classes.update(
            item["className"] for item in classes if item.get("className")
        )
        before_properties += sum(len(item.get("properties", [])) for item in classes)
        before_relationships += len(relationships)

        retained_classes = [
            item for item in classes if item.get("className") not in excluded
        ]
        retained_relationships = [
            item
            for item in relationships
            if item.get("fromClass") not in excluded
            and item.get("toClass") not in excluded
        ]
        removed_classes.update(
            item["className"]
            for item in classes
            if item.get("className") in excluded
        )
        after_classes.update(
            item["className"]
            for item in retained_classes
            if item.get("className")
        )
        after_properties += sum(
            len(item.get("properties", [])) for item in retained_classes
        )
        after_relationships += len(retained_relationships)

        if (
            len(retained_classes) != len(classes)
            or len(retained_relationships) != len(relationships)
        ):
            payload["classes"] = retained_classes
            payload["relationships"] = retained_relationships
            changed_payloads.append((path, payload))

    missing_from_ontology = excluded - before_classes
    backup_dir: Path | None = None
    if write and changed_payloads:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = backup_root / f"pre_sql_learning_scope_{stamp}"
        backup_dir.mkdir(parents=True, exist_ok=False)
        shutil.copy2(scope_path, backup_dir / scope_path.name)
        for path, payload in changed_payloads:
            shutil.copy2(path, backup_dir / path.name)
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    return {
        "profile": scope.get("profile", "sql_learning"),
        "ontology_files": len(files),
        "changed_files": len(changed_payloads),
        "classes_before": len(before_classes),
        "classes_after": len(after_classes),
        "classes_removed": len(removed_classes),
        "properties_before": before_properties,
        "properties_after": after_properties,
        "properties_removed": before_properties - after_properties,
        "relationships_before": before_relationships,
        "relationships_after": after_relationships,
        "relationships_removed": before_relationships - after_relationships,
        "configured_exclusions": len(excluded),
        "missing_from_ontology": sorted(missing_from_ontology),
        "backup_dir": str(backup_dir) if backup_dir else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology-dir", type=Path, default=DEFAULT_ONTOLOGY_DIR)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--backup-root", type=Path, default=DEFAULT_BACKUP_ROOT)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes after creating a timestamped backup.",
    )
    args = parser.parse_args()
    result = apply_scope(
        args.ontology_dir,
        args.scope,
        write=args.apply,
        backup_root=args.backup_root,
    )
    print(f"mode={'apply' if args.apply else 'dry-run'}")
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
