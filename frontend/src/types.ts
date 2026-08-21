export type QaRuntimeSnapshot = {
  profileKey: string;
  routeKey: string;
  environmentKey?: string;
  deploymentId: string;
  ontologyReleaseId: string;
  ontologyReleaseNo: number;
  ontologyClassCount: number;
  ontologyRelationshipCount: number;
  curatedReleaseId: string;
  curatedReleaseNo: number;
  objectCount: number;
  relationshipCount: number;
  graphmartUri: string;
  modelUri: string;
  layerUri: string;
  artifactHash: string;
  finishedAt?: string;
  cacheKey: string;
};

export type ServiceStatus = {
  status: string;
  graphstudio: string;
  llm: string;
  graphmart_uri?: string;
  detail?: string;
  runtime?: QaRuntimeSnapshot;
  schema_rows?: number;
};

export type SavedQuery = {
  uri: string;
  title: string;
  description?: string;
  modified?: string;
  forced_limit?: string;
  compatible?: boolean;
  missing_uris?: string[];
  ontology_release_no?: number;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  runtime?: QaRuntimeSnapshot;
};

export type ChatSessionSummary = {
  id: string;
  title: string;
  preview?: string;
  updated_at?: string;
  message_count?: number;
};

export type ChatSession = ChatSessionSummary & {
  messages: ChatMessage[];
  runtime?: QaRuntimeSnapshot;
};

export type StreamEvent = {
  type: "status" | "chunk" | "error" | "done";
  content?: string;
  session_id?: string;
  session_title?: string;
  runtime?: QaRuntimeSnapshot;
};

export type SyncConnection = {
  connection_key: string;
  kind: string;
  display_name: string;
  endpoint: string;
  database_name?: string | null;
  username?: string | null;
  secret_ref?: string | null;
  secret_configured?: boolean;
  enabled: boolean;
  status: string;
  last_tested_at?: string | null;
  last_error?: string | null;
  editable: boolean;
  config: Record<string, unknown>;
};

export type SyncJob = {
  job_name: string;
  title: string;
  description?: string;
  graphmart_uri?: string;
  mode: string;
  schedule?: string | null;
  timezone: string;
  enabled: boolean;
  retention_success: number;
  config: Record<string, unknown>;
  scopes?: Array<{ scope_key: string; layer_title: string; enabled: boolean }>;
};

export type SyncRun = {
  run_id: string;
  job_name: string;
  status: string;
  trigger_type: string;
  started_at?: string | null;
  finished_at?: string | null;
  row_count?: number | null;
  triple_count?: number | null;
  error?: string | null;
  metrics?: Record<string, unknown>;
};

export type GraphProfile = {
  profile_key: string;
  title: string;
  description?: string;
  enabled: boolean;
  max_depth: number;
  max_total_nodes_per_run: number;
};

export type GraphStudioTarget = {
  target_key: string;
  title: string;
  graphmart_uri: string;
  connection_key: string;
  description?: string;
  enabled: boolean;
};

export type PublicationRoute = {
  route_key: string;
  profile_key: string;
  environment_key: "dev" | "uat" | "prod";
  target_key: string;
  target_title?: string;
  title: string;
  promotion_order: number;
  graphmart_uri?: string;
  apply_enabled: boolean;
  requires_approval: boolean;
  enabled: boolean;
};

export type CuratedRelease = {
  release_id: string;
  release_no: number;
  status: string;
  preview_only: boolean;
  source_rows_read: number;
  object_count: number;
  relationship_count: number;
  quarantine_count: number;
  content_hash: string;
  started_at?: string | null;
  finished_at?: string | null;
  error?: unknown;
  is_active: boolean;
};

export type MaterializationPlan = {
  profileKey: string;
  ready: boolean;
  blockers: string[];
  batchRows: number;
  strategy: string;
  activation: string;
  rollback: string;
  activeReleaseId?: string | null;
  contracts: Array<Record<string, unknown>>;
  relationships: string[];
};

export type MaterializationStatus = {
  plan: MaterializationPlan;
  releases: CuratedRelease[];
};

export type DeploymentRelease = {
  deployment_id: string;
  environment_key: "dev" | "uat" | "prod";
  route_key: string;
  curated_release_id: string;
  status: string;
  ontology_release_id?: string | null;
  slot: "blue" | "green";
  artifact_uri?: string | null;
  artifact_hash?: string | null;
  dataset_uri?: string | null;
  layer_uri?: string | null;
  step_uri?: string | null;
  approved_by?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | { message?: string; retryable?: boolean; stage?: string } | null;
};

