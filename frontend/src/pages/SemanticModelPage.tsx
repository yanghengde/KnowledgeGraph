import {
  ApartmentOutlined, ArrowsAltOutlined, BranchesOutlined, DatabaseOutlined,
  CheckCircleOutlined, DeploymentUnitOutlined, FolderOpenOutlined,
  HistoryOutlined, PlusOutlined, ReloadOutlined, SearchOutlined, StarFilled, StarOutlined, TagsOutlined, UploadOutlined,
} from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert, App, Button, Card, Descriptions, Empty, Input, Segmented, Select, Space,
  Spin, Statistic, Table, Tabs, Tag, Tooltip, Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useRef, useState } from "react";
import { semanticApi, syncApi } from "../api";
import { OntologyWorkspacePanel } from "../components/ontology/OntologyWorkspacePanel";
import { OntologyDirectory } from "../components/ontology/OntologyDirectory";
import { SemanticG6Canvas, type SemanticG6Handle } from "../components/ontology/SemanticG6Canvas";
import type { SemanticClassDetail } from "../types";

const moduleNames: Record<string, string> = {
  workflow: "工作流", operation: "工序", spec: "规范与参数", workcenter: "工作中心",
  factory: "工厂模型", mfgline: "制造产线", product: "产品物料", container: "容器批次",
  quality: "质量管理", resource: "设备资源", material: "原材料", bom: "物料清单",
  mfgorder: "制造工单", employee: "人员资质", organization: "组织", tool: "工装工具",
  document: "文档控制", other: "其他",
};

const FOLLOWED_NODE_STORAGE_KEY = "camstar_priority_nodes_v2";

function loadFollowedNodes() {
  try {
    const saved = JSON.parse(localStorage.getItem(FOLLOWED_NODE_STORAGE_KEY) || "[]");
    return Array.isArray(saved) ? saved.filter((value): value is string => typeof value === "string") : [];
  } catch {
    return [];
  }
}

function displayModule(module: string) {
  if (moduleNames[module]) return moduleNames[module];
  if (module.startsWith("semiconductor_")) return `半导体 · ${module.replace("semiconductor_", "").replaceAll("_", " ")}`;
  return module.replaceAll("_", " ");
}

