"""Governed Camstar API actions with approval and idempotency.

This service deliberately has no database mutation adapter.  Real writes can
only use a configured Camstar business API after both global and per-action
switches are enabled.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from sqlalchemy import text

from .config import SyncSettings
from .materialization import canonical_json
from .repository import ControlPlaneRepository


SWAGGER_ROOT = Path(__file__).resolve().parents[2] / "data" / "openapi"
SAFE_ACTION_PART = re.compile(r"[^a-zA-Z0-9]+")


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
            text("SELECT action_key, title, description, object_class, endpoint_path, http_method, input_schema, allowed_roles, approval_required, enabled, timeout_seconds, retry_policy, compensation_action_key, version, status, origin, operation_id, reviewed_by, reviewed_at, approved_by, approved_at, config, updated_at FROM graphsync.action_definition ORDER BY object_class, action_key")
        ).mappings()]
        invocations = [dict(row) for row in connection.execute(
            text("SELECT invocation_id, action_key, idempotency_key, actor, actor_roles, status, dry_run, request_hash, response_summary, approved_by, approved_at, compensation_of, started_at, finished_at, error FROM graphsync.action_invocation ORDER BY started_at DESC LIMIT 100")
        ).mappings()]
        global_enabled = bool(connection.execute(
            text("SELECT coalesce((value #>> '{}')::boolean, false) FROM graphsync.app_setting WHERE setting_key='actions.apply_enabled'")
        ).scalar_one_or_none())
    return {"definitions": definitions, "invocations": invocations, "applyEnabled": global_enabled}


def upsert_action_definition(
    repository: ControlPlaneRepository,
    *,
    action_key: str,
    title: str,
    description: str | None,
    object_class: str,
    endpoint_path: str,
    http_method: str,
    input_schema: dict[str, Any],
    allowed_roles: list[str],
    approval_required: bool,
    timeout_seconds: int,
    retry_policy: dict[str, Any],
    compensation_action_key: str | None,
    origin: str = "manual",
    operation_id: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not action_key.strip() or not re.fullmatch(r"[A-Za-z0-9._:-]+", action_key):
        raise ValueError("Action key contains unsupported characters")
    if not endpoint_path.startswith("/") or "://" in endpoint_path:
        raise ValueError("Action endpoint must be a relative API path")
    if http_method not in {"POST", "PUT", "PATCH", "DELETE"}:
        raise ValueError("Action only supports POST/PUT/PATCH/DELETE")
    if compensation_action_key == action_key:
        raise ValueError("An Action cannot compensate itself")
    normalized_roles = sorted({item.strip() for item in allowed_roles if item.strip()})
    with repository.engine.begin() as connection:
        if compensation_action_key:
            exists = connection.execute(
                text("SELECT 1 FROM graphsync.action_definition WHERE action_key=:key"),
                {"key": compensation_action_key},
            ).scalar_one_or_none()
            if not exists:
                raise ValueError("Compensation Action does not exist")
        existing_version = connection.execute(
            text("SELECT version FROM graphsync.action_definition WHERE action_key=:key FOR UPDATE"),
            {"key": action_key},
        ).scalar_one_or_none()
        version = int(existing_version or 0) + 1
        row = connection.execute(
            text(
                """
                INSERT INTO graphsync.action_definition
                    (action_key, title, description, object_class, endpoint_path,
                     http_method, input_schema, allowed_roles, approval_required,
                     enabled, timeout_seconds, retry_policy,
                     compensation_action_key, version, status, origin,
                     operation_id, config)
                VALUES (:key, :title, :description, :object_class, :endpoint,
                        :method, CAST(:schema AS jsonb), CAST(:roles AS jsonb),
                        :approval, false, :timeout, CAST(:retry AS jsonb),
                        :compensation, :version, 'draft', :origin,
                        :operation_id, CAST(:config AS jsonb))
                ON CONFLICT (action_key) DO UPDATE SET
                    title=EXCLUDED.title, description=EXCLUDED.description,
                    object_class=EXCLUDED.object_class,
                    endpoint_path=EXCLUDED.endpoint_path,
                    http_method=EXCLUDED.http_method,
                    input_schema=EXCLUDED.input_schema,
                    allowed_roles=EXCLUDED.allowed_roles,
                    approval_required=EXCLUDED.approval_required,
                    enabled=false, timeout_seconds=EXCLUDED.timeout_seconds,
                    retry_policy=EXCLUDED.retry_policy,
                    compensation_action_key=EXCLUDED.compensation_action_key,
                    version=EXCLUDED.version, status='draft', origin=EXCLUDED.origin,
                    operation_id=EXCLUDED.operation_id, config=EXCLUDED.config,
                    reviewed_by=NULL, reviewed_at=NULL,
                    approved_by=NULL, approved_at=NULL
                RETURNING action_key, title, object_class, endpoint_path,
                          http_method, version, status, origin, enabled, updated_at
                """
            ),
            {
                "key": action_key, "title": title, "description": description,
                "object_class": object_class, "endpoint": endpoint_path,
                "method": http_method, "schema": canonical_json(input_schema),
                "roles": canonical_json(normalized_roles), "approval": approval_required,
                "timeout": timeout_seconds, "retry": canonical_json(retry_policy),
                "compensation": compensation_action_key, "version": version,
                "origin": origin, "operation_id": operation_id,
                "config": canonical_json({"writeBoundary": "camstar_api_only", **(config or {})}),
            },
        ).mappings().one()
    return dict(row)


def review_action_definition(
    repository: ControlPlaneRepository,
    action_key: str,
    *,
    status: str,
    actor: str,
) -> dict[str, Any]:
    if status not in {"reviewed", "approved", "retired"}:
        raise ValueError("Unsupported Action definition status")
    with repository.engine.begin() as connection:
        current = connection.execute(
            text("SELECT status, reviewed_by, allowed_roles FROM graphsync.action_definition WHERE action_key=:key FOR UPDATE"),
            {"key": action_key},
        ).mappings().one_or_none()
        if current is None:
            raise KeyError(action_key)
        if status == "reviewed" and current["status"] != "draft":
            raise ValueError("Only a draft Action can be reviewed")
        if status == "approved":
            if current["status"] != "reviewed":
                raise ValueError("Action must be reviewed before approval")
            if current["reviewed_by"] == actor:
                raise ValueError("Action reviewer and approver must be different people")
            if not current["allowed_roles"]:
                raise ValueError("Approved Action requires at least one allowed role")
        row = connection.execute(
            text(
                """
                UPDATE graphsync.action_definition
                SET status=:status,
                    enabled=CASE WHEN :status='approved' THEN true ELSE false END,
                    reviewed_by=CASE WHEN :status='reviewed' THEN :actor ELSE reviewed_by END,
                    reviewed_at=CASE WHEN :status='reviewed' THEN now() ELSE reviewed_at END,
                    approved_by=CASE WHEN :status='approved' THEN :actor ELSE approved_by END,
                    approved_at=CASE WHEN :status='approved' THEN now() ELSE approved_at END
                WHERE action_key=:key
                RETURNING action_key, version, status, enabled,
                          reviewed_by, reviewed_at, approved_by, approved_at
                """
            ),
            {"key": action_key, "status": status, "actor": actor},
        ).mappings().one()
    return dict(row)


def _resolved_openapi_schema(document: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    reference = schema.get("$ref")
    if not reference:
        return dict(schema)
    prefix = "#/components/schemas/"
    if not reference.startswith(prefix):
        return {"type": "object"}
    return dict((document.get("components") or {}).get("schemas", {}).get(reference[len(prefix):], {"type": "object"}))


def openapi_action_candidates(source_file: str | None = None) -> list[dict[str, Any]]:
    paths = [SWAGGER_ROOT / source_file] if source_file else sorted(SWAGGER_ROOT.glob("*.json"))
    candidates: list[dict[str, Any]] = []
    for path in paths:
        if path.parent != SWAGGER_ROOT or not path.is_file():
            raise KeyError(source_file or "")
        document = json.loads(path.read_text(encoding="utf-8"))
        object_class = str((document.get("info") or {}).get("title") or path.stem).removesuffix("Entity")
        server_path = str(((document.get("servers") or [{}])[0].get("url") or "")).rstrip("/")
        for endpoint, operations in (document.get("paths") or {}).items():
            for method, operation in operations.items():
                method_upper = method.upper()
                if method_upper not in {"POST", "PUT", "PATCH", "DELETE"}:
                    continue
                operation_id = operation.get("operationId") or f"{method_upper}:{endpoint}"
                request_schema = (((operation.get("requestBody") or {}).get("content") or {}).get("application/json") or {}).get("schema") or {"type": "object"}
                input_schema = _resolved_openapi_schema(document, request_schema)
                input_schema.setdefault("type", "object")
                input_schema.setdefault("properties", {})
                input_schema.setdefault("required", [])
                parameters = list((operations.get("parameters") or [])) + list(operation.get("parameters") or [])
                path_parameters = []
                for parameter in parameters:
                    if parameter.get("in") != "path":
                        continue
                    name = parameter["name"]
                    path_parameters.append(name)
                    input_schema["properties"].setdefault(name, parameter.get("schema") or {"type": "string"})
                    if name not in input_schema["required"]:
                        input_schema["required"].append(name)
                slug = SAFE_ACTION_PART.sub("-", str(operation_id)).strip("-").casefold()
                candidates.append({
                    "sourceFile": path.name,
                    "actionKey": f"camstar.openapi.{object_class.casefold()}.{slug}",
                    "title": operation.get("summary") or f"{method_upper} {object_class}",
                    "description": operation.get("description"),
                    "objectClass": object_class,
                    "endpointPath": f"{server_path}{endpoint}",
                    "httpMethod": method_upper,
                    "operationId": operation_id,
                    "inputSchema": input_schema,
                    "pathParameters": path_parameters,
                })
    return candidates


def openapi_action_sources() -> list[dict[str, str]]:
    result = []
    for path in sorted(SWAGGER_ROOT.glob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            title = str((document.get("info") or {}).get("title") or path.stem).removesuffix("Entity")
        except (OSError, json.JSONDecodeError):
            continue
        result.append({"sourceFile": path.name, "objectClass": title})
    return result


def import_openapi_action(
    repository: ControlPlaneRepository,
    *,
    source_file: str,
    operation_id: str,
) -> dict[str, Any]:
    candidate = next(
        (item for item in openapi_action_candidates(source_file) if item["operationId"] == operation_id),
        None,
    )
    if candidate is None:
        raise KeyError(operation_id)
    return upsert_action_definition(
        repository,
        action_key=candidate["actionKey"], title=candidate["title"],
        description=candidate["description"], object_class=candidate["objectClass"],
        endpoint_path=candidate["endpointPath"], http_method=candidate["httpMethod"],
        input_schema=candidate["inputSchema"], allowed_roles=[], approval_required=True,
        timeout_seconds=60, retry_policy={"maxAttempts": 1},
        compensation_action_key=None, origin="openapi", operation_id=operation_id,
        config={"sourceFile": source_file, "pathParameters": candidate["pathParameters"]},
    )


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
        if not definition["enabled"] or definition.get("status") != "approved":
            blockers.append("Action 定义尚未批准启用")
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


def approve_action(
    repository: ControlPlaneRepository,
    invocation_id: uuid.UUID,
    actor: str,
    actor_roles: list[str] | None = None,
) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        invocation = connection.execute(
            text("SELECT invocation.actor, invocation.status, invocation.dry_run, definition.allowed_roles FROM graphsync.action_invocation invocation JOIN graphsync.action_definition definition USING (action_key) WHERE invocation.invocation_id=:id FOR UPDATE OF invocation"),
            {"id": invocation_id},
        ).mappings().one_or_none()
        if invocation is None:
            raise KeyError(str(invocation_id))
        if invocation["status"] != "pending_approval" or invocation["dry_run"]:
            raise ValueError("Only a real pending Action can be approved")
        if invocation["actor"] == actor:
            raise ValueError("Action requester and approver must be different people")
        if invocation["allowed_roles"] and not set(invocation["allowed_roles"]).intersection(actor_roles or []):
            raise PermissionError("Approver does not have an allowed role for this Action")
        connection.execute(text("UPDATE graphsync.action_invocation SET status='approved', approved_by=:actor, approved_at=now() WHERE invocation_id=:id"), {"id": invocation_id, "actor": actor})
        _event(connection, invocation_id, "approved", actor, {})
    return {"invocationId": str(invocation_id), "status": "approved", "approvedBy": actor}


def plan_compensation(
    repository: ControlPlaneRepository,
    *,
    original_invocation_id: uuid.UUID,
    payload: dict[str, Any],
    actor: str,
    actor_roles: list[str],
    idempotency_key: str,
) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        original = connection.execute(
            text(
                """
                SELECT invocation.status, definition.compensation_action_key
                FROM graphsync.action_invocation invocation
                JOIN graphsync.action_definition definition USING (action_key)
                WHERE invocation.invocation_id=:id
                """
            ),
            {"id": original_invocation_id},
        ).mappings().one_or_none()
    if original is None:
        raise KeyError(str(original_invocation_id))
    if original["status"] != "succeeded":
        raise ValueError("Only a succeeded Action can be compensated")
    if not original["compensation_action_key"]:
        raise ValueError("Action has no configured compensation Action")
    planned = plan_action(
        repository, action_key=original["compensation_action_key"],
        payload=payload, actor=actor, actor_roles=actor_roles,
        idempotency_key=idempotency_key, dry_run=False,
    )
    if planned.get("replayed"):
        return planned
    compensation_id = uuid.UUID(planned["invocationId"])
    with repository.engine.begin() as connection:
        connection.execute(
            text("UPDATE graphsync.action_invocation SET compensation_of=:original WHERE invocation_id=:compensation"),
            {"original": original_invocation_id, "compensation": compensation_id},
        )
        connection.execute(
            text("UPDATE graphsync.action_invocation SET status='compensating' WHERE invocation_id=:original"),
            {"original": original_invocation_id},
        )
        _event(connection, original_invocation_id, "compensation_planned", actor, {"compensationInvocationId": str(compensation_id)})
    return {**planned, "compensationOf": str(original_invocation_id)}


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
    actor: str | None = None,
    actor_roles: list[str] | None = None,
) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        row = connection.execute(
            text(
                """
                SELECT invocation.*, definition.endpoint_path,
                       definition.http_method, definition.enabled,
                       definition.allowed_roles,
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
        if row["allowed_roles"] and not set(row["allowed_roles"]).intersection(actor_roles or []):
            raise PermissionError("Executor does not have an allowed role for this Action")
        if not settings.camstar_api_base_url:
            raise RuntimeError("CAMSTAR_API_BASE_URL is not configured")
        connection.execute(text("UPDATE graphsync.action_invocation SET status='executing' WHERE invocation_id=:id"), {"id": invocation_id})
        _event(connection, invocation_id, "executing", actor or row["actor"], {})

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
            _event(connection, invocation_id, "succeeded", actor or row["actor"], summary)
            if row["compensation_of"]:
                connection.execute(
                    text("UPDATE graphsync.action_invocation SET status='compensated', finished_at=now() WHERE invocation_id=:original"),
                    {"original": row["compensation_of"]},
                )
                _event(connection, row["compensation_of"], "compensated", row["actor"], {"compensationInvocationId": str(invocation_id)})
            connection.execute(
                text("INSERT INTO graphsync.runtime_lineage_event (lineage_event_id, profile_key, run_type, run_id, source_asset, target_asset, field_mappings, row_count, content_hash) VALUES (:event, :profile, 'action', :run, :source, :target, CAST(:fields AS jsonb), 1, :hash)"),
                {"event": uuid.uuid4(), "profile": (row["config"] or {}).get("profileKey", "opcenter2607-core"), "run": invocation_id, "source": f"action_request:{row['action_key']}", "target": f"camstar_api:{row['endpoint_path']}", "fields": json.dumps({key: key for key in body}), "hash": row["request_hash"]},
            )
        return {"invocationId": str(invocation_id), "status": "succeeded", "executedBy": actor, "responseSummary": summary}
    except Exception as exc:
        with repository.engine.begin() as connection:
            connection.execute(text("UPDATE graphsync.action_invocation SET status='failed', error=CAST(:error AS jsonb), finished_at=now() WHERE invocation_id=:id"), {"id": invocation_id, "error": json.dumps({"message": str(exc)})})
            _event(connection, invocation_id, "failed", row["actor"], {"message": str(exc)})
            if row["compensation_of"]:
                connection.execute(
                    text("UPDATE graphsync.action_invocation SET status='succeeded' WHERE invocation_id=:original"),
                    {"original": row["compensation_of"]},
                )
                _event(connection, row["compensation_of"], "compensation_failed", row["actor"], {"compensationInvocationId": str(invocation_id), "message": str(exc)})
        raise
