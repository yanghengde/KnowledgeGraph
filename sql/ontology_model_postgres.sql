-- Additive migration: no source or legacy release is deleted.
CREATE TABLE IF NOT EXISTS graphsync.ontology_source_snapshot (
    snapshot_id uuid PRIMARY KEY,
    content_hash text UNIQUE NOT NULL,
    payload jsonb NOT NULL,
    provenance jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS graphsync.ontology_source_activation (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    snapshot_id uuid NOT NULL REFERENCES graphsync.ontology_source_snapshot,
    previous_snapshot_id uuid REFERENCES graphsync.ontology_source_snapshot,
    activated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS graphsync.ontology_workspace_document (
    workspace_id uuid PRIMARY KEY REFERENCES graphsync.ontology_workspace ON DELETE CASCADE,
    graph jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS graphsync.ontology_release_document (
    ontology_release_id uuid PRIMARY KEY REFERENCES graphsync.ontology_release,
    graph jsonb NOT NULL,
    document_hash text NOT NULL,
    provenance jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
