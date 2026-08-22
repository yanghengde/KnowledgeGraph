import {
  ApartmentOutlined, BranchesOutlined, CheckCircleFilled, CheckCircleOutlined,
  DeleteOutlined, FileProtectOutlined, LinkOutlined, PlusOutlined, SearchOutlined,
  SendOutlined, TagsOutlined, WarningOutlined,
} from "@ant-design/icons";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Alert, App, Button, Card, Checkbox, Descriptions, Drawer, Empty, Form, Input, Modal, Popconfirm, Progress,
  Segmented, Select, Space, Steps, Switch, Table, Tag, Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { syncApi } from "../api";
import { PublishOntologyCanvas } from "./PublishOntologyCanvas";
import { OntologyPresentationPanel } from "./OntologyPresentationPanel";
import { useThemeMode } from "../theme";
import type {
  OntologyClass, OntologyGovernanceStatus, OntologyProperty, OntologyRelease,
  OntologyValidation, RelationshipSuggestion, RelationshipSuggestionResult, SemanticGraphOverview,
} from "../types";

type View = "workspace" | "validation" | "versions";
type Props = {
  view: View;
  governance?: OntologyGovernanceStatus;
  loading?: boolean;
  sourceGraph?: SemanticGraphOverview;
  onLocateSource: (className: string) => void;
};
type Operation = { kind: "review" | "approve" | "activate"; title: string; description: string; phrase?: string; release?: OntologyRelease };
type FrozenGraph = {
  classes: Array<{ class: OntologyClass & { sourceUid?: string }; properties: OntologyProperty[] }>;
  relationships: Array<{ source: OntologyClass; target: OntologyClass; relation: { targetName?: string; relationshipKey?: string } }>;
};

const roleLabels: Record<string, { text: string; color: string }> = {
  core: { text: "核心对象", color: "cyan" }, context: { text: "上下文对象", color: "geekblue" },
  reference: { text: "参考对象", color: "purple" }, on_demand: { text: "按需对象", color: "gold" }, excluded: { text: "不发布", color: "default" },
};
const releaseLabels: Record<string, { text: string; color: string }> = {
  active: { text: "当前活动版本", color: "success" }, approved: { text: "已批准待激活", color: "processing" }, superseded: { text: "历史版本", color: "default" },
};

function formatTime(value?: string | null) {
  return value ? new Date(value).toLocaleString("zh-CN") : "—";
}

