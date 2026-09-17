from pathlib import Path

from src.graphstudio_sync.row_scope import evaluate_row_scope


def test_row_scope_preserves_audit_rows_but_excludes_every_unanchored_record() -> None:
    policies = [
        {
            "policy_key": "workflowstep-manufacturing-workflow-v1",
            "source_contract_key": "workflowstep",
            "anchor_contract_key": "workflow",
            "source_columns": ["WorkflowId"],
            "anchor_columns": ["WorkflowId"],
        }
    ]
    rows = {
        "workflow": [{"WorkflowId": "MFG-1"}],
        "workflowstep": [
            {"WorkflowStepId": "S1", "WorkflowId": "MFG-1"},
            {"WorkflowStepId": "S2", "WorkflowId": "SYSTEM-1"},
            {"WorkflowStepId": "S3", "WorkflowId": "SYSTEM-1"},
        ],
    }

    scoped, excluded = evaluate_row_scope(rows, policies)

    assert [item["WorkflowStepId"] for item in scoped["workflowstep"]] == ["S1"]
    assert excluded["workflowstep-manufacturing-workflow-v1"] == [
        ("SYSTEM-1",), ("SYSTEM-1",),
    ]
    assert len(rows["workflowstep"]) == 3  # input/audit evidence is not mutated


def test_stage_four_schema_and_publish_filter_are_explicit() -> None:
    ddl = Path("sql/graphstudio_sync_control_postgres.sql").read_text(encoding="utf-8")
    deployment = Path("src/graphstudio_sync/publishing/deployment.py").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS graphsync.row_scope_policy" in ddl
    assert "'active', 'out_of_scope', 'quarantined', 'deleted'" in ddl
    assert "AND record_status='active'" in deployment
