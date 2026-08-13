"""Immutable, batched materialization of approved Camstar data contracts.

The active curated release is a pointer.  New releases are populated in
isolation and become visible only after verification, which keeps rollback
constant-time and avoids in-place rewrites of very large source tables.
"""

from __future__ import annotations

import datetime as dt
import decimal
import hashlib
import json
import uuid
from itertools import islice
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

from sqlalchemy import text

from .attribute_projection import apply_attribute_projections
from .config import SyncSettings
from .connections import resolved_settings
from .preview import _iter_rows
from .repository import ControlPlaneRepository
from .source_database import connect_source


DATA_NAMESPACE = "https://opcenter.siemens.com/data/camstar/2607/ontology"


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def object_uri(class_name: str, primary_key: dict[str, Any]) -> str:
    if not primary_key or any(value in (None, "") for value in primary_key.values()):
        raise ValueError(f"Cannot create {class_name} URI from an incomplete primary key")
    ordered = "|".join(f"{key}={_jsonable(value)}" for key, value in primary_key.items())
    return f"{DATA_NAMESPACE}/{quote(class_name, safe='-._~')}/{quote(ordered, safe='-._~')}"


def apply_transform(expression: str | None, row: dict[str, Any], source_column: str | None) -> Any:
    """Evaluate the deliberately small, auditable transform language."""

    if not expression:
        return row.get(source_column) if source_column else None
    command, separator, argument = expression.partition(":")
    if not separator:
        raise ValueError(f"Transform must use command:value syntax: {expression}")
    command = command.strip().casefold()
    argument = argument.strip()
    if command == "source":
        return row.get(argument)
    if command == "constant":
        try:
            return json.loads(argument)
        except json.JSONDecodeError:
            return argument
    if command == "coalesce":
        for column in (value.strip() for value in argument.split(",")):
            value = row.get(column)
            if value not in (None, ""):
                return value
        return None
    if command in {"trim", "upper", "lower"}:
        value = row.get(argument)
        if value is None:
            return None
        rendered = str(value).strip()
        return rendered.upper() if command == "upper" else rendered.lower() if command == "lower" else rendered
    raise ValueError(f"Unsupported governed transform command: {command}")


