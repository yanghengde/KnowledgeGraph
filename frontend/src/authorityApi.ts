export type Property = { name: string; type?: string; description?: string; required?: boolean };
export type ModelClass = { className: string; chineseName?: string; description?: string; properties: Property[]; _semanticMapping?: { draftId: string; snapshotId: string; revision: number; fieldRoles: Record<string, string>; identityColumns: string[] } };
export type Relation = { fromClass: string; toClass: string; relationName: string; cardinality?: string; description?: string; source?: string };
export type AuthorityRow = { className: string; chineseName: string; group: string; sourceCount: number; conflictCount: number; propertyCount: number; revision: number; status: string; pendingCandidateCount: number; primaryKeys: string[] };
export type Directory = { items: AuthorityRow[]; groups: string[]; summary: { classes: number; duplicates: number; conflicts: number; approved: number } };
export type Detail = { className: string; revision: number; fingerprint: string; primaryKeys: string[]; sources: { id: string; definition: ModelClass }[];
  conflicts: { property: string; variants: Record<string, Property>; expectedType?: string; physicalField?: string }[];
  relationships: Relation[]; authority?: { domain: string; model: { class: ModelClass; relationships: Relation[] }; decision: { choices: Record<string, string> } };
  history: { revision: number; created_at: string; snapshot: { domain: string; model: { class: ModelClass; relationships: Relation[] } } }[] };
export type Decision = { preferredSource: string; choices: Record<string, string>; domain: string; fingerprint: string; planHash?: string; chineseName?: string; description?: string };
export type Plan = { planHash: string; model: { class: ModelClass; relationships: Relation[] }; changes: { property: string; before?: Property; after?: Property | null }[]; blockers: string[]; note: string; extensionProperties: string[] };
export type ImportCandidate = { className: string; status: string; selected: boolean; reason: string; descriptionEn: string; descriptionZh: string; propertyCount: number; relationshipCount: number; incomingCount: number; workspace: string };
export type TranslationState = { status: string; metadataStatus: string; completed: number; total: number; warning: string };
export type ImportAnalysis = { importId: string; candidates: ImportCandidate[]; translation: TranslationState };
export type ImportTranslations = { translation: TranslationState; descriptions: Record<string, string>; translations: Record<string, string> };
export type PhysicalEdge = { source: string; target: string; fieldName: string; fieldId: string; targetField: string; isList: boolean; available: boolean };
export type ImportObject = { candidate: ImportCandidate; fields: (Property & { physicalName: string; target: string; primaryKey?: boolean; descriptionEn?: string; descriptionZh?: string })[]; outgoing: PhysicalEdge[]; incoming: PhysicalEdge[]; warning?: string };
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
  standard: (database: string) => request<ImportAnalysis>(`/api/ontology-import/analyze-standard?database=${database}`, {}),
  importTranslations: (id: string) => request<ImportTranslations>(`/api/ontology-import/translation/${id}`),
  retryTranslations: (id: string) => request(`/api/ontology-import/translation/${id}/retry`, {}),
  importObject: (id: string, name: string) => request<ImportObject>(`/api/ontology-import/objects/${id}/${encodeURIComponent(name)}`),
  enrichObject: (id: string, name: string) => request<ImportObject>(`/api/ontology-import/objects/${id}/${encodeURIComponent(name)}/descriptions`, {}),
  stage: (importId: string, selected: string[]) => request<{ message: string }>("/api/ontology-import/apply", { importId, selected }),
};
