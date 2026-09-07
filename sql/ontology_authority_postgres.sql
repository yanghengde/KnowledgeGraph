CREATE TABLE IF NOT EXISTS graphsync.physical_model_snapshot (
    snapshot_id text PRIMARY KEY,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS graphsync.semantic_mapping_draft (
    draft_id text PRIMARY KEY,
    snapshot_id text NOT NULL REFERENCES graphsync.physical_model_snapshot(snapshot_id),
    table_name text NOT NULL,
    revision integer NOT NULL DEFAULT 1,
    design jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(snapshot_id,table_name)
);
CREATE TABLE IF NOT EXISTS graphsync.ontology_authority (
    class_name text PRIMARY KEY,
    revision integer NOT NULL,
    domain text NOT NULL,
    model jsonb NOT NULL,
    decision jsonb NOT NULL,
    synced_revision integer,
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS graphsync.ontology_authority_revision (
    class_name text NOT NULL,
    revision integer NOT NULL,
    snapshot jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (class_name, revision)
);
CREATE TABLE IF NOT EXISTS graphsync.ontology_import_proposal (
    proposal_id text PRIMARY KEY,
    content_hash text UNIQUE NOT NULL,
    payload jsonb NOT NULL,
    accepted_classes jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Designer descriptions are reference metadata, never approved business semantics.
-- Keep each English revision alongside its translation for source traceability.
CREATE TABLE IF NOT EXISTS graphsync.designer_description (
    source_key text NOT NULL,
    class_name text NOT NULL,
    field_name text NOT NULL DEFAULT '',
    content_hash text NOT NULL,
    description_en text NOT NULL,
    description_zh text NOT NULL DEFAULT '',
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source_key, class_name, field_name, content_hash)
);
