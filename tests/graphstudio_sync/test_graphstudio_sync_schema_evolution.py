import pytest

from src.graphstudio_sync.schema_evolution import (
    analyze_schema_change,
    classify_schema_change,
)


def _contract(version=2):
    return {"contract_key": "product-v1", "version": version}


def _field(key="product-v1:description", **overrides):
    return {
        "field_key": key,
        "source_column": "Description",
        "target_field": "description",
        "data_type": "String",
        "nullable": True,
        "required": False,
        "lifecycle_status": "active",
        **overrides,
    }


def test_optional_field_addition_is_non_breaking() -> None:
    result = classify_schema_change(
        "add_field",
        None,
        {"target_field": "brandName", "data_type": "String", "nullable": True},
    )

    assert result["compatibility"] == "non_breaking"
    assert result["migrationRequired"] is False


def test_required_field_without_default_is_breaking_and_needs_backfill() -> None:
    result = classify_schema_change(
        "add_field",
        None,
        {"target_field": "plantCode", "required": True, "nullable": False},
    )

    assert result["compatibility"] == "breaking"
    assert result["migrationRequired"] is True
    assert result["backfillRequired"] is True


def test_deprecation_with_dependencies_requires_compatibility_window() -> None:
    result = classify_schema_change(
        "deprecate_field", _field(), None, dependency_count=3
    )

    assert result["compatibility"] == "conditional"
    assert result["dependencyCount"] == 3


def test_breaking_request_requires_migration_and_rollback_strategies() -> None:
    analysis = analyze_schema_change(
        _contract(),
        [_field()],
        [
            {
                "operation": "change_type",
                "field_key": "product-v1:description",
                "after_state": {"data_type": "Integer"},
            }
        ],
        [],
    )

    assert analysis["compatibility"] == "breaking"
    assert analysis["targetVersion"] == 3
    assert analysis["readyForReview"] is False
    assert len(analysis["blockers"]) == 2


def test_breaking_request_is_reviewable_with_migration_controls() -> None:
    analysis = analyze_schema_change(
        _contract(),
        [_field()],
        [
            {
                "operation": "change_type",
                "field_key": "product-v1:description",
                "after_state": {"data_type": "Integer"},
            }
        ],
        [],
        migration_strategy="Create a shadow column and backfill in bounded batches.",
        rollback_strategy="Keep the old column and switch readers back.",
    )

    assert analysis["readyForReview"] is True
    assert analysis["backfillRequired"] is True


def test_retirement_with_active_dependency_is_blocked() -> None:
    field = _field()
    analysis = analyze_schema_change(
        _contract(),
        [field],
        [{"operation": "retire_field", "field_key": field["field_key"]}],
        [{"upstream_key": field["field_key"], "active": True}],
        migration_strategy="Stop new writes after consumer migration.",
        rollback_strategy="Restore the previous contract version.",
    )

    assert analysis["dependencyCount"] == 1
    assert any("活动依赖" in blocker for blocker in analysis["blockers"])


def test_duplicate_field_changes_are_rejected() -> None:
    field = _field()
    with pytest.raises(ValueError, match="same field twice"):
        analyze_schema_change(
            _contract(),
            [field],
            [
                {"operation": "deprecate_field", "field_key": field["field_key"]},
                {"operation": "retire_field", "field_key": field["field_key"]},
            ],
            [],
        )
