"""model catalog persistence for the control plane."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text


from .repository_support import _rows, PLAN_FILE


class ModelCatalogRepository:
    def list_mapping_overrides(self) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            return _rows(
                connection.execute(
                    text(
                        """
                        SELECT class_name, property_name, physical_schema, physical_table,
                               physical_column, target_class, mapping_kind, expression,
                               enabled, notes, updated_at
                        FROM graphsync.mapping_override ORDER BY class_name, property_name
                        """
                    )
                )
            )


    def upsert_property_override(
        self,
        *,
        class_name: str,
        property_name: str,
        physical_table: str,
        physical_column: str | None,
        mapping_kind: str,
        expression: str | None,
        notes: str | None,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO graphsync.mapping_override
                        (class_name, property_name, physical_table, physical_column,
                         mapping_kind, expression, notes)
                    VALUES
                        (:class_name, :property_name, :physical_table, :physical_column,
                         :mapping_kind, :expression, :notes)
                    ON CONFLICT (class_name, property_name) DO UPDATE SET
                        physical_table=EXCLUDED.physical_table,
                        physical_column=EXCLUDED.physical_column,
                        mapping_kind=EXCLUDED.mapping_kind,
                        expression=EXCLUDED.expression,
                        notes=EXCLUDED.notes,
                        enabled=true
                    RETURNING class_name, property_name, physical_table, physical_column,
                              mapping_kind, expression, enabled, notes, updated_at
                    """
                ),
                locals(),
            ).mappings().one()
        return dict(row)


    def upsert_relationship_override(
        self,
        *,
        source_class: str,
        relationship_name: str,
        target_class: str,
        source_property: str,
        notes: str | None,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO graphsync.relationship_override
                        (source_class, relationship_name, target_class, source_property, notes)
                    VALUES
                        (:source_class, :relationship_name, :target_class, :source_property, :notes)
                    ON CONFLICT (source_class, relationship_name, target_class) DO UPDATE SET
                        source_property=EXCLUDED.source_property,
                        notes=EXCLUDED.notes,
                        enabled=true
                    RETURNING source_class, relationship_name, target_class,
                              source_property, enabled, notes, updated_at
                    """
                ),
                locals(),
            ).mappings().one()
        return dict(row)


    def inventory(self) -> dict[str, Any]:
        if not PLAN_FILE.exists():
            return {"available": False}
        return {"available": True, **json.loads(PLAN_FILE.read_text(encoding="utf-8"))}


    def mapping_catalog(self) -> dict[str, Any]:
        with self.engine.connect() as connection:
            snapshot = connection.execute(
                text("SELECT * FROM graphsync.current_catalog_snapshot")
            ).mappings().one_or_none()
            if snapshot is None:
                return {"available": False, "unresolvedProperties": [], "relationshipStatus": {}}
            unresolved = _rows(
                connection.execute(
                    text(
                        """
                        SELECT class_name AS "className", property_name AS "propertyName",
                               data_type AS "dataType", source_field_id AS "sourceFieldId",
                               physical_table AS "physicalTable", mapping_status AS "mappingStatus"
                        FROM graphsync.current_property_mapping
                        WHERE mapping_status = 'unresolved'
                        ORDER BY class_name, property_name
                        """
                    )
                )
            )
            relationship_status = {
                row["mapping_status"]: row["count"]
                for row in connection.execute(
                    text(
                        """
                        SELECT mapping_status, count(*) AS count
                        FROM graphsync.current_relationship_mapping GROUP BY mapping_status
                        """
                    )
                ).mappings()
            }
            relationship_review = _rows(
                connection.execute(
                    text(
                        """
                        SELECT source_class AS "sourceClass",
                               relationship_name AS "relationshipName",
                               target_class AS "targetClass", cardinality,
                               candidate_properties AS "candidateProperties",
                               mapping_status AS "mappingStatus",
                               candidate_count AS "candidateCount"
                        FROM graphsync.current_relationship_mapping
                        WHERE mapping_status <> 'resolved'
                        ORDER BY mapping_status, source_class, relationship_name, target_class
                        """
                    )
                )
            )
        return {
            "available": True,
            "snapshot": dict(snapshot),
            "unresolvedProperties": unresolved,
            "relationshipStatus": relationship_status,
            "relationshipReview": relationship_review,
        }


    def list_graph_profiles(self) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            profiles = _rows(
                connection.execute(
                    text(
                        """
                        SELECT profile_key, title, description, job_name, enabled,
                               max_depth, max_context_nodes_per_seed,
                               max_total_nodes_per_run, config, updated_at
                        FROM graphsync.graph_profile
                        ORDER BY profile_key
                        """
                    )
                )
            )
            counts = _rows(
                connection.execute(
                    text(
                        """
                        SELECT profile_key, role, count(*) AS count
                        FROM graphsync.profile_class
                        WHERE enabled
                        GROUP BY profile_key, role
                        """
                    )
                )
            )
        for profile in profiles:
            profile["class_counts"] = {
                row["role"]: row["count"]
                for row in counts
                if row["profile_key"] == profile["profile_key"]
            }
        return profiles


    def graph_profile(self, profile_key: str) -> dict[str, Any]:
        with self.engine.connect() as connection:
            profile = connection.execute(
                text(
                    """
                    SELECT profile_key, title, description, job_name, enabled,
                           max_depth, max_context_nodes_per_seed,
                           max_total_nodes_per_run, config, updated_at
                    FROM graphsync.graph_profile WHERE profile_key=:profile_key
                    """
                ),
                {"profile_key": profile_key},
            ).mappings().one_or_none()
            if profile is None:
                raise KeyError(profile_key)
            classes = _rows(
                connection.execute(
                    text(
                        """
                        SELECT configured.profile_key, configured.class_name,
                               configured.role, configured.orphan_policy,
                               configured.seed_enabled, configured.max_instances_per_run,
                               configured.priority, configured.enabled,
                               configured.review_status, configured.config,
                               mapping.physical_schema, mapping.physical_table,
                               mapping.approximate_rows, mapping.mapping_status
                        FROM graphsync.profile_class configured
                        LEFT JOIN graphsync.current_class_mapping mapping
                          ON mapping.class_name=configured.class_name
                        WHERE configured.profile_key=:profile_key
                        ORDER BY configured.priority, configured.class_name
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
            relationships = _rows(
                connection.execute(
                    text(
                        """
                        SELECT configured.profile_key, configured.source_class,
                               configured.relationship_name, configured.target_class,
                               configured.strength, configured.required_context,
                               configured.traverse, configured.direction,
                               configured.max_depth, configured.max_targets_per_source,
                               configured.enabled, configured.review_status,
                               configured.config,
                               COALESCE(
                                   mapping.mapping_status,
                                   CASE WHEN semantic_contract.relationship_contract_key IS NOT NULL
                                        THEN 'resolved' ELSE 'unresolved' END
                               ) AS mapping_status,
                               mapping.cardinality,
                               mapping.source_property,
                               COALESCE(mapping.physical_column,
                                        semantic_contract.source_columns->>0) AS physical_column
                        FROM graphsync.profile_relationship configured
                        LEFT JOIN graphsync.current_relationship_mapping mapping
                          ON mapping.source_class=configured.source_class
                         AND mapping.relationship_name=configured.relationship_name
                         AND mapping.target_class=configured.target_class
                        LEFT JOIN graphsync.data_contract source_contract
                          ON source_contract.profile_key=configured.profile_key
                         AND source_contract.class_name=configured.source_class
                        LEFT JOIN graphsync.data_contract target_contract
                          ON target_contract.profile_key=configured.profile_key
                         AND target_contract.class_name=configured.target_class
                        LEFT JOIN graphsync.relationship_contract semantic_contract
                          ON semantic_contract.profile_key=configured.profile_key
                         AND semantic_contract.source_contract_key=source_contract.contract_key
                         AND semantic_contract.relationship_name=configured.relationship_name
                         AND semantic_contract.target_contract_key=target_contract.contract_key
                         AND semantic_contract.status <> 'retired'
                        WHERE configured.profile_key=:profile_key
                        ORDER BY configured.source_class,
                                 configured.relationship_name, configured.target_class
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
        return {"profile": dict(profile), "classes": classes, "relationships": relationships}


    def graph_profile_candidates(self, profile_key: str) -> dict[str, list[dict[str, Any]]]:
        with self.engine.connect() as connection:
            exists = connection.execute(
                text("SELECT EXISTS(SELECT 1 FROM graphsync.graph_profile WHERE profile_key=:key)"),
                {"key": profile_key},
            ).scalar_one()
            if not exists:
                raise KeyError(profile_key)
            classes = _rows(
                connection.execute(
                    text(
                        """
                        SELECT mapping.class_name, mapping.chinese_name,
                               mapping.physical_schema, mapping.physical_table,
                               mapping.approximate_rows, mapping.mapping_status,
                               (configured.class_name IS NOT NULL) AS configured
                        FROM graphsync.current_class_mapping mapping
                        LEFT JOIN graphsync.profile_class configured
                          ON configured.profile_key=:profile_key
                         AND configured.class_name=mapping.class_name
                        ORDER BY configured DESC, mapping.approximate_rows DESC,
                                 mapping.class_name
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
            relationships = _rows(
                connection.execute(
                    text(
                        """
                        WITH candidates AS (
                            SELECT mapping.source_class, mapping.relationship_name,
                                   mapping.target_class, mapping.cardinality,
                                   mapping.mapping_status, mapping.source_property,
                                   mapping.physical_column
                            FROM graphsync.current_relationship_mapping mapping
                            JOIN graphsync.profile_class source_class
                              ON source_class.profile_key=:profile_key
                             AND source_class.class_name=mapping.source_class
                             AND source_class.enabled
                            UNION ALL
                            SELECT source.class_name, contract.relationship_name,
                                   target.class_name, NULL::text, 'resolved', NULL::text,
                                   contract.source_columns->>0
                            FROM graphsync.relationship_contract contract
                            JOIN graphsync.data_contract source
                              ON source.contract_key=contract.source_contract_key
                            JOIN graphsync.data_contract target
                              ON target.contract_key=contract.target_contract_key
                            JOIN graphsync.profile_class source_class
                              ON source_class.profile_key=:profile_key
                             AND source_class.class_name=source.class_name
                             AND source_class.enabled
                            WHERE contract.profile_key=:profile_key
                              AND contract.status <> 'retired'
                              AND NOT EXISTS (
                                  SELECT 1 FROM graphsync.current_relationship_mapping mapping
                                  WHERE mapping.source_class=source.class_name
                                    AND mapping.relationship_name=contract.relationship_name
                                    AND mapping.target_class=target.class_name
                              )
                        )
                        SELECT candidates.source_class, candidates.relationship_name,
                               candidates.target_class, candidates.cardinality,
                               candidates.mapping_status, candidates.source_property,
                               candidates.physical_column,
                               (configured.relationship_name IS NOT NULL) AS configured
                        FROM candidates
                        LEFT JOIN graphsync.profile_relationship configured
                          ON configured.profile_key=:profile_key
                         AND configured.source_class=candidates.source_class
                         AND configured.relationship_name=candidates.relationship_name
                         AND configured.target_class=candidates.target_class
                        ORDER BY configured DESC, candidates.source_class,
                                 candidates.relationship_name, candidates.target_class
                        """
                    ),
                    {"profile_key": profile_key},
                )
            )
        return {"classes": classes, "relationships": relationships}


    def update_graph_profile(
        self,
        profile_key: str,
        *,
        title: str,
        description: str | None,
        enabled: bool,
        max_depth: int,
        max_context_nodes_per_seed: int,
        max_total_nodes_per_run: int,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE graphsync.graph_profile
                    SET title=:title, description=:description, enabled=:enabled,
                        max_depth=:max_depth,
                        max_context_nodes_per_seed=:max_context_nodes_per_seed,
                        max_total_nodes_per_run=:max_total_nodes_per_run
                    WHERE profile_key=:profile_key
                    RETURNING profile_key, title, description, job_name, enabled,
                              max_depth, max_context_nodes_per_seed,
                              max_total_nodes_per_run, config, updated_at
                    """
                ),
                locals(),
            ).mappings().one_or_none()
        if row is None:
            raise KeyError(profile_key)
        return dict(row)


    def upsert_profile_class(
        self,
        profile_key: str,
        class_name: str,
        *,
        role: str,
        orphan_policy: str,
        seed_enabled: bool,
        max_instances_per_run: int | None,
        priority: int,
        enabled: bool,
        review_status: str,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            mapped = connection.execute(
                text("SELECT EXISTS(SELECT 1 FROM graphsync.current_class_mapping WHERE class_name=:class_name)"),
                {"class_name": class_name},
            ).scalar_one()
            if not mapped:
                raise KeyError(class_name)
            row = connection.execute(
                text(
                    """
                    INSERT INTO graphsync.profile_class
                        (profile_key, class_name, role, orphan_policy, seed_enabled,
                         max_instances_per_run, priority, enabled, review_status)
                    VALUES
                        (:profile_key, :class_name, :role, :orphan_policy, :seed_enabled,
                         :max_instances_per_run, :priority, :enabled, :review_status)
                    ON CONFLICT (profile_key, class_name) DO UPDATE SET
                        role=EXCLUDED.role, orphan_policy=EXCLUDED.orphan_policy,
                        seed_enabled=EXCLUDED.seed_enabled,
                        max_instances_per_run=EXCLUDED.max_instances_per_run,
                        priority=EXCLUDED.priority, enabled=EXCLUDED.enabled,
                        review_status=EXCLUDED.review_status
                    RETURNING profile_key, class_name, role, orphan_policy,
                              seed_enabled, max_instances_per_run, priority,
                              enabled, review_status, config, updated_at
                    """
                ),
                locals(),
            ).mappings().one()
        return dict(row)


    def upsert_profile_relationship(
        self,
        profile_key: str,
        source_class: str,
        relationship_name: str,
        target_class: str,
        *,
        strength: str,
        required_context: bool,
        traverse: bool,
        direction: str,
        max_depth: int | None,
        max_targets_per_source: int,
        enabled: bool,
        review_status: str,
    ) -> dict[str, Any]:
        with self.engine.begin() as connection:
            candidate = connection.execute(
                text(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM graphsync.current_relationship_mapping
                        WHERE source_class=:source_class
                          AND relationship_name=:relationship_name
                          AND target_class=:target_class
                        UNION ALL
                        SELECT 1
                        FROM graphsync.relationship_contract contract
                        JOIN graphsync.data_contract source
                          ON source.contract_key=contract.source_contract_key
                        JOIN graphsync.data_contract target
                          ON target.contract_key=contract.target_contract_key
                        WHERE contract.profile_key=:profile_key
                          AND source.class_name=:source_class
                          AND contract.relationship_name=:relationship_name
                          AND target.class_name=:target_class
                          AND contract.status <> 'retired'
                    )
                    """
                ),
                locals(),
            ).scalar_one()
            if not candidate:
                raise KeyError(relationship_name)
            row = connection.execute(
                text(
                    """
                    INSERT INTO graphsync.profile_relationship
                        (profile_key, source_class, relationship_name, target_class,
                         strength, required_context, traverse, direction, max_depth,
                         max_targets_per_source, enabled, review_status)
                    VALUES
                        (:profile_key, :source_class, :relationship_name, :target_class,
                         :strength, :required_context, :traverse, :direction, :max_depth,
                         :max_targets_per_source, :enabled, :review_status)
                    ON CONFLICT (profile_key, source_class, relationship_name, target_class)
                    DO UPDATE SET strength=EXCLUDED.strength,
                        required_context=EXCLUDED.required_context,
                        traverse=EXCLUDED.traverse, direction=EXCLUDED.direction,
                        max_depth=EXCLUDED.max_depth,
                        max_targets_per_source=EXCLUDED.max_targets_per_source,
                        enabled=EXCLUDED.enabled, review_status=EXCLUDED.review_status
                    RETURNING profile_key, source_class, relationship_name,
                              target_class, strength, required_context, traverse,
                              direction, max_depth, max_targets_per_source,
                              enabled, review_status, config, updated_at
                    """
                ),
                locals(),
            ).mappings().one()
        return dict(row)

