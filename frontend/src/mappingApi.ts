export type SourceRole = "pending" | "entity" | "event" | "relationship" | "auxiliary" | "excluded";
export type FieldRole = "pending" | "property" | "relationship" | "internal" | "excluded";
export type SourceDesign = { role: SourceRole; chineseName: string; description: string; notes: string; fields: Record<string, FieldRole> };
export type MappingRow = { draftId: string; snapshotId: string; tableName: string; revision: number; role: SourceRole; chineseName: string };
export type MappingField = { name: string; physicalName: string; type: string; target: string; primaryKey: boolean };
export type MappingDetail = MappingRow & { design: SourceDesign; fields: MappingField[]; tableNames: string[] };
export type MappingPreview = { planHash: string; blockers: string[]; counts: { properties: number; relationships: number; internal: number; excluded: number } };
export type SimpleCheck = MappingPreview & { revision: number; fields: { name: string; type: string }[]; removedFields: string[] };
async function request<T>(path = "", body?: unknown): Promise<T> {
  const response = await fetch(`/api/semantic-mapping${path}`, body === undefined ? undefined : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "来源设计请求失败，请检查输入或连接");
  return data;
}
export const mappingApi = {
  openPhysical: () => request<import("./authorityApi").ImportAnalysis & { database: string; snapshotId: string }>("/physical/open", {}),
  check: (id: string, workspaceKey: string) => request<SimpleCheck>(`/${id}/check`, { workspaceKey }),
  ready: (id: string, workspaceKey: string, revision: number, planHash: string) => request(`/${id}/ready`, { workspaceKey, revision, planHash }),
  physicalVersions: () => request<{ items: { snapshotId: string; createdAt: string; tableCount: number }[] }>("/physical/versions"),
  restorePhysical: (snapshotId: string, database: string) => request<import("./authorityApi").ImportAnalysis>("/physical/restore", { snapshotId, database }),
  addSources: (importId: string, selected: string[]) => request("/sources", { importId, selected }),
  list: () => request<{ items: MappingRow[] }>(),
  deleted: () => request<{ items: MappingRow[] }>("?deleted=true"),
  remove: (id: string, revision: number, deleted = true) => request(`/${id}/delete`, { revision, deleted }),
  detail: (id: string) => request<MappingDetail>(`/${id}`),
  save: (id: string, revision: number, design: SourceDesign) => request<MappingDetail>(`/${id}/save`, { revision, design }),
  preview: (id: string) => request<MappingPreview>(`/${id}/preview`, {}),
  submit: (id: string, revision: number, planHash: string) => request(`/${id}/submit`, { revision, planHash }),
};
