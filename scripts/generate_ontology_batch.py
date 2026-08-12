#!/usr/bin/env python3
"""Generate a CSV-backed ontology module from an explicit reviewed batch config."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

try:
    from validate_ontology_vs_csv import (
        DEFAULT_FIELDS,
        DEFAULT_ONTOLOGY_DIR,
        DEFAULT_TABLES,
        canonical_physical_fields,
        expected_type,
        is_system_field,
        normalize_field_name,
    )
except ModuleNotFoundError:
    from scripts.validate_ontology_vs_csv import (
        DEFAULT_FIELDS,
        DEFAULT_ONTOLOGY_DIR,
        DEFAULT_TABLES,
        canonical_physical_fields,
        expected_type,
        is_system_field,
        normalize_field_name,
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def relation_name(property_name: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", property_name).upper()
    if snake.startswith("HAS_"):
        return snake
    return f"HAS_{snake}"


def load_existing_class_names(ontology_dir: Path) -> set[str]:
    result: set[str] = set()
    for path in ontology_dir.glob("*_ontology.json"):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        result.update(
            item["className"]
            for item in payload.get("classes", [])
            if item.get("className")
        )
    return result


def property_description(
    field: dict[str, str],
    property_name: str,
) -> str:
    target = field.get("FKTableName", "")
    if target:
        return f"物理字段 {field['FieldName']} → {target}"
    return f"物理字段 {field['FieldName']}"


def generate(config_path: Path, tables_path: Path, fields_path: Path, ontology_dir: Path) -> tuple[Path, Path]:
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    module = config["module"]
    entries = config["entities"]
    requested_names = [entry["className"] for entry in entries]
    if len(requested_names) != len(set(requested_names)):
        raise ValueError("Batch config contains duplicate className values")

    tables = {row["CDOName"]: row for row in read_csv(tables_path)}
    fields_by_class: dict[str, list[dict[str, str]]] = {}
    for field in read_csv(fields_path):
        fields_by_class.setdefault(field["CDOName"], []).append(field)

    missing = [name for name in requested_names if name not in tables]
    if missing:
        raise ValueError(f"Classes absent from Database_Tables.csv: {missing}")

    existing_classes = load_existing_class_names(ontology_dir)
    batch_classes = set(requested_names)
    relationship_targets = existing_classes | batch_classes
    generated_classes: list[dict[str, Any]] = []
    generated_relationships: list[dict[str, str]] = []
    relationship_keys: set[tuple[str, str, str]] = set()

    for entry in entries:
        class_name = entry["className"]
        table = tables[class_name]
        properties: list[dict[str, Any]] = []
        for field in canonical_physical_fields(fields_by_class[class_name], class_name):
            property_name = normalize_field_name(field, class_name)
            property_type = expected_type(field)
            prop: dict[str, Any] = {
                "name": property_name,
                "type": property_type,
                "description": property_description(field, property_name),
            }
            if property_name == "name":
                prop["required"] = True
            properties.append(prop)

            target = field.get("FKTableName", "")
            if (
                property_type == "Navigation"
                and target
                and target in relationship_targets
            ):
                rel_name = relation_name(property_name)
                key = (class_name, target, rel_name)
                if key not in relationship_keys:
                    generated_relationships.append(
                        {
                            "fromClass": class_name,
                            "toClass": target,
                            "relationName": rel_name,
                            "cardinality": "MANY_TO_ONE",
                            "description": f"{class_name}.{field['FieldName']}",
                        }
                    )
                    relationship_keys.add(key)

        generated_classes.append(
            {
                "className": class_name,
                "chineseName": entry["chineseName"],
                "description": (
                    f"{entry['description']} 物理对应 {class_name} "
                    f"(CdoId: {table['CDODefId']}, Workspace: {table['Workspace']})。"
                ),
                "properties": properties,
            }
        )

    ontology_payload = {
        "module": module,
        "classes": generated_classes,
        "relationships": generated_relationships,
    }
    ontology_path = ontology_dir / f"{module}_ontology.json"
    ontology_path.write_text(
        json.dumps(ontology_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    chinese_lines = [
        f"# {config['titleZh']} / {config['titleEn']}",
        "",
        "## 中文",
        "",
        config["overviewZh"],
        "",
        "本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。"
        "主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；"
        "所有物理外键均映射为 `Navigation`。",
        "",
        "### 实体",
        "",
    ]
    for entry in entries:
        chinese_lines.append(
            f"- `{entry['className']}`（{entry['chineseName']}）：{entry['description']}"
        )
    chinese_lines += [
        "",
        "## English",
        "",
        config["overviewEn"],
        "",
        "The module is generated directly from the semiconductor physical schema. "
        "Infrastructure fields are excluded and every physical foreign key is represented "
        "as a Navigation property.",
        "",
    ]
    modeling_path = ontology_dir / f"{module}_modeling.md"
    modeling_path.write_text("\n".join(chinese_lines), encoding="utf-8")
    return ontology_path, modeling_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--tables", type=Path, default=DEFAULT_TABLES)
    parser.add_argument("--fields", type=Path, default=DEFAULT_FIELDS)
    parser.add_argument("--ontology-dir", type=Path, default=DEFAULT_ONTOLOGY_DIR)
    args = parser.parse_args()
    ontology_path, modeling_path = generate(
        args.config,
        args.tables,
        args.fields,
        args.ontology_dir,
    )
    print(f"ontology={ontology_path}")
    print(f"modeling={modeling_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
