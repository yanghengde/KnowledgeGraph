export type ServiceStatus = {
  status: string;
  graphstudio: string;
  llm: string;
  graphmart_uri?: string;
  detail?: string;
};

export type SavedQuery = {
  uri: string;
  title: string;
  description?: string;
  modified?: string;
  forced_limit?: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
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
};

export type StreamEvent = {
  type: "status" | "chunk" | "error" | "done";
  content?: string;
  session_id?: string;
  session_title?: string;
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
  apply_enabled: boolean;
  requires_approval: boolean;
  enabled: boolean;
};
