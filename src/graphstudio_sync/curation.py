"""Governed Camstar projection preview for the business ontology.

The preview is intentionally bounded and read-only for Camstar and Graph Studio.
It records contracts and aggregate quality evidence in PostgreSQL, but never copies
business rows into ``graphsync`` until a separate approved apply path exists.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import text

from .config import PROJECT_ROOT, SyncSettings
from .connections import resolved_settings
from src.graphstudio_sync.storage.repository import ControlPlaneRepository
from .row_scope import evaluate_row_scope, list_row_scope_policies
from .source_database import (
    ORACLE_KIND,
    connect_source,
    fetch_dicts,
    source_cursor,
    quote_identifier,
)


CURATION_ROOT = PROJECT_ROOT / "outputs" / "graphstudio" / "curation"
SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$#]*$")


def _safe_identifier(value: str, kind: str) -> str:
    if not SAFE_IDENTIFIER.fullmatch(value):
        raise RuntimeError(f"Unsafe source identifier in data contract: {value!r}")
    return quote_identifier(value, kind)


def _columns(
    contract: dict[str, Any],
    relationships: Iterable[dict[str, Any]],
    scope_policies: Iterable[dict[str, Any]] = (),
) -> list[str]:
    values = {
        *contract["primary_key_columns"],
        *contract["business_key_columns"],
        *contract["selected_columns"],
        *contract["required_columns"],
    }
    if contract.get("freshness_column"):
        values.add(contract["freshness_column"])
    for relationship in relationships:
        if relationship["source_contract_key"] == contract["contract_key"]:
            values.update(relationship["source_columns"])
        if relationship["target_contract_key"] == contract["contract_key"]:
            values.update(relationship["target_columns"])
    for policy in scope_policies:
        if policy["source_contract_key"] == contract["contract_key"]:
            values.update(policy["source_columns"])
        if policy["anchor_contract_key"] == contract["contract_key"]:
            values.update(policy["anchor_columns"])
    return sorted(values, key=str.casefold)


def _read_contract_rows(
    source,
    settings: SyncSettings,
    contract: dict[str, Any],
    relationships: list[dict[str, Any]],
    scope_policies: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    columns = _columns(contract, relationships, scope_policies or [])
    selected = ", ".join(_safe_identifier(column, settings.source_kind) for column in columns)
    table = (
        f"{_safe_identifier(contract['source_schema'], settings.source_kind)}."
        f"{_safe_identifier(contract['source_table'], settings.source_kind)}"
    )
    order = ", ".join(
        _safe_identifier(column, settings.source_kind)
        for column in contract["primary_key_columns"]
    )
    limit = int(contract["preview_row_limit"])
    if settings.source_kind == ORACLE_KIND:
        query = f"SELECT {selected} FROM {table} ORDER BY {order} FETCH FIRST {limit} ROWS ONLY"
    else:
        query = f"SELECT TOP ({limit}) {selected} FROM {table} ORDER BY {order}"
    cursor = source_cursor(source, settings.source_kind)
    try:
        cursor.execute(query)
        return fetch_dicts(cursor)
    finally:
        cursor.close()


def _row_key(row: dict[str, Any], columns: list[str]) -> tuple[Any, ...]:
    return tuple(row.get(column) for column in columns)


def _quality_result(
    rule: str,
    passed: bool,
    checked: int,
    failed: int,
    message: str,
    *,
    severity: str = "error",
    contract_key: str | None = None,
    relationship_contract_key: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ruleKey": rule,
        "severity": severity,
        "passed": passed,
        "checkedRows": checked,
        "failedRows": failed,
        "message": message,
        "contractKey": contract_key,
        "relationshipContractKey": relationship_contract_key,
        "details": details or {},
    }


def evaluate_entity_contract(
    contract: dict[str, Any], rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], set[tuple[Any, ...]]]:
    """Evaluate deterministic row-level gates without retaining source payloads."""

    contract_key = contract["contract_key"]
    primary_columns = list(contract["primary_key_columns"])
    business_columns = list(contract["business_key_columns"])
    results: list[dict[str, Any]] = []
    quarantined: set[tuple[Any, ...]] = set()

    approved = contract.get("status") == "approved"
    results.append(
        _quality_result(
            "contract.approved",
            approved,
            1,
            0 if approved else 1,
            "数据契约已批准" if approved else "数据契约仍为草案，不能发布到正式图谱",
            contract_key=contract_key,
        )
    )
    class_approved = contract.get("class_review_status") == "approved"
    results.append(
        _quality_result(
            "profile_class.approved",
            class_approved,
            1,
            0 if class_approved else 1,
            "业务对象角色已批准" if class_approved else "业务对象角色尚未批准",
            contract_key=contract_key,
        )
    )
    mapping_matches = (
        contract.get("mapping_status") == "resolved"
        and contract.get("mapped_schema") == contract.get("source_schema")
        and contract.get("mapped_table") == contract.get("source_table")
    )
    results.append(
        _quality_result(
            "source.mapping_current",
            mapping_matches,
            1,
            0 if mapping_matches else 1,
            "数据契约与当前物理映射一致" if mapping_matches else "数据契约与当前物理映射不一致",
            contract_key=contract_key,
            details={
                "contract": f"{contract.get('source_schema')}.{contract.get('source_table')}",
                "mapping": f"{contract.get('mapped_schema')}.{contract.get('mapped_table')}",
            },
        )
    )

    null_primary = [row for row in rows if any(value in (None, "") for value in _row_key(row, primary_columns))]
    for row in null_primary:
        quarantined.add(_row_key(row, primary_columns))
    results.append(
        _quality_result(
            "primary_key.not_null",
            not null_primary,
            len(rows),
            len(null_primary),
            "主键均不为空" if not null_primary else f"{len(null_primary)} 行主键为空",
            contract_key=contract_key,
        )
    )
    primary_counts = Counter(_row_key(row, primary_columns) for row in rows if row not in null_primary)
    duplicate_primary = {key for key, count in primary_counts.items() if count > 1}
    quarantined.update(duplicate_primary)
    results.append(
        _quality_result(
            "primary_key.unique",
            not duplicate_primary,
            len(rows),
            sum(primary_counts[key] for key in duplicate_primary),
            "预览范围内主键唯一" if not duplicate_primary else f"发现 {len(duplicate_primary)} 个重复主键",
            contract_key=contract_key,
        )
    )
    if business_columns:
        missing_business = [
            row for row in rows
            if any(value in (None, "") for value in _row_key(row, business_columns))
        ]
        results.append(
            _quality_result(
                "business_key.not_null",
                not missing_business,
                len(rows),
                len(missing_business),
                "业务键均不为空" if not missing_business else f"{len(missing_business)} 行业务键不完整",
                severity="warning",
                contract_key=contract_key,
            )
        )
        business_counts = Counter(
            _row_key(row, business_columns) for row in rows if row not in missing_business
        )
        duplicate_business = {key for key, count in business_counts.items() if count > 1}
        results.append(
            _quality_result(
                "business_key.unique",
                not duplicate_business,
                len(rows),
                sum(business_counts[key] for key in duplicate_business),
                "预览范围内业务键唯一" if not duplicate_business else f"发现 {len(duplicate_business)} 个重复业务键",
                severity="warning",
                contract_key=contract_key,
            )
        )
    for column in contract["required_columns"]:
        failed_rows = [row for row in rows if row.get(column) in (None, "")]
        for row in failed_rows:
            quarantined.add(_row_key(row, primary_columns))
        results.append(
            _quality_result(
                f"required.{column}",
                not failed_rows,
                len(rows),
                len(failed_rows),
                f"必填字段 {column} 完整" if not failed_rows else f"{len(failed_rows)} 行缺少 {column}",
                contract_key=contract_key,
            )
        )
    freshness = contract.get("freshness_column")
    if freshness:
        missing_freshness = sum(row.get(freshness) in (None, "") for row in rows)
        results.append(
            _quality_result(
                "freshness.cursor_present",
                missing_freshness == 0,
                len(rows),
                missing_freshness,
                f"增量时间列 {freshness} 均有值" if not missing_freshness else f"{missing_freshness} 行没有 {freshness}，不能可靠使用水位增量",
                severity="warning",
                contract_key=contract_key,
            )
        )
    return results, quarantined


def evaluate_relationship_contract(
    relationship: dict[str, Any],
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    key = relationship["relationship_contract_key"]
    source_columns = list(relationship["source_columns"])
    target_columns = list(relationship["target_columns"])
    match_pairs = [(source_columns, target_columns)]
    for alternative in (relationship.get("config") or {}).get("matchAlternatives", []):
        alternative_source = list(alternative.get("sourceColumns") or [])
        alternative_target = list(alternative.get("targetColumns") or [])
        if alternative_source and len(alternative_source) == len(alternative_target):
            match_pairs.append((alternative_source, alternative_target))
    approved = relationship.get("status") == "approved"
    results = [
        _quality_result(
            "relationship_contract.approved",
            approved,
            1,
            0 if approved else 1,
            "关系契约已批准" if approved else "关系语义仍为草案，不能用于正式图谱",
            relationship_contract_key=key,
        )
    ]
    empty_values = (None, "", "0000000000000000")
    target_keys = [
        {
            _row_key(row, pair_target)
            for row in target_rows
            if all(value not in empty_values for value in _row_key(row, pair_target))
        }
        for _, pair_target in match_pairs
    ]
    missing: list[tuple[Any, ...]] = []
    unresolved: list[tuple[Any, ...]] = []
    for row in source_rows:
        candidates = [
            _row_key(row, pair_source) for pair_source, _ in match_pairs
        ]
        meaningful = [
            (position, value) for position, value in enumerate(candidates)
            if all(item not in empty_values for item in value)
        ]
        if not meaningful:
            missing.append(candidates[0])
        elif not any(value in target_keys[position] for position, value in meaningful):
            unresolved.append(meaningful[0][1])
    severity = "error" if relationship.get("required_context") else "warning"
    results.append(
        _quality_result(
            "relationship.source_present",
            not missing or not relationship.get("required_context"),
            len(source_rows),
            len(missing),
            (
                "关系源键完整"
                if not missing
                else f"可选关系有 {len(missing)} 行未提供源键，不阻断发布"
                if not relationship.get("required_context")
                else f"{len(missing)} 行没有必需的关系源键"
            ),
            severity=severity,
            relationship_contract_key=key,
        )
    )
    results.append(
        _quality_result(
            "relationship.target_resolved",
            not unresolved,
            len(source_rows) - len(missing),
            len(unresolved),
            "关系目标均可解析" if not unresolved else f"{len(unresolved)} 个关系目标在预览目标集中不存在",
            severity=severity,
            relationship_contract_key=key,
        )
    )
    return results


def _record_results(
    connection,
    run_id: uuid.UUID,
    results: list[dict[str, Any]],
) -> None:
    if not results:
        return
    connection.execute(
        text(
            """
            INSERT INTO graphsync.data_quality_result
                (quality_result_id, curation_run_id, contract_key,
                 relationship_contract_key, rule_key, severity, passed,
                 checked_rows, failed_rows, message, details)
            VALUES
                (:id, :run_id, :contract_key, :relationship_contract_key,
                 :rule_key, :severity, :passed, :checked_rows, :failed_rows,
                 :message, CAST(:details AS jsonb))
            """
        ),
        [
            {
                "id": uuid.uuid4(),
                "run_id": run_id,
                "contract_key": item["contractKey"],
                "relationship_contract_key": item["relationshipContractKey"],
                "rule_key": item["ruleKey"],
                "severity": item["severity"],
                "passed": item["passed"],
                "checked_rows": item["checkedRows"],
                "failed_rows": item["failedRows"],
                "message": item["message"],
                "details": json.dumps(item["details"], ensure_ascii=False, default=str),
            }
            for item in results
        ],
    )


def build_curation_preview(
    base_settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    profile_key: str = "opcenter2607-core",
) -> dict[str, Any]:
    """Run bounded quality gates and record evidence without materializing rows."""

    bundle = repository.governance_profile(profile_key)
    profile = repository.graph_profile(profile_key)
    active_classes = {
        item["class_name"] for item in profile.get("classes", []) if item.get("enabled", True)
    }
    active_relationships = {
        (item.get("source_class"), item.get("relationship_name"), item.get("target_class"))
        for item in profile.get("relationships", []) if item.get("enabled", True)
    }
    contracts = [item for item in bundle["contracts"] if item.get("class_name") in active_classes]
    relationships = [
        item for item in bundle["relationships"]
        if (item.get("source_class"), item.get("relationship_name"), item.get("target_class"))
        in active_relationships
    ]
    scope_policies = list_row_scope_policies(repository, profile_key=profile_key)
    if not contracts:
        raise RuntimeError(f"No data contracts configured for business graph profile: {profile_key}")
    run_id = uuid.uuid4()
    lock_name = f"graphsync:curation-preview:{profile_key}"
    with repository.engine.connect() as control:
        acquired = control.execute(
            text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"),
            {"name": lock_name},
        ).scalar_one()
        if not acquired:
            raise RuntimeError(f"A curation preview is already running for {profile_key}")
        try:
            versions = {
                "objects": {item["contract_key"]: item["version"] for item in contracts},
                "relationships": {
                    item["relationship_contract_key"]: item["version"]
                    for item in relationships
                },
            }
            control.execute(
                text(
                    """
                    INSERT INTO graphsync.curation_run
                        (curation_run_id, profile_key, status, preview_only,
                         contract_versions)
                    VALUES (:run_id, :profile_key, 'started', true,
                            CAST(:versions AS jsonb))
                    """
                ),
                {
                    "run_id": run_id,
                    "profile_key": profile_key,
                    "versions": json.dumps(versions),
                },
            )
            control.commit()
            try:
                settings = resolved_settings(base_settings, repository)
                source = connect_source(settings)
                try:
                    rows_by_contract: dict[str, list[dict[str, Any]]] = {}
                    results: list[dict[str, Any]] = []
                    quarantined_by_contract: dict[str, set[tuple[Any, ...]]] = {}
                    truncated_contracts: list[str] = []
                    for contract in contracts:
                        rows = _read_contract_rows(
                            source, settings, contract, relationships, scope_policies,
                        )
                        rows_by_contract[contract["contract_key"]] = rows
                        entity_results, quarantined = evaluate_entity_contract(contract, rows)
                        results.extend(entity_results)
                        quarantined_by_contract[contract["contract_key"]] = quarantined
                        approximate = int(contract.get("approximate_rows") or 0)
                        if approximate > int(contract["preview_row_limit"]):
                            truncated_contracts.append(contract["contract_key"])
                            results.append(
                                _quality_result(
                                    "preview.complete",
                                    False,
                                    len(rows),
                                    approximate - len(rows),
                                    "预览达到行数上限，只能用于设计审核，不能证明全量数据可发布",
                                    severity="warning",
                                    contract_key=contract["contract_key"],
                                    details={"approximateRows": approximate, "previewLimit": contract["preview_row_limit"]},
                                )
                            )
                    scoped_rows_by_contract, scope_exclusions = evaluate_row_scope(
                        rows_by_contract, scope_policies,
                    )
                    for policy in scope_policies:
                        excluded_count = len(scope_exclusions.get(policy["policy_key"], []))
                        results.append(
                            _quality_result(
                                "row_scope.anchor_exists",
                                True,
                                len(rows_by_contract.get(policy["source_contract_key"], [])),
                                0,
                                f"{excluded_count} 行位于制造业务图谱作用域之外，保留审计但不发布",
                                severity="warning",
                                contract_key=policy["source_contract_key"],
                                details={
                                    "policyKey": policy["policy_key"],
                                    "excludedRows": excluded_count,
                                    "reason": policy["reason"],
                                },
                            )
                        )
                    for relationship in relationships:
                        results.extend(
                            evaluate_relationship_contract(
                                relationship,
                                scoped_rows_by_contract[relationship["source_contract_key"]],
                                scoped_rows_by_contract[relationship["target_contract_key"]],
                            )
                        )
                finally:
                    source.close()

                failed_errors = [
                    item for item in results
                    if item["severity"] == "error" and not item["passed"]
                ]
                source_rows = sum(len(rows) for rows in rows_by_contract.values())
                quarantined_rows = sum(len(values) for values in quarantined_by_contract.values())
                scope_excluded_rows = sum(len(values) for values in scope_exclusions.values())
                approvals_complete = all(item["status"] == "approved" for item in contracts) and all(
                    item["status"] == "approved" for item in relationships
                )
                publishable = not failed_errors and approvals_complete and not truncated_contracts
                severity_counts = Counter(
                    item["severity"] for item in results if not item["passed"]
                )
                summary = {
                    "contracts": len(contracts),
                    "relationshipContracts": len(relationships),
                    "contractsApproved": sum(item["status"] == "approved" for item in contracts),
                    "relationshipContractsApproved": sum(item["status"] == "approved" for item in relationships),
                    "failedErrors": severity_counts["error"],
                    "failedWarnings": severity_counts["warning"],
                    "truncatedContracts": truncated_contracts,
                }
                output_dir = CURATION_ROOT / str(run_id)
                output_dir.mkdir(parents=True, exist_ok=False)
                artifact = output_dir / "governance_preview.json"
                payload = {
                    "runId": str(run_id),
                    "profileKey": profile_key,
                    "previewOnly": True,
                    "camstarMutated": False,
                    "curatedBusinessRowsWritten": 0,
                    "graphStudioMutated": False,
                    "sourceRowsRead": source_rows,
                    "acceptedRows": source_rows - quarantined_rows,
                    "publishableRows": source_rows - quarantined_rows - scope_excluded_rows,
                    "quarantinedRows": quarantined_rows,
                    "scopeExcludedRows": scope_excluded_rows,
                    "publishable": publishable,
                    "summary": summary,
                    "qualityResults": results,
                    "artifact": str(artifact),
                }
                artifact.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
                    encoding="utf-8",
                )
                digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
                summary["artifact"] = str(artifact)
                summary["artifactSha256"] = digest
                _record_results(control, run_id, results)
                control.execute(
                    text(
                        """
                        UPDATE graphsync.curation_run
                        SET status='succeeded', finished_at=now(),
                            source_rows_read=:source_rows,
                            accepted_rows=:accepted_rows,
                            quarantined_rows=:quarantined_rows,
                            publishable=:publishable,
                            summary=CAST(:summary AS jsonb)
                        WHERE curation_run_id=:run_id
                        """
                    ),
                    {
                        "run_id": run_id,
                        "source_rows": source_rows,
                        "accepted_rows": source_rows - quarantined_rows,
                        "quarantined_rows": quarantined_rows,
                        "publishable": publishable,
                        "summary": json.dumps(summary, ensure_ascii=False),
                    },
                )
                control.commit()
                return payload
            except Exception as exc:
                control.rollback()
                control.execute(
                    text(
                        """
                        UPDATE graphsync.curation_run
                        SET status='failed', finished_at=now(),
                            error=CAST(:error AS jsonb)
                        WHERE curation_run_id=:run_id
                        """
                    ),
                    {
                        "run_id": run_id,
                        "error": json.dumps(
                            {"type": type(exc).__name__, "message": str(exc)[:4000]},
                            ensure_ascii=False,
                        ),
                    },
                )
                control.commit()
                raise
        finally:
            control.execute(
                text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"),
                {"name": lock_name},
            )
            control.commit()
