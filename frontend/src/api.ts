import type {
  ChatSession,
  ChatSessionSummary,
  SavedQuery,
  ServiceStatus,
  StreamEvent,
  SyncConnection,
  SyncJob,
  SyncRun,
  GraphProfile,
  GraphStudioTarget,
  PublicationRoute,
  MaterializationStatus,
  DataSyncStatus,
  DeploymentStatus,
  DeploymentPlan,
  OntologyGovernanceStatus,
  OntologyPresentationInput,
  OntologyValidation,
  SemanticClassDetail,
  SemanticGraphOverview,
  SemanticGraphStats,
  RelationshipSuggestionResult,
} from "./types";

async function requestJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = `请求失败（HTTP ${response.status}）`;
    try {
      const payload = await response.json();
      detail = payload.detail || payload.error || detail;
    } catch {
      // Keep the HTTP fallback message.
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const manufacturingApi = {
  status: (refresh = false) => requestJson<ServiceStatus>(
    `/api/manufacturing-chat/status${refresh ? "?refresh=true" : ""}`,
  ),
  queries: (refresh = false) => requestJson<{ items: SavedQuery[]; count: number }>(
    `/api/manufacturing-chat/queries${refresh ? "?refresh=true" : ""}`,
  ),
  sessions: () => requestJson<{ items: ChatSessionSummary[] }>(
    "/api/manufacturing-chat/sessions?limit=200",
  ),
  session: (id: string) => requestJson<ChatSession>(
    `/api/manufacturing-chat/sessions/${encodeURIComponent(id)}`,
  ),
  createSession: () => requestJson<ChatSession>("/api/manufacturing-chat/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "新建制造问答" }),
  }),
  deleteSession: (id: string) => requestJson<{ status: string }>(
    `/api/manufacturing-chat/sessions/${encodeURIComponent(id)}`,
    { method: "DELETE" },
  ),
};

