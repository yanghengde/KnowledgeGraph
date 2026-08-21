-- Camstar -> Graph Studio control plane.
-- This schema stores orchestration metadata and immutable governed projections;
-- source business data remains in Camstar and published RDF remains in Graph Studio.

CREATE SCHEMA IF NOT EXISTS graphsync;

CREATE TABLE IF NOT EXISTS graphsync.schema_version (
    version         integer PRIMARY KEY,
    description     text NOT NULL,
    installed_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graphsync.connection_profile (
    connection_key  text PRIMARY KEY,
    kind            text NOT NULL CHECK (kind IN (
                        'camstar_sqlserver', 'camstar_oracle', 'ontology_neo4j',
                        'publish_ontology_neo4j',
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
        'publish_ontology_neo4j',
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

-- The data lane is scheduled independently from Graph Studio publication.
-- PostgreSQL owns the clock and lease so multiple API/worker replicas cannot
-- execute the same due window twice.
CREATE TABLE IF NOT EXISTS graphsync.data_sync_schedule (
    profile_key          text PRIMARY KEY,
    job_name             text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    enabled              boolean NOT NULL DEFAULT false,
    interval_minutes     integer NOT NULL DEFAULT 15 CHECK (interval_minutes BETWEEN 1 AND 10080),
    max_attempts         integer NOT NULL DEFAULT 3 CHECK (max_attempts BETWEEN 1 AND 10),
    retry_backoff_seconds integer NOT NULL DEFAULT 60 CHECK (retry_backoff_seconds BETWEEN 5 AND 86400),
    next_run_at          timestamptz,
    lease_token          uuid,
    lease_until          timestamptz,
    last_run_id          uuid,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graphsync.data_sync_execution (
    run_id               uuid PRIMARY KEY,
    profile_key          text NOT NULL REFERENCES graphsync.data_sync_schedule(profile_key) ON DELETE CASCADE,
    job_name             text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    trigger_type         text NOT NULL CHECK (trigger_type IN ('manual','scheduled','retry')),
    status               text NOT NULL CHECK (status IN ('queued','running','succeeded','failed','skipped')),
    attempt              integer NOT NULL DEFAULT 1 CHECK (attempt >= 1),
    scheduled_for        timestamptz NOT NULL,
    next_retry_at        timestamptz,
    actor                text,
    release_id           uuid,
    error                jsonb,
    metrics              jsonb NOT NULL DEFAULT '{}'::jsonb,
    started_at           timestamptz,
    finished_at          timestamptz,
    created_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (profile_key, scheduled_for, attempt)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_data_sync_due
    ON graphsync.data_sync_schedule (next_run_at) WHERE enabled;
CREATE INDEX IF NOT EXISTS ix_graphsync_data_sync_execution_recent
    ON graphsync.data_sync_execution (profile_key, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_graphsync_data_sync_retry_due
    ON graphsync.data_sync_execution (next_retry_at)
    WHERE status='failed' AND next_retry_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS graphsync.data_sync_worker_heartbeat (
    worker_id             text PRIMARY KEY,
    last_seen_at          timestamptz NOT NULL DEFAULT now(),
    metadata              jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS graphsync.checkpoint (
    job_name              text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    partition_key         text NOT NULL,
    committed_watermark   jsonb NOT NULL,
    source_schema_hash    text,
    committed_run_id      uuid REFERENCES graphsync.sync_run(run_id),
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
                              'planned', 'baseline_required', 'no_changes', 'blocked', 'extracting',
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

ALTER TABLE graphsync.incremental_window
    DROP CONSTRAINT IF EXISTS incremental_window_status_check;
ALTER TABLE graphsync.incremental_window
    ADD CONSTRAINT incremental_window_status_check CHECK (status IN (
        'planned', 'baseline_required', 'no_changes', 'blocked', 'extracting',
        'staged', 'verified', 'committed', 'failed', 'abandoned'
    ));

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

CREATE TABLE IF NOT EXISTS graphsync.data_contract_field (
    contract_key          text NOT NULL REFERENCES graphsync.data_contract(contract_key) ON DELETE CASCADE,
    field_key             text NOT NULL,
    source_column         text,
    target_field          text NOT NULL,
    data_type             text NOT NULL DEFAULT 'String',
    nullable              boolean NOT NULL DEFAULT true,
    required              boolean NOT NULL DEFAULT false,
    field_role            text NOT NULL DEFAULT 'attribute' CHECK (field_role IN (
                              'primary_key', 'business_key', 'freshness',
                              'attribute', 'navigation', 'system'
                          )),
    lifecycle_status      text NOT NULL DEFAULT 'active' CHECK (lifecycle_status IN (
                              'experimental', 'active', 'deprecated', 'retired'
                          )),
    ordinal_position      integer NOT NULL DEFAULT 100,
    introduced_version   integer NOT NULL DEFAULT 1 CHECK (introduced_version > 0),
    deprecated_version   integer CHECK (deprecated_version IS NULL OR deprecated_version > 0),
    transform_expression text,
    default_expression   text,
    ontology_property    text,
    sensitivity          text NOT NULL DEFAULT 'internal' CHECK (sensitivity IN (
                              'public', 'internal', 'confidential', 'restricted'
                          )),
    searchable           boolean NOT NULL DEFAULT true,
    sortable             boolean NOT NULL DEFAULT true,
    config               jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (contract_key, field_key),
    UNIQUE (contract_key, target_field)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_contract_field_status
    ON graphsync.data_contract_field (contract_key, lifecycle_status, ordinal_position);

-- Generic relational attribute projection.  It can enrich any governed object
-- from one related table or an approved multi-hop join plan without changing
-- the canonical Camstar ontology or the source database schema.
CREATE TABLE IF NOT EXISTS graphsync.attribute_projection_contract (
    projection_key        text PRIMARY KEY,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    target_contract_key   text NOT NULL REFERENCES graphsync.data_contract(contract_key) ON DELETE CASCADE,
    title                 text NOT NULL,
    description           text,
    version               integer NOT NULL DEFAULT 1 CHECK (version > 0),
    status                text NOT NULL DEFAULT 'draft' CHECK (status IN (
                              'draft', 'reviewed', 'approved', 'retired'
                          )),
    enabled               boolean NOT NULL DEFAULT true,
    source_schema         text NOT NULL,
    source_table          text NOT NULL,
    source_alias          text NOT NULL DEFAULT 'src',
    owner_mapping         jsonb NOT NULL,
    join_plan             jsonb NOT NULL DEFAULT '[]'::jsonb,
    row_filters           jsonb NOT NULL DEFAULT '[]'::jsonb,
    cardinality           text NOT NULL DEFAULT 'one' CHECK (cardinality IN ('one', 'many')),
    multiple_match_policy text NOT NULL DEFAULT 'reject' CHECK (multiple_match_policy IN (
                              'reject', 'first', 'latest', 'array'
                          )),
    missing_policy        text NOT NULL DEFAULT 'null' CHECK (missing_policy IN (
                              'null', 'quarantine', 'reject'
                          )),
    collision_policy      text NOT NULL DEFAULT 'reject' CHECK (collision_policy IN (
                              'reject', 'overwrite', 'coalesce'
                          )),
    order_by              jsonb NOT NULL DEFAULT '[]'::jsonb,
    preview_row_limit     integer NOT NULL DEFAULT 100 CHECK (preview_row_limit BETWEEN 1 AND 10000),
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    approved_by           text,
    approved_at           timestamptz
);

CREATE INDEX IF NOT EXISTS ix_graphsync_attribute_projection_target
    ON graphsync.attribute_projection_contract (target_contract_key, status, enabled);

ALTER TABLE graphsync.attribute_projection_contract
    ADD COLUMN IF NOT EXISTS collision_policy text NOT NULL DEFAULT 'reject';
ALTER TABLE graphsync.attribute_projection_contract
    DROP CONSTRAINT IF EXISTS attribute_projection_contract_collision_policy_check;
ALTER TABLE graphsync.attribute_projection_contract
    ADD CONSTRAINT attribute_projection_contract_collision_policy_check
    CHECK (collision_policy IN ('reject', 'overwrite', 'coalesce'));

CREATE TABLE IF NOT EXISTS graphsync.attribute_projection_field (
    projection_key        text NOT NULL REFERENCES graphsync.attribute_projection_contract(projection_key) ON DELETE CASCADE,
    field_key             text NOT NULL,
    source_path           text NOT NULL,
    target_field          text NOT NULL,
    data_type             text NOT NULL DEFAULT 'String' CHECK (data_type IN (
                              'String', 'Integer', 'Float', 'Boolean',
                              'DateTime', 'Date', 'Navigation'
                          )),
    required              boolean NOT NULL DEFAULT false,
    ontology_property     text,
    lifecycle_status      text NOT NULL DEFAULT 'active' CHECK (lifecycle_status IN (
                              'experimental', 'active', 'deprecated', 'retired'
                          )),
    ordinal_position      integer NOT NULL DEFAULT 100,
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (projection_key, field_key),
    UNIQUE (projection_key, target_field)
);

CREATE TABLE IF NOT EXISTS graphsync.attribute_projection_preview (
    preview_id             uuid PRIMARY KEY,
    projection_key         text NOT NULL REFERENCES graphsync.attribute_projection_contract(projection_key) ON DELETE CASCADE,
    projection_version     integer NOT NULL CHECK (projection_version > 0),
    status                 text NOT NULL CHECK (status IN ('started', 'succeeded', 'failed')),
    owner_rows             integer NOT NULL DEFAULT 0,
    matched_rows           integer NOT NULL DEFAULT 0,
    missing_owners         integer NOT NULL DEFAULT 0,
    multiple_matches       integer NOT NULL DEFAULT 0,
    sample                 jsonb NOT NULL DEFAULT '[]'::jsonb,
    compiled_query_hash    text,
    error                  jsonb,
    started_at             timestamptz NOT NULL DEFAULT now(),
    finished_at            timestamptz
);

ALTER TABLE graphsync.attribute_projection_preview
    ADD COLUMN IF NOT EXISTS projection_version integer NOT NULL DEFAULT 1;

CREATE TABLE IF NOT EXISTS graphsync.asset_dependency (
    dependency_id         uuid PRIMARY KEY,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    upstream_type         text NOT NULL CHECK (upstream_type IN (
                              'data_contract', 'data_contract_field',
                              'relationship_contract', 'ontology_property',
                              'attribute_projection', 'attribute_projection_field'
                          )),
    upstream_key          text NOT NULL,
    downstream_type       text NOT NULL CHECK (downstream_type IN (
                              'curated_column', 'relationship_contract',
                              'ontology_property', 'graphstudio_predicate',
                              'query', 'dashboard', 'api', 'action'
                          )),
    downstream_key        text NOT NULL,
    dependency_kind       text NOT NULL DEFAULT 'hard' CHECK (dependency_kind IN (
                              'hard', 'soft', 'informational'
                          )),
    discovered_by         text NOT NULL DEFAULT 'compiler' CHECK (discovered_by IN (
                              'compiler', 'graphstudio', 'manual', 'runtime'
                          )),
    active                boolean NOT NULL DEFAULT true,
    metadata              jsonb NOT NULL DEFAULT '{}'::jsonb,
    first_seen_at         timestamptz NOT NULL DEFAULT now(),
    last_seen_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (profile_key, upstream_type, upstream_key, downstream_type, downstream_key)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_dependency_upstream
    ON graphsync.asset_dependency (profile_key, upstream_type, upstream_key, active);

ALTER TABLE graphsync.asset_dependency
    DROP CONSTRAINT IF EXISTS asset_dependency_upstream_type_check;
ALTER TABLE graphsync.asset_dependency
    ADD CONSTRAINT asset_dependency_upstream_type_check CHECK (upstream_type IN (
        'data_contract', 'data_contract_field', 'relationship_contract',
        'ontology_property', 'attribute_projection', 'attribute_projection_field'
    ));

CREATE TABLE IF NOT EXISTS graphsync.schema_change_request (
    change_id             uuid PRIMARY KEY,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    contract_key          text NOT NULL REFERENCES graphsync.data_contract(contract_key) ON DELETE CASCADE,
    base_version          integer NOT NULL CHECK (base_version > 0),
    target_version        integer NOT NULL CHECK (target_version > base_version),
    title                 text NOT NULL,
    description           text,
    status                text NOT NULL DEFAULT 'draft' CHECK (status IN (
                              'draft', 'analysis_ready', 'reviewed', 'approved',
                              'applying', 'applied', 'rejected', 'failed',
                              'rolled_back'
                          )),
    compatibility         text NOT NULL DEFAULT 'non_breaking' CHECK (compatibility IN (
                              'non_breaking', 'conditional', 'breaking'
                          )),
    migration_strategy    text,
    rollback_strategy     text,
    impact_summary        jsonb NOT NULL DEFAULT '{}'::jsonb,
    requested_by          text,
    approved_by           text,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    approved_at           timestamptz,
    applied_at            timestamptz
);

CREATE INDEX IF NOT EXISTS ix_graphsync_schema_change_contract
    ON graphsync.schema_change_request (contract_key, status, created_at DESC);

CREATE TABLE IF NOT EXISTS graphsync.schema_change_item (
    item_id               uuid PRIMARY KEY,
    change_id             uuid NOT NULL REFERENCES graphsync.schema_change_request(change_id) ON DELETE CASCADE,
    sequence_no           integer NOT NULL,
    operation             text NOT NULL CHECK (operation IN (
                              'add_field', 'deprecate_field', 'retire_field',
                              'rename_field', 'change_type', 'change_required',
                              'change_key', 'change_source', 'change_transform'
                          )),
    field_key             text NOT NULL,
    before_state          jsonb,
    after_state           jsonb,
    compatibility         text NOT NULL CHECK (compatibility IN (
                              'non_breaking', 'conditional', 'breaking'
                          )),
    migration_required    boolean NOT NULL DEFAULT false,
    backfill_required     boolean NOT NULL DEFAULT false,
    dependency_count      integer NOT NULL DEFAULT 0,
    notes                 text,
    created_at            timestamptz NOT NULL DEFAULT now(),
    UNIQUE (change_id, sequence_no)
);

CREATE TABLE IF NOT EXISTS graphsync.schema_migration_run (
    migration_run_id      uuid PRIMARY KEY,
    change_id             uuid NOT NULL REFERENCES graphsync.schema_change_request(change_id) ON DELETE CASCADE,
    status                text NOT NULL CHECK (status IN (
                              'planned', 'started', 'backfilling', 'verifying',
                              'succeeded', 'failed', 'rolled_back'
                          )),
    preview_only          boolean NOT NULL DEFAULT true,
    started_at            timestamptz NOT NULL DEFAULT now(),
    finished_at           timestamptz,
    affected_rows         bigint NOT NULL DEFAULT 0,
    checkpoint            jsonb,
    verification          jsonb NOT NULL DEFAULT '{}'::jsonb,
    error                 jsonb
);

-- Live physical-schema observations are evidence only.  Candidate columns are
-- never added to a publication contract until an explicit Schema change is
-- reviewed and applied.
CREATE TABLE IF NOT EXISTS graphsync.source_schema_observation (
    observation_id        uuid PRIMARY KEY,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    contract_key          text NOT NULL REFERENCES graphsync.data_contract(contract_key) ON DELETE CASCADE,
    source_schema         text NOT NULL,
    source_table          text NOT NULL,
    observed_at           timestamptz NOT NULL DEFAULT now(),
    schema_hash           text NOT NULL,
    status                text NOT NULL CHECK (status IN ('stable', 'drifted', 'failed')),
    columns               jsonb NOT NULL DEFAULT '[]'::jsonb,
    drift                 jsonb NOT NULL DEFAULT '{}'::jsonb,
    error                 jsonb
);

CREATE INDEX IF NOT EXISTS ix_graphsync_schema_observation_latest
    ON graphsync.source_schema_observation (profile_key, contract_key, observed_at DESC);

-- Immutable curated releases.  A release is populated and verified in isolation;
-- activation only moves a small pointer and therefore provides an inexpensive
-- rollback even when the source tables contain hundreds of millions of rows.
CREATE TABLE IF NOT EXISTS graphsync.curated_release (
    release_id            uuid PRIMARY KEY,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    release_no            bigint NOT NULL,
    status                text NOT NULL DEFAULT 'planned' CHECK (status IN (
                              'planned', 'extracting', 'verifying', 'ready',
                              'active', 'superseded', 'failed', 'rolled_back'
                          )),
    preview_only          boolean NOT NULL DEFAULT true,
    quality_run_id        uuid REFERENCES graphsync.curation_run(curation_run_id) ON DELETE SET NULL,
    contract_versions     jsonb NOT NULL DEFAULT '{}'::jsonb,
    schema_change_ids     jsonb NOT NULL DEFAULT '[]'::jsonb,
    source_snapshot       jsonb NOT NULL DEFAULT '{}'::jsonb,
    source_rows_read      bigint NOT NULL DEFAULT 0,
    object_count          bigint NOT NULL DEFAULT 0,
    relationship_count    bigint NOT NULL DEFAULT 0,
    quarantine_count      bigint NOT NULL DEFAULT 0,
    content_hash          text,
    summary               jsonb NOT NULL DEFAULT '{}'::jsonb,
    error                 jsonb,
    requested_by          text,
    started_at            timestamptz NOT NULL DEFAULT now(),
    finished_at           timestamptz,
    UNIQUE (profile_key, release_no)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_curated_release_status
    ON graphsync.curated_release (profile_key, status, release_no DESC);

CREATE TABLE IF NOT EXISTS graphsync.curated_release_activation (
    profile_key           text PRIMARY KEY REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    active_release_id     uuid NOT NULL REFERENCES graphsync.curated_release(release_id),
    previous_release_id   uuid REFERENCES graphsync.curated_release(release_id),
    activated_at          timestamptz NOT NULL DEFAULT now(),
    activated_by          text
);

CREATE TABLE IF NOT EXISTS graphsync.materialization_batch (
    batch_id              uuid PRIMARY KEY,
    release_id            uuid NOT NULL REFERENCES graphsync.curated_release(release_id) ON DELETE CASCADE,
    contract_key          text NOT NULL REFERENCES graphsync.data_contract(contract_key),
    batch_no              integer NOT NULL,
    status                text NOT NULL CHECK (status IN (
                              'started', 'written', 'verified', 'failed'
                          )),
    lower_key             jsonb,
    upper_key             jsonb,
    rows_read             bigint NOT NULL DEFAULT 0,
    rows_written          bigint NOT NULL DEFAULT 0,
    rows_quarantined      bigint NOT NULL DEFAULT 0,
    content_hash          text,
    started_at            timestamptz NOT NULL DEFAULT now(),
    finished_at           timestamptz,
    error                 jsonb,
    UNIQUE (release_id, contract_key, batch_no)
);

-- Governed target ontology.  Neo4j stores the editable/released graph while
-- PostgreSQL owns workflow, approval, activation and audit metadata.
CREATE TABLE IF NOT EXISTS graphsync.ontology_workspace (
    workspace_id          uuid PRIMARY KEY,
    workspace_key         text NOT NULL UNIQUE,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    title                 text NOT NULL,
    description           text,
    status                text NOT NULL DEFAULT 'draft' CHECK (status IN (
                              'draft', 'reviewed', 'frozen', 'retired'
                          )),
    revision              integer NOT NULL DEFAULT 1 CHECK (revision >= 1),
    graph_database        text NOT NULL,
    source_ontology_hash  text,
    created_by            text,
    reviewed_by           text,
    reviewed_at           timestamptz,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now(),
    config                jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS graphsync.ontology_release (
    ontology_release_id   uuid PRIMARY KEY,
    workspace_id          uuid NOT NULL REFERENCES graphsync.ontology_workspace(workspace_id),
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    release_no            bigint NOT NULL,
    status                text NOT NULL DEFAULT 'approved' CHECK (status IN (
                              'approved', 'active', 'superseded', 'retired'
                          )),
    graph_database        text NOT NULL,
    content_hash          text NOT NULL,
    class_count           integer NOT NULL DEFAULT 0,
    property_count        integer NOT NULL DEFAULT 0,
    relationship_count    integer NOT NULL DEFAULT 0,
    approved_by           text NOT NULL,
    created_at            timestamptz NOT NULL DEFAULT now(),
    activated_at          timestamptz,
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (profile_key, release_no),
    UNIQUE (profile_key, content_hash)
);

CREATE TABLE IF NOT EXISTS graphsync.ontology_release_activation (
    profile_key           text PRIMARY KEY REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    active_release_id     uuid NOT NULL REFERENCES graphsync.ontology_release(ontology_release_id),
    previous_release_id   uuid REFERENCES graphsync.ontology_release(ontology_release_id),
    activated_at          timestamptz NOT NULL DEFAULT now(),
    activated_by          text NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_graphsync_ontology_workspace_profile
    ON graphsync.ontology_workspace (profile_key, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS ix_graphsync_ontology_release_profile
    ON graphsync.ontology_release (profile_key, status, release_no DESC);

-- v16 consolidates the immutable business projection into graphsync.  Move
-- existing relations by OID so every row, constraint and index is preserved.
DROP VIEW IF EXISTS camstar_curated.active_relationship;
DROP VIEW IF EXISTS camstar_curated.active_object;

DO $$
BEGIN
    IF to_regclass('camstar_curated.object_version') IS NOT NULL
       AND to_regclass('graphsync.object_version') IS NULL THEN
        ALTER TABLE camstar_curated.object_version SET SCHEMA graphsync;
    END IF;
    IF to_regclass('camstar_curated.relationship_version') IS NOT NULL
       AND to_regclass('graphsync.relationship_version') IS NULL THEN
        ALTER TABLE camstar_curated.relationship_version SET SCHEMA graphsync;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS graphsync.object_version (
    release_id            uuid NOT NULL REFERENCES graphsync.curated_release(release_id) ON DELETE CASCADE,
    profile_key           text NOT NULL,
    contract_key          text NOT NULL,
    contract_version      integer NOT NULL,
    class_name            text NOT NULL,
    object_uri            text NOT NULL,
    source_primary_key    jsonb NOT NULL,
    business_key          jsonb NOT NULL DEFAULT '{}'::jsonb,
    source_values         jsonb NOT NULL,
    properties            jsonb NOT NULL,
    source_hash           text NOT NULL,
    source_change_at      timestamptz,
    record_status         text NOT NULL DEFAULT 'active' CHECK (record_status IN (
                              'active', 'quarantined', 'deleted'
                          )),
    quality_issues        jsonb NOT NULL DEFAULT '[]'::jsonb,
    loaded_at             timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (release_id, contract_key, object_uri)
);

CREATE INDEX IF NOT EXISTS ix_curated_object_lookup
    ON graphsync.object_version (profile_key, contract_key, object_uri);
CREATE INDEX IF NOT EXISTS ix_curated_object_source_key
    ON graphsync.object_version USING gin (source_primary_key jsonb_path_ops);

CREATE TABLE IF NOT EXISTS graphsync.relationship_version (
    release_id            uuid NOT NULL REFERENCES graphsync.curated_release(release_id) ON DELETE CASCADE,
    relationship_contract_key text NOT NULL,
    relationship_name     text NOT NULL,
    source_contract_key   text NOT NULL,
    target_contract_key   text NOT NULL,
    source_object_uri     text NOT NULL,
    target_object_uri     text,
    source_reference      jsonb NOT NULL,
    resolution_status     text NOT NULL CHECK (resolution_status IN (
                              'resolved', 'pending', 'quarantined'
                          )),
    source_hash           text NOT NULL,
    loaded_at             timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (release_id, relationship_contract_key, source_object_uri)
);

CREATE INDEX IF NOT EXISTS ix_curated_relationship_target
    ON graphsync.relationship_version (release_id, target_contract_key, target_object_uri);

-- Source ingestion is committed independently from Graph Studio delivery.
-- A baseline snapshot may have no incremental sync_run, so the immutable
-- curated release is the durable commit owner and committed_run_id is optional.
ALTER TABLE graphsync.checkpoint
    ALTER COLUMN committed_run_id DROP NOT NULL;
ALTER TABLE graphsync.checkpoint
    ADD COLUMN IF NOT EXISTS committed_release_id uuid
    REFERENCES graphsync.curated_release(release_id);
ALTER TABLE graphsync.checkpoint
    ADD COLUMN IF NOT EXISTS validation jsonb NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS graphsync.ingestion_checkpoint_history (
    job_name              text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    partition_key         text NOT NULL,
    committed_release_id  uuid NOT NULL REFERENCES graphsync.curated_release(release_id) ON DELETE CASCADE,
    committed_watermark   jsonb NOT NULL,
    committed_run_id      uuid REFERENCES graphsync.sync_run(run_id),
    source_schema_hash    text,
    validation            jsonb NOT NULL DEFAULT '{}'::jsonb,
    committed_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (job_name, partition_key, committed_release_id)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_checkpoint_history_release
    ON graphsync.ingestion_checkpoint_history (committed_release_id, partition_key);

-- Durable inbox for at-least-once source capture. event_key is derived from
-- source table + primary key + source position + operation, making retries of
-- the same frozen window harmless.
CREATE TABLE IF NOT EXISTS graphsync.change_event (
    event_key             text PRIMARY KEY,
    job_name              text NOT NULL REFERENCES graphsync.sync_job(job_name) ON DELETE CASCADE,
    class_name            text NOT NULL,
    window_id             uuid NOT NULL REFERENCES graphsync.incremental_window(window_id) ON DELETE CASCADE,
    operation             text NOT NULL CHECK (operation IN (
                              'insert', 'update', 'upsert', 'delete'
                          )),
    source_primary_key    jsonb NOT NULL,
    source_position       jsonb NOT NULL,
    row_payload           jsonb,
    payload_hash          text NOT NULL,
    status                text NOT NULL DEFAULT 'captured' CHECK (status IN (
                              'captured', 'applied', 'ignored'
                          )),
    applied_release_id    uuid REFERENCES graphsync.curated_release(release_id),
    captured_at           timestamptz NOT NULL DEFAULT now(),
    applied_at            timestamptz,
    UNIQUE (job_name, class_name, source_position, source_primary_key, operation)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_change_event_window
    ON graphsync.change_event (window_id, status, captured_at);
CREATE INDEX IF NOT EXISTS ix_graphsync_change_event_release
    ON graphsync.change_event (applied_release_id, class_name);

-- Count reconciliation is release evidence, not a transient UI calculation.
CREATE TABLE IF NOT EXISTS graphsync.reconciliation_result (
    reconciliation_id    uuid PRIMARY KEY,
    release_id            uuid NOT NULL REFERENCES graphsync.curated_release(release_id) ON DELETE CASCADE,
    contract_key          text NOT NULL REFERENCES graphsync.data_contract(contract_key),
    mode                  text NOT NULL CHECK (mode IN (
                              'snapshot', 'baseline_snapshot', 'incremental',
                              'field_backfill'
                          )),
    source_count          bigint,
    release_count         bigint NOT NULL,
    difference            bigint,
    status                text NOT NULL CHECK (status IN (
                              'verified', 'warning', 'failed'
                          )),
    details               jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    UNIQUE (release_id, contract_key)
);

CREATE INDEX IF NOT EXISTS ix_graphsync_reconciliation_release
    ON graphsync.reconciliation_result (release_id, status, contract_key);

-- A partially applied migration may have created both copies.  Merge only
-- non-conflicting immutable rows, reject conflicting duplicates, then remove
-- the legacy tables rather than silently choosing one copy.
DO $$
BEGIN
    IF to_regclass('camstar_curated.object_version') IS NOT NULL THEN
        IF EXISTS (
            SELECT 1
            FROM camstar_curated.object_version legacy
            JOIN graphsync.object_version current
              USING (release_id, contract_key, object_uri)
            WHERE to_jsonb(legacy) IS DISTINCT FROM to_jsonb(current)
        ) THEN
            RAISE EXCEPTION 'Conflicting object_version rows exist in both schemas';
        END IF;
        INSERT INTO graphsync.object_version
        SELECT * FROM camstar_curated.object_version
        ON CONFLICT (release_id, contract_key, object_uri) DO NOTHING;
        DROP TABLE camstar_curated.object_version;
    END IF;
    IF to_regclass('camstar_curated.relationship_version') IS NOT NULL THEN
        IF EXISTS (
            SELECT 1
            FROM camstar_curated.relationship_version legacy
            JOIN graphsync.relationship_version current
              USING (release_id, relationship_contract_key, source_object_uri)
            WHERE to_jsonb(legacy) IS DISTINCT FROM to_jsonb(current)
        ) THEN
            RAISE EXCEPTION 'Conflicting relationship_version rows exist in both schemas';
        END IF;
        INSERT INTO graphsync.relationship_version
        SELECT * FROM camstar_curated.relationship_version
        ON CONFLICT (release_id, relationship_contract_key, source_object_uri) DO NOTHING;
        DROP TABLE camstar_curated.relationship_version;
    END IF;
END $$;

CREATE OR REPLACE VIEW graphsync.active_object AS
SELECT object.*
FROM graphsync.object_version object
JOIN graphsync.curated_release_activation active
  ON active.profile_key=object.profile_key
 AND active.active_release_id=object.release_id
WHERE object.record_status='active';

CREATE OR REPLACE VIEW graphsync.active_relationship AS
SELECT relationship.*
FROM graphsync.relationship_version relationship
JOIN graphsync.curated_release release USING (release_id)
JOIN graphsync.curated_release_activation active
  ON active.profile_key=release.profile_key
 AND active.active_release_id=relationship.release_id
WHERE relationship.resolution_status='resolved';

DROP SCHEMA IF EXISTS camstar_curated;

-- Environment promotion and blue/green Graph Studio deployment ledger.
CREATE TABLE IF NOT EXISTS graphsync.deployment_environment (
    environment_key       text PRIMARY KEY,
    title                 text NOT NULL,
    promotion_order       integer NOT NULL,
    graphmart_uri         text NOT NULL,
    apply_enabled         boolean NOT NULL DEFAULT false,
    requires_approval     boolean NOT NULL DEFAULT true,
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);

-- Graph Studio destinations are independent from promotion environments.  A
-- business graph profile can be routed to one or more Graphmarts without
-- changing the governed ontology or duplicating the source configuration.
CREATE TABLE IF NOT EXISTS graphsync.graphstudio_target (
    target_key             text PRIMARY KEY,
    title                  text NOT NULL,
    connection_key         text NOT NULL DEFAULT 'graph-studio'
                           REFERENCES graphsync.connection_profile(connection_key),
    graphmart_uri          text NOT NULL,
    description            text,
    enabled                boolean NOT NULL DEFAULT true,
    config                 jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at             timestamptz NOT NULL DEFAULT now(),
    updated_at             timestamptz NOT NULL DEFAULT now(),
    UNIQUE (connection_key, graphmart_uri)
);

CREATE TABLE IF NOT EXISTS graphsync.publication_route (
    route_key              text PRIMARY KEY,
    profile_key            text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    environment_key        text NOT NULL REFERENCES graphsync.deployment_environment(environment_key),
    target_key             text NOT NULL REFERENCES graphsync.graphstudio_target(target_key),
    title                  text NOT NULL,
    promotion_order        integer NOT NULL,
    apply_enabled          boolean NOT NULL DEFAULT false,
    requires_approval      boolean NOT NULL DEFAULT true,
    enabled                boolean NOT NULL DEFAULT true,
    config                 jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at             timestamptz NOT NULL DEFAULT now(),
    updated_at             timestamptz NOT NULL DEFAULT now(),
    UNIQUE (profile_key, environment_key, target_key)
);

CREATE TABLE IF NOT EXISTS graphsync.target_release_activation (
    route_key              text PRIMARY KEY REFERENCES graphsync.publication_route(route_key) ON DELETE CASCADE,
    ontology_release_id    uuid REFERENCES graphsync.ontology_release(ontology_release_id),
    curated_release_id     uuid REFERENCES graphsync.curated_release(release_id),
    deployment_id          uuid,
    activated_at           timestamptz NOT NULL DEFAULT now(),
    activated_by           text
);

CREATE TABLE IF NOT EXISTS graphsync.deployment_release (
    deployment_id         uuid PRIMARY KEY,
    environment_key       text NOT NULL REFERENCES graphsync.deployment_environment(environment_key),
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key),
    curated_release_id    uuid NOT NULL REFERENCES graphsync.curated_release(release_id),
    ontology_release_id   uuid REFERENCES graphsync.ontology_release(ontology_release_id),
    status                text NOT NULL DEFAULT 'planned' CHECK (status IN (
                              'planned', 'approved', 'uploading', 'loading',
                              'verifying', 'active', 'failed', 'rolled_back'
                          )),
    slot                   text NOT NULL CHECK (slot IN ('blue', 'green')),
    artifact_uri          text,
    artifact_hash         text,
    model_uri             text,
    dataset_uri           text,
    catalog_entry         text,
    layer_uri             text,
    step_uri              text,
    previous_deployment_id uuid REFERENCES graphsync.deployment_release(deployment_id),
    validation_plan       jsonb NOT NULL DEFAULT '{}'::jsonb,
    validation_result     jsonb NOT NULL DEFAULT '{}'::jsonb,
    approved_by           text,
    requested_by          text,
    started_at            timestamptz NOT NULL DEFAULT now(),
    finished_at           timestamptz,
    error                 jsonb
);

ALTER TABLE graphsync.deployment_release
    ADD COLUMN IF NOT EXISTS route_key text
    REFERENCES graphsync.publication_route(route_key);

ALTER TABLE graphsync.target_release_activation
    DROP CONSTRAINT IF EXISTS target_release_activation_deployment_id_fkey;
ALTER TABLE graphsync.target_release_activation
    ADD CONSTRAINT target_release_activation_deployment_id_fkey
    FOREIGN KEY (deployment_id) REFERENCES graphsync.deployment_release(deployment_id);

CREATE INDEX IF NOT EXISTS ix_graphsync_publication_route_profile
    ON graphsync.publication_route (profile_key, enabled, promotion_order);
CREATE INDEX IF NOT EXISTS ix_graphsync_deployment_route
    ON graphsync.deployment_release (route_key, started_at DESC);

CREATE INDEX IF NOT EXISTS ix_graphsync_deployment_env
    ON graphsync.deployment_release (environment_key, profile_key, started_at DESC);

ALTER TABLE graphsync.deployment_release
    ADD COLUMN IF NOT EXISTS ontology_release_id uuid
    REFERENCES graphsync.ontology_release(ontology_release_id);

-- Target delivery has its own checkpoint. It advances only after Layer switch
-- and SPARQL acceptance have succeeded for one publication route.
CREATE TABLE IF NOT EXISTS graphsync.publication_checkpoint (
    route_key             text PRIMARY KEY REFERENCES graphsync.publication_route(route_key) ON DELETE CASCADE,
    deployment_id         uuid NOT NULL REFERENCES graphsync.deployment_release(deployment_id),
    ontology_release_id   uuid NOT NULL REFERENCES graphsync.ontology_release(ontology_release_id),
    curated_release_id    uuid NOT NULL REFERENCES graphsync.curated_release(release_id),
    artifact_hash         text NOT NULL,
    validation            jsonb NOT NULL DEFAULT '{}'::jsonb,
    committed_at          timestamptz NOT NULL DEFAULT now()
);

-- Runtime lineage, health metrics and alert lifecycle.
CREATE TABLE IF NOT EXISTS graphsync.runtime_lineage_event (
    lineage_event_id      uuid PRIMARY KEY,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    run_type              text NOT NULL CHECK (run_type IN (
                              'curation', 'materialization', 'deployment', 'action'
                          )),
    run_id                uuid NOT NULL,
    source_asset          text NOT NULL,
    target_asset          text NOT NULL,
    field_mappings        jsonb NOT NULL DEFAULT '{}'::jsonb,
    row_count             bigint NOT NULL DEFAULT 0,
    content_hash          text,
    occurred_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_graphsync_runtime_lineage_profile
    ON graphsync.runtime_lineage_event (profile_key, occurred_at DESC);

CREATE TABLE IF NOT EXISTS graphsync.health_check_run (
    health_run_id         uuid PRIMARY KEY,
    profile_key           text NOT NULL REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    status                text NOT NULL CHECK (status IN ('healthy', 'degraded', 'unhealthy', 'failed')),
    started_at            timestamptz NOT NULL DEFAULT now(),
    finished_at           timestamptz,
    summary               jsonb NOT NULL DEFAULT '{}'::jsonb,
    error                 jsonb
);

CREATE TABLE IF NOT EXISTS graphsync.health_metric (
    metric_id             uuid PRIMARY KEY,
    health_run_id         uuid NOT NULL REFERENCES graphsync.health_check_run(health_run_id) ON DELETE CASCADE,
    metric_key            text NOT NULL,
    scope_type            text NOT NULL DEFAULT 'profile',
    scope_key             text NOT NULL,
    value_numeric         numeric,
    value_text            text,
    unit                   text,
    status                text NOT NULL CHECK (status IN ('healthy', 'warning', 'critical', 'unknown')),
    message               text NOT NULL,
    details               jsonb NOT NULL DEFAULT '{}'::jsonb,
    measured_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graphsync.alert_rule (
    rule_key              text PRIMARY KEY,
    profile_key           text REFERENCES graphsync.graph_profile(profile_key) ON DELETE CASCADE,
    metric_key            text NOT NULL,
    operator              text NOT NULL CHECK (operator IN ('gt', 'gte', 'lt', 'lte', 'eq', 'missing')),
    threshold             numeric,
    severity              text NOT NULL CHECK (severity IN ('warning', 'critical')),
    consecutive_failures  integer NOT NULL DEFAULT 1 CHECK (consecutive_failures > 0),
    enabled               boolean NOT NULL DEFAULT true,
    channels              jsonb NOT NULL DEFAULT '[]'::jsonb,
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graphsync.alert_event (
    alert_event_id        uuid PRIMARY KEY,
    rule_key              text NOT NULL REFERENCES graphsync.alert_rule(rule_key),
    health_run_id         uuid REFERENCES graphsync.health_check_run(health_run_id),
    status                text NOT NULL CHECK (status IN ('open', 'acknowledged', 'resolved')),
    severity              text NOT NULL CHECK (severity IN ('warning', 'critical')),
    fingerprint           text NOT NULL,
    message               text NOT NULL,
    details               jsonb NOT NULL DEFAULT '{}'::jsonb,
    opened_at             timestamptz NOT NULL DEFAULT now(),
    acknowledged_at       timestamptz,
    resolved_at           timestamptz,
    acknowledged_by      text
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_graphsync_open_alert
    ON graphsync.alert_event (rule_key, fingerprint)
    WHERE status IN ('open', 'acknowledged');

-- Governed Camstar API actions.  No action definition contains database SQL;
-- mutations must travel through the configured Camstar service endpoint.
CREATE TABLE IF NOT EXISTS graphsync.action_definition (
    action_key            text PRIMARY KEY,
    title                 text NOT NULL,
    description           text,
    object_class          text NOT NULL,
    endpoint_path         text NOT NULL,
    http_method           text NOT NULL CHECK (http_method IN ('POST', 'PUT', 'PATCH', 'DELETE')),
    input_schema          jsonb NOT NULL DEFAULT '{}'::jsonb,
    allowed_roles         jsonb NOT NULL DEFAULT '[]'::jsonb,
    approval_required     boolean NOT NULL DEFAULT true,
    enabled               boolean NOT NULL DEFAULT false,
    timeout_seconds       integer NOT NULL DEFAULT 60 CHECK (timeout_seconds BETWEEN 1 AND 600),
    retry_policy          jsonb NOT NULL DEFAULT '{"maxAttempts":1}'::jsonb,
    compensation_action_key text REFERENCES graphsync.action_definition(action_key),
    version               integer NOT NULL DEFAULT 1 CHECK (version > 0),
    status                text NOT NULL DEFAULT 'draft' CHECK (status IN (
                              'draft', 'reviewed', 'approved', 'retired'
                          )),
    origin                text NOT NULL DEFAULT 'manual' CHECK (origin IN (
                              'manual', 'openapi'
                          )),
    operation_id          text,
    reviewed_by           text,
    reviewed_at           timestamptz,
    approved_by           text,
    approved_at           timestamptz,
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graphsync.action_invocation (
    invocation_id         uuid PRIMARY KEY,
    action_key            text NOT NULL REFERENCES graphsync.action_definition(action_key),
    idempotency_key       text NOT NULL UNIQUE,
    actor                 text NOT NULL,
    actor_roles           jsonb NOT NULL DEFAULT '[]'::jsonb,
    status                text NOT NULL CHECK (status IN (
                              'planned', 'pending_approval', 'approved', 'executing',
                              'succeeded', 'failed', 'compensating', 'compensated', 'rejected'
                          )),
    dry_run               boolean NOT NULL DEFAULT true,
    request_payload       jsonb NOT NULL,
    request_hash          text NOT NULL,
    response_summary      jsonb,
    approved_by           text,
    approved_at           timestamptz,
    started_at            timestamptz NOT NULL DEFAULT now(),
    finished_at           timestamptz,
    error                 jsonb
);

ALTER TABLE graphsync.action_definition
    ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 1;
ALTER TABLE graphsync.action_definition
    ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'draft';
ALTER TABLE graphsync.action_definition
    ADD COLUMN IF NOT EXISTS origin text NOT NULL DEFAULT 'manual';
ALTER TABLE graphsync.action_definition
    ADD COLUMN IF NOT EXISTS operation_id text;
ALTER TABLE graphsync.action_definition
    ADD COLUMN IF NOT EXISTS reviewed_by text;
ALTER TABLE graphsync.action_definition
    ADD COLUMN IF NOT EXISTS reviewed_at timestamptz;
ALTER TABLE graphsync.action_definition
    ADD COLUMN IF NOT EXISTS approved_by text;
ALTER TABLE graphsync.action_definition
    ADD COLUMN IF NOT EXISTS approved_at timestamptz;
ALTER TABLE graphsync.action_definition
    DROP CONSTRAINT IF EXISTS action_definition_status_check;
ALTER TABLE graphsync.action_definition
    ADD CONSTRAINT action_definition_status_check
    CHECK (status IN ('draft', 'reviewed', 'approved', 'retired'));
ALTER TABLE graphsync.action_definition
    DROP CONSTRAINT IF EXISTS action_definition_origin_check;
ALTER TABLE graphsync.action_definition
    ADD CONSTRAINT action_definition_origin_check
    CHECK (origin IN ('manual', 'openapi'));

ALTER TABLE graphsync.action_invocation
    ADD COLUMN IF NOT EXISTS compensation_of uuid REFERENCES graphsync.action_invocation(invocation_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_graphsync_action_compensation
    ON graphsync.action_invocation (compensation_of)
    WHERE compensation_of IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_graphsync_action_invocation
    ON graphsync.action_invocation (action_key, started_at DESC);

CREATE TABLE IF NOT EXISTS graphsync.action_event (
    action_event_id       uuid PRIMARY KEY,
    invocation_id         uuid NOT NULL REFERENCES graphsync.action_invocation(invocation_id) ON DELETE CASCADE,
    event_type            text NOT NULL,
    actor                 text,
    details               jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now()
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

DROP TRIGGER IF EXISTS trg_data_contract_field_updated ON graphsync.data_contract_field;
CREATE TRIGGER trg_data_contract_field_updated
BEFORE UPDATE ON graphsync.data_contract_field
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_attribute_projection_contract_updated ON graphsync.attribute_projection_contract;
CREATE TRIGGER trg_attribute_projection_contract_updated
BEFORE UPDATE ON graphsync.attribute_projection_contract
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_attribute_projection_field_updated ON graphsync.attribute_projection_field;
CREATE TRIGGER trg_attribute_projection_field_updated
BEFORE UPDATE ON graphsync.attribute_projection_field
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_schema_change_request_updated ON graphsync.schema_change_request;
CREATE TRIGGER trg_schema_change_request_updated
BEFORE UPDATE ON graphsync.schema_change_request
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_deployment_environment_updated ON graphsync.deployment_environment;
CREATE TRIGGER trg_deployment_environment_updated
BEFORE UPDATE ON graphsync.deployment_environment
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_ontology_workspace_updated ON graphsync.ontology_workspace;
CREATE TRIGGER trg_ontology_workspace_updated
BEFORE UPDATE ON graphsync.ontology_workspace
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_alert_rule_updated ON graphsync.alert_rule;
CREATE TRIGGER trg_alert_rule_updated
BEFORE UPDATE ON graphsync.alert_rule
FOR EACH ROW EXECUTE FUNCTION graphsync.touch_updated_at();

DROP TRIGGER IF EXISTS trg_action_definition_updated ON graphsync.action_definition;
CREATE TRIGGER trg_action_definition_updated
BEFORE UPDATE ON graphsync.action_definition
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

INSERT INTO graphsync.schema_version (version, description)
VALUES (9, 'Schema evolution requests, field lifecycle and dependency impact')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (10, 'Immutable curated releases, batched materialization and pointer rollback')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (11, 'Environment promotion and blue-green Graph Studio deployment ledger')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (12, 'Runtime field lineage, health metrics and alert lifecycle')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (13, 'Governed Camstar API actions with idempotency and compensation audit')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (14, 'Generic related-table attribute projections for any governed object')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (15, 'Single-database generic curated storage and configurable governed actions')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (16, 'Unified graphsync instance storage and governed publish ontology workspace')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (17, 'Continuous publication, live schema drift evidence and narrow field backfill')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (18, 'Effectively-once ingestion, split delivery checkpoints and reconciliation evidence')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.schema_version (version, description)
VALUES (19, 'Leased data-lane scheduling, audited retries and worker heartbeat')
ON CONFLICT (version) DO NOTHING;

INSERT INTO graphsync.data_sync_schedule
    (profile_key, job_name, enabled, interval_minutes, max_attempts,
     retry_backoff_seconds, next_run_at)
SELECT profile.profile_key, profile.job_name, false, 15, 3, 60, NULL
FROM graphsync.graph_profile profile
ON CONFLICT (profile_key) DO NOTHING;

-- WorkflowStep may reference a fixed Spec revision (SpecId) or the current
-- revision through SpecBaseId.  Preserve both representations in one audited
-- relationship contract, with the revision-specific key taking precedence.
UPDATE graphsync.relationship_contract
SET config = config || '{"matchAlternatives":[{"sourceColumns":["SpecBaseId"],"targetColumns":["SpecBaseId"]}]}'::jsonb
WHERE profile_key='opcenter2607-core'
  AND source_contract_key='opcenter2607-core:workflowstep:v1'
  AND target_contract_key='opcenter2607-core:spec:v1'
  AND relationship_name='HAS_SPEC';

INSERT INTO graphsync.menu_item
    (menu_key, label_zh, label_en, route, icon, sort_order, enabled, capability)
VALUES
    ('overview',    '总览',     'Overview',    '#overview',    'dashboard', 10, true,  'sync.read'),
    ('connections', '连接管理', 'Connections', '#connections', 'plug',      20, true,  'connection.read'),
    ('jobs',        '同步任务', 'Sync Jobs',   '#jobs',        'schedule',  30, true,  'job.read'),
    ('ontology_governance','本体治理','Ontology Governance','#ontology_governance','ontology',34,true,'ontology.write'),
    ('profiles',    '业务图谱', 'Graph Profile','#profiles',    'profile',   35, true,  'profile.write'),
    ('projections', '属性投影', 'Attribute Projections','#projections','projection', 36, true, 'projection.write'),
    ('releases',    '治理版本', 'Curated Releases','#releases', 'database',  37, true,  'curation.write'),
    ('deployments', '环境发布', 'Deployments', '#deployments', 'rocket',    38, true,  'deployment.write'),
    ('observability','血缘监控','Observability','#observability','pulse',   39, true,  'health.read'),
    ('actions',     '业务动作', 'Actions',     '#actions',     'action',    40, true,  'action.plan'),
    ('mappings',    '映射管理', 'Mappings',    '#mappings',    'mapping',   40, true,  'mapping.read'),
    ('runs',        '运行记录', 'Runs',        '#runs',        'history',   50, true,  'run.read'),
    ('settings',    '系统设置', 'Settings',    '#settings',    'settings',  60, true,  'setting.write')
ON CONFLICT (menu_key) DO NOTHING;

UPDATE graphsync.menu_item
SET route='#ontology_governance', updated_at=now()
WHERE menu_key='ontology_governance' AND route <> '#ontology_governance';

INSERT INTO graphsync.sync_job
    (job_name, title, description, graphmart_uri, mode, schedule, timezone, enabled, config)
VALUES (
    'camstar-full',
    'Camstar 全量图谱同步',
    '从 Camstar SQL Server 和 Neo4j 本体生成 RDF 快照并发布到 Opcenter2607。',
    'http://cambridgesemantics.com/Graphmart/fa5ee4d00d9744c996165abcdec9a647',
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

INSERT INTO graphsync.deployment_environment
    (environment_key, title, promotion_order, graphmart_uri,
     apply_enabled, requires_approval, config)
VALUES
    ('dev', '开发验证', 10,
     'http://cambridgesemantics.com/Graphmart/fa5ee4d00d9744c996165abcdec9a647',
     false, false, '{"purpose":"integration","blueGreen":true}'::jsonb),
    ('uat', '业务验收', 20,
     'http://cambridgesemantics.com/Graphmart/fa5ee4d00d9744c996165abcdec9a647',
     false, true, '{"purpose":"business_acceptance","blueGreen":true}'::jsonb),
    ('prod', '生产', 30,
     'http://cambridgesemantics.com/Graphmart/fa5ee4d00d9744c996165abcdec9a647',
     false, true, '{"purpose":"production","blueGreen":true,"requireUat":true}'::jsonb)
ON CONFLICT (environment_key) DO NOTHING;

-- Migrate the original environment-bound Graphmart configuration into the
-- multi-target model.  Identical URIs become one reusable target; each
-- profile/environment pair receives an explicit publication route.
INSERT INTO graphsync.graphstudio_target
    (target_key, title, connection_key, graphmart_uri, description, config)
SELECT 'graphmart-' || substr(md5(environment.graphmart_uri), 1, 12),
       'Opcenter2607 Graphmart',
       'graph-studio', environment.graphmart_uri,
       '由原 Graph Studio 环境配置自动迁移的发布目标。',
       jsonb_build_object('migratedFromEnvironment', true)
FROM graphsync.deployment_environment environment
GROUP BY environment.graphmart_uri
ON CONFLICT (connection_key, graphmart_uri) DO UPDATE SET
    title=CASE
        WHEN graphsync.graphstudio_target.config->>'migratedFromEnvironment'='true'
        THEN EXCLUDED.title
        ELSE graphsync.graphstudio_target.title
    END,
    updated_at=now();

INSERT INTO graphsync.publication_route
    (route_key, profile_key, environment_key, target_key, title,
     promotion_order, apply_enabled, requires_approval, config)
SELECT profile.profile_key || '-' || environment.environment_key,
       profile.profile_key, environment.environment_key, target.target_key,
       profile.title || ' → ' || environment.title,
       environment.promotion_order, environment.apply_enabled,
       environment.requires_approval,
       jsonb_build_object('migratedFromEnvironment', true)
FROM graphsync.graph_profile profile
CROSS JOIN graphsync.deployment_environment environment
JOIN graphsync.graphstudio_target target
  ON target.connection_key='graph-studio'
 AND target.graphmart_uri=environment.graphmart_uri
WHERE profile.profile_key='opcenter2607-core'
ON CONFLICT (profile_key, environment_key, target_key) DO NOTHING;

UPDATE graphsync.deployment_release deployment
SET route_key=route.route_key
FROM graphsync.publication_route route
WHERE deployment.route_key IS NULL
  AND route.profile_key=deployment.profile_key
  AND route.environment_key=deployment.environment_key;

INSERT INTO graphsync.target_release_activation
    (route_key, ontology_release_id, curated_release_id,
     deployment_id, activated_at, activated_by)
SELECT DISTINCT ON (deployment.route_key)
       deployment.route_key, deployment.ontology_release_id,
       deployment.curated_release_id, deployment.deployment_id,
       coalesce(deployment.finished_at, deployment.started_at),
       coalesce(deployment.approved_by, deployment.requested_by, 'migration')
FROM graphsync.deployment_release deployment
WHERE deployment.route_key IS NOT NULL
  AND deployment.status='active'
ORDER BY deployment.route_key,
         coalesce(deployment.finished_at, deployment.started_at) DESC
ON CONFLICT (route_key) DO UPDATE SET
    ontology_release_id=EXCLUDED.ontology_release_id,
    curated_release_id=EXCLUDED.curated_release_id,
    deployment_id=EXCLUDED.deployment_id,
    activated_at=EXCLUDED.activated_at,
    activated_by=EXCLUDED.activated_by;

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
     '{"targetStore":"graphsync.object_version","businessKeyRequiresReview":true}'::jsonb),
    ('opcenter2607-mfgorder-v1', 'opcenter2607-core', 'MfgOrder',
     'CamstarPRD_SCHEMA', 'MfgOrder', '["MfgOrderId"]'::jsonb,
     '["MfgOrderName"]'::jsonb,
     '["MfgOrderId", "MfgOrderName", "Description", "ProductId", "BeginProductId", "Qty", "OrderStatusId", "ReportingFactoryId", "PlannedStartDateGMT", "PlannedCompletionDateGMT", "LastChangeDate", "ChangeCount"]'::jsonb,
     '["MfgOrderId", "MfgOrderName", "ProductId"]'::jsonb,
     'LastChangeDate', 'core',
     '{"maxErrorRate":0,"maxWarningRate":0.05}'::jsonb,
     '{"targetStore":"graphsync.object_version"}'::jsonb)
ON CONFLICT (contract_key) DO NOTHING;

UPDATE graphsync.data_contract
SET config=(config - 'targetTable') || jsonb_build_object('targetStore', 'graphsync.object_version')
WHERE config ? 'targetTable';

UPDATE graphsync.data_contract
SET config=jsonb_set(config, '{targetStore}', '"graphsync.object_version"'::jsonb, true)
WHERE config->>'targetStore'='camstar_curated.object_version';

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

INSERT INTO graphsync.data_contract_field
    (contract_key, field_key, source_column, target_field, data_type,
     nullable, required, field_role, lifecycle_status, ordinal_position,
     introduced_version, ontology_property, config)
SELECT contract.contract_key,
       contract.contract_key || ':' || lower(source_column.value) AS field_key,
       source_column.value,
       coalesce(property.property_name, source_column.value) AS target_field,
       coalesce(property.data_type, 'String') AS data_type,
       NOT (contract.required_columns ? source_column.value) AS nullable,
       contract.required_columns ? source_column.value AS required,
       CASE
         WHEN contract.primary_key_columns ? source_column.value THEN 'primary_key'
         WHEN contract.business_key_columns ? source_column.value THEN 'business_key'
         WHEN contract.freshness_column = source_column.value THEN 'freshness'
         WHEN property.data_type = 'Navigation' THEN 'navigation'
         ELSE 'attribute'
       END AS field_role,
       'active', source_column.ordinality * 10, contract.version,
       property.property_name,
       jsonb_build_object('seededFromContract', true)
FROM graphsync.data_contract contract
CROSS JOIN LATERAL jsonb_array_elements_text(contract.selected_columns)
    WITH ORDINALITY AS source_column(value, ordinality)
LEFT JOIN LATERAL (
    SELECT mapping.property_name, mapping.data_type
    FROM graphsync.current_property_mapping mapping
    WHERE mapping.class_name=contract.class_name
      AND mapping.physical_column=source_column.value
    ORDER BY mapping.property_name
    LIMIT 1
) property ON true
-- Existing installations may already contain a manually governed field with a
-- different stable key but the same target name.  Either uniqueness identity
-- means the seed is already represented and must not overwrite user work.
ON CONFLICT DO NOTHING;

INSERT INTO graphsync.asset_dependency
    (dependency_id, profile_key, upstream_type, upstream_key,
     downstream_type, downstream_key, dependency_kind, discovered_by, metadata)
SELECT gen_random_uuid(), contract.profile_key, 'data_contract_field', field.field_key,
       'curated_column', contract.config->>'targetTable' || '.' || field.target_field,
       'hard', 'compiler', jsonb_build_object('contractKey', contract.contract_key)
FROM graphsync.data_contract_field field
JOIN graphsync.data_contract contract USING (contract_key)
WHERE contract.config ? 'targetTable'
ON CONFLICT (profile_key, upstream_type, upstream_key, downstream_type, downstream_key)
DO UPDATE SET active=true, last_seen_at=now(), metadata=EXCLUDED.metadata;

INSERT INTO graphsync.alert_rule
    (rule_key, profile_key, metric_key, operator, threshold, severity,
     consecutive_failures, enabled, channels, config)
VALUES
    ('opcenter-release-age', 'opcenter2607-core', 'curated.release_age_minutes',
     'gt', 1440, 'warning', 1, true, '[]'::jsonb,
     '{"description":"治理快照超过24小时未更新"}'::jsonb),
    ('opcenter-release-missing', 'opcenter2607-core', 'curated.release_age_minutes',
     'missing', NULL, 'critical', 1, true, '[]'::jsonb,
     '{"description":"尚无活动治理快照"}'::jsonb),
    ('opcenter-unresolved-relations', 'opcenter2607-core', 'curated.unresolved_relationships',
     'gt', 0, 'critical', 1, true, '[]'::jsonb,
     '{"description":"核心关系存在未解析目标"}'::jsonb),
    ('opcenter-failed-schema-changes', 'opcenter2607-core', 'schema.failed_changes',
     'gt', 0, 'warning', 1, true, '[]'::jsonb,
     '{"description":"Schema 变更执行失败"}'::jsonb),
    ('opcenter-deployment-health', 'opcenter2607-core', 'deployment.failed_recent',
     'gt', 0, 'critical', 1, true, '[]'::jsonb,
     '{"description":"最近 Graph Studio 发布失败"}'::jsonb)
ON CONFLICT (rule_key) DO NOTHING;

-- Remove the two v13 proof-of-concept MfgOrder actions only when they have no
-- audit history.  Real user-defined actions and invocations are never deleted.
DELETE FROM graphsync.action_definition definition
WHERE definition.action_key IN ('camstar.mfgorder.update', 'camstar.mfgorder.release')
  AND NOT EXISTS (
      SELECT 1 FROM graphsync.action_invocation invocation
      WHERE invocation.action_key=definition.action_key
  );

INSERT INTO graphsync.asset_dependency
    (dependency_id, profile_key, upstream_type, upstream_key,
     downstream_type, downstream_key, dependency_kind, discovered_by, metadata)
SELECT gen_random_uuid(), contract.profile_key, 'data_contract_field', field.field_key,
       'ontology_property', contract.class_name || '.' || field.ontology_property,
       'hard', 'compiler', jsonb_build_object('contractKey', contract.contract_key)
FROM graphsync.data_contract_field field
JOIN graphsync.data_contract contract USING (contract_key)
WHERE field.ontology_property IS NOT NULL
ON CONFLICT (profile_key, upstream_type, upstream_key, downstream_type, downstream_key)
DO UPDATE SET active=true, last_seen_at=now(), metadata=EXCLUDED.metadata;

INSERT INTO graphsync.asset_dependency
    (dependency_id, profile_key, upstream_type, upstream_key,
     downstream_type, downstream_key, dependency_kind, discovered_by, metadata)
SELECT gen_random_uuid(), contract.profile_key, 'data_contract_field', field.field_key,
       'graphstudio_predicate', contract.class_name || '.' || field.ontology_property,
       'hard', 'compiler', jsonb_build_object('deployment', 'Opcenter2607')
FROM graphsync.data_contract_field field
JOIN graphsync.data_contract contract USING (contract_key)
WHERE field.ontology_property IS NOT NULL
ON CONFLICT (profile_key, upstream_type, upstream_key, downstream_type, downstream_key)
DO UPDATE SET active=true, last_seen_at=now(), metadata=EXCLUDED.metadata;

INSERT INTO graphsync.asset_dependency
    (dependency_id, profile_key, upstream_type, upstream_key,
     downstream_type, downstream_key, dependency_kind, discovered_by, metadata)
SELECT gen_random_uuid(), relationship.profile_key, 'data_contract_field', field.field_key,
       'relationship_contract', relationship.relationship_contract_key,
       'hard', 'compiler', jsonb_build_object(
           'relationshipName', relationship.relationship_name,
           'side', dependency.side
       )
FROM graphsync.relationship_contract relationship
CROSS JOIN LATERAL (
    SELECT relationship.source_contract_key AS contract_key,
           jsonb_array_elements_text(relationship.source_columns) AS source_column,
           'source'::text AS side
    UNION ALL
    SELECT relationship.target_contract_key,
           jsonb_array_elements_text(relationship.target_columns),
           'target'::text
) dependency
JOIN graphsync.data_contract_field field
  ON field.contract_key=dependency.contract_key
 AND field.source_column=dependency.source_column
ON CONFLICT (profile_key, upstream_type, upstream_key, downstream_type, downstream_key)
DO UPDATE SET active=true, last_seen_at=now(), metadata=EXCLUDED.metadata;

INSERT INTO graphsync.app_setting (setting_key, value, description, editable)
VALUES
    ('product.name', '"Opcenter Graph Sync"'::jsonb, '主页产品名称', true),
    ('workflow.primary', '"camstar-to-graphstudio"'::jsonb, '平台主流程', false),
    ('sync.snapshot_row_threshold', '5000000'::jsonb, '切换到分区增量的建议行数阈值', true),
    ('sync.default_batch_rows', '10000'::jsonb, '流式导出每批最大行数', true),
    ('sync.target_shard_bytes', '67108864'::jsonb, '单个 RDF 分片目标字节数', true),
    ('sync.reference_validation_row_limit', '1000000'::jsonb, '内存引用完整性校验的目标类行数上限', true),
    ('curation.materialization_batch_rows', '10000'::jsonb, '治理物化每批最大行数', true),
    ('curation.release_retention', '3'::jsonb, '每个业务图谱保留的成功治理快照数', true),
    ('health.release_max_age_minutes', '1440'::jsonb, '治理快照最大允许陈旧分钟数', true),
    ('actions.apply_enabled', 'false'::jsonb, '全局 Camstar Action 实际执行开关', true),
    ('sync.retention_success', '3'::jsonb, '成功产物保留数', true),
    ('catalog.retention_ready', '5'::jsonb, '映射目录 ready 快照保留数', true),
    ('ui.default_language', '"zh-CN"'::jsonb, '同步中心默认语言', true)
ON CONFLICT (setting_key) DO NOTHING;

-- The runner must acquire this lock before starting a job:
-- SELECT pg_try_advisory_lock(hashtextextended('graphsync:' || :job_name, 0));
