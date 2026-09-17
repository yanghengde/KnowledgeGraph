type Draft = { draftId: string; snapshotId: string; revision: number };
type Mapping = { draftId?: string; snapshotId?: string; revision?: number };

export function modelRevisionState(draft: Draft, mapping?: Mapping): string {
  if (!mapping?.draftId || !mapping.snapshotId || mapping.revision === undefined) return "版本待核实";
  if (mapping.draftId !== draft.draftId || mapping.snapshotId !== draft.snapshotId) return "来源版本不同";
  if (mapping.revision === draft.revision) return "与草稿一致";
  if (mapping.revision < draft.revision) return "草稿有新修改";
  return "版本待核实";
}
