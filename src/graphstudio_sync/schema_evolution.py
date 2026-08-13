"""Schema evolution compatibility and impact analysis.

This module only plans changes. Applying DDL, backfills, ontology migrations or
Graph Studio updates belongs to the separately approved migration phase.
"""

from __future__ import annotations

from collections import Counter
import json
import uuid
from typing import Any, Iterable

from sqlalchemy import text

from .repository import ControlPlaneRepository


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


FIELD_COLUMNS = {
    "source_column", "target_field", "data_type", "nullable", "required",
    "field_role", "lifecycle_status", "ordinal_position",
    "introduced_version", "deprecated_version", "transform_expression",
    "default_expression", "ontology_property", "sensitivity", "searchable",
    "sortable", "config",
}


def _merged_field(before: dict[str, Any] | None, after: dict[str, Any] | None, operation: str, target_version: int) -> dict[str, Any] | None:
    value = {key: item for key, item in (before or {}).items() if key in FIELD_COLUMNS}
    after = after or {}
    if operation == "add_field":
        value = {
            "source_column": None, "target_field": "", "data_type": "String",
            "nullable": True, "required": False, "field_role": "attribute",
            "lifecycle_status": "active", "ordinal_position": 100,
            "introduced_version": target_version, "deprecated_version": None,
            "transform_expression": None, "default_expression": None,
            "ontology_property": None, "sensitivity": "internal",
            "searchable": True, "sortable": True, "config": {},
            **{key: item for key, item in after.items() if key in FIELD_COLUMNS},
        }
    elif operation == "deprecate_field":
        value.update({"lifecycle_status": "deprecated", "deprecated_version": target_version})
    elif operation == "retire_field":
        value.update({"lifecycle_status": "retired", "deprecated_version": value.get("deprecated_version") or target_version})
    elif operation == "rename_field":
        value["target_field"] = after["target_field"]
    elif operation == "change_type":
        value["data_type"] = after["data_type"]
    elif operation == "change_required":
        required = bool(after.get("required"))
        value.update({"required": required, "nullable": not required})
        if "default_expression" in after:
            value["default_expression"] = after["default_expression"]
    elif operation == "change_key":
        value["field_role"] = after["field_role"]
    elif operation == "change_source":
        value["source_column"] = after.get("source_column")
    elif operation == "change_transform":
        value["transform_expression"] = after.get("transform_expression")
    else:
        raise ValueError(f"Unsupported schema operation: {operation}")
    return value


def _update_contract_projection(connection, contract_key: str, target_version: int) -> None:
    fields = [dict(row) for row in connection.execute(
        text("SELECT source_column, required, field_role, lifecycle_status FROM graphsync.data_contract_field WHERE contract_key=:key ORDER BY ordinal_position"),
        {"key": contract_key},
    ).mappings()]
    available = [item for item in fields if item["lifecycle_status"] != "retired" and item["source_column"]]
    selected = [item["source_column"] for item in available]
    primary = [item["source_column"] for item in available if item["field_role"] == "primary_key"]
    business = [item["source_column"] for item in available if item["field_role"] == "business_key"]
    required = [item["source_column"] for item in available if item["required"]]
    freshness = next((item["source_column"] for item in available if item["field_role"] == "freshness"), None)
    if not primary:
        raise ValueError("Schema migration cannot remove every primary key field")
    connection.execute(
        text(
            """
            UPDATE graphsync.data_contract
            SET version=:version, selected_columns=CAST(:selected AS jsonb),
                primary_key_columns=CAST(:primary AS jsonb),
                business_key_columns=CAST(:business AS jsonb),
                required_columns=CAST(:required AS jsonb),
                freshness_column=:freshness
            WHERE contract_key=:key
            """
        ),
        {"version": target_version, "selected": json.dumps(selected), "primary": json.dumps(primary), "business": json.dumps(business), "required": json.dumps(required), "freshness": freshness, "key": contract_key},
    )


