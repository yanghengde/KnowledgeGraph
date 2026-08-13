import pytest

from src.graphstudio_sync.actions import _resolved_path, _validate_payload
from src.graphstudio_sync.materialization import (
    apply_transform,
    build_materialization_plan,
    canonical_json,
    normalize_object_record,
    object_uri,
)
from src.graphstudio_sync.observability import _rule_failed
from src.graphstudio_sync.schema_evolution import _merged_field


def _contract(**overrides):
    return {
        "contract_key": "product-v1",
        "class_name": "Product",
        "version": 3,
        "status": "approved",
        "class_review_status": "approved",
        "mapping_status": "resolved",
        "source_schema": "Camstar",
        "source_table": "Product",
        "primary_key_columns": ["ProductId"],
        "business_key_columns": ["Name"],
        "freshness_column": None,
        **overrides,
    }


def _governance(**overrides):
    contracts = [_contract()]
    return {
        "contracts": contracts,
        "relationships": [],
        "latestRun": {
            "publishable": True,
            "contract_versions": {"objects": {"product-v1": 3}},
        },
        **overrides,
    }


def test_materialization_plan_ready_after_all_gates() -> None:
    plan = build_materialization_plan(
        _governance(), [], profile_key="core", batch_rows=5000
    )

    assert plan["ready"] is True
    assert plan["batchRows"] == 5000
    assert plan["activation"] == "verified_pointer_switch"


def test_materialization_plan_blocks_unapproved_contract_and_stale_quality() -> None:
    contract = _contract(status="draft")
    governance = _governance(
        contracts=[contract],
        latestRun={"publishable": True, "contract_versions": {"objects": {"product-v1": 2}}},
    )

    plan = build_materialization_plan(governance, [], profile_key="core")

    assert plan["ready"] is False
    assert any("数据契约未批准" in item for item in plan["blockers"])
    assert any("版本已经过期" in item for item in plan["blockers"])


def test_materialization_plan_blocks_approved_unapplied_schema_change() -> None:
    plan = build_materialization_plan(
        _governance(), [{"status": "approved"}], profile_key="core"
    )

    assert plan["ready"] is False
    assert any("Schema 变更" in item for item in plan["blockers"])


def test_materialization_plan_blocks_profile_scope_without_contracts() -> None:
    plan = build_materialization_plan(
        _governance(),
        [],
        profile_key="core",
        profile_classes=[
            {"class_name": "Product", "enabled": True},
            {"class_name": "Container", "enabled": True},
        ],
        profile_relationships=[{
            "source_class": "Container",
            "relationship_name": "HAS_PRODUCT",
            "target_class": "Product",
            "enabled": True,
        }],
    )

    assert plan["ready"] is False
    assert "发布对象缺少数据契约：Container" in plan["blockers"]
    assert "发布关系缺少关系契约：Container.HAS_PRODUCT->Product" in plan["blockers"]


def test_materialization_plan_never_falls_back_to_large_table_scan() -> None:
    governance = _governance(contracts=[_contract(approximate_rows=100_000_000)])

    plan = build_materialization_plan(
        governance,
        [],
        profile_key="core",
        table_policies=[{
            "class_name": "Product",
            "strategy": "cdc",
            "effective_strategy": "cdc",
            "requires_review": False,
        }],
        incremental_windows=[],
        active_release_id="release-1",
    )

    assert plan["ready"] is False
    assert any("没有已验证的增量变更包" in item for item in plan["blockers"])
    assert plan["contracts"][0]["strategy"] == "cdc"


