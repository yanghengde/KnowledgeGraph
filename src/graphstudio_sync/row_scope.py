"""Audited row-level publication scope for the governed business graph."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from src.graphstudio_sync.storage.repository import ControlPlaneRepository


EMPTY_REFERENCE_VALUES = {None, "", "0000000000000000"}


def list_row_scope_policies(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
) -> list[dict[str, Any]]:
    with repository.engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                text(
                    """
                    SELECT policy_key, profile_key, source_contract_key,
                           anchor_contract_key, source_columns, anchor_columns,
                           action, reason, enabled, version, config, updated_at
                    FROM graphsync.row_scope_policy
                    WHERE profile_key=:profile AND enabled
                    ORDER BY policy_key
                    """
                ),
                {"profile": profile_key},
            ).mappings()
        ]


def evaluate_row_scope(
    rows_by_contract: dict[str, list[dict[str, Any]]],
    policies: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[tuple[Any, ...]]]]:
    """Return in-scope preview rows and the excluded source keys per policy."""

    in_scope = {key: list(rows) for key, rows in rows_by_contract.items()}
    excluded: dict[str, list[tuple[Any, ...]]] = {}
    for policy in policies:
        source_columns = list(policy["source_columns"])
        anchor_columns = list(policy["anchor_columns"])
        anchor_keys = {
            tuple(row.get(column) for column in anchor_columns)
            for row in rows_by_contract.get(policy["anchor_contract_key"], [])
            if all(row.get(column) not in EMPTY_REFERENCE_VALUES for column in anchor_columns)
        }
        retained: list[dict[str, Any]] = []
        rejected: list[tuple[Any, ...]] = []
        for row in in_scope.get(policy["source_contract_key"], []):
            key = tuple(row.get(column) for column in source_columns)
            if key in anchor_keys:
                retained.append(row)
            else:
                rejected.append(key)
        in_scope[policy["source_contract_key"]] = retained
        excluded[policy["policy_key"]] = rejected
    return in_scope, excluded


def apply_release_row_scope(
    connection,
    *,
    release_id,
    policies: list[dict[str, Any]],
) -> dict[str, int]:
    """Mark out-of-scope objects in-place inside one still-unpublished release."""

    counts: dict[str, int] = {}
    for policy in policies:
        source_columns = list(policy["source_columns"])
        anchor_columns = list(policy["anchor_columns"])
        if not source_columns or len(source_columns) != len(anchor_columns):
            raise RuntimeError(f"Invalid row scope policy columns: {policy['policy_key']}")
        comparisons = []
        for source_column, anchor_column in zip(source_columns, anchor_columns, strict=True):
            safe_source = str(source_column).replace("'", "''")
            safe_anchor = str(anchor_column).replace("'", "''")
            comparisons.append(
                f"anchor.source_values ->> '{safe_anchor}' = source.source_values ->> '{safe_source}'"
            )
        result = connection.execute(
            text(
                f"""
                UPDATE graphsync.object_version source
                SET record_status='out_of_scope',
                    quality_issues=source.quality_issues || jsonb_build_array(
                        jsonb_build_object(
                            'rule', 'row_scope.anchor_exists',
                            'policyKey', CAST(:policy AS text),
                            'reason', CAST(:reason AS text)
                        )
                    )
                WHERE source.release_id=:release
                  AND source.contract_key=:source_contract
                  AND source.record_status='active'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM graphsync.object_version anchor
                      WHERE anchor.release_id=source.release_id
                        AND anchor.contract_key=:anchor_contract
                        AND anchor.record_status='active'
                        AND {' AND '.join(comparisons)}
                  )
                """
            ),
            {
                "release": release_id,
                "policy": policy["policy_key"],
                "reason": policy["reason"],
                "source_contract": policy["source_contract_key"],
                "anchor_contract": policy["anchor_contract_key"],
            },
        )
        counts[policy["policy_key"]] = int(result.rowcount or 0)
    return counts
