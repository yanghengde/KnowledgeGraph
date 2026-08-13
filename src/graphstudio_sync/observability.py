"""Runtime lineage, health metrics and alert evaluation."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from sqlalchemy import text

from .repository import ControlPlaneRepository


def record_lineage(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    run_type: str,
    run_id: uuid.UUID,
    source_asset: str,
    target_asset: str,
    field_mappings: dict[str, Any],
    row_count: int,
    content_hash: str | None = None,
) -> dict[str, Any]:
    event_id = uuid.uuid4()
    with repository.engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO graphsync.runtime_lineage_event
                    (lineage_event_id, profile_key, run_type, run_id,
                     source_asset, target_asset, field_mappings,
                     row_count, content_hash)
                VALUES (:event_id, :profile_key, :run_type, :run_id,
                        :source_asset, :target_asset, CAST(:field_mappings AS jsonb),
                        :row_count, :content_hash)
                """
            ),
            {
                "event_id": event_id,
                "profile_key": profile_key,
                "run_type": run_type,
                "run_id": run_id,
                "source_asset": source_asset,
                "target_asset": target_asset,
                "field_mappings": json.dumps(field_mappings, ensure_ascii=False),
                "row_count": row_count,
                "content_hash": content_hash,
            },
        )
    return {"lineageEventId": str(event_id)}


def _metric(
    key: str,
    value: float | int | None,
    status: str,
    message: str,
    *,
    unit: str | None = None,
    scope_key: str = "opcenter2607-core",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "metricKey": key,
        "scopeType": "profile",
        "scopeKey": scope_key,
        "valueNumeric": value,
        "valueText": None,
        "unit": unit,
        "status": status,
        "message": message,
        "details": details or {},
    }


def collect_health_metrics(repository: ControlPlaneRepository, profile_key: str) -> list[dict[str, Any]]:
    with repository.engine.connect() as connection:
        release = connection.execute(
            text(
                """
                SELECT release.release_id, release.object_count,
                       release.relationship_count, release.quarantine_count,
                       extract(epoch FROM (now()-active.activated_at))/60 AS age_minutes
                FROM graphsync.curated_release_activation active
                JOIN graphsync.curated_release release
                  ON release.release_id=active.active_release_id
                WHERE active.profile_key=:profile_key
                """
            ),
            {"profile_key": profile_key},
        ).mappings().one_or_none()
        unresolved = connection.execute(
            text(
                """
                SELECT count(*)
                FROM camstar_curated.relationship_version relationship
                JOIN graphsync.curated_release release USING (release_id)
                JOIN graphsync.curated_release_activation active
                  ON active.profile_key=release.profile_key
                 AND active.active_release_id=relationship.release_id
                WHERE active.profile_key=:profile_key
                  AND relationship.resolution_status <> 'resolved'
                """
            ),
            {"profile_key": profile_key},
        ).scalar_one()
        failed_changes = connection.execute(
            text("SELECT count(*) FROM graphsync.schema_change_request WHERE profile_key=:profile_key AND status='failed'"),
            {"profile_key": profile_key},
        ).scalar_one()
        failed_deployments = connection.execute(
            text("SELECT count(*) FROM graphsync.deployment_release WHERE profile_key=:profile_key AND status='failed' AND started_at > now()-interval '24 hours'"),
            {"profile_key": profile_key},
        ).scalar_one()
        pending_actions = connection.execute(
            text("SELECT count(*) FROM graphsync.action_invocation WHERE status IN ('pending_approval','executing','compensating')"),
        ).scalar_one()
    metrics: list[dict[str, Any]] = []
    if release:
        age = float(release["age_minutes"] or 0)
        metrics.extend([
            _metric("curated.release_age_minutes", age, "healthy" if age <= 1440 else "warning", f"活动治理快照已运行 {age:.1f} 分钟", unit="minutes", scope_key=profile_key),
            _metric("curated.object_count", int(release["object_count"]), "healthy", "活动治理对象数", unit="rows", scope_key=profile_key),
            _metric("curated.relationship_count", int(release["relationship_count"]), "healthy", "活动治理关系数", unit="rows", scope_key=profile_key),
            _metric("curated.quarantine_count", int(release["quarantine_count"]), "healthy" if not release["quarantine_count"] else "critical", "隔离对象数", unit="rows", scope_key=profile_key),
        ])
    else:
        metrics.append(_metric("curated.release_age_minutes", None, "critical", "尚无活动治理快照", unit="minutes", scope_key=profile_key))
    metrics.extend([
        _metric("curated.unresolved_relationships", int(unresolved), "healthy" if not unresolved else "critical", "未解析治理关系数", unit="rows", scope_key=profile_key),
        _metric("schema.failed_changes", int(failed_changes), "healthy" if not failed_changes else "warning", "失败的 Schema 变更数", unit="changes", scope_key=profile_key),
        _metric("deployment.failed_recent", int(failed_deployments), "healthy" if not failed_deployments else "critical", "24 小时内发布失败数", unit="deployments", scope_key=profile_key),
        _metric("actions.pending", int(pending_actions), "healthy" if pending_actions < 20 else "warning", "待审批或执行中的 Action 数", unit="actions", scope_key=profile_key),
    ])
    return metrics