def build_materialization_plan(
    governance: dict[str, Any],
    schema_changes: Iterable[dict[str, Any]],
    *,
    profile_key: str,
    batch_rows: int = 10_000,
    table_policies: Iterable[dict[str, Any]] = (),
    incremental_windows: Iterable[dict[str, Any]] = (),
    active_release_id: str | None = None,
    active_source_snapshot: dict[str, Any] | None = None,
    active_contract_versions: dict[str, Any] | None = None,
    large_table_threshold: int = 5_000_000,
    attribute_projections: Iterable[dict[str, Any]] = (),
    profile_classes: Iterable[dict[str, Any]] = (),
    profile_relationships: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    contracts = list(governance.get("contracts") or [])
    relationships = list(governance.get("relationships") or [])
    schema_changes = list(schema_changes)
    governed_classes = [item for item in profile_classes if item.get("enabled", True)]
    governed_relationships = [item for item in profile_relationships if item.get("enabled", True)]
    if governed_classes:
        governed_class_names = {item.get("class_name") for item in governed_classes}
        contracts = [item for item in contracts if item.get("class_name") in governed_class_names]
    latest = governance.get("latestRun")
    blockers: list[str] = []
    if not contracts:
        blockers.append("业务图谱没有数据契约")
    contract_classes = {item["class_name"] for item in contracts}
    for item in governed_classes:
        if item["class_name"] not in contract_classes:
            blockers.append(f"发布对象缺少数据契约：{item['class_name']}")
    contract_relationships = {
        (item.get("source_class"), item.get("relationship_name"), item.get("target_class"))
        for item in relationships
    }
    governed_relationship_identities = {
        (item.get("source_class"), item.get("relationship_name"), item.get("target_class"))
        for item in governed_relationships
    }
    for item in governed_relationships:
        identity = (item.get("source_class"), item.get("relationship_name"), item.get("target_class"))
        if identity not in contract_relationships:
            blockers.append(
                "发布关系缺少关系契约："
                f"{item.get('source_class')}.{item.get('relationship_name')}->{item.get('target_class')}"
            )
    # Relationship contracts are versioned and retained for audit.  A retired or
    # historical contract outside the active profile must not block, nor leak
    # into, the current data release.
    relationships = [
        item for item in relationships
        if (item.get("source_class"), item.get("relationship_name"), item.get("target_class"))
        in governed_relationship_identities
    ]
    for contract in contracts:
        if contract.get("status") != "approved":
            blockers.append(f"数据契约未批准：{contract['contract_key']}")
        if contract.get("class_review_status") != "approved":
            blockers.append(f"对象角色未批准：{contract['class_name']}")
        if contract.get("mapping_status") != "resolved":
            blockers.append(f"物理映射未解析：{contract['class_name']}")
    for relationship in relationships:
        if relationship.get("status") != "approved":
            blockers.append(f"关系契约未批准：{relationship['relationship_contract_key']}")
    if not latest:
        blockers.append("尚未运行治理质量预览")
    elif not latest.get("publishable"):
        blockers.append("最近治理质量预览未通过发布门禁")
    else:
        expected = {item["contract_key"]: int(item["version"]) for item in contracts}
        actual = (latest.get("contract_versions") or {}).get("objects", {})
        if actual != expected:
            blockers.append("最近质量预览使用的数据契约版本已经过期")
    pending_changes = [
        item for item in schema_changes
        if item.get("status") in {"approved", "applying", "failed"}
    ]
    if pending_changes:
        blockers.append(f"存在 {len(pending_changes)} 个尚未完成或回滚的 Schema 变更")
    projections = [item for item in attribute_projections if item.get("enabled")]
    for projection in projections:
        if projection.get("status") != "approved":
            blockers.append(f"属性投影未批准：{projection['projection_key']}")
        elif projection.get("preview_status") != "succeeded":
            blockers.append(f"属性投影尚无成功预览：{projection['projection_key']}")
    policies = {item["class_name"]: item for item in table_policies}
    windows = {item["class_name"]: item for item in incremental_windows}
    active_versions = dict(active_contract_versions or {})
    contract_plans: list[dict[str, Any]] = []
    for item in contracts:
        approximate = int(item.get("approximate_rows") or 0)
        policy = policies.get(item["class_name"])
        strategy = (policy or {}).get("effective_strategy") or (policy or {}).get("strategy") or "snapshot"
        extraction_mode = "keyset_snapshot"
        current_version = int(item["version"])
        previous_version = int(active_versions.get(item["contract_key"]) or 0)
        applied_changes = [
            change for change in schema_changes
            if change.get("contract_key") == item["contract_key"]
            and change.get("status") == "applied"
            and previous_version < int(change.get("target_version") or 0) <= current_version
        ]
        backfill_items = [
            operation
            for change in sorted(applied_changes, key=lambda value: int(value.get("target_version") or 0))
            for operation in (change.get("items") or [])
        ]
        remove_fields = sorted({
            str((operation.get("before_state") or {}).get("target_field"))
            for operation in backfill_items
            if operation.get("operation") in {"retire_field", "rename_field"}
            and (operation.get("before_state") or {}).get("target_field")
        })
        affected_field_keys = sorted({
            str(operation.get("field_key"))
            for operation in backfill_items
            if operation.get("operation") not in {"deprecate_field", "retire_field"}
            and operation.get("field_key")
        })
        field_backfill = None
        if active_release_id and previous_version and previous_version < current_version:
            extraction_mode = "field_backfill"
            field_backfill = {
                "fromVersion": previous_version,
                "toVersion": current_version,
                "changeIds": [str(change["change_id"]) for change in applied_changes],
                "affectedFieldKeys": affected_field_keys,
                "removeTargetFields": remove_fields,
            }
            if not applied_changes:
                blockers.append(
                    f"数据契约 {item['contract_key']} 已从 v{previous_version} 升级到 v{current_version}，但找不到已应用的迁移记录"
                )
        elif approximate > large_table_threshold:
            if not policy or policy.get("requires_review"):
                blockers.append(f"亿级/大表尚未显式配置同步策略：{item['class_name']}（约 {approximate} 行）")
            elif strategy == "snapshot":
                blockers.append(f"大表禁止日常全量物化：{item['class_name']}；应启用 CDC/SCN 并先完成受控基线")
            elif not active_release_id:
                blockers.append(f"大表 {item['class_name']} 尚无活动基线版本，必须先执行分区基线导入")
            else:
                window = windows.get(item["class_name"])
                if not window or window.get("status") != "verified" or not (window.get("metadata") or {}).get("changeFile"):
                    blockers.append(f"大表 {item['class_name']} 没有已验证的增量变更包")
                else:
                    extraction_mode = "verified_incremental_package"
                    if str((active_source_snapshot or {}).get(item["class_name"], {}).get("windowId")) == str(window["window_id"]):
                        blockers.append(f"大表 {item['class_name']} 的最新增量窗口已被活动治理版本消费")
        contract_plans.append(
            {
                "contractKey": item["contract_key"],
                "className": item["class_name"],
                "version": item["version"],
                "source": f"{item['source_schema']}.{item['source_table']}",
                "primaryKey": item["primary_key_columns"],
                "approximateRows": approximate,
                "strategy": strategy,
                "extractionMode": extraction_mode,
                "incrementalWindow": (
                    {
                        "windowId": str(windows[item["class_name"]]["window_id"]),
                        "runId": str(windows[item["class_name"]].get("run_id")) if windows[item["class_name"]].get("run_id") else None,
                        "changeFile": (windows[item["class_name"]].get("metadata") or {}).get("changeFile"),
                        "upperBound": windows[item["class_name"]].get("upper_bound"),
                    }
                    if extraction_mode == "verified_incremental_package" else None
                ),
                "fieldBackfill": field_backfill,
            }
        )
    return {
        "profileKey": profile_key,
        "ready": not blockers,
        "blockers": blockers,
        "batchRows": int(batch_rows),
        "strategy": "immutable_release_keyset_batches",
        "activation": "verified_pointer_switch",
        "rollback": "restore_previous_release_pointer",
        "activeReleaseId": active_release_id,
        "activeContractVersions": active_versions,
        "schemaChangeIds": sorted({
            change_id
            for contract in contract_plans
            for change_id in ((contract.get("fieldBackfill") or {}).get("changeIds") or [])
        }),
        "contracts": contract_plans,
        "relationships": [item["relationship_contract_key"] for item in relationships],
        "attributeProjections": [
            {
                "projectionKey": item["projection_key"],
                "targetContractKey": item["target_contract_key"],
                "version": item["version"],
                "fieldCount": len(item.get("fields") or []),
            }
            for item in projections
        ],
    }


def normalize_object_record(
    contract: dict[str, Any],
    fields: Iterable[dict[str, Any]],
    row: dict[str, Any],
) -> dict[str, Any]:
    primary_key = {column: _jsonable(row.get(column)) for column in contract["primary_key_columns"]}
    business_key = {column: _jsonable(row.get(column)) for column in contract["business_key_columns"]}
    issues: list[str] = []
    if any(value in (None, "") for value in primary_key.values()):
        issues.append("primary_key.not_null")
    properties: dict[str, Any] = {}
    source_values: dict[str, Any] = {}
    for field in fields:
        if field.get("lifecycle_status") == "retired":
            continue
        source_column = field.get("source_column")
        if source_column:
            source_values[source_column] = _jsonable(row.get(source_column))
        value = apply_transform(field.get("transform_expression"), row, source_column)
        if value in (None, "") and field.get("default_expression"):
            value = apply_transform(f"constant:{field['default_expression']}", row, None)
        value = _jsonable(value)
        if field.get("required") and value in (None, ""):
            issues.append(f"required.{field['field_key']}")
        properties[field["target_field"]] = value
    uri = object_uri(contract["class_name"], primary_key) if not issues or "primary_key.not_null" not in issues else ""
    payload = {
        "sourcePrimaryKey": primary_key,
        "businessKey": business_key,
        "sourceValues": source_values,
        "properties": properties,
    }
    return {
        "objectUri": uri,
        **payload,
        "sourceHash": content_hash(payload),
        "sourceChangeAt": _jsonable(row.get(contract.get("freshness_column"))) if contract.get("freshness_column") else None,
        "recordStatus": "quarantined" if issues else "active",
        "qualityIssues": issues,
    }


def _field_source_columns(field: dict[str, Any]) -> set[str]:
    """Return every physical column referenced by one governed transform."""

    columns = {str(field["source_column"])} if field.get("source_column") else set()
    expression = str(field.get("transform_expression") or "")
    command, separator, argument = expression.partition(":")
    if not separator:
        return columns
    command = command.strip().casefold()
    if command in {"source", "trim", "upper", "lower"} and argument.strip():
        columns.add(argument.strip())
    elif command == "coalesce":
        columns.update(value.strip() for value in argument.split(",") if value.strip())
    return columns


def build_field_backfill_patch(
    contract: dict[str, Any],
    fields: Iterable[dict[str, Any]],
    row: dict[str, Any],
) -> dict[str, Any]:
    """Build a narrow property patch without re-reading an entire source row."""

    primary_key = {
        column: _jsonable(row.get(column))
        for column in contract["primary_key_columns"]
    }
    uri = object_uri(contract["class_name"], primary_key)
    properties: dict[str, Any] = {}
    source_values: dict[str, Any] = {}
    issues: list[str] = []
    for field in fields:
        for source_column in _field_source_columns(field):
            source_values[source_column] = _jsonable(row.get(source_column))
        value = apply_transform(
            field.get("transform_expression"), row, field.get("source_column"),
        )
        if value in (None, "") and field.get("default_expression"):
            value = apply_transform(
                f"constant:{field['default_expression']}", row, None,
            )
        value = _jsonable(value)
        if field.get("required") and value in (None, ""):
            issues.append(f"required.{field['field_key']}")
        if value not in (None, ""):
            properties[field["target_field"]] = value
    payload = {
        "sourcePrimaryKey": primary_key,
        "sourceValues": source_values,
        "properties": properties,
    }
    return {
        "objectUri": uri,
        "sourceValues": source_values,
        "properties": properties,
        "qualityIssues": issues,
        "patchHash": content_hash(payload),
    }


def _insert_object_records(
    connection,
    records: list[dict[str, Any]],
    *,
    release_id: uuid.UUID,
    profile_key: str,
    contract: dict[str, Any],
) -> None:
    if not records:
        return
    connection.execute(
        text(
            """
            INSERT INTO graphsync.object_version
                (release_id, profile_key, contract_key, contract_version,
                 class_name, object_uri, source_primary_key, business_key,
                 source_values, properties, source_hash, source_change_at,
                 record_status, quality_issues)
            VALUES
                (:release_id, :profile_key, :contract_key, :contract_version,
                 :class_name, :object_uri, CAST(:source_primary_key AS jsonb),
                 CAST(:business_key AS jsonb), CAST(:source_values AS jsonb),
                 CAST(:properties AS jsonb), :source_hash,
                 CAST(:source_change_at AS timestamptz), :record_status,
                 CAST(:quality_issues AS jsonb))
            """
        ),
        [
            {
                "release_id": release_id,
                "profile_key": profile_key,
                "contract_key": contract["contract_key"],
                "contract_version": contract["version"],
                "class_name": contract["class_name"],
                "object_uri": item["objectUri"],
                "source_primary_key": canonical_json(item["sourcePrimaryKey"]),
                "business_key": canonical_json(item["businessKey"]),
                "source_values": canonical_json(item["sourceValues"]),
                "properties": canonical_json(item["properties"]),
                "source_hash": item["sourceHash"],
                "source_change_at": item["sourceChangeAt"],
                "record_status": item["recordStatus"],
                "quality_issues": canonical_json(item["qualityIssues"]),
            }
            for item in records
        ],
    )


def _chunks(iterator, size: int):
    while True:
        page = list(islice(iterator, size))
        if not page:
            return
        yield page


def _release_plan_from_repository(repository: ControlPlaneRepository, profile_key: str, batch_rows: int) -> tuple[dict[str, Any], dict[str, Any]]:
    governance = repository.governance_profile(profile_key)
    graph_profile = repository.graph_profile(profile_key)
    changes = repository.list_schema_changes(profile_key, limit=500)
    projections = repository.list_attribute_projections(profile_key)
    policies = repository.list_table_policies("camstar-full")
    windows = repository.latest_incremental_windows("camstar-full")
    with repository.engine.connect() as connection:
        active_release = connection.execute(
            text("SELECT active.active_release_id, release.source_snapshot, release.contract_versions FROM graphsync.curated_release_activation active JOIN graphsync.curated_release release ON release.release_id=active.active_release_id WHERE active.profile_key=:profile_key"),
            {"profile_key": profile_key},
        ).mappings().one_or_none()
        threshold = int(connection.execute(
            text("SELECT coalesce((value #>> '{}')::bigint, 5000000) FROM graphsync.app_setting WHERE setting_key='sync.snapshot_row_threshold'")
        ).scalar_one_or_none() or 5_000_000)
    return governance, build_materialization_plan(
        governance, changes, profile_key=profile_key, batch_rows=batch_rows,
        table_policies=policies, incremental_windows=windows,
        active_release_id=str(active_release["active_release_id"]) if active_release else None,
        active_source_snapshot=dict(active_release["source_snapshot"] or {}) if active_release else None,
        active_contract_versions=dict(active_release["contract_versions"] or {}) if active_release else None,
        large_table_threshold=threshold,
        attribute_projections=projections,
        profile_classes=graph_profile.get("classes") or [],
        profile_relationships=graph_profile.get("relationships") or [],
    )


def materialization_status(repository: ControlPlaneRepository, profile_key: str) -> dict[str, Any]:
    with repository.engine.connect() as connection:
        releases = [dict(row) for row in connection.execute(
            text(
                """
                SELECT release.release_id, release.release_no, release.status,
                       release.preview_only, release.source_rows_read,
                       release.object_count, release.relationship_count,
                       release.quarantine_count, release.content_hash,
                       release.summary, release.error, release.started_at,
                       release.finished_at,
                       (active.active_release_id=release.release_id) AS is_active
                FROM graphsync.curated_release release
                LEFT JOIN graphsync.curated_release_activation active
                  ON active.profile_key=release.profile_key
                WHERE release.profile_key=:profile_key
                ORDER BY release.release_no DESC LIMIT 20
                """
            ),
            {"profile_key": profile_key},
        ).mappings()]
        batch_rows = int(connection.execute(
            text("SELECT coalesce((value #>> '{}')::integer, 10000) FROM graphsync.app_setting WHERE setting_key='curation.materialization_batch_rows'")
        ).scalar_one_or_none() or 10_000)
    _, plan = _release_plan_from_repository(repository, profile_key, batch_rows)
    return {"plan": plan, "releases": releases}


def execute_materialization(
    base_settings: SyncSettings,
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    apply: bool = False,
    activate: bool = False,
    actor: str | None = None,
) -> dict[str, Any]:
    """Plan or execute a release.  ``apply=False`` never reads source rows."""

    status = materialization_status(repository, profile_key)
    plan = status["plan"]
    if not apply:
        return {"ok": True, "previewOnly": True, "plan": plan, "mutations": []}
    if not plan["ready"]:
        raise RuntimeError("Materialization is blocked: " + "; ".join(plan["blockers"]))

    governance = repository.governance_profile(profile_key)
    contracts = governance["contracts"]
    relationships = governance["relationships"]
    fields_by_contract = {
        item["contract_key"]: repository.contract_schema(item["contract_key"])["fields"]
        for item in contracts
    }
    projections_by_contract: dict[str, list[dict[str, Any]]] = {}
    for projection in repository.list_attribute_projections(profile_key):
        if projection.get("enabled") and projection.get("status") == "approved":
            projections_by_contract.setdefault(projection["target_contract_key"], []).append(projection)
    settings = resolved_settings(base_settings, repository)
    release_id = uuid.uuid4()
    lock_name = f"graphsync:materialize:{profile_key}"
    with repository.engine.connect() as lock_connection:
        acquired = lock_connection.execute(
            text("SELECT pg_try_advisory_lock(hashtextextended(:name, 0))"), {"name": lock_name}
        ).scalar_one()
        if not acquired:
            raise RuntimeError(f"A materialization is already running for {profile_key}")
        try:
            with repository.engine.begin() as connection:
                release_no = connection.execute(
                    text("SELECT coalesce(max(release_no),0)+1 FROM graphsync.curated_release WHERE profile_key=:profile_key"),
                    {"profile_key": profile_key},
                ).scalar_one()
                versions = {item["contract_key"]: item["version"] for item in contracts}
                versions["__attributeProjections"] = {
                    item["projectionKey"]: item["version"]
                    for item in plan.get("attributeProjections") or []
                }
                source_snapshot = {
                    item["className"]: item["incrementalWindow"]
                    for item in plan["contracts"] if item.get("incrementalWindow")
                }
                connection.execute(
                    text(
                        """
                        INSERT INTO graphsync.curated_release
                            (release_id, profile_key, release_no, status, preview_only,
                             quality_run_id, contract_versions, schema_change_ids,
                             source_snapshot, requested_by)
                        VALUES (:release_id, :profile_key, :release_no, 'extracting', false,
                                :quality_run_id, CAST(:versions AS jsonb),
                                CAST(:schema_change_ids AS jsonb),
                                CAST(:source_snapshot AS jsonb), :actor)
                        """
                    ),
                    {
                        "release_id": release_id,
                        "profile_key": profile_key,
                        "release_no": release_no,
                        "quality_run_id": governance["latestRun"]["curation_run_id"],
                        "versions": canonical_json(versions),
                        "schema_change_ids": canonical_json(plan.get("schemaChangeIds") or []),
                        "source_snapshot": canonical_json(source_snapshot),
                        "actor": actor,
                    },
                )

            source = None
            totals = {"read": 0, "objects": 0, "quarantine": 0, "batches": 0}
            try:
                for contract in contracts:
                    fields = fields_by_contract[contract["contract_key"]]
                    contract_plan = next(item for item in plan["contracts"] if item["contractKey"] == contract["contract_key"])
                    if contract_plan["extractionMode"] == "field_backfill":
                        previous_release = uuid.UUID(plan["activeReleaseId"])
                        backfill = contract_plan.get("fieldBackfill") or {}
                        affected_keys = set(backfill.get("affectedFieldKeys") or [])
                        affected_fields = [
                            field for field in fields
                            if field.get("field_key") in affected_keys
                            and field.get("lifecycle_status") != "retired"
                        ]
                        remove_targets = sorted({
                            *(backfill.get("removeTargetFields") or []),
                            *(field["target_field"] for field in affected_fields),
                        })
                        with repository.engine.begin() as connection:
                            connection.execute(
                                text(
                                    """
                                    INSERT INTO graphsync.object_version
                                        (release_id, profile_key, contract_key, contract_version,
                                         class_name, object_uri, source_primary_key, business_key,
                                         source_values, properties, source_hash, source_change_at,
                                         record_status, quality_issues, loaded_at)
                                    SELECT :release_id, profile_key, contract_key, :contract_version,
                                           class_name, object_uri, source_primary_key, business_key,
                                           source_values, properties, source_hash, source_change_at,
                                           record_status, quality_issues, now()
                                    FROM graphsync.object_version
                                    WHERE release_id=:previous_release
                                      AND contract_key=:contract_key
                                    """
                                ),
                                {
                                    "release_id": release_id,
                                    "previous_release": previous_release,
                                    "contract_key": contract["contract_key"],
                                    "contract_version": contract["version"],
                                },
                            )
                            if remove_targets:
                                connection.execute(
                                    text(
                                        """
                                        UPDATE graphsync.object_version
                                        SET properties=properties - CAST(:targets AS text[])
                                        WHERE release_id=:release_id
                                          AND contract_key=:contract_key
                                        """
                                    ),
                                    {
                                        "release_id": release_id,
                                        "contract_key": contract["contract_key"],
                                        "targets": remove_targets,
                                    },
                                )
                        if affected_fields:
                            if source is None:
                                source = connect_source(settings)
                            columns = sorted({
                                *contract["primary_key_columns"],
                                *(
                                    column
                                    for field in affected_fields
                                    for column in _field_source_columns(field)
                                ),
                            })
                            iterator = _iter_rows(
                                source,
                                kind=settings.source_kind,
                                schema=contract["source_schema"],
                                table=contract["source_table"],
                                columns=columns,
                                primary_keys=contract["primary_key_columns"],
                                fetch_size=plan["batchRows"],
                            )
                            for batch_no, page in enumerate(
                                _chunks(iterator, plan["batchRows"]), start=1,
                            ):
                                patches = [
                                    build_field_backfill_patch(
                                        contract, affected_fields, row,
                                    )
                                    for row in page
                                ]
                                with repository.engine.begin() as connection:
                                    connection.execute(
                                        text(
                                            """
                                            UPDATE graphsync.object_version
                                            SET properties=properties || CAST(:properties AS jsonb),
                                                source_values=source_values || CAST(:source_values AS jsonb),
                                                source_hash=md5(source_hash || :patch_hash),
                                                quality_issues=CASE
                                                    WHEN CAST(:has_issues AS boolean)
                                                    THEN quality_issues || CAST(:quality_issues AS jsonb)
                                                    ELSE quality_issues
                                                END,
                                                record_status=CASE
                                                    WHEN CAST(:has_issues AS boolean)
                                                    THEN 'quarantined' ELSE record_status
                                                END,
                                                loaded_at=now()
                                            WHERE release_id=:release_id
                                              AND contract_key=:contract_key
                                              AND object_uri=:object_uri
                                            """
                                        ),
                                        [
                                            {
                                                "release_id": release_id,
                                                "contract_key": contract["contract_key"],
                                                "object_uri": patch["objectUri"],
                                                "properties": canonical_json(patch["properties"]),
                                                "source_values": canonical_json(patch["sourceValues"]),
                                                "patch_hash": patch["patchHash"],
                                                "quality_issues": canonical_json(patch["qualityIssues"]),
                                                "has_issues": bool(patch["qualityIssues"]),
                                            }
                                            for patch in patches
                                        ],
                                    )
                                    connection.execute(
                                        text(
                                            """
                                            INSERT INTO graphsync.materialization_batch
                                                (batch_id, release_id, contract_key, batch_no,
                                                 status, rows_read, rows_written,
                                                 rows_quarantined, content_hash, finished_at)
                                            VALUES (:batch, :release, :contract, :batch_no,
                                                    'verified', :rows, :written,
                                                    :quarantine, :hash, now())
                                            """
                                        ),
                                        {
                                            "batch": uuid.uuid4(),
                                            "release": release_id,
                                            "contract": contract["contract_key"],
                                            "batch_no": batch_no,
                                            "rows": len(page),
                                            "written": len(patches),
                                            "quarantine": sum(bool(item["qualityIssues"]) for item in patches),
                                            "hash": content_hash([item["patchHash"] for item in patches]),
                                        },
                                    )
                                totals["read"] += len(page)
                                totals["batches"] += 1
                        elif remove_targets:
                            with repository.engine.begin() as connection:
                                affected_rows = connection.execute(
                                    text(
                                        """
                                        SELECT count(*) FROM graphsync.object_version
                                        WHERE release_id=:release AND contract_key=:contract
                                        """
                                    ),
                                    {"release": release_id, "contract": contract["contract_key"]},
                                ).scalar_one()
                                connection.execute(
                                    text(
                                        """
                                        INSERT INTO graphsync.materialization_batch
                                            (batch_id, release_id, contract_key, batch_no,
                                             status, rows_read, rows_written,
                                             rows_quarantined, content_hash, finished_at)
                                        VALUES (:batch, :release, :contract, 1, 'verified',
                                                0, :written, 0, :hash, now())
                                        """
                                    ),
                                    {
                                        "batch": uuid.uuid4(), "release": release_id,
                                        "contract": contract["contract_key"],
                                        "written": affected_rows,
                                        "hash": content_hash(remove_targets),
                                    },
                                )
                            totals["batches"] += 1
                        continue
                    if contract_plan["extractionMode"] == "verified_incremental_package":
                        previous_release = uuid.UUID(plan["activeReleaseId"])
                        change_path = Path(contract_plan["incrementalWindow"]["changeFile"])
                        if not change_path.is_file():
                            raise RuntimeError(f"Verified incremental change file is missing: {change_path}")
                        with repository.engine.begin() as connection:
                            connection.execute(
                                text(
                                    """
                                    INSERT INTO graphsync.object_version
                                        (release_id, profile_key, contract_key, contract_version,
                                         class_name, object_uri, source_primary_key, business_key,
                                         source_values, properties, source_hash, source_change_at,
                                         record_status, quality_issues, loaded_at)
                                    SELECT :release_id, profile_key, contract_key, :contract_version,
                                           class_name, object_uri, source_primary_key, business_key,
                                           source_values, properties, source_hash, source_change_at,
                                           record_status, quality_issues, now()
                                    FROM graphsync.object_version
                                    WHERE release_id=:previous_release
                                      AND contract_key=:contract_key
                                    """
                                ),
                                {"release_id": release_id, "previous_release": previous_release, "contract_key": contract["contract_key"], "contract_version": contract["version"]},
                            )
                        with change_path.open("r", encoding="utf-8") as stream:
                            events = (json.loads(line) for line in stream if line.strip())
                            for batch_no, page in enumerate(_chunks(events, plan["batchRows"]), start=1):
                                batch_id = uuid.uuid4()
                                upserts: list[dict[str, Any]] = []
                                upsert_rows: list[dict[str, Any]] = []
                                deleted: list[tuple[str, dict[str, Any]]] = []
                                for event in page:
                                    key = {column: (event.get("key") or {}).get(column) for column in contract["primary_key_columns"]}
                                    uri = object_uri(contract["class_name"], key)
                                    if event.get("operation") == "delete":
                                        deleted.append((uri, key))
                                    else:
                                        if not isinstance(event.get("row"), dict):
                                            raise RuntimeError(f"Incremental {event.get('operation')} has no source row for {contract['class_name']}")
                                        upsert_rows.append(event["row"])
                                        upserts.append(normalize_object_record(contract, fields, event["row"]))
                                contract_projections = projections_by_contract.get(contract["contract_key"], [])
                                if upserts and contract_projections:
                                    if source is None:
                                        source = connect_source(settings)
                                    upserts = apply_attribute_projections(
                                        source, kind=settings.source_kind,
                                        projections=contract_projections,
                                        owner_rows=upsert_rows, records=upserts,
                                    )
                                with repository.engine.begin() as connection:
                                    uris = [item["objectUri"] for item in upserts] + [item[0] for item in deleted]
                                    if uris:
                                        connection.execute(text("DELETE FROM graphsync.object_version WHERE release_id=:release_id AND contract_key=:contract_key AND object_uri=ANY(:uris)"), {"release_id": release_id, "contract_key": contract["contract_key"], "uris": uris})
                                    _insert_object_records(connection, [item for item in upserts if item["objectUri"]], release_id=release_id, profile_key=profile_key, contract=contract)
                                    if deleted:
                                        tombstones = []
                                        for uri, key in deleted:
                                            payload = {"sourcePrimaryKey": key, "operation": "delete"}
                                            tombstones.append({"objectUri": uri, "sourcePrimaryKey": key, "businessKey": {}, "sourceValues": key, "properties": {}, "sourceHash": content_hash(payload), "sourceChangeAt": None, "recordStatus": "deleted", "qualityIssues": []})
                                        _insert_object_records(connection, tombstones, release_id=release_id, profile_key=profile_key, contract=contract)
                                    connection.execute(
                                        text("INSERT INTO graphsync.materialization_batch (batch_id, release_id, contract_key, batch_no, status, rows_read, rows_written, rows_quarantined, content_hash, finished_at) VALUES (:batch, :release, :contract, :batch_no, 'verified', :rows, :written, :quarantine, :hash, now())"),
                                        {"batch": batch_id, "release": release_id, "contract": contract["contract_key"], "batch_no": batch_no, "rows": len(page), "written": len(upserts) + len(deleted), "quarantine": sum(item["recordStatus"] == "quarantined" for item in upserts), "hash": content_hash(page)},
                                    )
                                totals["read"] += len(page)
                                totals["batches"] += 1
                        continue
                    if source is None:
                        source = connect_source(settings)
                    columns = sorted({
                        *(column for field in fields for column in _field_source_columns(field)),
                        *contract["primary_key_columns"],
                        *contract["business_key_columns"],
                        *(
                            mapping["targetColumn"]
                            for projection in projections_by_contract.get(contract["contract_key"], [])
                            for mapping in projection.get("owner_mapping") or []
                        ),
                    })
                    iterator = _iter_rows(
                        source,
                        kind=settings.source_kind,
                        schema=contract["source_schema"],
                        table=contract["source_table"],
                        columns=columns,
                        primary_keys=contract["primary_key_columns"],
                        fetch_size=plan["batchRows"],
                    )
                    for batch_no, page in enumerate(_chunks(iterator, plan["batchRows"]), start=1):
                        batch_id = uuid.uuid4()
                        records = [normalize_object_record(contract, fields, row) for row in page]
                        contract_projections = projections_by_contract.get(contract["contract_key"], [])
                        if records and contract_projections:
                            records = apply_attribute_projections(
                                source, kind=settings.source_kind,
                                projections=contract_projections,
                                owner_rows=page, records=records,
                            )
                        valid = [item for item in records if item["objectUri"]]
                        with repository.engine.begin() as connection:
                            connection.execute(
                                text(
                                    """
                                    INSERT INTO graphsync.materialization_batch
                                        (batch_id, release_id, contract_key, batch_no, status,
                                         lower_key, upper_key, rows_read, rows_written,
                                         rows_quarantined, content_hash, finished_at)
                                    VALUES (:batch_id, :release_id, :contract_key, :batch_no,
                                            'verified', CAST(:lower_key AS jsonb), CAST(:upper_key AS jsonb),
                                            :rows_read, :rows_written, :rows_quarantined,
                                            :content_hash, now())
                                    """
                                ),
                                {
                                    "batch_id": batch_id,
                                    "release_id": release_id,
                                    "contract_key": contract["contract_key"],
                                    "batch_no": batch_no,
                                    "lower_key": canonical_json(valid[0]["sourcePrimaryKey"] if valid else {}),
                                    "upper_key": canonical_json(valid[-1]["sourcePrimaryKey"] if valid else {}),
                                    "rows_read": len(page),
                                    "rows_written": len(valid),
                                    "rows_quarantined": sum(item["recordStatus"] == "quarantined" for item in valid),
                                    "content_hash": content_hash([item["sourceHash"] for item in valid]),
                                },
                            )
                            _insert_object_records(connection, valid, release_id=release_id, profile_key=profile_key, contract=contract)
                        totals["read"] += len(page)
                        totals["objects"] += len(valid)
                        totals["quarantine"] += sum(item["recordStatus"] == "quarantined" for item in valid)
                        totals["batches"] += 1
            finally:
                if source is not None:
                    source.close()

            unresolved_required = 0
            relationship_count = 0
            with repository.engine.begin() as connection:
                connection.execute(
                    text("UPDATE graphsync.curated_release SET status='verifying' WHERE release_id=:release_id"),
                    {"release_id": release_id},
                )
                for relationship in relationships:
                    source_columns = relationship["source_columns"]
                    target_columns = relationship["target_columns"]
                    join_parts = [
                        f"target.source_values ->> '{target.replace(chr(39), chr(39)*2)}' = source.source_values ->> '{source_col.replace(chr(39), chr(39)*2)}'"
                        for source_col, target in zip(source_columns, target_columns, strict=True)
                    ]
                    reference_parts = ", ".join(
                        f"'{column.replace(chr(39), chr(39)*2)}', source.source_values -> '{column.replace(chr(39), chr(39)*2)}'"
                        for column in source_columns
                    )
                    sql = f"""
                        INSERT INTO graphsync.relationship_version
                            (release_id, relationship_contract_key, relationship_name,
                             source_contract_key, target_contract_key, source_object_uri,
                             target_object_uri, source_reference, resolution_status, source_hash)
                        SELECT :release_id, :relationship_key, :relationship_name,
                               :source_contract, :target_contract, source.object_uri,
                               target.object_uri, jsonb_build_object({reference_parts}),
                               CASE WHEN target.object_uri IS NULL THEN 'pending' ELSE 'resolved' END,
                               md5(source.object_uri || ':' || coalesce(target.object_uri, ''))
                        FROM graphsync.object_version source
                        LEFT JOIN graphsync.object_version target
                          ON target.release_id=source.release_id
                         AND target.contract_key=:target_contract
                         AND target.record_status='active'
                         AND {' AND '.join(join_parts)}
                        WHERE source.release_id=:release_id
                          AND source.contract_key=:source_contract
                          AND source.record_status='active'
                          AND ({' OR '.join(f"source.source_values ->> \'{column.replace(chr(39), chr(39)*2)}\' IS NOT NULL" for column in source_columns)})
                    """
                    connection.execute(
                        text(sql),
                        {
                            "release_id": release_id,
                            "relationship_key": relationship["relationship_contract_key"],
                            "relationship_name": relationship["relationship_name"],
                            "source_contract": relationship["source_contract_key"],
                            "target_contract": relationship["target_contract_key"],
                        },
                    )
                    counts = connection.execute(
                        text(
                            """
                            SELECT count(*) AS total,
                                   count(*) FILTER (WHERE resolution_status='pending') AS pending
                            FROM graphsync.relationship_version
                            WHERE release_id=:release_id
                              AND relationship_contract_key=:relationship_key
                            """
                        ),
                        {"release_id": release_id, "relationship_key": relationship["relationship_contract_key"]},
                    ).mappings().one()
                    relationship_count += int(counts["total"])
                    if relationship.get("required_context"):
                        unresolved_required += int(counts["pending"])

                object_totals = connection.execute(
                    text("SELECT count(*) FILTER (WHERE record_status <> 'deleted') AS objects, count(*) FILTER (WHERE record_status='quarantined') AS quarantine FROM graphsync.object_version WHERE release_id=:release_id"),
                    {"release_id": release_id},
                ).mappings().one()
                totals["objects"] = int(object_totals["objects"] or 0)
                totals["quarantine"] = int(object_totals["quarantine"] or 0)
                ready = totals["quarantine"] == 0 and unresolved_required == 0
                release_hash = content_hash({"objects": totals["objects"], "relationships": relationship_count})
                summary = {**totals, "relationships": relationship_count, "unresolvedRequired": unresolved_required}
                connection.execute(
                    text(
                        """
                        UPDATE graphsync.curated_release
                        SET status=:status, source_rows_read=:source_rows,
                            object_count=:objects, relationship_count=:relationships,
                            quarantine_count=:quarantine, content_hash=:content_hash,
                            summary=CAST(:summary AS jsonb), finished_at=now()
                        WHERE release_id=:release_id
                        """
                    ),
                    {
                        "release_id": release_id,
                        "status": "ready" if ready else "failed",
                        "source_rows": totals["read"],
                        "objects": totals["objects"],
                        "relationships": relationship_count,
                        "quarantine": totals["quarantine"],
                        "content_hash": release_hash,
                        "summary": canonical_json(summary),
                    },
                )
                if plan.get("schemaChangeIds"):
                    connection.execute(
                        text(
                            """
                            UPDATE graphsync.schema_migration_run migration
                            SET verification=coalesce(migration.verification, '{}'::jsonb)
                                || jsonb_build_object(
                                    'immutableBackfillPending', false,
                                    'backfillReleaseId', CAST(:release_id AS text),
                                    'backfillReleaseNo', CAST(:release_no AS bigint),
                                    'verifiedAt', to_jsonb(now())
                                )
                            FROM graphsync.schema_change_request change
                            WHERE migration.change_id=change.change_id
                              AND change.change_id=ANY(CAST(:change_ids AS uuid[]))
                              AND migration.status='succeeded'
                            """
                        ),
                        {
                            "release_id": release_id,
                            "release_no": release_no,
                            "change_ids": plan["schemaChangeIds"],
                        },
                    )
                for contract in contracts:
                    field_map = {
                        field["source_column"]: field["target_field"]
                        for field in fields_by_contract[contract["contract_key"]]
                        if field.get("source_column") and field.get("lifecycle_status") != "retired"
                    }
                    contract_rows = connection.execute(
                        text("SELECT count(*) FROM graphsync.object_version WHERE release_id=:release_id AND contract_key=:contract_key"),
                        {"release_id": release_id, "contract_key": contract["contract_key"]},
                    ).scalar_one()
                    connection.execute(
                        text(
                            """
                            INSERT INTO graphsync.runtime_lineage_event
                                (lineage_event_id, profile_key, run_type, run_id,
                                 source_asset, target_asset, field_mappings,
                                 row_count, content_hash)
                            VALUES (:id, :profile_key, 'materialization', :run_id,
                                    :source, :target, CAST(:fields AS jsonb),
                                    :rows, :hash)
                            """
                        ),
                        {
                            "id": uuid.uuid4(), "profile_key": profile_key,
                            "run_id": release_id,
                            "source": f"{settings.source_kind}:{contract['source_schema']}.{contract['source_table']}",
                            "target": f"graphsync.object_version:{contract['contract_key']}:{release_id}",
                            "fields": canonical_json(field_map), "rows": contract_rows,
                            "hash": release_hash,
                        },
                    )
                if not ready:
                    raise RuntimeError(f"Curated release verification failed: {summary}")
            if activate:
                activate_release(repository, profile_key=profile_key, release_id=release_id, actor=actor)
            return {
                "ok": True,
                "previewOnly": False,
                "releaseId": str(release_id),
                "releaseNo": release_no,
                "status": "active" if activate else "ready",
                **totals,
                "relationships": relationship_count,
            }
        except Exception as exc:
            with repository.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        UPDATE graphsync.curated_release
                        SET status='failed', finished_at=now(),
                            error=CAST(:error AS jsonb)
                        WHERE release_id=:release_id
                        """
                    ),
                    {"release_id": release_id, "error": canonical_json({"message": str(exc)})},
                )
            raise
        finally:
            lock_connection.execute(
                text("SELECT pg_advisory_unlock(hashtextextended(:name, 0))"), {"name": lock_name}
            )


def activate_release(
    repository: ControlPlaneRepository,
    *,
    profile_key: str,
    release_id: uuid.UUID,
    actor: str | None,
) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        release = connection.execute(
            text("SELECT status FROM graphsync.curated_release WHERE release_id=:release_id AND profile_key=:profile_key FOR UPDATE"),
            {"release_id": release_id, "profile_key": profile_key},
        ).mappings().one_or_none()
        if release is None:
            raise KeyError(str(release_id))
        if release["status"] not in {"ready", "active"}:
            raise ValueError("Only a verified ready release can be activated")
        previous = connection.execute(
            text("SELECT active_release_id FROM graphsync.curated_release_activation WHERE profile_key=:profile_key"),
            {"profile_key": profile_key},
        ).scalar_one_or_none()
        connection.execute(
            text(
                """
                INSERT INTO graphsync.curated_release_activation
                    (profile_key, active_release_id, previous_release_id, activated_by)
                VALUES (:profile_key, :release_id, :previous, :actor)
                ON CONFLICT (profile_key) DO UPDATE SET
                    previous_release_id=graphsync.curated_release_activation.active_release_id,
                    active_release_id=EXCLUDED.active_release_id,
                    activated_at=now(), activated_by=EXCLUDED.activated_by
                """
            ),
            {"profile_key": profile_key, "release_id": release_id, "previous": previous, "actor": actor},
        )
        if previous and previous != release_id:
            connection.execute(text("UPDATE graphsync.curated_release SET status='superseded' WHERE release_id=:id"), {"id": previous})
        connection.execute(text("UPDATE graphsync.curated_release SET status='active' WHERE release_id=:id"), {"id": release_id})
    return {"profileKey": profile_key, "activeReleaseId": str(release_id), "previousReleaseId": str(previous) if previous else None}


def rollback_release(repository: ControlPlaneRepository, *, profile_key: str, actor: str | None) -> dict[str, Any]:
    with repository.engine.begin() as connection:
        active = connection.execute(
            text(
                """
                SELECT active_release_id, previous_release_id
                FROM graphsync.curated_release_activation
                WHERE profile_key=:profile_key FOR UPDATE
                """
            ),
            {"profile_key": profile_key},
        ).mappings().one_or_none()
        if active is None or active["previous_release_id"] is None:
            raise ValueError("No previous curated release is available for rollback")
        connection.execute(
            text(
                """
                UPDATE graphsync.curated_release_activation
                SET active_release_id=previous_release_id,
                    previous_release_id=active_release_id,
                    activated_at=now(), activated_by=:actor
                WHERE profile_key=:profile_key
                """
            ),
            {"profile_key": profile_key, "actor": actor},
        )
        connection.execute(text("UPDATE graphsync.curated_release SET status='rolled_back' WHERE release_id=:id"), {"id": active["active_release_id"]})
        connection.execute(text("UPDATE graphsync.curated_release SET status='active' WHERE release_id=:id"), {"id": active["previous_release_id"]})
    return {
        "profileKey": profile_key,
        "activeReleaseId": str(active["previous_release_id"]),
        "rolledBackReleaseId": str(active["active_release_id"]),
    }
