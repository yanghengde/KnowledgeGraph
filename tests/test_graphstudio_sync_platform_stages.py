import pytest

from src.graphstudio_sync.actions import _resolved_path, _validate_payload
from src.graphstudio_sync.deployment import (
    _catalog_entry,
    _ensure_dataset,
    _ensure_model,
    _requires_dataset_replacement,
    _set_layer_enabled,
    build_deployment_plan,
    release_model_uri,
)


def test_deployment_plan_selects_exact_route_and_only_checks_its_promotion_lane(monkeypatch) -> None:
    import uuid
    from types import SimpleNamespace
    from src.graphstudio_sync import deployment as deployment_module

    release_id = uuid.uuid4()
    previous_id = uuid.uuid4()
    routes = [
        {"route_key": "lane-a-dev", "environment_key": "dev", "target_key": "a", "title": "A DEV", "promotion_order": 10, "apply_enabled": True, "requires_approval": False, "config": {"promotionLane": "a"}},
        {"route_key": "lane-b-dev", "environment_key": "dev", "target_key": "b-dev", "title": "B DEV", "promotion_order": 10, "apply_enabled": True, "requires_approval": False, "config": {"promotionLane": "b"}},
        {"route_key": "lane-b-prod", "environment_key": "prod", "target_key": "b-prod", "title": "B PROD", "promotion_order": 30, "apply_enabled": True, "requires_approval": True, "config": {"promotionLane": "b"}},
    ]
    status = {
        "routes": routes,
        "activeCuratedRelease": {"release_id": release_id, "release_no": 3, "status": "active"},
        "activeOntologyRelease": {"ontology_release_id": uuid.uuid4(), "release_no": 2},
        "deployments": [{"deployment_id": previous_id, "route_key": "lane-b-dev", "status": "active", "curated_release_id": release_id, "slot": "blue"}],
    }
    monkeypatch.setattr(deployment_module, "deployment_status", lambda _repo, _profile: status)

    plan = build_deployment_plan(
        SimpleNamespace(), profile_key="core", environment_key="prod", route_key="lane-b-prod",
    )

    assert plan["ready"] is True
    assert plan["routeKey"] == "lane-b-prod"
    assert plan["targetKey"] == "b-prod"
    assert plan["blockers"] == []


def test_deployment_plan_toggles_slot_per_route_not_per_environment(monkeypatch) -> None:
    import uuid
    from types import SimpleNamespace
    from src.graphstudio_sync import deployment as deployment_module

    release_id = uuid.uuid4()
    route = {"route_key": "core-dev-two", "environment_key": "dev", "target_key": "two", "title": "Second Graphmart", "promotion_order": 10, "apply_enabled": True, "requires_approval": False, "config": {}}
    monkeypatch.setattr(deployment_module, "deployment_status", lambda _repo, _profile: {
        "routes": [route],
        "activeCuratedRelease": {"release_id": release_id, "release_no": 1, "status": "active"},
        "activeOntologyRelease": {"ontology_release_id": uuid.uuid4(), "release_no": 1},
        "deployments": [{"deployment_id": uuid.uuid4(), "route_key": route["route_key"], "status": "active", "curated_release_id": release_id, "slot": "blue"}],
    })

    plan = build_deployment_plan(
        SimpleNamespace(), profile_key="core", environment_key="dev", route_key=route["route_key"],
    )

    assert plan["slot"] == "green"


def test_apply_deployment_lookup_qualifies_deployment_id_column() -> None:
    """The previous-deployment self join must not make the lookup ambiguous."""
    from pathlib import Path

    source = Path("src/graphstudio_sync/deployment.py").read_text(encoding="utf-8")

    assert "WHERE deployment.deployment_id=:deployment_id" in source
from src.graphstudio_sync.materialization import (
    apply_transform,
    build_field_backfill_patch,
    build_materialization_plan,
    canonical_json,
    normalize_object_record,
    object_uri,
)
from src.graphstudio_sync.observability import _rule_failed
from src.graphstudio_sync.schema_evolution import _merged_field
from src.graphstudio_sync.repository import _physical_key_catalog


