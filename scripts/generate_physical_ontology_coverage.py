#!/usr/bin/env python3
"""Generate a table-by-table physical schema to ontology coverage matrix."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from validate_ontology_vs_csv import DEFAULT_FIELDS, DEFAULT_ONTOLOGY_DIR, DEFAULT_TABLES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "physical_ontology_coverage.csv"
DEFAULT_SUMMARY = PROJECT_ROOT / "docs" / "physical_ontology_coverage_summary.md"
DEFAULT_SCOPE = PROJECT_ROOT / "src" / "ontology" / "sql_learning_scope.json"

RUNTIME_PATTERN = re.compile(
    r"(History|Hist|Runtime|TxnData|TransactionData|Audit|Cache|Log$|"
    r"LogDetail|Summary$|Snapshot|Temp|CurrentStatus|Status$|"
    r"AdHocWIP|^A_WIP|^A_Lot|ScheduleData|ScheduleTraveler|"
    r"PreactorScheduleData|ScanningData|IntegrationError|^A_Job$|"
    r"JobOrder|PartRequestOrder|SPCRuleViolations|AssignedMaintReq|"
    r"OutboundXMLDocStatus)",
    re.IGNORECASE,
)
CHILD_PATTERN = re.compile(
    r"(Detail|Details|Dtl$|Map$|Mapping|Entries|Groups|ListItem|"
    r"MaterialList|Params$|Parameters$|Allowed|DefaultFor|TextVariables|"
    r"Overrides|Prerequisite|Substitute|RI$|FieldItem$|SubscriptionItem$|"
    r"Subscriptions$|HeaderSection$|SMSEntry$|InstructionVariable$|"
    r"RecipeItem$|Item$|SheetEntry$|CollaboratorData$|CustomerData$|"
    r"CheckBoxFieldData$|EventLot$|NCRComments$|StatusReason$|"
    r"LotCarrierPosition$|TargetDeploymentHeader$)",
    re.IGNORECASE,
)
INFRA_PATTERN = re.compile(
    r"^(UI|Query|QueryString|WebPart|Portal|Dictionary|Button|RequestId|"
    r"MessageType|TagData|UserQuery|UIPersonalization)",
    re.IGNORECASE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_owners(ontology_dir: Path) -> dict[str, str]:
    owners: dict[str, str] = {}
    for path in ontology_dir.glob("*_ontology.json"):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        for item in payload.get("classes", []):
            if item.get("className"):
                owners[item["className"]] = path.name
    return owners


def load_exclusions(scope_path: Path) -> set[str]:
    if not scope_path.exists():
        return set()
    payload = json.loads(scope_path.read_text(encoding="utf-8-sig"))
    return {
        class_name
        for category in payload.get("categories", [])
        for class_name in category.get("classes", [])
    }


def classify(
    name: str,
    fields: list[dict[str, str]],
    incoming_count: int,
) -> tuple[str, str]:
    field_names = {field["FieldName"] for field in fields}
    has_name = "Name" in field_names or any(
        value.lower().endswith("name") for value in field_names
    )
    has_frozen = "IsFrozen" in field_names
    has_change_history = any(
        value.lower() == "changehistoryid" for value in field_names
    )
    has_primary_key = any(
        field["IsPrimaryKey"].lower() == "true" for field in fields
    )

    if RUNTIME_PATTERN.search(name):
        return "runtime_or_history", "名称显示为运行、历史、审计、缓存或日志表"
    if CHILD_PATTERN.search(name):
        return "child_or_association", "名称显示为明细、映射、列表或参数子表"
    if INFRA_PATTERN.search(name):
        return "internal_infrastructure", "名称显示为UI、查询、门户或内部基础设施"
    if has_name and has_frozen and (has_change_history or incoming_count > 0):
        return "top_level_candidate", "具备名称、冻结/变更字段并被外键引用"
    if incoming_count >= 2 or re.search(
        r"(Base|Type|Status|Reason|Code|Group|Definition|Def)$",
        name,
        re.IGNORECASE,
    ):
        return "support_candidate", "被多个外键引用或具有Base/类型/状态/代码形态"
    if has_primary_key and len(fields) >= 8:
        return (
            "non_top_level_record",
            "虽有独立主键，但缺少名称、冻结/变更或被引用等顶级建模特征",
        )
    return "internal_or_unclassified", "缺少顶级建模实体的稳定特征"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", type=Path, default=DEFAULT_TABLES)
    parser.add_argument("--fields", type=Path, default=DEFAULT_FIELDS)
    parser.add_argument("--ontology-dir", type=Path, default=DEFAULT_ONTOLOGY_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    args = parser.parse_args()

    tables = read_csv(args.tables)
    fields = read_csv(args.fields)
    owners = load_owners(args.ontology_dir)
    exclusions = load_exclusions(args.scope)
    fields_by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    incoming: Counter[str] = Counter()
    for field in fields:
        fields_by_class[field["CDOName"]].append(field)
        if field["IsForeignKey"].lower() == "true" and field.get("FKTableName"):
            incoming[field["FKTableName"]] += 1

    rows: list[dict[str, str | int]] = []
    classifications: Counter[str] = Counter()
    for table in sorted(tables, key=lambda row: row["CDOName"].lower()):
        name = table["CDOName"]
        table_fields = fields_by_class[name]
        if name in exclusions:
            classification = "excluded_from_sql_learning"
            rationale = "物理表保留，但按SQL学习范围从业务图谱中排除"
            status = "excluded"
        elif name in owners:
            classification = "modeled"
            rationale = "存在与物理CDOName精确同名的本体类"
            status = "modeled"
        else:
            classification, rationale = classify(
                name,
                table_fields,
                incoming[name],
            )
            status = "not_modeled"
        classifications[classification] += 1
        rows.append(
            {
                "CDODefId": table["CDODefId"],
                "CDOName": name,
                "Workspace": table.get("Workspace", ""),
                "OntologyStatus": status,
                "OntologyFile": owners.get(name, ""),
                "Classification": classification,
                "Rationale": rationale,
                "FieldCount": len(table_fields),
                "ForeignKeyCount": sum(
                    field["IsForeignKey"].lower() == "true"
                    and bool(field.get("FKTableName"))
                    for field in table_fields
                ),
                "IncomingForeignKeyCount": incoming[name],
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# 物理表与本体覆盖矩阵汇总",
        "",
        f"- 物理表总数：{len(rows)}",
        f"- 已建本体：{classifications['modeled']}",
        f"- SQL学习范围排除：{classifications['excluded_from_sql_learning']}",
        f"- 其他未建顶级本体：{len(rows) - classifications['modeled'] - classifications['excluded_from_sql_learning']}",
        "",
        "| 规则分类 | 数量 |",
        "|---|---:|",
    ]
    for name, count in sorted(classifications.items()):
        lines.append(f"| {name} | {count} |")
    lines += [
        "",
        "完整逐表清单见 `docs/physical_ontology_coverage.csv`。分类为规则初筛，"
        "高置信顶级和支撑候选已完成审核并生成；SQL学习范围排除项仍完整"
        "保留在物理CSV中，但不进入业务关系图。",
        "",
    ]
    args.summary.write_text("\n".join(lines), encoding="utf-8")
    print(f"tables={len(rows)}")
    for name, count in sorted(classifications.items()):
        print(f"{name}={count}")
    print(f"output={args.output}")
    print(f"summary={args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
