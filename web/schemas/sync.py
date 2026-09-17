"""Validated request contracts for synchronization, governance and publishing."""
from __future__ import annotations
import uuid
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

class ConnectionUpdate(BaseModel):
    kind: Literal[
        "camstar_sqlserver", "camstar_oracle",
        "graph_studio", "state_postgresql",
    ]
    display_name: str = Field(min_length=1, max_length=120)
    endpoint: str = Field(min_length=1, max_length=500)
    database_name: str | None = Field(default=None, max_length=500)
    username: str | None = Field(default=None, max_length=200)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class NavigationUpdate(BaseModel):
    label_zh: str = Field(min_length=1, max_length=80)
    label_en: str = Field(min_length=1, max_length=80)
    sort_order: int = Field(ge=0, le=10000)
    enabled: bool = True


class JobUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    mode: Literal["atomic_snapshot", "partitioned_incremental"]
    schedule: str | None = Field(default=None, max_length=100)
    timezone: str = Field(default="Asia/Shanghai", min_length=1, max_length=100)
    enabled: bool = True
    retention_success: int = Field(default=3, ge=1, le=100)


class TablePolicyUpdate(BaseModel):
    strategy: Literal["snapshot", "watermark", "append_only", "cdc", "excluded"]
    watermark_column: str | None = Field(default=None, max_length=200)
    partition_column: str | None = Field(default=None, max_length=200)
    batch_rows: int = Field(default=10000, ge=100, le=1000000)
    target_shard_bytes: int = Field(default=67108864, ge=1048576, le=4294967296)
    hot_window_days: int | None = Field(default=None, ge=1, le=36500)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_incremental_cursor(self):
        if self.strategy in {"watermark", "append_only"} and not self.watermark_column:
            raise ValueError("watermark_column is required for watermark and append_only strategies")
        return self


class SettingUpdate(BaseModel):
    value: Any


class PropertyOverrideUpdate(BaseModel):
    physical_table: str = Field(min_length=1, max_length=200)
    physical_column: str | None = Field(default=None, max_length=200)
    mapping_kind: Literal["property", "relationship", "computed", "ignored"] = "property"
    expression: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=2000)


class RelationshipOverrideUpdate(BaseModel):
    source_property: str = Field(min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)


class OntologyActorRequest(BaseModel):
    actor: str = Field(min_length=2, max_length=200)


class OntologyDiscoveryPlanRequest(BaseModel):
    selected_classes: list[str] = Field(default_factory=list, max_length=16)
    dialect: Literal["sqlserver", "oracle"] = "sqlserver"


class PublishClassCreate(BaseModel):
    source_class: str | None = Field(default=None, max_length=200)
    target_name: str = Field(min_length=1, max_length=200)
    label: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    role: Literal["core", "context", "reference", "on_demand", "excluded"] = "context"
    orphan_policy: Literal["reject", "quarantine", "allow", "referenced_only"] = "quarantine"


class PublishClassUpdate(BaseModel):
    targetName: str = Field(min_length=1, max_length=200)
    label: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    role: Literal["core", "context", "reference", "on_demand", "excluded"] = "context"
    orphanPolicy: Literal["reject", "quarantine", "allow", "referenced_only"] = "quarantine"


class PublishPresentationUpdate(BaseModel):
    labelMode: Literal["auto", "field", "template"] = "auto"
    labelField: str | None = Field(default=None, max_length=300)
    labelTemplate: str | None = Field(default=None, max_length=500)
    labelFallbacks: list[str] = Field(default_factory=list, max_length=12)
    searchFields: list[str] = Field(default_factory=list, max_length=24)
    emitRdfsLabel: bool = True


class PublishPropertyUpdate(BaseModel):
    uid: str | None = Field(default=None, max_length=600)
    propertyKey: str | None = Field(default=None, max_length=300)
    sourceName: str | None = Field(default=None, max_length=300)
    targetName: str = Field(min_length=1, max_length=300)
    sourcePath: str | None = Field(default=None, max_length=1000)
    dataType: str = Field(default="String", min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=4000)
    required: bool = False
    published: bool = True
    origin: Literal["source", "custom", "projection"] = "custom"


class PublishRelationshipUpdate(BaseModel):
    relationshipKey: str | None = Field(default=None, max_length=300)
    sourceUid: str = Field(min_length=1, max_length=600)
    targetUid: str = Field(min_length=1, max_length=600)
    sourceRelationship: str | None = Field(default=None, max_length=300)
    targetName: str = Field(min_length=1, max_length=300)
    usage: Literal["published_link", "projection_only", "context_only", "excluded"] = "published_link"
    strength: Literal["core", "context", "weak", "on_demand"] = "context"
    cardinality: str = Field(default="many-to-one", max_length=100)
    requiredContext: bool = False
    questionEnabled: bool = True
    description: str | None = Field(default=None, max_length=4000)


