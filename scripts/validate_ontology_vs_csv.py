#!/usr/bin/env python3
"""Validate ontology JSON files against the physical Camstar CSV schema.

The validator is intentionally read-only. It treats Database_Tables.csv and
Database_Fields.csv as the source of truth and writes a Markdown report.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLES = PROJECT_ROOT / "docs" / "Database_Tables.csv"
DEFAULT_FIELDS = PROJECT_ROOT / "docs" / "Database_Fields.csv"
DEFAULT_ONTOLOGY_DIR = PROJECT_ROOT / "src" / "ontology" / "wiki_kb"
DEFAULT_REPORT = PROJECT_ROOT / "docs" / "ontology_csv_validation_report.md"

SYSTEM_FIELDS = {
    "CDOTypeId",
    "ChangeCount",
    "ExportImportKey",
    "InstanceID",
    "InstanceId",
    "LastChangeDate",
    "LastChangeDateGMT",
}

DATA_TYPE_MAP = {
    "-10": "String",
    "-7": "Boolean",
    "-4": "Binary",
    "1": "Integer",
    "3": "Float",
    "4": "Integer",
    "8": "Float",
    "12": "String",
    "93": "DateTime",
}

TYPE_EQUIVALENTS = {
    "Array": {"Array", "SubentityList"},
    "Binary": {"Binary", "String"},
    "DateTime": {"DateTime", "String"},
    "Float": {"Float", "Number", "Decimal"},
    "Integer": {"Integer", "Number"},
    "Navigation": {"Navigation"},
    "String": {"String"},
}


@dataclass(frozen=True)
class ClassDef:
    name: str
    source_file: str
    properties: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class RelationshipDef:
    source: str
    target: str
    name: str
    source_file: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def to_camel_case(value: str) -> str:
    tokens = re.findall(
        r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+",
        value.replace("_", " "),
    )
    if not tokens:
        return value[:1].lower() + value[1:]
    first, *rest = tokens
    return first.lower() + "".join(token[:1].upper() + token[1:].lower() for token in rest)


def normalize_field_name(field: dict[str, str], class_name: str) -> str:
    name = field["FieldName"]
    if field["IsForeignKey"].lower() == "true":
        name = re.sub(r"(DefId|RefId|Id)$", "", name)
    physical_stem = re.sub(r"^(A_|ss_|ES_)", "", class_name, flags=re.IGNORECASE)
    stem_variants = {
        class_name,
        physical_stem,
        re.sub(r"(Base|Def)$", "", physical_stem),
    }
    if name == "Name" or any(name == f"{stem}Name" for stem in stem_variants):
        return "name"
    if any(name == f"{stem}Revision" for stem in stem_variants):
        return "revision"
    return to_camel_case(name)


def expected_type(field: dict[str, str]) -> str:
    if field["IsForeignKey"].lower() == "true" and field.get("FKTableName"):
        return "Navigation"
    if field["IsList"].lower() == "true":
        return "Array"
    return DATA_TYPE_MAP.get(field["DataType"], f"PhysicalType({field['DataType']})")


def canonical_physical_fields(
    fields: list[dict[str, str]],
    class_name: str,
) -> list[dict[str, str]]:
    """Return one authoritative physical row per normalized property.

    Camstar exports can contain inherited duplicate rows. A row with a valid
    foreign-key target wins because physical foreign keys must be Navigation.
    """
    selected: dict[str, dict[str, str]] = {}

    def priority(field: dict[str, str]) -> tuple[bool, bool, bool]:
        is_fk = field["IsForeignKey"].lower() == "true"
        return (
            is_fk and bool(field.get("FKTableName")),
            is_fk,
            field["IsList"].lower() == "true",
        )

    for field in fields:
        if is_system_field(field, class_name):
            continue
        name = normalize_field_name(field, class_name)
        current = selected.get(name)
        if current is None or priority(field) > priority(current):
            selected[name] = field
    return list(selected.values())


def load_ontologies(path: Path) -> tuple[list[ClassDef], list[RelationshipDef], list[str]]:
    classes: list[ClassDef] = []
    relationships: list[RelationshipDef] = []
    parse_errors: list[str] = []

    for json_path in sorted(path.glob("*_ontology.json")):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            parse_errors.append(f"{json_path.name}: {exc}")
            continue

        for item in payload.get("classes", []):
            class_name = item.get("className")
            if not class_name:
                parse_errors.append(f"{json_path.name}: class without className")
                continue
            classes.append(
                ClassDef(
                    name=class_name,
                    source_file=json_path.name,
                    properties=tuple(item.get("properties", [])),
                )
            )

        for item in payload.get("relationships", []):
            relationships.append(
                RelationshipDef(
                    source=item.get("fromClass", ""),
                    target=item.get("toClass", ""),
                    name=item.get("relationName", ""),
                    source_file=json_path.name,
                )
            )

    return classes, relationships, parse_errors


def is_system_field(field: dict[str, str], class_name: str) -> bool:
    return (
        field["FieldName"] in SYSTEM_FIELDS
        or field["IsPrimaryKey"].lower() == "true"
        or field["FieldName"] == f"{class_name}Id"
    )


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["_None._", ""]
    output = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    output.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    output.append("")
    return output


def validate(
    tables_path: Path,
    fields_path: Path,
    ontology_dir: Path,
) -> tuple[str, dict[str, int]]:
    tables = read_csv(tables_path)
    fields = read_csv(fields_path)
    classes, relationships, parse_errors = load_ontologies(ontology_dir)

    table_by_name = {row["CDOName"]: row for row in tables}
    fields_by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    for field in fields:
        fields_by_class[field["CDOName"]].append(field)

    class_defs: dict[str, list[ClassDef]] = defaultdict(list)
    for class_def in classes:
        class_defs[class_def.name].append(class_def)

    unique_class_names = set(class_defs)
    duplicate_classes = {
        name: definitions for name, definitions in class_defs.items() if len(definitions) > 1
    }
    duplicate_properties: list[list[Any]] = []
    for definition in classes:
        property_counts = Counter(
            prop.get("name")
            for prop in definition.properties
            if prop.get("name")
        )
        for property_name, count in sorted(property_counts.items()):
            if count > 1:
                duplicate_properties.append(
                    [definition.name, property_name, count, definition.source_file]
                )
    ontology_only_classes = sorted(unique_class_names - set(table_by_name))
    physical_only_classes = sorted(set(table_by_name) - unique_class_names)

    relationship_keys = {
        (relationship.source, relationship.target) for relationship in relationships
    }
    relationship_triples = Counter(
        (relationship.source, relationship.target, relationship.name)
        for relationship in relationships
    )
    duplicate_relationships = {
        key: count
        for key, count in relationship_triples.items()
        if count > 1
    }
    invalid_relationships = [
        relationship
        for relationship in relationships
        if relationship.source not in unique_class_names
        or relationship.target not in unique_class_names
        or not relationship.source
        or not relationship.target
        or not relationship.name
    ]

    missing_properties: list[list[Any]] = []
    ontology_only_properties: list[list[Any]] = []
    type_mismatches: list[list[Any]] = []
    missing_relationships: list[list[Any]] = []
    module_stats: dict[str, Counter[str]] = defaultdict(Counter)

    for class_name in sorted(unique_class_names & set(table_by_name)):
        physical_fields = fields_by_class[class_name]
        definitions = class_defs[class_name]
        ontology_properties: dict[str, dict[str, Any]] = {}
        property_sources: dict[str, str] = {}
        for definition in definitions:
            for prop in definition.properties:
                prop_name = prop.get("name")
                if prop_name:
                    ontology_properties[prop_name] = prop
                    property_sources[prop_name] = definition.source_file

        normalized_physical = {
            normalize_field_name(field, class_name): field
            for field in canonical_physical_fields(physical_fields, class_name)
        }

        owning_files = sorted({definition.source_file for definition in definitions})
        module_label = ", ".join(owning_files)

        for property_name, field in sorted(normalized_physical.items()):
            expected = expected_type(field)
            if property_name not in ontology_properties:
                missing_properties.append(
                    [
                        class_name,
                        property_name,
                        field["FieldName"],
                        expected,
                        field.get("FKTableName", ""),
                        module_label,
                    ]
                )
                module_stats[module_label]["missing_properties"] += 1
                continue
            actual = ontology_properties[property_name].get("type", "String")
            allowed = TYPE_EQUIVALENTS.get(expected, {expected})
            if actual not in allowed:
                type_mismatches.append(
                    [
                        class_name,
                        property_name,
                        field["FieldName"],
                        expected,
                        actual,
                        property_sources[property_name],
                    ]
                )
                module_stats[module_label]["type_mismatches"] += 1

        for property_name, prop in sorted(ontology_properties.items()):
            if property_name not in normalized_physical:
                ontology_only_properties.append(
                    [
                        class_name,
                        property_name,
                        prop.get("type", "String"),
                        property_sources[property_name],
                    ]
                )
                module_stats[module_label]["ontology_only_properties"] += 1

        for field in canonical_physical_fields(physical_fields, class_name):
            if (
                field["IsForeignKey"].lower() != "true"
                or not field.get("FKTableName")
                or field["FKTableName"] not in unique_class_names
            ):
                continue
            key = (class_name, field["FKTableName"])
            if key not in relationship_keys:
                missing_relationships.append(
                    [
                        class_name,
                        field["FKTableName"],
                        field["FieldName"],
                        normalize_field_name(field, class_name),
                        module_label,
                    ]
                )
                module_stats[module_label]["missing_relationships"] += 1

    summary = {
        "physical_tables": len(table_by_name),
        "physical_fields": len(fields),
        "ontology_files": len(list(ontology_dir.glob("*_ontology.json"))),
        "ontology_classes": len(unique_class_names),
        "ontology_relationships": len(relationships),
        "duplicate_relationships": len(duplicate_relationships),
        "duplicate_properties": len(duplicate_properties),
        "exact_class_matches": len(unique_class_names & set(table_by_name)),
        "duplicate_classes": len(duplicate_classes),
        "ontology_only_classes": len(ontology_only_classes),
        "physical_only_classes": len(physical_only_classes),
        "missing_properties": len(missing_properties),
        "ontology_only_properties": len(ontology_only_properties),
        "type_mismatches": len(type_mismatches),
        "missing_relationships": len(missing_relationships),
        "invalid_relationships": len(invalid_relationships),
        "parse_errors": len(parse_errors),
    }

    lines = [
        "# Ontology vs Semiconductor CSV Validation Report",
        "",
        f"- Tables source: `{tables_path}`",
        f"- Fields source: `{fields_path}`",
        f"- Ontology directory: `{ontology_dir}`",
        "",
        "## Summary",
        "",
    ]
    lines += markdown_table(
        ["Metric", "Count"],
        [[key.replace("_", " ").title(), value] for key, value in summary.items()],
    )

    lines += ["## Duplicate Class Definitions", ""]
    lines += markdown_table(
        ["Class", "Files"],
        [
            [name, "<br>".join(definition.source_file for definition in definitions)]
            for name, definitions in sorted(duplicate_classes.items())
        ],
    )

    lines += ["## Duplicate Property Definitions", ""]
    lines += markdown_table(
        ["Class", "Property", "Count", "File"],
        duplicate_properties,
    )

    lines += ["## Ontology Classes Without a Physical Semiconductor Table", ""]
    lines += markdown_table(["Class"], [[name] for name in ontology_only_classes])

    lines += ["## Invalid Relationship Endpoints", ""]
    lines += markdown_table(
        ["From", "Relation", "To", "File"],
        [
            [item.source, item.name, item.target, item.source_file]
            for item in invalid_relationships
        ],
    )

    lines += ["## Duplicate Relationship Definitions", ""]
    lines += markdown_table(
        ["From", "Relation", "To", "Count"],
        [
            [source, relation, target, count]
            for (source, target, relation), count
            in sorted(duplicate_relationships.items())
        ],
    )

    lines += ["## Missing Physical Properties", ""]
    lines += markdown_table(
        ["Class", "Ontology Property", "Physical Field", "Expected Type", "FK Target", "File"],
        missing_properties,
    )

    lines += ["## Property Type Mismatches", ""]
    lines += markdown_table(
        ["Class", "Property", "Physical Field", "Expected", "Actual", "File"],
        type_mismatches,
    )

    lines += ["## Ontology Properties Without a Physical Field", ""]
    lines += markdown_table(
        ["Class", "Property", "Type", "File"],
        ontology_only_properties,
    )

    lines += ["## Missing Relationships for Physical Foreign Keys", ""]
    lines += markdown_table(
        ["From", "To", "Physical Field", "Navigation Property", "File"],
        missing_relationships,
    )

    lines += ["## Module-Level Warning Counts", ""]
    module_rows = []
    for module_name, counts in sorted(module_stats.items()):
        module_rows.append(
            [
                module_name,
                counts["missing_properties"],
                counts["type_mismatches"],
                counts["ontology_only_properties"],
                counts["missing_relationships"],
            ]
        )
    lines += markdown_table(
        [
            "Ontology File(s)",
            "Missing Properties",
            "Type Mismatches",
            "Ontology-only Properties",
            "Missing Relationships",
        ],
        module_rows,
    )

    lines += ["## Parse Errors", ""]
    lines += markdown_table(["Error"], [[error] for error in parse_errors])

    return "\n".join(lines), summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ontology JSON files against Camstar physical CSV schema."
    )
    parser.add_argument("--tables", type=Path, default=DEFAULT_TABLES)
    parser.add_argument("--fields", type=Path, default=DEFAULT_FIELDS)
    parser.add_argument("--ontology-dir", type=Path, default=DEFAULT_ONTOLOGY_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when alignment warnings are present.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report, summary = validate(args.tables, args.fields, args.ontology_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")

    print(f"Validation report: {args.report}")
    for key, value in summary.items():
        print(f"{key}={value}")

    warning_keys = (
        "duplicate_classes",
        "duplicate_relationships",
        "duplicate_properties",
        "ontology_only_classes",
        "missing_properties",
        "type_mismatches",
        "missing_relationships",
        "invalid_relationships",
        "parse_errors",
    )
    has_warnings = any(summary[key] for key in warning_keys)
    return 1 if args.strict and has_warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
