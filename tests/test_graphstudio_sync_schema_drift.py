from src.graphstudio_sync.schema_drift import compare_contract_schema


def _contract():
    return {
        "contract_key": "product-v1",
        "class_name": "Product",
        "version": 3,
        "source_schema": "dbo",
        "source_table": "Product",
    }


def test_schema_drift_detects_missing_and_new_columns_without_auto_publishing() -> None:
    result = compare_contract_schema(
        _contract(),
        [{
            "field_key": "product-v1:name",
            "source_column": "ProductName",
            "target_field": "name",
            "data_type": "String",
            "required": True,
            "lifecycle_status": "active",
        }],
        [{
            "column_name": "BrandName", "data_type": "nvarchar",
            "nullable": True, "ordinal_position": 2,
        }],
    )

    assert result["status"] == "drifted"
    assert result["blockers"] == 1
    candidate = next(item for item in result["changes"] if item["kind"] == "candidate_column")
    assert candidate["suggestedOperation"] == "add_field"
    assert candidate["suggestedAfterState"]["target_field"] == "brandName"


def test_schema_drift_classifies_physical_type_change_as_blocking() -> None:
    result = compare_contract_schema(
        _contract(),
        [{
            "field_key": "product-v1:quantity",
            "source_column": "Quantity",
            "target_field": "quantity",
            "data_type": "Integer",
            "required": False,
            "lifecycle_status": "active",
        }],
        [{
            "column_name": "Quantity", "data_type": "nvarchar",
            "nullable": True, "ordinal_position": 1,
        }],
        [{
            "column_name": "Quantity", "data_type": "int",
            "nullable": True, "ordinal_position": 1,
        }],
    )

    change = next(item for item in result["changes"] if item["kind"] == "type_changed")
    assert change["suggestedOperation"] == "change_type"
    assert change["afterType"] == "String"


def test_initial_contract_type_mismatch_is_warning_not_source_drift() -> None:
    result = compare_contract_schema(
        _contract(),
        [{
            "field_key": "product-v1:quantity",
            "source_column": "Quantity", "target_field": "quantity",
            "data_type": "Integer", "required": False,
            "lifecycle_status": "active",
        }],
        [{
            "column_name": "Quantity", "data_type": "nvarchar",
            "nullable": True, "ordinal_position": 1,
        }],
    )

    assert result["blockers"] == 0
    assert any(item["kind"] == "contract_type_mismatch" for item in result["changes"])


def test_schema_drift_reports_stable_when_contract_matches() -> None:
    result = compare_contract_schema(
        _contract(),
        [{
            "field_key": "product-v1:name",
            "source_column": "ProductName",
            "target_field": "name",
            "data_type": "String",
            "required": False,
            "lifecycle_status": "active",
        }],
        [{
            "column_name": "ProductName", "data_type": "nvarchar",
            "nullable": True, "ordinal_position": 1,
        }],
    )

    assert result["status"] == "stable"
    assert result["blockers"] == 0


def test_navigation_field_accepts_scalar_foreign_key_storage() -> None:
    result = compare_contract_schema(
        _contract(),
        [{
            "field_key": "product-v1:workflow",
            "source_column": "WorkflowId",
            "target_field": "workflow",
            "data_type": "Navigation",
            "required": False,
            "lifecycle_status": "active",
        }],
        [{
            "column_name": "WorkflowId", "data_type": "char",
            "nullable": True, "ordinal_position": 1,
        }],
    )

    assert result["blockers"] == 0
    assert not any(item["kind"] == "type_changed" for item in result["changes"])


def test_system_columns_are_not_offered_as_ontology_candidates() -> None:
    result = compare_contract_schema(
        _contract(),
        [],
        [
            {"column_name": "CDOTypeId", "data_type": "int", "nullable": False},
            {"column_name": "ChangeCount", "data_type": "int", "nullable": False},
            {"column_name": "ExportImportKey", "data_type": "varchar", "nullable": True},
            {"column_name": "BusinessValue", "data_type": "varchar", "nullable": True},
        ],
    )

    candidates = [
        item["column"] for item in result["changes"]
        if item["kind"] == "candidate_column"
    ]
    assert candidates == ["BusinessValue"]