export function OntologyWorkspacePanel({ view, governance, loading, sourceGraph, onLocateSource }: Props) {
  const { mode } = useThemeMode();
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const workspace = governance?.currentWorkspace;
  const graph = governance?.graph;
  const activeRelease = governance?.activeRelease;
  const pendingRelease = governance?.releases.find((item) =>
    item.status === "approved"
    && item.release_no > (activeRelease?.release_no || 0)
  );
  const [selectedId, setSelectedId] = useState("");
  const [search, setSearch] = useState("");
  const [propertySearch, setPropertySearch] = useState("");
  const [validation, setValidation] = useState<OntologyValidation | null>(null);
  const [operation, setOperation] = useState<Operation | null>(null);
  const [actor, setActor] = useState("local-console");
  const [confirmation, setConfirmation] = useState("");
  const [modelView, setModelView] = useState<"preview" | "scope" | "presentation" | "diff">("preview");
  const [createClassOpen, setCreateClassOpen] = useState(false);
  const [createPropertyOpen, setCreatePropertyOpen] = useState(false);
  const [createRelationshipOpen, setCreateRelationshipOpen] = useState(false);
  const [suggestionOpen, setSuggestionOpen] = useState(false);
  const [suggestionResult, setSuggestionResult] = useState<RelationshipSuggestionResult | null>(null);
  const [selectedSuggestionIds, setSelectedSuggestionIds] = useState<string[]>([]);
  const [lastSuggestionBatch, setLastSuggestionBatch] = useState<{ id: string; nodes: number; relationships: number } | null>(null);
  const [classForm] = Form.useForm();
  const [propertyForm] = Form.useForm();
  const [relationshipForm] = Form.useForm();

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["ontology-governance", "opcenter2607-core"] });
  };
  useEffect(() => {
    if (!graph?.nodes.some((node) => node.id === selectedId)) setSelectedId(graph?.nodes[0]?.id || "");
  }, [graph?.nodes, selectedId]);
  const openRelationshipEditor = () => {
    relationshipForm.resetFields();
    relationshipForm.setFieldsValue({ sourceUid: selectedId || undefined, cardinality: "many-to-one", strength: "context" });
    setCreateRelationshipOpen(true);
  };

  const selectedNode = graph?.nodes.find((node) => node.id === selectedId);
  const modelSourceNames = useMemo(() => new Set((graph?.nodes || []).map((node) => node.data.sourceClass || node.data.targetName)), [graph?.nodes]);
  const sourceNode = sourceGraph?.nodes.find((node) => node.id === (selectedNode?.data.sourceClass || selectedNode?.data.targetName));
  const suggestions = useMemo(() => {
    if (!sourceGraph || !sourceNode) return [];
    const neighborIds = new Set<string>();
    sourceGraph.edges.forEach((edge) => {
      if (edge.source === sourceNode.id) neighborIds.add(edge.target);
      if (edge.target === sourceNode.id) neighborIds.add(edge.source);
    });
    return sourceGraph.nodes.filter((node) => neighborIds.has(node.id) && !modelSourceNames.has(node.id)).slice(0, 16);
  }, [modelSourceNames, sourceGraph, sourceNode]);
  const selectedAllProperties = useMemo(() => (graph?.properties || []).filter((item) => item.classUid === selectedId), [graph?.properties, selectedId]);
  const selectedProperties = useMemo(() => {
    const keyword = propertySearch.trim().toLocaleLowerCase();
    return selectedAllProperties.filter((item) => !keyword || [item.targetName, item.sourceName, item.dataType].some((value) => String(value || "").toLocaleLowerCase().includes(keyword)));
  }, [propertySearch, selectedAllProperties]);
  const filteredNodes = useMemo(() => {
    const keyword = search.trim().toLocaleLowerCase();
    return (graph?.nodes || []).filter((node) => !keyword || [node.data.targetName, node.data.sourceClass, node.data.description].some((value) => String(value || "").toLocaleLowerCase().includes(keyword)));
  }, [graph?.nodes, search]);
  const incidentRelationships = useMemo(() => (graph?.edges || []).filter((edge) => edge.source === selectedId || edge.target === selectedId), [graph?.edges, selectedId]);
  const modelDiff = useMemo(() => {
    const frozen = (governance?.activeReleaseGraph || { classes: [], relationships: [] }) as unknown as FrozenGraph;
    const activeBySource = new Map((frozen.classes || []).map((item) => [item.class.sourceClass || item.class.targetName, item]));
    const draftBySource = new Map((graph?.nodes || []).map((item) => [item.data.sourceClass || item.data.targetName, item]));
    const added = [...draftBySource.keys()].filter((name) => !activeBySource.has(name));
    const removed = [...activeBySource.keys()].filter((name) => !draftBySource.has(name));
    const modified = [...draftBySource.keys()].filter((name) => {
      const active = activeBySource.get(name); const draft = draftBySource.get(name);
      if (!active || !draft) return false;
      const activeProperties = new Set(active.properties.filter((item) => item.published !== false).map((item) => item.targetName));
      const draftProperties = new Set((graph?.properties || []).filter((item) => item.classUid === draft.id && item.published !== false).map((item) => item.targetName));
      return active.class.role !== draft.data.role || activeProperties.size !== draftProperties.size || [...activeProperties].some((property) => !draftProperties.has(property));
    });
    const draftNames = new Map((graph?.nodes || []).map((item) => [item.id, item.data.sourceClass || item.data.targetName]));
    const draftRelationships = new Set((graph?.edges || []).map((edge) => `${draftNames.get(edge.source)}\0${edge.data.targetName || edge.data.relationshipKey}\0${draftNames.get(edge.target)}`));
    const activeRelationships = new Set((frozen.relationships || []).map((item) => `${item.source.sourceClass || item.source.targetName}\0${item.relation.targetName || item.relation.relationshipKey}\0${item.target.sourceClass || item.target.targetName}`));
    const addedRelationships = [...draftRelationships].filter((key) => !activeRelationships.has(key));
    const removedRelationships = [...activeRelationships].filter((key) => !draftRelationships.has(key));
    return { added, removed, modified, addedRelationships, removedRelationships, activeClassCount: activeBySource.size, activeRelationshipCount: activeRelationships.size };
  }, [governance?.activeReleaseGraph, graph]);

  const addClass = useMutation({
    mutationFn: (className: string) => syncApi.addOntologyClass(workspace!.workspace_key, { source_class: className, target_name: className, role: "context", orphan_policy: "quarantine" }),
    onSuccess: async (_, className) => { message.success(`${className} 已加入当前发布模型`); await refresh(); },
    onError: (error: Error) => message.error(error.message),
  });
  const addAllSuggestions = useMutation({
    mutationFn: async () => {
      for (const item of suggestions) await syncApi.addOntologyClass(workspace!.workspace_key, { source_class: item.id, target_name: item.id, role: "context", orphan_policy: "quarantine" });
      return suggestions.length;
    },
    onSuccess: async (count) => { message.success(`已补充 ${count} 个一跳依赖对象`); await refresh(); },
    onError: (error: Error) => message.error(error.message),
  });
  const createCustomClass = useMutation({
    mutationFn: (values: { targetName: string; label?: string; description?: string; role: "core" | "context" | "reference" | "on_demand"; orphanPolicy: "reject" | "quarantine" | "allow" | "referenced_only" }) => syncApi.addOntologyClass(workspace!.workspace_key, {
      source_class: null, target_name: values.targetName.trim(), label: values.label?.trim(),
      description: values.description?.trim(), role: values.role, orphan_policy: values.orphanPolicy,
    }),
    onSuccess: async (result) => {
      message.success(`${result.targetName} 已作为自定义发布对象加入草稿`);
      setCreateClassOpen(false); classForm.resetFields(); await refresh(); setSelectedId(result.classUid);
    },
    onError: (error: Error) => message.error(error.message),
  });
  const createCustomProperty = useMutation({
    mutationFn: (values: { targetName: string; dataType: string; description?: string; required?: boolean }) => syncApi.updateOntologyProperty(workspace!.workspace_key, selectedId, {
      propertyKey: values.targetName.trim(), sourceName: values.targetName.trim(), targetName: values.targetName.trim(),
      dataType: values.dataType, description: values.description?.trim(), required: Boolean(values.required),
      published: true, origin: "custom",
    }),
    onSuccess: async () => {
      message.success("自定义属性已写入发布本体草稿");
      setCreatePropertyOpen(false); propertyForm.resetFields(); await refresh();
    },
    onError: (error: Error) => message.error(error.message),
  });
  const createCustomRelationship = useMutation({
    mutationFn: (values: { sourceUid: string; targetUid: string; targetName: string; cardinality: string; strength: "core" | "context" | "weak" | "on_demand"; description?: string }) => syncApi.addOntologyRelationship(workspace!.workspace_key, {
      sourceUid: values.sourceUid, targetUid: values.targetUid, sourceRelationship: values.targetName.trim(),
      targetName: values.targetName.trim(), cardinality: values.cardinality, strength: values.strength,
      usage: "published_link", description: values.description?.trim(),
    }),
    onSuccess: async () => {
      message.success("自定义发布关系已写入草稿");
      setCreateRelationshipOpen(false); relationshipForm.resetFields(); await refresh();
    },
    onError: (error: Error) => message.error(error.message),
  });
  const removeClass = useMutation({
    mutationFn: (classUid: string) => syncApi.removeOntologyClass(workspace!.workspace_key, classUid),
    onSuccess: async () => { message.success("对象已移出当前发布模型"); await refresh(); },
    onError: (error: Error) => message.error(error.message),
  });
  const updateClass = useMutation({
    mutationFn: ({ item, role }: { item: OntologyClass; role: "core" | "context" | "reference" | "on_demand" | "excluded" }) => syncApi.updateOntologyClass(workspace!.workspace_key, item.uid, {
      targetName: item.targetName, label: String(item.label || item.targetName), description: String(item.description || ""), role,
      orphanPolicy: (item.orphanPolicy || "quarantine") as "reject" | "quarantine" | "allow" | "referenced_only",
    }),
    onSuccess: async () => { message.success("对象发布角色已更新"); await refresh(); },
    onError: (error: Error) => message.error(error.message),
  });
  const updateProperty = useMutation({
    mutationFn: ({ item, changes }: { item: OntologyProperty; changes: Partial<Pick<OntologyProperty, "published" | "required">> }) => syncApi.updateOntologyProperty(workspace!.workspace_key, item.classUid, {
      uid: item.uid, propertyKey: item.sourceName || item.targetName, sourceName: item.sourceName || item.targetName,
      targetName: item.targetName, sourcePath: item.sourcePath || "", dataType: item.dataType || "String",
      description: item.description || "", required: changes.required ?? item.required ?? false,
      published: changes.published ?? item.published ?? true, origin: (item.origin || "source") as "source" | "custom" | "projection",
    }),
    onSuccess: async () => { await refresh(); },
    onError: (error: Error) => message.error(error.message),
  });
  const syncRelationships = useMutation({
    mutationFn: async () => {
      if (!sourceGraph || !graph || !workspace) return 0;
      const bySource = new Map(graph.nodes.map((node) => [node.data.sourceClass || node.data.targetName, node.id]));
      const existing = new Set(graph.edges.map((edge) => `${edge.source}\0${edge.data.targetName || edge.data.relationshipKey}\0${edge.target}`));
      let count = 0;
      for (const edge of sourceGraph.edges) {
        const sourceUid = bySource.get(edge.source); const targetUid = bySource.get(edge.target); const label = edge.data.label || "RELATED_TO";
        if (!sourceUid || !targetUid || existing.has(`${sourceUid}\0${label}\0${targetUid}`)) continue;
        await syncApi.addOntologyRelationship(workspace.workspace_key, { sourceUid, targetUid, sourceRelationship: label, targetName: label, cardinality: edge.data.cardinality || "many-to-one", strength: "context", usage: "published_link" });
        count += 1;
      }
      return count;
    },
    onSuccess: async (count) => { message.success(count ? `已补齐 ${count} 条模型内关系` : "模型内关系已经完整"); await refresh(); },
    onError: (error: Error) => message.error(error.message),
  });
  const discoverRelationships = useMutation({
    mutationFn: (classUid: string) => syncApi.relationshipSuggestions(workspace!.workspace_key, classUid),
    onSuccess: (result) => {
      setSuggestionResult(result);
      setSelectedSuggestionIds(result.items.filter((item) => item.recommended).map((item) => item.id));
      setSuggestionOpen(true);
    },
    onError: (error: Error) => message.error(error.message),
  });
  const applySuggestions = useMutation({
    mutationFn: () => syncApi.applyRelationshipSuggestions(
      workspace!.workspace_key,
      suggestionResult!.classUid,
      selectedSuggestionIds,
    ),
    onSuccess: async (result) => {
      setLastSuggestionBatch({
        id: result.batchId,
        nodes: result.addedNodeUids.length,
        relationships: result.addedRelationshipKeys.length,
      });
      setSuggestionOpen(false);
      message.success(`已添加 ${result.addedNodeUids.length} 个桥接对象、${result.addedRelationshipKeys.length} 条关系`);
      await refresh();
    },
    onError: (error: Error) => message.error(error.message),
  });
  const undoSuggestions = useMutation({
    mutationFn: (batchId: string) => syncApi.undoRelationshipSuggestionBatch(workspace!.workspace_key, batchId),
    onSuccess: async (result) => {
      message.success(`已撤销 ${result.removedNodes} 个对象、${result.removedRelationships} 条关系`);
      setLastSuggestionBatch(null);
      await refresh();
    },
    onError: (error: Error) => message.error(error.message),
  });
  const removeRelationship = useMutation({
    mutationFn: (key: string) => syncApi.removeOntologyRelationship(workspace!.workspace_key, key),
    onSuccess: async () => { message.success("关系已移出发布模型"); await refresh(); },
    onError: (error: Error) => message.error(error.message),
  });
  const validate = useMutation({
    mutationFn: () => syncApi.validateOntologyWorkspace(workspace!.workspace_key),
    onSuccess: (result) => { setValidation(result); result.valid ? message.success("本体质量校验通过") : message.warning(`发现 ${result.errors.length} 个阻断问题`); },
    onError: (error: Error) => message.error(error.message),
  });
  const govern = useMutation({
    mutationFn: async ({ action, operator }: { action: Operation; operator: string }) => {
      if (!workspace) throw new Error("当前没有可治理工作区");
      if (action.kind === "review") return syncApi.reviewOntologyWorkspace(workspace.workspace_key, operator);
      if (action.kind === "approve") return syncApi.approveOntologyWorkspace(workspace.workspace_key, operator);
      return syncApi.activateOntologyRelease("opcenter2607-core", action.release!.ontology_release_id, operator);
    },
    onSuccess: async () => { message.success("治理操作已完成"); setOperation(null); await refresh(); },
    onError: (error: Error) => message.error(error.message),
  });

  const classColumns: ColumnsType<{ id: string; data: OntologyClass }> = [
    { title: "发布对象", key: "name", render: (_, item) => <div className="ontology-class-name"><strong>{item.data.targetName}</strong><small>{item.data.sourceClass || "自定义对象"}</small></div> },
    { title: "发布角色", key: "role", width: 150, render: (_, item) => <Select size="small" value={item.data.role} style={{ width: 126 }} onClick={(event) => event.stopPropagation()} onChange={(role) => updateClass.mutate({ item: item.data, role: role as "core" | "context" | "reference" | "on_demand" | "excluded" })} options={Object.entries(roleLabels).map(([value, config]) => ({ value, label: config.text }))} /> },
    { title: "属性", key: "properties", width: 72, align: "right", render: (_, item) => graph?.properties.filter((property) => property.classUid === item.id && property.published !== false).length || 0 },
    { title: "操作", key: "action", width: 112, render: (_, item) => <Space size={2}>{item.data.sourceClass ? <Button type="link" size="small" onClick={(event) => { event.stopPropagation(); onLocateSource(item.data.sourceClass!); }}>主图定位</Button> : <Tag>自定义</Tag>}<Popconfirm title="移出当前发布模型？" description="对象属性及其发布关系也会一起移除。" onConfirm={() => removeClass.mutate(item.id)}><Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={(event) => event.stopPropagation()} /></Popconfirm></Space> },
  ];
  const propertyColumns: ColumnsType<OntologyProperty> = [
    { title: "属性", dataIndex: "targetName", render: (value, item) => <div className="ontology-property-name"><strong>{value}</strong><small>{item.sourceName || "自定义属性"}</small></div> },
    { title: "类型", dataIndex: "dataType", width: 105, render: (value) => <Tag>{value || "String"}</Tag> },
    { title: "发布", dataIndex: "published", width: 78, align: "center", render: (value, item) => <Switch size="small" checked={value !== false} loading={updateProperty.isPending && updateProperty.variables?.item.uid === item.uid} onChange={(published) => updateProperty.mutate({ item, changes: { published } })} /> },
    { title: "必填", dataIndex: "required", width: 78, align: "center", render: (value, item) => <Switch size="small" checked={Boolean(value)} disabled={item.published === false} onChange={(required) => updateProperty.mutate({ item, changes: { required } })} /> },
  ];
  const releaseColumns: ColumnsType<OntologyRelease> = [
    { title: "版本", key: "release", width: 120, render: (_, item) => <div className="version-cell"><strong>R{item.release_no}</strong><small>{item.ontology_release_id.slice(0, 8)}</small></div> },
    { title: "状态", dataIndex: "status", width: 160, render: (value) => <Tag color={(releaseLabels[value] || { color: "default" }).color}>{(releaseLabels[value] || { text: value }).text}</Tag> },
    { title: "对象", dataIndex: "class_count", width: 90, align: "right" }, { title: "属性", dataIndex: "property_count", width: 100, align: "right" },
    { title: "关系", dataIndex: "relationship_count", width: 90, align: "right" }, { title: "批准人", dataIndex: "approved_by", width: 150, render: (value) => value || "—" },
    { title: "创建时间", dataIndex: "created_at", width: 190, render: formatTime },
    { title: "操作", key: "action", width: 110, fixed: "right", render: (_, item) => item.status === "approved" ? <Button type="primary" size="small" onClick={() => { setConfirmation(""); setOperation({ kind: "activate", title: `激活本体版本 R${item.release_no}`, description: "激活后将成为数据发布与 Graph Studio 使用的语义契约。", phrase: `激活本体 R${item.release_no}`, release: item }); }}>激活</Button> : "—" },
  ];

  if (!workspace && !loading) return <Alert type="warning" showIcon message="尚未初始化本体发布工作区" />;
  if (view === "workspace") return <div className="ontology-integrated-view">
    <div className="ontology-workspace-summary">
      <div><small>当前草稿</small><strong>{workspace?.title}</strong><span>Rev. {workspace?.revision} · {workspace?.status}</span></div>
      <div><small>发布范围</small><strong>{graph?.nodes.length || 0} 个对象</strong><span>{graph?.properties.filter((item) => item.published !== false).length || 0} 个属性 · {graph?.edges.length || 0} 条关系</span></div>
      <Space wrap><Button icon={<PlusOutlined />} onClick={() => setCreateClassOpen(true)}>新建自定义对象</Button><Button icon={<LinkOutlined />} disabled={(graph?.nodes.length || 0) < 2} onClick={openRelationshipEditor}>新建发布关系</Button><Button icon={<BranchesOutlined />} loading={syncRelationships.isPending} onClick={() => syncRelationships.mutate()}>补齐模型内关系</Button><Button type="primary" icon={<CheckCircleOutlined />} onClick={() => validate.mutate()}>检查当前模型</Button></Space>
    </div>
    <Card className="publish-ontology-view-switch" styles={{ body: { padding: 10 } }}><Segmented block value={modelView} onChange={(value) => setModelView(value as typeof modelView)} options={[{ value: "preview", label: "发布本体图" }, { value: "scope", label: "范围与属性" }, { value: "presentation", label: "显示与检索" }, { value: "diff", label: `版本差异 ${modelDiff.added.length + modelDiff.removed.length + modelDiff.modified.length + modelDiff.addedRelationships.length + modelDiff.removedRelationships.length}` }]} /></Card>

    {modelView === "preview" && <>
      {lastSuggestionBatch && <Alert className="relationship-batch-alert" type="success" showIcon message="刚刚应用了一组关联建议" description={`新增 ${lastSuggestionBatch.nodes} 个桥接对象、${lastSuggestionBatch.relationships} 条关系；你可以逐项检查，也可以撤销本次添加。`} action={<Popconfirm title="撤销刚刚添加的关联？" description="仅移除本批次新增的关系以及没有其他关系的桥接对象。" onConfirm={() => undoSuggestions.mutate(lastSuggestionBatch.id)}><Button danger loading={undoSuggestions.isPending}>撤销本次补齐</Button></Popconfirm>} />}
      <div className="publish-ontology-status-strip">
        <div><small>发布本体库</small><strong>{governance?.database || "graphstudio-model"}</strong></div>
        <span className="publish-flow-arrow">→</span><div><small>工作区草稿</small><strong>Rev. {workspace?.revision}</strong></div>
        <span className="publish-flow-arrow">→</span><div><small>模型状态</small><strong>{workspace?.status === "draft" ? "已保存 · 待校验" : workspace?.status}</strong></div>
        <span className="publish-flow-arrow">→</span><div><small>Graph Studio 使用版本</small><strong className={pendingRelease ? "pending" : undefined}>{pendingRelease ? `活动 R${activeRelease?.release_no || "—"} · 待激活 R${pendingRelease.release_no}` : activeRelease ? `活动 R${activeRelease.release_no}` : "尚未发布"}</strong></div>
      </div>
      <div className="publish-ontology-preview-grid">
        <Card className="publish-ontology-graph-card" title={<Space><ApartmentOutlined /><span>Graph Studio Publish Ontology</span></Space>} extra={<Space><Tag>{graph?.nodes.length || 0} 个对象</Tag><Tag>{graph?.edges.length || 0} 条关系</Tag></Space>} styles={{ body: { padding: 0 } }}>
          <PublishOntologyCanvas graph={graph} selectedId={selectedId} mode={mode} onSelect={setSelectedId} />
        </Card>
        <Card className="publish-ontology-inspector" title={selectedNode ? <div className="semantic-detail-title"><span>{selectedNode.data.targetName}</span><small>{selectedNode.data.sourceClass}</small></div> : "发布对象详情"} extra={selectedNode && <Tag color={roleLabels[selectedNode.data.role]?.color}>{roleLabels[selectedNode.data.role]?.text}</Tag>}>
          {!selectedNode ? <Empty description="选择图中的发布对象" /> : <>
            <Alert type="info" showIcon message="已写入发布本体草稿" description={`存储于 ${governance?.database} · ${workspace?.workspace_key}`} />
            <Descriptions size="small" column={2} className="publish-ontology-meta"><Descriptions.Item label="发布名称">{selectedNode.data.targetName}</Descriptions.Item><Descriptions.Item label="来源对象">{selectedNode.data.sourceClass}</Descriptions.Item><Descriptions.Item label="发布属性">{selectedAllProperties.filter((item) => item.published !== false).length}</Descriptions.Item><Descriptions.Item label="关联关系">{incidentRelationships.length}</Descriptions.Item><Descriptions.Item label="孤立策略">{selectedNode.data.orphanPolicy}</Descriptions.Item><Descriptions.Item label="来源类型">{selectedNode.data.origin}</Descriptions.Item></Descriptions>
            <Typography.Text strong>发布属性</Typography.Text>
            <Table className="publish-preview-property-table" rowKey="uid" size="small" dataSource={selectedAllProperties.filter((item) => item.published !== false)} pagination={false} scroll={{ y: 185 }} columns={[{ title: "属性", dataIndex: "targetName", render: (value, item) => <div className="ontology-property-name"><strong>{value}</strong><small>{item.sourceName}</small></div> }, { title: "类型", dataIndex: "dataType", width: 100, render: (value) => <Tag>{value}</Tag> }, { title: "必填", dataIndex: "required", width: 58, align: "center", render: (value) => value ? <CheckCircleFilled className="ontology-valid-icon" /> : "—" }]} />
            <Typography.Text strong>发布关系</Typography.Text>
            <div className="publish-preview-relations">{incidentRelationships.length ? incidentRelationships.map((edge) => <button type="button" key={edge.id} onClick={() => setSelectedId(edge.source === selectedId ? edge.target : edge.source)}><span>{edge.source === selectedId ? "下游" : "上游"}</span><strong>{edge.data.targetName || edge.data.relationshipKey}</strong><small>{graph?.nodes.find((node) => node.id === (edge.source === selectedId ? edge.target : edge.source))?.data.targetName}</small></button>) : <Typography.Text type="secondary">当前对象暂无发布关系</Typography.Text>}</div>
            <Button block icon={<BranchesOutlined />} loading={discoverRelationships.isPending} disabled={!selectedNode.data.sourceClass} onClick={() => discoverRelationships.mutate(selectedId)}>发现与现有图谱的关联</Button>
          </>}
        </Card>
      </div>
    </>}

    {modelView === "scope" && <>
      <div className="ontology-workspace-grid">
        <Card className="ontology-scope-card" title={<Space><ApartmentOutlined /><span>当前模型对象</span></Space>} extra={<Space><Tag>{filteredNodes.length} 个</Tag><Button size="small" icon={<PlusOutlined />} onClick={() => setCreateClassOpen(true)}>新建</Button></Space>}><Input allowClear prefix={<SearchOutlined />} placeholder="搜索当前模型对象" value={search} onChange={(event) => setSearch(event.target.value)} /><Table rowKey="id" size="small" columns={classColumns} dataSource={filteredNodes} pagination={false} scroll={{ x: 620, y: 520 }} onRow={(item) => ({ onClick: () => setSelectedId(item.id) })} rowClassName={(item) => item.id === selectedId ? "selected-row" : ""} /></Card>
        <Card className="ontology-object-editor" title={selectedNode ? <div className="semantic-detail-title"><span>{selectedNode.data.targetName}</span><small>{selectedNode.data.sourceClass || "自定义发布对象"}</small></div> : "对象配置"} extra={selectedNode && <Space><Tag color={roleLabels[selectedNode.data.role]?.color}>{roleLabels[selectedNode.data.role]?.text}</Tag><Button size="small" icon={<PlusOutlined />} onClick={() => setCreatePropertyOpen(true)}>新增属性</Button></Space>}>
          {!selectedNode ? <Empty description="选择左侧对象进行配置" /> : <><Descriptions column={2} size="small"><Descriptions.Item label="来源">{selectedNode.data.origin}</Descriptions.Item><Descriptions.Item label="孤立策略">{selectedNode.data.orphanPolicy}</Descriptions.Item></Descriptions><Button className="relationship-discovery-button" type="primary" ghost block icon={<BranchesOutlined />} loading={discoverRelationships.isPending} disabled={!selectedNode.data.sourceClass} onClick={() => discoverRelationships.mutate(selectedId)}>发现与现有图谱的关联</Button><Input allowClear prefix={<SearchOutlined />} placeholder="搜索对象属性" value={propertySearch} onChange={(event) => setPropertySearch(event.target.value)} /><Table rowKey="uid" size="small" columns={propertyColumns} dataSource={selectedProperties} pagination={false} scroll={{ x: 500, y: 300 }} /><div className="ontology-suggestion-block"><div><Typography.Text strong>一跳依赖建议</Typography.Text><Typography.Text type="secondary">加入必要上下游对象后，再补齐模型内关系。</Typography.Text></div>{suggestions.length ? <><div className="ontology-suggestion-tags">{suggestions.map((item) => <Button size="small" key={item.id} icon={<PlusOutlined />} loading={addClass.isPending && addClass.variables === item.id} onClick={() => addClass.mutate(item.id)}>{item.data.chineseName || item.id}</Button>)}</div><Button type="link" loading={addAllSuggestions.isPending} onClick={() => addAllSuggestions.mutate()}>全部加入当前一跳</Button></> : <Alert type="success" showIcon message="当前对象的一跳依赖均已纳入模型" />}</div></>}
        </Card>
      </div>
      <Card title={<Space><LinkOutlined /><span>当前模型关系</span></Space>} extra={<Space><Tag>{graph?.edges.length || 0} 条</Tag><Button size="small" icon={<PlusOutlined />} disabled={(graph?.nodes.length || 0) < 2} onClick={openRelationshipEditor}>新建关系</Button></Space>}><Table rowKey="id" size="small" dataSource={graph?.edges || []} pagination={false} columns={[{ title: "源对象", dataIndex: "source", render: (value) => graph?.nodes.find((node) => node.id === value)?.data.targetName || value }, { title: "关系", key: "relation", render: (_, item) => <Tag color="cyan">{item.data.targetName || item.data.relationshipKey}</Tag> }, { title: "目标对象", dataIndex: "target", render: (value) => graph?.nodes.find((node) => node.id === value)?.data.targetName || value }, { title: "基数", dataIndex: ["data", "cardinality"], width: 130 }, { title: "操作", key: "action", width: 80, render: (_, item) => <Popconfirm title="移出该发布关系？" onConfirm={() => removeRelationship.mutate(item.data.relationshipKey)}><Button type="text" danger icon={<DeleteOutlined />} /></Popconfirm> }]} /></Card>
    </>}

    {modelView === "presentation" && <OntologyPresentationPanel graph={graph} workspaceKey={workspace?.workspace_key} selectedId={selectedId} onSelect={setSelectedId} onSaved={refresh} />}

    {modelView === "diff" && <div className="publish-diff-view">
      <Alert type="info" showIcon message={`草稿 Rev.${workspace?.revision} 对比活动版本 R${governance?.activeRelease?.release_no || "—"}`} description="差异以来源对象、启用属性、发布角色和对象关系为基准；活动版本保持不可变。" />
      <div className="publish-diff-metrics"><Card><small>新增对象</small><strong className="added">{modelDiff.added.length}</strong></Card><Card><small>修改对象</small><strong className="changed">{modelDiff.modified.length}</strong></Card><Card><small>移除对象</small><strong className="removed">{modelDiff.removed.length}</strong></Card><Card><small>关系变化</small><strong>{modelDiff.addedRelationships.length + modelDiff.removedRelationships.length}</strong></Card></div>
      <div className="publish-diff-grid">
        <Card title="对象差异" extra={<Typography.Text type="secondary">活动 {modelDiff.activeClassCount} → 草稿 {graph?.nodes.length || 0}</Typography.Text>}><div className="publish-diff-list"><DiffGroup title="新增" color="success" items={modelDiff.added} /><DiffGroup title="修改" color="warning" items={modelDiff.modified} /><DiffGroup title="移除" color="error" items={modelDiff.removed} /></div></Card>
        <Card title="关系差异" extra={<Typography.Text type="secondary">活动 {modelDiff.activeRelationshipCount} → 草稿 {graph?.edges.length || 0}</Typography.Text>}><div className="publish-diff-list"><DiffGroup title="新增关系" color="success" items={modelDiff.addedRelationships.map(formatRelationshipDiff)} /><DiffGroup title="移除关系" color="error" items={modelDiff.removedRelationships.map(formatRelationshipDiff)} /></div></Card>
      </div>
    </div>}
    <Modal title="新建自定义发布对象" open={createClassOpen} okText="加入当前草稿" cancelText="取消" confirmLoading={createCustomClass.isPending} onCancel={() => { setCreateClassOpen(false); classForm.resetFields(); }} onOk={() => classForm.validateFields().then((values) => createCustomClass.mutate(values))}>
      <Alert type="info" showIcon message="不依赖 Neo4j 源对象" description="适用于聚合概念、发布视图或 Graph Studio 专用语义对象；创建后可继续添加属性和关系。" />
      <Form form={classForm} layout="vertical" initialValues={{ role: "context", orphanPolicy: "quarantine" }} className="ontology-create-form">
        <Form.Item name="targetName" label="发布对象技术名" rules={[{ required: true, message: "请输入对象技术名" }, { pattern: /^[A-Za-z_][A-Za-z0-9_]*$/, message: "请使用英文字母开头的字母、数字或下划线" }]}><Input placeholder="例如 ManufacturingImpact" /></Form.Item>
        <Form.Item name="label" label="业务显示名" rules={[{ required: true, message: "请输入业务显示名" }]}><Input placeholder="例如 制造影响" /></Form.Item>
        <Form.Item name="description" label="业务定义"><Input.TextArea rows={3} placeholder="说明对象的制造业务含义和使用边界" /></Form.Item>
        <div className="ontology-form-grid"><Form.Item name="role" label="发布角色"><Select options={Object.entries(roleLabels).filter(([value]) => value !== "excluded").map(([value, config]) => ({ value, label: config.text }))} /></Form.Item><Form.Item name="orphanPolicy" label="孤立数据策略"><Select options={[{ value: "quarantine", label: "隔离并复核" }, { value: "reject", label: "拒绝发布" }, { value: "allow", label: "允许发布" }, { value: "referenced_only", label: "仅被引用时发布" }]} /></Form.Item></div>
      </Form>
    </Modal>
    <Modal title={`为 ${selectedNode?.data.targetName || "当前对象"} 新增属性`} open={createPropertyOpen} okText="保存属性" cancelText="取消" confirmLoading={createCustomProperty.isPending} onCancel={() => { setCreatePropertyOpen(false); propertyForm.resetFields(); }} onOk={() => propertyForm.validateFields().then((values) => createCustomProperty.mutate(values))}>
      <Form form={propertyForm} layout="vertical" initialValues={{ dataType: "String", required: false }} className="ontology-create-form">
        <Form.Item name="targetName" label="属性技术名" rules={[{ required: true, message: "请输入属性技术名" }, { pattern: /^[A-Za-z_][A-Za-z0-9_]*$/, message: "请使用英文字母开头的字母、数字或下划线" }]}><Input placeholder="例如 impactLevel" /></Form.Item>
        <Form.Item name="dataType" label="数据类型" rules={[{ required: true }]}><Select options={["String", "Integer", "Float", "Boolean", "DateTime", "Date", "Navigation", "Array"].map((value) => ({ value, label: value }))} /></Form.Item>
        <Form.Item name="description" label="业务说明"><Input.TextArea rows={3} placeholder="说明属性含义、单位或允许值" /></Form.Item>
        <Form.Item name="required" label="发布约束" valuePropName="checked"><Switch checkedChildren="必填" unCheckedChildren="可选" /></Form.Item>
      </Form>
    </Modal>
    <Modal title="新建发布关系" open={createRelationshipOpen} okText="保存关系" cancelText="取消" confirmLoading={createCustomRelationship.isPending} onCancel={() => { setCreateRelationshipOpen(false); relationshipForm.resetFields(); }} onOk={() => relationshipForm.validateFields().then((values) => createCustomRelationship.mutate(values))}>
      <Alert type="info" showIcon message="关系只作用于当前 Graph Studio 发布草稿" description="不会反向修改 Neo4j 制造语义主图，版本冻结后将作为不可变发布契约。" />
      <Form form={relationshipForm} layout="vertical" initialValues={{ sourceUid: selectedId || undefined, cardinality: "many-to-one", strength: "context" }} className="ontology-create-form">
        <div className="ontology-form-grid"><Form.Item name="sourceUid" label="源对象" rules={[{ required: true }]}><Select showSearch optionFilterProp="label" options={(graph?.nodes || []).map((node) => ({ value: node.id, label: node.data.targetName }))} /></Form.Item><Form.Item name="targetUid" label="目标对象" dependencies={["sourceUid"]} rules={[{ required: true }, ({ getFieldValue }) => ({ validator(_, value) { return !value || value !== getFieldValue("sourceUid") ? Promise.resolve() : Promise.reject(new Error("源对象与目标对象不能相同")); } })]}><Select showSearch optionFilterProp="label" options={(graph?.nodes || []).map((node) => ({ value: node.id, label: node.data.targetName }))} /></Form.Item></div>
        <Form.Item name="targetName" label="关系技术名" rules={[{ required: true, message: "请输入关系技术名" }, { pattern: /^[A-Za-z_][A-Za-z0-9_]*$/, message: "请使用英文字母开头的字母、数字或下划线" }]}><Input placeholder="例如 IMPACTS_QUALITY" /></Form.Item>
        <div className="ontology-form-grid"><Form.Item name="cardinality" label="基数"><Select options={[{ value: "one-to-one", label: "一对一" }, { value: "one-to-many", label: "一对多" }, { value: "many-to-one", label: "多对一" }, { value: "many-to-many", label: "多对多" }]} /></Form.Item><Form.Item name="strength" label="关系强度"><Select options={[{ value: "core", label: "核心关系" }, { value: "context", label: "上下文关系" }, { value: "weak", label: "弱关系" }, { value: "on_demand", label: "按需关系" }]} /></Form.Item></div>
        <Form.Item name="description" label="业务说明"><Input.TextArea rows={2} placeholder="说明该关系在制造业务中的含义" /></Form.Item>
      </Form>
    </Modal>
    <Drawer
      className="relationship-suggestion-drawer"
      title={`为 ${suggestionResult?.sourceClass || selectedNode?.data.targetName || "当前对象"} 发现关联`}
      width={680}
      open={suggestionOpen}
      onClose={() => !applySuggestions.isPending && setSuggestionOpen(false)}
      extra={<Space><Typography.Text type="secondary">已选 {selectedSuggestionIds.length} 条路径</Typography.Text><Button type="primary" icon={<BranchesOutlined />} loading={applySuggestions.isPending} disabled={!selectedSuggestionIds.length} onClick={() => applySuggestions.mutate()}>应用选中关联</Button></Space>}
    >
      <Alert type="info" showIcon message="先预览，再写入草稿" description="建议只来自制造语义主图中的已有关系。路径中标记为“新增”的桥接对象会随关系一起加入，应用后仍可逐项删除或整批撤销。" />
      <div className="relationship-suggestion-list">
        {suggestionResult?.items.length ? suggestionResult.items.map((item) => {
          const checked = selectedSuggestionIds.includes(item.id);
          return <label className={`relationship-suggestion-card ${checked ? "selected" : ""}`} key={item.id}>
            <Checkbox checked={checked} onChange={(event) => setSelectedSuggestionIds((values) => event.target.checked ? [...values, item.id] : values.filter((value) => value !== item.id))} />
            <div className="relationship-suggestion-content">
              <div className="relationship-suggestion-heading"><strong>{item.anchorClass} 接入 {item.existingClass}</strong><Space size={6}>{item.recommended && <Tag color="cyan">推荐</Tag>}<Tag>{item.summary}</Tag></Space></div>
              <div className="relationship-path">{formatSuggestionPath(item)}</div>
              {!!item.missingNodes.length && <div className="relationship-new-nodes"><span>将新增桥接对象</span>{item.missingNodes.map((node) => <Tag color="geekblue" key={node.sourceClass}>{node.label || node.sourceClass}</Tag>)}</div>}
            </div>
          </label>;
        }) : <Empty description={suggestionResult?.reason === "custom_class_has_no_source_ontology" ? "自定义对象没有源本体，无法自动发现关系" : "未找到通往当前草稿对象的两跳内关系路径"} />}
      </div>
    </Drawer>
  </div>;

  if (view === "validation") {
    const step = workspace?.status === "frozen" ? 3 : workspace?.status === "reviewed" ? 2 : 0;
    const issueCount = (validation?.errors.length || 0) + (validation?.warnings.length || 0);
    return <div className="ontology-integrated-view">
      <Card title={<Space><CheckCircleOutlined /><span>质量门禁与发布准备</span></Space>} extra={<Tag color={validation?.valid ? "success" : validation ? "error" : "default"}>{validation ? validation.valid ? "校验通过" : "需要处理" : "尚未校验"}</Tag>}>
        <Steps current={step} items={[{ title: "建模草稿" }, { title: "质量校验" }, { title: "同行复核" }, { title: "版本冻结" }, { title: "Graph Studio 发布" }]} />
        <div className="ontology-validation-grid">
          <div><Typography.Text type="secondary">模型完整度</Typography.Text><Progress percent={validation ? validation.valid ? 100 : Math.max(20, 100 - issueCount * 12) : 0} status={validation?.valid ? "success" : "active"} /></div>
          <Descriptions size="small" column={2}><Descriptions.Item label="对象">{graph?.nodes.length || 0}</Descriptions.Item><Descriptions.Item label="属性">{graph?.properties.filter((item) => item.published !== false).length || 0}</Descriptions.Item><Descriptions.Item label="关系">{graph?.edges.length || 0}</Descriptions.Item><Descriptions.Item label="发布库">{governance?.database}</Descriptions.Item></Descriptions>
        </div>
        <Space wrap><Button type="primary" icon={<CheckCircleOutlined />} loading={validate.isPending} onClick={() => validate.mutate()}>执行完整性校验</Button><Button disabled={!validation?.valid || workspace?.status !== "draft"} onClick={() => { setConfirmation(""); setOperation({ kind: "review", title: "提交同行复核", description: "校验通过的当前模型将进入复核状态。" }); }}>提交复核</Button><Button disabled={!validation?.valid || !["draft", "reviewed"].includes(workspace?.status || "")} onClick={() => { setConfirmation(""); setOperation({ kind: "approve", title: "批准并冻结本体版本", description: "当前对象、属性和关系将生成不可变版本。", phrase: "批准本体版本" }); }}>批准并冻结</Button><Button href="/app/publish" icon={<FileProtectOutlined />}>进入 Graph Studio 发布</Button></Space>
      </Card>
      {pendingRelease && <Alert type="warning" showIcon message={`冻结版本 R${pendingRelease.release_no} 尚未激活`} description={`当前 Graph Studio 发布仍使用${activeRelease ? ` R${activeRelease.release_no}（${activeRelease.class_count} 个对象、${activeRelease.relationship_count} 条关系）` : "旧的或空的本体契约"}。必须先激活 R${pendingRelease.release_no}（${pendingRelease.class_count} 个对象、${pendingRelease.relationship_count} 条关系），再到数据发布管理准备新制品。`} action={<Button type="primary" onClick={() => { setConfirmation(""); setOperation({ kind: "activate", title: `激活本体版本 R${pendingRelease.release_no}`, description: "激活后，新的 Graph Studio 制品将使用该不可变语义契约。", phrase: `激活本体 R${pendingRelease.release_no}`, release: pendingRelease }); }}>激活 R{pendingRelease.release_no}</Button>} />}
      {validation && <Card title={`校验结果 · ${validation.errors.length} 个错误，${validation.warnings.length} 个提醒`}>
        {!issueCount ? <Alert type="success" showIcon message="模型完整性校验通过，可以进入复核与版本冻结。" /> : <div className="ontology-issue-list">{validation.errors.map((item) => <Alert key={`${item.code}-${item.message}`} type="error" showIcon icon={<WarningOutlined />} message={item.message} description={item.code} />)}{validation.warnings.map((item) => <Alert key={`${item.code}-${item.message}`} type="warning" showIcon message={item.message} description={item.code} />)}</div>}
      </Card>}
      <OperationModal operation={operation} actor={actor} confirmation={confirmation} loading={govern.isPending} onActor={setActor} onConfirmation={setConfirmation} onCancel={() => setOperation(null)} onConfirm={() => operation && govern.mutate({ action: operation, operator: actor.trim() })} />
    </div>;
  }

  return <div className="ontology-integrated-view">
    {governance?.activeRelease && <Alert type="success" showIcon icon={<CheckCircleFilled />} message={`当前活动本体 R${governance.activeRelease.release_no}`} description={`已激活于 ${formatTime(governance.activeRelease.activated_at)}，是当前 Graph Studio 数据发布使用的语义契约。`} action={<Button href="/app/publish">进入数据发布管理</Button>} />}
    <Card title={<Space><FileProtectOutlined /><span>不可变本体版本记录</span></Space>} extra={<Typography.Text type="secondary">版本激活后成为正式发布契约</Typography.Text>}>
      <Table rowKey="ontology_release_id" columns={releaseColumns} dataSource={governance?.releases || []} pagination={false} scroll={{ x: 1060 }} />
    </Card>
    <OperationModal operation={operation} actor={actor} confirmation={confirmation} loading={govern.isPending} onActor={setActor} onConfirmation={setConfirmation} onCancel={() => setOperation(null)} onConfirm={() => operation && govern.mutate({ action: operation, operator: actor.trim() })} />
  </div>;
}

