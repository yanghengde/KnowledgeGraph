#!/usr/bin/env python3
"""Audit ontology classes that do not have an exact physical CDOName.

Candidate physical aliases are ranked using explicit migration hints, common
Camstar suite prefixes, and normalized property overlap. The script is
read-only and produces JSON plus Markdown review artifacts.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from validate_ontology_vs_csv import (
    DEFAULT_FIELDS,
    DEFAULT_ONTOLOGY_DIR,
    DEFAULT_TABLES,
    is_system_field,
    normalize_field_name,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "src" / "ontology" / "semiconductor_migration_manifest.json"
DEFAULT_JSON_REPORT = PROJECT_ROOT / "docs" / "logical_class_audit.json"
DEFAULT_MD_REPORT = PROJECT_ROOT / "docs" / "logical_class_audit.md"
PREFIXES = ("A_", "ss_", "scs", "I_", "CIO", "ES_")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def simplified(value: str) -> str:
    result = value
    for prefix in PREFIXES:
        if result.lower().startswith(prefix.lower()):
            result = result[len(prefix) :]
            break
    return re.sub(r"[^a-z0-9]", "", result.lower())


def load_ontology(ontology_dir: Path) -> tuple[dict[str, dict[str, Any]], set[str]]:
    classes: dict[str, dict[str, Any]] = {}
    modeled: set[str] = set()
    for path in sorted(ontology_dir.glob("*_ontology.json")):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        for item in payload.get("classes", []):
            name = item.get("className")
            if not name:
                continue
            modeled.add(name)
            classes[name] = {
                "sourceFile": path.name,
                "properties": item.get("properties", []),
                "chineseName": item.get("chineseName", ""),
                "description": item.get("description", ""),
            }
    return classes, modeled


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", type=Path, default=DEFAULT_TABLES)
    parser.add_argument("--fields", type=Path, default=DEFAULT_FIELDS)
    parser.add_argument("--ontology-dir", type=Path, default=DEFAULT_ONTOLOGY_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--md-report", type=Path, default=DEFAULT_MD_REPORT)
    args = parser.parse_args()

    table_rows = read_csv(args.tables)
    physical_names = {row["CDOName"] for row in table_rows}
    table_by_name = {row["CDOName"]: row for row in table_rows}
    table_by_id = {
        row["CDODefId"]: row["CDOName"]
        for row in table_rows
        if row.get("CDODefId")
    }
    fields_by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    for field in read_csv(args.fields):
        fields_by_class[field["CDOName"]].append(field)

    ontology, modeled = load_ontology(args.ontology_dir)
    logical_names = sorted(set(ontology) - physical_names)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    manual = manifest.get("physicalRenameCandidates", {})

    simplified_index: dict[str, list[str]] = defaultdict(list)
    for name in physical_names:
        simplified_index[simplified(name)].append(name)

    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = defaultdict(int)
    for logical_name in logical_names:
        old_props = {
            prop.get("name")
            for prop in ontology[logical_name]["properties"]
            if prop.get("name")
        }
        candidate_names = set(manual.get(logical_name, []))
        candidate_names.update(simplified_index.get(simplified(logical_name), []))
        match_methods = {
            name: (
                "explicit"
                if name in manual.get(logical_name, [])
                else "normalized_name"
            )
            for name in candidate_names
        }
        cdo_match = re.search(
            r"CdoId\s*:\s*(\d+)",
            ontology[logical_name].get("description", ""),
            flags=re.IGNORECASE,
        )
        if cdo_match and cdo_match.group(1) in table_by_id:
            name = table_by_id[cdo_match.group(1)]
            candidate_names.add(name)
            match_methods[name] = "cdo_id"
        if not candidate_names:
            inferred: list[tuple[float, str]] = []
            for physical_name in physical_names:
                physical_props = {
                    normalize_field_name(field, physical_name)
                    for field in fields_by_class[physical_name]
                    if not is_system_field(field, physical_name)
                }
                intersection = len(old_props & physical_props)
                if intersection < 2:
                    continue
                union = old_props | physical_props
                prop_overlap = intersection / len(union) if union else 0.0
                name_similarity = difflib.SequenceMatcher(
                    None,
                    simplified(logical_name),
                    simplified(physical_name),
                ).ratio()
                score = 0.7 * prop_overlap + 0.3 * name_similarity
                if score >= 0.45:
                    inferred.append((score, physical_name))
            for _, name in sorted(inferred, reverse=True)[:3]:
                candidate_names.add(name)
                match_methods[name] = "inferred"
        candidate_details: list[dict[str, Any]] = []
        for candidate in sorted(candidate_names):
            if candidate not in physical_names:
                continue
            physical_props = {
                normalize_field_name(field, candidate)
                for field in fields_by_class[candidate]
                if not is_system_field(field, candidate)
            }
            union = old_props | physical_props
            overlap = len(old_props & physical_props) / len(union) if union else 1.0
            candidate_details.append(
                {
                    "className": candidate,
                    "workspace": table_by_name[candidate].get("Workspace", ""),
                    "modeled": candidate in modeled,
                    "propertyOverlap": round(overlap, 3),
                    "explicitHint": candidate in manual.get(logical_name, []),
                    "matchMethod": match_methods[candidate],
                }
            )
        candidate_details.sort(
            key=lambda item: (
                {"cdo_id": 3, "explicit": 2, "normalized_name": 1, "inferred": 0}[
                    item["matchMethod"]
                ],
                item["modeled"],
                item["propertyOverlap"],
            ),
            reverse=True,
        )

        if (
            candidate_details
            and candidate_details[0]["modeled"]
            and candidate_details[0]["matchMethod"] != "inferred"
        ):
            decision = "replace_with_modeled_physical"
        elif candidate_details and candidate_details[0]["matchMethod"] != "inferred":
            decision = "review_physical_candidate"
        elif candidate_details:
            decision = "review_inferred_candidate"
        else:
            decision = "review_logical_abstraction"
        counts[decision] += 1
        rows.append(
            {
                "logicalClass": logical_name,
                "sourceFile": ontology[logical_name]["sourceFile"],
                "chineseName": ontology[logical_name]["chineseName"],
                "decision": decision,
                "candidates": candidate_details,
            }
        )

    payload = {
        "summary": {
            "logicalClasses": len(logical_names),
            **dict(sorted(counts.items())),
        },
        "classes": rows,
    }
    args.json_report.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# 无同名物理表的逻辑类审计",
        "",
        "候选匹配来自迁移清单、Camstar套件常见前缀和属性重叠度。"
        "该报告只提供审核候选，不会自动删除逻辑类。",
        "",
        "## 汇总",
        "",
        "| 分类 | 数量 |",
        "|---|---:|",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        "## 明细",
        "",
        "| 逻辑类 | 来源 | 建议 | 物理候选（Workspace / 已建 / 属性重叠） |",
        "|---|---|---|---|",
    ]
    for row in rows:
        candidates = "<br>".join(
            f"`{item['className']}` ({item['workspace']} / "
            f"{'是' if item['modeled'] else '否'} / {item['propertyOverlap']:.3f} / "
            f"{item['matchMethod']})"
            for item in row["candidates"]
        )
        lines.append(
            f"| `{row['logicalClass']}` | `{row['sourceFile']}` | "
            f"{row['decision']} | {candidates or '—'} |"
        )
    args.md_report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"logical_classes={len(logical_names)}")
    for key, value in sorted(counts.items()):
        print(f"{key}={value}")
    print(f"json_report={args.json_report}")
    print(f"md_report={args.md_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
