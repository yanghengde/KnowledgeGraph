"""Read-only natural-language assistant for the active Graph Studio graphmart.

The assistant deliberately keeps Graph Studio access outside the LLM.  The
model can propose a SPARQL SELECT statement, but this module validates and
executes it with a read-only HTTP request before asking the model to summarize
the returned evidence.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, AsyncIterator
from urllib.parse import quote

import requests
from openai import AsyncOpenAI

from src.graphstudio_sync.config import SyncSettings
from src.graphstudio_sync.deployment import deployment_status
from src.graphstudio_sync.repository import ControlPlaneRepository


_SCHEMA_TTL_SECONDS = 300
_SCHEMA_CACHE_PATH = Path(
    os.getenv(
        "MANUFACTURING_CHAT_SCHEMA_CACHE",
        Path(__file__).resolve().parents[2] / "data" / "manufacturing_chat_schema.json",
    )
)
_schema_lock = threading.Lock()
_schema_cache: tuple[str, float, list[dict[str, Any]]] | None = None
_llm_client: AsyncOpenAI | None = None

_PUBLISH_NAMESPACE = "https://opcenter.siemens.com/ontology/camstar/2607/publish#"
_SCHEMA_INVENTORY_QUESTION = re.compile(
    r"(?:有哪些|列出|当前|全部).*(?:对象类型|对象类|类和关系|类型和关系|本体关系|图谱结构)",
    re.IGNORECASE,
)

_FORBIDDEN_SPARQL = re.compile(
    r"\b(?:INSERT|DELETE|LOAD|CLEAR|CREATE|DROP|COPY|MOVE|ADD|SERVICE|USING)\b",
    re.IGNORECASE,
)
_SELECT_START = re.compile(
    r"^(?:\s*PREFIX\s+[^\n]+\s*)*(?:\s*BASE\s+[^\n]+\s*)*\s*SELECT\b",
    re.IGNORECASE,
)


class GraphStudioAssistantError(RuntimeError):
    """A safe, user-displayable Graph Studio assistant error."""


def _runtime_cache_key(snapshot: dict[str, Any]) -> str:
    return "graphstudio-schema-v2::" + "::".join(str(snapshot.get(key) or "") for key in (
        "profileKey", "routeKey", "deploymentId", "ontologyReleaseId",
        "curatedReleaseId", "artifactHash",
    ))


def resolve_runtime_snapshot() -> dict[str, Any]:
    """Resolve the exact active Graph Studio deployment used by one answer."""
    profile_key = os.getenv(
        "MANUFACTURING_CHAT_PROFILE_KEY", "opcenter2607-core",
    ).strip() or "opcenter2607-core"
    route_key = os.getenv("MANUFACTURING_CHAT_ROUTE_KEY", "").strip()
    try:
        settings = SyncSettings.from_env()
        repository = ControlPlaneRepository(settings)
        status = deployment_status(repository, profile_key)
    except Exception as exc:
        raise GraphStudioAssistantError(
            f"无法解析制造问答活动发布版本：{exc}"
        ) from exc

    active_data = status.get("activeCuratedRelease") or {}
    active_ontology = status.get("activeOntologyRelease") or {}
    if not active_data or not active_ontology:
        raise GraphStudioAssistantError("制造问答没有可用的活动数据版本或本体版本")

    routes = {item["route_key"]: item for item in status.get("routes", [])}
    candidates = [
        item for item in status.get("deployments", [])
        if item.get("status") == "active"
        and str(item.get("curated_release_id")) == str(active_data.get("release_id"))
        and str(item.get("ontology_release_id")) == str(active_ontology.get("ontology_release_id"))
        and (not route_key or item.get("route_key") == route_key)
    ]
    if not candidates:
        detail = f"（路由 {route_key}）" if route_key else ""
        raise GraphStudioAssistantError(
            "当前活动数据/本体组合尚未成功发布到 Graph Studio" + detail
        )
    deployment = candidates[0]
    route = routes.get(deployment.get("route_key"), {})
    validation_plan = dict(deployment.get("validation_plan") or {})
    graphmart_uri = str(
        validation_plan.get("graphmartUri")
        or route.get("graphmart_uri")
        or settings.graphmart_uri
    )
    model_uri = str(validation_plan.get("modelUri") or "")
    if not graphmart_uri or not model_uri or not deployment.get("layer_uri"):
        raise GraphStudioAssistantError("活动部署缺少 Graphmart、Model 或 Layer 版本证据")
    snapshot = {
        "profileKey": profile_key,
        "routeKey": deployment.get("route_key"),
        "environmentKey": deployment.get("environment_key"),
        "deploymentId": str(deployment["deployment_id"]),
        "ontologyReleaseId": str(active_ontology["ontology_release_id"]),
        "ontologyReleaseNo": int(active_ontology["release_no"]),
        "ontologyClassCount": int(active_ontology.get("class_count") or 0),
        "ontologyRelationshipCount": int(active_ontology.get("relationship_count") or 0),
        "curatedReleaseId": str(active_data["release_id"]),
        "curatedReleaseNo": int(active_data["release_no"]),
        "objectCount": int(active_data.get("object_count") or 0),
        "relationshipCount": int(active_data.get("relationship_count") or 0),
        "graphmartUri": graphmart_uri,
        "modelUri": model_uri,
        "layerUri": str(deployment["layer_uri"]),
        "artifactHash": str(deployment.get("artifact_hash") or ""),
        "finishedAt": str(deployment.get("finished_at") or ""),
    }
    snapshot["cacheKey"] = _runtime_cache_key(snapshot)
    return snapshot


def _get_llm() -> AsyncOpenAI:
    global _llm_client
    if _llm_client is None:
        _llm_client = AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            timeout=float(os.getenv("LLM_TIMEOUT", "120")),
        )
    return _llm_client


def _configuration() -> dict[str, str]:
    from src.graphstudio_sync.config import normalize_graphstudio_url
    values = {
        "base_url": os.getenv("GRAPHSTUDIO_BASE_URL", "").strip().rstrip("/"),
        "username": os.getenv("GRAPHSTUDIO_USER", "").strip(),
        "password": os.getenv("GRAPHSTUDIO_PASSWORD", ""),
        "graphmart_uri": os.getenv("GRAPHSTUDIO_GRAPHMART_URI", "").strip(),
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise GraphStudioAssistantError(
            "制造知识问答尚未完成 Graph Studio 连接配置："
            + "、".join(missing)
        )
    values["base_url"] = normalize_graphstudio_url(values["base_url"])
    return values


def _sparql_endpoint(
    config: dict[str, str], graphmart_uri: str | None = None,
) -> str:
    encoded = quote(graphmart_uri or config["graphmart_uri"], safe="")
    return f"{config['base_url']}/sparql/graphmart/{encoded}"


def _request_sparql(
    query: str,
    *,
    timeout: float = 45,
    runtime_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = _configuration()
    response = None
    last_error: requests.RequestException | None = None
    for attempt in range(4):
        session = None
        try:
            from src.graphstudio_sync.transport import configure_graphstudio_tls
            fingerprint = os.getenv("GRAPHSTUDIO_TLS_FINGERPRINT", "").strip()
            session = configure_graphstudio_tls(requests.Session(), config["base_url"], fingerprint) if fingerprint else None
            response = (session.post if session else requests.post)(
                _sparql_endpoint(
                    config,
                    str(runtime_snapshot.get("graphmartUri"))
                    if runtime_snapshot else None,
                ),
                data={"query": query},
                headers={
                    "Accept": "application/sparql-results+json",
                    "User-Agent": "Opcenter-Manufacturing-QA/1.0",
                },
                auth=(config["username"], config["password"]),
                timeout=timeout,
            )
            if response.status_code not in {502, 503, 504}:
                break
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_error = exc
        finally:
            if session:
                session.close()
        if attempt < 3:
            time.sleep(0.35 * (2**attempt))
    if response is None:
        raise GraphStudioAssistantError(
            "Graph Studio 查询连接被远端中断，已自动重试 4 次。"
            "请稍后重试或检查 Graph Studio 查询服务状态。"
        ) from last_error
    if not response.ok:
        detail = response.text.strip().replace("\n", " ")[:500]
        raise GraphStudioAssistantError(
            f"Graph Studio 查询失败（HTTP {response.status_code}）：{detail}"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise GraphStudioAssistantError("Graph Studio 返回了无法识别的查询结果") from exc
    if not isinstance(payload, dict):
        raise GraphStudioAssistantError("Graph Studio 查询结果格式不正确")
    return payload


def _binding_rows(payload: dict[str, Any]) -> list[dict[str, str]]:
    bindings = ((payload.get("results") or {}).get("bindings") or [])
    rows: list[dict[str, str]] = []
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        rows.append({
            str(key): str(value.get("value", ""))
            for key, value in binding.items()
            if isinstance(value, dict)
        })
    return rows


def _runtime_layer(runtime_snapshot: dict[str, Any]) -> str:
    layer = str(runtime_snapshot.get("layerUri") or "")
    if not layer.startswith(("http://", "https://")) or re.search(r'[<>\s"{}]', layer):
        raise GraphStudioAssistantError("活动部署缺少有效的数据层地址")
    return layer


def _instance_counts(runtime_snapshot: dict[str, Any]) -> dict[str, int]:
    query = f"""
        SELECT ?class (COUNT(DISTINCT ?instance) AS ?instanceCount) WHERE {{
          GRAPH <{_runtime_layer(runtime_snapshot)}> {{ ?instance a ?class . }}
        }}
        GROUP BY ?class
        LIMIT 600
    """
    try:
        rows = _binding_rows(_request_sparql(
            query, runtime_snapshot=runtime_snapshot,
        ))
    except GraphStudioAssistantError:
        return {}
    counts: dict[str, int] = {}
    for row in rows:
        class_uri = row.get("class", "")
        if class_uri.startswith(_PUBLISH_NAMESPACE):
            try:
                counts[class_uri] = int(row.get("instanceCount", "0"))
            except ValueError:
                counts[class_uri] = 0
    return counts


def _relationship_counts(
    runtime_snapshot: dict[str, Any],
) -> dict[str, int] | None:
    """Count materialized publish relationships in the active Graphmart."""
    query = f"""
        SELECT ?relationship (COUNT(*) AS ?relationshipCount) WHERE {{
          GRAPH <{_runtime_layer(runtime_snapshot)}> {{ ?source ?relationship ?target . }}
          FILTER(STRSTARTS(
            STR(?relationship),
            "{_PUBLISH_NAMESPACE}REL_"
          ))
        }}
        GROUP BY ?relationship
        LIMIT 600
    """
    try:
        rows = _binding_rows(_request_sparql(
            query, runtime_snapshot=runtime_snapshot,
        ))
    except GraphStudioAssistantError:
        # Preserve ontology-only planning when the count probe is temporarily
        # unavailable; an unavailable probe is not evidence of zero edges.
        return None
    counts: dict[str, int] = {}
    for row in rows:
        relationship_uri = row.get("relationship", "")
        if relationship_uri.startswith(_PUBLISH_NAMESPACE + "REL_"):
            try:
                counts[relationship_uri] = int(
                    row.get("relationshipCount", "0")
                )
            except ValueError:
                counts[relationship_uri] = 0
    return counts


def _schema_rows_from_release(
    model: dict[str, Any],
    instance_counts: dict[str, int],
    relationship_counts: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in model.get("classes", []):
        ontology_class = entry.get("class") or {}
        target_name = str(ontology_class.get("targetName") or "")
        if not target_name:
            continue
        class_uri = _PUBLISH_NAMESPACE + target_name
        base = {
            "class": class_uri,
            "classLabel": str(ontology_class.get("label") or target_name),
            "role": str(ontology_class.get("role") or "context"),
            "instanceCount": instance_counts.get(class_uri, 0),
        }
        rows.append({**base, "property": "", "valueKind": "对象类型"})
        for prop in entry.get("properties", []):
            if not prop.get("published"):
                continue
            rows.append({
                **base,
                "property": f"{_PUBLISH_NAMESPACE}{target_name}_{prop['targetName']}",
                "propertyLabel": str(prop.get("targetName") or ""),
                "dataType": str(prop.get("dataType") or "String"),
                "valueKind": "属性",
            })
    for entry in model.get("relationships", []):
        relation = entry.get("relation") or {}
        if relation.get("usage") != "published_link":
            continue
        source = entry.get("source") or {}
        target = entry.get("target") or {}
        source_name = str(source.get("targetName") or "")
        target_name = str(target.get("targetName") or "")
        relation_name = str(relation.get("targetName") or "")
        if not source_name or not target_name or not relation_name:
            continue
        class_uri = _PUBLISH_NAMESPACE + source_name
        relationship_uri = _PUBLISH_NAMESPACE + "REL_" + relation_name
        rows.append({
            "class": class_uri,
            "classLabel": str(source.get("label") or source_name),
            "role": str(source.get("role") or "context"),
            "instanceCount": instance_counts.get(class_uri, 0),
            "property": relationship_uri,
            "propertyLabel": relation_name,
            "targetClass": _PUBLISH_NAMESPACE + target_name,
            "valueKind": "关系",
            "questionEnabled": relation.get("questionEnabled", True) is not False,
            "relationshipCount": (
                relationship_counts.get(relationship_uri, 0)
                if relationship_counts is not None else None
            ),
        })
    return rows


def _discover_schema_uncached(
    runtime_snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
    # The published layer contains both the immutable model and business data.
    # The modeling Neo4j service is not a runtime dependency for answers.
    layer = _runtime_layer(runtime_snapshot)
    query = f"""
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX pub: <{_PUBLISH_NAMESPACE}>
        SELECT DISTINCT ?class ?classLabel ?property ?propertyLabel
                        ?dataType ?targetClass ?valueKind ?role ?questionEnabled
        WHERE {{ GRAPH <{layer}> {{
          ?class a owl:Class .
          FILTER(STRSTARTS(STR(?class), "{_PUBLISH_NAMESPACE}"))
          OPTIONAL {{ ?class rdfs:label ?classLabel }}
          OPTIONAL {{ ?class pub:role ?role }}
          {{ BIND("" AS ?property) BIND("对象类型" AS ?valueKind) }}
          UNION {{
            ?property a owl:DatatypeProperty ; rdfs:domain ?class .
            OPTIONAL {{ ?property rdfs:label ?propertyLabel }}
            OPTIONAL {{ ?property rdfs:range ?dataType }}
            BIND("属性" AS ?valueKind)
          }}
          UNION {{
            ?property a owl:ObjectProperty ; rdfs:domain ?class ; rdfs:range ?targetClass .
            OPTIONAL {{ ?property rdfs:label ?propertyLabel }}
            OPTIONAL {{ ?property pub:questionEnabled ?questionEnabled }}
            BIND("关系" AS ?valueKind)
          }}
        }} }} ORDER BY ?class ?valueKind ?property LIMIT 10001
    """
    rows = _binding_rows(_request_sparql(query, runtime_snapshot=runtime_snapshot))
    if not rows or len(rows) > 10000:
        raise GraphStudioAssistantError(
            "Graph Studio 活动数据层未返回完整的已发布本体，请检查模型发布状态"
        )
    instance_counts = _instance_counts(runtime_snapshot)
    relationship_counts = _relationship_counts(runtime_snapshot)
    result = []
    for row in rows:
        entry = {**row, "role": row.get("role") or "context",
                 "instanceCount": instance_counts.get(row["class"], 0)}
        if row.get("valueKind") == "关系":
            entry["questionEnabled"] = row.get("questionEnabled", "true").lower() not in {"false", "0"}
            entry["relationshipCount"] = (
                relationship_counts.get(row["property"], 0)
                if relationship_counts is not None else None
            )
        result.append(entry)
    return result


def _load_persisted_schema(
    runtime_snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
    try:
        payload = json.loads(_SCHEMA_CACHE_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return []
    if payload.get("runtime_key") != runtime_snapshot.get("cacheKey"):
        return []
    rows = payload.get("rows")
    return rows if isinstance(rows, list) else []


def _persist_schema(
    rows: list[dict[str, Any]], runtime_snapshot: dict[str, Any],
) -> None:
    try:
        _SCHEMA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SCHEMA_CACHE_PATH.write_text(
            json.dumps(
                {
                    "runtime_key": runtime_snapshot["cacheKey"],
                    "graphmart_uri": runtime_snapshot["graphmartUri"],
                    "deployment_id": runtime_snapshot["deploymentId"],
                    "ontology_release_id": runtime_snapshot["ontologyReleaseId"],
                    "curated_release_id": runtime_snapshot["curatedReleaseId"],
                    "saved_at": time.time(),
                    "rows": rows,
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def discover_schema(
    runtime_snapshot: dict[str, Any] | None = None,
    *,
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    global _schema_cache
    runtime_snapshot = runtime_snapshot or resolve_runtime_snapshot()
    runtime_key = str(runtime_snapshot["cacheKey"])
    now = time.monotonic()
    if (
        not force_refresh and _schema_cache
        and _schema_cache[0] == runtime_key
        and now - _schema_cache[1] < _SCHEMA_TTL_SECONDS
    ):
        return _schema_cache[2]
    with _schema_lock:
        now = time.monotonic()
        if (
            not force_refresh and _schema_cache
            and _schema_cache[0] == runtime_key
            and now - _schema_cache[1] < _SCHEMA_TTL_SECONDS
        ):
            return _schema_cache[2]
        try:
            rows = _discover_schema_uncached(runtime_snapshot)
            _persist_schema(rows, runtime_snapshot)
        except GraphStudioAssistantError:
            rows = _load_persisted_schema(runtime_snapshot)
            if not rows:
                raise
        _schema_cache = (runtime_key, now, rows)
        return rows


def _local_name(uri: str) -> str:
    return uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _schema_context(rows: list[dict[str, Any]]) -> str:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        class_uri = row.get("class", "")
        if not class_uri:
            continue
        class_text = f"{_local_name(class_uri)} <{class_uri}>"
        group = grouped.setdefault(class_text, {
            "role": row.get("role", "context"),
            "instanceCount": int(row.get("instanceCount") or 0),
            "properties": [],
            "relationships": [],
            "disabledRelationships": [],
        })
        property_uri = row.get("property", "")
        if not property_uri:
            continue
        if row.get("valueKind") == "关系":
            count = row.get("relationshipCount")
            enabled = row.get("questionEnabled", True) is not False
            executable = enabled and (count is None or int(count) > 0)
            relationship_text = (
                f"{row.get('propertyLabel') or _local_name(property_uri)} "
                f"<{property_uri}> → {_local_name(str(row.get('targetClass') or ''))}；"
                f"当前关系实例数：{'未知' if count is None else int(count)}；"
                f"问答可用：{'是' if executable else '否'}"
            )
            target_group = "relationships" if executable else "disabledRelationships"
            if relationship_text not in group[target_group]:
                group[target_group].append(relationship_text)
        else:
            property_text = (
                f"{row.get('propertyLabel') or _local_name(property_uri)} "
                f"<{property_uri}>（{row.get('dataType', 'String')}）"
            )
            if property_text not in group["properties"]:
                group["properties"].append(property_text)
    if not grouped:
        return "当前活动本体没有可查询的发布对象。"
    lines = []
    for class_text, group in list(grouped.items())[:120]:
        lines.append(
            f"- 类：{class_text}；角色：{group['role']}；"
            f"当前实例数：{group['instanceCount']}"
        )
        if group["properties"]:
            lines.append("  属性：" + "；".join(group["properties"][:80]))
        if group["relationships"]:
            lines.append(
                "  可执行关系（查询连接只能使用这些关系）："
                + "；".join(group["relationships"][:80])
            )
        if group["disabledRelationships"]:
            lines.append(
                "  禁止用于查询连接的关系："
                + "；".join(group["disabledRelationships"][:80])
            )
    return "\n".join(lines)


def _schema_inventory_sparql(rows: list[dict[str, Any]]) -> str:
    class_uris = sorted({str(row.get("class") or "") for row in rows if row.get("class")})
    values = " ".join(f"<{uri}>" for uri in class_uris)
    return validate_readonly_sparql(f"""
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?class ?label ?relation ?targetClass WHERE {{
          VALUES ?class {{ {values} }}
          ?class a owl:Class .
          OPTIONAL {{ ?class rdfs:label ?label . }}
          OPTIONAL {{
            ?relation a owl:ObjectProperty ;
                      rdfs:domain ?class ;
                      rdfs:range ?targetClass .
          }}
        }}
        ORDER BY ?class ?relation ?targetClass
        LIMIT 500
    """)


def _history_for_model(history: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    retained: list[dict[str, str]] = []
    total = 0
    for message in reversed((history or [])[-24:]):
        role = message.get("role")
        content = str(message.get("content") or "")
        if role not in {"user", "assistant"} or not content:
            continue
        if retained and total + len(content) > 18000:
            break
        retained.append({"role": role, "content": content})
        total += len(content)
    return list(reversed(retained))


def _extract_json(text: str) -> dict[str, Any]:
    candidate = (text or "").strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
        candidate = re.sub(r"\s*```$", "", candidate)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", candidate)
        if not match:
            raise GraphStudioAssistantError("模型没有生成可验证的查询计划")
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise GraphStudioAssistantError("模型生成的查询计划格式不正确") from exc
    if not isinstance(payload, dict):
        raise GraphStudioAssistantError("模型生成的查询计划格式不正确")
    return payload


def validate_readonly_sparql(query: str) -> str:
    normalized = (query or "").strip()
    normalized = re.sub(r"^```(?:sparql)?\s*", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s*```$", "", normalized).strip().rstrip(";")
    if not _SELECT_START.search(normalized):
        raise GraphStudioAssistantError("安全校验未通过：仅允许 SPARQL SELECT 查询")
    if _FORBIDDEN_SPARQL.search(normalized):
        raise GraphStudioAssistantError("安全校验未通过：查询包含写入或外部访问操作")
    if len(normalized) > 12000:
        raise GraphStudioAssistantError("安全校验未通过：查询长度超过限制")
    if not re.search(r"\bLIMIT\s+\d+", normalized, re.IGNORECASE):
        normalized += "\nLIMIT 100"
    return normalized


async def _plan_query(
    question: str,
    history: list[dict[str, Any]] | None,
    schema_context: str,
) -> tuple[str, str]:
    client = _get_llm()
    model = os.getenv("LLM_MODEL", "deepseek-v4-flash")
    system = (
        "你是工业制造知识图谱的只读查询规划器。根据提供的 Graph Studio 实际类和属性，"
        "把用户问题转换为一条 SPARQL SELECT。只能使用上下文中存在的完整 URI，不得猜测字段。"
        "关系连接只能使用标记为‘问答可用：是’的可执行关系；标记为‘问答可用：否’的关系即使路径更短也禁止使用。"
        "对象之间必须使用 REL_ 开头的关系 URI连接，Navigation/ID 普通属性不得代替对象关系。"
        "禁止 INSERT、DELETE、LOAD、CLEAR、CREATE、DROP、COPY、MOVE、ADD 和 SERVICE。"
        "明细查询最多返回100条。输出严格 JSON："
        '{"sparql":"...","understanding":"一句中文查询理解"}。'
        "如果数据模型不足以回答，也输出安全的探查 SELECT，并在 understanding 中说明限制。\n\n"
        f"当前 Graphmart 实际结构：\n{schema_context}"
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(_history_for_model(history))
    messages.append({"role": "user", "content": question})
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=2200,
        )
    except Exception:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
            max_tokens=2200,
        )
    payload = _extract_json(response.choices[0].message.content or "")
    return validate_readonly_sparql(str(payload.get("sparql") or "")), str(
        payload.get("understanding") or "制造知识图谱查询"
    )


async def _select_saved_query(
    question: str,
    history: list[dict[str, Any]] | None,
    queries: list[dict[str, str]],
) -> tuple[dict[str, str] | None, str]:
    """Select a governed saved Query only when it can directly support the question."""
    if not queries:
        return None, "当前没有可用的已保存 Query"
    candidates = [item for item in queries if item.get("compatible", True)][:40]
    if not candidates:
        return None, "当前已保存 Query 均与活动本体版本不兼容"
    catalog = [
        {
            "uri": item["uri"],
            "title": item["title"],
            "description": item.get("description", ""),
            "sparql": item.get("sparql", "")[:1800],
        }
        for item in candidates
    ]
    client = _get_llm()
    model = os.getenv("LLM_MODEL", "deepseek-v4-flash")
    messages = [{
        "role": "system",
        "content": (
            "你是制造知识问答的 Query 路由器。判断用户问题能否由某一条 Graph Studio 已保存 Query "
            "直接提供主要证据。优先选语义最精确的 Query；不要因为只沾边就勉强选择。"
            "如果都不适合，query_uri 必须为 null，以便系统生成动态只读查询。"
            "只能返回目录中真实存在的 URI。输出严格 JSON："
            '{"query_uri":"URI或null","reason":"一句中文理由"}。\n\n'
            f"Query 目录：\n{json.dumps(catalog, ensure_ascii=False)}"
        ),
    }]
    messages.extend(_history_for_model(history)[-6:])
    messages.append({"role": "user", "content": question})
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=500,
        )
    except Exception:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
            max_tokens=500,
        )
    selection = _extract_json(response.choices[0].message.content or "")
    selected_uri = selection.get("query_uri")
    selected = next((item for item in candidates if item["uri"] == selected_uri), None)
    return selected, str(selection.get("reason") or "Query 能力匹配")


async def graphstudio_query_stream(
    question: str,
    history: list[dict[str, Any]] | None = None,
    *,
    query_mode: str = "auto",
    query_uri: str | None = None,
    runtime_snapshot: dict[str, Any] | None = None,
) -> AsyncIterator[str | dict[str, Any]]:
    if not os.getenv("DEEPSEEK_API_KEY", "").strip():
        raise GraphStudioAssistantError("尚未配置 DEEPSEEK_API_KEY，无法启动制造知识问答")

    runtime_snapshot = runtime_snapshot or await asyncio.to_thread(
        resolve_runtime_snapshot
    )
    yield {
        "type": "status",
        "content": (
            f"已连接本体 R{runtime_snapshot['ontologyReleaseNo']} / "
            f"数据 R{runtime_snapshot['curatedReleaseNo']}，正在读取版本化语义契约…"
        ),
    }
    schema_rows = await asyncio.to_thread(discover_schema, runtime_snapshot)
    schema_context = _schema_context(schema_rows)
    if not schema_rows:
        raise GraphStudioAssistantError("当前活动本体没有可供问答的发布对象")

    saved_query = None
    routing_reason = ""
    schema_inventory = bool(_SCHEMA_INVENTORY_QUESTION.search(question))
    if query_mode != "dynamic" and not schema_inventory:
        yield {"type": "status", "content": "正在匹配 Graph Studio 已保存 Query…"}
        try:
            from src.qa.graphstudio_saved_queries import list_saved_queries

            saved_queries = await asyncio.to_thread(
                list_saved_queries, runtime_snapshot=runtime_snapshot,
            )
            if query_uri:
                saved_query = next(
                    (
                        item for item in saved_queries
                        if item["uri"] == query_uri and item.get("compatible", True)
                    ),
                    None,
                )
                if saved_query is None:
                    raise GraphStudioAssistantError(
                        "指定的 Graph Studio Query 不存在、不安全或与当前本体版本不兼容"
                    )
                routing_reason = "用户指定使用该 Query"
            else:
                saved_query, routing_reason = await _select_saved_query(
                    question, history, saved_queries
                )
        except GraphStudioAssistantError:
            if query_uri:
                raise
            saved_query = None

    if schema_inventory:
        sparql = _schema_inventory_sparql(schema_rows)
        understanding = (
            f"读取活动本体 R{runtime_snapshot['ontologyReleaseNo']} 的完整对象与关系定义"
        )
        yield {"type": "status", "content": "正在核对活动本体中的全部对象和关系…"}
    elif saved_query:
        sparql = validate_readonly_sparql(saved_query["sparql"])
        understanding = f"使用已保存 Query：{saved_query['title']}（{routing_reason}）"
        yield {
            "type": "status",
            "content": f"已匹配 Query「{saved_query['title']}」，正在执行…",
        }
    else:
        yield {"type": "status", "content": "正在生成并校验动态只读查询计划…"}
        sparql, understanding = await _plan_query(question, history, schema_context)

    yield {"type": "status", "content": "正在查询 Graph Studio 当前发布数据…"}
    result = await asyncio.to_thread(
        _request_sparql, sparql, runtime_snapshot=runtime_snapshot,
    )
    rows = _binding_rows(result)
    variables = ((result.get("head") or {}).get("vars") or [])
    evidence = {
        "runtime": runtime_snapshot,
        "variables": variables,
        "rowCount": len(rows),
        "rows": rows[:100],
    }
    evidence_text = json.dumps(evidence, ensure_ascii=False)
    if len(evidence_text) > 32000:
        evidence["rows"] = rows[:30]
        evidence["truncated"] = True
        evidence_text = json.dumps(evidence, ensure_ascii=False)

    client = _get_llm()
    model = os.getenv("LLM_MODEL", "deepseek-v4-flash")
    messages = [{
        "role": "system",
        "content": (
            "你是 Opcenter 制造知识问答助手。只能根据本次 Graph Studio 查询证据回答，"
            "不得补充证据中不存在的订单、产品、状态、数量或日期。使用简洁专业的中文，"
            "先给结论，再给必要明细。没有结果时明确说当前发布数据未找到记录。"
            "对于 URI，优先显示 # 或最后一个 / 后的业务标识。"
        ),
    }]
    messages.extend(_history_for_model(history))
    messages.append({
        "role": "user",
        "content": (
            f"用户问题：{question}\n"
            f"查询理解：{understanding}\n"
            f"Graphmart：{runtime_snapshot['graphmartUri']}\n"
            f"活动本体：R{runtime_snapshot['ontologyReleaseNo']}\n"
            f"活动数据：R{runtime_snapshot['curatedReleaseNo']}\n"
            f"只读SPARQL：\n{sparql}\n"
            f"查询证据JSON：\n{evidence_text}"
        ),
    })

    yield {"type": "status", "content": "正在根据查询证据组织回答…"}
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=0.1,
        max_tokens=3000,
    )
    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

    query_source = (
        f"Graph Studio 已保存 Query「{saved_query['title']}」"
        if saved_query else (
            "活动本体清单查询" if schema_inventory
            else "动态生成并安全校验的只读查询"
        )
    )
    yield (
        "\n\n### 查询依据\n"
        f"- 发布版本：本体 R{runtime_snapshot['ontologyReleaseNo']} · "
        f"数据 R{runtime_snapshot['curatedReleaseNo']}\n"
        f"- 部署：`{runtime_snapshot['deploymentId'][:8]}` · "
        f"Layer `{_local_name(runtime_snapshot['layerUri'])}`\n"
        f"- 数据源：当前 Graphmart（返回 {len(rows)} 条）\n"
        f"- 查询方式：{query_source}\n\n"
        f"```sparql\n{sparql}\n```"
    )


def graphstudio_connection_status(*, force_refresh: bool = False) -> dict[str, Any]:
    llm_configured = bool(os.getenv("DEEPSEEK_API_KEY", "").strip())
    try:
        config = _configuration()
        runtime_snapshot = resolve_runtime_snapshot()
    except GraphStudioAssistantError as exc:
        return {
            "status": "not_configured",
            "graphstudio": "未配置",
            "llm": "已配置" if llm_configured else "未配置",
            "detail": str(exc),
        }
    try:
        payload = _request_sparql(
            "SELECT (COUNT(*) AS ?statementCount) WHERE { ?s ?p ?o }",
            timeout=15,
            runtime_snapshot=runtime_snapshot,
        )
        schema_rows = discover_schema(
            runtime_snapshot, force_refresh=force_refresh,
        )
        rows = _binding_rows(payload)
        statement_count = int(rows[0].get("statementCount", "0")) if rows else 0
        graphstudio = "在线"
        status = "ready" if llm_configured else "llm_missing"
        detail = (
            f"制造知识问答已就绪 · 本体 R{runtime_snapshot['ontologyReleaseNo']} · "
            f"数据 R{runtime_snapshot['curatedReleaseNo']} · "
            f"{runtime_snapshot['ontologyClassCount']} 类 / "
            f"{runtime_snapshot['ontologyRelationshipCount']} 关系 · "
            f"{statement_count:,} 条图谱语句"
            if llm_configured
            else "Graph Studio 在线，但 DeepSeek 未配置"
        )
    except (requests.RequestException, GraphStudioAssistantError, ValueError) as exc:
        graphstudio = "离线"
        status = "unavailable"
        detail = f"Graph Studio 连接失败：{exc}"
    return {
        "status": status,
        "graphstudio": graphstudio,
        "llm": "已配置" if llm_configured else "未配置",
        "graphmart_uri": runtime_snapshot.get("graphmartUri", config["graphmart_uri"]),
        "runtime": runtime_snapshot,
        "schema_rows": len(schema_rows) if status == "ready" else 0,
        "detail": detail,
    }