class RelationshipSuggestionApply(BaseModel):
    classUid: str = Field(min_length=1, max_length=600)
    suggestionIds: list[str] = Field(min_length=1, max_length=12)


class GraphProfileUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    enabled: bool = True
    max_depth: int = Field(default=2, ge=0, le=8)
    max_context_nodes_per_seed: int = Field(default=200, ge=1, le=100000)
    max_total_nodes_per_run: int = Field(default=1000000, ge=1, le=1000000000)


class ProfileClassUpdate(BaseModel):
    role: Literal["core", "context", "reference", "on_demand", "excluded"]
    orphan_policy: Literal["reject", "quarantine", "allow", "referenced_only"] = "quarantine"
    seed_enabled: bool = False
    max_instances_per_run: int | None = Field(default=None, ge=1, le=1000000000)
    priority: int = Field(default=100, ge=0, le=10000)
    enabled: bool = True
    review_status: Literal["draft", "reviewed", "approved"] = "draft"

    @model_validator(mode="after")
    def validate_seed_role(self):
        if self.seed_enabled and self.role != "core":
            raise ValueError("Only a core class may be used as a context seed")
        return self


class ProfileRelationshipUpdate(BaseModel):
    strength: Literal["core", "context", "weak", "on_demand"]
    required_context: bool = False
    traverse: bool = False
    direction: Literal["outgoing", "incoming", "both"] = "outgoing"
    max_depth: int | None = Field(default=None, ge=1, le=8)
    max_targets_per_source: int = Field(default=50, ge=1, le=100000)
    enabled: bool = True
    review_status: Literal["draft", "reviewed", "approved"] = "draft"

    @model_validator(mode="after")
    def validate_traversal_strength(self):
        if self.strength == "weak" and self.traverse:
            raise ValueError("Weak relationships cannot drive context traversal")
        if self.required_context and self.strength not in {"core", "context"}:
            raise ValueError("Required context must use a core or context relationship")
        return self


class DataContractUpdate(BaseModel):
    status: Literal["draft", "reviewed", "approved", "retired"] = "draft"
    business_key_columns: list[str] = Field(default_factory=list, max_length=20)
    required_columns: list[str] = Field(default_factory=list, max_length=100)
    freshness_column: str | None = Field(default=None, max_length=200)
    preview_row_limit: int = Field(default=100000, ge=1, le=1000000)
    publication_layer: Literal["core", "context", "reference", "quarantine"] = "core"


class DataContractCreate(BaseModel):
    class_name: str = Field(min_length=1, max_length=200)
    primary_key_columns: list[str] = Field(min_length=1, max_length=10)
    business_key_columns: list[str] = Field(default_factory=list, max_length=20)
    selected_columns: list[str] = Field(min_length=1, max_length=1000)
    required_columns: list[str] = Field(default_factory=list, max_length=100)
    freshness_column: str | None = Field(default=None, max_length=200)
    preview_row_limit: int = Field(default=100000, ge=1, le=1000000)
    publication_layer: Literal["core", "context", "reference", "quarantine"] = "core"


class RelationshipContractUpdate(BaseModel):
    status: Literal["draft", "reviewed", "approved", "retired"] = "draft"
    semantic_role: str = Field(min_length=1, max_length=200)
    required_context: bool = False


class RelationshipContractCreate(BaseModel):
    source_class: str = Field(min_length=1, max_length=200)
    relationship_name: str = Field(min_length=1, max_length=300)
    target_class: str = Field(min_length=1, max_length=200)
    semantic_role: str = Field(min_length=1, max_length=200)
    required_context: bool = False


class SchemaChangeOperation(BaseModel):
    operation: Literal[
        "add_field", "deprecate_field", "retire_field", "rename_field",
        "change_type", "change_required", "change_key", "change_source",
        "change_transform",
    ]
    field_key: str = Field(min_length=1, max_length=300)
    after_state: dict[str, Any] | None = None
    notes: str | None = Field(default=None, max_length=2000)


class SchemaChangeCreate(BaseModel):
    contract_key: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    migration_strategy: str | None = Field(default=None, max_length=8000)
    rollback_strategy: str | None = Field(default=None, max_length=8000)
    requested_by: str | None = Field(default=None, max_length=200)
    operations: list[SchemaChangeOperation] = Field(min_length=1, max_length=100)


class SchemaChangeReview(BaseModel):
    status: Literal["reviewed", "approved", "rejected"]
    actor: str | None = Field(default=None, max_length=200)


