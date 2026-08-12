-- Graph Studio sync control plane. This database stores orchestration state only;
-- Camstar business rows remain in SQL Server and RDF data remains in Graph Studio.

CREATE SCHEMA IF NOT EXISTS graphsync;

CREATE TABLE IF NOT EXISTS graphsync.job (
    job_name              text PRIMARY KEY,
    graphmart_uri         text NOT NULL,
    mode                  text NOT NULL CHECK (mode IN ('atomic_snapshot', 'partitioned_incremental')),
    schedule              text,
    enabled               boolean NOT NULL DEFAULT true,
    config                jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS graphsync.run (
    run_id                uuid PRIMARY KEY,
    job_name              text NOT NULL REFERENCES graphsync.job(job_name),
    status                text NOT NULL CHECK (
                              status IN ('started', 'extracting', 'staged', 'loading',
                                         'verifying', 'succeeded', 'failed', 'cancelled')
                          ),
    trigger_type          text NOT NULL DEFAULT 'scheduled',
    started_at            timestamptz NOT NULL DEFAULT now(),
    finished_at           timestamptz,
    source_high_watermark jsonb,
    ontology_hash         text,
    manifest_hash         text,
    row_count             bigint NOT NULL DEFAULT 0,
    triple_count          bigint NOT NULL DEFAULT 0,
    error                 jsonb,
    metrics               jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_graphsync_run_job_started
    ON graphsync.run (job_name, started_at DESC);

CREATE TABLE IF NOT EXISTS graphsync.checkpoint (
    job_name              text NOT NULL REFERENCES graphsync.job(job_name),
    partition_key         text NOT NULL,
    committed_watermark   jsonb NOT NULL,
    source_schema_hash    text,
    committed_run_id      uuid NOT NULL REFERENCES graphsync.run(run_id),
    committed_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (job_name, partition_key)
);

CREATE TABLE IF NOT EXISTS graphsync.artifact (
    artifact_id           uuid PRIMARY KEY,
    run_id                uuid NOT NULL REFERENCES graphsync.run(run_id) ON DELETE CASCADE,
    artifact_type         text NOT NULL CHECK (
                              artifact_type IN ('manifest', 'rdf_archive', 'model',
                                                'dataset', 'layer', 'step', 'verification')
                          ),
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

-- Optional. Only populate this table for sources without Change Tracking/CDC when
-- per-row hash comparison is required for incremental deletion detection.
CREATE TABLE IF NOT EXISTS graphsync.row_state (
    job_name              text NOT NULL REFERENCES graphsync.job(job_name),
    partition_key         text NOT NULL,
    entity_uri            text NOT NULL,
    row_hash              text NOT NULL,
    last_seen_run_id      uuid NOT NULL REFERENCES graphsync.run(run_id),
    last_seen_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (job_name, partition_key, entity_uri)
);

-- Runners should acquire this transaction-scoped lock before starting a job:
-- SELECT pg_try_advisory_lock(hashtextextended('graphsync:' || :job_name, 0));
-- Release it after the terminal run state is persisted:
-- SELECT pg_advisory_unlock(hashtextextended('graphsync:' || :job_name, 0));

INSERT INTO graphsync.job (job_name, graphmart_uri, mode, schedule)
VALUES (
    'camstar-full',
    'http://cambridgesemantics.com/Graphmart/ba6308d1b3764b8a8ad40d90500ddd56',
    'atomic_snapshot',
    '0 * * * *'
)
ON CONFLICT (job_name) DO NOTHING;
