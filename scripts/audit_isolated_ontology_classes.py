#!/usr/bin/env python3
"""Audit isolated ontology classes against physical CSV foreign-key evidence."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = PROJECT_ROOT / "src" / "ontology" / "wiki_kb"
FIELDS_PATH = PROJECT_ROOT / "docs" / "Database_Fields.csv"
REPORT_PATH = PROJECT_ROOT / "docs" / "isolated_ontology_classes_report.md"

INFRASTRUCTURE_SOURCES = {"ModelingInstanceLock"}
INFRASTRUCTURE_TARGETS = {"A_SetupAccess", "ChangeStatus"}


def _load_ontology():
    classes = {}
    relationships = []
    for path in ONTOLOGY_DIR.glob("*_ontology.json"):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        module = payload.get("module") or path.stem.replace("_ontology", "")
        for item in payload.get("classes", []):
            classes[item["className"]] = {
                "module": module,
                "chineseName": item.get("chineseName", ""),
                "file": path.name,
            }
        relationships.extend(payload.get("relationships", []))
    return classes, relationships


def _load_foreign_keys():
    with FIELDS_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        row
        for row in rows
        if row.get("IsForeignKey", "").lower() == "true"
        and row.get("FKTableName")
    ]


def _compact_bridges(bridges):
    values = []
    for table, targets in bridges:
        values.append(f"`{table}` → {', '.join(f'`{item}`' for item in targets)}")
    return "<br>".join(values) or "—"


def main() -> int:
    classes, relationships = _load_ontology()
    modeled = set(classes)
    degree = {name: 0 for name in modeled}
    for relationship in relationships:
        source = relationship.get("fromClass")
        target = relationship.get("toClass")
        if source in degree:
            degree[source] += 1
        if target in degree:
            degree[target] += 1
    isolated = {name for name, value in degree.items() if value == 0}
    connected = modeled - isolated

    foreign_keys = _load_foreign_keys()
    by_source = defaultdict(list)
    inbound = defaultdict(list)
    for row in foreign_keys:
        by_source[row["CDOName"]].append(row)
        inbound[row["FKTableName"]].append(row)

    categories = defaultdict(list)
    for name in sorted(isolated):
        direct = []
        for row in by_source[name]:
            target = row["FKTableName"]
            if target in connected and target not in INFRASTRUCTURE_TARGETS:
                direct.append(
                    f"`{name}.{row['FieldName']}` → `{target}.{row['FKFieldName']}`"
                )
        for row in inbound[name]:
            source = row["CDOName"]
            if source in connected and source not in INFRASTRUCTURE_SOURCES:
                direct.append(
                    f"`{source}.{row['FieldName']}` → `{name}.{row['FKFieldName']}`"
                )

        business_refs = [
            row
            for row in inbound[name]
            if row["CDOName"] not in INFRASTRUCTURE_SOURCES
        ]
        outgoing = [
            row
            for row in by_source[name]
            if row["FKTableName"] not in INFRASTRUCTURE_TARGETS
        ]
        bridge_main = []
        bridge_isolated = []
        for row in business_refs:
            bridge = row["CDOName"]
            if bridge in modeled:
                continue
            targets = {
                item["FKTableName"]
                for item in by_source[bridge]
                if item["FKTableName"] in modeled
                and item["FKTableName"] != name
            }
            main_targets = sorted(targets & connected)
            isolated_targets = sorted(targets & isolated)
            if main_targets:
                bridge_main.append((bridge, main_targets))
            elif isolated_targets:
                bridge_isolated.append((bridge, isolated_targets))

        if direct:
            category = "A0_direct_physical_fk_missing"
            evidence = "<br>".join(sorted(set(direct)))
        elif bridge_main:
            category = "A1_bridge_to_connected_graph"
            evidence = _compact_bridges(sorted(set(
                (table, tuple(targets))
                for table, targets in bridge_main
            )))
        elif bridge_isolated:
            category = "B_bridge_only_isolated"
            evidence = _compact_bridges(sorted(set(
                (table, tuple(targets))
                for table, targets in bridge_isolated
            )))
        elif business_refs or outgoing:
            category = "C_unmodeled_reference_only"
            tables = sorted({
                row["CDOName"] for row in business_refs
            } | {
                row["FKTableName"] for row in outgoing
            })
            evidence = ", ".join(f"`{item}`" for item in tables) or "—"
        else:
            category = "D_no_business_fk_evidence"
            evidence = "物理CSV中仅有基础设施外键，或没有业务外键。"

        categories[category].append({
            "name": name,
            "chineseName": classes[name]["chineseName"],
            "module": classes[name]["module"],
            "file": classes[name]["file"],
            "evidence": evidence,
        })

    lines = [
        "# 本体图谱游离类审计报告",
        "",
        "本报告只依据当前本体 JSON 与 `Database_Fields.csv` 的物理外键事实。",
        "Neo4j 已通过 JSON 一致性校验，因此这里的游离点不是加载失败，而是本体源关系缺失。",
        "",
        "## 汇总",
        "",
        f"- 本体类：{len(modeled)}",
        f"- 本体关系：{len(relationships)}",
        f"- 游离类：{len(isolated)}（{len(isolated) / len(modeled) * 100:.1f}%）",
        "",
        "| 分类 | 数量 | 解释 |",
        "|---|---:|---|",
    ]
    labels = {
        "A0_direct_physical_fk_missing": "存在当前类之间的直接物理FK，但本体未建关系",
        "A1_bridge_to_connected_graph": "经未建模桥接/历史表可连接主图",
        "B_bridge_only_isolated": "桥接表目前只连到其他游离类",
        "C_unmodeled_reference_only": "只有未建模引用表，尚未形成通往主图的事实路径",
        "D_no_business_fk_evidence": "没有可确认的业务外键证据",
    }
    for category in labels:
        lines.append(
            f"| `{category}` | {len(categories[category])} | {labels[category]} |"
        )

    lines += [
        "",
        "## 重点对象",
        "",
        "### IssueReason",
        "",
        f"- 当前状态：{'游离' if 'IssueReason' in isolated else '已连接'}。",
        "- 物理事实：`IssueActualsHistory.IssueReasonId → IssueReason.IssueReasonId`。",
        "- `IssueActualsHistory` 同时关联 `Product`、`Container`、`ResourceDef`、"
        "`Location`、`SubstitutionReason`、`IssueDifferenceReason` 等对象。",
        (
            "- 当前缺口：`IssueActualsHistory` 尚未建成本体类。"
            if "IssueActualsHistory" not in modeled
            else "- 修复路径：已建模 `IssueActualsHistory`，保留真实中间事实表。"
        ),
        "",
        "### ChangeStatusReason",
        "",
        f"- 当前状态：{'游离' if 'ChangeStatusReason' in isolated else '已连接'}。",
        "- 物理事实："
        "`ContainerStatusChangeHistory.ChangeStatusReasonId → "
        "ChangeStatusReason.ChangeStatusReasonId`。",
        "- `ContainerStatusChangeHistory.HistoryMainlineId → "
        "HistoryMainline.HistoryMainlineId`，可继续关联容器事务主线。",
        (
            "- 当前缺口：`ContainerStatusChangeHistory` 尚未建成本体类。"
            if "ContainerStatusChangeHistory" not in modeled
            else "- 修复路径：已建模 `ContainerStatusChangeHistory`，"
            "并连接 `HistoryMainline`。"
        ),
        "",
        "## 分组明细",
        "",
    ]
    for category, label in labels.items():
        items = categories[category]
        lines += [
            f"### {category}",
            "",
            label + "。",
            "",
            "| 类 | 中文名 | 模块 | 物理证据 |",
            "|---|---|---|---|",
        ]
        for item in items:
            lines.append(
                f"| `{item['name']}` | {item['chineseName']} | "
                f"`{item['module']}` | {item['evidence']} |"
            )
        if not items:
            lines.append("| — | — | — | — |")
        lines.append("")

    lines += [
        "## 建议顺序",
        "",
        "1. 若 `A0` 或 `A1` 非零，优先补齐其中有直接FK或明确桥接路径的对象。",
        "2. `C_unmodeled_reference_only` 需要继续建模其引用表，"
        "并确认这些表能否形成通向主图的业务路径。",
        "3. `D_no_business_fk_evidence` 不应为了视觉效果强行连线；"
        "需要 Swagger、业务配置或多态列表定义提供额外证据。",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(
        {
            "classes": len(modeled),
            "relationships": len(relationships),
            "isolated": len(isolated),
            "categories": {
                key: len(categories[key])
                for key in labels
            },
        },
        ensure_ascii=False,
    ))
    print(f"report={REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