class AttributeProjectionFieldInput(BaseModel):
    field_key: str = Field(min_length=1, max_length=300)
    source_path: str = Field(min_length=3, max_length=400)
    target_field: str = Field(min_length=1, max_length=200)
    data_type: Literal["String", "Integer", "Float", "Boolean", "DateTime", "Date", "Navigation"] = "String"
    required: bool = False
    ontology_property: str | None = Field(default=None, max_length=500)
    lifecycle_status: Literal["active", "deprecated", "retired"] = "active"
    ordinal_position: int = Field(default=10, ge=0, le=100000)
    config: dict[str, Any] = Field(default_factory=dict)


class AttributeProjectionUpdate(BaseModel):
    target_contract_key: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    source_schema: str = Field(min_length=1, max_length=200)
    source_table: str = Field(min_length=1, max_length=200)
    source_alias: str = Field(default="src", min_length=1, max_length=80)
    owner_mapping: list[dict[str, Any]] = Field(min_length=1, max_length=20)
    join_plan: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    row_filters: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    cardinality: Literal["one", "many"] = "one"
    multiple_match_policy: Literal["reject", "first", "latest", "array"] = "reject"
    missing_policy: Literal["null", "quarantine", "reject"] = "null"
    collision_policy: Literal["reject", "overwrite", "coalesce"] = "reject"
    order_by: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    preview_row_limit: int = Field(default=200, ge=1, le=10000)
    enabled: bool = True
    fields: list[AttributeProjectionFieldInput] = Field(min_length=1, max_length=200)
    config: dict[str, Any] = Field(default_factory=dict)


class AttributeProjectionReview(BaseModel):
    status: Literal["reviewed", "approved", "retired"]
    actor: str | None = Field(default=None, max_length=200)


class MaterializationRequest(BaseModel):
    apply: bool = False
    activate: bool = False
    actor: str | None = Field(default=None, max_length=200)


class ContinuousSyncRequest(BaseModel):
    apply: bool = False
    profile_key: str = Field(default="opcenter2607-core", min_length=1, max_length=200)
    environment_key: Literal["dev", "uat", "prod"] = "dev"
    route_key: str | None = Field(default=None, max_length=300)
    actor: str | None = Field(default="local-console", max_length=200)


class DataSyncRequest(BaseModel):
    actor: str = Field(default="local-console", min_length=2, max_length=200)


class DataSyncScheduleRequest(BaseModel):
    enabled: bool
    interval_minutes: int = Field(default=15, ge=1, le=10080)
    max_attempts: int = Field(default=3, ge=1, le=10)
    retry_backoff_seconds: int = Field(default=60, ge=5, le=86400)


class ReleaseActivation(BaseModel):
    actor: str | None = Field(default=None, max_length=200)


class DeploymentCreate(BaseModel):
    environment_key: Literal["dev", "uat", "prod"] = "dev"
    route_key: str | None = Field(default=None, max_length=300)
    release_id: uuid.UUID | None = None
    actor: str | None = Field(default=None, max_length=200)


class DeploymentEnvironmentUpdate(BaseModel):
    apply_enabled: bool


class GraphStudioTargetUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    graphmart_uri: str = Field(min_length=1, max_length=1000)
    connection_key: str = Field(default="graph-studio", min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class PublicationRouteUpdate(BaseModel):
    profile_key: str = Field(min_length=1, max_length=200)
    environment_key: Literal["dev", "uat", "prod"]
    target_key: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=300)
    promotion_order: int = Field(ge=1, le=10000)
    apply_enabled: bool = False
    requires_approval: bool = True
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class ActorRequest(BaseModel):
    actor: str | None = Field(default=None, max_length=200)


class ActionPlanRequest(BaseModel):
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=8, max_length=300)
    dry_run: bool = True


class ActionDefinitionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    object_class: str = Field(min_length=1, max_length=200)
    endpoint_path: str = Field(min_length=1, max_length=1000)
    http_method: Literal["POST", "PUT", "PATCH", "DELETE"]
    input_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    allowed_roles: list[str] = Field(min_length=1, max_length=100)
    approval_required: bool = True
    timeout_seconds: int = Field(default=60, ge=1, le=600)
    retry_policy: dict[str, Any] = Field(default_factory=lambda: {"maxAttempts": 1})
    compensation_action_key: str | None = Field(default=None, max_length=300)
    config: dict[str, Any] = Field(default_factory=dict)


class ActionDefinitionReview(BaseModel):
    status: Literal["reviewed", "approved", "retired"]


class OpenApiActionImport(BaseModel):
    source_file: str = Field(min_length=6, max_length=300)
    operation_id: str = Field(min_length=1, max_length=1000)


class ActionCompensationRequest(BaseModel):
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=8, max_length=300)


class SyncClassConfiguration(BaseModel):
    mode: Literal["data", "model_only"]
    selected_columns: list[str] = Field(default_factory=list, max_length=2000)
    fingerprint: str = Field(min_length=64, max_length=64)
    actor: str = Field(min_length=1, max_length=200)

