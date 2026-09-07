from src.graphstudio_sync.curation import (
    evaluate_entity_contract,
    evaluate_relationship_contract,
)


def _contract(**overrides):
    return {
        "contract_key": "product-v1",
        "status": "approved",
        "class_review_status": "approved",
        "mapping_status": "resolved",
        "source_schema": "CamstarPRD_SCHEMA",
        "source_table": "Product",
        "mapped_schema": "CamstarPRD_SCHEMA",
        "mapped_table": "Product",
        "primary_key_columns": ["ProductId"],
        "business_key_columns": ["ProductBaseId", "ProductRevision"],
        "required_columns": ["ProductId"],
        "freshness_column": None,
        **overrides,
    }


def test_entity_contract_passes_clean_rows() -> None:
    rows = [
        {"ProductId": "1", "ProductBaseId": "B1", "ProductRevision": "A"},
        {"ProductId": "2", "ProductBaseId": "B2", "ProductRevision": "A"},
    ]

    results, quarantined = evaluate_entity_contract(_contract(), rows)

    assert not quarantined
    assert all(item["passed"] for item in results)


def test_required_and_duplicate_primary_keys_are_quarantined() -> None:
    rows = [
        {"ProductId": "1", "ProductBaseId": "B1", "ProductRevision": "A"},
        {"ProductId": "1", "ProductBaseId": "B2", "ProductRevision": "A"},
        {"ProductId": None, "ProductBaseId": "B3", "ProductRevision": "A"},
    ]

    results, quarantined = evaluate_entity_contract(_contract(), rows)

    assert ("1",) in quarantined
    assert (None,) in quarantined
    assert next(item for item in results if item["ruleKey"] == "primary_key.unique")["failedRows"] == 2
    assert next(item for item in results if item["ruleKey"] == "required.ProductId")["failedRows"] == 1


def test_draft_contract_blocks_publication_even_when_rows_are_clean() -> None:
    results, _ = evaluate_entity_contract(
        _contract(status="draft"),
        [{"ProductId": "1", "ProductBaseId": "B1", "ProductRevision": "A"}],
    )

    approval = next(item for item in results if item["ruleKey"] == "contract.approved")
    assert approval["passed"] is False
    assert approval["severity"] == "error"


def test_required_relationship_detects_unresolved_target() -> None:
    relationship = {
        "relationship_contract_key": "mfgorder-product-v1",
        "status": "approved",
        "source_columns": ["ProductId"],
        "target_columns": ["ProductId"],
        "required_context": True,
    }
    source_rows = [{"ProductId": "P1"}, {"ProductId": "P2"}]
    target_rows = [{"ProductId": "P1"}]

    results = evaluate_relationship_contract(relationship, source_rows, target_rows)

    target_result = next(
        item for item in results if item["ruleKey"] == "relationship.target_resolved"
    )
    assert target_result["passed"] is False
    assert target_result["severity"] == "error"
    assert target_result["failedRows"] == 1


def test_optional_relationship_missing_source_is_warning_only() -> None:
    relationship = {
        "relationship_contract_key": "mfgorder-begin-product-v1",
        "status": "approved",
        "source_columns": ["BeginProductId"],
        "target_columns": ["ProductId"],
        "required_context": False,
    }

    results = evaluate_relationship_contract(
        relationship,
        [{"BeginProductId": None}],
        [{"ProductId": "P1"}],
    )

    source_result = next(
        item for item in results if item["ruleKey"] == "relationship.source_present"
    )
    assert source_result["passed"] is True
    assert source_result["severity"] == "warning"


def test_relationship_can_resolve_revision_or_base_identifier() -> None:
    relationship = {
        "relationship_contract_key": "workflowstep-spec-v1",
        "status": "approved",
        "source_columns": ["SpecId"],
        "target_columns": ["SpecId"],
        "required_context": False,
        "config": {
            "matchAlternatives": [
                {"sourceColumns": ["SpecBaseId"], "targetColumns": ["SpecBaseId"]},
            ],
        },
    }

    results = evaluate_relationship_contract(
        relationship,
        [
            {"SpecId": "SPEC-1", "SpecBaseId": "0000000000000000"},
            {"SpecId": "0000000000000000", "SpecBaseId": "BASE-2"},
            {"SpecId": "STALE", "SpecBaseId": "0000000000000000"},
        ],
        [
            {"SpecId": "SPEC-1", "SpecBaseId": "BASE-1"},
            {"SpecId": "SPEC-2", "SpecBaseId": "BASE-2"},
        ],
    )

    target_result = next(
        item for item in results if item["ruleKey"] == "relationship.target_resolved"
    )
    assert target_result["failedRows"] == 1
