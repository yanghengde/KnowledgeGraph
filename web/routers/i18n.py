"""Runtime internationalization and editable ontology display names."""

from __future__ import annotations

import glob
import json
import os
import re
import tempfile
import threading
import time
import csv
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from web.shared import PROJECT_ROOT


router = APIRouter(prefix="/api/i18n", tags=["internationalization"])

I18N_DIR = os.path.join(PROJECT_ROOT, "src", "ontology")
TRANSLATIONS_FILE = os.path.join(I18N_DIR, "display_translations.json")
_file_lock = threading.RLock()

KIND_TO_BUCKET = {
    "node_description": "nodeDescriptions",
    "property_description": "propertyDescriptions",
}

_TOKEN_ZH = {
    "a": "一个", "access": "访问", "action": "操作", "active": "启用", "actual": "实际",
    "amount": "数量", "approval": "审批", "associated": "关联", "attribute": "特性",
    "base": "基础", "batch": "批次", "bill": "清单", "bom": "物料清单", "business": "业务",
    "calendar": "日历", "can": "可", "carrier": "载具", "category": "类别", "change": "变更",
    "check": "检查", "class": "类", "code": "代码", "collection": "采集", "complete": "完成",
    "component": "组件", "container": "容器", "count": "数量", "created": "创建", "current": "当前",
    "customer": "客户", "cycle": "周期", "data": "数据", "date": "日期", "default": "默认",
    "def": "定义", "definition": "定义", "description": "描述", "detail": "明细", "document": "文档",
    "employee": "员工", "enabled": "启用", "end": "结束", "enterprise": "企业", "entry": "条目",
    "equipment": "设备", "erp": "ERP", "event": "事件", "factory": "工厂", "failure": "故障",
    "family": "系列", "field": "字段", "filter": "筛选", "first": "首个", "flow": "流程",
    "frozen": "冻结", "from": "来源", "group": "组", "has": "包含", "history": "历史",
    "icon": "图标", "id": "标识", "image": "图像", "in": "入", "inactive": "停用",
    "instance": "实例", "inventory": "库存", "is": "是否", "item": "项目", "label": "标签",
    "last": "最后", "level": "级别", "line": "产线", "list": "列表", "location": "位置",
    "locked": "锁定", "lot": "批次", "management": "管理", "manager": "管理器",
    "material": "物料", "max": "最大", "message": "消息", "mfg": "制造", "min": "最小",
    "model": "模型", "name": "名称", "new": "新", "notes": "备注", "notification": "通知",
    "number": "编号", "object": "对象", "operation": "工序", "order": "工单", "organization": "组织",
    "out": "出", "owner": "所有者", "package": "包", "part": "部件", "path": "路径",
    "physical": "物理", "plan": "计划", "priority": "优先级", "process": "过程", "product": "产品",
    "property": "属性", "queue": "队列", "reason": "原因", "record": "记录", "ref": "引用",
    "relationship": "关系", "remaining": "剩余", "required": "必需", "resource": "资源",
    "revision": "版本", "role": "角色", "route": "路线", "sales": "销售", "sample": "样本",
    "schedule": "排程", "scheduling": "排程", "sequence": "顺序", "setup": "设置", "shift": "班次",
    "shipping": "出货", "source": "来源", "spec": "规范", "start": "开始", "status": "状态",
    "step": "步骤", "supplier": "供应商", "tag": "标签", "tags": "标签", "target": "目标",
    "team": "团队", "template": "模板", "time": "时间", "to": "目标", "tool": "工装",
    "total": "总计", "training": "培训", "transaction": "事务", "type": "类型", "uom": "计量单位",
    "updated": "更新", "user": "用户", "uses": "使用", "value": "值", "vendor": "供应商",
    "version": "版本", "warehouse": "仓库", "workflow": "工作流", "work": "工作", "wip": "在制品",
    "with": "关联", "yield": "良率",
}


def _empty_store() -> dict:
    return {
        "version": 1,
        "revision": 0,
        "updatedAt": None,
        "translations": {"nodeDescriptions": {}, "propertyDescriptions": {}},
        "manualEdits": {"nodeDescriptions": {}, "propertyDescriptions": {}},
        "syncMeta": {},
    }