export const syncApi = {
  connections: () => requestJson<{ items: SyncConnection[] }>("/api/sync/connections"),
  updateConnection: (connection: SyncConnection) => requestJson<SyncConnection>(
    `/api/sync/connections/${encodeURIComponent(connection.connection_key)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: connection.kind,
        display_name: connection.display_name,
        endpoint: connection.endpoint,
        database_name: connection.database_name || null,
        username: connection.username || null,
        enabled: connection.enabled,
        config: connection.config || {},
      }),
    },
  ),
  testConnection: (key: string) => requestJson<{ ok: boolean; detail?: string }>(
    `/api/sync/connections/${encodeURIComponent(key)}/test`, { method: "POST" },
  ),
  testAllConnections: () => requestJson<{ ok: boolean; items: Array<{ connection_key: string; ok: boolean; detail?: string }> }>(
    "/api/sync/connections/test-all", { method: "POST" },
  ),
  jobs: () => requestJson<{ items: SyncJob[] }>("/api/sync/jobs"),
  runs: (limit = 50) => requestJson<{ items: SyncRun[] }>(`/api/sync/runs?limit=${limit}`),
  profiles: () => requestJson<{ items: GraphProfile[] }>("/api/sync/profiles"),
  targets: () => requestJson<{ items: GraphStudioTarget[]; routes: PublicationRoute[] }>("/api/sync/graphstudio-targets"),
  dryRun: (jobName: string) => requestJson<Record<string, unknown>>(
    `/api/sync/jobs/${encodeURIComponent(jobName)}/dry-run`, { method: "POST" },
  ),
  preview: (jobName: string) => requestJson<Record<string, unknown>>(
    `/api/sync/jobs/${encodeURIComponent(jobName)}/preview`, { method: "POST" },
  ),
  materialization: (profileKey: string) => requestJson<MaterializationStatus>(
    `/api/sync/profiles/${encodeURIComponent(profileKey)}/materialization`,
  ),
  dataSync: (profileKey: string) => requestJson<DataSyncStatus>(
    `/api/sync/profiles/${encodeURIComponent(profileKey)}/data-sync`,
  ),
  runDataSync: (profileKey: string, actor: string) => requestJson<{
    ok: boolean; graphStudioMutated: boolean; status: DataSyncStatus;
    materialization: Record<string, unknown>;
  }>(
    `/api/sync/profiles/${encodeURIComponent(profileKey)}/data-sync`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor }),
    },
  ),
  configureDataSync: (
    profileKey: string,
    payload: { enabled: boolean; interval_minutes: number; max_attempts: number; retry_backoff_seconds: number },
  ) => requestJson<{ ok: boolean; schedule: Record<string, unknown> }>(
    `/api/sync/profiles/${encodeURIComponent(profileKey)}/data-sync/schedule`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  ),
  generateRelease: (profileKey: string, actor: string) => requestJson<Record<string, unknown>>(
    `/api/sync/profiles/${encodeURIComponent(profileKey)}/materialization`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ apply: true, activate: false, actor }),
    },
  ),
  activateRelease: (profileKey: string, releaseId: string, actor: string) => requestJson<Record<string, unknown>>(
    `/api/sync/profiles/${encodeURIComponent(profileKey)}/releases/${encodeURIComponent(releaseId)}/activate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor }),
    },
  ),
  rollbackRelease: (profileKey: string, actor: string) => requestJson<Record<string, unknown>>(
    `/api/sync/profiles/${encodeURIComponent(profileKey)}/releases/rollback`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor }),
    },
  ),
  deployments: (profileKey: string) => requestJson<DeploymentStatus>(
    `/api/sync/profiles/${encodeURIComponent(profileKey)}/deployments`,
  ),
  deploymentPlan: (profileKey: string, route: PublicationRoute) => requestJson<DeploymentPlan>(
    `/api/sync/profiles/${encodeURIComponent(profileKey)}/deployments/plan/${route.environment_key}?route_key=${encodeURIComponent(route.route_key)}`,
  ),
  setRouteWriteEnabled: (routeKey: string, applyEnabled: boolean) => requestJson<PublicationRoute>(
    `/api/sync/publication-routes/${encodeURIComponent(routeKey)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ apply_enabled: applyEnabled }),
    },
  ),
  prepareDeployment: (profileKey: string, route: PublicationRoute, actor: string) => requestJson<Record<string, unknown>>(
    `/api/sync/profiles/${encodeURIComponent(profileKey)}/deployments`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ environment_key: route.environment_key, route_key: route.route_key, actor }),
    },
  ),
  approveDeployment: (deploymentId: string, actor: string) => requestJson<Record<string, unknown>>(
    `/api/sync/deployments/${encodeURIComponent(deploymentId)}/approve`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor }),
    },
  ),
  applyDeployment: (deploymentId: string) => requestJson<Record<string, unknown>>(
    `/api/sync/deployments/${encodeURIComponent(deploymentId)}/apply`, { method: "POST" },
  ),
  ontologyGovernance: (profileKey: string) => requestJson<OntologyGovernanceStatus>(
    `/api/sync/ontology-governance?profile_key=${encodeURIComponent(profileKey)}`,
  ),
  addOntologyClass: (workspaceKey: string, input: {
    source_class?: string | null; target_name: string; label?: string; description?: string;
    role?: "core" | "context" | "reference" | "on_demand" | "excluded";
    orphan_policy?: "reject" | "quarantine" | "allow" | "referenced_only";
  }) => requestJson<{ workspaceKey: string; classUid: string; targetName: string }>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/classes`,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) },
  ),
  updateOntologyClass: (workspaceKey: string, classUid: string, input: {
    targetName: string; label?: string; description?: string;
    role: "core" | "context" | "reference" | "on_demand" | "excluded";
    orphanPolicy: "reject" | "quarantine" | "allow" | "referenced_only";
  }) => requestJson<{ ok: boolean }>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/classes/${encodeURIComponent(classUid)}`,
    { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) },
  ),
  removeOntologyClass: (workspaceKey: string, classUid: string) => requestJson<{ ok: boolean }>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/classes/${encodeURIComponent(classUid)}`,
    { method: "DELETE" },
  ),
  updateOntologyPresentation: (workspaceKey: string, classUid: string, input: OntologyPresentationInput) => requestJson<OntologyPresentationInput>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/classes/${encodeURIComponent(classUid)}/presentation`,
    { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) },
  ),
  updateOntologyProperty: (workspaceKey: string, classUid: string, input: {
    uid?: string; propertyKey?: string; sourceName?: string; targetName: string;
    sourcePath?: string; dataType?: string; description?: string; required?: boolean;
    published?: boolean; origin?: "source" | "custom" | "projection";
  }) => requestJson<{ uid: string }>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/classes/${encodeURIComponent(classUid)}/properties`,
    { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) },
  ),
  addOntologyRelationship: (workspaceKey: string, input: {
    relationshipKey?: string; sourceUid: string; targetUid: string; sourceRelationship?: string;
    targetName: string; usage?: "published_link" | "projection_only" | "context_only" | "excluded";
    strength?: "core" | "context" | "weak" | "on_demand"; cardinality?: string;
    requiredContext?: boolean; questionEnabled?: boolean; description?: string;
  }) => requestJson<{ relationshipKey: string }>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/relationships`,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) },
  ),
  removeOntologyRelationship: (workspaceKey: string, relationshipKey: string) => requestJson<{ ok: boolean }>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/relationships/${encodeURIComponent(relationshipKey)}`,
    { method: "DELETE" },
  ),
  relationshipSuggestions: (workspaceKey: string, classUid: string) => requestJson<RelationshipSuggestionResult>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/classes/${encodeURIComponent(classUid)}/relationship-suggestions`,
  ),
  applyRelationshipSuggestions: (workspaceKey: string, classUid: string, suggestionIds: string[]) => requestJson<{
    batchId: string; addedNodeUids: string[]; addedRelationshipKeys: string[]; appliedSuggestionIds: string[];
  }>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/relationship-suggestions/apply`,
    {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ classUid, suggestionIds }),
    },
  ),
  undoRelationshipSuggestionBatch: (workspaceKey: string, batchId: string) => requestJson<{
    batchId: string; removedNodes: number; removedRelationships: number;
  }>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/relationship-suggestion-batches/${encodeURIComponent(batchId)}`,
    { method: "DELETE" },
  ),
  validateOntologyWorkspace: (workspaceKey: string) => requestJson<OntologyValidation>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/validate`,
    { method: "POST" },
  ),
  reviewOntologyWorkspace: (workspaceKey: string, actor: string) => requestJson<OntologyValidation>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/review`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor }),
    },
  ),
  approveOntologyWorkspace: (workspaceKey: string, actor: string) => requestJson<Record<string, unknown>>(
    `/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspaceKey)}/approve`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor }),
    },
  ),
  activateOntologyRelease: (profileKey: string, releaseId: string, actor: string) => requestJson<Record<string, unknown>>(
    `/api/sync/ontology-governance/releases/${encodeURIComponent(releaseId)}/activate?profile_key=${encodeURIComponent(profileKey)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor }),
    },
  ),
};

export const semanticApi = {
  overview: (refresh = false) => requestJson<SemanticGraphOverview>(
    `/api/graph/overview${refresh ? "?refresh=true" : ""}`,
  ),
  stats: (refresh = false) => requestJson<SemanticGraphStats>(
    `/api/stats${refresh ? "?refresh=true" : ""}`,
  ),
  classDetail: (className: string, refresh = false) => requestJson<SemanticClassDetail>(
    `/api/graph/class/${encodeURIComponent(className)}${refresh ? "?refresh=true" : ""}`,
  ),
};

export async function streamManufacturingAnswer(
  input: {
    question: string;
    sessionId: string;
    queryMode: "auto" | "dynamic";
    queryUri?: string;
  },
  onEvent: (event: StreamEvent) => void,
  signal: AbortSignal,
) {
  const response = await fetch("/api/manufacturing-chat/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: input.question,
      session_id: input.sessionId,
      query_mode: input.queryMode,
      query_uri: input.queryUri || null,
    }),
    signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`问答请求失败（HTTP ${response.status}）`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const eventText of events) {
      const line = eventText.split("\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      try {
        onEvent(JSON.parse(line.slice(6)) as StreamEvent);
      } catch {
        // Ignore malformed partial stream events.
      }
    }
  }
}