def apply_schema_change(
    repository: ControlPlaneRepository,
    *,
    change_id: uuid.UUID,
    actor: str | None,
) -> dict[str, Any]:
    run_id = uuid.uuid4()
    with repository.engine.begin() as connection:
        change = connection.execute(
            text("SELECT * FROM graphsync.schema_change_request WHERE change_id=:id FOR UPDATE"),
            {"id": change_id},
        ).mappings().one_or_none()
        if change is None:
            raise KeyError(str(change_id))
        if change["status"] != "approved":
            raise ValueError("Only an approved Schema change can be applied")
        current_version = connection.execute(
            text("SELECT version FROM graphsync.data_contract WHERE contract_key=:key FOR UPDATE"),
            {"key": change["contract_key"]},
        ).scalar_one()
        if int(current_version) != int(change["base_version"]):
            raise ValueError(f"Data contract version changed from v{change['base_version']} to v{current_version}; rebase the request")
        connection.execute(
            text("INSERT INTO graphsync.schema_migration_run (migration_run_id, change_id, status, preview_only, checkpoint) VALUES (:run, :change, 'started', false, CAST(:checkpoint AS jsonb))"),
            {"run": run_id, "change": change_id, "checkpoint": json.dumps({"actor": actor, "baseVersion": change["base_version"]})},
        )
        connection.execute(text("UPDATE graphsync.schema_change_request SET status='applying' WHERE change_id=:id"), {"id": change_id})
        items = [dict(row) for row in connection.execute(
            text("SELECT * FROM graphsync.schema_change_item WHERE change_id=:id ORDER BY sequence_no"),
            {"id": change_id},
        ).mappings()]
        for item in items:
            merged = _merged_field(item["before_state"], item["after_state"], item["operation"], int(change["target_version"]))
            if item["operation"] == "add_field":
                connection.execute(
                    text(
                        """
                        INSERT INTO graphsync.data_contract_field
                            (contract_key, field_key, source_column, target_field,
                             data_type, nullable, required, field_role,
                             lifecycle_status, ordinal_position, introduced_version,
                             deprecated_version, transform_expression,
                             default_expression, ontology_property, sensitivity,
                             searchable, sortable, config)
                        VALUES (:contract_key, :field_key, :source_column, :target_field,
                                :data_type, :nullable, :required, :field_role,
                                :lifecycle_status, :ordinal_position, :introduced_version,
                                :deprecated_version, :transform_expression,
                                :default_expression, :ontology_property, :sensitivity,
                                :searchable, :sortable, CAST(:config AS jsonb))
                        """
                    ),
                    {"contract_key": change["contract_key"], "field_key": item["field_key"], **merged, "config": json.dumps(merged.get("config") or {})},
                )
            else:
                connection.execute(
                    text(
                        """
                        UPDATE graphsync.data_contract_field SET
                            source_column=:source_column, target_field=:target_field,
                            data_type=:data_type, nullable=:nullable,
                            required=:required, field_role=:field_role,
                            lifecycle_status=:lifecycle_status,
                            ordinal_position=:ordinal_position,
                            introduced_version=:introduced_version,
                            deprecated_version=:deprecated_version,
                            transform_expression=:transform_expression,
                            default_expression=:default_expression,
                            ontology_property=:ontology_property,
                            sensitivity=:sensitivity, searchable=:searchable,
                            sortable=:sortable, config=CAST(:config AS jsonb)
                        WHERE contract_key=:contract_key AND field_key=:field_key
                        """
                    ),
                    {"contract_key": change["contract_key"], "field_key": item["field_key"], **merged, "config": json.dumps(merged.get("config") or {})},
                )
            connection.execute(
                text("UPDATE graphsync.asset_dependency SET active=false, last_seen_at=now() WHERE profile_key=:profile AND upstream_type='data_contract_field' AND upstream_key=:field AND downstream_type='curated_column'"),
                {"profile": change["profile_key"], "field": item["field_key"]},
            )
            if merged["lifecycle_status"] != "retired":
                target_table = connection.execute(text("SELECT config->>'targetTable' FROM graphsync.data_contract WHERE contract_key=:key"), {"key": change["contract_key"]}).scalar_one()
                connection.execute(
                    text("INSERT INTO graphsync.asset_dependency (dependency_id, profile_key, upstream_type, upstream_key, downstream_type, downstream_key, dependency_kind, discovered_by, metadata) VALUES (:id, :profile, 'data_contract_field', :field, 'curated_column', :target, 'hard', 'compiler', CAST(:metadata AS jsonb)) ON CONFLICT (profile_key, upstream_type, upstream_key, downstream_type, downstream_key) DO UPDATE SET active=true, last_seen_at=now()"),
                    {"id": uuid.uuid4(), "profile": change["profile_key"], "field": item["field_key"], "target": f"{target_table}.{merged['target_field']}", "metadata": json.dumps({"schemaChangeId": str(change_id)})},
                )
        _update_contract_projection(connection, change["contract_key"], int(change["target_version"]))
        connection.execute(text("UPDATE graphsync.schema_change_request SET status='applied', applied_at=now() WHERE change_id=:id"), {"id": change_id})
        connection.execute(text("UPDATE graphsync.schema_migration_run SET status='succeeded', affected_rows=:rows, verification=CAST(:verification AS jsonb), finished_at=now() WHERE migration_run_id=:run"), {"run": run_id, "rows": len(items), "verification": json.dumps({"contractVersion": change["target_version"], "fieldOperations": len(items), "immutableBackfillPending": True})})
    return {"changeId": str(change_id), "migrationRunId": str(run_id), "status": "applied", "contractVersion": change["target_version"], "fieldOperations": len(items), "nextGate": "materialize_immutable_release"}


