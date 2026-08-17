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
from typing import Any, AsyncIterator
from urllib.parse import quote

import requests
from openai import AsyncOpenAI


_SCHEMA_TTL_SECONDS = 300
_schema_lock = threading.Lock()
_schema_cache: tuple[float, list[dict[str, str]]] | None = None
_llm_client: AsyncOpenAI | None = None

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
    return values


def _sparql_endpoint(config: dict[str, str]) -> str:
    encoded = quote(config["graphmart_uri"], safe="")
    return f"{config['base_url']}/sparql/graphmart/{encoded}"


def _request_sparql(query: str, *, timeout: float = 45) -> dict[str, Any]:
    config = _configuration()
    response = requests.post(
        _sparql_endpoint(config),
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        auth=(config["username"], config["password"]),
        timeout=timeout,
    )
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


def _discover_schema_uncached() -> list[dict[str, str]]:
    query = """
        SELECT DISTINCT ?class ?property ?valueKind WHERE {
          ?instance a ?class .
          OPTIONAL {
            ?instance ?property ?value .
            FILTER(?property != <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>)
            BIND(IF(isIRI(?value), "资源关联", "数据属性") AS ?valueKind)
          }
        }
        ORDER BY ?class ?property
        LIMIT 600
    """
    return _binding_rows(_request_sparql(query))


def discover_schema() -> list[dict[str, str]]:
    global _schema_cache
    now = time.monotonic()
    if _schema_cache and now - _schema_cache[0] < _SCHEMA_TTL_SECONDS:
        return _schema_cache[1]
    with _schema_lock:
        now = time.monotonic()
        if _schema_cache and now - _schema_cache[0] < _SCHEMA_TTL_SECONDS:
            return _schema_cache[1]
        rows = _discover_schema_uncached()
        _schema_cache = (now, rows)
        return rows


def _local_name(uri: str) -> str:
    return uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _schema_context(rows: list[dict[str, str]]) -> str:
    grouped: dict[str, list[str]] = {}
    for row in rows:
        class_uri = row.get("class", "")
        if not class_uri:
            continue
        class_text = f"{_local_name(class_uri)} <{class_uri}>"
        properties = grouped.setdefault(class_text, [])
        property_uri = row.get("property", "")
        if property_uri:
            property_text = (
                f"{_local_name(property_uri)} <{property_uri}>"
                f"（{row.get('valueKind', '属性')}）"
            )
            if property_text not in properties:
                properties.append(property_text)
    if not grouped:
        return "当前 Graphmart 未发现可查询的实例类型。"
    lines = []
    for class_text, properties in list(grouped.items())[:120]:
        lines.append(f"- 类：{class_text}")
        if properties:
            lines.append("  属性：" + "；".join(properties[:80]))
    return "\n".join(lines)


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


async def graphstudio_query_stream(
    question: str,
    history: list[dict[str, Any]] | None = None,
) -> AsyncIterator[str | dict[str, str]]:
    if not os.getenv("DEEPSEEK_API_KEY", "").strip():
        raise GraphStudioAssistantError("尚未配置 DEEPSEEK_API_KEY，无法启动制造知识问答")

    yield {"type": "status", "content": "正在读取当前 Graphmart 语义结构…"}
    schema_rows = await asyncio.to_thread(discover_schema)
    schema_context = _schema_context(schema_rows)
    if not schema_rows:
        raise GraphStudioAssistantError("当前 Graphmart 没有可供问答的实例数据")

    yield {"type": "status", "content": "正在生成并校验只读查询计划…"}
    sparql, understanding = await _plan_query(question, history, schema_context)

    yield {"type": "status", "content": "正在查询 Graph Studio 当前发布数据…"}
    result = await asyncio.to_thread(_request_sparql, sparql)
    rows = _binding_rows(result)
    variables = ((result.get("head") or {}).get("vars") or [])
    evidence = {
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
    config = _configuration()
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
            f"Graphmart：{config['graphmart_uri']}\n"
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

    yield (
        "\n\n### 查询依据\n"
        f"- 数据源：当前 Graphmart（返回 {len(rows)} 条）\n"
        "- 查询方式：经安全校验的只读 SPARQL SELECT\n\n"
        f"```sparql\n{sparql}\n```"
    )


def graphstudio_connection_status() -> dict[str, Any]:
    llm_configured = bool(os.getenv("DEEPSEEK_API_KEY", "").strip())
    try:
        config = _configuration()
    except GraphStudioAssistantError as exc:
        return {
            "status": "not_configured",
            "graphstudio": "未配置",
            "llm": "已配置" if llm_configured else "未配置",
            "detail": str(exc),
        }
    encoded = quote(config["graphmart_uri"], safe="")
    try:
        response = requests.get(
            f"{config['base_url']}/api/graphmarts/{encoded}/status",
            params={"detail": "false"},
            auth=(config["username"], config["password"]),
            timeout=8,
        )
        response.raise_for_status()
        graphstudio = "在线"
        status = "ready" if llm_configured else "llm_missing"
        detail = "制造知识问答已就绪" if llm_configured else "Graph Studio 在线，但 DeepSeek 未配置"
    except requests.RequestException as exc:
        graphstudio = "离线"
        status = "unavailable"
        detail = f"Graph Studio 连接失败：{exc}"
    return {
        "status": status,
        "graphstudio": graphstudio,
        "llm": "已配置" if llm_configured else "未配置",
        "graphmart_uri": config["graphmart_uri"],
        "detail": detail,
    }