class _GraphStudioResponse:
    def __init__(self, payload, *, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.text = "" if payload is None else str(payload)

    def json(self):
        return self._payload


class _ModelSession:
    def __init__(self, model_uri):
        self.model_uri = model_uri
        self.get_count = 0
        self.uploaded_name = None

    def get(self, _url, **_kwargs):
        self.get_count += 1
        return _GraphStudioResponse([] if self.get_count == 1 else [self.model_uri])

    def post(self, _url, *, files, **_kwargs):
        self.uploaded_name = files["modelData"][0]
        return _GraphStudioResponse({"status": "uploaded"}, status_code=201)


def test_release_model_uri_is_immutable_per_ontology_release() -> None:
    release_id = "5e76088e-74df-4859-a9a3-1aa7649534d3"

    assert release_model_uri(release_id).endswith(f"/releases/{release_id}")


def test_catalog_entry_accepts_graph_studio_list_response() -> None:
    entry = "http://openanzo.org/catEntry(example)"

    assert _catalog_entry({"catalogEntry": [entry]}) == entry


def test_ensure_model_uploads_model_data_then_verifies_registration(tmp_path) -> None:
    model_uri = release_model_uri("release-1")
    model_path = tmp_path / "curated_model.trig"
    model_path.write_text("<urn:model> { <urn:model> a <http://www.w3.org/2002/07/owl#Ontology> . }")
    session = _ModelSession(model_uri)

    _ensure_model(session, "https://graphstudio.example", model_uri=model_uri, model_path=model_path)

    assert session.uploaded_name == "curated_model.trig"
    assert session.get_count == 2


class _DatasetSession:
    def __init__(self, deployment_id):
        self.deployment_id = str(deployment_id)
        self.deleted = []
        self.delete_kwargs = []
        self.uploaded = 0

    def get(self, url, **_kwargs):
        if url.endswith("/api/datasets"):
            return _GraphStudioResponse([{
                "uri": "http://example.com/dataset/old",
                "dataLocation": {"filePath": f"sync/{self.deployment_id}/old"},
            }])
        return _GraphStudioResponse({"catalogEntry": ["http://example.com/catalog/new"]})

    def delete(self, url, **kwargs):
        self.deleted.append(url)
        self.delete_kwargs.append(kwargs)
        return _GraphStudioResponse({"deleted": True})

    def post(self, _url, **_kwargs):
        self.uploaded += 1
        return _GraphStudioResponse({"uri": "http://example.com/dataset/new"}, status_code=201)


def test_ensure_dataset_replaces_legacy_orphan_before_upload(tmp_path) -> None:
    import uuid
    from types import SimpleNamespace

    deployment_id = uuid.uuid4()
    zip_path = tmp_path / "data.zip"
    zip_path.write_bytes(b"zip")
    session = _DatasetSession(deployment_id)
    settings = SimpleNamespace(shared_file_connection="urn:file", shared_file_path="sync")

    dataset_uri, catalog = _ensure_dataset(
        session, "https://graphstudio.example",
        deployment_id=deployment_id,
        deployment={
            "profile_key": "core", "environment_key": "dev", "slot": "blue",
            "curated_release_id": uuid.uuid4(),
        },
        zip_path=zip_path,
        model_uri=release_model_uri("release-1"),
        settings=settings,
        reuse_existing=False,
    )

    assert session.deleted and "http%3A%2F%2Fexample.com%2Fdataset%2Fold" in session.deleted[0]
    assert session.delete_kwargs[0]["params"] == {"force": "true"}
    assert session.uploaded == 1
    assert dataset_uri == "http://example.com/dataset/new"
    assert catalog == "http://example.com/catalog/new"


def test_dataset_replacement_remains_pending_after_force_delete_failure() -> None:
    plan = {"modelUri": release_model_uri("release-1")}
    error = {"message": "Remove obsolete deployment dataset failed: HTTP 500"}

    assert _requires_dataset_replacement(plan, error) is True
    assert _requires_dataset_replacement({**plan, "replaceExistingDataset": True}, {}) is True
    assert _requires_dataset_replacement(plan, {}) is False


class _LayerSession:
    def __init__(self):
        self.calls = []

    def patch(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _GraphStudioResponse({"updated": True})


def test_layer_switch_targets_only_the_requested_layer() -> None:
    session = _LayerSession()
    layer_uri = "http://example.com/layer/green"

    _set_layer_enabled(
        session,
        "https://graphstudio.example",
        encoded_graphmart="urn%3Agraphmart",
        layer_uri=layer_uri,
        enabled=False,
    )

    url, kwargs = session.calls[0]
    assert url.endswith("/api/graphmarts/urn%3Agraphmart/disableLayers")
    assert kwargs["json"] == [layer_uri]


class _LegacyLayerSession:
    def __init__(self, *, enabled, configured=True):
        self.enabled = enabled
        self.configured = configured

    def patch(self, _url, **_kwargs):
        response = _GraphStudioResponse(
            {"detail": "No handler found"}, ok=False, status_code=404,
        )
        response.text = "No handler found for PATCH /api/graphmarts/example/enableLayers"
        return response

    def get(self, url, **kwargs):
        if url.endswith("/layers"):
            return _GraphStudioResponse(
                [{"uri": "http://example.com/layer/green"}]
                if self.configured else []
            )
        assert url.endswith("/status")
        assert kwargs["params"] == {"detail": "true"}
        return _GraphStudioResponse({
            "childLayer": [{"uri": "http://example.com/layer/green", "enabled": self.enabled}],
        })


def test_legacy_layer_switch_accepts_manually_verified_state() -> None:
    mode = _set_layer_enabled(
        _LegacyLayerSession(enabled=True),
        "https://graphstudio.example",
        encoded_graphmart="urn%3Agraphmart",
        layer_uri="http://example.com/layer/green",
        enabled=True,
    )

    assert mode == "legacy_status_verified"


def test_legacy_layer_switch_requires_manual_change_before_retry() -> None:
    with pytest.raises(RuntimeError, match="手工启用 Layer"):
        _set_layer_enabled(
            _LegacyLayerSession(enabled=False),
            "https://graphstudio.example",
            encoded_graphmart="urn%3Agraphmart",
            layer_uri="http://example.com/layer/green",
            enabled=True,
        )


def test_legacy_layer_switch_skips_predecessor_from_another_graphmart() -> None:
    mode = _set_layer_enabled(
        _LegacyLayerSession(enabled=None, configured=False),
        "https://graphstudio.example",
        encoded_graphmart="urn%3Agraphmart",
        layer_uri="http://example.com/layer/from-old-target",
        enabled=False,
    )

    assert mode == "legacy_layer_not_in_target"


def test_deployment_plan_starts_new_lineage_after_graphmart_target_change(monkeypatch) -> None:
    import uuid
    from types import SimpleNamespace
    from src.graphstudio_sync import deployment as deployment_module

    release_id = uuid.uuid4()
    route = {
        "route_key": "core-dev", "environment_key": "dev", "target_key": "new-target",
        "graphmart_uri": "http://example.com/graphmart/new", "title": "New Graphmart",
        "promotion_order": 10, "apply_enabled": True, "requires_approval": False, "config": {},
    }
    monkeypatch.setattr(deployment_module, "deployment_status", lambda _repo, _profile: {
        "routes": [route],
        "activeCuratedRelease": {"release_id": release_id, "release_no": 2, "status": "active"},
        "activeOntologyRelease": {"ontology_release_id": uuid.uuid4(), "release_no": 1},
        "deployments": [{
            "deployment_id": uuid.uuid4(), "route_key": route["route_key"], "status": "active",
            "curated_release_id": release_id, "slot": "blue",
            "validation_result": {"reload": {"graphmartUri": "http://example.com/graphmart/old"}},
        }],
    })

    plan = build_deployment_plan(
        SimpleNamespace(), profile_key="core", environment_key="dev", route_key=route["route_key"],
    )

    assert plan["slot"] == "blue"
    assert plan["previousDeploymentId"] is None


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


def test_materialization_plan_ignores_retired_relationship_outside_active_scope() -> None:
    governance = _governance(relationships=[{
        "relationship_contract_key": "mfgorder-begin-product-v1",
        "source_class": "MfgOrder",
        "relationship_name": "BEGIN_PRODUCT",
        "target_class": "Product",
        "status": "retired",
    }])

    plan = build_materialization_plan(
        governance,
        [],
        profile_key="core",
        profile_relationships=[],
    )

    assert plan["ready"] is True
    assert plan["relationships"] == []
    assert not any("mfgorder-begin-product-v1" in item for item in plan["blockers"])


def test_materialization_plan_still_blocks_unapproved_relationship_in_active_scope() -> None:
    governance = _governance(relationships=[{
        "relationship_contract_key": "container-product-v1",
        "source_class": "Container",
        "relationship_name": "HAS_PRODUCT",
        "target_class": "Product",
        "status": "draft",
    }])

    plan = build_materialization_plan(
        governance,
        [],
        profile_key="core",
        profile_relationships=[{
            "source_class": "Container",
            "relationship_name": "HAS_PRODUCT",
            "target_class": "Product",
            "enabled": True,
        }],
    )

    assert plan["ready"] is False
    assert "关系契约未批准：container-product-v1" in plan["blockers"]


def test_physical_key_catalog_supplies_keys_not_exposed_as_ontology_properties() -> None:
    keys = _physical_key_catalog()["Container"]

    assert keys["primary"] == ["ContainerId"]


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


def test_materialization_plan_uses_narrow_backfill_after_contract_upgrade() -> None:
    governance = _governance(
        contracts=[_contract(version=4, approximate_rows=100_000_000)],
        latestRun={"publishable": True, "contract_versions": {"objects": {"product-v1": 4}}},
    )
    change = {
        "change_id": "11111111-1111-1111-1111-111111111111",
        "contract_key": "product-v1",
        "status": "applied",
        "target_version": 4,
        "items": [{
            "operation": "add_field",
            "field_key": "product-v1:brand-name",
            "before_state": None,
            "after_state": {"target_field": "brandName"},
        }],
    }

    plan = build_materialization_plan(
        governance, [change], profile_key="core",
        active_release_id="22222222-2222-2222-2222-222222222222",
        active_contract_versions={"product-v1": 3},
    )

    contract = plan["contracts"][0]
    assert plan["ready"] is True
    assert contract["extractionMode"] == "field_backfill"
    assert contract["fieldBackfill"]["affectedFieldKeys"] == ["product-v1:brand-name"]
    assert plan["schemaChangeIds"] == [change["change_id"]]


def test_field_backfill_patch_only_contains_changed_properties() -> None:
    patch = build_field_backfill_patch(
        _contract(),
        [{
            "field_key": "product-v1:brand-name",
            "source_column": "BrandName",
            "target_field": "brandName",
            "required": False,
        }],
        {"ProductId": 7, "BrandName": "Acme", "Description": "not selected"},
    )

    assert patch["properties"] == {"brandName": "Acme"}
    assert patch["sourceValues"] == {"BrandName": "Acme"}
    assert "Description" not in patch["sourceValues"]


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
