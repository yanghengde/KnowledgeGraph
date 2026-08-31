"""Graph Studio 2026.1+ REST API compatibility and readiness checks."""

from __future__ import annotations

import re
from typing import Any

import requests


SUPPORTED_PRODUCT_VERSION = (2026, 1)
SUPPORTED_API_VERSION = (6, 3)
_VERSION_PATTERN = re.compile(r"\b(?:20\d{2}|\d+)\.\d+(?:\.\d+)?\b")


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def _version_from_payload(payload: Any) -> str | None:
    if isinstance(payload, str):
        match = _VERSION_PATTERN.search(payload)
        return match.group(0) if match else None
    if isinstance(payload, dict):
        for key in ("version", "serverVersion", "productVersion", "apiVersion"):
            found = _version_from_payload(payload.get(key))
            if found:
                return found
        for value in payload.values():
            found = _version_from_payload(value)
            if found:
                return found
    return None


def require_graphstudio_2026_1_ready(
    session: requests.Session,
    base_url: str,
) -> dict[str, str]:
    """Require a ready Graph Studio 2026.1+/REST API 6.3+ server."""
    response = session.get(
        f"{base_url.rstrip('/')}/util/serverVersion",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(
            f"Graph Studio 版本检查失败：HTTP {response.status_code}: {response.text[:500]}"
        )
    try:
        payload: Any = response.json()
    except ValueError:
        payload = response.text
    text = str(payload)
    if "still starting" in text.casefold() or "application is still starting" in text.casefold():
        raise RuntimeError(
            "Graph Studio 2026.1.2 尚未完成启动；已阻止发布写入。"
            "请等待 /util/serverVersion 返回版本信息后重试。"
        )
    version = _version_from_payload(payload)
    if not version:
        raise RuntimeError(
            "Graph Studio /util/serverVersion 未返回可识别的 2026.1+ 版本信息；已阻止发布写入。"
        )
    parsed = _version_tuple(version)
    supported = (
        parsed[:2] >= SUPPORTED_PRODUCT_VERSION
        if parsed[0] >= 2000
        else parsed[:2] >= SUPPORTED_API_VERSION
    )
    if not supported:
        raise RuntimeError(
            f"Graph Studio {version} 不符合当前发布适配基线 2026.1 / REST API 6.3。"
        )
    return {"version": version}
