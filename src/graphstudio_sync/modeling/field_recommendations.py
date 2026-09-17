"""Conservative suggestions for drafts, never approvals or physical facts."""

from scripts.validate_ontology_vs_csv import SYSTEM_FIELDS


TECHNICAL_FIELDS = {name.casefold() for name in SYSTEM_FIELDS} | {
    "iconid", "xlocation", "ylocation", "objecttype", "cdotypeid",
}
COMMON_PROPERTIES = {
    "name": "用于识别业务对象", "description": "用于说明业务对象",
    "revision": "用于区分业务版本",
}
# Explicit profiles avoid recommending every status, count or Id column.
OBJECT_PROPERTIES = {
    "WorkflowStep": {
        "Sequence": "用于查看步骤顺序", "StepType": "用于区分步骤类型",
        "IsLastStep": "用于识别末步骤", "Optional": "用于区分可选步骤",
    },
    "Product": {"LotSize": "用于查看批量大小", "IsAvailable": "用于查看可用状态"},
    "Container": {"Qty": "用于查看批次数量", "Status": "用于查看批次状态"},
}
BUSINESS_TARGETS = {
    "Product", "ProductBase", "Container", "MfgOrder", "MfgLot", "Workflow",
    "WorkflowBase", "WorkflowStep", "Spec", "SpecBase", "Operation", "Factory",
    "WorkCenter", "MfgLine", "Resource", "ResourceBase", "UOM", "BOM", "BOMBase",
}
OBJECT_RELATIONSHIPS = {
    "WorkflowStep": {"SubWorkflowId": "Workflow"},
    "Container": {"ParentContainerId": "Container"},
}
SCALAR_TYPES = {"String", "Boolean", "Integer", "Float", "DateTime"}


def recommend_fields(table_name, fields):
    def recommend(field):
        if field["primaryKey"]:
            return {"role": "internal", "autoSelect": True, "reason": "身份主键，由系统保留"}
        physical = field["physicalName"]
        if physical.casefold() in TECHNICAL_FIELDS:
            return {"role": "excluded", "autoSelect": False,
                    "reason": "疑似系统维护或界面字段，默认不选"}
        if field["type"] == "Navigation":
            target = field.get("target")
            direct_link = target in BUSINESS_TARGETS and physical in {
                f"{target}Id", f"{target}DefId", f"{target}RefId",
            }
            if direct_link or (target and OBJECT_RELATIONSHIPS.get(table_name, {}).get(physical) == target):
                return {"role": "relationship", "autoSelect": False,
                        "reason": f"物理外键关联 {target}，按业务需要勾选"}
            return {"role": "pending", "autoSelect": False,
                    "reason": f"关联 {target}，是否需要纳入业务模型待确认" if target else "外键目标不完整，需核实"}
        if physical.casefold().endswith("id"):
            return {"role": "pending", "autoSelect": False,
                    "reason": "未声明可用物理外键，不自动推荐为关联"}
        if field["type"] not in SCALAR_TYPES or field.get("isList"):
            return {"role": "pending", "autoSelect": False,
                    "reason": "复杂字段，确认用途后再选择"}
        reason = COMMON_PROPERTIES.get(field["name"])
        reason = reason or OBJECT_PROPERTIES.get(table_name, {}).get(physical)
        if reason:
            return {"role": "property", "autoSelect": True,
                    "reason": f"{reason}（按字段名称推荐）"}
        return {"role": "pending", "autoSelect": False,
                "reason": "用途尚不明确，需要时再选择"}

    return {field["name"]: recommend(field) for field in fields}


def suggested_fields(design, recommendations):
    """Only fill pending selections; never reset manually excluded fields."""
    fields = dict(design.get("fields", {}))
    if design.get("role") not in {"pending", "entity"}:
        return fields
    for name, recommendation in recommendations.items():
        if fields.get(name, "pending") == "pending" and recommendation["autoSelect"]:
            fields[name] = recommendation["role"]
    return fields
