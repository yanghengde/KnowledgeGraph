"""Preview and atomically configure newly added ontology objects for data sync."""
from contextlib import nullcontext
from copy import copy
import json

from sqlalchemy import text

from .ontology_store import digest
from .repository import _physical_key_catalog


class _TransactionEngine:
    """Reuse repository operations without committing part of a configuration."""
    def __init__(self, connection):
        self.connection = connection

    def connect(self):
        return nullcontext(self.connection)

    def begin(self):
        return nullcontext(self.connection)


def configuration_preview(repository, profile_key, class_name):
    with repository.engine.connect() as conn:
        active = conn.execute(text("""
            SELECT activation.active_release_id, document.graph, document.document_hash
            FROM graphsync.ontology_release_activation activation
            JOIN graphsync.ontology_release_document document
              ON document.ontology_release_id=activation.active_release_id
            WHERE activation.profile_key=:profile
        """), {"profile": profile_key}).mappings().one_or_none()
        if not active or digest(active["graph"]) != active["document_hash"]:
            raise ValueError("活动本体不存在或内容校验失败")
        node = next((item["class"] for item in active["graph"]["classes"]
                     if item["class"].get("sourceClass") == class_name), None)
        if node is None:
            raise ValueError("对象不在当前活动本体中，请刷新页面")
        mapping = conn.execute(text("SELECT * FROM graphsync.current_class_mapping WHERE class_name=:name"), {"name": class_name}).mappings().one_or_none()
        fields = [dict(row) for row in conn.execute(text("""
            SELECT property_name, physical_column, data_type, required
            FROM graphsync.current_property_mapping WHERE class_name=:name
              AND physical_column IS NOT NULL AND mapping_status IN ('resolved','override')
            ORDER BY property_name
        """), {"name": class_name}).mappings()]
        relation_mappings = [dict(row) for row in conn.execute(text("""
            SELECT source_class, relationship_name, target_class, physical_column, mapping_status
            FROM graphsync.current_relationship_mapping
            WHERE source_class=:name OR target_class=:name
        """), {"name": class_name}).mappings()]
    profile = repository.graph_profile(profile_key)
    with repository.engine.connect() as conn:
        policy = conn.execute(text("SELECT * FROM graphsync.table_sync_policy WHERE job_name=:job AND class_name=:name"),
                              {"job": profile["profile"]["job_name"], "name": class_name}).mappings().one_or_none()
    governance = repository.governance_profile(profile_key)
    configured = next((c for c in profile["classes"] if c["class_name"] == class_name), None)
    contracts = {c["class_name"]: c for c in governance["contracts"]}
    keys = _physical_key_catalog().get(class_name, {"primary": [], "business": []})
    by_column = {f["physical_column"]: f for f in fields}
    for column in [*keys["primary"], *keys["business"]]:
        by_column.setdefault(column, {"physical_column": column, "property_name": column,
                                     "data_type": "String", "required": column in keys["primary"]})
    blockers = []
    if policy and (policy["strategy"] != "snapshot" or not policy["enabled"]):
        blockers.append("该对象已有其他采集策略，需在原策略中调整，本入口不覆盖")
    if not mapping or mapping["mapping_status"] != "resolved" or not mapping["physical_table"]:
        blockers.append("尚无已解析的源表映射，请先刷新数据源目录与字段映射")
    if not keys["primary"]:
        blockers.append("CSV 中未找到主键，需先核实物理主键")
    if mapping and int(mapping.get("approximate_rows") or 0) >= 5_000_000:
        blockers.append("源表达到大表阈值，需要专门配置增量采集，不能使用小表快照")
    # This wizard handles new objects; existing contracts must not be overwritten.
    if class_name in contracts:
        blockers.append("该对象已有数据契约，本入口不覆盖已有契约")
    relations = []
    for edge in active["graph"]["relationships"]:
        source, target = edge["source"].get("sourceClass"), edge["target"].get("sourceClass")
        name = edge["relation"]["targetName"]
        if class_name not in (source, target) or not source or not target:
            continue
        identity = (source, name, target)
        if any((r["source_class"], r["relationship_name"], r["target_class"]) == identity
               and r["status"] != "retired" for r in governance["relationships"]):
            continue
        mapped = next((r for r in relation_mappings if (r["source_class"], r["relationship_name"], r["target_class"]) == identity), None)
        column = mapped.get("physical_column") if mapped else None
        target_keys = keys["primary"] if target == class_name else (contracts.get(target) or {}).get("primary_key_columns", [])
        source_columns = list(by_column) if source == class_name else (contracts.get(source) or {}).get("selected_columns", [])
        reason = None
        if not mapped or mapped["mapping_status"] != "resolved" or not column:
            reason = "外键映射尚未解析"
        elif any(other != class_name and other not in contracts for other in (source, target)):
            reason = "请先配置关联对象的数据契约"
        elif len(target_keys) != 1:
            reason = "目标主键需要人工配置"
        elif column not in source_columns:
            reason = f"来源数据契约未包含外键 {column}"
        if reason:
            blockers.append(f"{source} → {target} ({name})：{reason}")
        relations.append({"source": source, "name": name, "target": target,
                          "column": column, "targetColumns": target_keys, "blocker": reason})
    plan = {"className": class_name, "releaseId": str(active["active_release_id"]),
            "jobName": profile["profile"]["job_name"], "sourceSchema": mapping["physical_schema"] if mapping else None,
            "sourceTable": mapping["physical_table"] if mapping else None,
            "primaryKeys": keys["primary"], "businessKeys": keys["business"],
            "fields": list(by_column.values()), "relationships": relations,
            "role": node.get("role") or "context", "blockers": blockers,
            "configured": bool(configured), "hasContract": class_name in contracts,
            "currentMode": (configured or {}).get("config", {}).get("instanceMode", "data"),
            "modelOnlyAllowed": class_name not in contracts, "hasPolicy": bool(policy)}
    plan["fingerprint"] = digest({"plan": plan, "configured": configured,
                                   "contracts": governance["contracts"], "relationships": governance["relationships"],
                                   "profileRelationships": profile["relationships"], "policy": dict(policy) if policy else None})
    return plan


