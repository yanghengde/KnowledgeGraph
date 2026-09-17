import pytest

from src.graphstudio_sync.attribute_projection import (
    apply_attribute_projections,
    compile_projection_query,
    fetch_projection_values,
    validate_projection_definition,
)
from src.graphstudio_sync.publishing.materialization import build_materialization_plan


def _projection(**overrides):
    return {
        "projection_key": "product-details",
        "source_schema": "dbo",
        "source_table": "A_ProductDetails",
        "source_alias": "src",
        "owner_mapping": [{"targetColumn": "ProductId", "sourcePath": "src.ProductId"}],
        "join_plan": [],
        "row_filters": [],
        "cardinality": "one",
        "multiple_match_policy": "reject",
        "missing_policy": "null",
        "collision_policy": "reject",
        "order_by": [],
        "config": {},
        "fields": [{
            "field_key": "product-details:brandName",
            "source_path": "src.BrandName",
            "target_field": "brandName",
            "data_type": "String",
            "required": False,
            "lifecycle_status": "active",
        }],
        **overrides,
    }


def _contract(**overrides):
    return {
        "selected_columns": ["ProductId", "Name"],
        "primary_key_columns": ["ProductId"],
        "fields": [{"target_field": "name", "lifecycle_status": "active"}],
        **overrides,
    }


def test_projection_definition_supports_declarative_multihop_join() -> None:
    projection = _projection(
        join_plan=[{
            "joinType": "left", "schema": "dbo", "table": "A_ProductDef",
            "alias": "definition", "left": "src.DefId", "right": "definition.InstanceId",
        }],
        fields=[{
            "field_key": "product-details:planningCode", "source_path": "definition.PlanningCode",
            "target_field": "planningCode", "data_type": "String", "lifecycle_status": "active",
        }],
    )

    result = validate_projection_definition(projection, projection["fields"], _contract())

    assert result["valid"] is True
    assert result["joinCount"] == 1


def test_projection_definition_rejects_raw_sql_and_implicit_collision() -> None:
    projection = _projection(
        source_table="A_ProductDetails; DROP TABLE Product",
        fields=[{
            "field_key": "overwrite-name", "source_path": "src.Name", "target_field": "name",
            "data_type": "String", "lifecycle_status": "active",
        }],
    )

    result = validate_projection_definition(projection, projection["fields"], _contract())

    assert result["valid"] is False
    assert any("source_table" in error for error in result["errors"])
    assert any("冲突" in error for error in result["errors"])


def test_compile_projection_query_uses_database_specific_bind_parameters() -> None:
    sql_server_sql, sql_server_params = compile_projection_query(
        _projection(), _projection()["fields"], [("P1",), ("P2",)], kind="camstar_sqlserver",
    )
    oracle_sql, oracle_params = compile_projection_query(
        _projection(source_schema="CAMSTAR", source_table="A_PRODUCTDETAILS"),
        _projection()["fields"], [("P1",)], kind="camstar_oracle",
    )

    assert "[dbo].[A_ProductDetails] [src]" in sql_server_sql
    assert sql_server_sql.count("%s") == 2
    assert sql_server_params == ("P1", "P2")
    assert '"CAMSTAR"."A_PRODUCTDETAILS" "src"' in oracle_sql
    assert ":p0" in oracle_sql
    assert oracle_params == {"p0": "P1"}


class _Cursor:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, sql, parameters):
        self.calls.append((sql, parameters))

    def fetchall(self):
        return list(self.rows)

    def close(self):
        pass


class _Connection:
    def __init__(self, rows):
        self.cursor_instance = _Cursor(rows)

    def cursor(self, **_kwargs):
        return self.cursor_instance


def test_projection_reads_owner_keys_in_bounded_batches() -> None:
    connection = _Connection([])
    owner_rows = [{"ProductId": index} for index in range(1001)]

    result = fetch_projection_values(
        connection, kind="camstar_sqlserver", projection=_projection(), owner_rows=owner_rows,
    )

    assert result["ownerCount"] == 1001
    assert len(connection.cursor_instance.calls) == 3
    assert max(len(parameters) for _, parameters in connection.cursor_instance.calls) <= 500


def test_projection_merges_values_and_quarantines_implicit_collision() -> None:
    connection = _Connection([{"__owner_0": "P1", "__field_0": "Related Name"}])
    projection = _projection(
        fields=[{
            "field_key": "related-name", "source_path": "src.Name", "target_field": "name",
            "data_type": "String", "required": False, "lifecycle_status": "active",
        }],
    )
    record = {
        "sourcePrimaryKey": {"ProductId": "P1"}, "businessKey": {"Name": "Main Name"},
        "sourceValues": {"ProductId": "P1", "Name": "Main Name"},
        "properties": {"name": "Main Name"}, "qualityIssues": [], "recordStatus": "active",
    }

    result = apply_attribute_projections(
        connection, kind="camstar_sqlserver", projections=[projection],
        owner_rows=[{"ProductId": "P1"}], records=[record],
    )

    assert result[0]["properties"]["name"] == "Main Name"
    assert result[0]["recordStatus"] == "quarantined"
    assert any("collision.name" in issue for issue in result[0]["qualityIssues"])


def test_materialization_plan_blocks_unapproved_projection() -> None:
    contract = {
        "contract_key": "product-v1", "class_name": "Product", "version": 1,
        "status": "approved", "class_review_status": "approved", "mapping_status": "resolved",
        "source_schema": "dbo", "source_table": "Product", "primary_key_columns": ["ProductId"],
    }
    governance = {
        "contracts": [contract], "relationships": [],
        "latestRun": {"publishable": True, "contract_versions": {"objects": {"product-v1": 1}}},
    }

    plan = build_materialization_plan(
        governance, [], profile_key="core",
        attribute_projections=[{
            "projection_key": "product-details", "target_contract_key": "product-v1",
            "version": 1, "enabled": True, "status": "draft", "preview_status": "succeeded", "fields": [],
        }],
    )

    assert plan["ready"] is False
    assert any("属性投影未批准" in blocker for blocker in plan["blockers"])

