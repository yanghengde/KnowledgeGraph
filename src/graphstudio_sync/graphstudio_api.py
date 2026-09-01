"""Graph Studio 2026.1+ REST API compatibility and readiness checks."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

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
    *,
    graphmart_uri: str | None = None,
    file_connection: str | None = None,
    file_path: str | None = None,
) -> dict[str, Any]:
    """Require a ready Graph Studio 2026.1+/REST API 6.3+ server.

    Some 2026.1.2 deployments do not expose ``/util/serverVersion`` through
    the same ingress as the REST API. In that topology, verify the live 6.3
    read APIs and the configured FLDS directory before allowing writes.
    """
    base = base_url.rstrip("/")
    response = session.get(
        f"{base}/api/utils/serverVersion",
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        timeout=30,
    )
    payload: Any = None
    detected_version: str | None = None
    if response.ok:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        payload_text = payload.casefold() if isinstance(payload, str) else ""
        is_html_or_startup = any(
            marker in payload_text
            for marker in ("<!doctype", "<html", "still starting", "application is still starting")
        )
        version = None if is_html_or_startup else _version_from_payload(payload)
        if version:
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
            detected_version = version

    if detected_version and not graphmart_uri and not file_connection:
        return {"version": detected_version}

    failures: list[str] = []
    probes: list[tuple[str, str, type, dict[str, str] | None]] = [
        ("graphmarts", f"{base}/api/graphmarts", list, None),
        ("models", f"{base}/api/models", list, None),
        ("datasets", f"{base}/api/datasets", list, None),
    ]
    if graphmart_uri:
        encoded_graphmart = quote(graphmart_uri, safe="")
        design_runconfig = quote(f"{graphmart_uri}_RunConfiguration-Design", safe="")
        probes.extend(
            [
                (
                    "graphmart",
                    f"{base}/api/graphmarts/{encoded_graphmart}",
                    dict,
                    None,
                ),
                (
                    "designRunConfiguration",
                    f"{base}/api/runconfigs/{design_runconfig}",
                    dict,
                    None,
                ),
            ]
        )
    for name, url, expected_type, params in probes:
        probe = session.get(url, params=params, timeout=30)
        try:
            probe_payload = probe.json()
        except ValueError:
            probe_payload = None
        if not probe.ok or not isinstance(probe_payload, expected_type):
            failures.append(f"{name}=HTTP {probe.status_code}")

    file_connection_graph_secured = False
    if file_connection:
        encoded_connection = quote(file_connection, safe="")
        connection_probe = session.get(
            f"{base}/api/fileconnections/{encoded_connection}",
            params={
                "expand": (
                    "fileConnectionSupportsGlobalLoad,"
                    "fileConnectionGraphSecured,fileConnectionBaseFolder"
                )
            },
            timeout=30,
        )
        try:
            connection_payload = connection_probe.json()
        except ValueError:
            connection_payload = None
        if not connection_probe.ok or not isinstance(connection_payload, dict):
            failures.append(f"fileConnection=HTTP {connection_probe.status_code}")
        else:
            file_connection_graph_secured = (
                connection_payload.get("fileConnectionGraphSecured") is True
            )
            if connection_payload.get("fileConnectionSupportsGlobalLoad") is not True:
                failures.append(
                    "fileConnectionSupportsGlobalLoad=false "
                    "(shared store is not enabled for Graph Lakehouse)"
                )
            if file_connection_graph_secured:
                failures.append(
                    "fileConnectionGraphSecured=true (Graphmart File Staging cannot be "
                    "used by REST API 6.3 /datasets/from-rdf-zip because that operation "
                    "does not accept the required graph context)"
                )
            else:
                path_probe = session.get(
                    f"{base}/api/fileconnections/{encoded_connection}/files",
                    params={"path": (file_path or "/").strip("/") or "/"},
                    timeout=30,
                )
                try:
                    path_payload = path_probe.json()
                except ValueError:
                    path_payload = None
                if not path_probe.ok or not isinstance(path_payload, list):
                    failures.append(f"filePath=HTTP {path_probe.status_code}")

    if failures:
        version_status = f"HTTP {response.status_code}"
        if detected_version:
            version_status = f"REST API {detected_version}"
        elif response.ok:
            version_status = "未返回可识别版本"
        raise RuntimeError(
            "Graph Studio 2026.1.2 发布能力尚未就绪；已阻止发布写入。"
            f"/api/utils/serverVersion {version_status}；能力检查失败：{', '.join(failures)}。"
        )

    result: dict[str, Any]
    if detected_version:
        result = {"version": detected_version}
    else:
        result = {"version": "6.3-compatible", "source": "capabilityProbe"}
    return result
