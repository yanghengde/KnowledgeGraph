#!/usr/bin/env python3
"""Apply deterministic suite-migration cleanup to ontology JSON arrays."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = (
    PROJECT_ROOT / "src" / "ontology" / "semiconductor_migration_manifest.json"
)
DEFAULT_ONTOLOGY_DIR = PROJECT_ROOT / "src" / "ontology" / "wiki_kb"


def find_array_bounds(text: str, key: str) -> tuple[int, int]:
    marker = f'"{key}"'
    key_pos = text.find(marker)
    if key_pos < 0:
        raise ValueError(f"JSON key not found: {key}")
    start = text.find("[", key_pos + len(marker))
    if start < 0:
        raise ValueError(f"Array not found for key: {key}")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return start, index
    raise ValueError(f"Unterminated array for key: {key}")


def split_top_level_objects(array_text: str) -> list[str]:
    objects: list[str] = []
    depth = 0
    start: int | None = None
    in_string = False
    escaped = False

    for index, char in enumerate(array_text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(array_text[start : index + 1])
                start = None
    if depth != 0:
        raise ValueError("Unbalanced object braces")
    return objects


def filter_array(
    text: str,
    key: str,
    keep: Callable[[dict[str, Any]], bool],
) -> tuple[str, int]:
    start, end = find_array_bounds(text, key)
    raw_objects = split_top_level_objects(text[start + 1 : end])
    retained: list[str] = []
    removed = 0
    for raw_object in raw_objects:
        item = json.loads(raw_object)
        if keep(item):
            retained.append(raw_object)
        else:
            removed += 1

    if not raw_objects or removed == 0:
        return text, 0

    key_line_start = text.rfind("\n", 0, start) + 1
    key_line_prefix = text[key_line_start:start]
    key_indent = key_line_prefix[: len(key_line_prefix) - len(key_line_prefix.lstrip())]
    item_indent = key_indent + "    "
    replacement = "["
    if retained:
        replacement += "\n" + item_indent
        replacement += (",\n" + item_indent).join(retained)
        replacement += "\n" + key_indent
    replacement += "]"
    return text[:start] + replacement + text[end + 1 :], removed


def apply_cleanup(
    ontology_dir: Path,
    obsolete: set[str],
    owners: dict[str, str],
    write: bool,
) -> tuple[int, int, list[str]]:
    removed_classes = 0
    removed_relationships = 0
    changed_files: list[str] = []

    for path in sorted(ontology_dir.glob("*_ontology.json")):
        original = path.read_text(encoding="utf-8-sig")
        updated, class_count = filter_array(
            original,
            "classes",
            lambda item: (
                item.get("className") not in obsolete
                and (
                    item.get("className") not in owners
                    or owners[item["className"]] == path.name
                )
            ),
        )
        updated, relationship_count = filter_array(
            updated,
            "relationships",
            lambda item: (
                item.get("fromClass") not in obsolete
                and item.get("toClass") not in obsolete
            ),
        )

        if class_count or relationship_count:
            json.loads(updated)
            changed_files.append(path.name)
            removed_classes += class_count
            removed_relationships += relationship_count
            if write:
                path.write_text(updated, encoding="utf-8")

    return removed_classes, removed_relationships, changed_files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--ontology-dir", type=Path, default=DEFAULT_ONTOLOGY_DIR)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes. Without this flag the command is a dry run.",
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    obsolete = set(manifest["obsoleteElectronicClasses"])
    obsolete.update(manifest.get("logicalClassReplacements", {}))
    obsolete.update(manifest.get("nonPhysicalLogicalClasses", []))
    owners = manifest["duplicateClassOwners"]
    removed_classes, removed_relationships, changed_files = apply_cleanup(
        args.ontology_dir,
        obsolete,
        owners,
        args.apply,
    )
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"mode={mode}")
    print(f"removed_classes={removed_classes}")
    print(f"removed_relationships={removed_relationships}")
    print(f"changed_files={len(changed_files)}")
    for filename in changed_files:
        print(filename)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
