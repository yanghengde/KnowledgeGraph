import {
  CheckCircleFilled, CheckCircleOutlined, ClockCircleOutlined, CloudUploadOutlined,
  DatabaseOutlined, ExperimentOutlined, EyeOutlined, FileProtectOutlined,
  HistoryOutlined, LockOutlined, ReloadOutlined, RocketOutlined, RollbackOutlined,
  SafetyCertificateOutlined, UnlockOutlined, WarningOutlined,
} from "@ant-design/icons";
import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert, App, Button, Card, Col, Descriptions, Divider, Input, Modal, Popconfirm,
  Row, Space, Statistic, Steps, Table, Tag, Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useState } from "react";
import { syncApi } from "../api";
import { PublishedCoverageCard } from "../components/PublishedCoverageCard";
import type { CuratedRelease, DeploymentPlan, DeploymentRelease, PublicationRoute, SyncRun } from "../types";

const runStatusLabels: Record<string, { color: string; text: string }> = {
  succeeded: { color: "success", text: "成功" }, running: { color: "processing", text: "运行中" },
  failed: { color: "error", text: "失败" }, started: { color: "processing", text: "已启动" },
};
const deploymentStatusLabels: Record<string, { color: string; text: string }> = {
  planned: { color: "warning", text: "等待审批" }, approved: { color: "processing", text: "等待发布" },
  uploading: { color: "processing", text: "上传中" }, loading: { color: "processing", text: "加载中" },
  verifying: { color: "processing", text: "验证中" }, active: { color: "success", text: "已发布" },
  failed: { color: "error", text: "发布失败" },
};
const releaseStatusLabels: Record<string, { color: string; text: string }> = {
  ready: { color: "processing", text: "等待激活" }, active: { color: "success", text: "活动版本" },
  superseded: { color: "default", text: "历史版本" }, failed: { color: "error", text: "生成失败" },
};
const environmentLabels: Record<string, string> = { dev: "开发验证", uat: "业务验收", prod: "生产" };

type GovernedOperation = {
  kind: "generate" | "activate" | "rollback" | "toggle" | "prepare" | "approve" | "apply";
  title: string; description: string; successMessage: string; danger?: boolean; confirmPhrase?: string;
  release?: CuratedRelease; route?: PublicationRoute; deployment?: DeploymentRelease; applyEnabled?: boolean;
};

function deploymentErrorMessage(deployment?: DeploymentRelease) {
  if (!deployment?.error) return "";
  if (typeof deployment.error === "string") return deployment.error;
  return deployment.error.message || "发布失败，请检查 Graph Studio 状态后重试。";
}

function deploymentErrorTitle(deployment: DeploymentRelease) {
  const detail = deploymentErrorMessage(deployment);
  if (/REST Layer|手工启用 Layer/i.test(detail)) return "Graph Studio 图层需人工启用";
  if (/permission|权限|ACL/i.test(detail)) return "Graph Studio 账号权限不足";
  return "发布未完成，可检查后重试";
}