export function SemanticModelPage() {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const graphRef = useRef<SemanticG6Handle>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [moduleFilter, setModuleFilter] = useState("all");
  const [layout, setLayout] = useState<"preset" | "dagre-tb" | "dagre-lr" | "radial" | "force">("preset");
  const [detailTab, setDetailTab] = useState("properties");
  const [moduleSearch, setModuleSearch] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [followedNodeIds, setFollowedNodeIds] = useState<string[]>(loadFollowedNodes);
  const [workbenchView, setWorkbenchView] = useState<"directory" | "source" | "workspace" | "validation" | "versions">("directory");

  const overview = useQuery({ queryKey: ["semantic-graph-overview"], queryFn: () => semanticApi.overview(), enabled: workbenchView !== "directory" });
  const stats = useQuery({ queryKey: ["semantic-graph-stats"], queryFn: () => semanticApi.stats(), enabled: workbenchView !== "directory" });
  const detail = useQuery({
    queryKey: ["semantic-class-detail", selectedNodeId],
    queryFn: () => semanticApi.classDetail(selectedNodeId!),
    enabled: Boolean(selectedNodeId),
  });
  const governance = useQuery({
    queryKey: ["ontology-governance", "opcenter2607-core"],
    queryFn: () => syncApi.ontologyGovernance("opcenter2607-core"),
    enabled: workbenchView !== "directory",
  });

  const modules = useMemo(() => {
    const counts = new Map<string, number>();
    for (const node of overview.data?.nodes || []) counts.set(node.data.module || "other", (counts.get(node.data.module || "other") || 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [overview.data?.nodes]);

  const filteredGraph = useMemo(() => {
    if (!overview.data || moduleFilter === "all") return overview.data;
    const nodes = overview.data.nodes.filter((node) => node.data.module === moduleFilter);
    const ids = new Set(nodes.map((node) => node.id));
    return { ...overview.data, nodes, edges: overview.data.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target)) };
  }, [moduleFilter, overview.data]);

  const selectedNode = overview.data?.nodes.find((node) => node.id === selectedNodeId);
  const selectedModelClass = governance.data?.graph.nodes.find((node) => (node.data.sourceClass || node.data.targetName) === selectedNodeId);
  const selectedIncidentCount = useMemo(() => (overview.data?.edges || []).filter((edge) => edge.source === selectedNodeId || edge.target === selectedNodeId).length, [overview.data?.edges, selectedNodeId]);
  const moduleOptions = modules.map(([key, count]) => ({ value: key, label: `${displayModule(key)}（${count}）` }));
  const searchOptions = (filteredGraph?.nodes || []).map((node) => ({
    value: node.id,
    label: `${node.data.chineseName ? `${node.data.chineseName} · ` : ""}${node.id}`,
  }));

  useEffect(() => {
    if (selectedNodeId && filteredGraph && !filteredGraph.nodes.some((node) => node.id === selectedNodeId)) setSelectedNodeId(null);
  }, [filteredGraph, selectedNodeId]);

  const selectNode = (id: string | null, locate = false) => {
    setSelectedNodeId(id);
    if (id) {
      setDetailTab("properties");
      if (locate) window.setTimeout(() => graphRef.current?.focusNode(id), 0);
    }
  };
  const toggleFollowedNode = () => {
    if (!selectedNodeId) return;
    const next = followedNodeIds.includes(selectedNodeId)
      ? followedNodeIds.filter((id) => id !== selectedNodeId)
      : [...followedNodeIds, selectedNodeId];
    setFollowedNodeIds(next);
    localStorage.setItem(FOLLOWED_NODE_STORAGE_KEY, JSON.stringify(next));
    setLayout("preset");
    graphRef.current?.setFollowedNodes(next);
  };
  const addSelectedToModel = useMutation({
    mutationFn: () => syncApi.addOntologyClass(governance.data!.currentWorkspace!.workspace_key, {
      source_class: selectedNodeId!, target_name: selectedNodeId!, role: "context", orphan_policy: "quarantine",
    }),
    onSuccess: async () => {
      message.success(`${selectedNodeId} 已加入当前发布模型，源属性已自动带入`);
      await queryClient.invalidateQueries({ queryKey: ["ontology-governance", "opcenter2607-core"] });
    },
    onError: (error: Error) => message.error(error.message),
  });
  const locateSourceObject = (className: string) => {
    setWorkbenchView("source");
    setModuleFilter("all");
    window.setTimeout(() => selectNode(className, true), 0);
  };
  const refresh = async () => {
    setRefreshing(true);
    try {
      const [nextOverview, nextStats] = await Promise.all([semanticApi.overview(true), semanticApi.stats(true)]);
      queryClient.setQueryData(["semantic-graph-overview"], nextOverview);
      queryClient.setQueryData(["semantic-graph-stats"], nextStats);
      await Promise.all(["ontology-directory", "authority-detail", "semantic-class-detail", "ontology-governance"].map(key => queryClient.invalidateQueries({ queryKey: [key] })));
    } catch (error) {
      message.error(error instanceof Error ? error.message : "刷新失败，请重试");
    } finally {
      setRefreshing(false);
    }
  };
  const changeLayout = (value: string | number) => {
    const next = value as typeof layout;
    setLayout(next);
    graphRef.current?.setLayout(next);
  };

  const changeModule = (value: string) => {
    if (selectedNodeId && value !== "all" && overview.data?.nodes.find((node) => node.id === selectedNodeId)?.data.module !== value) {
      setSelectedNodeId(null);
    }
    setModuleFilter(value);
  };

  const propertyColumns: ColumnsType<SemanticClassDetail["properties"][number]> = [
    { title: "属性", dataIndex: "name", width: 160, render: (value) => <Typography.Text strong>{value}</Typography.Text> },
    { title: "类型", dataIndex: "dataType", width: 105, render: (value) => <Tag>{value || "—"}</Tag> },
    { title: "业务说明", dataIndex: "description", ellipsis: { showTitle: false }, render: (value) => <Typography.Text type="secondary" ellipsis={{ tooltip: value }}>{value || "—"}</Typography.Text> },
  ];
  const relationColumns = (direction: "outgoing" | "incoming"): ColumnsType<SemanticClassDetail["outgoing"][number] & SemanticClassDetail["incoming"][number]> => [
    { title: direction === "outgoing" ? "目标对象" : "来源对象", key: "class", width: 160, render: (_, item) => <Button type="link" size="small" onClick={() => selectNode(direction === "outgoing" ? item.targetClass : item.sourceClass, true)}>{direction === "outgoing" ? item.targetClass : item.sourceClass}</Button> },
    { title: "关系", dataIndex: "relName", width: 150, render: (value) => <Tag color="cyan">{value || "RELATED_TO"}</Tag> },
    { title: "基数", dataIndex: "cardinality", width: 100, render: (value) => value || "—" },
    { title: "说明", dataIndex: "description", ellipsis: { showTitle: false }, render: (value) => <Typography.Text type="secondary" ellipsis={{ tooltip: value }}>{value || "—"}</Typography.Text> },
  ];

  return <div className="semantic-model-page">
    <section className="semantic-page-heading">
      <div>
        <Typography.Title level={2}>制造语义模型</Typography.Title>
        <Typography.Paragraph>导入 CSV → 审阅并同步建模库 → 查看主图 → 选择发布范围 → 发布到 Graph Studio。</Typography.Paragraph>
      </div>
      <Space wrap>
        <Button type="primary" icon={<UploadOutlined />} onClick={() => { setWorkbenchView("directory"); setImportOpen(true); }}>导入 CSV</Button>
        <Button icon={<ReloadOutlined />} loading={refreshing || overview.isFetching || stats.isFetching} onClick={() => void refresh()}>刷新</Button>
      </Space>
    </section>

    <Card className="semantic-stage-card" styles={{ body: { padding: "4px 14px 0" } }}>
      <Tabs activeKey={workbenchView} onChange={(key) => setWorkbenchView(key as typeof workbenchView)} items={[
        { key: "directory", label: <Space><TagsOutlined />本体目录与差异审阅</Space> },
        { key: "source", label: <Space><ApartmentOutlined />制造语义主图{overview.data && <Tag>{overview.data.nodes.length}</Tag>}</Space> },
        { key: "workspace", label: <Space><FolderOpenOutlined />模型工作区{governance.data && <Tag color="cyan">{governance.data.graph.nodes.length}</Tag>}</Space> },
        { key: "validation", label: <Space><CheckCircleOutlined />校验与发布</Space> },
        { key: "versions", label: <Space><HistoryOutlined />版本记录{governance.data && <Tag color="gold">{governance.data.releases.length}</Tag>}</Space> },
      ]} />
    </Card>

    {workbenchView === "directory" ? <OntologyDirectory importOpen={importOpen} closeImport={() => setImportOpen(false)} /> : workbenchView === "source" ? <>
    <Alert type="info" showIcon message="制造语义主图是只读事实来源" description="“关注”只改变个人浏览布局；“加入模型”才会把对象及其源属性纳入当前 Graph Studio 发布草稿。" />

    <div className="semantic-stat-grid">
      <Card><Statistic title="制造对象" value={stats.data?.classCount || overview.data?.nodes.length || 0} suffix="个" prefix={<ApartmentOutlined />} /></Card>
      <Card><Statistic title="本体属性" value={stats.data?.propertyCount || 0} suffix="项" prefix={<TagsOutlined />} /></Card>
      <Card><Statistic title="语义关系" value={stats.data?.relationCount || overview.data?.edges.length || 0} suffix="条" prefix={<BranchesOutlined />} /></Card>
      <Card><Statistic title="业务模块" value={modules.length} suffix="个" prefix={<DeploymentUnitOutlined />} /></Card>
    </div>

    <Card className="semantic-toolbar-card" styles={{ body: { padding: 12 } }}>
      <div className="semantic-toolbar">
        <Select
          showSearch allowClear suffixIcon={<SearchOutlined />} placeholder="搜索并定位制造对象"
          value={selectedNodeId || undefined} options={searchOptions} optionFilterProp="label"
          onChange={(value) => selectNode(value || null, Boolean(value))} className="semantic-object-search"
        />
        <Select
          showSearch value={moduleFilter} optionFilterProp="label" className="semantic-module-select"
          options={[{ value: "all", label: `全部业务模块（${overview.data?.nodes.length || 0}）` }, ...moduleOptions]}
          onChange={changeModule}
        />
        <Segmented
          value={layout}
          onChange={changeLayout}
          options={[{ value: "preset", label: "稳定总览" }]}
        />
        <Tooltip title="适应全部图谱"><Button icon={<ArrowsAltOutlined />} onClick={() => graphRef.current?.fitView()}>适应画布</Button></Tooltip>
      </div>
    </Card>

    <div className={`semantic-workbench ${selectedNodeId ? "with-detail" : ""}`}>
      <Card className="semantic-graph-card" title={<Space><DatabaseOutlined /><span>Camstar 制造本体</span></Space>} extra={<Space><Tag color="gold">关注 {followedNodeIds.length}</Tag><Tag color="cyan">G6</Tag><Typography.Text type="secondary">{filteredGraph?.nodes.length || 0} 个对象 · {filteredGraph?.edges.length || 0} 条关系</Typography.Text></Space>} styles={{ body: { padding: 0 } }}>
        {overview.isLoading ? <div className="semantic-loading"><Spin size="large" /><Typography.Text type="secondary">正在读取完整本体…</Typography.Text></div> : overview.error ? <Alert type="error" message="完整本体读取失败" description={(overview.error as Error).message} /> : <SemanticG6Canvas ref={graphRef} data={filteredGraph} mode="dark" selectedNodeId={selectedNodeId || undefined} followedNodeIds={followedNodeIds} onNodeSelect={selectNode} />}
      </Card>

      {selectedNodeId && <Card className="semantic-detail-card" title={selectedNode ? <div className="semantic-detail-title"><span>{selectedNode.data.chineseName || selectedNode.id}</span><small>{selectedNode.id}</small></div> : "对象详情"} extra={selectedNode && <Space size={6}><Tag>{displayModule(selectedNode.data.module)}</Tag><Tooltip title={followedNodeIds.includes(selectedNodeId) ? "取消关注并移回外围" : "关注后进入图谱中心区域"}><Button className="semantic-follow-button" type={followedNodeIds.includes(selectedNodeId) ? "primary" : "default"} size="small" icon={followedNodeIds.includes(selectedNodeId) ? <StarFilled /> : <StarOutlined />} onClick={toggleFollowedNode}>{followedNodeIds.includes(selectedNodeId) ? "已关注" : "关注"}</Button></Tooltip><Tooltip title={selectedModelClass ? "该对象已经属于当前发布模型" : "将对象和源属性加入当前模型工作区"}><Button size="small" type={selectedModelClass ? "default" : "primary"} icon={selectedModelClass ? <CheckCircleOutlined /> : <PlusOutlined />} disabled={Boolean(selectedModelClass) || !governance.data?.currentWorkspace} loading={addSelectedToModel.isPending} onClick={() => addSelectedToModel.mutate()}>{selectedModelClass ? "已在模型" : "加入模型"}</Button></Tooltip></Space>}>
        {!selectedNode ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="在画布或搜索框中选择制造对象" /> : <>
          <Descriptions column={2} size="small" className="semantic-meta">
            <Descriptions.Item label="对象层级">{selectedNode.data.layer || "Config"}</Descriptions.Item>
            <Descriptions.Item label="属性数量">{selectedNode.data.propertyCount}</Descriptions.Item>
            <Descriptions.Item label="关联关系">{selectedIncidentCount}</Descriptions.Item>
            <Descriptions.Item label="业务模块">{displayModule(selectedNode.data.module)}</Descriptions.Item>
          </Descriptions>
          {selectedNode.data.description && <Typography.Paragraph className="semantic-description">{selectedNode.data.description}</Typography.Paragraph>}
          <Tabs activeKey={detailTab} onChange={setDetailTab} items={[
            { key: "properties", label: `属性 ${detail.data?.properties.length ?? selectedNode.data.propertyCount}`, children: <Table size="small" rowKey="name" loading={detail.isLoading} columns={propertyColumns} dataSource={detail.data?.properties || []} pagination={{ pageSize: 12, showSizeChanger: false }} scroll={{ x: 500, y: 390 }} /> },
            { key: "outgoing", label: `下游 ${detail.data?.outgoing.length || 0}`, children: <Table size="small" rowKey={(item) => `${item.targetClass}-${item.relName}`} loading={detail.isLoading} columns={relationColumns("outgoing")} dataSource={(detail.data?.outgoing || []) as never[]} pagination={false} scroll={{ x: 580, y: 430 }} /> },
            { key: "incoming", label: `上游 ${detail.data?.incoming.length || 0}`, children: <Table size="small" rowKey={(item) => `${item.sourceClass}-${item.relName}`} loading={detail.isLoading} columns={relationColumns("incoming")} dataSource={(detail.data?.incoming || []) as never[]} pagination={false} scroll={{ x: 580, y: 430 }} /> },
          ]} />
        </>}
      </Card>}
    </div>

    <Card className="semantic-module-card" title="业务模块索引" extra={<Input allowClear size="small" prefix={<SearchOutlined />} placeholder="筛选模块" value={moduleSearch} onChange={(event) => setModuleSearch(event.target.value)} />}>
      <div className="semantic-module-tags">
        {modules.filter(([key]) => !moduleSearch || displayModule(key).toLocaleLowerCase().includes(moduleSearch.toLocaleLowerCase()) || key.includes(moduleSearch.toLocaleLowerCase())).map(([key, count]) => <button key={key} type="button" className={moduleFilter === key ? "active" : ""} onClick={() => changeModule(moduleFilter === key ? "all" : key)}><span>{displayModule(key)}</span><small>{count}</small></button>)}
      </div>
    </Card>
    </> : <OntologyWorkspacePanel view={workbenchView} governance={governance.data} loading={governance.isLoading} sourceGraph={overview.data} onLocateSource={locateSourceObject} />}
  </div>;
}
