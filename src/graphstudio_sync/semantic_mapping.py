"""Physical snapshots and reviewed source-to-ontology mapping drafts.

Physical facts are immutable and separate from the active ontology. Only an
explicit entity mapping can produce a candidate; other source roles remain
design inputs until their business transformation has been implemented.
"""
from __future__ import annotations

import copy
import uuid

from sqlalchemy import text

from scripts.validate_ontology_vs_csv import expected_type, normalize_field_name
from src.ontology.physical_naming import relation_name
from .ontology_store import canonical, digest
from .physical_model import physical_fields

SOURCE_ROLES = {"pending", "entity", "event", "relationship", "auxiliary", "excluded"}
FIELD_ROLES = {"pending", "property", "relationship", "internal", "excluded"}


def source_fields(name, rows):
    return [{"name": normalize_field_name(row, name), "physicalName": row["FieldName"],
             "type": expected_type(row), "target": row.get("FKTableName", ""),
             "targetField": row.get("FKFieldName", ""), "fieldId": row.get("FieldID", ""),
             "primaryKey": str(row.get("IsPrimaryKey", "")).lower() == "true",
             "isList": str(row.get("IsList", "")).lower() == "true"}
            for row in physical_fields(rows)]


def validate_design(design, fields):
    if design.get("role") not in SOURCE_ROLES:
        raise ValueError("请选择有效的来源用途")
    roles = design.get("fields", {})
    known = {f["name"]: f for f in fields}
    if len(known) != len(fields):
        raise ValueError("多个物理字段规范化为同一名称，需要先明确字段映射，不能自动合并")
    if set(roles) - known.keys():
        raise ValueError("字段已不在该物理快照中，请刷新来源")
    for name, role in roles.items():
        if role not in FIELD_ROLES:
            raise ValueError(f"{name} 的字段用途无效")
        field = known[name]
        if field["primaryKey"] and role not in {"internal", "property"}:
            raise ValueError(f"{name} 是身份键，需保留为内部字段或业务属性")
        if role == "relationship" and (field["type"] != "Navigation" or not field["target"]):
            raise ValueError(f"{name} 没有可用的物理外键依据")
        if role == "property" and field["type"] == "Navigation":
            raise ValueError(f"{name} 是 Navigation 外键，请选择业务关系或内部字段")
    return {**copy.deepcopy(design), "fields": {
        f["name"]: roles.get(f["name"], "internal" if f["primaryKey"] else "pending") for f in fields}}


def candidate_preview(draft):
    fields = draft["fields"]
    design = validate_design(draft["design"], fields)
    blockers = []
    if design["role"] != "entity":
        blockers.append("只有明确的一表一实体映射可生成候选；事件拆分、关系表转换和多表组合需先完成业务转换规则。")
    if not design.get("chineseName", "").strip() or not design.get("description", "").strip():
        blockers.append("请填写业务中文名和业务定义")
    if not any(f["primaryKey"] for f in fields):
        blockers.append("CSV 未声明身份主键，请先核实实体身份；不能按表名推测")
    pending = [f["name"] for f in fields if design["fields"][f["name"]] == "pending"]
    if pending:
        blockers.append(f"还有 {len(pending)} 个字段未评估，请指定用途")
    name = draft["tableName"]
    properties, relationships = [], []
    for field in fields:
        role = design["fields"][field["name"]]
        if role in {"property", "relationship"}:
            properties.append({"name": field["name"], "type": field["type"], "description": "",
                               "physicalColumn": field["physicalName"], "sourceFieldId": field["fieldId"]})
        if role == "relationship":
            if field["target"] not in draft["tableNames"]:
                blockers.append(f"{field['name']} 的外键终点不在物理快照中")
            relationships.append({"fromClass": name, "toClass": field["target"],
                                  "relationName": relation_name(field["name"]), "sourceProperty": field["name"],
                                  "physicalColumn": field["physicalName"], "targetColumn": field["targetField"],
                                  "cardinality": "ONE_TO_MANY" if field["isList"] else "MANY_TO_ONE"})
    mapping = {"draftId": draft["draftId"], "revision": draft["revision"],
               "snapshotId": draft["snapshotId"], "sourceTable": name,
               "role": design["role"], "fieldRoles": design["fields"],
               "sourceFields": fields,
               "identityColumns": [f["physicalName"] for f in fields if f["primaryKey"]]}
    payload = {"classes": [{"className": name, "chineseName": design.get("chineseName", "").strip(),
                           "description": design.get("description", "").strip(), "properties": properties,
                           "_semanticMapping": mapping}], "relationships": relationships}
    result = {"payload": payload, "blockers": blockers,
              "counts": {"properties": sum(design["fields"][f["name"]] == "property" for f in fields),
                         "relationships": len(relationships),
                         "internal": sum(v == "internal" for v in design["fields"].values()),
                         "excluded": sum(v == "excluded" for v in design["fields"].values())}}
    result["planHash"] = digest(result)
    return result