def _load_store() -> dict:
    with _file_lock:
        if not os.path.exists(TRANSLATIONS_FILE):
            return _empty_store()
        try:
            with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=500, detail=f"Translation configuration is invalid: {exc}") from exc
        store = _empty_store()
        store.update(data if isinstance(data, dict) else {})
        configured = store.setdefault("translations", {})
        manual_edits = store.setdefault("manualEdits", {})
        for bucket in KIND_TO_BUCKET.values():
            if not isinstance(configured.get(bucket), dict):
                configured[bucket] = {}
            if not isinstance(manual_edits.get(bucket), dict):
                manual_edits[bucket] = {}
        if not isinstance(store.get("syncMeta"), dict):
            store["syncMeta"] = {}
        return store


def _save_store(store: dict) -> None:
    os.makedirs(I18N_DIR, exist_ok=True)
    with _file_lock:
        fd, temporary_path = tempfile.mkstemp(prefix="translations-", suffix=".json", dir=I18N_DIR)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(store, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temporary_path, TRANSLATIONS_FILE)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)


def _words(identifier: str) -> list[str]:
    normalized = re.sub(r"[_\-.]+", " ", identifier or "")
    tokens: list[str] = []
    for part in normalized.split():
        tokens.extend(re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", part))
    return tokens or ([identifier] if identifier else [])


def _default_en(identifier: str) -> str:
    acronyms = {"api", "bom", "cdo", "eco", "erp", "id", "mes", "spc", "sql", "uom", "wip"}
    return " ".join(
        word.upper() if word.lower() in acronyms else word.capitalize()
        for word in _words(identifier)
    )


def _default_zh(identifier: str) -> str:
    translated = []
    for token in _words(identifier):
        translated.append(_TOKEN_ZH.get(token.lower(), token))
    return "".join(translated)


@lru_cache(maxsize=1)
def _ontology_catalog() -> dict[str, object]:
    nodes: dict[str, dict] = {}
    properties: dict[str, dict] = {}
    properties_by_node: dict[str, list[dict]] = {}
    pattern = os.path.join(PROJECT_ROOT, "src", "ontology", "wiki_kb", "*_ontology.json")
    for file_path in sorted(glob.glob(pattern)):
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        for ontology_class in data.get("classes", []):
            class_name = str(ontology_class.get("className") or "").strip()
            if not class_name:
                continue
            nodes[class_name] = {
                "kind": "node",
                "key": class_name,
                "owner": data.get("module") or os.path.basename(file_path),
                "original": class_name,
                "chineseName": ontology_class.get("chineseName") or "",
                "descriptionZh": ontology_class.get("description") or "",
                "descriptionEn": ontology_class.get("descriptionEn") or "",
                "propertyCount": len(ontology_class.get("properties", [])),
            }
            class_properties = []
            for prop in ontology_class.get("properties", []):
                prop_name = str(prop.get("name") or "").strip()
                if not prop_name:
                    continue
                key = f"{class_name}.{prop_name}"
                property_item = {
                    "kind": "property",
                    "key": key,
                    "owner": class_name,
                    "original": prop_name,
                    "zh": prop.get("chineseName") or _default_zh(prop_name),
                    "en": _default_en(prop_name),
                }
                properties[key] = property_item
                class_properties.append(property_item)
            properties_by_node[class_name] = sorted(class_properties, key=lambda item: item["original"].lower())
    return {
        "node": sorted(nodes.values(), key=lambda item: item["key"].lower()),
        "property": sorted(properties.values(), key=lambda item: item["key"].lower()),
        "propertiesByNode": properties_by_node,
    }


def _graph_catalog_snapshot() -> tuple[list[dict], dict[str, dict]]:
    """Use the exact graph data shown by the main node-detail panel."""
    from web.routers.graph import _all_class_details_cached, _graph_overview_cached

    overview = _graph_overview_cached()
    details = _all_class_details_cached()
    nodes = []
    for graph_node in overview.get("nodes", []):
        class_name = str(graph_node.get("id") or "")
        data = graph_node.get("data") or {}
        nodes.append({
            "kind": "node",
            "key": class_name,
            "owner": data.get("module") or "",
            "original": class_name,
            "chineseName": data.get("chineseName") or "",
            "descriptionZh": data.get("description") or "",
            "descriptionEn": "",
            "propertyCount": len((details.get(class_name) or {}).get("properties", [])),
        })
    return sorted(nodes, key=lambda item: item["key"].lower()), details


class TranslationUpdate(BaseModel):
    kind: Literal["node_description", "property_description"]
    key: str = Field(min_length=1, max_length=300)
    zh: str = Field(default="", max_length=5000)
    en: str = Field(default="", max_length=5000)


class DescriptionSyncRequest(BaseModel):
    className: str = Field(min_length=1, max_length=200)
    database: Literal["oracle", "sqlserver"] = "oracle"


@router.get("")
def get_translations():
    store = _load_store()
    return {
        "version": store["version"],
        "revision": store["revision"],
        "updatedAt": store.get("updatedAt"),
        "translations": store["translations"],
    }


@router.get("/catalog")
def get_translation_catalog(
    search: str = Query(default="", max_length=200),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=80, ge=1, le=200),
):
    items, _ = _graph_catalog_snapshot()
    store = _load_store()
    description_overrides = store["translations"]["nodeDescriptions"]
    query = search.strip().casefold()
    results = []
    for base in items:
        override = description_overrides.get(base["key"], {})
        item = {**base}
        item["descriptionZh"] = override.get("zh", base["descriptionZh"])
        item["descriptionEn"] = override.get("en", base["descriptionEn"])
        item["customized"] = base["key"] in description_overrides
        if query and query not in " ".join(
            str(item.get(field, "")) for field in ("key", "owner", "original", "chineseName", "descriptionZh", "descriptionEn")
        ).casefold():
            continue
        results.append(item)
    if query:
        def search_rank(item: dict) -> tuple[int, str]:
            name = str(item.get("key", "")).casefold()
            chinese_name = str(item.get("chineseName", "")).casefold()
            if name == query:
                rank = 0
            elif name.startswith(query):
                rank = 1
            elif query in name:
                rank = 2
            elif query in chinese_name:
                rank = 3
            else:
                rank = 4
            return rank, name
        results.sort(key=search_rank)
    return {
        "kind": "node",
        "items": results[offset:offset + limit],
        "offset": offset,
        "limit": limit,
        "total": len(results),
        "revision": store["revision"],
    }


