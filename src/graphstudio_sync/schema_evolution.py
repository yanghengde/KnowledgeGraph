"""Schema evolution compatibility and impact analysis.

This module only plans changes. Applying DDL, backfills, ontology migrations or
Graph Studio updates belongs to the separately approved migration phase.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


COMPATIBILITY_RANK = {"non_breaking": 0, "conditional": 1, "breaking": 2}
VALID_OPERATIONS = {
    "add_field",
    "deprecate_field",
    "retire_field",
    "rename_field",
    "change_type",
    "change_required",
    "change_key",
    "change_source",
    "change_transform",
}


def classify_schema_change(
    operation: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    *,
    dependency_count: int = 0,
) -> dict[str, Any]:
    """Classify one proposed change and derive mandatory migration controls."""

    if operation not in VALID_OPERATIONS:
        raise ValueError(f"Unsupported schema operation: {operation}")
    before = before or {}
    after = after or {}
    compatibility = "non_breaking"
    migration_required = False
    backfill_required = False
    reasons: list[str] = []

    if operation == "add_field":
        required = bool(after.get("required")) or not bool(after.get("nullable", True))
        has_default = bool(after.get("default_expression"))
        if required and not has_default:
            compatibility = "breaking"
            migration_required = True
            backfill_required = True
            reasons.append("新增必填字段没有默认值，历史数据无法直接满足契约")
        elif required:
            compatibility = "conditional"
            migration_required = True
            backfill_required = True
            reasons.append("新增必填字段需要先回填并验证默认值")
        else:
            reasons.append("新增可空字段不改变现有消费者行为")
    elif operation == "deprecate_field":
        compatibility = "conditional" if dependency_count else "non_breaking"
        migration_required = bool(dependency_count)
        reasons.append(
            f"字段仍有 {dependency_count} 个下游依赖，需保留兼容窗口"
            if dependency_count
            else "仅标记废弃，不立即停止写入或删除数据"
        )
    elif operation == "retire_field":
        compatibility = "breaking"
        migration_required = True
        reasons.append("字段退役会停止写入并影响下游Schema")
        if dependency_count:
            reasons.append(f"字段仍有 {dependency_count} 个活动依赖")
    elif operation == "rename_field":
        compatibility = "conditional"
        migration_required = True
        reasons.append("字段稳定ID保持不变，但需要旧名称别名和消费者迁移窗口")
        if dependency_count:
            reasons.append(f"需迁移 {dependency_count} 个下游依赖")
    elif operation == "change_type":
        compatibility = "breaking"
        migration_required = True
        backfill_required = True
        reasons.append(
            f"字段类型从 {before.get('data_type', '未知')} 变为 {after.get('data_type', '未知')}，需要转换和全量验证"
        )
    elif operation == "change_required":
        becoming_required = bool(after.get("required")) and not bool(before.get("required"))
        compatibility = "breaking" if becoming_required else "non_breaking"
        migration_required = becoming_required
        backfill_required = becoming_required
        reasons.append("可空字段变为必填，需要历史回填" if becoming_required else "放宽必填约束")
    elif operation == "change_key":
        compatibility = "breaking"
        migration_required = True
        backfill_required = True
        reasons.append("修改主键或业务键可能改变实例URI、去重和全部关系")
    elif operation == "change_source":
        compatibility = "breaking"
        migration_required = True
        backfill_required = True
        reasons.append("更换物理来源需要重建治理数据并重新验证血缘")
    elif operation == "change_transform":
        compatibility = "conditional"
        migration_required = True
        backfill_required = True
        reasons.append("转换逻辑变化需要重算历史值并进行新旧结果对比")

    return {
        "compatibility": compatibility,
        "migrationRequired": migration_required,
        "backfillRequired": backfill_required,
        "dependencyCount": dependency_count,
        "reasons": reasons,
    }


def analyze_schema_change(
    contract: dict[str, Any],
    fields: Iterable[dict[str, Any]],
    operations: Iterable[dict[str, Any]],
    dependencies: Iterable[dict[str, Any]],
    *,
    migration_strategy: str | None = None,
    rollback_strategy: str | None = None,
) -> dict[str, Any]:
    """Validate a multi-operation request and calculate its release gates."""

    fields_by_key = {field["field_key"]: dict(field) for field in fields}
    dependency_counts = Counter(
        row["upstream_key"] for row in dependencies if row.get("active", True)
    )
    analyzed: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for sequence, item in enumerate(operations, start=1):
        operation = item.get("operation")
        field_key = str(item.get("field_key") or "").strip()
        if not field_key:
            raise ValueError("Every schema change item requires field_key")
        if field_key in seen_keys:
            raise ValueError(f"A change request cannot modify the same field twice: {field_key}")
        seen_keys.add(field_key)
        before = fields_by_key.get(field_key)
        after = dict(item.get("after_state") or {})
        if operation == "add_field":
            if before is not None:
                raise ValueError(f"Field already exists: {field_key}")
            if not after.get("target_field"):
                raise ValueError(f"add_field requires after_state.target_field: {field_key}")
            if not after.get("source_column") and not after.get("transform_expression"):
                raise ValueError(
                    f"add_field requires source_column or transform_expression: {field_key}"
                )
            if any(field["target_field"] == after["target_field"] for field in fields_by_key.values()):
                raise ValueError(f"Target field already exists: {after['target_field']}")
        elif before is None:
            raise ValueError(f"Field does not exist in the current contract: {field_key}")
        dependency_count = dependency_counts[field_key]
        classification = classify_schema_change(
            operation,
            before,
            after,
            dependency_count=dependency_count,
        )
        analyzed.append(
            {
                "sequenceNo": sequence,
                "operation": operation,
                "fieldKey": field_key,
                "beforeState": before,
                "afterState": after or None,
                **classification,
                "notes": item.get("notes"),
            }
        )

    overall = max(
        (item["compatibility"] for item in analyzed),
        key=lambda value: COMPATIBILITY_RANK[value],
        default="non_breaking",
    )
    migration_required = any(item["migrationRequired"] for item in analyzed)
    blockers: list[str] = []
    if not analyzed:
        blockers.append("变更申请至少需要一个字段操作")
    if migration_required and not str(migration_strategy or "").strip():
        blockers.append("条件性或破坏性变更必须填写迁移方案")
    if overall == "breaking" and not str(rollback_strategy or "").strip():
        blockers.append("破坏性变更必须填写回滚方案")
    if any(
        item["operation"] == "retire_field" and item["dependencyCount"] > 0
        for item in analyzed
    ):
        blockers.append("存在活动依赖的字段不能直接退役，应先迁移依赖")

    return {
        "contractKey": contract["contract_key"],
        "baseVersion": int(contract["version"]),
        "targetVersion": int(contract["version"]) + 1,
        "compatibility": overall,
        "migrationRequired": migration_required,
        "backfillRequired": any(item["backfillRequired"] for item in analyzed),
        "dependencyCount": sum(item["dependencyCount"] for item in analyzed),
        "items": analyzed,
        "blockers": blockers,
        "readyForReview": bool(analyzed) and not blockers,
    }