def _rule_failed(operator: str, value: float | None, threshold: float | None) -> bool:
    if operator == "missing":
        return value is None
    if value is None or threshold is None:
        return False
    return {
        "gt": value > threshold,
        "gte": value >= threshold,
        "lt": value < threshold,
        "lte": value <= threshold,
        "eq": value == threshold,
    }[operator]


def run_health_check(repository: ControlPlaneRepository, profile_key: str) -> dict[str, Any]:
    run_id = uuid.uuid4()
    try:
        metrics = collect_health_metrics(repository, profile_key)
        rank = {"healthy": 0, "unknown": 1, "warning": 2, "critical": 3}
        worst = max((item["status"] for item in metrics), key=lambda item: rank[item], default="unknown")
        health_status = "healthy" if worst == "healthy" else "degraded" if worst in {"warning", "unknown"} else "unhealthy"
        with repository.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO graphsync.health_check_run (health_run_id, profile_key, status, finished_at, summary) VALUES (:run_id, :profile_key, :status, now(), CAST(:summary AS jsonb))"),
                {"run_id": run_id, "profile_key": profile_key, "status": health_status, "summary": json.dumps({"metricCount": len(metrics), "worst": worst})},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO graphsync.health_metric
                        (metric_id, health_run_id, metric_key, scope_type,
                         scope_key, value_numeric, value_text, unit, status,
                         message, details)
                    VALUES (:metric_id, :run_id, :metric_key, :scope_type,
                            :scope_key, :value_numeric, :value_text, :unit,
                            :status, :message, CAST(:details AS jsonb))
                    """
                ),
                [{
                    "metric_id": uuid.uuid4(), "run_id": run_id,
                    "metric_key": item["metricKey"], "scope_type": item["scopeType"],
                    "scope_key": item["scopeKey"], "value_numeric": item["valueNumeric"],
                    "value_text": item["valueText"], "unit": item["unit"],
                    "status": item["status"], "message": item["message"],
                    "details": json.dumps(item["details"], ensure_ascii=False),
                } for item in metrics],
            )
            rules = [dict(row) for row in connection.execute(
                text("SELECT * FROM graphsync.alert_rule WHERE enabled AND (profile_key IS NULL OR profile_key=:profile_key)"),
                {"profile_key": profile_key},
            ).mappings()]
            by_key = {item["metricKey"]: item for item in metrics}
            alert_changes: list[dict[str, Any]] = []
            for rule in rules:
                metric = by_key.get(rule["metric_key"])
                value = float(metric["valueNumeric"]) if metric and metric["valueNumeric"] is not None else None
                failed = _rule_failed(rule["operator"], value, float(rule["threshold"]) if rule["threshold"] is not None else None)
                fingerprint = hashlib.sha256(f"{profile_key}:{rule['rule_key']}".encode()).hexdigest()
                existing = connection.execute(
                    text("SELECT alert_event_id, status FROM graphsync.alert_event WHERE rule_key=:rule_key AND fingerprint=:fingerprint AND status IN ('open','acknowledged')"),
                    {"rule_key": rule["rule_key"], "fingerprint": fingerprint},
                ).mappings().one_or_none()
                if failed and existing is None:
                    alert_id = uuid.uuid4()
                    message = metric["message"] if metric else f"指标缺失：{rule['metric_key']}"
                    connection.execute(
                        text("INSERT INTO graphsync.alert_event (alert_event_id, rule_key, health_run_id, status, severity, fingerprint, message, details) VALUES (:id, :rule, :run, 'open', :severity, :fingerprint, :message, CAST(:details AS jsonb))"),
                        {"id": alert_id, "rule": rule["rule_key"], "run": run_id, "severity": rule["severity"], "fingerprint": fingerprint, "message": message, "details": json.dumps({"value": value, "threshold": rule["threshold"]}, default=str)},
                    )
                    alert_changes.append({"ruleKey": rule["rule_key"], "change": "opened"})
                elif not failed and existing is not None:
                    connection.execute(text("UPDATE graphsync.alert_event SET status='resolved', resolved_at=now(), health_run_id=:run WHERE alert_event_id=:id"), {"run": run_id, "id": existing["alert_event_id"]})
                    alert_changes.append({"ruleKey": rule["rule_key"], "change": "resolved"})
        return {"healthRunId": str(run_id), "status": health_status, "metrics": metrics, "alertChanges": alert_changes}
    except Exception as exc:
        with repository.engine.begin() as connection:
            connection.execute(text("INSERT INTO graphsync.health_check_run (health_run_id, profile_key, status, finished_at, error) VALUES (:run, :profile, 'failed', now(), CAST(:error AS jsonb)) ON CONFLICT (health_run_id) DO NOTHING"), {"run": run_id, "profile": profile_key, "error": json.dumps({"message": str(exc)})})
        raise


def observability_status(repository: ControlPlaneRepository, profile_key: str) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        latest = connection.execute(
            text("SELECT health_run_id, status, started_at, finished_at, summary, error FROM graphsync.health_check_run WHERE profile_key=:profile_key ORDER BY started_at DESC LIMIT 1"),
            {"profile_key": profile_key},
        ).mappings().one_or_none()
        metrics = [] if latest is None else [dict(row) for row in connection.execute(
            text("SELECT metric_key, scope_type, scope_key, value_numeric, value_text, unit, status, message, details, measured_at FROM graphsync.health_metric WHERE health_run_id=:run ORDER BY status DESC, metric_key"),
            {"run": latest["health_run_id"]},
        ).mappings()]
        alerts = [dict(row) for row in connection.execute(
            text("SELECT event.alert_event_id, event.rule_key, event.status, event.severity, event.message, event.details, event.opened_at, event.acknowledged_at, event.resolved_at FROM graphsync.alert_event event JOIN graphsync.alert_rule rule USING (rule_key) WHERE rule.profile_key=:profile_key ORDER BY event.opened_at DESC LIMIT 50"),
            {"profile_key": profile_key},
        ).mappings()]
        lineage = [dict(row) for row in connection.execute(
            text("SELECT lineage_event_id, run_type, run_id, source_asset, target_asset, field_mappings, row_count, content_hash, occurred_at FROM graphsync.runtime_lineage_event WHERE profile_key=:profile_key ORDER BY occurred_at DESC LIMIT 50"),
            {"profile_key": profile_key},
        ).mappings()]
    return {"latestRun": dict(latest) if latest else None, "metrics": metrics, "alerts": alerts, "lineage": lineage}


def acknowledge_alert(repository: ControlPlaneRepository, alert_id: uuid.UUID, actor: str | None) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        row = connection.execute(
            text("UPDATE graphsync.alert_event SET status='acknowledged', acknowledged_at=now(), acknowledged_by=:actor WHERE alert_event_id=:id AND status='open' RETURNING alert_event_id, status, acknowledged_at, acknowledged_by"),
            {"id": alert_id, "actor": actor},
        ).mappings().one_or_none()
    if row is None:
        raise ValueError("Only an open alert can be acknowledged")
    return dict(row)
