import {
  ApartmentOutlined, CheckCircleFilled, CheckCircleOutlined, DatabaseOutlined,
  FileProtectOutlined, LinkOutlined, ReloadOutlined, SafetyCertificateOutlined,
  SearchOutlined, SendOutlined, TagsOutlined, WarningOutlined,
} from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert, App, Button, Card, Col, Descriptions, Empty, Input, Modal, Row, Space,
  Statistic, Steps, Table, Tag, Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState } from "react";
import { syncApi } from "../api";
import type {
  OntologyClass, OntologyGraph, OntologyProperty, OntologyRelationship, OntologyRelease,
} from "../types";

const workspaceStatuses: Record<string, { text: string; color: string; step: number }> = {
  draft: { text: "草稿", color: "default", step: 0 },
  reviewed: { text: "已复核", color: "processing", step: 2 },
  frozen: { text: "已冻结", color: "success", step: 3 },
};

const releaseStatuses: Record<string, { text: string; color: string }> = {
  approved: { text: "已批准待激活", color: "processing" },
  active: { text: "当前活动版本", color: "success" },
  superseded: { text: "历史版本", color: "default" },
};

const roleLabels: Record<string, { text: string; color: string }> = {
  core: { text: "核心对象", color: "cyan" },
  context: { text: "上下文对象", color: "geekblue" },
  excluded: { text: "不发布", color: "default" },
};

type GovernedAction = {
  kind: "review" | "approve" | "activate";
  title: string;
  description: string;
  successMessage: string;
  confirmPhrase?: string;
  release?: OntologyRelease;
};

function formatTime(value?: string | null) {
  return value ? new Date(value).toLocaleString("zh-CN") : "—";
}

function OntologyTopology({ graph, selectedId, onSelect }: { graph?: OntologyGraph; selectedId: string; onSelect: (id: string) => void }) {
  const topology = useMemo(() => {
    if (!graph || !selectedId) return { nodes: [], edges: [] };
    const incident = graph.edges.filter((edge) => edge.source === selectedId || edge.target === selectedId);
    const neighborIds = [...new Set(incident.flatMap((edge) => [edge.source, edge.target]).filter((id) => id !== selectedId))];
    const ids = [selectedId, ...neighborIds];
    const positions = new Map<string, { x: number; y: number }>();
    positions.set(selectedId, { x: 450, y: 160 });
    neighborIds.forEach((id, index) => {
      const angle = neighborIds.length === 1 ? 0 : (-Math.PI / 2) + (index * Math.PI * 2 / neighborIds.length);
      positions.set(id, { x: 450 + Math.cos(angle) * 285, y: 160 + Math.sin(angle) * 105 });
    });
    return {
      nodes: ids.map((id) => ({ item: graph.nodes.find((node) => node.id === id), position: positions.get(id)! })).filter((entry) => entry.item),
      edges: incident.map((edge) => ({ edge, source: positions.get(edge.source)!, target: positions.get(edge.target)! })),
    };
  }, [graph, selectedId]);

  if (!topology.nodes.length) return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择制造对象查看关系邻域" />;
  return <div className="ontology-topology-wrap">
    <svg className="ontology-topology" viewBox="0 0 900 320" role="img" aria-label="制造对象关系拓扑">
      <defs><marker id="ontology-arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" /></marker></defs>
      {topology.edges.map(({ edge, source, target }) => {
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const length = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const start = { x: source.x + dx / length * 88, y: source.y + dy / length * 38 };
        const end = { x: target.x - dx / length * 92, y: target.y - dy / length * 40 };
        return <g className="topology-edge" key={edge.id}>
          <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} markerEnd="url(#ontology-arrow)" />
          <text x={(source.x + target.x) / 2} y={(source.y + target.y) / 2 - 8} textAnchor="middle">{edge.data.targetName || edge.data.relationshipKey}</text>
        </g>;
      })}
      {topology.nodes.map(({ item, position }) => item && <g key={item.id} className={`topology-node ${item.id === selectedId ? "selected" : ""}`} transform={`translate(${position.x - 82} ${position.y - 34})`} role="button" tabIndex={0} onClick={() => onSelect(item.id)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") onSelect(item.id); }}>
        <rect width="164" height="68" rx="13" />
        <text className="topology-node-title" x="82" y="28" textAnchor="middle">{item.data.targetName}</text>
        <text className="topology-node-role" x="82" y="48" textAnchor="middle">{roleLabels[item.data.role]?.text || item.data.role}</text>
      </g>)}
    </svg>
    <div className="topology-legend"><span><i className="core" />核心对象</span><span><i className="context" />上下文对象</span><span>仅展示当前对象的一跳邻域，适配大规模本体</span></div>
  </div>;
}