def validate_selection(plan, mode, selected_columns):
    if mode not in {"data", "model_only"}:
        raise ValueError("请选择同步业务数据或仅发布模型")
    if mode == "model_only":
        if not plan["modelOnlyAllowed"]:
            raise ValueError("已有数据契约，不能在此改为仅发布模型")
        return
    if plan["blockers"]:
        raise ValueError("；".join(plan["blockers"]))
    available = {f["physical_column"] for f in plan["fields"]}
    required = set(plan["primaryKeys"]) | set(plan["businessKeys"])
    required.update(f["physical_column"] for f in plan["fields"] if f["required"])
    required.update(r["column"] for r in plan["relationships"] if r["source"] == plan["className"])
    if not required.issubset(selected_columns) or not set(selected_columns).issubset(available):
        raise ValueError("选择字段必须包含主键、业务键、必填字段和关系外键，且不能包含未知字段")


def save_configuration(repository, profile_key, class_name, *, mode, selected_columns, fingerprint, actor):
    if not actor.strip():
        raise ValueError("请填写操作人")
    with repository.engine.begin() as conn:
        acquired = conn.execute(text("SELECT pg_try_advisory_xact_lock(hashtextextended(:name, 0))"),
                                {"name": f"graphsync:data-lane:{profile_key}"}).scalar_one()
        if not acquired:
            raise ValueError("数据同步正在运行，请完成后再修改配置")
        conn.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": f"sync-config:{profile_key}"})
        conn.execute(text("SELECT active_release_id FROM graphsync.ontology_release_activation WHERE profile_key=:profile FOR UPDATE"), {"profile": profile_key})
        scoped = copy(repository)
        scoped.engine = _TransactionEngine(conn)
        plan = configuration_preview(scoped, profile_key, class_name)
        if plan["fingerprint"] != fingerprint:
            raise ValueError("模型或同步配置已变化，请关闭后重新打开配置")
        validate_selection(plan, mode, selected_columns)
        audit = json.dumps({"instanceMode": mode, "configuredBy": actor.strip(), "configurationFingerprint": fingerprint})
        if not plan["configured"]:
            # Model-only classes need no physical mapping.
            conn.execute(text("""
                INSERT INTO graphsync.profile_class (profile_key,class_name,role,orphan_policy,seed_enabled,priority,enabled,review_status)
                VALUES (:profile,:name,:role,'quarantine',false,100,true,'approved')
            """), {"profile": profile_key, "name": class_name, "role": plan["role"]})
        conn.execute(text("""UPDATE graphsync.profile_class SET enabled=true,
            config=config || CAST(:audit AS jsonb), updated_at=now()
            WHERE profile_key=:profile AND class_name=:name"""), {"profile": profile_key, "name": class_name, "audit": audit})
        if mode == "data":
            required = sorted(set(plan["primaryKeys"]) | {f["physical_column"] for f in plan["fields"] if f["required"]})
            contract = scoped.create_data_contract(profile_key, class_name=class_name,
                primary_key_columns=plan["primaryKeys"], business_key_columns=plan["businessKeys"],
                selected_columns=selected_columns, required_columns=required, freshness_column=None,
                preview_row_limit=100000, publication_layer=plan["role"])
            scoped.update_data_contract(contract["contract_key"], status="approved",
                business_key_columns=plan["businessKeys"], required_columns=required, freshness_column=None,
                preview_row_limit=100000, publication_layer=plan["role"])
            if not plan["hasPolicy"]:
                scoped.upsert_table_policy(plan["jobName"], class_name, strategy="snapshot", watermark_column=None,
                    partition_column=None, batch_rows=10000, target_shard_bytes=134217728,
                    hot_window_days=None, enabled=True, config={"configuredBy": actor.strip()})
            for relation in plan["relationships"]:
                existing = next((r for r in scoped.graph_profile(profile_key)["relationships"]
                    if (r["source_class"], r["relationship_name"], r["target_class"]) ==
                       (relation["source"], relation["name"], relation["target"])), None)
                if not existing:
                    scoped.upsert_profile_relationship(profile_key, relation["source"], relation["name"], relation["target"],
                        strength="context", required_context=False, traverse=False, direction="outgoing",
                        max_depth=1, max_targets_per_source=50, enabled=True, review_status="approved")
                elif not existing["enabled"]:
                    raise ValueError("关联已明确停用，请先审阅关联范围")
                required_context = bool(existing and existing["required_context"])
                semantic_role = existing["strength"] if existing else "context"
                result = scoped.create_relationship_contract(profile_key, source_class=relation["source"],
                    relationship_name=relation["name"], target_class=relation["target"], semantic_role=semantic_role, required_context=required_context)
                scoped.update_relationship_contract(result["relationship_contract_key"], status="approved",
                    semantic_role=semantic_role, required_context=required_context)
        return {"ok": True, "mode": mode, "className": class_name}
