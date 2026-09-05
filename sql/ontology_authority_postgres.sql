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
