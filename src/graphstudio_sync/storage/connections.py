"""connections persistence for the control plane."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from src.graphstudio_sync.config import connection_endpoints

from .repository_support import _rows


class ConnectionsRepository:
    def overview(self) -> dict[str, Any]:
        with self.engine.connect() as connection:
            summary = dict(
                connection.execute(text("SELECT * FROM graphsync.dashboard_summary")).mappings().one()
            )
            connections = _rows(
                connection.execute(
                    text(
                        """
                        SELECT connection_key, kind, display_name, endpoint, database_name,
                               enabled, status, last_tested_at, last_error
                        FROM graphsync.connection_profile ORDER BY connection_key
                        """
                    )
                )
            )
            jobs = _rows(
                connection.execute(
                    text(
                        """
                        SELECT j.job_name, j.title, j.mode, j.schedule, j.timezone, j.enabled,
                               r.status AS last_status, r.started_at AS last_started_at,
                               r.finished_at AS last_finished_at, r.row_count, r.triple_count
                        FROM graphsync.sync_job j
                        LEFT JOIN graphsync.latest_job_run r ON r.job_name = j.job_name
                        ORDER BY j.job_name
                        """
                    )
                )
            )
            recent_runs = _rows(
                connection.execute(
                    text(
                        """
                        SELECT run_id, job_name, status, trigger_type, started_at, finished_at,
                               row_count, triple_count
                        FROM graphsync.sync_run ORDER BY started_at DESC LIMIT 8
                        """
                    )
                )
            )
        connections = [item for item in connections if item["connection_key"] in {"camstar-source", "graph-studio", "control-postgresql"}]
        connections = self._runtime_connections(connections)
        return {"summary": summary, "connections": connections, "jobs": jobs, "recentRuns": recent_runs}


    def _runtime_connections(self, profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        endpoints = connection_endpoints(self.settings)
        result = []
        for profile in profiles:
            item = dict(profile)
            endpoint = endpoints.get(item["connection_key"])
            if endpoint is not None:
                if item.get("endpoint") != endpoint:
                    item.update(status="unknown", last_tested_at=None, last_error=None)
                item["endpoint"] = endpoint
            result.append(item)
        return result


    def list_connections(self) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            return self._runtime_connections(_rows(
                connection.execute(
                    text(
                        """
                        SELECT connection_key, kind, display_name, endpoint, database_name,
                               username, secret_ref, enabled, status, last_tested_at,
                               last_error, config, updated_at
                        FROM graphsync.connection_profile ORDER BY connection_key
                        """
                    )
                )
            ))


    def update_connection_status(self, key: str, *, status: str, error: str | None = None) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE graphsync.connection_profile
                    SET status=:status, last_error=:error, last_tested_at=now(),
                        endpoint=COALESCE(:endpoint, endpoint)
                    WHERE connection_key=:key
                    """
                ),
                {"key": key, "status": status, "error": error,
                 "endpoint": connection_endpoints(self.settings).get(key)},
            )


    def update_connection(
        self,
        key: str,
        *,
        kind: str,
        display_name: str,
        endpoint: str,
        database_name: str | None,
        username: str | None,
        enabled: bool,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            previous = connection.execute(
                text(
                    """
                    SELECT database_name
                    FROM graphsync.connection_profile
                    WHERE connection_key=:key
                    FOR UPDATE
                    """
                ),
                {"key": key},
            ).mappings().one_or_none()
            if previous is None:
                raise KeyError(key)
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.connection_profile
                    SET kind=:kind, display_name=:display_name, endpoint=:endpoint,
                        database_name=:database_name, username=:username,
                        enabled=:enabled, config=CAST(:config AS jsonb),
                        status=CASE WHEN :enabled THEN 'unknown' ELSE 'disabled' END,
                        last_error=NULL
                    WHERE connection_key=:key
                    RETURNING connection_key, kind, display_name, endpoint, database_name,
                              username, secret_ref, enabled, status, config, updated_at
                    """
                ),
                {
                    "key": key,
                    "kind": kind,
                    "display_name": display_name,
                    "endpoint": endpoint,
                    "database_name": database_name,
                    "username": username,
                    "enabled": enabled,
                    "config": json.dumps(config, ensure_ascii=False),
                },
            ).mappings().one_or_none()
            synchronized = {"targets": 0, "environments": 0, "jobs": 0}
            previous_graphmart = previous["database_name"]
            if (
                key == "graph-studio"
                and previous_graphmart
                and database_name
                and previous_graphmart != database_name
            ):
                synchronized["targets"] = connection.execute(
                    text(
                        """
                        UPDATE graphsync.graphstudio_target
                        SET graphmart_uri=:new_uri, updated_at=now()
                        WHERE connection_key=:key AND graphmart_uri=:old_uri
                        """
                    ),
                    {"key": key, "old_uri": previous_graphmart, "new_uri": database_name},
                ).rowcount
                synchronized["environments"] = connection.execute(
                    text(
                        """
                        UPDATE graphsync.deployment_environment
                        SET graphmart_uri=:new_uri, updated_at=now()
                        WHERE graphmart_uri=:old_uri
                        """
                    ),
                    {"old_uri": previous_graphmart, "new_uri": database_name},
                ).rowcount
                synchronized["jobs"] = connection.execute(
                    text(
                        """
                        UPDATE graphsync.sync_job
                        SET graphmart_uri=:new_uri, updated_at=now()
                        WHERE graphmart_uri=:old_uri
                        """
                    ),
                    {"old_uri": previous_graphmart, "new_uri": database_name},
                ).rowcount
        result = dict(row)
        result["synchronized_references"] = synchronized
        return result


    def list_navigation(self, *, include_disabled: bool = False) -> list[dict[str, Any]]:
        predicate = "" if include_disabled else "WHERE enabled"
        with self.engine.connect() as connection:
            return _rows(
                connection.execute(
                    text(
                        f"""
                        SELECT menu_key, parent_key, label_zh, label_en, route, icon,
                               sort_order, enabled, capability
                        FROM graphsync.menu_item {predicate}
                        ORDER BY sort_order, menu_key
                        """
                    )
                )
            )


    def update_navigation(
        self,
        key: str,
        *,
        label_zh: str,
        label_en: str,
        sort_order: int,
        enabled: bool,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.menu_item
                    SET label_zh=:label_zh, label_en=:label_en,
                        sort_order=:sort_order, enabled=:enabled
                    WHERE menu_key=:key
                    RETURNING menu_key, label_zh, label_en, route, icon, sort_order, enabled
                    """
                ),
                {
                    "key": key,
                    "label_zh": label_zh,
                    "label_en": label_en,
                    "sort_order": sort_order,
                    "enabled": enabled,
                },
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(key)
        return dict(row)


    def list_settings(self) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            return _rows(
                connection.execute(
                    text(
                        """
                        SELECT setting_key, value, description, editable, updated_at
                        FROM graphsync.app_setting ORDER BY setting_key
                        """
                    )
                )
            )


    def update_setting(self, key: str, value: Any) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.app_setting
                    SET value=CAST(:value AS jsonb), updated_at=now()
                    WHERE setting_key=:key AND editable
                    RETURNING setting_key, value, description, editable, updated_at
                    """
                ),
                {"key": key, "value": json.dumps(value, ensure_ascii=False)},
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(key)
        return dict(row)

