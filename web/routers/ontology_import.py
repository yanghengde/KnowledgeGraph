"""Reviewed CSV import for the physical Camstar ontology skeleton.

CSV rows are never published directly. Existing graph classes stay selected,
while classes already modeled in the curated ontology library are offered as
business recommendations. Unknown and technical CDOs remain unchecked.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from src.ontology.physical_naming import relation_name
from src.graphstudio_sync.physical_model import physical_fields
from src.ontology.designer_descriptions import load_descriptions, save_descriptions
from scripts.validate_ontology_vs_csv import (
    canonical_physical_fields,
    expected_type,
    normalize_field_name,
)
from web.shared import PROJECT_ROOT


router = APIRouter(prefix="/api/ontology-import", tags=["ontology-import"])

ONTOLOGY_DIR = Path(PROJECT_ROOT) / "src" / "ontology" / "wiki_kb"
IMPORTED_ONTOLOGY = ONTOLOGY_DIR / "csv_business_import_ontology.json"
IMPORT_MANIFEST = Path(PROJECT_ROOT) / "data" / "ontology_import_manifest.json"
DESCRIPTION_TRANSLATION_CACHE = Path(PROJECT_ROOT) / "data" / "import_description_translations.json"
MAX_UPLOAD_BYTES = 40 * 1024 * 1024
SESSION_TTL_SECONDS = 60 * 60

_sessions: dict[str, dict[str, Any]] = {}
_session_lock = threading.RLock()
_cache_lock = threading.RLock()

_TECHNICAL_PATTERNS = (
    (re.compile(r"(?:Changes|Maint|Inquiry|Service)$", re.I), "维护、查询或服务型 CDO"),
    (re.compile(r"(?:HistoryDetails?|Txn|Txns|Map|Mapping|ListItem|Details)$", re.I), "历史明细、事务或桥接型 CDO"),
    (re.compile(r"(?:Enum|Message|QueryDef|InquiryDef)$", re.I), "枚举、消息或查询定义型 CDO"),
    (re.compile(r"(?:DefaultForObj(?:ect)?Types?|DefaultForObjec|Entries|Groups|PathSelectors)$", re.I), "分组成员、默认范围或路径子表"),
    (re.compile(r"^(?:UI|Portal|WebPart|XMLConnect)|^VersionInfo$", re.I), "界面、门户或平台基础设施 CDO"),
)


class ImportApplyRequest(BaseModel):
    importId: str = Field(min_length=1, max_length=80)
    selected: list[str] = Field(default_factory=list, max_length=5000)


def _read_csv_upload(upload: UploadFile, required: set[str]) -> list[dict[str, str]]:
    raw = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"{upload.filename or 'CSV'} 超过 40 MB 限制")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("gb18030")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=422, detail=f"{upload.filename or 'CSV'} 不是 UTF-8 或 GB18030 编码") from exc
    reader = csv.DictReader(io.StringIO(text))
    columns = {str(name or "").strip() for name in (reader.fieldnames or [])}
    missing = sorted(required - columns)
    if missing:
        raise HTTPException(status_code=422, detail=f"{upload.filename or 'CSV'} 缺少列：{', '.join(missing)}")
    rows = []
    for row in reader:
        normalized = {str(key or "").strip(): str(value or "").strip() for key, value in row.items()}
        if any(normalized.values()):
            rows.append(normalized)
    return rows


def _reviewed_class_names() -> set[str]:
    names: set[str] = set()
    for path in ONTOLOGY_DIR.glob("*_ontology.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        names.update(
            str(item.get("className") or "").strip()
            for item in payload.get("classes", [])
            if item.get("className")
        )
    try:
        from web.routers.graph import _graph_overview_cached

        names.update(str(item.get("id") or "") for item in _graph_overview_cached().get("nodes", []))
    except Exception:
        pass
    return {name for name in names if name}


def _curated_business_class_names() -> set[str]:
    """Return classes deliberately modeled in source-controlled ontologies.

    The generated CSV import file is excluded so a previous broad import cannot
    silently become a recommendation on the next run.
    """
    names: set[str] = set()
    for path in ONTOLOGY_DIR.glob("*_ontology.json"):
        if path == IMPORTED_ONTOLOGY:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        names.update(
            str(item.get("className") or "").strip()
            for item in payload.get("classes", [])
            if item.get("className")
        )
    return {name for name in names if name}


def _candidate_status(
    class_name: str,
    reviewed: set[str],
    curated: set[str],
) -> tuple[str, str, bool]:
    if class_name in reviewed:
        return "approved", "当前图谱中已审核的业务对象", True
    for pattern, reason in _TECHNICAL_PATTERNS:
        if pattern.search(class_name):
            return "excluded", reason, False
    if class_name in curated:
        return "recommended", "项目本体库中已正式建模的业务对象，建议导入", True
    return "review", "新发现的 CDO，需要确认是否具有独立业务意义", False


def _purge_expired_sessions() -> None:
    cutoff = time.time() - SESSION_TTL_SECONDS
    for session_id in [key for key, value in _sessions.items() if value["createdAt"] < cutoff]:
        _sessions.pop(session_id, None)


def _designer_description_for(class_name: str, catalog: dict[str, dict[str, str]]) -> str:
    matched = catalog.get(class_name.casefold())
    if not matched and class_name.startswith("A_"):
        matched = catalog.get(class_name[2:].casefold())
    return str((matched or {}).get("description") or "")


def _load_description_cache() -> dict[str, str]:
    cache: dict[str, str] = {}
    with _cache_lock:
        if DESCRIPTION_TRANSLATION_CACHE.exists():
            try:
                payload = json.loads(DESCRIPTION_TRANSLATION_CACHE.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    cache.update({str(key): str(value) for key, value in payload.items() if key and value})
            except (OSError, json.JSONDecodeError):
                pass
    try:
        from web.routers.i18n import _load_store

        for value in _load_store()["translations"]["nodeDescriptions"].values():
            english = str(value.get("en") or "").strip()
            chinese = str(value.get("zh") or "").strip()
            if english and chinese:
                cache.setdefault(english, chinese)
    except Exception:
        pass
    return cache


def _save_description_cache(cache: dict[str, str]) -> None:
    with _cache_lock:
        DESCRIPTION_TRANSLATION_CACHE.parent.mkdir(parents=True, exist_ok=True)
        current: dict[str, str] = {}
        if DESCRIPTION_TRANSLATION_CACHE.exists():
            try:
                payload = json.loads(DESCRIPTION_TRANSLATION_CACHE.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    current.update({str(key): str(value) for key, value in payload.items() if key and value})
            except (OSError, json.JSONDecodeError):
                pass
        current.update(cache)
        temporary = DESCRIPTION_TRANSLATION_CACHE.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(DESCRIPTION_TRANSLATION_CACHE)


def _configured_translation_provider() -> str:
    """Choose a fast translation service first and keep the LLM as fallback."""
    requested = os.getenv("IMPORT_TRANSLATION_PROVIDER", "auto").strip().lower()
    if requested in {"none", "disabled", "off"}:
        return "none"
    if requested in {"api", "translation_api"}:
        return "api" if os.getenv("TRANSLATION_API_URL", "").strip() else "none"
    if requested in {"llm", "deepseek"}:
        return "llm" if os.getenv("DEEPSEEK_API_KEY", "").strip() else "none"
    if os.getenv("TRANSLATION_API_URL", "").strip():
        return "api"
    if os.getenv("DEEPSEEK_API_KEY", "").strip():
        return "llm"
    return "none"


def _build_batch_translator(provider: str):
    if provider == "api":
        endpoint = os.getenv("TRANSLATION_API_URL", "").strip()
        api_key = os.getenv("TRANSLATION_API_KEY", "").strip()

        def translate_with_api(batch: list[str]) -> list[str]:
            body: dict[str, Any] = {"q": batch, "source": "en", "target": "zh", "format": "text"}
            if api_key:
                body["api_key"] = api_key
            request = urllib.request.Request(
                endpoint,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=float(os.getenv("TRANSLATION_API_TIMEOUT", "30"))) as response:
                payload = json.loads(response.read().decode("utf-8"))
            translated = payload.get("translatedText") if isinstance(payload, dict) else None
            if isinstance(translated, str):
                translated = [translated]
            if not isinstance(translated, list) or len(translated) != len(batch):
                raise RuntimeError("专用翻译服务返回格式不正确")
            return [str(value).strip() for value in translated]

        return translate_with_api, 80

    if provider == "llm":
        from openai import OpenAI
        from src.ontology.translation import translate_batch

        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            timeout=float(os.getenv("LLM_TIMEOUT", "120")),
        )
        model = os.getenv("LLM_MODEL", "deepseek-chat")

        def translate_with_llm(batch: list[str]) -> list[str]:
            return translate_batch(client, model, "en_to_zh", batch)

        return translate_with_llm, 35

    raise RuntimeError("未配置可用的翻译服务")


def _translation_public_state(session: dict[str, Any]) -> dict[str, Any]:
    state = session["translation"]
    return {
        "status": state["status"],
        "metadataStatus": state["metadataStatus"],
        "provider": state["provider"],
        "total": state["total"],
        "completed": state["completed"],
        "warning": state.get("warning", ""),
    }


def _run_description_job(session_id: str) -> None:
    with _session_lock:
        session = _sessions.get(session_id)
        if not session:
            return
        state = session["translation"]
        if state["metadataStatus"] == "loading":
            return
        state["metadataStatus"] = "loading"
        state["warning"] = ""
        database = session["database"]
    try:
        from web.designer_metadata import load_cdo_description_catalog

        stored = load_descriptions(database)
        # Saved reference metadata remains usable when the source is offline.
        with _session_lock:
            for (class_name, field_name), entry in stored.items():
                if class_name not in session["candidates"]:
                    continue
                if field_name:
                    session.setdefault("fieldDescriptions", {}).setdefault(class_name, {})[field_name] = entry
                else:
                    session["candidates"][class_name].update(entry)
        catalog = load_cdo_description_catalog(database)
        cache = _load_description_cache()
        for item in stored.values():
            if item.get("descriptionZh"):
                cache.setdefault(item["descriptionEn"], item["descriptionZh"])
        with _session_lock:
            session = _sessions.get(session_id)
            if not session:
                return
            for (class_name, field_name), entry in stored.items():
                if field_name and class_name in session["candidates"]:
                    session.setdefault("fieldDescriptions", {}).setdefault(class_name, {})[field_name] = entry
            descriptions: list[str] = []
            for class_name, candidate in session["candidates"].items():
                english = _designer_description_for(class_name, catalog)
                candidate["descriptionEn"] = english
                candidate["descriptionZh"] = cache.get(english, "") if english else ""
                if english:
                    descriptions.append(english)
            unique = list(dict.fromkeys(descriptions))
            pending = [value for value in unique if value not in cache]
            provider = _configured_translation_provider()
            job = session["translation"]
            job.update({
                "metadataStatus": "completed",
                "provider": provider,
                "total": len(unique),
                "completed": len(unique) - len(pending),
                "pending": pending,
                "status": (
                    "completed" if not pending
                    else "unavailable" if provider == "none"
                    else "pending"
                ),
                "warning": (
                    "未配置可用的翻译服务，中文界面暂时显示数据库英文原文。"
                    if pending and provider == "none" else ""
                ),
            })
        save_descriptions(database, [dict(candidate, className=name)
                                    for name, candidate in session["candidates"].items()])
        if pending and provider != "none":
            _run_translation_job(session_id)
    except Exception as exc:
        label = "Oracle" if database == "oracle" else "SQL Server"
        with _session_lock:
            session = _sessions.get(session_id)
            if session:
                session["translation"].update({
                    "metadataStatus": "failed",
                    "status": "unavailable",
                    "warning": f"无法连接 {label} 获取 CDO 描述，候选结构仍可审核：{exc}",
                })


def _start_description_job(session_id: str) -> None:
    threading.Thread(
        target=_run_description_job,
        args=(session_id,),
        name=f"ontology-descriptions-{session_id[:8]}",
        daemon=True,
    ).start()


def _run_translation_job(session_id: str) -> None:
    with _session_lock:
        session = _sessions.get(session_id)
        if not session:
            return
        state = session["translation"]
        if state["status"] == "running":
            return
        provider = state["provider"]
        pending = list(state["pending"])
        state["status"] = "running"
        state["warning"] = ""
    try:
        translator, batch_size = _build_batch_translator(provider)
        cache = _load_description_cache()
        for index in range(0, len(pending), batch_size):
            batch = pending[index:index + batch_size]
            translated = translator(batch)
            if len(translated) != len(batch):
                raise RuntimeError("翻译结果数量与原文不一致")
            updates = {source: target for source, target in zip(batch, translated) if target}
            cache.update(updates)
            _save_description_cache(updates)
            save_descriptions(session["database"], [
                {"className": name, "descriptionEn": candidate["descriptionEn"],
                 "descriptionZh": updates[candidate["descriptionEn"]]}
                for name, candidate in session["candidates"].items()
                if candidate.get("descriptionEn") in updates
            ])
            with _session_lock:
                session = _sessions.get(session_id)
                if not session:
                    continue
                for candidate in session["candidates"].values():
                    source = candidate.get("descriptionEn", "")
                    if source in updates:
                        candidate["descriptionZh"] = updates[source]
                job = session["translation"]
                job["completed"] += len(updates)
                job["pending"] = [value for value in job["pending"] if value not in updates]
        with _session_lock:
            session = _sessions.get(session_id)
            if session:
                job = session["translation"]
                job["status"] = "completed" if not job["pending"] else "failed"
                if job["pending"]:
                    job["warning"] = "部分描述未能翻译，暂时显示数据库英文原文。"
    except Exception as exc:
        with _session_lock:
            session = _sessions.get(session_id)
            if session:
                session["translation"]["status"] = "failed"
                session["translation"]["warning"] = f"翻译服务暂时不可用，未完成内容显示英文原文：{exc}"


def _start_translation_job(session_id: str) -> None:
    threading.Thread(
        target=_run_translation_job,
        args=(session_id,),
        name=f"ontology-translation-{session_id[:8]}",
        daemon=True,
    ).start()


@router.post("/analyze")
def analyze_import(
    tables: UploadFile = File(...),
    fields: UploadFile = File(...),
    database: str = Form(...),
):
    database = database.strip().lower()
    if database not in {"oracle", "sqlserver"}:
        raise HTTPException(status_code=422, detail="数据库类型必须是 Oracle 或 SQL Server")
    table_rows = _read_csv_upload(tables, {"CDODefId", "CDOName", "Workspace"})
    field_rows = _read_csv_upload(
        fields,
        {"CDODefId", "CDOName", "FieldID", "FieldName", "IsForeignKey", "FKTableName", "DataType"},
    )
    table_by_name: dict[str, dict[str, str]] = {}
    duplicates: set[str] = set()
    for row in table_rows:
        name = row.get("CDOName", "")
        if not name:
            continue
        if name in table_by_name:
            duplicates.add(name)
        table_by_name[name] = row
    if duplicates:
        sample = ", ".join(sorted(duplicates)[:10])
        raise HTTPException(status_code=422, detail=f"表 CSV 存在重复 CDOName：{sample}")

    fields_by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    orphan_fields: set[str] = set()
    for row in field_rows:
        name = row.get("CDOName", "")
        if not name:
            continue
        if name not in table_by_name:
            orphan_fields.add(name)
        fields_by_class[name].append(row)
    if orphan_fields:
        sample = ", ".join(sorted(orphan_fields)[:10])
        raise HTTPException(status_code=422, detail=f"字段 CSV 引用了表 CSV 中不存在的 CDO：{sample}")

    reviewed = _reviewed_class_names()
    curated = _curated_business_class_names()
    candidates = []
    for name, table in sorted(table_by_name.items(), key=lambda item: item[0].casefold()):
        canonical = canonical_physical_fields(fields_by_class.get(name, []), name)
        status, reason, selected = _candidate_status(name, reviewed, curated)
        relationship_count = sum(
            1
            for field in canonical
            if str(field.get("IsForeignKey", "")).lower() == "true" and field.get("FKTableName")
        )
        candidates.append({
            "className": name,
            "cdoDefId": table.get("CDODefId", ""),
            "workspace": table.get("Workspace", ""),
            "propertyCount": len(physical_fields(fields_by_class.get(name, []))),
            "relationshipCount": relationship_count,
            "status": status,
            "reason": reason,
            "selected": selected,
            "descriptionEn": "",
            "descriptionZh": "",
        })

    outgoing: dict[str, list[dict]] = defaultdict(list)
    incoming: dict[str, list[dict]] = defaultdict(list)
    for name, rows in fields_by_class.items():
        for field in physical_fields(rows):
            target = field.get("FKTableName", "")
            if expected_type(field) != "Navigation" or not target:
                continue
            edge = {"source": name, "target": target, "fieldName": field["FieldName"],
                    "fieldId": field.get("FieldID", ""), "targetField": field.get("FKFieldName", ""),
                    "isList": field.get("IsList", "").lower() == "true",
                    "available": target in table_by_name}
            outgoing[name].append(edge)
            incoming[target].append(edge)
    for candidate in candidates:
        candidate["incomingCount"] = len(incoming[candidate["className"]])
        candidate["relationshipCount"] = len(outgoing[candidate["className"]])
    session_id = uuid.uuid4().hex
    translation_state = {
        "status": "waiting",
        "metadataStatus": "pending",
        "provider": _configured_translation_provider(),
        "total": 0,
        "completed": 0,
        "pending": [],
        "warning": "",
    }
    with _session_lock:
        _purge_expired_sessions()
        _sessions[session_id] = {
            "createdAt": time.time(),
            "tables": table_by_name,
            "fields": dict(fields_by_class),
            "candidates": {item["className"]: item for item in candidates},
            "reviewed": reviewed,
            "database": database,
            "outgoing": dict(outgoing), "incoming": dict(incoming),
            "fieldDescriptions": {},
            "translation": translation_state,
        }
    summary = {
        "tables": len(table_by_name),
        "fields": len(field_rows),
        "approved": sum(item["status"] == "approved" for item in candidates),
        "recommended": sum(item["status"] == "recommended" for item in candidates),
        "review": sum(item["status"] == "review" for item in candidates),
        "excluded": sum(item["status"] == "excluded" for item in candidates),
        "defaultSelected": sum(item["selected"] for item in candidates),
        "described": sum(bool(item["descriptionEn"]) for item in candidates),
        "translated": sum(bool(item["descriptionZh"]) for item in candidates),
    }
    result = {
        "importId": session_id,
        "database": database,
        "summary": summary,
        "descriptionWarning": "",
        "translation": _translation_public_state(_sessions[session_id]),
        "candidates": candidates,
    }
    _start_description_job(session_id)
    return result


@router.get("/translation/{import_id}")
def translation_status(import_id: str):
    with _session_lock:
        _purge_expired_sessions()
        session = _sessions.get(import_id)
        if session is None:
            raise HTTPException(status_code=404, detail="导入分析已过期，请重新选择 CSV")
        translations = {
            class_name: candidate.get("descriptionZh", "")
            for class_name, candidate in session["candidates"].items()
            if candidate.get("descriptionZh")
        }
        descriptions = {
            class_name: candidate.get("descriptionEn", "")
            for class_name, candidate in session["candidates"].items()
            if candidate.get("descriptionEn")
        }
        described_count = sum(bool(item.get("descriptionEn")) for item in session["candidates"].values())
        translated_count = sum(bool(item.get("descriptionZh")) for item in session["candidates"].values())
        state = _translation_public_state(session)
    return {
        "translation": state,
        "described": described_count,
        "translated": translated_count,
        "descriptions": descriptions,
        "translations": translations,
    }


@router.post("/translation/{import_id}/retry")
def retry_translation(import_id: str):
    with _session_lock:
        _purge_expired_sessions()
        session = _sessions.get(import_id)
        if session is None:
            raise HTTPException(status_code=404, detail="导入分析已过期，请重新选择 CSV")
        job = session["translation"]
        if job["status"] == "running" or job["metadataStatus"] in {"pending", "loading"}:
            return {"translation": _translation_public_state(session)}
        retry_descriptions = job["metadataStatus"] == "failed"
        if retry_descriptions:
            job.update({"metadataStatus": "pending", "status": "waiting", "warning": ""})
            state = _translation_public_state(session)
        else:
            cache = _load_description_cache()
            descriptions = list(dict.fromkeys(
                item.get("descriptionEn", "") for item in session["candidates"].values() if item.get("descriptionEn")
            ))
            pending = [value for value in descriptions if value not in cache]
            provider = _configured_translation_provider()
            job.update({
                "status": "completed" if not pending else "unavailable" if provider == "none" else "pending",
                "provider": provider,
                "total": len(descriptions),
                "completed": len(descriptions) - len(pending),
                "pending": pending,
                "warning": "" if provider != "none" or not pending else "未配置可用的翻译服务，中文界面暂时显示数据库英文原文。",
            })
            state = _translation_public_state(session)
    if retry_descriptions:
        _start_description_job(import_id)
    elif state["status"] == "pending":
        _start_translation_job(import_id)
    return {"translation": state}


def _property_definition(field: dict[str, str], class_name: str) -> dict[str, Any]:
    name = normalize_field_name(field, class_name)
    item: dict[str, Any] = {
        "name": name,
        "type": expected_type(field),
        "description": "",
        "sourceFieldId": field.get("FieldID", ""),
    }
    if name == "name" or str(field.get("IsPrimaryKey", "")).lower() == "true":
        item["required"] = True
    return item


def _enriched_property(field: dict, class_name: str, session: dict) -> dict:
    descriptions = session.get("fieldDescriptions", {}).get(class_name, {}).get(field["FieldName"].casefold(), {})
    return {**_property_definition(field, class_name), **descriptions,
            "description": descriptions.get("descriptionZh") or descriptions.get("descriptionEn") or ""}


def _write_imported_ontology(
    new_classes: list[dict],
    relationships: list[dict],
    *,
    allowed_class_names: set[str] | None = None,
) -> None:
    existing = {"module": "csv_business_import", "classes": [], "relationships": []}
    if IMPORTED_ONTOLOGY.exists():
        existing = json.loads(IMPORTED_ONTOLOGY.read_text(encoding="utf-8-sig"))
    if allowed_class_names is not None:
        existing["classes"] = [
            item for item in existing.get("classes", [])
            if item.get("className") in allowed_class_names
        ]
        existing["relationships"] = [
            item for item in existing.get("relationships", [])
            if item.get("fromClass") in allowed_class_names and item.get("toClass") in allowed_class_names
        ]
    class_by_name = {item["className"]: item for item in existing.get("classes", [])}
    for item in new_classes:
        class_by_name[item["className"]] = item
    relationship_by_key = {
        (item.get("fromClass"), item.get("toClass"), item.get("relationName")): item
        for item in existing.get("relationships", [])
    }
    for item in relationships:
        relationship_by_key[(item["fromClass"], item["toClass"], item["relationName"])] = item
    payload = {
        "module": "csv_business_import",
        "classes": sorted(class_by_name.values(), key=lambda item: item["className"].casefold()),
        "relationships": sorted(
            relationship_by_key.values(),
            key=lambda item: (item["fromClass"].casefold(), item["toClass"].casefold(), item["relationName"]),
        ),
    }
    IMPORTED_ONTOLOGY.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="csv-business-import-", suffix=".json", dir=IMPORTED_ONTOLOGY.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, IMPORTED_ONTOLOGY)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_manifest(selected: set[str], source_count: int, *, reset: bool = False) -> None:
    current: dict[str, Any] = {"version": 1, "approvedBusinessObjects": []}
    if IMPORT_MANIFEST.exists() and not reset:
        try:
            current.update(json.loads(IMPORT_MANIFEST.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            pass
    approved = set(current.get("approvedBusinessObjects") or []) | selected
    current.update({
        "approvedBusinessObjects": sorted(approved, key=str.casefold),
        "lastImportAt": int(time.time() * 1000),
        "lastSourceTableCount": source_count,
    })
    IMPORT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = IMPORT_MANIFEST.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(IMPORT_MANIFEST)


@router.post("/apply")
def apply_import(request: ImportApplyRequest):
    """Stage immutable candidates; only the authority review can accept them."""
    import copy
    from src.ontology.authority_store import authority_store
    with _session_lock:
        _purge_expired_sessions()
        session = copy.deepcopy(_sessions.get(request.importId))
    if session is None:
        raise HTTPException(status_code=404, detail="导入分析已过期，请重新选择 CSV")
    selected = {name.strip() for name in request.selected if name.strip()}
    if not selected or selected - set(session["candidates"]):
        raise HTTPException(status_code=422, detail="请仅选择本次分析中的业务对象")
    allowed_targets = set(session["reviewed"]) | selected | _curated_business_class_names()
    classes, relationships = [], []
    seen = set()
    for name in sorted(selected):
        fields = canonical_physical_fields(session["fields"].get(name, []), name)
        candidate = session["candidates"][name]
        classes.append({"className": name, "chineseName": "",
                        "description": candidate.get("descriptionZh") or candidate.get("descriptionEn") or "",
                        "descriptionEn": candidate.get("descriptionEn", ""),
                        "descriptionZh": candidate.get("descriptionZh", ""),
                        "sourceCDODefId": session["tables"][name].get("CDODefId", ""),
                        "properties": [_enriched_property(f, name, session) for f in fields]})
        for field in fields:
            target = field.get("FKTableName")
            relation = relation_name(normalize_field_name(field, name))
            key = (name, relation, target)
            if expected_type(field) == "Navigation" and target in allowed_targets and key not in seen:
                relationships.append({"fromClass": name, "toClass": target, "relationName": relation,
                                      "cardinality": "MANY_TO_ONE", "description": name + "." + field["FieldName"]})
                seen.add(key)
    try:
        staged = authority_store().stage({"classes": classes, "relationships": relationships})
    except Exception as exc:
        raise HTTPException(503, "候选保存失败，请检查 PostgreSQL；未改写活动本体") from exc
    return {"success": True, "status": "pending_review", **staged,
            "classes": len(classes), "relationships": len(relationships),
            "reviewUrl": "/app/ontology-model",
            "message": "已保存导入候选，请到本体目录查看差异并确认合并。"}


def _import_session(import_id: str) -> dict:
    with _session_lock:
        _purge_expired_sessions()
        session = _sessions.get(import_id)
        if session is None:
            raise HTTPException(404, "导入分析已过期，请重新分析 CSV")
        return session


@router.get("/objects/{import_id}/{class_name}")
def import_object(import_id: str, class_name: str):
    session = _import_session(import_id)
    with _session_lock:
        if class_name not in session["candidates"]:
            raise HTTPException(404, "本次 CSV 中没有该对象")
        fields = [dict(_enriched_property(field, class_name, session),
                       physicalName=field["FieldName"], target=field.get("FKTableName", ""),
                       primaryKey=str(field.get("IsPrimaryKey", "")).lower() == "true")
                  for field in physical_fields(session["fields"].get(class_name, []))]
        return {"candidate": dict(session["candidates"][class_name]), "fields": fields,
                "outgoing": session["outgoing"].get(class_name, []),
                "incoming": session["incoming"].get(class_name, [])}


@router.post("/objects/{import_id}/{class_name}/descriptions")
def enrich_object(import_id: str, class_name: str):
    session = _import_session(import_id)
    if class_name not in session["candidates"]:
        raise HTTPException(404, "本次 CSV 中没有该对象")
    from web.designer_metadata import get_cdo_metadata
    database = session["database"]
    warning = ""
    try:
        stored = load_descriptions(database)
        metadata = get_cdo_metadata(database, class_name)
        english = {key: item["description"] for key, item in metadata["fields"].items()}
        cache = _load_description_cache()
        for item in stored.values():
            if item.get("descriptionZh"):
                cache.setdefault(item["descriptionEn"], item["descriptionZh"])
        rows = [{"className": class_name, "fieldName": key, "descriptionEn": value,
                 "descriptionZh": cache.get(value, "")} for key, value in english.items() if value]
        save_descriptions(database, rows)
        pending = list(dict.fromkeys(row["descriptionEn"] for row in rows if not row["descriptionZh"]))
        provider = _configured_translation_provider()
        try:
            if pending and provider != "none":
                translator, size = _build_batch_translator(provider)
                for index in range(0, len(pending), size):
                    batch = pending[index:index + size]
                    translated = translator(batch)
                    if len(translated) != len(batch) or any(not value.strip() for value in translated):
                        raise ValueError("翻译结果不完整")
                    updates = dict(zip(batch, translated))
                    cache.update(updates)
                    _save_description_cache(updates)
                    save_descriptions(database, [dict(row, descriptionZh=cache.get(row["descriptionEn"], "")) for row in rows])
            elif pending:
                warning = "未配置翻译服务，英文原文已保存，可稍后重试。"
        except Exception:
            warning = "翻译暂未完成，英文原文和已完成的中文已保存，可重试。"
        with _session_lock:
            session["fieldDescriptions"][class_name] = {
                key: {"descriptionEn": value, "descriptionZh": cache.get(value, "")}
                for key, value in english.items() if value}
    except Exception:
        raise HTTPException(503, "读取或保存系统说明失败，请检查源数据库与 PostgreSQL 连接")
    return {**import_object(import_id, class_name), "warning": warning}


@router.post("/analyze-standard")
def analyze_standard(database: str = "sqlserver"):
    with (Path(PROJECT_ROOT) / "docs/Database_Tables.csv").open("rb") as tables, (Path(PROJECT_ROOT) / "docs/Database_Fields.csv").open("rb") as fields:
        return analyze_import(UploadFile(filename="Database_Tables.csv", file=tables),
                              UploadFile(filename="Database_Fields.csv", file=fields), database)
