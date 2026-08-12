"""Reviewed CSV import for the physical Camstar ontology skeleton.

CSV rows are never published directly.  Existing ontology classes are treated
as the reviewed business allow-list; every previously unseen CDO remains an
unchecked candidate until the user explicitly selects it in the settings UI.
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

from scripts.generate_ontology_batch import relation_name
from scripts.validate_ontology_vs_csv import (
    canonical_physical_fields,
    expected_type,
    normalize_field_name,
)
from src.ontology.runtime_state import (
    is_empty_baseline_mode,
    load_graph_state,
    mark_graph_cleared,
    save_graph_state,
)
from web.shared import PROJECT_ROOT, driver


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
)


class ImportApplyRequest(BaseModel):
    importId: str = Field(min_length=1, max_length=80)
    selected: list[str] = Field(default_factory=list, max_length=5000)


class ClearGraphRequest(BaseModel):
    confirmation: str = Field(min_length=1, max_length=80)
    acknowledgeIrreversible: bool = False


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
    if not is_empty_baseline_mode():
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


def _candidate_status(class_name: str, reviewed: set[str]) -> tuple[str, str, bool]:
    if class_name in reviewed:
        return "approved", "当前图谱中已审核的业务对象", True
    for pattern, reason in _TECHNICAL_PATTERNS:
        if pattern.search(class_name):
            return "excluded", reason, False
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
        from scripts.build_designer_display_translations import translate_batch

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

        catalog = load_cdo_description_catalog(database)
        cache = _load_description_cache()
        with _session_lock:
            session = _sessions.get(session_id)
            if not session:
                return
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
    candidates = []
    for name, table in sorted(table_by_name.items(), key=lambda item: item[0].casefold()):
        canonical = canonical_physical_fields(fields_by_class.get(name, []), name)
        status, reason, selected = _candidate_status(name, reviewed)
        relationship_count = sum(
            1
            for field in canonical
            if str(field.get("IsForeignKey", "")).lower() == "true" and field.get("FKTableName")
        )
        candidates.append({
            "className": name,
            "cdoDefId": table.get("CDODefId", ""),
            "workspace": table.get("Workspace", ""),
            "propertyCount": len(canonical),
            "relationshipCount": relationship_count,
            "status": status,
            "reason": reason,
            "selected": selected,
            "descriptionEn": "",
            "descriptionZh": "",
        })

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
            "translation": translation_state,
        }
    summary = {
        "tables": len(table_by_name),
        "fields": len(field_rows),
        "approved": sum(item["status"] == "approved" for item in candidates),
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


def _invalidate_graph_caches() -> None:
    from web.routers.graph import (
        _all_class_details_cached,
        _graph_class_detail_cached,
        _graph_overview_cached,
        _stats_cached,
    )
    from web.routers.i18n import _ontology_catalog

    _graph_overview_cached.cache_clear()
    _graph_class_detail_cached.cache_clear()
    _all_class_details_cached.cache_clear()
    _stats_cached.cache_clear()
    _ontology_catalog.cache_clear()


def _graph_counts(neo_session) -> dict[str, int]:
    record = neo_session.run("""
        CALL { MATCH (n) RETURN count(n) AS totalNodes }
        CALL { MATCH ()-[r]->() RETURN count(r) AS totalRelationships }
        CALL { MATCH (n:OntologyClass) RETURN count(n) AS classes }
        CALL { MATCH (n:OntologyProperty) RETURN count(n) AS properties }
        CALL { MATCH ()-[r:ONTOLOGY_RELATION]->() RETURN count(r) AS ontologyRelationships }
        RETURN totalNodes, totalRelationships, classes, properties, ontologyRelationships
    """).single()
    values = dict(record or {})
    return {
        "totalNodes": int(values.get("totalNodes") or 0),
        "totalRelationships": int(values.get("totalRelationships") or 0),
        "classes": int(values.get("classes") or 0),
        "properties": int(values.get("properties") or 0),
        "ontologyRelationships": int(values.get("ontologyRelationships") or 0),
    }


@router.get("/clear-preview")
def clear_graph_preview():
    try:
        with driver.session() as neo_session:
            counts = _graph_counts(neo_session)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"无法读取 Neo4j 图谱规模：{exc}") from exc
    return {**counts, "emptyBaselineMode": is_empty_baseline_mode()}


@router.post("/clear")
def clear_graph(request: ClearGraphRequest):
    allowed_phrases = {"清空全部图谱", "CLEAR ALL GRAPH DATA"}
    if not request.acknowledgeIrreversible or request.confirmation.strip() not in allowed_phrases:
        raise HTTPException(status_code=422, detail="请勾选不可撤销确认，并输入完整确认词")

    previous_state = load_graph_state()
    # Persist empty-baseline mode before the destructive query so a process
    # restart cannot unexpectedly repopulate the database after it is cleared.
    try:
        mark_graph_cleared()
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"无法保存空图谱状态，未执行清空：{exc}") from exc

    try:
        with driver.session() as neo_session:
            counts = _graph_counts(neo_session)
            neo_session.run("MATCH (n) DETACH DELETE n").consume()
    except Exception as exc:
        try:
            save_graph_state(previous_state)
        except OSError:
            pass
        raise HTTPException(status_code=503, detail=f"清空 Neo4j 图谱失败：{exc}") from exc

    try:
        mark_graph_cleared(nodes=counts["totalNodes"], relationships=counts["totalRelationships"])
    except OSError:
        # The pre-delete marker already guarantees empty-baseline behavior;
        # detailed counts are helpful metadata but are not required for safety.
        pass
    with _session_lock:
        _sessions.clear()
    _invalidate_graph_caches()
    return {
        "success": True,
        "deleted": counts,
        "emptyBaselineMode": True,
    }


@router.post("/apply")
def apply_import(request: ImportApplyRequest):
    with _session_lock:
        _purge_expired_sessions()
        session = _sessions.get(request.importId)
    if session is None:
        raise HTTPException(status_code=404, detail="导入分析已过期，请重新选择 CSV")
    selected = {name.strip() for name in request.selected if name.strip()}
    unknown = selected - set(session["candidates"])
    if unknown:
        raise HTTPException(status_code=422, detail=f"包含未知 CDO：{', '.join(sorted(unknown)[:10])}")
    if not selected:
        raise HTTPException(status_code=422, detail="请至少选择一个经过确认的业务对象")

    reviewed: set[str] = set(session["reviewed"])
    allowed_targets = reviewed | selected
    class_batch = []
    property_batch = []
    relationship_batch = []
    new_class_payloads = []
    imported_relationships = []
    seen_relationships: set[tuple[str, str, str]] = set()

    for class_name in sorted(selected, key=str.casefold):
        table = session["tables"][class_name]
        canonical = canonical_physical_fields(session["fields"].get(class_name, []), class_name)
        class_batch.append({"name": class_name, "cdoDefId": table.get("CDODefId", ""), "workspace": table.get("Workspace", "")})
        properties = [_property_definition(field, class_name) for field in canonical]
        for prop in properties:
            property_batch.append({"className": class_name, **prop})
        if class_name not in reviewed:
            new_class_payloads.append({
                "className": class_name,
                "chineseName": "",
                "description": "",
                "sourceCDODefId": table.get("CDODefId", ""),
                "properties": properties,
            })
        for field in canonical:
            target = field.get("FKTableName", "")
            if expected_type(field) != "Navigation" or not target or target not in allowed_targets:
                continue
            name = relation_name(normalize_field_name(field, class_name))
            key = (class_name, target, name)
            if key in seen_relationships:
                continue
            item = {
                "fromClass": class_name,
                "toClass": target,
                "relationName": name,
                "cardinality": "MANY_TO_ONE",
                "description": "",
            }
            relationship_batch.append(item)
            if class_name not in reviewed or target not in reviewed:
                imported_relationships.append(item)
            seen_relationships.add(key)

    try:
        with driver.session() as neo_session:
            neo_session.run("""
                UNWIND $batch AS item
                MERGE (c:OntologyClass {name: item.name})
                ON CREATE SET c.chineseName = '', c.description = '', c.layer = 'Config'
                SET c.sourceCDODefId = item.cdoDefId,
                    c.sourceWorkspace = item.workspace,
                    c.schemaSource = 'CSV',
                    c.schemaImportedAt = timestamp()
            """, batch=class_batch).consume()
            neo_session.run("""
                UNWIND $batch AS item
                MATCH (c:OntologyClass {name: item.className})
                MERGE (p:OntologyProperty {className: item.className, name: item.name})
                ON CREATE SET p.description = ''
                SET p.dataType = item.type,
                    p.required = coalesce(item.required, false),
                    p.sourceFieldId = item.sourceFieldId,
                    p.schemaSource = 'CSV',
                    p.schemaImportedAt = timestamp()
                MERGE (c)-[:HAS_PROPERTY]->(p)
            """, batch=property_batch).consume()
            neo_session.run("""
                UNWIND $batch AS item
                MATCH (source:OntologyClass {name: item.fromClass})
                MATCH (target:OntologyClass {name: item.toClass})
                MERGE (source)-[r:ONTOLOGY_RELATION {name: item.relationName}]->(target)
                ON CREATE SET r.description = ''
                SET r.cardinality = item.cardinality,
                    r.schemaSource = 'CSV',
                    r.schemaImportedAt = timestamp()
            """, batch=relationship_batch).consume()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"写入 Neo4j 失败：{exc}") from exc

    _write_imported_ontology(
        new_class_payloads,
        imported_relationships,
        allowed_class_names=reviewed | selected,
    )
    _write_manifest(
        selected,
        len(session["tables"]),
        reset=is_empty_baseline_mode() and not reviewed,
    )
    _invalidate_graph_caches()
    with _session_lock:
        _sessions.pop(request.importId, None)
    return {
        "success": True,
        "classes": len(class_batch),
        "newClasses": len(new_class_payloads),
        "properties": len(property_batch),
        "relationships": len(relationship_batch),
    }