def test_materialization_plan_uses_verified_incremental_package_for_large_table() -> None:
    governance = _governance(contracts=[_contract(approximate_rows=100_000_000)])
    plan = build_materialization_plan(
        governance, [], profile_key="core",
        table_policies=[{"class_name": "Product", "effective_strategy": "cdc", "requires_review": False}],
        incremental_windows=[{"class_name": "Product", "window_id": "w1", "run_id": "r1", "status": "verified", "upper_bound": {"lsn": "2"}, "metadata": {"changeFile": "Product.jsonl"}}],
        active_release_id="release-1",
    )

    assert plan["ready"] is True
    assert plan["contracts"][0]["extractionMode"] == "verified_incremental_package"


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("source:Name", "  Product A  "),
        ("trim:Name", "Product A"),
        ("upper:Code", "P-1"),
        ("lower:Code", "p-1"),
        ("coalesce:Missing,Code", "P-1"),
        ("constant:42", 42),
    ],
)
def test_governed_transform_language(expression, expected) -> None:
    assert apply_transform(expression, {"Name": "  Product A  ", "Code": "P-1"}, None) == expected


def test_governed_transform_rejects_arbitrary_code() -> None:
    with pytest.raises(ValueError, match="Unsupported governed transform"):
        apply_transform("eval:__import__('os')", {}, None)


def test_normalize_object_record_has_stable_uri_and_hash() -> None:
    contract = _contract()
    fields = [
        {"field_key": "id", "source_column": "ProductId", "target_field": "id", "lifecycle_status": "active", "required": True},
        {"field_key": "name", "source_column": "Name", "target_field": "name", "lifecycle_status": "active", "required": True, "transform_expression": "trim:Name"},
    ]

    first = normalize_object_record(contract, fields, {"ProductId": "P 1", "Name": " A "})
    second = normalize_object_record(contract, fields, {"ProductId": "P 1", "Name": " A "})

    assert first["objectUri"].endswith("ProductId%3DP%201")
    assert first["properties"]["name"] == "A"
    assert first["sourceHash"] == second["sourceHash"]
    assert first["recordStatus"] == "active"


def test_normalize_object_record_quarantines_missing_required_value() -> None:
    fields = [{"field_key": "name", "source_column": "Name", "target_field": "name", "lifecycle_status": "active", "required": True}]

    record = normalize_object_record(_contract(), fields, {"ProductId": "P1", "Name": None})

    assert record["recordStatus"] == "quarantined"
    assert "required.name" in record["qualityIssues"]


def test_object_uri_rejects_incomplete_key() -> None:
    with pytest.raises(ValueError, match="incomplete primary key"):
        object_uri("Product", {"ProductId": None})


def test_canonical_json_is_order_independent() -> None:
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_schema_migration_marks_deprecated_version() -> None:
    before = {"target_field": "name", "data_type": "String", "lifecycle_status": "active"}

    result = _merged_field(before, None, "deprecate_field", 4)

    assert result["lifecycle_status"] == "deprecated"
    assert result["deprecated_version"] == 4


def test_schema_migration_add_uses_target_version() -> None:
    result = _merged_field(None, {"target_field": "brand", "source_column": "Brand"}, "add_field", 5)

    assert result["introduced_version"] == 5
    assert result["nullable"] is True


def test_action_payload_schema_validation() -> None:
    schema = {"type": "object", "required": ["id", "changes"], "properties": {"id": {"type": "string"}, "changes": {"type": "object"}}}

    assert _validate_payload(schema, {"id": "1", "changes": {}}) == []
    assert len(_validate_payload(schema, {"id": 1})) == 2


def test_action_path_is_encoded_and_complete() -> None:
    assert _resolved_path("/orders/{id}", {"id": "A/B"}, ["id"]) == "/orders/A%2FB"
    with pytest.raises(ValueError, match="Missing path parameter"):
        _resolved_path("/orders/{id}", {}, ["id"])


@pytest.mark.parametrize(
    ("operator", "value", "threshold", "failed"),
    [
        ("gt", 11, 10, True),
        ("lte", 11, 10, False),
        ("eq", 10, 10, True),
        ("missing", None, None, True),
        ("missing", 0, None, False),
    ],
)
def test_alert_rule_evaluation(operator, value, threshold, failed) -> None:
    assert _rule_failed(operator, value, threshold) is failed
