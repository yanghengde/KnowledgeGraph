"""Read-only local ontology inventory. Writes review artifacts, never loads a database."""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    "组织与位置": ["Enterprise", "Site", "Factory", "WorkCenter", "ss_MfgLine", "Organization"],
    "产品与计量": ["Product", "ProductBase", "ProductFamily", "UOM"],
    "人员与职责": ["Employee", "RoleDef", "Team"],
    "设备与资源": ["ResourceDef", "ResourceFamily", "ResourceType"],
    "后续共享对象": ["Vendor", "Customer", "Owner", "Location"],
    "首期业务骨架（不归公共主数据）": ["MfgOrder", "Container", "Workflow", "WorkflowStep", "Spec", "Operation"],
}


def main():
    definitions = defaultdict(list)
    relationships = []
    files = sorted((ROOT / "src/ontology/wiki_kb").glob("*_ontology.json"))
    for path in files:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
        for entry in doc.get("classes", []):
            definitions[entry["className"]].append({"file": path.relative_to(ROOT).as_posix(), "definition": entry})
        relationships.extend(doc.get("relationships", []))
    fields = defaultdict(list)
    with (ROOT / "docs/Database_Fields.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            fields[row["CDOName"]].append(row)
    unique_edges = {(r["fromClass"], r["relationName"], r["toClass"]) for r in relationships}
    incoming = defaultdict(set)
    for source, _, target in unique_edges:
        incoming[target].add(source)
    groups = {name: group for group, names in GROUPS.items() for name in names}
    catalog = []
    for name, entries in sorted(definitions.items()):
        types = defaultdict(lambda: defaultdict(list))
        for entry in entries:
            for prop in entry["definition"].get("properties", []):
                types[prop["name"]][prop.get("type", "String")].append(entry["file"])
        conflicts = {key: dict(value) for key, value in types.items() if len(value) > 1}
        catalog.append({
            "className": name, "chineseNames": sorted({e["definition"].get("chineseName", "") for e in entries}),
            "proposedGroup": groups.get(name, "其他领域／辅助对象，待分类"),
            "sources": [{"file": e["file"], "propertyCount": len(e["definition"].get("properties", []))} for e in entries],
            "canonicalSource": None, "duplicateDefinition": len(entries) > 1,
            "propertyTypeConflicts": conflicts,
            "physicalPrimaryKeys": [r["FieldName"] for r in fields[name] if r.get("IsPrimaryKey") == "True"],
            "incomingClassCount": len(incoming[name]),
            "outgoingRelationships": [{"relation": r, "target": t} for s, r, t in sorted(unique_edges) if s == name],
        })
    summary = {
        "ontologyFiles": len(files), "uniqueClasses": len(catalog),
        "classDefinitions": sum(len(v) for v in definitions.values()),
        "classesWithDuplicateDefinitions": sum(c["duplicateDefinition"] for c in catalog),
        "relationshipDeclarations": len(relationships), "uniqueRelationshipTriples": len(unique_edges),
        "classesWithPropertyTypeConflicts": sum(bool(c["propertyTypeConflicts"]) for c in catalog),
        "conflictingClassProperties": sum(len(c["propertyTypeConflicts"]) for c in catalog),
    }
    output = ROOT / "docs/public_core_inventory.json"
    output.write_text(json.dumps({"scope": "local files only; proposed groups; no canonical source approved", "summary": summary, "classes": catalog}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    by_name = {c["className"]: c for c in catalog}
    lines = ["# Camstar 公共核心本体盘点", "", "本报告从当前项目文件生成；归组是治理建议，不是已经生效的发布配置。未修改模型、数据库或活动发布版本。", "", "## 当前事实", ""]
    lines.extend(f"- {key}: {value}" for key, value in summary.items())
    lines += ["", "重复定义不等于数据库存在重复节点，但同名属性、中文名和模块归属可能在加载时被不同文件覆盖。权威来源必须逐类确认，不能按文件顺序裁决。", "", "## 建议公共核心与首期业务骨架", ""]
    for group, names in GROUPS.items():
        lines += [f"### {group}", "", "| 类 | 中文名 | 属性数（按文件） | 主键候选（物理声明） | 引用它的类数 | 重复/类型冲突 |", "|---|---|---|---|---|---|"]
        for name in names:
            c = by_name[name]
            labels = " / ".join(label for label in c["chineseNames"] if label) or "待补充"
            counts = "/".join(str(s["propertyCount"]) for s in c["sources"])
            lines.append(f"| {name} | {labels} | {counts} | {', '.join(c['physicalPrimaryKeys']) or '待确认'} | {c['incomingClassCount']} | {'重复定义' if c['duplicateDefinition'] else '单一定义'} / {len(c['propertyTypeConflicts'])} |")
        lines.append("")
    lines += ["主键列只是物理候选；实际对象 URI 必须确认复合键、版本和来源实例标识。引用次数仅辅助判断共享程度，不表示业务优先级。", "", "## 跨文件同名属性类型冲突", "", "| 类.属性 | 各类型与来源 |", "|---|---|"]
    for c in catalog:
        for prop, variants in c["propertyTypeConflicts"].items():
            detail = "；".join(f"{t}: {', '.join(Path(f).name for f in sources)}" for t, sources in variants.items())
            lines.append(f"| {c['className']}.{prop} | {detail} |")
    lines += ["", "## 如何最简单地落地", "",
        "1. 全部 593 类留在目录中，先治理 16 个公共核心候选（前四组）；供应商、客户、所有者和位置 4 类后续纳入。订单、批次、工艺 6 类单独作为首期业务骨架。",
        "2. 生成每类一张模型卡：业务定义、权威来源、物理键、常用属性、关系、发布状态。CSV 导入改为已有类的差异审阅候选，而非第二份自动生效定义；该机制本次仅建议，尚未实施。",
        "3. 依据物理 CSV 逐项确认冲突，再合并业务说明与扩展属性。先保护版本标识、外键和关系终点；附加属性不直接删除，应区分业务扩展、计算属性与错误字段。",
        "4. 问数按发布范围提供常用问题：有哪些对象、多少个、某订单对应什么产品。固定查询依据模型生成，仅开放已验证的单跳关系。用户不需要选查询语言或传输方式。",
        "5. 完整本体治理与实例全量导入分开：先统一模型，数据先接一条业务链。未发布、无数据、查询失败三种状态明确区分。复杂分析、权限深化与亿级容量后续推进。",
        "", "## 本项目的具体注意事项", "",
        "- Material、MfgLine、Resource、Role、Supplier 不是当前同名本体类；material 和 mfgline 文件没有类定义。实际候选包括 ss_MfgLine、ResourceDef、RoleDef、Vendor。不要仅凭文件名或中文词新增重复实体。物料概念需结合 Product、BOM及物料类别关系确认，不能直接等同。",
        "- Product.materialCategory 存在 Navigation/String 冲突。物理 Product.MaterialCategoryId 是指向 A_MaterialCategory 的外键，应保留导航语义；物理校验器合并同名属性后检查，因此总类型错误为零不能排除文件间冲突。",
        "- Site 定义包含 password 属性：通用模型字段不应默认进入问数/业务发布属性集，应采用业务属性白名单。此盘点未读取密码值，也未证明该字段已被发布。",
        "- 旧 docs/ontology_csv_validation_report.md 引用 CamstarSemiOntology 目录；本次重新校验结果见 ontology_current_inventory_validation.md。",
        "- 全量可追溯来源、主键候选、出边及冲突见 public_core_inventory.json。canonicalSource 为 null，表示尚未裁决，不表示没有源文件。", ""]
    (ROOT / "docs/public_core_inventory.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
