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
  status: () => requestJson<ServiceStatus>("/api/manufacturing-chat/status"),
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