@router.get("/node/{class_name}")
def get_node_translation_editor(class_name: str):
    graph_nodes, graph_details = _graph_catalog_snapshot()
    node = next((item for item in graph_nodes if item["key"] == class_name), None)
    if node is None:
        raise HTTPException(status_code=404, detail="Ontology node not found")
    store = _load_store()
    description_override = store["translations"]["nodeDescriptions"].get(class_name, {})
    property_overrides = store["translations"]["propertyDescriptions"]
    properties = []
    graph_properties = (graph_details.get(class_name) or {}).get("properties", [])
    for graph_property in graph_properties:
        property_name = str(graph_property.get("name") or "")
        key = f"{class_name}.{property_name}"
        override = property_overrides.get(key, {})
        properties.append({
            "kind": "property_description",
            "key": key,
            "owner": class_name,
            "original": property_name,
            "dataType": graph_property.get("dataType") or "String",
            "sourceDescription": graph_property.get("description") or "",
            "descriptionZh": override.get("zh", graph_property.get("description") or ""),
            "descriptionEn": override.get("en", ""),
            "customized": key in property_overrides,
        })
    return {
        **node,
        "descriptionZh": description_override.get("zh", node["descriptionZh"]),
        "descriptionEn": description_override.get("en", node["descriptionEn"]),
        "descriptionCustomized": class_name in store["translations"]["nodeDescriptions"],
        "properties": properties,
        "revision": store["revision"],
    }


@router.put("/translation")
def update_translation(update: TranslationUpdate):
    key = update.key.strip()
    if not key:
        raise HTTPException(status_code=422, detail="Translation key cannot be empty")
    store = _load_store()
    bucket = store["translations"][KIND_TO_BUCKET[update.kind]]
    zh = update.zh.strip()
    en = update.en.strip()
    if zh or en:
        bucket[key] = {"zh": zh, "en": en}
        store["manualEdits"][KIND_TO_BUCKET[update.kind]][key] = int(time.time() * 1000)
    else:
        bucket.pop(key, None)
        store["manualEdits"][KIND_TO_BUCKET[update.kind]].pop(key, None)
    store["revision"] = int(store.get("revision") or 0) + 1
    store["updatedAt"] = int(time.time() * 1000)
    _save_store(store)
    return {
        "success": True,
        "revision": store["revision"],
        "kind": update.kind,
        "key": key,
        "translation": bucket.get(key),
    }