function formatRelationshipDiff(value: string) {
  const [source, relation, target] = value.split("\0");
  return `${source} — ${relation} → ${target}`;
}

function formatSuggestionPath(item: RelationshipSuggestion) {
  const path: ReactNode[] = [];
  if (item.nodes[0]) path.push(<strong key="node-0">{item.nodes[0].label || item.nodes[0].sourceClass}</strong>);
  item.relationships.forEach((relation, index) => {
    const current = item.nodes[index]?.sourceClass;
    const next = item.nodes[index + 1];
    path.push(<span key={`relation-${index}`}>{relation.sourceClass === current ? `— ${relation.targetName} →` : `← ${relation.targetName} —`}</span>);
    if (next) path.push(<strong key={`node-${index + 1}`}>{next.label || next.sourceClass}</strong>);
  });
  return path;
}

function DiffGroup({ title, color, items }: { title: string; color: string; items: string[] }) {
  return <section><div><Tag color={color}>{title}</Tag><Typography.Text type="secondary">{items.length} 项</Typography.Text></div>{items.length ? items.map((item) => <button type="button" key={item}>{item}</button>) : <Typography.Text type="secondary">无变化</Typography.Text>}</section>;
}

function OperationModal({ operation, actor, confirmation, loading, onActor, onConfirmation, onCancel, onConfirm }: {
  operation: Operation | null; actor: string; confirmation: string; loading: boolean;
  onActor: (value: string) => void; onConfirmation: (value: string) => void; onCancel: () => void; onConfirm: () => void;
}) {
  return <Modal title={operation?.title} open={Boolean(operation)} okText="确认执行" cancelText="取消" okButtonProps={{ loading, danger: operation?.kind === "activate", disabled: !actor.trim() || Boolean(operation?.phrase && confirmation !== operation.phrase) }} onOk={onConfirm} onCancel={onCancel}>
    <Alert showIcon type={operation?.kind === "activate" ? "warning" : "info"} message={operation?.description} />
    <div className="governed-operation-form"><label><span>操作人标识</span><Input value={actor} onChange={(event) => onActor(event.target.value)} /></label>{operation?.phrase && <label><span>请输入 <strong>{operation.phrase}</strong> 确认</span><Input prefix={<SendOutlined />} value={confirmation} onChange={(event) => onConfirmation(event.target.value)} /></label>}</div>
  </Modal>;
}
