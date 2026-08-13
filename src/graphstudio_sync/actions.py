"""Governed Camstar API actions with approval and idempotency.

This service deliberately has no database mutation adapter.  Real writes can
only use a configured Camstar business API after both global and per-action
switches are enabled.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any
from urllib.parse import quote

import requests
from sqlalchemy import text

from .config import SyncSettings
from .materialization import canonical_json
from .repository import ControlPlaneRepository


def _validate_payload(schema: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("type") == "object" and not isinstance(payload, dict):
        return ["请求必须是 JSON 对象"]
    for key in schema.get("required", []):
        if key not in payload or payload[key] in (None, ""):
            errors.append(f"缺少必填参数：{key}")
    properties = schema.get("properties", {})
    for key, value in payload.items():
        expected = (properties.get(key) or {}).get("type")
        if expected == "string" and not isinstance(value, str):
            errors.append(f"参数 {key} 必须是字符串")
        elif expected == "object" and not isinstance(value, dict):
            errors.append(f"参数 {key} 必须是对象")
        elif expected == "array" and not isinstance(value, list):
            errors.append(f"参数 {key} 必须是数组")
        elif expected == "number" and not isinstance(value, (int, float)):
            errors.append(f"参数 {key} 必须是数字")
    return errors


def _event(connection, invocation_id: uuid.UUID, event_type: str, actor: str | None, details: dict[str, Any]) -> None:
    connection.execute(
        text("INSERT INTO graphsync.action_event (action_event_id, invocation_id, event_type, actor, details) VALUES (:id, :invocation, :event, :actor, CAST(:details AS jsonb))"),
        {"id": uuid.uuid4(), "invocation": invocation_id, "event": event_type, "actor": actor, "details": json.dumps(details, ensure_ascii=False, default=str)},
    )


def list_actions(repository: ControlPlaneRepository) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        definitions = [dict(row) for row in connection.execute(
            text("SELECT action_key, title, description, object_class, endpoint_path, http_method, input_schema, allowed_roles, approval_required, enabled, timeout_seconds, retry_policy, compensation_action_key, config, updated_at FROM graphsync.action_definition ORDER BY action_key")
        ).mappings()]
        invocations = [dict(row) for row in connection.execute(
            text("SELECT invocation_id, action_key, idempotency_key, actor, actor_roles, status, dry_run, request_hash, response_summary, approved_by, approved_at, started_at, finished_at, error FROM graphsync.action_invocation ORDER BY started_at DESC LIMIT 100")
        ).mappings()]
        global_enabled = bool(connection.execute(
            text("SELECT coalesce((value #>> '{}')::boolean, false) FROM graphsync.app_setting WHERE setting_key='actions.apply_enabled'")
        ).scalar_one_or_none())
    return {"definitions": definitions, "invocations": invocations, "applyEnabled": global_enabled}


def plan_action(
    repository: ControlPlaneRepository,
    *,
    action_key: str,
    payload: dict[str, Any],
    actor: str,
    actor_roles: list[str],
    idempotency_key: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    if not idempotency_key.strip():
        raise ValueError("Action requires a non-empty idempotency key")
    with repository.engine.begin() as connection:
        definition = connection.execute(
            text("SELECT * FROM graphsync.action_definition WHERE action_key=:action_key"),
            {"action_key": action_key},
        ).mappings().one_or_none()
        if definition is None:
            raise KeyError(action_key)
        existing = connection.execute(
            text("SELECT invocation_id, action_key, status, dry_run, request_hash, response_summary, error FROM graphsync.action_invocation WHERE idempotency_key=:key"),
            {"key": idempotency_key},
        ).mappings().one_or_none()
        request_hash = hashlib.sha256(canonical_json(payload).encode()).hexdigest()
        if existing:
            if existing["action_key"] != action_key or existing["request_hash"] != request_hash:
                raise ValueError("Idempotency key was already used with a different action or payload")
            return {"replayed": True, **dict(existing)}
        allowed = set(definition["allowed_roles"] or [])
        if allowed and not allowed.intersection(actor_roles):
            raise PermissionError("Actor does not have an allowed role for this Action")
        validation_errors = _validate_payload(definition["input_schema"] or {}, payload)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
        blockers: list[str] = []
        if not definition["enabled"]:
            blockers.append("Action 定义尚未启用")
        status = "planned" if dry_run or blockers else "pending_approval" if definition["approval_required"] else "approved"
        invocation_id = uuid.uuid4()
        connection.execute(
            text(
                """
                INSERT INTO graphsync.action_invocation
                    (invocation_id, action_key, idempotency_key, actor,
                     actor_roles, status, dry_run, request_payload, request_hash)
                VALUES (:id, :action, :key, :actor, CAST(:roles AS jsonb),
                        :status, :dry_run, CAST(:payload AS jsonb), :hash)
                """
            ),
            {"id": invocation_id, "action": action_key, "key": idempotency_key, "actor": actor, "roles": json.dumps(actor_roles), "status": status, "dry_run": dry_run, "payload": canonical_json(payload), "hash": request_hash},
        )
        _event(connection, invocation_id, "planned", actor, {"dryRun": dry_run, "blockers": blockers})
    return {
        "invocationId": str(invocation_id),
        "actionKey": action_key,
        "status": status,
        "dryRun": dry_run,
        "requestHash": request_hash,
        "blockers": blockers,
        "wouldCall": {"method": definition["http_method"], "path": definition["endpoint_path"]},
    }


def approve_action(repository: ControlPlaneRepository, invocation_id: uuid.UUID, actor: str) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        invocation = connection.execute(
            text("SELECT actor, status, dry_run FROM graphsync.action_invocation WHERE invocation_id=:id FOR UPDATE"),
            {"id": invocation_id},
        ).mappings().one_or_none()
        if invocation is None:
            raise KeyError(str(invocation_id))
        if invocation["status"] != "pending_approval" or invocation["dry_run"]:
            raise ValueError("Only a real pending Action can be approved")
        if invocation["actor"] == actor:
            raise ValueError("Action requester and approver must be different people")
        connection.execute(text("UPDATE graphsync.action_invocation SET status='approved', approved_by=:actor, approved_at=now() WHERE invocation_id=:id"), {"id": invocation_id, "actor": actor})
        _event(connection, invocation_id, "approved", actor, {})
    return {"invocationId": str(invocation_id), "status": "approved", "approvedBy": actor}


def _resolved_path(template: str, payload: dict[str, Any], path_parameters: list[str]) -> str:
    result = template
    for key in path_parameters:
        if key not in payload:
            raise ValueError(f"Missing path parameter: {key}")
        result = result.replace("{" + key + "}", quote(str(payload[key]), safe=""))
    if "{" in result or "}" in result:
        raise ValueError("Action endpoint contains unresolved path parameters")
    return result


def execute_action(
    settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    invocation_id: uuid.UUID,
) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        row = connection.execute(
            text(
                """
                SELECT invocation.*, definition.endpoint_path,
                       definition.http_method, definition.enabled,
                       definition.timeout_seconds, definition.retry_policy,
                       definition.config, definition.compensation_action_key,
                       coalesce((setting.value #>> '{}')::boolean, false) AS global_enabled
                FROM graphsync.action_invocation invocation
                JOIN graphsync.action_definition definition USING (action_key)
                LEFT JOIN graphsync.app_setting setting
                  ON setting.setting_key='actions.apply_enabled'
                WHERE invocation.invocation_id=:id FOR UPDATE OF invocation
                """
            ),
            {"id": invocation_id},
        ).mappings().one_or_none()
        if row is None:
            raise KeyError(str(invocation_id))
        if row["dry_run"]:
            raise ValueError("Dry-run Action plans cannot be executed")
        if row["status"] != "approved":
            raise ValueError("Action must be approved before execution")
        if not row["enabled"] or not row["global_enabled"]:
            raise RuntimeError("Camstar Action execution is disabled")
        if not settings.camstar_api_base_url:
            raise RuntimeError("CAMSTAR_API_BASE_URL is not configured")
        connection.execute(text("UPDATE graphsync.action_invocation SET status='executing' WHERE invocation_id=:id"), {"id": invocation_id})
        _event(connection, invocation_id, "executing", row["actor"], {})

    session = requests.Session()
    headers = {"Accept": "application/json", "Content-Type": "application/json", "Idempotency-Key": row["idempotency_key"]}
    if settings.camstar_api_token:
        headers["Authorization"] = f"Bearer {settings.camstar_api_token}"
    elif settings.camstar_api_user:
        session.auth = (settings.camstar_api_user, settings.camstar_api_password or "")
    session.headers.update(headers)
    path = _resolved_path(row["endpoint_path"], row["request_payload"], (row["config"] or {}).get("pathParameters", []))
    url = settings.camstar_api_base_url + "/" + path.lstrip("/")
    max_attempts = max(1, min(3, int((row["retry_policy"] or {}).get("maxAttempts", 1))))
    retry_statuses = set((row["retry_policy"] or {}).get("retryStatuses", []))
    body = {key: value for key, value in row["request_payload"].items() if key not in (row["config"] or {}).get("pathParameters", [])}
    try:
        response = None
        for attempt in range(1, max_attempts + 1):
            response = session.request(row["http_method"], url, json=body, timeout=int(row["timeout_seconds"]))
            if response.status_code not in retry_statuses or attempt == max_attempts:
                break
            time.sleep(min(2 ** (attempt - 1), 4))
        assert response is not None
        if not response.ok:
            raise RuntimeError(f"Camstar API returned HTTP {response.status_code}: {response.text[:1000]}")
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"body": response.text[:1000]}
        summary = {"statusCode": response.status_code, "responseHash": hashlib.sha256(response.content).hexdigest()}
        if isinstance(response_body, dict):
            summary["resultKeys"] = sorted(response_body)[:50]
        with repository.engine.begin() as connection:
            connection.execute(text("UPDATE graphsync.action_invocation SET status='succeeded', response_summary=CAST(:summary AS jsonb), finished_at=now() WHERE invocation_id=:id"), {"id": invocation_id, "summary": json.dumps(summary)})
            _event(connection, invocation_id, "succeeded", row["actor"], summary)
            connection.execute(
                text("INSERT INTO graphsync.runtime_lineage_event (lineage_event_id, profile_key, run_type, run_id, source_asset, target_asset, field_mappings, row_count, content_hash) VALUES (:event, :profile, 'action', :run, :source, :target, CAST(:fields AS jsonb), 1, :hash)"),
                {"event": uuid.uuid4(), "profile": (row["config"] or {}).get("profileKey", "opcenter2607-core"), "run": invocation_id, "source": f"action_request:{row['action_key']}", "target": f"camstar_api:{row['endpoint_path']}", "fields": json.dumps({key: key for key in body}), "hash": row["request_hash"]},
            )
        return {"invocationId": str(invocation_id), "status": "succeeded", "responseSummary": summary}
    except Exception as exc:
        with repository.engine.begin() as connection:
            connection.execute(text("UPDATE graphsync.action_invocation SET status='failed', error=CAST(:error AS jsonb), finished_at=now() WHERE invocation_id=:id"), {"id": invocation_id, "error": json.dumps({"message": str(exc)})})
            _event(connection, invocation_id, "failed", row["actor"], {"message": str(exc)})
        raise
