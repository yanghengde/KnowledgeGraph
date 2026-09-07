from pathlib import Path

import pytest

from src.graphstudio_sync import data_sync as data_sync_module


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, *_args, **_kwargs):
        return _ScalarResult(True)


class _Engine:
    def connect(self):
        return _Connection()


class _Repository:
    engine = _Engine()

    def graph_profile(self, _profile_key):
        return {"profile": {"job_name": "camstar-full"}}

    def list_table_policies(self, _job_name):
        return [{"class_name": "Product", "enabled": True, "effective_strategy": "snapshot"}]


def test_data_sync_blocks_incomplete_ontology_coverage(monkeypatch) -> None:
    monkeypatch.setattr(
        data_sync_module,
        "data_sync_status",
        lambda *_args, **_kwargs: {
            "coverage": {"missing": 1},
            "blockers": ["Spec is missing"],
        },
    )

    with pytest.raises(RuntimeError, match="coverage is incomplete"):
        data_sync_module.execute_data_sync(
            object(), _Repository(), profile_key="core", actor="tester",
        )


def test_snapshot_data_sync_runs_quality_then_activates_without_graphstudio(monkeypatch) -> None:
    status = {
        "coverage": {"missing": 0},
        "blockers": [],
        "classes": [{"className": "Product", "coverageStatus": "synchronized"}],
    }
    statuses = iter([status, {**status, "activeRelease": {"release_no": 8}}])
    calls = []
    monkeypatch.setattr(
        data_sync_module, "data_sync_status",
        lambda *_args, **_kwargs: next(statuses),
    )
    monkeypatch.setattr(
        data_sync_module, "build_curation_preview",
        lambda *_args, **_kwargs: calls.append("quality") or {"publishable": True},
    )
    monkeypatch.setattr(
        data_sync_module, "execute_materialization",
        lambda *_args, **kwargs: calls.append(("materialize", kwargs["activate"]))
        or {"releaseId": "release-8", "status": "active"},
    )
    monkeypatch.setattr(
        data_sync_module, "execute_incremental_plan",
        lambda *_args, **_kwargs: pytest.fail("snapshot lane must not run an incremental plan"),
    )

    result = data_sync_module.execute_data_sync(
        object(), _Repository(), profile_key="core", actor="tester",
    )

    assert calls == ["quality", ("materialize", True)]
    assert result["graphStudioMutated"] is False
    assert result["status"]["activeRelease"]["release_no"] == 8


def test_data_sync_api_and_react_route_are_exposed() -> None:
    router = Path("web/routers/sync_center.py").read_text(encoding="utf-8")
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    shell = Path("frontend/src/components/layout/AppShell.tsx").read_text(encoding="utf-8")

    assert '@router.get("/profiles/{profile_key}/data-sync")' in router
    assert '@router.post("/profiles/{profile_key}/data-sync")' in router
    assert '@router.put("/profiles/{profile_key}/data-sync/schedule")' in router
    assert 'path="data-sync"' in app
    assert 'label: "制造数据同步"' in shell


def test_data_lane_has_no_graphstudio_deployment_dependency() -> None:
    source = Path("src/graphstudio_sync/data_sync.py").read_text(encoding="utf-8")

    assert "from .deployment" not in source
    assert '"graphStudioMutated": False' in source


def test_data_lane_scheduler_uses_database_lease_and_audit_tables() -> None:
    source = Path("src/graphstudio_sync/data_sync.py").read_text(encoding="utf-8")
    ddl = Path("sql/graphstudio_sync_control_postgres.sql").read_text(encoding="utf-8")

    assert "FOR UPDATE SKIP LOCKED" in source
    assert "graphsync.data_sync_execution" in source
    assert "CREATE TABLE IF NOT EXISTS graphsync.data_sync_schedule" in ddl
    assert "CREATE TABLE IF NOT EXISTS graphsync.data_sync_worker_heartbeat" in ddl
