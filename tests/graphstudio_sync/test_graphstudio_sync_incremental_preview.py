import zipfile

from src.graphstudio_sync.incremental_preview import (
    _write_change_archive,
    build_incremental_preview,
)

from test_graphstudio_sync_connections import _settings


class EmptyWindowRepository:
    def latest_incremental_windows(self, job_name):
        assert job_name == "camstar-full"
        return []


class BaselineWindowRepository:
    def latest_incremental_windows(self, job_name):
        assert job_name == "camstar-full"
        return [{
            "window_id": "11111111-1111-1111-1111-111111111111",
            "class_name": "WorkflowStep",
            "status": "baseline_required",
        }]


def test_incremental_preview_is_safe_noop_without_windows() -> None:
    result = build_incremental_preview(
        _settings(), EmptyWindowRepository(), job_name="camstar-full"
    )

    assert result["status"] == "no_incremental_windows"
    assert result["events"] == 0
    assert result["graphStudioMutated"] is False
    assert result["checkpointCommitted"] is False


def test_incremental_preview_leaves_baseline_for_snapshot_materialization() -> None:
    result = build_incremental_preview(
        _settings(), BaselineWindowRepository(), job_name="camstar-full",
    )

    assert result["status"] == "baseline_required"
    assert result["baselineClasses"] == ["WorkflowStep"]
    assert result["events"] == 0
    assert result["checkpointCommitted"] is False


def test_change_archive_layout_is_deterministic(tmp_path) -> None:
    first = tmp_path / "Product.jsonl"
    second = tmp_path / "MfgOrder.jsonl"
    first.write_text('{"operation":"update"}\n', encoding="utf-8")
    second.write_text('{"operation":"delete"}\n', encoding="utf-8")

    archive = _write_change_archive(tmp_path, [first, second])

    with zipfile.ZipFile(archive) as bundle:
        assert bundle.namelist() == ["changes/MfgOrder.jsonl", "changes/Product.jsonl"]
        assert bundle.testzip() is None
        assert all(item.date_time == (1980, 1, 1, 0, 0, 0) for item in bundle.infolist())
