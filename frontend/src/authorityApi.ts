export type Property = { name: string; type?: string; description?: string; required?: boolean };
export type ModelClass = { className: string; chineseName?: string; description?: string; properties: Property[] };
export type Relation = { fromClass: string; toClass: string; relationName: string; cardinality?: string; description?: string; source?: string };
export type AuthorityRow = { className: string; chineseName: string; group: string; sourceCount: number; conflictCount: number; propertyCount: number; revision: number; status: string; pendingCandidateCount: number; primaryKeys: string[] };
export type Directory = { items: AuthorityRow[]; groups: string[]; summary: { classes: number; duplicates: number; conflicts: number; approved: number } };
export type Detail = { className: string; revision: number; fingerprint: string; primaryKeys: string[]; sources: { id: string; definition: ModelClass }[];
  conflicts: { property: string; variants: Record<string, Property>; expectedType?: string; physicalField?: string }[];
  relationships: Relation[]; authority?: { domain: string; model: { class: ModelClass; relationships: Relation[] }; decision: { choices: Record<string, string> } };
  history: { revision: number; created_at: string; snapshot: { domain: string; model: { class: ModelClass; relationships: Relation[] } } }[] };
export type Decision = { preferredSource: string; choices: Record<string, string>; domain: string; fingerprint: string; planHash?: string; chineseName?: string; description?: string };
export type Plan = { planHash: string; model: { class: ModelClass; relationships: Relation[] }; changes: { property: string; before?: Property; after: Property }[]; blockers: string[]; note: string; extensionProperties: string[] };
export type ImportAnalysis = { importId: string; candidates: { className: string; status: string; selected: boolean; reason: string }[] };
async function request<T>(path: string, body?: unknown, form?: FormData): Promise<T> {
  const response = await fetch(path, form ? { method: "POST", body: form } : body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : undefined);
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "请求未完成，请检查输入或稍后重试");
  return data;
}
const path = (name: string) => `/api/ontology-authority/classes/${encodeURIComponent(name)}`;
export const authorityApi = {
  directory: () => request<Directory>("/api/ontology-authority"),
  detail: (name: string) => request<Detail>(path(name)),
  preview: (name: string, body: Decision) => request<Plan>(`${path(name)}/preview`, body),
  approve: (name: string, body: Decision) => request<{ revision: number }>(`${path(name)}/approve`, body),
  sync: (name: string, revision: number) => request(`${path(name)}/sync`, { revision }),
  analyze: (form: FormData) => request<ImportAnalysis>("/api/ontology-import/analyze", undefined, form),
  stage: (importId: string, selected: string[]) => request<{ message: string }>("/api/ontology-import/apply", { importId, selected }),
};