def _designer_descriptions(class_name: str, database: str = "sqlserver") -> dict:
    from web.designer_metadata import get_cdo_metadata

    try:
        return get_cdo_metadata(database, class_name)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        label = "Oracle" if database == "oracle" else "SQL Server"
        raise HTTPException(status_code=503, detail=f"无法从 {label} 读取 Camstar Designer 描述：{exc}") from exc


def _physical_field_names(class_name: str) -> dict[str, str]:
    from scripts.validate_ontology_vs_csv import canonical_physical_fields, normalize_field_name

    path = Path(PROJECT_ROOT) / "docs" / "Database_Fields.csv"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("CDOName") == class_name]
    return {
        normalize_field_name(row, class_name): str(row.get("FieldName") or "")
        for row in canonical_physical_fields(rows, class_name)
    }


def _translate_descriptions(values: list[str]) -> dict[str, str]:
    from dotenv import load_dotenv
    from openai import OpenAI
    from scripts.build_designer_display_translations import compact, translate_batch

    unique = list(dict.fromkeys(compact(value) for value in values if compact(value)))
    if not unique:
        return {}
    load_dotenv(Path(PROJECT_ROOT) / ".env", override=False)
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="缺少翻译服务配置 DEEPSEEK_API_KEY")
    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        timeout=float(os.getenv("LLM_TIMEOUT", "120")),
    )
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    result: dict[str, str] = {}
    try:
        for index in range(0, len(unique), 35):
            batch = unique[index:index + 35]
            translated = translate_batch(client, model, "en_to_zh", batch)
            result.update(zip(batch, translated))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"中文翻译失败：{exc}") from exc
    return result


@router.post("/sync-descriptions")
def sync_descriptions(request: DescriptionSyncRequest):
    class_name = request.className.strip()
    graph_nodes, graph_details = _graph_catalog_snapshot()
    node = next((item for item in graph_nodes if item["key"] == class_name), None)
    if node is None:
        raise HTTPException(status_code=404, detail="Ontology node not found")
    designer = _designer_descriptions(class_name, request.database)
    property_names = _physical_field_names(class_name)
    graph_properties = (graph_details.get(class_name) or {}).get("properties", [])
    sources: list[tuple[str, str, str]] = []
    if designer["description"]:
        sources.append(("nodeDescriptions", class_name, designer["description"]))
    for prop in graph_properties:
        property_name = str(prop.get("name") or "")
        physical_name = property_names.get(property_name, property_name)
        matched = designer["fields"].get(physical_name.casefold()) or designer["fields"].get(property_name.casefold())
        if matched and matched["description"]:
            sources.append(("propertyDescriptions", f"{class_name}.{property_name}", matched["description"]))
    translation_warning = ""
    try:
        translations = _translate_descriptions([source for _, _, source in sources])
    except HTTPException as exc:
        translations = {source: source for _, _, source in sources}
        translation_warning = f"大模型或网络不可用，已保留英文原文：{exc.detail}"
    store = _load_store()
    updated = 0
    skipped_manual = 0
    for bucket_name, key, english in sources:
        if key in store["manualEdits"][bucket_name]:
            skipped_manual += 1
            continue
        store["translations"][bucket_name][key] = {"zh": translations[english], "en": english}
        updated += 1
    store["syncMeta"][class_name] = {
        "source": "Camstar Designer",
        "sourceCDOName": designer["cdoName"],
        "sourceCDODefId": designer["cdoDefId"],
        "syncedAt": int(time.time() * 1000),
        "matchedDescriptions": len(sources),
        "updatedDescriptions": updated,
        "manualDescriptionsPreserved": skipped_manual,
    }
    store["revision"] = int(store.get("revision") or 0) + 1
    store["updatedAt"] = int(time.time() * 1000)
    _save_store(store)
    return {
        "success": True,
        "className": class_name,
        "database": request.database,
        "matched": len(sources),
        "updated": updated,
        "manualPreserved": skipped_manual,
        "missing": 1 + len(graph_properties) - len(sources),
        "warning": translation_warning,
        "revision": store["revision"],
    }