export function PublishManagementPage() {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [operation, setOperation] = useState<GovernedOperation | null>(null);
  const [actor, setActor] = useState("local-console");
  const [confirmation, setConfirmation] = useState("");

  const jobs = useQuery({ queryKey: ["sync-jobs"], queryFn: syncApi.jobs });
  const runs = useQuery({ queryKey: ["sync-runs"], queryFn: () => syncApi.runs(50) });
  const profiles = useQuery({ queryKey: ["sync-profiles"], queryFn: syncApi.profiles });
  const targets = useQuery({ queryKey: ["sync-targets"], queryFn: syncApi.targets });
  const profileKey = profiles.data?.items[0]?.profile_key || "opcenter2607-core";
  const materialization = useQuery({ queryKey: ["sync-materialization", profileKey], queryFn: () => syncApi.materialization(profileKey) });
  const deployments = useQuery({ queryKey: ["sync-deployments", profileKey], queryFn: () => syncApi.deployments(profileKey) });
  const planQueries = useQueries({ queries: (deployments.data?.routes || []).map((route) => ({
    queryKey: ["sync-deployment-plan", profileKey, route.route_key], queryFn: () => syncApi.deploymentPlan(profileKey, route),
  })) });
  const activeJob = jobs.data?.items[0];
  const activeRelease = materialization.data?.releases.find((item) => item.is_active) || deployments.data?.activeCuratedRelease;
  const activeOntologyRelease = deployments.data?.activeOntologyRelease;
  const planByRoute = new Map<string, DeploymentPlan>();
  (deployments.data?.routes || []).forEach((route, index) => {
    const plan = planQueries[index]?.data;
    if (plan) planByRoute.set(route.route_key, plan);
  });

  const refreshRuns = () => void queryClient.invalidateQueries({ queryKey: ["sync-runs"] });
  const refreshGovernance = () => {
    void queryClient.invalidateQueries({ queryKey: ["sync-materialization"] });
    void queryClient.invalidateQueries({ queryKey: ["sync-deployments"] });
    void queryClient.invalidateQueries({ queryKey: ["sync-deployment-plan"] });
    void queryClient.invalidateQueries({ queryKey: ["sync-targets"] });
  };
  const dryRun = useMutation({
    mutationFn: syncApi.dryRun,
    onSuccess: () => { message.success("发布前检验已完成，未写入 Graph Studio"); refreshRuns(); },
    onError: (error: Error) => message.error(error.message),
  });
  const preview = useMutation({
    mutationFn: syncApi.preview,
    onSuccess: (result) => { message.success(`发布预览已生成：${Number(result.instances || 0).toLocaleString()} 个实例`); refreshRuns(); },
    onError: (error: Error) => message.error(error.message),
  });
  const governedAction = useMutation<unknown, Error, { operation: GovernedOperation; actor: string }>({
    mutationFn: async ({ operation: action, actor: operator }) => {
      if (action.kind === "generate") return syncApi.generateRelease(profileKey, operator);
      if (action.kind === "activate" && action.release) return syncApi.activateRelease(profileKey, action.release.release_id, operator);
      if (action.kind === "rollback") return syncApi.rollbackRelease(profileKey, operator);
      if (action.kind === "toggle" && action.route) return syncApi.setRouteWriteEnabled(action.route.route_key, Boolean(action.applyEnabled));
      if (action.kind === "prepare" && action.route) return syncApi.prepareDeployment(profileKey, action.route, operator);
      if (action.kind === "approve" && action.deployment) return syncApi.approveDeployment(action.deployment.deployment_id, operator);
      if (action.kind === "apply" && action.deployment) return syncApi.applyDeployment(action.deployment.deployment_id);
      throw new Error("操作参数不完整");
    },
    onSuccess: (_, variables) => { message.success(variables.operation.successMessage); setOperation(null); refreshGovernance(); },
    onError: (error) => message.error(error.message),
  });

  const openOperation = (next: GovernedOperation) => { setActor("local-console"); setConfirmation(""); setOperation(next); };
  const confirmOperation = () => {
    if (!operation) return;
    if (actor.trim().length < 2) { message.warning("请输入操作人标识，用于审计记录"); return; }
    if (operation.confirmPhrase && confirmation !== operation.confirmPhrase) { message.warning(`请输入“${operation.confirmPhrase}”确认操作`); return; }
    governedAction.mutate({ operation, actor: actor.trim() });
  };

  const runColumns: ColumnsType<SyncRun> = [
    { title: "运行时间", dataIndex: "started_at", width: 170, render: (value) => value ? new Date(value).toLocaleString("zh-CN") : "—" },
    { title: "类型", dataIndex: "trigger_type", width: 120, render: (value) => <Tag>{value === "dry_run" ? "发布前检验" : value}</Tag> },
    { title: "状态", dataIndex: "status", width: 100, render: (value) => { const status = runStatusLabels[value] || { color: "default", text: value }; return <Tag color={status.color}>{status.text}</Tag>; } },
    { title: "实例行", dataIndex: "row_count", align: "right", width: 110, render: (value) => Number(value || 0).toLocaleString() },
    { title: "RDF 三元组", dataIndex: "triple_count", align: "right", width: 130, render: (value) => Number(value || 0).toLocaleString() },
    { title: "质量信息", key: "quality", render: (_, run) => run.error ? <Typography.Text type="danger">{run.error}</Typography.Text> : <Typography.Text type="secondary">悬空引用 {Number(run.metrics?.danglingReferences || 0)} · 类型回退 {Number(run.metrics?.datatypeFallbacks || 0)}</Typography.Text> },
  ];
  const releaseColumns: ColumnsType<CuratedRelease> = [
    { title: "数据版本", key: "release", width: 120, render: (_, item) => <div className="version-cell"><strong>R{item.release_no}</strong><small>{item.release_id.slice(0, 8)}</small></div> },
    { title: "状态", key: "status", width: 110, render: (_, item) => { const status = item.is_active ? releaseStatusLabels.active : releaseStatusLabels[item.status] || { color: "default", text: item.status }; return <Tag color={status.color}>{status.text}</Tag>; } },
    { title: "对象实例", dataIndex: "object_count", align: "right", width: 110, render: (value) => Number(value || 0).toLocaleString() },
    { title: "关系实例", dataIndex: "relationship_count", align: "right", width: 110, render: (value) => Number(value || 0).toLocaleString() },
    { title: "隔离数据", dataIndex: "quarantine_count", align: "right", width: 100, render: (value) => Number(value || 0).toLocaleString() },
    { title: "生成时间", dataIndex: "started_at", width: 170, render: (value) => value ? new Date(value).toLocaleString("zh-CN") : "—" },
    { title: "操作", key: "action", width: 100, render: (_, item) => item.status === "ready" ? <Button size="small" type="primary" onClick={() => openOperation({ kind: "activate", title: `激活数据版本 R${item.release_no}`, description: "将活动版本指针原子切换到该不可变快照，不会立即写入 Graph Studio。", successMessage: `数据版本 R${item.release_no} 已激活`, release: item })}>激活</Button> : "—" },
  ];
  const deploymentColumns: ColumnsType<DeploymentRelease> = [
    { title: "环境", dataIndex: "environment_key", width: 110, render: (value) => environmentLabels[value] || value },
    { title: "数据版本", dataIndex: "curated_release_id", width: 120, render: (value) => activeRelease && value === activeRelease.release_id ? `R${activeRelease.release_no}` : String(value).slice(0, 8) },
    { title: "槽位", dataIndex: "slot", width: 90, render: (value) => <Tag color={value === "blue" ? "blue" : "green"}>{String(value).toUpperCase()}</Tag> },
    { title: "状态", dataIndex: "status", width: 120, render: (value) => { const status = deploymentStatusLabels[value] || { color: "default", text: value }; return <Tag color={status.color}>{status.text}</Tag>; } },
    { title: "制品校验值", dataIndex: "artifact_hash", width: 160, render: (value) => value ? <Typography.Text code copyable={{ text: String(value) }}>{String(value).slice(0, 12)}</Typography.Text> : "—" },
    { title: "操作人", dataIndex: "approved_by", width: 130, render: (value) => value || "—" },
    { title: "开始时间", dataIndex: "started_at", width: 180, render: (value) => value ? new Date(value).toLocaleString("zh-CN") : "—" },
    { title: "结果", key: "result", width: 360, render: (_, item) => item.status === "failed" ? <div className="deployment-result failed"><strong>{deploymentErrorTitle(item)}</strong><Typography.Text ellipsis={{ tooltip: deploymentErrorMessage(item) }}>{deploymentErrorMessage(item)}</Typography.Text></div> : <div className="deployment-result success"><strong>{item.status === "active" ? "发布验证通过" : "等待后续操作"}</strong><span>{item.status === "active" ? "检查点已提交" : "—"}</span></div> },
  ];

  return (
    <div className="page-stack operations-page">
      <section className="section-intro operations-heading">
        <div><Typography.Title level={2}>数据发布管理</Typography.Title><Typography.Paragraph>以“先检验、版本冻结、环境审批、正式发布、可验证回滚”为主线管理 Camstar 到 Graph Studio 的可审计发布。</Typography.Paragraph></div>
        <Space wrap>
          <Popconfirm title="执行发布前检验？" description="只生成校验产物，不会写入 Graph Studio。" onConfirm={() => activeJob && dryRun.mutate(activeJob.job_name)}><Button icon={<ExperimentOutlined />} loading={dryRun.isPending} disabled={!activeJob}>执行发布前检验</Button></Popconfirm>
          <Button type="primary" icon={<EyeOutlined />} loading={preview.isPending} disabled={!activeJob} onClick={() => activeJob && preview.mutate(activeJob.job_name)}>生成发布预览</Button>
        </Space>
      </section>
      <Alert showIcon type="info" icon={<SafetyCertificateOutlined />} message="先确定本体，再核实数据与关联" description="选择业务对象和关系 → 生成并校验数据版本 → 发布到 Graph Studio。下方可核实当前问数版本中，哪些对象和关系已经带有数据。" />
      <PublishedCoverageCard profileKey={profileKey} />

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="同步任务" value={jobs.data?.items.length || 0} suffix="个" prefix={<CloudUploadOutlined />} /></Card></Col>
        <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="活动数据版本" value={activeRelease ? `R${activeRelease.release_no}` : "无"} prefix={<DatabaseOutlined />} /></Card></Col>
        <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="发布目标" value={targets.data?.items.length || 0} suffix="个" prefix={<CheckCircleOutlined />} /></Card></Col>
        <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="历史运行" value={runs.data?.items.length || 0} suffix="次" prefix={<HistoryOutlined />} /></Card></Col>
      </Row>

      <Card className="release-control-card" title={<Space><FileProtectOutlined /><span>不可变数据版本</span></Space>} extra={<Space wrap>
        <Button icon={<ReloadOutlined />} onClick={() => void materialization.refetch()}>刷新</Button>
        <Button icon={<RollbackOutlined />} danger disabled={(materialization.data?.releases.length || 0) < 2} onClick={() => openOperation({ kind: "rollback", title: "回滚活动数据版本", description: "活动版本将恢复到上一不可变快照；后续环境发布仍需单独执行。", successMessage: "活动数据版本已回滚", danger: true, confirmPhrase: "回滚数据版本" })}>回滚版本</Button>
        <Button type="primary" icon={<DatabaseOutlined />} disabled={!materialization.data?.plan.ready} onClick={() => openOperation({ kind: "generate", title: "生成不可变数据版本", description: "从已批准的数据契约生成新快照并执行质量验证，生成后仍需单独激活。", successMessage: "新的不可变数据版本已生成" })}>生成数据版本</Button>
      </Space>} loading={materialization.isLoading}>
        <div className="release-plan-strip"><Tag color={materialization.data?.plan.ready ? "success" : "error"}>{materialization.data?.plan.ready ? "数据门禁已通过" : "数据门禁未通过"}</Tag><span>批处理行数 <strong>{Number(materialization.data?.plan.batchRows || 0).toLocaleString()}</strong></span><span>契约 <strong>{materialization.data?.plan.contracts.length || 0}</strong></span><span>关系 <strong>{materialization.data?.plan.relationships.length || 0}</strong></span><span>激活策略 <strong>验证后指针切换</strong></span></div>
        {!!materialization.data?.plan.blockers.length && <Alert className="release-blockers" type="error" showIcon message="当前版本生成被阻断" description={materialization.data.plan.blockers.join("；")} />}
        <Table rowKey="release_id" columns={releaseColumns} dataSource={materialization.data?.releases || []} pagination={false} scroll={{ x: 850 }} />
      </Card>

      <section className="promotion-section">
        <div className="promotion-title"><div><Typography.Title level={3}>环境晋级与正式发布</Typography.Title><Typography.Text type="secondary">同一不可变制品按开发验证 → 业务验收 → 生产顺序晋级。</Typography.Text></div><Tag color="cyan">BLUE / GREEN</Tag></div>
        <Row gutter={[16, 16]}>
          {(deployments.data?.routes || []).map((route, index) => {
            const plan = planByRoute.get(route.route_key);
            // A deployable contract is the pair (data release, ontology release).
            // An older active deployment must not hide the prepare action after
            // a new ontology version is activated for the same data snapshot.
            const latest = deployments.data?.deployments.find((item) =>
              item.route_key === route.route_key
              && item.curated_release_id === activeRelease?.release_id
              && item.ontology_release_id === activeOntologyRelease?.ontology_release_id
            );
            const status = latest ? deploymentStatusLabels[latest.status] || { color: "default", text: latest.status } : plan?.ready ? { color: "processing", text: "等待准备" } : { color: "default", text: "前置门禁" };
            const errorMessage = deploymentErrorMessage(latest);
            const stepCurrent = latest?.status === "active" ? 3 : latest?.status === "approved" || latest?.status === "failed" ? 2 : latest ? 1 : route.apply_enabled ? 1 : 0;
            return <Col xs={24} xl={8} key={route.route_key}><Card className={`promotion-card environment-${route.environment_key}`} title={<div><strong>{environmentLabels[route.environment_key]}</strong><small>{route.target_title || route.title}</small></div>} extra={<Tag color={status.color}>{status.text}</Tag>}>
              <Steps size="small" current={stepCurrent} status={latest?.status === "failed" ? "error" : latest?.status === "active" ? "finish" : "process"} items={[{ title: "授权" }, { title: "制品" }, { title: route.requires_approval ? "审批" : "就绪" }, { title: "发布" }]} />
              <Descriptions column={1} size="small" className="promotion-details">
                <Descriptions.Item label="活动数据版本">{activeRelease ? `R${activeRelease.release_no}` : "无"}</Descriptions.Item><Descriptions.Item label="活动本体版本">{activeOntologyRelease ? `R${activeOntologyRelease.release_no}` : "无"}</Descriptions.Item><Descriptions.Item label="目标槽位">{plan?.slot ? plan.slot.toUpperCase() : "—"}</Descriptions.Item>
                <Descriptions.Item label="写入安全开关"><Tag icon={route.apply_enabled ? <UnlockOutlined /> : <LockOutlined />} color={route.apply_enabled ? "success" : "default"}>{route.apply_enabled ? "已开启" : "已锁定"}</Tag></Descriptions.Item><Descriptions.Item label="外部门禁">{route.requires_approval ? "需要审批" : "无需审批"}</Descriptions.Item>
              </Descriptions>
              {!plan?.ready && <Alert className="promotion-message" type="warning" showIcon message={plan?.blockers[0] || (planQueries[index]?.isLoading ? "正在计算发布门禁" : "发布计划不可用")} />}
              {errorMessage && <Alert className="promotion-message" type="error" showIcon message="上次发布未完成" description={errorMessage} />}
              <Divider />
              <Space wrap className="promotion-actions">
                <Button icon={route.apply_enabled ? <LockOutlined /> : <UnlockOutlined />} disabled={!plan?.ready && !route.apply_enabled} onClick={() => openOperation({ kind: "toggle", title: `${route.apply_enabled ? "锁定" : "开启"}${environmentLabels[route.environment_key]}写入`, description: route.apply_enabled ? "关闭后将阻止新的 Graph Studio 写入操作。" : "仅开启安全开关，不会自动准备制品或执行发布。", successMessage: `${environmentLabels[route.environment_key]}写入开关已${route.apply_enabled ? "锁定" : "开启"}`, route, applyEnabled: !route.apply_enabled, danger: route.apply_enabled })}>{route.apply_enabled ? "锁定写入" : "开启写入"}</Button>
                {plan?.ready && route.apply_enabled && !latest && <Button type="primary" icon={<FileProtectOutlined />} onClick={() => openOperation({ kind: "prepare", title: `准备${environmentLabels[route.environment_key]}发布制品`, description: `为数据版本 R${activeRelease?.release_no} 生成不可变 RDF 制品；此步骤不会写入 Graph Studio。`, successMessage: "不可变发布制品已准备", route })}>准备制品</Button>}
                {latest?.status === "planned" && <Button type="primary" icon={<CheckCircleFilled />} onClick={() => openOperation({ kind: "approve", title: `批准${environmentLabels[route.environment_key]}发布`, description: "记录审批人并解除部署审批门禁；环境写入开关仍独立生效。", successMessage: "环境发布已批准", deployment: latest })}>批准发布</Button>}
                {latest && ["approved", "failed"].includes(latest.status) && route.apply_enabled && <Button danger={latest.status === "failed"} type="primary" icon={latest.status === "failed" ? <ReloadOutlined /> : <RocketOutlined />} onClick={() => openOperation({ kind: "apply", title: `${latest.status === "failed" ? "重试" : "正式"}发布到${environmentLabels[route.environment_key]}`, description: `系统将上传不可变制品、切换 ${latest.slot.toUpperCase()} 槽位并执行验收。只有验证通过后才提交检查点。`, successMessage: `${environmentLabels[route.environment_key]}发布已完成`, danger: true, confirmPhrase: `发布到 ${route.environment_key.toUpperCase()}`, deployment: latest, route })}>{latest.status === "failed" ? "修复后重试" : "正式发布"}</Button>}
              </Space>
            </Card></Col>;
          })}
        </Row>
      </section>

      <Card title="Graph Studio 部署记录" extra={<Button type="link" onClick={() => void deployments.refetch()}>刷新记录</Button>}><Table className="deployment-table" rowKey="deployment_id" columns={deploymentColumns} dataSource={deployments.data?.deployments || []} loading={deployments.isLoading} pagination={{ pageSize: 6, showSizeChanger: false }} scroll={{ x: 1270 }} tableLayout="fixed" /></Card>
      <Row gutter={[16, 16]}><Col xs={24} xl={14}><Card title="当前同步任务" extra={activeJob && <Tag color={activeJob.enabled ? "success" : "default"}>{activeJob.enabled ? "已启用" : "已停用"}</Tag>} loading={jobs.isLoading}>{activeJob ? <Descriptions column={{ xs: 1, md: 2 }} size="small"><Descriptions.Item label="任务名称">{activeJob.title}</Descriptions.Item><Descriptions.Item label="发布方式">{activeJob.mode === "atomic_snapshot" ? "原子快照" : "分区增量"}</Descriptions.Item><Descriptions.Item label="调度计划"><Space><ClockCircleOutlined />{activeJob.schedule || "手动执行"}</Space></Descriptions.Item><Descriptions.Item label="成功版本保留">最近 {activeJob.retention_success} 个</Descriptions.Item><Descriptions.Item label="Graphmart" span={2}><Typography.Text copyable ellipsis>{activeJob.graphmart_uri || "—"}</Typography.Text></Descriptions.Item></Descriptions> : <Typography.Text type="secondary">暂无发布任务</Typography.Text>}</Card></Col>
        <Col xs={24} xl={10}><Card title="发布安全说明"><div className="safety-list"><span><CheckCircleFilled />制品与数据版本均不可变</span><span><CheckCircleFilled />写入授权与正式发布相互独立</span><span><CheckCircleFilled />验证通过后才提交检查点</span><span><WarningOutlined />生产发布必须完成前置环境晋级</span></div></Card></Col></Row>
      <Card title="同步与检验运行记录" extra={<Button type="link" onClick={() => void runs.refetch()}>刷新记录</Button>}><Table rowKey="run_id" columns={runColumns} dataSource={runs.data?.items || []} loading={runs.isLoading} pagination={{ pageSize: 8, showSizeChanger: false }} scroll={{ x: 900 }} /></Card>

      <Modal title={operation?.title} open={Boolean(operation)} onCancel={() => !governedAction.isPending && setOperation(null)} onOk={confirmOperation} okText={operation?.kind === "apply" ? "确认正式发布" : "确认操作"} cancelText="取消" confirmLoading={governedAction.isPending} okButtonProps={{ danger: operation?.danger, disabled: actor.trim().length < 2 || Boolean(operation?.confirmPhrase && confirmation !== operation.confirmPhrase) }} maskClosable={!governedAction.isPending} closable={!governedAction.isPending}>
        <Alert type={operation?.danger ? "warning" : "info"} showIcon message={operation?.description} />
        <div className="governed-operation-form"><label><span>操作人标识</span><Input value={actor} onChange={(event) => setActor(event.target.value)} placeholder="用于审计记录" /></label>{operation?.confirmPhrase && <label><span>请输入确认短语：<strong>{operation.confirmPhrase}</strong></span><Input value={confirmation} onChange={(event) => setConfirmation(event.target.value)} placeholder={operation.confirmPhrase} /></label>}</div>
      </Modal>
    </div>
  );
}