export function OntologyGovernancePage() {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const profileKey = "opcenter2607-core";
  const [selectedClassId, setSelectedClassId] = useState("");
  const [classSearch, setClassSearch] = useState("");
  const [propertySearch, setPropertySearch] = useState("");
  const [operation, setOperation] = useState<GovernedAction | null>(null);
  const [actor, setActor] = useState("local-console");
  const [confirmation, setConfirmation] = useState("");

  const governance = useQuery({
    queryKey: ["ontology-governance", profileKey],
    queryFn: () => syncApi.ontologyGovernance(profileKey),
  });
  const workspace = governance.data?.currentWorkspace;
  const graph = governance.data?.graph;
  const workspaceStatus = workspaceStatuses[workspace?.status || "draft"] || { text: workspace?.status || "未知", color: "default", step: 0 };
  const newestRelease = governance.data?.releases[0];
  const activeRelease = governance.data?.activeRelease;

  useEffect(() => {
    if (!selectedClassId && graph?.nodes[0]?.id) setSelectedClassId(graph.nodes[0].id);
  }, [graph?.nodes, selectedClassId]);

  const propertyCounts = useMemo(() => {
    const result = new Map<string, number>();
    for (const property of graph?.properties || []) {
      if (property.published !== false) result.set(property.classUid, (result.get(property.classUid) || 0) + 1);
    }
    return result;
  }, [graph?.properties]);

  const filteredClasses = useMemo(() => {
    const keyword = classSearch.trim().toLocaleLowerCase();
    return (graph?.nodes || []).filter((item) => !keyword || [item.data.targetName, item.data.sourceClass, item.data.description]
      .some((value) => String(value || "").toLocaleLowerCase().includes(keyword)));
  }, [classSearch, graph?.nodes]);

  const selectedClass = graph?.nodes.find((item) => item.id === selectedClassId)?.data;
  const selectedProperties = useMemo(() => {
    const keyword = propertySearch.trim().toLocaleLowerCase();
    return (graph?.properties || []).filter((property) => property.classUid === selectedClassId)
      .filter((property) => !keyword || [property.targetName, property.sourceName, property.dataType, property.description]
        .some((value) => String(value || "").toLocaleLowerCase().includes(keyword)));
  }, [graph?.properties, propertySearch, selectedClassId]);

  const refresh = () => void queryClient.invalidateQueries({ queryKey: ["ontology-governance", profileKey] });
  const validateWorkspace = useMutation({
    mutationFn: () => syncApi.validateOntologyWorkspace(workspace!.workspace_key),
    onSuccess: (result) => {
      if (result.valid) message.success(`本体质量校验通过：${result.counts.classes} 个对象、${result.counts.properties} 个属性、${result.counts.relationships} 条关系`);
      else Modal.error({ title: "本体质量校验未通过", content: result.errors.map((item) => item.message).join("；") });
    },
    onError: (error: Error) => message.error(error.message),
  });
  const governedMutation = useMutation<unknown, Error, { action: GovernedAction; actor: string }>({
    mutationFn: ({ action, actor: operator }) => {
      if (!workspace) throw new Error("当前没有可治理的本体工作区");
      if (action.kind === "review") return syncApi.reviewOntologyWorkspace(workspace.workspace_key, operator);
      if (action.kind === "approve") return syncApi.approveOntologyWorkspace(workspace.workspace_key, operator);
      if (action.kind === "activate" && action.release) return syncApi.activateOntologyRelease(profileKey, action.release.ontology_release_id, operator);
      throw new Error("操作参数不完整");
    },
    onSuccess: (_, variables) => {
      message.success(variables.action.successMessage);
      setOperation(null);
      refresh();
    },
    onError: (error) => message.error(error.message),
  });

  const openOperation = (next: GovernedAction) => {
    setActor("local-console");
    setConfirmation("");
    setOperation(next);
  };
  const confirmOperation = () => {
    if (!operation) return;
    if (actor.trim().length < 2) return void message.warning("请输入操作人标识，用于审计记录");
    if (operation.confirmPhrase && confirmation !== operation.confirmPhrase) return void message.warning(`请输入“${operation.confirmPhrase}”确认操作`);
    governedMutation.mutate({ action: operation, actor: actor.trim() });
  };

  const classColumns: ColumnsType<{ id: string; data: OntologyClass }> = [
    {
      title: "制造对象", key: "class", render: (_, item) => <div className="ontology-class-name">
        <strong>{item.data.targetName}</strong><small>{item.data.sourceClass || "自定义语义对象"}</small>
      </div>,
    },
    { title: "角色", dataIndex: ["data", "role"], width: 105, render: (value) => { const role = roleLabels[value] || { text: value, color: "default" }; return <Tag color={role.color}>{role.text}</Tag>; } },
    { title: "发布属性", key: "properties", width: 92, align: "right", render: (_, item) => propertyCounts.get(item.id) || 0 },
  ];
  const propertyColumns: ColumnsType<OntologyProperty> = [
    { title: "发布属性", dataIndex: "targetName", width: 190, render: (value, item) => <div className="ontology-property-name"><strong>{value}</strong><small>{item.sourceName || "自定义属性"}</small></div> },
    { title: "数据类型", dataIndex: "dataType", width: 120, render: (value) => <Tag>{value || "未定义"}</Tag> },
    { title: "必填", dataIndex: "required", width: 76, align: "center", render: (value) => value ? <CheckCircleFilled className="ontology-valid-icon" /> : "—" },
    { title: "发布", dataIndex: "published", width: 76, align: "center", render: (value) => <Tag color={value === false ? "default" : "success"}>{value === false ? "停用" : "启用"}</Tag> },
    { title: "业务说明", dataIndex: "description", ellipsis: { showTitle: false }, render: (value) => <Typography.Text type="secondary" ellipsis={{ tooltip: value }}>{value || "—"}</Typography.Text> },
  ];
  const relationshipColumns: ColumnsType<{ id: string; source: string; target: string; data: OntologyRelationship }> = [
    { title: "源对象", dataIndex: "source", width: 160, render: (value) => graph?.nodes.find((item) => item.id === value)?.data.targetName || value },
    { title: "关系语义", key: "relationship", width: 220, render: (_, item) => <div className="relationship-name"><LinkOutlined /><strong>{item.data.targetName || item.data.relationshipKey}</strong></div> },
    { title: "目标对象", dataIndex: "target", width: 160, render: (value) => graph?.nodes.find((item) => item.id === value)?.data.targetName || value },
    { title: "基数", dataIndex: ["data", "cardinality"], width: 120, render: (value) => value || "—" },
    { title: "用途", dataIndex: ["data", "usage"], width: 120, render: (value) => <Tag color={value === "core" ? "cyan" : "geekblue"}>{value === "core" ? "核心链路" : value === "context" ? "上下文链路" : value || "—"}</Tag> },
    { title: "上下文要求", dataIndex: ["data", "requiredContext"], render: (value) => value ? "必须存在" : "可选" },
  ];
  const releaseColumns: ColumnsType<OntologyRelease> = [
    { title: "本体版本", key: "release", width: 120, render: (_, item) => <div className="version-cell"><strong>R{item.release_no}</strong><small>{item.ontology_release_id.slice(0, 8)}</small></div> },
    { title: "状态", dataIndex: "status", width: 150, render: (value) => { const status = releaseStatuses[value] || { text: value, color: "default" }; return <Tag color={status.color}>{status.text}</Tag>; } },
    { title: "对象", dataIndex: "class_count", width: 90, align: "right" },
    { title: "属性", dataIndex: "property_count", width: 100, align: "right", render: (value) => Number(value || 0).toLocaleString() },
    { title: "关系", dataIndex: "relationship_count", width: 90, align: "right" },
    { title: "批准人", dataIndex: "approved_by", width: 150, render: (value) => value || "—" },
    { title: "激活时间", dataIndex: "activated_at", width: 180, render: formatTime },
    { title: "操作", key: "action", width: 105, fixed: "right", render: (_, item) => item.status === "approved" ? <Button size="small" type="primary" onClick={() => openOperation({ kind: "activate", title: `激活本体版本 R${item.release_no}`, description: "活动本体指针将切换到该不可变版本，新的数据版本与 Graph Studio 发布将使用这套语义契约。", successMessage: `本体版本 R${item.release_no} 已激活`, confirmPhrase: `激活本体 R${item.release_no}`, release: item })}>激活</Button> : "—" },
  ];

  return <div className="page-stack ontology-page">
    <section className="section-intro operations-heading">
      <div><Typography.Title level={2}>制造语义模型</Typography.Title><Typography.Paragraph>集中治理 Camstar 制造对象、发布属性、业务关系和不可变本体版本，为数据发布与知识问答提供统一语义契约。</Typography.Paragraph></div>
      <Space wrap>
        <Button icon={<ReloadOutlined />} loading={governance.isFetching} onClick={() => void governance.refetch()}>刷新</Button>
        <Button icon={<CheckCircleOutlined />} disabled={!workspace} loading={validateWorkspace.isPending} onClick={() => validateWorkspace.mutate()}>执行质量校验</Button>
        <Button type="primary" icon={<ApartmentOutlined />} href="/ontology">打开图形化编辑器</Button>
      </Space>
    </section>

    <Alert showIcon type="info" icon={<SafetyCertificateOutlined />} message="React 本体治理工作台已启用" description="对象、属性、关系、质量校验、复核批准与版本激活已迁移；复杂的拖拽建模暂由旧版图形化编辑器承接。" />
    {newestRelease && activeRelease && newestRelease.ontology_release_id !== activeRelease.ontology_release_id && <Alert showIcon type="warning" icon={<WarningOutlined />} message={`存在尚未激活的新本体版本 R${newestRelease.release_no}`} description={`当前数据发布仍使用 R${activeRelease.release_no}。激活新版本前，请确认下游字段映射和受控 Query 已完成兼容性检查。`} />}

    <Row gutter={[16, 16]}>
      <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="制造对象" value={graph?.nodes.length || 0} suffix="个" prefix={<ApartmentOutlined />} /></Card></Col>
      <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="发布属性" value={graph?.properties.filter((item) => item.published !== false).length || 0} suffix="项" prefix={<TagsOutlined />} /></Card></Col>
      <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="业务关系" value={graph?.edges.length || 0} suffix="条" prefix={<LinkOutlined />} /></Card></Col>
      <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="活动本体版本" value={activeRelease ? `R${activeRelease.release_no}` : "无"} prefix={<FileProtectOutlined />} /></Card></Col>
    </Row>

    <Card className="ontology-lifecycle-card" loading={governance.isLoading} title={<Space><DatabaseOutlined /><span>本体工作区与版本门禁</span></Space>} extra={workspace && <Tag color={workspaceStatus.color}>{workspaceStatus.text}</Tag>}>
      {workspace ? <Row gutter={[28, 20]} align="middle">
        <Col xs={24} xl={15}>
          <Steps current={workspaceStatus.step} status="process" items={[{ title: "建模草稿" }, { title: "质量校验" }, { title: "同行复核" }, { title: "版本冻结" }]} />
        </Col>
        <Col xs={24} xl={9}>
          <Descriptions size="small" column={2} className="ontology-workspace-details">
            <Descriptions.Item label="工作区">{workspace.title}</Descriptions.Item>
            <Descriptions.Item label="修订">Rev. {workspace.revision}</Descriptions.Item>
            <Descriptions.Item label="发布图库">{governance.data?.database}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{formatTime(workspace.updated_at)}</Descriptions.Item>
          </Descriptions>
          <Space wrap>
            <Button disabled={workspace.status !== "draft"} onClick={() => openOperation({ kind: "review", title: "提交本体复核", description: "系统将先执行质量校验；通过后记录复核人并锁定当前审查状态。", successMessage: "本体工作区已通过复核" })}>提交复核</Button>
            <Button type="primary" disabled={!(["draft", "reviewed"].includes(workspace.status))} onClick={() => openOperation({ kind: "approve", title: "批准并冻结本体版本", description: "将当前对象、属性和关系生成不可变本体快照。生成后仍需单独激活，才会成为发布契约。", successMessage: "不可变本体版本已生成", confirmPhrase: "批准本体版本" })}>批准并冻结</Button>
          </Space>
        </Col>
      </Row> : <Empty description="尚未初始化本体治理工作区" />}
    </Card>

    <Card className="ontology-topology-card" title={<Space><ApartmentOutlined /><span>制造对象关系拓扑</span></Space>} extra={<Space><Tag color="cyan">局部图谱</Tag><Typography.Text type="secondary">点击节点切换中心对象</Typography.Text></Space>}>
      <OntologyTopology graph={graph} selectedId={selectedClassId} onSelect={setSelectedClassId} />
    </Card>

    <Row gutter={[16, 16]} className="ontology-browser-row">
      <Col xs={24} xl={9}>
        <Card className="ontology-browser-card" title="制造对象目录" extra={<Tag>{filteredClasses.length} 个</Tag>}>
          <Input allowClear prefix={<SearchOutlined />} placeholder="搜索对象或来源类" value={classSearch} onChange={(event) => setClassSearch(event.target.value)} />
          <Table className="ontology-class-table" rowKey="id" size="small" columns={classColumns} dataSource={filteredClasses} pagination={false} scroll={{ y: 410 }} onRow={(item) => ({ onClick: () => setSelectedClassId(item.id) })} rowClassName={(item) => item.id === selectedClassId ? "selected-row" : ""} />
        </Card>
      </Col>
      <Col xs={24} xl={15}>
        <Card className="ontology-browser-card ontology-property-card" title={selectedClass ? <Space><span>{selectedClass.targetName} 属性契约</span><Tag color={roleLabels[selectedClass.role]?.color || "default"}>{roleLabels[selectedClass.role]?.text || selectedClass.role}</Tag></Space> : "属性契约"} extra={<Typography.Text type="secondary">{selectedProperties.length} 项</Typography.Text>}>
          <Input allowClear prefix={<SearchOutlined />} placeholder="搜索属性、来源字段或数据类型" value={propertySearch} onChange={(event) => setPropertySearch(event.target.value)} />
          <Table rowKey="uid" size="small" columns={propertyColumns} dataSource={selectedProperties} pagination={{ pageSize: 8, showSizeChanger: false }} scroll={{ x: 820 }} locale={{ emptyText: "该对象暂无发布属性" }} />
        </Card>
      </Col>
    </Row>

    <Card title={<Space><LinkOutlined /><span>对象关系契约</span></Space>} extra={<Tag>{graph?.edges.length || 0} 条</Tag>}>
      <Table rowKey="id" columns={relationshipColumns} dataSource={graph?.edges || []} pagination={false} scroll={{ x: 900 }} />
    </Card>

    <Card title={<Space><FileProtectOutlined /><span>不可变本体版本</span></Space>} extra={<Typography.Text type="secondary">激活后成为数据发布语义契约</Typography.Text>}>
      <Table rowKey="ontology_release_id" columns={releaseColumns} dataSource={governance.data?.releases || []} pagination={false} scroll={{ x: 1050 }} />
    </Card>

    <Modal title={operation?.title} open={Boolean(operation)} okText="确认执行" cancelText="取消" okButtonProps={{ danger: operation?.kind === "activate", loading: governedMutation.isPending, disabled: Boolean(operation?.confirmPhrase && confirmation !== operation.confirmPhrase) }} onOk={confirmOperation} onCancel={() => setOperation(null)}>
      <Alert showIcon type={operation?.kind === "activate" ? "warning" : "info"} message={operation?.description} />
      <div className="governed-operation-form">
        <label><span>操作人标识</span><Input value={actor} onChange={(event) => setActor(event.target.value)} placeholder="用于审计记录" /></label>
        {operation?.confirmPhrase && <label><span>请输入 <strong>{operation.confirmPhrase}</strong> 确认</span><Input value={confirmation} onChange={(event) => setConfirmation(event.target.value)} placeholder={operation.confirmPhrase} prefix={<SendOutlined />} /></label>}
      </div>
    </Modal>
  </div>;
}