export type DeploymentStatus = {
  environments: PublicationRoute[];
  routes: PublicationRoute[];
  targets: GraphStudioTarget[];
  deployments: DeploymentRelease[];
  activeCuratedRelease?: CuratedRelease | null;
  activeOntologyRelease?: OntologyRelease | null;
};

export type DeploymentPlan = {
  profileKey: string;
  routeKey: string;
  targetKey: string;
  environment: PublicationRoute;
  release?: CuratedRelease | null;
  ontologyRelease?: Record<string, unknown> | null;
  slot: "blue" | "green";
  ready: boolean;
  blockers: string[];
  applyEnabled: boolean;
  approvalRequired: boolean;
  previousDeploymentId?: string | null;
  strategy: string;
};

export type OntologyWorkspace = {
  workspace_id: string;
  workspace_key: string;
  profile_key: string;
  title: string;
  status: "draft" | "reviewed" | "frozen" | string;
  revision: number;
  graph_database: string;
  created_by?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  updated_at?: string | null;
  config?: Record<string, unknown>;
};

export type OntologyClass = {
  uid: string;
  targetName: string;
  sourceClass?: string | null;
  role: "core" | "context" | "excluded" | string;
  orphanPolicy?: string | null;
  origin?: string | null;
  published?: boolean;
  description?: string | null;
  [key: string]: unknown;
};

export type OntologyProperty = {
  uid: string;
  classUid: string;
  targetName: string;
  sourceName?: string | null;
  dataType?: string | null;
  origin?: string | null;
  description?: string | null;
  published?: boolean;
  required?: boolean;
  sourcePath?: string | null;
  [key: string]: unknown;
};

export type OntologyRelationship = {
  relationshipKey: string;
  targetName?: string | null;
  usage?: string | null;
  cardinality?: string | null;
  requiredContext?: boolean;
  origin?: string | null;
  [key: string]: unknown;
};

export type OntologyGraph = {
  nodes: Array<{ id: string; data: OntologyClass }>;
  edges: Array<{ id: string; source: string; target: string; data: OntologyRelationship }>;
  properties: OntologyProperty[];
};

export type RelationshipSuggestion = {
  id: string;
  anchorClass: string;
  existingClass: string;
  nodes: Array<{ sourceClass: string; label?: string; description?: string }>;
  relationships: Array<{
    sourceClass: string; targetClass: string; targetName: string;
    cardinality?: string; description?: string;
  }>;
  missingNodes: Array<{ sourceClass: string; label?: string; description?: string }>;
  missingRelationships: Array<{
    sourceClass: string; targetClass: string; targetName: string;
    cardinality?: string; description?: string;
  }>;
  score: number;
  summary: string;
  recommended: boolean;
};

export type RelationshipSuggestionResult = {
  classUid: string;
  sourceClass?: string | null;
  items: RelationshipSuggestion[];
  reason?: string | null;
};

export type OntologyRelease = {
  ontology_release_id: string;
  release_no: number;
  status: "approved" | "active" | "superseded" | string;
  content_hash: string;
  class_count: number;
  property_count: number;
  relationship_count: number;
  approved_by?: string | null;
  activated_at?: string | null;
  created_at?: string | null;
};

export type OntologyValidation = {
  valid: boolean;
  errors: Array<{ code: string; message: string }>;
  warnings: Array<{ code: string; message: string }>;
  contentHash: string;
  counts: { classes: number; properties: number; relationships: number };
};

export type OntologyGovernanceStatus = {
  database: string;
  sourceDatabase: string;
  workspaces: OntologyWorkspace[];
  currentWorkspace?: OntologyWorkspace | null;
  graph: OntologyGraph;
  releases: OntologyRelease[];
  activeRelease?: OntologyRelease | null;
  activeReleaseGraph?: Record<string, unknown>;
};

export type SemanticGraphNode = {
  id: string;
  data: {
    label: string;
    chineseName?: string;
    description?: string;
    layer?: string;
    propertyCount: number;
    module: string;
    type: string;
  };
};

export type SemanticGraphEdge = {
  id?: string;
  source: string;
  target: string;
  data: {
    label?: string;
    cardinality?: string;
    lineStyle?: string;
  };
};

export type SemanticGraphOverview = {
  nodes: SemanticGraphNode[];
  edges: SemanticGraphEdge[];
  combos: Array<{ id: string; data: { label: string } }>;
};

export type SemanticClassDetail = {
  className: string;
  properties: Array<{ name: string; dataType?: string; description?: string }>;
  outgoing: Array<{ targetClass: string; relName?: string; cardinality?: string; description?: string }>;
  incoming: Array<{ sourceClass: string; relName?: string; cardinality?: string; description?: string }>;
};

export type SemanticGraphStats = {
  classCount: number;
  propertyCount: number;
  relationCount: number;
};
