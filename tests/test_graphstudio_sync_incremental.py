from src.graphstudio_sync import incremental

from test_graphstudio_sync_connections import _settings


def _policy(class_name="HistoryMainline", strategy="cdc"):
    return {
        "class_name": class_name,
        "physical_schema": "CamstarPRD_SCHEMA",
        "physical_table": class_name,
        "effective_strategy": strategy,
        "watermark_column": "LastUpdatedDate" if strategy != "cdc" else None,
        "enabled": True,
    }


def _probe(table, *, position=120):
    return {
        "sourceKind": "camstar_sqlserver",
        "sourcePosition": {"changeTrackingVersion": position, "cdcMaxLsn": None},
        "tables": [table],
    }


def test_change_tracking_window_uses_frozen_upper_bound() -> None:
    table = {
        "className": "HistoryMainline",
        "nativeAdapter": "sqlserver_change_tracking",
        "changeTracking": {"min_valid_version": 80},
    }
    checkpoints = {
        "HistoryMainline": {"committed_watermark": {"changeTrackingVersion": 100}}
    }

    windows = incremental.plan_incremental_windows(
        _settings(), [_policy()], _probe(table), checkpoints
    )

    assert windows[0]["status"] == "planned"
    assert windows[0]["lower_bound"] == {"changeTrackingVersion": 100}
    assert windows[0]["upper_bound"] == {"changeTrackingVersion": 120}


def test_expired_change_tracking_checkpoint_is_blocked() -> None:
    table = {
        "className": "HistoryMainline",
        "nativeAdapter": "sqlserver_change_tracking",
        "changeTracking": {"min_valid_version": 110},
    }
    checkpoints = {
        "HistoryMainline": {"committed_watermark": {"changeTrackingVersion": 100}}
    }

    window = incremental.plan_incremental_windows(
        _settings(), [_policy()], _probe(table), checkpoints
    )[0]

    assert window["status"] == "blocked"
    assert window["metadata"]["reason"] == "checkpoint_before_min_valid_change_tracking_version"


def test_incremental_table_without_checkpoint_requires_baseline() -> None:
    table = {
        "className": "HistoryMainline",
        "nativeAdapter": "sqlserver_change_tracking",
        "changeTracking": {"min_valid_version": 80},
    }

    window = incremental.plan_incremental_windows(
        _settings(), [_policy()], _probe(table), {}
    )[0]

    assert window["status"] == "baseline_required"


def test_cdc_policy_without_native_capture_is_blocked() -> None:
    table = {
        "className": "HistoryMainline",
        "nativeAdapter": None,
        "changeTracking": None,
        "cdc": None,
    }

    window = incremental.plan_incremental_windows(
        _settings(), [_policy()], _probe(table, position=None), {}
    )[0]

    assert window["status"] == "blocked"
    assert window["metadata"]["reason"] == "native_change_capture_not_enabled"


def test_watermark_window_reads_upper_bound_without_full_scan(monkeypatch) -> None:
    monkeypatch.setattr(
        incremental,
        "read_watermark_upper_bound",
        lambda *args, **kwargs: "2026-08-13T12:00:00+00:00",
    )
    table = {"className": "MfgOrder", "nativeAdapter": None}
    checkpoints = {
        "MfgOrder": {"committed_watermark": {"watermark": "2026-08-13T11:00:00+00:00"}}
    }

    window = incremental.plan_incremental_windows(
        _settings(), [_policy("MfgOrder", "watermark")], _probe(table), checkpoints
    )[0]

    assert window["adapter"] == "database_watermark"
    assert window["status"] == "planned"
    assert window["upper_bound"]["watermark"] == "2026-08-13T12:00:00+00:00"
