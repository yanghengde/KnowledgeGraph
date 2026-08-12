-- Camstar -> Graph Studio control plane.
-- This schema stores orchestration metadata only; source business data remains
-- in the Camstar SQL Server/Oracle source and published RDF remains in Graph Studio.

CREATE SCHEMA IF NOT EXISTS graphsync;
CREATE SCHEMA IF NOT EXISTS camstar_curated;

CREATE TABLE IF NOT EXISTS graphsync.schema_version (
    version         integer PRIMARY KEY,
    description     text NOT NULL,
    installed_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graphsync.connection_profile (
    connection_key  text PRIMARY KEY,
    kind            text NOT NULL CHECK (kind IN (
                        'camstar_sqlserver', 'camstar_oracle', 'ontology_neo4j',
                        'graph_studio', 'state_postgresql'
                    )),
    display_name    text NOT NULL,
    endpoint        text NOT NULL,
    database_name   text,
    username        text,
    secret_ref      text NOT NULL,
    enabled         boolean NOT NULL DEFAULT true,
    status          text NOT NULL DEFAULT 'unknown' CHECK (status IN (
                        'unknown', 'online', 'degraded', 'offline', 'disabled'
                    )),
    last_tested_at  timestamptz,
    last_error      text,
    config          jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- Existing installations need the expanded source-engine constraint as well.
ALTER TABLE graphsync.connection_profile
    DROP CONSTRAINT IF EXISTS connection_profile_kind_check;
ALTER TABLE graphsync.connection_profile
    ADD CONSTRAINT connection_profile_kind_check CHECK (kind IN (
        'camstar_sqlserver', 'camstar_oracle', 'ontology_neo4j',
        'graph_studio', 'state_postgresql'
    ));

CREATE TABLE IF NOT EXISTS graphsync.menu_item (
    menu_key        text PRIMARY KEY,
    parent_key      text REFERENCES graphsync.menu_item(menu_key) ON DELETE SET NULL,
    label_zh        text NOT NULL,
    label_en        text NOT NULL,
    route           text NOT NULL,
    icon            text NOT NULL DEFAULT 'circle',
    sort_order      integer NOT NULL DEFAULT 100,
    enabled         boolean NOT NULL DEFAULT true,
    capability      text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graphsync.sync_job (
    job_name              text PRIMARY KEY,
    title                 text NOT NULL,
    description           text,
    graphmart_uri         text NOT NULL,
    mode                  text NOT NULL CHECK (mode IN (
                              'atomic_snapshot', 'partitioned_incremental'
                          )),
    schedule              text,
    timezone              text NOT NULL DEFAULT 'Asia/Shanghai',
    enabled               boolean NOT NULL DEFAULT true,
    retention_success     integer NOT NULL DEFAULT 3 CHECK (retention_success >= 1),
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graphsync.sync_scope (
    job_name        text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    scope_key       text NOT NULL,
    class_pattern   text NOT NULL DEFAULT '*',
    layer_title     text,
    enabled         boolean NOT NULL DEFAULT true,
    sort_order      integer NOT NULL DEFAULT 100,
    config          jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (job_name, scope_key)
);

CREATE TABLE IF NOT EXISTS graphsync.sync_run (
    run_id                uuid PRIMARY KEY,
    job_name              text NOT NULL REFERENCES graphsync.sync_job(job_name),
    status                text NOT NULL CHECK (status IN (
                              'queued', 'started', 'extracting', 'staged', 'loading',
                              'verifying', 'succeeded', 'failed', 'cancelled'
                          )),
    trigger_type          text NOT NULL DEFAULT 'scheduled' CHECK (trigger_type IN (
                              'scheduled', 'manual', 'recovery', 'dry_run'
                          )),
    started_at            timestamptz NOT NULL DEFAULT now(),
    finished_at           timestamptz,
    source_high_watermark jsonb,
    ontology_hash         text,
    source_schema_hash    text,
    manifest_hash         text,
    row_count             bigint NOT NULL DEFAULT 0,
    triple_count          bigint NOT NULL DEFAULT 0,
    error                 jsonb,
    metrics               jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_graphsync_run_job_started
    ON graphsync.sync_run (job_name, started_at DESC);
CREATE INDEX IF NOT EXISTS ix_graphsync_run_status
    ON graphsync.sync_run (status, started_at DESC);

CREATE TABLE IF NOT EXISTS graphsync.checkpoint (
    job_name              text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    partition_key         text NOT NULL,
    committed_watermark   jsonb NOT NULL,
    source_schema_hash    text,
    committed_run_id      uuid NOT NULL REFERENCES graphsync.sync_run(run_id),
    committed_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (job_name, partition_key)
);

CREATE TABLE IF NOT EXISTS graphsync.table_sync_policy (
    job_name              text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    class_name            text NOT NULL,
    physical_schema       text NOT NULL,
    physical_table        text NOT NULL,
    strategy              text NOT NULL CHECK (strategy IN (
                              'snapshot', 'watermark', 'append_only', 'cdc', 'excluded'
                          )),
    watermark_column      text,
    partition_column      text,
    batch_rows            integer NOT NULL DEFAULT 10000 CHECK (
                              batch_rows BETWEEN 100 AND 1000000
                          ),
    target_shard_bytes    bigint NOT NULL DEFAULT 67108864 CHECK (
                              target_shard_bytes BETWEEN 1048576 AND 4294967296
                          ),
    hot_window_days       integer CHECK (hot_window_days IS NULL OR hot_window_days > 0),
    enabled               boolean NOT NULL DEFAULT true,
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (job_name, class_name)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_table_policy_strategy
    ON graphsync.table_sync_policy (job_name, strategy, enabled);

CREATE TABLE IF NOT EXISTS graphsync.sync_batch (
    batch_id              uuid PRIMARY KEY,
    run_id                uuid NOT NULL REFERENCES graphsync.sync_run(run_id) ON DELETE CASCADE,
    job_name              text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    class_name            text NOT NULL,
    partition_key         text NOT NULL,
    sequence_no           integer NOT NULL,
    status                text NOT NULL CHECK (status IN (
                              'queued', 'extracting', 'staged', 'loading',
                              'verified', 'failed', 'cancelled'
                          )),
    source_from           jsonb,
    source_to             jsonb,
    row_count             bigint NOT NULL DEFAULT 0,
    triple_count          bigint NOT NULL DEFAULT 0,
    byte_size             bigint NOT NULL DEFAULT 0,
    sha256                text,
    storage_path          text,
    attempt_count         integer NOT NULL DEFAULT 0,
    error                 jsonb,
    started_at            timestamptz,
    finished_at           timestamptz,
    UNIQUE (run_id, class_name, partition_key, sequence_no)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_batch_run_status
    ON graphsync.sync_batch (run_id, status, class_name, sequence_no);

CREATE TABLE IF NOT EXISTS graphsync.source_capability_snapshot (
    snapshot_id           uuid PRIMARY KEY,
    connection_key        text NOT NULL REFERENCES graphsync.connection_profile(connection_key),
    source_kind           text NOT NULL,
    captured_at           timestamptz NOT NULL DEFAULT now(),
    source_position       jsonb NOT NULL DEFAULT '{}'::jsonb,
    capabilities          jsonb NOT NULL DEFAULT '{}'::jsonb,
    table_capabilities    jsonb NOT NULL DEFAULT '[]'::jsonb,
    success               boolean NOT NULL DEFAULT true,
    error                 jsonb
);

CREATE INDEX IF NOT EXISTS ix_graphsync_capability_connection_captured
    ON graphsync.source_capability_snapshot (connection_key, captured_at DESC);

CREATE TABLE IF NOT EXISTS graphsync.incremental_window (
    window_id             uuid PRIMARY KEY,
    job_name              text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    class_name            text NOT NULL,
    strategy              text NOT NULL CHECK (strategy IN (
                              'watermark', 'append_only', 'cdc'
                          )),
    adapter               text NOT NULL,
    status                text NOT NULL CHECK (status IN (
                              'planned', 'baseline_required', 'blocked', 'extracting',
                              'staged', 'verified', 'committed', 'failed', 'abandoned'
                          )),
    lower_bound           jsonb,
    upper_bound           jsonb NOT NULL,
    capability_snapshot_id uuid REFERENCES graphsync.source_capability_snapshot(snapshot_id),
    run_id                uuid REFERENCES graphsync.sync_run(run_id) ON DELETE SET NULL,
    row_count             bigint NOT NULL DEFAULT 0,
    tombstone_count       bigint NOT NULL DEFAULT 0,
    error                 jsonb,
    metadata              jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    UNIQUE (job_name, class_name, upper_bound)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_incremental_window_status
    ON graphsync.incremental_window (job_name, status, class_name, created_at DESC);

CREATE TABLE IF NOT EXISTS graphsync.artifact (
    artifact_id           uuid PRIMARY KEY,
    run_id                uuid NOT NULL REFERENCES graphsync.sync_run(run_id) ON DELETE CASCADE,
    artifact_type         text NOT NULL CHECK (artifact_type IN (
                              'manifest', 'rdf_archive', 'model', 'dataset',
                              'layer', 'step', 'verification'
                          )),
    uri                   text,
    storage_path          text,
    sha256                text,
    byte_size             bigint,
    active                boolean NOT NULL DEFAULT false,
    metadata              jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_graphsync_artifact_run_type
    ON graphsync.artifact (run_id, artifact_type);

CREATE TABLE IF NOT EXISTS graphsync.mapping_override (
    class_name       text NOT NULL,
    property_name    text NOT NULL,
    physical_schema  text,
    physical_table   text NOT NULL,
    physical_column  text,
    target_class     text,
    mapping_kind     text NOT NULL DEFAULT 'property' CHECK (mapping_kind IN (
                         'property', 'relationship', 'computed', 'ignored'
                     )),
    expression       text,
    enabled          boolean NOT NULL DEFAULT true,
    notes            text,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (class_name, property_name)
);

CREATE TABLE IF NOT EXISTS graphsync.catalog_snapshot (
    snapshot_id             uuid PRIMARY KEY,
    status                  text NOT NULL CHECK (status IN ('compiling', 'ready', 'failed')),
    started_at              timestamptz NOT NULL DEFAULT now(),
    finished_at             timestamptz,
    ontology_class_count    integer NOT NULL DEFAULT 0,
    ontology_property_count integer NOT NULL DEFAULT 0,
    relationship_count      integer NOT NULL DEFAULT 0,
    physical_table_count    integer NOT NULL DEFAULT 0,
    approximate_row_count   bigint NOT NULL DEFAULT 0,
    mapping_coverage        numeric(6,3),
    catalog_hash            text,
    error                   jsonb
);

CREATE TABLE IF NOT EXISTS graphsync.class_mapping (
    snapshot_id        uuid NOT NULL REFERENCES graphsync.catalog_snapshot(snapshot_id) ON DELETE CASCADE,
    class_name         text NOT NULL,
    chinese_name       text,
    ontology_layer     text,
    source_workspace   text,
    source_cdo_def_id  text,
    physical_schema    text,
    physical_table     text,
    approximate_rows   bigint NOT NULL DEFAULT 0,
    mapping_status     text NOT NULL CHECK (mapping_status IN ('resolved', 'unresolved', 'ignored')),
    PRIMARY KEY (snapshot_id, class_name)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_class_mapping_name
    ON graphsync.class_mapping (class_name, snapshot_id);

CREATE TABLE IF NOT EXISTS graphsync.property_mapping (
    snapshot_id        uuid NOT NULL REFERENCES graphsync.catalog_snapshot(snapshot_id) ON DELETE CASCADE,
    class_name         text NOT NULL,
    property_name      text NOT NULL,
    data_type          text,
    required           boolean NOT NULL DEFAULT false,
    source_field_id    text,
    physical_schema    text,
    physical_table     text,
    physical_column    text,
    fk_table_name      text,
    fk_field_name      text,
    mapping_status     text NOT NULL CHECK (mapping_status IN (
                           'resolved', 'override', 'computed', 'ignored', 'unresolved'
                       )),
    resolution_method  text,
    PRIMARY KEY (snapshot_id, class_name, property_name),
    FOREIGN KEY (snapshot_id, class_name)
        REFERENCES graphsync.class_mapping(snapshot_id, class_name) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_graphsync_property_mapping_status
    ON graphsync.property_mapping (snapshot_id, mapping_status);

CREATE TABLE IF NOT EXISTS graphsync.relationship_mapping (
    snapshot_id        uuid NOT NULL REFERENCES graphsync.catalog_snapshot(snapshot_id) ON DELETE CASCADE,
    source_class       text NOT NULL,
    relationship_name text NOT NULL,
    target_class       text NOT NULL,
    cardinality        text,
    source_property    text,
    source_field_id    text,
    physical_column    text,
    candidate_properties jsonb NOT NULL DEFAULT '[]'::jsonb,
    mapping_status     text NOT NULL CHECK (mapping_status IN (
                           'resolved', 'ambiguous', 'semantic_only', 'unresolved'
                       )),
    candidate_count    integer NOT NULL DEFAULT 0,
    resolution_method  text,
    PRIMARY KEY (snapshot_id, source_class, relationship_name, target_class)
);

ALTER TABLE graphsync.relationship_mapping
    ADD COLUMN IF NOT EXISTS candidate_properties jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE graphsync.relationship_mapping
    ADD COLUMN IF NOT EXISTS resolution_method text;

CREATE INDEX IF NOT EXISTS ix_graphsync_relationship_mapping_status
    ON graphsync.relationship_mapping (snapshot_id, mapping_status);

CREATE TABLE IF NOT EXISTS graphsync.relationship_override (
    source_class       text NOT NULL,
    relationship_name text NOT NULL,
    target_class       text NOT NULL,
    source_property    text NOT NULL,
    enabled            boolean NOT NULL DEFAULT true,
    notes              text,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source_class, relationship_name, target_class)
);

CREATE TABLE IF NOT EXISTS graphsync.validation_result (
    validation_id    uuid PRIMARY KEY,
    run_id           uuid REFERENCES graphsync.sync_run(run_id) ON DELETE CASCADE,
    phase            text NOT NULL,
    rule_key         text NOT NULL,
    severity         text NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
    passed           boolean NOT NULL,
    message          text NOT NULL,
    details          jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_graphsync_validation_run
    ON graphsync.validation_result (run_id, severity, passed);

CREATE TABLE IF NOT EXISTS graphsync.row_state (
    job_name              text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    partition_key         text NOT NULL,
    entity_uri            text NOT NULL,
    row_hash              text NOT NULL,
    last_seen_run_id      uuid NOT NULL REFERENCES graphsync.sync_run(run_id),
    last_seen_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (job_name, partition_key, entity_uri)
);

CREATE TABLE IF NOT EXISTS graphsync.app_setting (
    setting_key      text PRIMARY KEY,
    value            jsonb NOT NULL,
    description      text,
    editable         boolean NOT NULL DEFAULT true,
    updated_at       timestamptz NOT NULL DEFAULT now()
);

-- Business graph profiles deliberately separate the complete ontology from the
-- bounded instance graph that is useful to operations.  Physical mappings remain
-- facts; these rows record business intent and may therefore be reviewed safely.
CREATE TABLE IF NOT EXISTS graphsync.graph_profile (
    profile_key                 text PRIMARY KEY,
    title                       text NOT NULL,
    description                 text,
    job_name                    text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    enabled                     boolean NOT NULL DEFAULT true,
    max_depth                   integer NOT NULL DEFAULT 2 CHECK (max_depth BETWEEN 0 AND 8),
    max_context_nodes_per_seed  integer NOT NULL DEFAULT 200 CHECK (max_context_nodes_per_seed BETWEEN 1 AND 100000),
    max_total_nodes_per_run     bigint NOT NULL DEFAULT 1000000 CHECK (max_total_nodes_per_run BETWEEN 1 AND 1000000000),
    config                      jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    updated_at                  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graphsync.profile_class (
    profile_key          text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    class_name           text NOT NULL,
    role                 text NOT NULL CHECK (role IN (
                             'core', 'context', 'reference', 'on_demand', 'excluded'
                         )),
    orphan_policy        text NOT NULL DEFAULT 'quarantine' CHECK (orphan_policy IN (
                             'reject', 'quarantine', 'allow', 'referenced_only'
                         )),
    seed_enabled         boolean NOT NULL DEFAULT false,
    max_instances_per_run bigint CHECK (max_instances_per_run IS NULL OR max_instances_per_run > 0),
    priority             integer NOT NULL DEFAULT 100,
    enabled              boolean NOT NULL DEFAULT true,
    review_status        text NOT NULL DEFAULT 'draft' CHECK (review_status IN (
                             'draft', 'reviewed', 'approved'
                         )),
    config               jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (profile_key, class_name),
    CHECK (NOT seed_enabled OR role = 'core')
);

CREATE INDEX IF NOT EXISTS ix_graphsync_profile_class_role
    ON graphsync.profile_class (profile_key, role, enabled, priority);

CREATE TABLE IF NOT EXISTS graphsync.profile_relationship (
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    source_class          text NOT NULL,
    relationship_name     text NOT NULL,
    target_class          text NOT NULL,
    strength              text NOT NULL CHECK (strength IN (
                              'core', 'context', 'weak', 'on_demand'
                          )),
    required_context      boolean NOT NULL DEFAULT false,
    traverse              boolean NOT NULL DEFAULT false,
    direction             text NOT NULL DEFAULT 'outgoing' CHECK (direction IN (
                              'outgoing', 'incoming', 'both'
                          )),
    max_depth             integer CHECK (max_depth IS NULL OR max_depth BETWEEN 1 AND 8),
    max_targets_per_source integer NOT NULL DEFAULT 50 CHECK (max_targets_per_source BETWEEN 1 AND 100000),
    enabled               boolean NOT NULL DEFAULT true,
    review_status         text NOT NULL DEFAULT 'draft' CHECK (review_status IN (
                              'draft', 'reviewed', 'approved'
                          )),
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (profile_key, source_class, relationship_name, target_class),
    CHECK (strength <> 'weak' OR NOT traverse),
    CHECK (NOT required_context OR strength IN ('core', 'context'))
);

CREATE INDEX IF NOT EXISTS ix_graphsync_profile_relationship_traversal
    ON graphsync.profile_relationship (profile_key, traverse, strength, enabled);

CREATE TABLE IF NOT EXISTS graphsync.context_validation (
    validation_id        uuid PRIMARY KEY,
    profile_key          text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    run_id               uuid REFERENCES graphsync.sync_run(run_id) ON DELETE CASCADE,
    class_name           text,
    entity_uri           text,
    rule_key             text NOT NULL,
    severity             text NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
    status               text NOT NULL CHECK (status IN ('open', 'resolved', 'ignored')),
    message              text NOT NULL,
    details              jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at           timestamptz NOT NULL DEFAULT now(),
    resolved_at          timestamptz
);

CREATE INDEX IF NOT EXISTS ix_graphsync_context_validation_open
    ON graphsync.context_validation (profile_key, status, severity, created_at DESC);

CREATE TABLE IF NOT EXISTS graphsync.pending_reference (
    profile_key          text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    source_entity_uri    text NOT NULL,
    relationship_name   text NOT NULL,
    target_entity_key    text NOT NULL,
    target_class         text NOT NULL,
    first_seen_at        timestamptz NOT NULL DEFAULT now(),
    last_seen_at         timestamptz NOT NULL DEFAULT now(),
    attempt_count        integer NOT NULL DEFAULT 0,
    status               text NOT NULL DEFAULT 'pending' CHECK (status IN (
                             'pending', 'resolved', 'quarantined', 'expired'
                         )),
    details              jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (profile_key, source_entity_uri, relationship_name, target_entity_key)
);

CREATE TABLE IF NOT EXISTS graphsync.data_contract (
    contract_key          text PRIMARY KEY,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    class_name            text NOT NULL,
    version               integer NOT NULL DEFAULT 1 CHECK (version > 0),
    status                text NOT NULL DEFAULT 'draft' CHECK (status IN (
                             'draft', 'reviewed', 'approved', 'retired'
                         )),
    source_schema         text NOT NULL,
    source_table          text NOT NULL,
    primary_key_columns   jsonb NOT NULL,
    business_key_columns  jsonb NOT NULL DEFAULT '[]'::jsonb,
    selected_columns      jsonb NOT NULL,
    required_columns      jsonb NOT NULL DEFAULT '[]'::jsonb,
    freshness_column      text,
    preview_row_limit     integer NOT NULL DEFAULT 100000 CHECK (
                             preview_row_limit BETWEEN 1 AND 1000000
                         ),
    publication_layer     text NOT NULL DEFAULT 'core' CHECK (publication_layer IN (
                             'core', 'context', 'reference', 'quarantine'
                         )),
    quality_thresholds    jsonb NOT NULL DEFAULT '{}'::jsonb,
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    UNIQUE (profile_key, class_name),
    CHECK (jsonb_typeof(primary_key_columns) = 'array'),
    CHECK (jsonb_array_length(primary_key_columns) > 0),
    CHECK (jsonb_typeof(selected_columns) = 'array')
);

CREATE TABLE IF NOT EXISTS graphsync.relationship_contract (
    relationship_contract_key text PRIMARY KEY,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    version               integer NOT NULL DEFAULT 1 CHECK (version > 0),
    source_contract_key   text NOT NULL REFERENCES graphsync.data_contract(contract_key) ON DELETE CASCADE,
    relationship_name     text NOT NULL,
    target_contract_key   text NOT NULL REFERENCES graphsync.data_contract(contract_key) ON DELETE CASCADE,
    source_columns        jsonb NOT NULL,
    target_columns        jsonb NOT NULL,
    semantic_role         text NOT NULL,
    required_context      boolean NOT NULL DEFAULT false,
    status                text NOT NULL DEFAULT 'draft' CHECK (status IN (
                              'draft', 'reviewed', 'approved', 'retired'
                          )),
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    CHECK (jsonb_typeof(source_columns) = 'array'),
    CHECK (jsonb_typeof(target_columns) = 'array'),
    CHECK (jsonb_array_length(source_columns) > 0),
    CHECK (jsonb_array_length(source_columns) = jsonb_array_length(target_columns))
);

ALTER TABLE graphsync.relationship_contract
    ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 1;

CREATE TABLE IF NOT EXISTS graphsync.curation_run (
    curation_run_id       uuid PRIMARY KEY,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key),
    status                text NOT NULL CHECK (status IN (
                              'started', 'succeeded', 'failed', 'cancelled'
                          )),
    preview_only          boolean NOT NULL DEFAULT true,
    started_at            timestamptz NOT NULL DEFAULT now(),
    finished_at           timestamptz,
    source_rows_read      bigint NOT NULL DEFAULT 0,
    accepted_rows         bigint NOT NULL DEFAULT 0,
    quarantined_rows      bigint NOT NULL DEFAULT 0,
    publishable           boolean NOT NULL DEFAULT false,
    contract_versions     jsonb NOT NULL DEFAULT '{}'::jsonb,
    summary               jsonb NOT NULL DEFAULT '{}'::jsonb,
    error                 jsonb
);

CREATE INDEX IF NOT EXISTS ix_graphsync_curation_run_profile
    ON graphsync.curation_run (profile_key, started_at DESC);

CREATE TABLE IF NOT EXISTS graphsync.data_quality_result (
    quality_result_id     uuid PRIMARY KEY,
    curation_run_id       uuid NOT NULL REFERENCES graphsync.curation_run(curation_run_id) ON DELETE CASCADE,
    contract_key          text REFERENCES graphsync.data_contract(contract_key) ON DELETE SET NULL,
    relationship_contract_key text REFERENCES graphsync.relationship_contract(relationship_contract_key) ON DELETE SET NULL,
    rule_key              text NOT NULL,
    severity              text NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
    passed                boolean NOT NULL,
    checked_rows          bigint NOT NULL DEFAULT 0,
    failed_rows           bigint NOT NULL DEFAULT 0,
    message               text NOT NULL,
    details               jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_graphsync_quality_run
    ON graphsync.data_quality_result (curation_run_id, severity, passed);

-- Curated tables contain only governance-approved projections. The initial
-- implementation creates the contract-shaped targets but preview runs do not
-- write business rows into them.
CREATE TABLE IF NOT EXISTS camstar_curated.product (
    source_product_id     text PRIMARY KEY,
    product_base_id       text,
    revision              text,
    description           text,
    status                integer,
    object_type           text,
    workflow_id           text,
    product_type_id       text,
    change_count          bigint,
    source_payload        jsonb NOT NULL DEFAULT '{}'::jsonb,
    source_hash           text NOT NULL,
    source_change_at      timestamptz,
    curated_at            timestamptz NOT NULL DEFAULT now(),
    curation_run_id       uuid NOT NULL REFERENCES graphsync.curation_run(curation_run_id)
);

CREATE TABLE IF NOT EXISTS camstar_curated.mfg_order (
    source_mfg_order_id   text PRIMARY KEY,
    order_name            text NOT NULL,
    description           text,
    ordered_product_id    text,
    begin_product_id      text,
    quantity              numeric,
    order_status_id       text,
    reporting_factory_id  text,
    planned_start_at      timestamptz,
    planned_completion_at timestamptz,
    last_change_at        timestamptz,
    change_count          bigint,
    source_payload        jsonb NOT NULL DEFAULT '{}'::jsonb,
    source_hash           text NOT NULL,
    curated_at            timestamptz NOT NULL DEFAULT now(),
    curation_run_id       uuid NOT NULL REFERENCES graphsync.curation_run(curation_run_id)
);

CREATE INDEX IF NOT EXISTS ix_curated_mfg_order_product
    ON camstar_curated.mfg_order (ordered_product_id);

CREATE TABLE IF NOT EXISTS camstar_curated.mfg_order_product_link (
    source_mfg_order_id   text NOT NULL,
    relationship_name    text NOT NULL CHECK (relationship_name IN (
                             'ORDERED_PRODUCT', 'BEGIN_PRODUCT'
                         )),
    source_product_id     text NOT NULL,
    resolution_status    text NOT NULL CHECK (resolution_status IN (
                             'resolved', 'pending', 'quarantined'
                         )),
    curated_at            timestamptz NOT NULL DEFAULT now(),
    curation_run_id       uuid NOT NULL REFERENCES graphsync.curation_run(curation_run_id),
    PRIMARY KEY (source_mfg_order_id, relationship_name)
);

CREATE INDEX IF NOT EXISTS ix_curated_mfg_order_product_target
    ON camstar_curated.mfg_order_product_link (source_product_id, relationship_name);

CREATE TABLE IF NOT EXISTS camstar_curated.quarantine_record (
    quarantine_id        uuid PRIMARY KEY,
    curation_run_id      uuid NOT NULL REFERENCES graphsync.curation_run(curation_run_id) ON DELETE CASCADE,
    contract_key         text NOT NULL REFERENCES graphsync.data_contract(contract_key),
    source_primary_key   jsonb NOT NULL,
    rule_keys            jsonb NOT NULL,
    source_payload       jsonb NOT NULL,
    status               text NOT NULL DEFAULT 'open' CHECK (status IN (
                             'open', 'resolved', 'ignored', 'expired'
                         )),
    created_at           timestamptz NOT NULL DEFAULT now(),
    resolved_at          timestamptz
);

CREATE OR REPLACE FUNCTION graphsync.touch_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_connection_profile_updated ON graphsync.connection_profile;
CREATE TRIGGER trg_connection_profile_updated
BEFORE UPDATE ON graphsync.connection_profile
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_menu_item_updated ON graphsync.menu_item;
CREATE TRIGGER trg_menu_item_updated
BEFORE UPDATE ON graphsync.menu_item
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_sync_job_updated ON graphsync.sync_job;
CREATE TRIGGER trg_sync_job_updated
BEFORE UPDATE ON graphsync.sync_job
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_mapping_override_updated ON graphsync.mapping_override;
CREATE TRIGGER trg_mapping_override_updated
BEFORE UPDATE ON graphsync.mapping_override
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_relationship_override_updated ON graphsync.relationship_override;
CREATE TRIGGER trg_relationship_override_updated
BEFORE UPDATE ON graphsync.relationship_override
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_table_sync_policy_updated ON graphsync.table_sync_policy;
CREATE TRIGGER trg_table_sync_policy_updated
BEFORE UPDATE ON graphsync.table_sync_policy
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_incremental_window_updated ON graphsync.incremental_window;
CREATE TRIGGER trg_incremental_window_updated
BEFORE UPDATE ON graphsync.incremental_window
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_graph_profile_updated ON graphsync.graph_profile;
CREATE TRIGGER trg_graph_profile_updated
BEFORE UPDATE ON graphsync.graph_profile
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_profile_class_updated ON graphsync.profile_class;
CREATE TRIGGER trg_profile_class_updated
BEFORE UPDATE ON graphsync.profile_class
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_profile_relationship_updated ON graphsync.profile_relationship;
CREATE TRIGGER trg_profile_relationship_updated
BEFORE UPDATE ON graphsync.profile_relationship
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_data_contract_updated ON graphsync.data_contract;
CREATE TRIGGER trg_data_contract_updated
BEFORE UPDATE ON graphsync.data_contract
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_relationship_contract_updated ON graphsync.relationship_contract;
CREATE TRIGGER trg_relationship_contract_updated
BEFORE UPDATE ON graphsync.relationship_contract
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

CREATE OR REPLACE VIEW graphsync.latest_job_run AS
SELECT DISTINCT ON (job_name)
       job_name, run_id, status, trigger_type, started_at, finished_at,
       row_count, triple_count, error, metrics
FROM graphsync.sync_run
ORDER BY job_name, started_at DESC;

CREATE OR REPLACE VIEW graphsync.dashboard_summary AS
SELECT
    (SELECT count(*) FROM graphsync.connection_profile WHERE enabled) AS enabled_connections,
    (SELECT count(*) FROM graphsync.connection_profile WHERE status = 'online') AS online_connections,
    (SELECT count(*) FROM graphsync.sync_job WHERE enabled) AS enabled_jobs,
    (SELECT count(*) FROM graphsync.sync_run) AS total_runs,
    (SELECT max(finished_at) FROM graphsync.sync_run
     WHERE status = 'succeeded' AND trigger_type <> 'dry_run') AS last_success_at;

CREATE OR REPLACE VIEW graphsync.current_catalog_snapshot AS
SELECT * FROM graphsync.catalog_snapshot
WHERE status = 'ready'
ORDER BY finished_at DESC
LIMIT 1;

CREATE OR REPLACE VIEW graphsync.current_class_mapping AS
SELECT mapping.*
FROM graphsync.class_mapping mapping
JOIN graphsync.current_catalog_snapshot snapshot USING (snapshot_id);

CREATE OR REPLACE VIEW graphsync.current_property_mapping AS
SELECT mapping.*
FROM graphsync.property_mapping mapping
JOIN graphsync.current_catalog_snapshot snapshot USING (snapshot_id);

CREATE OR REPLACE VIEW graphsync.current_relationship_mapping AS
SELECT mapping.*
FROM graphsync.relationship_mapping mapping
JOIN graphsync.current_catalog_snapshot snapshot USING (snapshot_id);

INSERT INTO graphsync.schema_version (version, description)
VALUES (1, 'Initial Camstar to Graph Studio control plane')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (2, 'Versioned ontology to physical mapping catalog')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (3, 'Mapping review overrides and relationship candidates')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (4, 'SQL Server and Oracle Camstar source profiles')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (5, 'Large-table policies and resumable partition batches')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (6, 'Source capability snapshots and bounded incremental windows')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (7, 'Business graph profiles and controlled context closure')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (8, 'Governed Camstar curated layer and data quality contracts')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.menu_item
    (menu_key, label_zh, label_en, route, icon, sort_order, enabled, capability)
VALUES
    ('overview',    '总览',     'Overview',    '#overview',    'dashboard', 10, true,  'sync.read'),
    ('connections', '连接管理', 'Connections', '#connections', 'plug',      20, true,  'connection.read'),
    ('jobs',        '同步任务', 'Sync Jobs',   '#jobs',        'schedule',  30, true,  'job.read'),
    ('profiles',    '业务图谱', 'Graph Profile','#profiles',    'profile',   35, true,  'profile.write'),
    ('mappings',    '映射管理', 'Mappings',    '#mappings',    'mapping',   40, true,  'mapping.read'),
    ('runs',        '运行记录', 'Runs',        '#runs',        'history',   50, true,  'run.read'),
    ('settings',    '系统设置', 'Settings',    '#settings',    'settings',  60, true,  'setting.write')
ON CONFLICT (menu_key) DO NOTHING;

INSERT INTO graphsync.sync_job
    (job_name, title, description, graphmart_uri, mode, schedule, timezone, enabled, config)
VALUES (
    'camstar-full',
    'Camstar 全量图谱同步',
    '从 Camstar SQL Server 和 Neo4j 本体生成 RDF 快照并发布到 Opcenter2607。',
    'http://cambridgesemantics.com/Graphmart/ba6308d1b3764b8a8ad40d90500ddd56',
    'atomic_snapshot',
    '0 * * * *',
    'Asia/Shanghai',
    true,
    '{"verificationRequired": true, "atomicDatasetSwitch": true}'::jsonb
)
ON CONFLICT (job_name) DO NOTHING;

INSERT INTO graphsync.sync_scope
    (job_name, scope_key, class_pattern, layer_title, enabled, sort_order)
VALUES ('camstar-full', 'all', '*', 'Camstar Full Ontology and Data', true, 10)
ON CONFLICT (job_name, scope_key) DO NOTHING;

INSERT INTO graphsync.graph_profile
    (profile_key, title, description, job_name, max_depth,
     max_context_nodes_per_seed, max_total_nodes_per_run, config)
VALUES (
    'opcenter2607-core',
    'Opcenter2607 核心业务图谱',
    '完整本体、受控实例：从核心对象出发，仅沿审核通过的核心/上下文关系扩展。',
    'camstar-full', 2, 200, 1000000,
    '{"ontologyLayer":"complete","instanceMode":"controlled_context_closure","reviewRequired":true}'::jsonb
)
ON CONFLICT (profile_key) DO NOTHING;

INSERT INTO graphsync.profile_class
    (profile_key, class_name, role, orphan_policy, seed_enabled, priority,
     review_status, config)
VALUES
    ('opcenter2607-core', 'Product',  'core', 'quarantine', true, 10, 'draft',
     '{"reason":"Initial core object requested by user"}'::jsonb),
    ('opcenter2607-core', 'MfgOrder', 'core', 'quarantine', true, 20, 'draft',
     '{"reason":"Initial core object requested by user"}'::jsonb)
ON CONFLICT (profile_key, class_name) DO NOTHING;

INSERT INTO graphsync.data_contract
    (contract_key, profile_key, class_name, source_schema, source_table,
     primary_key_columns, business_key_columns, selected_columns,
     required_columns, freshness_column, publication_layer,
     quality_thresholds, config)
VALUES
    ('opcenter2607-product-v1', 'opcenter2607-core', 'Product',
     'CamstarPRD_SCHEMA', 'Product', '["ProductId"]'::jsonb,
     '["ProductBaseId", "ProductRevision"]'::jsonb,
     '["ProductId", "ProductBaseId", "ProductRevision", "Description", "Status", "ObjectType", "WorkflowId", "ProductTypeId", "ChangeCount"]'::jsonb,
     '["ProductId"]'::jsonb, NULL, 'core',
     '{"maxErrorRate":0,"maxWarningRate":0.05}'::jsonb,
     '{"targetTable":"camstar_curated.product","businessKeyRequiresReview":true}'::jsonb),
    ('opcenter2607-mfgorder-v1', 'opcenter2607-core', 'MfgOrder',
     'CamstarPRD_SCHEMA', 'MfgOrder', '["MfgOrderId"]'::jsonb,
     '["MfgOrderName"]'::jsonb,
     '["MfgOrderId", "MfgOrderName", "Description", "ProductId", "BeginProductId", "Qty", "OrderStatusId", "ReportingFactoryId", "PlannedStartDateGMT", "PlannedCompletionDateGMT", "LastChangeDate", "ChangeCount"]'::jsonb,
     '["MfgOrderId", "MfgOrderName", "ProductId"]'::jsonb,
     'LastChangeDate', 'core',
     '{"maxErrorRate":0,"maxWarningRate":0.05}'::jsonb,
     '{"targetTable":"camstar_curated.mfg_order"}'::jsonb)
ON CONFLICT (contract_key) DO NOTHING;

INSERT INTO graphsync.relationship_contract
    (relationship_contract_key, profile_key, source_contract_key,
     relationship_name, target_contract_key, source_columns, target_columns,
     semantic_role, required_context, status, config)
VALUES
    ('mfgorder-ordered-product-v1', 'opcenter2607-core',
     'opcenter2607-mfgorder-v1', 'ORDERED_PRODUCT', 'opcenter2607-product-v1',
     '["ProductId"]'::jsonb, '["ProductId"]'::jsonb,
     '订单目标产品', true, 'draft',
     '{"ontologyCandidate":"HAS_PRODUCT","requiresBusinessApproval":true}'::jsonb),
    ('mfgorder-begin-product-v1', 'opcenter2607-core',
     'opcenter2607-mfgorder-v1', 'BEGIN_PRODUCT', 'opcenter2607-product-v1',
     '["BeginProductId"]'::jsonb, '["ProductId"]'::jsonb,
     '订单起始产品', false, 'draft',
     '{"ontologyCandidate":"HAS_BEGIN_PRODUCT","requiresBusinessApproval":true}'::jsonb)
ON CONFLICT (relationship_contract_key) DO NOTHING;

INSERT INTO graphsync.app_setting (setting_key, value, description, editable)
VALUES
    ('product.name', '"Opcenter Graph Sync"'::jsonb, '主页产品名称', true),
    ('workflow.primary', '"camstar-to-graphstudio"'::jsonb, '平台主流程', false),
    ('sync.snapshot_row_threshold', '5000000'::jsonb, '切换到分区增量的建议行数阈值', true),
    ('sync.default_batch_rows', '10000'::jsonb, '流式导出每批最大行数', true),
    ('sync.target_shard_bytes', '67108864'::jsonb, '单个 RDF 分片目标字节数', true),
    ('sync.reference_validation_row_limit', '1000000'::jsonb, '内存引用完整性校验的目标类行数上限', true),
    ('sync.retention_success', '3'::jsonb, '成功产物保留数', true),
    ('catalog.retention_ready', '5'::jsonb, '映射目录 ready 快照保留数', true),
    ('ui.default_language', '"zh-CN"'::jsonb, '同步中心默认语言', true)
ON CONFLICT (setting_key) DO NOTHING;

-- The runner must acquire this lock before starting a job:
-- SELECT pg_try_advisory_lock(hashtextextended('graphsync:' || :job_name, 0));
