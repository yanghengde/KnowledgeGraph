-- Camstar -> Graph Studio control plane.
-- This schema stores orchestration metadata only; source business data remains
-- in the Camstar SQL Server/Oracle source and published RDF remains in Graph Studio.

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

INSERT INTO graphsync.menu_item
    (menu_key, label_zh, label_en, route, icon, sort_order, enabled, capability)
VALUES
    ('overview',    '总览',     'Overview',    '#overview',    'dashboard', 10, true,  'sync.read'),
    ('connections', '连接管理', 'Connections', '#connections', 'plug',      20, true,  'connection.read'),
    ('jobs',        '同步任务', 'Sync Jobs',   '#jobs',        'schedule',  30, true,  'job.read'),
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

INSERT INTO graphsync.app_setting (setting_key, value, description, editable)
VALUES
    ('product.name', '"Opcenter Graph Sync"'::jsonb, '主页产品名称', true),
    ('workflow.primary', '"camstar-to-graphstudio"'::jsonb, '平台主流程', false),
    ('sync.snapshot_row_threshold', '5000000'::jsonb, '切换到分区增量的建议行数阈值', true),
    ('sync.retention_success', '3'::jsonb, '成功产物保留数', true),
    ('catalog.retention_ready', '5'::jsonb, '映射目录 ready 快照保留数', true),
    ('ui.default_language', '"zh-CN"'::jsonb, '同步中心默认语言', true)
ON CONFLICT (setting_key) DO NOTHING;

-- The runner must acquire this lock before starting a job:
-- SELECT pg_try_advisory_lock(hashtextextended('graphsync:' || :job_name, 0));