def rollback_schema_change(
    repository: ControlPlaneRepository,
    *,
    change_id: uuid.UUID,
    actor: str | None,
) -> dict[str, Any]:
    run_id = uuid.uuid4()
    with repository.engine.begin() as connection:
        change = connection.execute(text("SELECT * FROM graphsync.schema_change_request WHERE change_id=:id FOR UPDATE"), {"id": change_id}).mappings().one_or_none()
        if change is None:
            raise KeyError(str(change_id))
        if change["status"] != "applied":
            raise ValueError("Only an applied Schema change can be rolled back")
        active_use = connection.execute(
            text("SELECT count(*) FROM graphsync.curated_release release JOIN graphsync.curated_release_activation active ON active.active_release_id=release.release_id WHERE release.profile_key=:profile AND (release.contract_versions->>:contract_key)::integer=:version"),
            {"profile": change["profile_key"], "contract_key": change["contract_key"], "version": change["target_version"]},
        ).scalar_one()
        if active_use:
            raise ValueError("Active curated release uses this Schema version; roll back the curated release first")
        items = [dict(row) for row in connection.execute(text("SELECT * FROM graphsync.schema_change_item WHERE change_id=:id ORDER BY sequence_no DESC"), {"id": change_id}).mappings()]
        for item in items:
            if item["operation"] == "add_field":
                connection.execute(text("DELETE FROM graphsync.data_contract_field WHERE contract_key=:contract AND field_key=:field"), {"contract": change["contract_key"], "field": item["field_key"]})
                connection.execute(text("UPDATE graphsync.asset_dependency SET active=false WHERE profile_key=:profile AND upstream_key=:field"), {"profile": change["profile_key"], "field": item["field_key"]})
            else:
                before = {key: value for key, value in (item["before_state"] or {}).items() if key in FIELD_COLUMNS}
                connection.execute(
                    text("UPDATE graphsync.data_contract_field SET source_column=:source_column, target_field=:target_field, data_type=:data_type, nullable=:nullable, required=:required, field_role=:field_role, lifecycle_status=:lifecycle_status, ordinal_position=:ordinal_position, introduced_version=:introduced_version, deprecated_version=:deprecated_version, transform_expression=:transform_expression, default_expression=:default_expression, ontology_property=:ontology_property, sensitivity=:sensitivity, searchable=:searchable, sortable=:sortable, config=CAST(:config AS jsonb) WHERE contract_key=:contract_key AND field_key=:field_key"),
                    {"contract_key": change["contract_key"], "field_key": item["field_key"], **before, "config": json.dumps(before.get("config") or {})},
                )
        _update_contract_projection(connection, change["contract_key"], int(change["base_version"]))
        connection.execute(text("UPDATE graphsync.schema_change_request SET status='rolled_back' WHERE change_id=:id"), {"id": change_id})
        connection.execute(text("INSERT INTO graphsync.schema_migration_run (migration_run_id, change_id, status, preview_only, affected_rows, checkpoint, verification, finished_at) VALUES (:run, :change, 'rolled_back', false, :rows, CAST(:checkpoint AS jsonb), CAST(:verification AS jsonb), now())"), {"run": run_id, "change": change_id, "rows": len(items), "checkpoint": json.dumps({"actor": actor}), "verification": json.dumps({"contractVersion": change["base_version"]})})
    return {"changeId": str(change_id), "migrationRunId": str(run_id), "status": "rolled_back", "contractVersion": change["base_version"]}