class MappingStore:
    def __init__(self, engine):
        self.engine = engine

    def stage_sources(self, session, selected):
        # Retain all raw physical rows, including technical fields and unselected
        # tables. Descriptions and source credentials are not part of the facts.
        physical = {"tables": session["tables"], "fields": session["fields"]}
        snapshot_id = digest(physical)
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO graphsync.physical_model_snapshot(snapshot_id,payload) VALUES (:id,CAST(:p AS jsonb)) ON CONFLICT DO NOTHING"),
                         {"id": snapshot_id, "p": canonical(physical)})
            for name in sorted(selected):
                fields = source_fields(name, physical["fields"].get(name, []))
                design = {"role": "pending", "chineseName": "", "description": "", "notes": "",
                          "fields": {f["name"]: "internal" if f["primaryKey"] else "pending" for f in fields}}
                conn.execute(text("""INSERT INTO graphsync.semantic_mapping_draft(draft_id,snapshot_id,table_name,design)
                    VALUES (:id,:snapshot,:name,CAST(:design AS jsonb)) ON CONFLICT(snapshot_id,table_name) DO UPDATE SET
                    design=graphsync.semantic_mapping_draft.design - 'deleted',
                    revision=graphsync.semantic_mapping_draft.revision+1,updated_at=now()
                    WHERE COALESCE((graphsync.semantic_mapping_draft.design->>'deleted')::boolean,false)"""),
                    {"id": uuid.uuid4().hex, "snapshot": snapshot_id, "name": name, "design": canonical(design)})
        return {"snapshotId": snapshot_id, "sources": len(selected)}

    def list(self, deleted=False):
        with self.engine.connect() as conn:
            return [dict(r) for r in conn.execute(text("""SELECT draft_id AS "draftId", snapshot_id AS "snapshotId",
                table_name AS "tableName", revision, design->>'role' AS role, design->>'chineseName' AS "chineseName",
                updated_at AS "updatedAt" FROM graphsync.semantic_mapping_draft WHERE COALESCE((design->>'deleted')::boolean,false)=:deleted ORDER BY updated_at DESC,table_name"""), {"deleted": deleted}).mappings()]

    def set_deleted(self, draft_id, revision, deleted):
        with self.engine.begin() as conn:
            row = conn.execute(text("SELECT revision,design FROM graphsync.semantic_mapping_draft WHERE draft_id=:id FOR UPDATE"), {"id": draft_id}).mappings().one_or_none()
            if row is None:
                raise LookupError("来源草稿不存在")
            if row["revision"] != revision:
                raise RuntimeError("草稿已变化，请刷新后重试")
            design = {**row["design"], "deleted": deleted}
            conn.execute(text("UPDATE graphsync.semantic_mapping_draft SET design=CAST(:design AS jsonb),revision=revision+1,updated_at=now() WHERE draft_id=:id"), {"id": draft_id, "design": canonical(design)})
        return {"deleted": deleted}

    def snapshots(self):
        with self.engine.connect() as conn:
            return [dict(r) for r in conn.execute(text("""SELECT snapshot_id AS "snapshotId", created_at AS "createdAt",
                (SELECT count(*) FROM jsonb_object_keys(payload->'tables')) AS "tableCount"
                FROM graphsync.physical_model_snapshot ORDER BY created_at DESC LIMIT 50""")).mappings()]

    def physical(self, snapshot_id):
        with self.engine.connect() as conn:
            payload = conn.execute(text("SELECT payload FROM graphsync.physical_model_snapshot WHERE snapshot_id=:id"), {"id": snapshot_id}).scalar_one_or_none()
            if payload is None:
                raise LookupError("物理快照不存在")
            if digest(payload) != snapshot_id:
                raise ValueError("物理快照校验失败")
            return payload

    def detail(self, draft_id, conn=None, lock=False):
        if conn is None:
            with self.engine.connect() as connection:
                return self.detail(draft_id, connection)
        row = conn.execute(text("""SELECT d.*, s.payload FROM graphsync.semantic_mapping_draft d
            JOIN graphsync.physical_model_snapshot s USING(snapshot_id) WHERE draft_id=:id""" + (" FOR UPDATE OF d" if lock else "")), {"id": draft_id}).mappings().one_or_none()
        if row is None:
            raise LookupError("来源草稿不存在")
        if row["design"].get("deleted"):
            raise RuntimeError("草稿已删除，请先从已删除列表恢复")
        if digest(row["payload"]) != row["snapshot_id"]:
            raise ValueError("物理快照校验失败")
        return {"draftId": row["draft_id"], "snapshotId": row["snapshot_id"], "tableName": row["table_name"],
                "revision": row["revision"], "design": row["design"],
                "fields": source_fields(row["table_name"], row["payload"]["fields"].get(row["table_name"], [])),
                "tableNames": sorted(row["payload"]["tables"])}

    def save(self, draft_id, revision, design):
        with self.engine.begin() as conn:
            current = self.detail(draft_id, conn, lock=True)
            if current["revision"] != revision:
                raise RuntimeError("草稿已被修改，请刷新后重新编辑")
            design = validate_design(design, current["fields"])
            conn.execute(text("""UPDATE graphsync.semantic_mapping_draft SET design=CAST(:design AS jsonb),
                revision=revision+1,updated_at=now() WHERE draft_id=:id"""), {"design": canonical(design), "id": draft_id})
            return {**current, "design": design, "revision": revision + 1}
