import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, App, Button, Empty, Input, Modal, Segmented, Space, Spin, Tag, Typography } from "antd";
import { syncApi } from "../../api";
import type { OntologyGraph, OntologyWorkspace, RelationshipSuggestion } from "../../types";
import { PublishOntologyCanvas } from "./PublishOntologyCanvas";

type Props = {
  workspace: OntologyWorkspace;
  graph: OntologyGraph;
  selectedId: string;
  mode: "light" | "dark";
  onSelect: (id: string) => void;
  onApplied: (result: { batchId: string; addedNodeUids: string[]; addedRelationshipKeys: string[] }) => Promise<void>;
};

export function OntologyNextSteps({ workspace, graph, selectedId, mode, onSelect, onApplied }: Props) {
  const { message } = App.useApp();
  const [search, setSearch] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [scope, setScope] = useState("direct");
  const [preview, setPreview] = useState<RelationshipSuggestion | null>(null);
  const selected = graph.nodes.find((node) => node.id === selectedId);
  const suggestions = useQuery({
    queryKey: ["ontology-next-steps", workspace.workspace_key, workspace.revision, selectedId],
    queryFn: () => syncApi.relationshipSuggestions(workspace.workspace_key, selectedId),
    enabled: Boolean(selected?.data.sourceClass),
    retry: false,
  });
  const apply = useMutation({
    mutationFn: (item: RelationshipSuggestion) => syncApi.applyRelationshipSuggestions(workspace.workspace_key, selectedId, [item.id]),
    onSuccess: async (result) => {
      setPreview(null);
      message.success(`已加入草稿：${result.addedNodeUids.length} 个对象、${result.addedRelationshipKeys.length} 条关系`);
      await onApplied(result);
    },
    onError: (error: Error) => { message.error(error.message); void suggestions.refetch(); },
  });
  const linked = graph.edges.filter((edge) => edge.source === selectedId || edge.target === selectedId);
  const items = (suggestions.data?.items || []).filter((item) =>
    (scope === "direct" ? item.relationships.length === 1 : item.relationships.length > 1)
    && [item.existingClass, ...item.nodes.map((node) => `${node.sourceClass} ${node.label || ""}`), ...item.relationships.map((rel) => rel.targetName)].join(" ").toLowerCase().includes(search.trim().toLowerCase())
  );
  const previewGraph = useMemo<OntologyGraph | undefined>(() => {
    if (!preview) return undefined;
    const bySource = new Map(graph.nodes.map((node) => [node.data.sourceClass || node.data.targetName, node.id]));
    const pathNames = new Set(preview.nodes.map((node) => node.sourceClass));
    const nodes = graph.nodes.filter((node) => pathNames.has(node.data.sourceClass || node.data.targetName));
    for (const node of preview.missingNodes) {
      const id = `preview::${node.sourceClass}`;
      bySource.set(node.sourceClass, id);
      nodes.push({ id, data: { uid: id, targetName: node.sourceClass, label: node.label, sourceClass: node.sourceClass, role: "context", preview: true } });
    }
    const nodeIds = new Set(nodes.map((node) => node.id));
    const edges = [...graph.edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)), ...preview.missingRelationships.map((rel, index) => ({
      id: `preview-edge::${index}`, source: bySource.get(rel.sourceClass)!, target: bySource.get(rel.targetClass)!,
      data: { relationshipKey: `preview-edge::${index}`, targetName: rel.targetName, preview: true },
    }))];
    return { nodes, edges, properties: graph.properties.filter((property) => nodeIds.has(property.classUid)) };
  }, [preview, graph]);

  return <section className="ontology-next-steps" aria-label="下一步可关联对象">
    <div className="ontology-next-heading"><Typography.Text strong>下一步可关联对象</Typography.Text><Tag color="cyan">{selected?.data.targetName}</Tag></div>
    <Typography.Paragraph type="secondary">选择一个候选预览关联，确认后再加入草稿。推荐依据为来源本体关系，需要业务审阅。</Typography.Paragraph>
    <Segmented block value={scope} onChange={(value) => { setScope(value); setShowAll(false); }} options={[{ value: "direct", label: "直接关联" }, { value: "bridge", label: "通过其他对象关联" }]} />
    <Input.Search aria-label="搜索下一步关联" placeholder="搜索对象、中文名称或关系" value={search} onChange={(event) => { setSearch(event.target.value); setShowAll(false); }} allowClear />
    {!selected?.data.sourceClass ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="自定义对象没有来源关联，可在范围与属性中手动添加关系" />
      : suggestions.isPending ? <div className="ontology-next-loading"><Spin size="small" /> 正在查找关联…</div>
      : suggestions.isError ? <Alert type="error" message="关联推荐加载失败" description={(suggestions.error as Error).message} action={<Button onClick={() => void suggestions.refetch()}>重试</Button>} />
      : !items.length ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={search ? "没有匹配的候选，试试其他关键词" : scope === "direct" ? "暂无待添加的直接关联，可查看已有关联或间接路径" : "暂无通往现有图谱的间接路径"} />
      : <>
        {(showAll ? items : items.slice(0, 5)).map((item) => <div className="ontology-next-item" key={item.id}>
          <div><Typography.Text strong>{item.nodes.find((node) => node.sourceClass === item.existingClass)?.label || item.existingClass}</Typography.Text><Typography.Text type="secondary"> {item.existingClass}</Typography.Text></div>
          <Space size={4} wrap><Tag color={item.missingNodes.length ? "cyan" : "blue"}>{item.missingNodes.length ? "添加对象及关系" : "补充关系"}</Tag>{item.recommended && <Tag color="green">优先推荐</Tag>}</Space>
          {item.relationships.map((rel, index) => <div className="ontology-next-direction" key={index}>{rel.sourceClass} → {rel.targetClass} · {rel.targetName}{rel.physicalColumn ? ` · 字段 ${rel.physicalColumn}` : ""}</div>)}
          <div className="ontology-next-action"><Typography.Text type="secondary">{item.summary}</Typography.Text><Button size="small" onClick={() => setPreview(item)}>预览关联</Button></div>
        </div>)}
        {items.length > 5 && <Button type="link" block onClick={() => setShowAll(!showAll)}>{showAll ? "收起候选" : `查看全部 ${items.length} 个候选`}</Button>}
      </>}
    {linked.length > 0 && <div className="ontology-next-linked"><Typography.Text strong>已有关联 · 点击继续浏览</Typography.Text><Space wrap size={6}>{linked.map((edge) => {
      const target = graph.nodes.find((node) => node.id === (edge.source === selectedId ? edge.target : edge.source));
      return <Button size="small" key={edge.id} onClick={() => target && onSelect(target.id)} title={String(edge.data.targetName || "")}>{edge.source === selectedId ? "→" : "←"} {target?.data.targetName} · {edge.data.targetName}</Button>;
    })}</Space></div>}
    <Modal open={Boolean(preview)} title="预览下一步关联" width={960} destroyOnHidden onCancel={() => { if (!apply.isPending) setPreview(null); }} keyboard={!apply.isPending} maskClosable={!apply.isPending} closable={!apply.isPending}
      footer={<Space><Button disabled={apply.isPending} onClick={() => setPreview(null)}>取消</Button><Button type="primary" loading={apply.isPending} disabled={!preview || workspace.status === "retired"} onClick={() => preview && apply.mutate(preview)}>{workspace.status === "frozen" ? "生成下一版草稿并添加" : "确认加入草稿"}</Button></Space>}>
      <Alert showIcon type="info" message={workspace.status === "frozen" ? "当前模型已冻结；确认后生成下一修订草稿，冻结版本与当前发布保持不变。" : "虚线表示本次拟新增内容，确认前不会写入模型。"} description={`${preview?.summary || ""}。新增对象同时带入来源属性，可在“范围与属性”中调整发布字段。`} />
      <div className="ontology-next-preview"><PublishOntologyCanvas graph={previewGraph} mode={mode} onSelect={() => {}} preview /></div>
      {preview?.relationships.map((rel, index) => <Typography.Paragraph key={index}><strong>{rel.sourceClass} → {rel.targetClass}</strong> · {rel.targetName} · {rel.cardinality || "基数未标注"}{rel.physicalColumn ? ` · 关联字段 ${rel.physicalColumn}` : ""}<br />{rel.description || "来源本体已声明此关联，请确认其适用于当前业务范围。"}</Typography.Paragraph>)}
    </Modal>
  </section>;
}
