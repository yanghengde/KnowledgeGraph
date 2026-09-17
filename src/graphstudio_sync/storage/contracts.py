"""contracts persistence for the control plane."""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

from sqlalchemy import text


from .repository_support import _rows, _physical_key_catalog


class ContractsRepository:
    def governance_profile(self, profile_key: str) -> dict[str, Any]:
        with self.engine.connect() as connection:
            profile_exists = connection.execute(
                text("SELECT EXISTS(SELECT 1 FROM graphsync.graph_profile WHERE profile_key=:key)"),
                {"key": profile_key},
            ).scalar_one()
            if not profile_exists:
                raise KeyError(profile_key)
            contracts = _rows(
                connection.execute(
                    text(
                        """
                        SELECT contract.contract_key, contract.profile_key,
                               contract.class_name, contract.version, contract.status,
                               contract.source_schema, contract.source_table,
                               contract.primary_key_columns,
                               contract.business_key_columns,
                               contract.selected_columns, contract.required_columns,
                               contract.freshness_column, contract.preview_row_limit,
                               contract.publication_layer, contract.quality_thresholds,
                               contract.config, contract.updated_at,
                               mapping.physical_schema AS mapped_schema,
                               mapping.physical_table AS mapped_table,
                               mapping.approximate_rows, mapping.mapping_status,
                               class.review_status AS class_review_status,
                               class.orphan_policy
                        FROM graphsync.data_contract contract
                        LEFT JOIN graphsync.current_class_mapping mapping
                          ON mapping.class_name=contract.class_name
                        LEFT JOIN graphsync.profile_class class
                          ON class.profile_key=contract.profile_key
                         AND class.class_name=contract.class_name
                        WHERE contract.profile_key=:profile_key
                        ORDER BY contract.class_name
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
            relationships = _rows(
                connection.execute(
                    text(
                        """
                        SELECT relationship.relationship_contract_key,
                               relationship.profile_key,
                               relationship.version,
                               relationship.source_contract_key,
                               source.class_name AS source_class,
                               relationship.relationship_name,
                               relationship.target_contract_key,
                               target.class_name AS target_class,
                               relationship.source_columns,
                               relationship.target_columns,
                               relationship.semantic_role,
                               relationship.required_context,
                               relationship.status, relationship.config,
                               relationship.updated_at
                        FROM graphsync.relationship_contract relationship
                        JOIN graphsync.data_contract source
                          ON source.contract_key=relationship.source_contract_key
                        JOIN graphsync.data_contract target
                          ON target.contract_key=relationship.target_contract_key
                        WHERE relationship.profile_key=:profile_key
                        ORDER BY source.class_name, relationship.relationship_name
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
            latest_run = connection.execute(
                text(
                    """
                    SELECT curation_run_id, profile_key, status, preview_only,
                           started_at, finished_at, source_rows_read,
                           accepted_rows, quarantined_rows, publishable,
                           contract_versions, summary, error
                    FROM graphsync.curation_run
                    WHERE profile_key=:profile_key
                    ORDER BY started_at DESC LIMIT 1
                    """
                ),
                {"profile_key": profile_key},
            ).mappings().one_or_none()
            quality_results: list[dict[str, Any]] = []
            if latest_run is not None:
                quality_results = _rows(
                    connection.execute(
                        text(
                            """
                            SELECT quality_result_id, contract_key,
                                   relationship_contract_key, rule_key,
                                   severity, passed, checked_rows, failed_rows,
                                   message, details, created_at
                            FROM graphsync.data_quality_result
                            WHERE curation_run_id=:run_id
                            ORDER BY passed, severity DESC, rule_key
                            """
                        ),
                        {"run_id": latest_run["curation_run_id"]},
                    )
                )
        return {
            "contracts": contracts,
            "relationships": relationships,
            "latestRun": dict(latest_run) if latest_run else None,
            "qualityResults": quality_results,
        }


    def governance_contract_candidates(self, profile_key: str) -> dict[str, Any]:
        """Return only active profile members that still need governed contracts."""
        with self.engine.connect() as connection:
            classes = _rows(connection.execute(text("""
                SELECT configured.class_name, configured.role,
                       mapping.physical_schema, mapping.physical_table,
                       mapping.mapping_status
                FROM graphsync.profile_class configured
                JOIN graphsync.current_class_mapping mapping
                  ON mapping.class_name=configured.class_name
                LEFT JOIN graphsync.data_contract contract
                  ON contract.profile_key=configured.profile_key
                 AND contract.class_name=configured.class_name
                WHERE configured.profile_key=:profile_key
                  AND configured.enabled AND contract.contract_key IS NULL
                ORDER BY configured.priority, configured.class_name
            """), {"profile_key": profile_key}))
            properties = _rows(connection.execute(text("""
                SELECT property.class_name, property.property_name,
                       property.data_type, property.required,
                       property.physical_column, property.mapping_status
                FROM graphsync.current_property_mapping property
                JOIN graphsync.profile_class configured
                  ON configured.profile_key=:profile_key
                 AND configured.class_name=property.class_name
                 AND configured.enabled
                LEFT JOIN graphsync.data_contract contract
                  ON contract.profile_key=configured.profile_key
                 AND contract.class_name=configured.class_name
                WHERE contract.contract_key IS NULL
                  AND property.physical_column IS NOT NULL
                  AND property.mapping_status IN ('resolved', 'override')
                ORDER BY property.class_name, property.required DESC,
                         property.property_name
            """), {"profile_key": profile_key}))
            relationships = _rows(connection.execute(text("""
                SELECT configured.source_class, configured.relationship_name,
                       configured.target_class, configured.required_context,
                       mapping.mapping_status, mapping.source_property,
                       mapping.physical_column,
                       source.contract_key AS source_contract_key,
                       target.contract_key AS target_contract_key,
                       target.primary_key_columns AS target_columns
                FROM graphsync.profile_relationship configured
                LEFT JOIN graphsync.current_relationship_mapping mapping
                  ON mapping.source_class=configured.source_class
                 AND mapping.relationship_name=configured.relationship_name
                 AND mapping.target_class=configured.target_class
                LEFT JOIN graphsync.data_contract source
                  ON source.profile_key=configured.profile_key
                 AND source.class_name=configured.source_class
                LEFT JOIN graphsync.data_contract target
                  ON target.profile_key=configured.profile_key
                 AND target.class_name=configured.target_class
                LEFT JOIN graphsync.relationship_contract contract
                  ON contract.profile_key=configured.profile_key
                 AND contract.source_contract_key=source.contract_key
                 AND contract.relationship_name=configured.relationship_name
                 AND contract.target_contract_key=target.contract_key
                WHERE configured.profile_key=:profile_key
                  AND configured.enabled
                  AND contract.relationship_contract_key IS NULL
                ORDER BY configured.source_class, configured.relationship_name,
                         configured.target_class
            """), {"profile_key": profile_key}))
        property_groups: dict[str, list[dict[str, Any]]] = {}
        for item in properties:
            property_groups.setdefault(item["class_name"], []).append(item)
        for item in classes:
            physical_keys = _physical_key_catalog().get(item["class_name"], {"primary": [], "business": []})
            resolved = property_groups.get(item["class_name"], [])
            resolved_columns = {property["physical_column"] for property in resolved}
            for column in [*physical_keys["primary"], *physical_keys["business"]]:
                if column not in resolved_columns:
                    resolved.append({
                        "class_name": item["class_name"],
                        "property_name": column,
                        "data_type": "String",
                        "required": column in physical_keys["primary"],
                        "physical_column": column,
                        "mapping_status": "physical_key",
                    })
            item["properties"] = resolved
            item["suggested_primary_key_columns"] = physical_keys["primary"]
            item["suggested_business_key_columns"] = physical_keys["business"]
        return {"classes": classes, "relationships": relationships}


    def create_data_contract(
        self,
        profile_key: str,
        *,
        class_name: str,
        primary_key_columns: list[str],
        business_key_columns: list[str],
        selected_columns: list[str],
        required_columns: list[str],
        freshness_column: str | None,
        preview_row_limit: int,
        publication_layer: str,
    ) -> dict[str, Any]:
        candidates = self.governance_contract_candidates(profile_key)
        candidate = next((item for item in candidates["classes"] if item["class_name"] == class_name), None)
        if candidate is None:
            raise KeyError(class_name)
        available = {item["physical_column"] for item in candidate["properties"]}
        selected = list(dict.fromkeys(selected_columns))
        primary = list(dict.fromkeys(primary_key_columns))
        business = list(dict.fromkeys(business_key_columns))
        required = list(dict.fromkeys([*primary, *required_columns]))
        requested = set(selected) | set(primary) | set(business) | set(required)
        if freshness_column:
            requested.add(freshness_column)
        unknown = sorted(requested - available)
        if unknown:
            raise ValueError(f"Contract columns are not resolved physical columns: {unknown}")
        if not primary:
            raise ValueError("At least one primary key column is required")
        if not set(primary).issubset(selected):
            raise ValueError("Primary key columns must be part of selected columns")
        contract_key = f"{profile_key}:{class_name}:v1".lower()
        property_by_column: dict[str, dict[str, Any]] = {}
        for item in candidate["properties"]:
            property_by_column.setdefault(item["physical_column"], item)
        with self.engine.begin() as connection:
            row = connection.execute(text("""
                INSERT INTO graphsync.data_contract
                    (contract_key, profile_key, class_name, version, status,
                     source_schema, source_table, primary_key_columns,
                     business_key_columns, selected_columns, required_columns,
                     freshness_column, preview_row_limit, publication_layer,
                     quality_thresholds, config)
                VALUES
                    (:contract_key, :profile_key, :class_name, 1, 'draft',
                     :source_schema, :source_table, CAST(:primary AS jsonb),
                     CAST(:business AS jsonb), CAST(:selected AS jsonb),
                     CAST(:required AS jsonb), :freshness, :preview_limit,
                     :publication_layer, '{}'::jsonb,
                     jsonb_build_object('generatedBy', 'advanced-governance-wizard'))
                RETURNING *
            """), {
                "contract_key": contract_key, "profile_key": profile_key,
                "class_name": class_name,
                "source_schema": candidate["physical_schema"],
                "source_table": candidate["physical_table"],
                "primary": json.dumps(primary), "business": json.dumps(business),
                "selected": json.dumps(selected), "required": json.dumps(required),
                "freshness": freshness_column, "preview_limit": preview_row_limit,
                "publication_layer": publication_layer,
            }).mappings().one()
            field_rows = []
            for position, column in enumerate(selected, start=1):
                prop = property_by_column[column]
                role = "primary_key" if column in primary else "business_key" if column in business else "freshness" if column == freshness_column else "navigation" if prop.get("data_type") == "Navigation" else "attribute"
                field_rows.append({
                    "contract_key": contract_key,
                    "field_key": f"{contract_key}:{prop['property_name'].lower()}",
                    "source_column": column,
                    "target_field": prop["property_name"],
                    "data_type": prop.get("data_type") or "String",
                    "nullable": column not in required,
                    "required": column in required,
                    "field_role": role,
                    "position": position * 10,
                    "ontology_property": prop["property_name"],
                })
            connection.execute(text("""
                INSERT INTO graphsync.data_contract_field
                    (contract_key, field_key, source_column, target_field,
                     data_type, nullable, required, field_role,
                     lifecycle_status, ordinal_position, introduced_version,
                     ontology_property, config)
                VALUES
                    (:contract_key, :field_key, :source_column, :target_field,
                     :data_type, :nullable, :required, :field_role,
                     'active', :position, 1, :ontology_property,
                     jsonb_build_object('generatedBy', 'advanced-governance-wizard'))
            """), field_rows)
        return dict(row)


    def create_relationship_contract(
        self,
        profile_key: str,
        *,
        source_class: str,
        relationship_name: str,
        target_class: str,
        semantic_role: str,
        required_context: bool,
    ) -> dict[str, Any]:
        candidates = self.governance_contract_candidates(profile_key)
        candidate = next((item for item in candidates["relationships"] if item["source_class"] == source_class and item["relationship_name"] == relationship_name and item["target_class"] == target_class), None)
        if candidate is None:
            raise KeyError(relationship_name)
        target_columns = list(candidate.get("target_columns") or [])
        if candidate.get("mapping_status") != "resolved" or not candidate.get("physical_column"):
            raise ValueError("Relationship mapping must be resolved before creating its contract")
        if not candidate.get("source_contract_key") or not candidate.get("target_contract_key"):
            raise ValueError("Source and target data contracts must exist first")
        if len(target_columns) != 1:
            raise ValueError("Composite target keys require manual relationship contract configuration")
        key = f"{profile_key}:{source_class}:{relationship_name}:{target_class}:v1".lower()
        with self.engine.begin() as connection:
            row = connection.execute(text("""
                INSERT INTO graphsync.relationship_contract
                    (relationship_contract_key, profile_key, version,
                     source_contract_key, relationship_name,
                     target_contract_key, source_columns, target_columns,
                     semantic_role, required_context, status, config)
                VALUES
                    (:key, :profile_key, 1, :source_contract_key,
                     :relationship_name, :target_contract_key,
                     CAST(:source_columns AS jsonb), CAST(:target_columns AS jsonb),
                     :semantic_role, :required_context, 'draft',
                     jsonb_build_object('generatedBy', 'advanced-governance-wizard'))
                RETURNING *
            """), {
                "key": key, "profile_key": profile_key,
                "source_contract_key": candidate["source_contract_key"],
                "relationship_name": relationship_name,
                "target_contract_key": candidate["target_contract_key"],
                "source_columns": json.dumps([candidate["physical_column"]]),
                "target_columns": json.dumps(target_columns),
                "semantic_role": semantic_role,
                "required_context": required_context,
            }).mappings().one()
        return dict(row)


    def update_data_contract(
        self,
        contract_key: str,
        *,
        status: str,
        business_key_columns: list[str],
        required_columns: list[str],
        freshness_column: str | None,
        preview_row_limit: int,
        publication_layer: str,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            existing = connection.execute(
                text(
                    """
                    SELECT selected_columns
                    FROM graphsync.data_contract
                    WHERE contract_key=:contract_key
                    FOR UPDATE
                    """
                ),
                {"contract_key": contract_key},
            ).mappings().one_or_none()
            if existing is None:
                raise KeyError(contract_key)
            selected = set(existing["selected_columns"] or [])
            requested = set(business_key_columns) | set(required_columns)
            if freshness_column:
                requested.add(freshness_column)
            unknown = sorted(requested - selected)
            if unknown:
                raise ValueError(
                    f"Contract columns are not part of the governed projection: {unknown}"
                )
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.data_contract
                    SET version=version + 1, status=:status,
                        business_key_columns=CAST(:business_keys AS jsonb),
                        required_columns=CAST(:required_columns AS jsonb),
                        freshness_column=:freshness_column,
                        preview_row_limit=:preview_row_limit,
                        publication_layer=:publication_layer
                    WHERE contract_key=:contract_key
                    RETURNING contract_key, profile_key, class_name, version,
                              status, source_schema, source_table,
                              primary_key_columns, business_key_columns,
                              selected_columns, required_columns,
                              freshness_column, preview_row_limit,
                              publication_layer, quality_thresholds, config,
                              updated_at
                    """
                ),
                {
                    "contract_key": contract_key,
                    "status": status,
                    "business_keys": json.dumps(business_key_columns),
                    "required_columns": json.dumps(required_columns),
                    "freshness_column": freshness_column,
                    "preview_row_limit": preview_row_limit,
                    "publication_layer": publication_layer,
                },
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(contract_key)
        return dict(row)


    def update_relationship_contract(
        self,
        relationship_contract_key: str,
        *,
        status: str,
        semantic_role: str,
        required_context: bool,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.relationship_contract
                    SET version=version + 1, status=:status, semantic_role=:semantic_role,
                        required_context=:required_context
                    WHERE relationship_contract_key=:key
                    RETURNING relationship_contract_key, profile_key, version,
                              source_contract_key, relationship_name,
                              target_contract_key, source_columns,
                              target_columns, semantic_role, required_context,
                              status, config, updated_at
                    """
                ),
                {
                    "key": relationship_contract_key,
                    "status": status,
                    "semantic_role": semantic_role,
                    "required_context": required_context,
                },
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(relationship_contract_key)
        return dict(row)


    def contract_schema(self, contract_key: str) -> dict[str, Any]:
        with self.engine.connect() as connection:
            contract = connection.execute(
                text(
                    """
                    SELECT contract_key, profile_key, class_name, version, status,
                           source_schema, source_table, primary_key_columns,
                           business_key_columns, selected_columns, required_columns,
                           freshness_column, publication_layer, config, updated_at
                    FROM graphsync.data_contract
                    WHERE contract_key=:contract_key
                    """
                ),
                {"contract_key": contract_key},
            ).mappings().one_or_none()
            if contract is None:
                raise KeyError(contract_key)
            fields = _rows(
                connection.execute(
                    text(
                        """
                        SELECT contract_key, field_key, source_column, target_field,
                               data_type, nullable, required, field_role,
                               lifecycle_status, ordinal_position,
                               introduced_version, deprecated_version,
                               transform_expression, default_expression,
                               ontology_property, sensitivity, searchable,
                               sortable, config, updated_at
                        FROM graphsync.data_contract_field
                        WHERE contract_key=:contract_key
                        ORDER BY ordinal_position, field_key
                        """
                    ),
                    {"contract_key": contract_key},
                )
            )
            field_keys = [row["field_key"] for row in fields]
            dependencies = []
            if field_keys:
                dependencies = _rows(
                    connection.execute(
                        text(
                            """
                            SELECT dependency_id, profile_key, upstream_type,
                                   upstream_key, downstream_type, downstream_key,
                                   dependency_kind, discovered_by, active, metadata,
                                   first_seen_at, last_seen_at
                            FROM graphsync.asset_dependency
                            WHERE profile_key=:profile_key
                              AND upstream_type='data_contract_field'
                              AND upstream_key = ANY(:field_keys)
                            ORDER BY upstream_key, downstream_type, downstream_key
                            """
                        ),
                        {
                            "profile_key": contract["profile_key"],
                            "field_keys": field_keys,
                        },
                    )
                )
        counts = Counter(row["upstream_key"] for row in dependencies if row["active"])
        for field in fields:
            field["dependency_count"] = counts[field["field_key"]]
        return {
            "contract": dict(contract),
            "fields": fields,
            "dependencies": dependencies,
        }

