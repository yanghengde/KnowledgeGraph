import {
CheckCircleOutlined,ClockCircleOutlined,CloudSyncOutlined,DatabaseOutlined,
ExclamationCircleOutlined,FileProtectOutlined,ReloadOutlined,
SafetyCertificateOutlined,SettingOutlined,SyncOutlined,
} from "@ant-design/icons";
import { useMutation,useQuery,useQueryClient } from "@tanstack/react-query";
import {
Alert,App,Button,Card,Col,Input,InputNumber,Modal,Row,Space,Statistic,
Steps,Switch,Table,Tag,Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useState } from "react";
import { syncApi } from "../../../api";
import { useModelScope } from "../../../app/modelScope";
import type { DataSyncClassStatus } from "../../../types";
import { SyncClassConfigurationDialog } from "../components/SyncClassConfigurationDialog";

const coverageLabels: Record<string, { color: string; text: string }> = {
  synchronized: { color: "success", text: "同步数据" },
  model_only: { color: "processing", text: "仅发布模型" },
  excluded: { color: "default", text: "已排除" },
  missing: { color: "error", text: "未配置" },
};

const strategyLabels: Record<string, string> = {
  snapshot: "小表快照",
  watermark: "水位增量",
  append_only: "只增不改",
  cdc: "CDC 变更捕获",
  excluded: "排除",
};

const extractionLabels: Record<string, string> = {
  keyset_snapshot: "键集快照",
  baseline_snapshot: "首次基线",
  verified_incremental_package: "已验证增量",
  copy_active: "无变化复用",
  field_backfill: "字段回填",
};

export function DataSynchronizationPage() {
  const { profileKey } = useModelScope();
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [configureClass, setConfigureClass] = useState<string>();
  const [actor, setActor] = useState("local-console");
  const [confirmation, setConfirmation] = useState("");
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [intervalMinutes, setIntervalMinutes] = useState(15);
  const [maxAttempts, setMaxAttempts] = useState(3);
  const [retryBackoff, setRetryBackoff] = useState(60);
  const status = useQuery({
    queryKey: ["data-sync", profileKey],
    queryFn: () => syncApi.dataSync(profileKey),
    refetchInterval: (query) => query.state.data?.summary.pendingEvents ? 8_000 : false,
  });
  const run = useMutation({
    mutationFn: () => syncApi.runDataSync(profileKey, actor.trim()),
    onSuccess: (result) => {
      const release = result.status.activeRelease;
      message.success(`数据同步完成${release ? `，活动版本 R${release.release_no}` : ""}`);
      setDialogOpen(false);
      setConfirmation("");
      void queryClient.invalidateQueries({ queryKey: ["data-sync"] });
      void queryClient.invalidateQueries({ queryKey: ["sync-materialization"] });
      void queryClient.invalidateQueries({ queryKey: ["sync-deployments"] });
    },
    onError: (error: Error) => message.error(error.message),
  });
  const configure = useMutation({
    mutationFn: () => syncApi.configureDataSync(profileKey, {
      enabled: scheduleEnabled,
      interval_minutes: intervalMinutes,
      max_attempts: maxAttempts,
      retry_backoff_seconds: retryBackoff,
    }),
    onSuccess: () => {
      message.success(scheduleEnabled ? "自动数据同步已启用" : "自动数据同步已停用");
      setScheduleOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["data-sync", profileKey] });
    },
    onError: (error: Error) => message.error(error.message),
  });

  const data = status.data;
  const coverageIncomplete = Number(data?.summary.missing || 0) > 0;
  const columns: ColumnsType<DataSyncClassStatus> = [
    { title: "操作", key: "configure", fixed: "right", width: 125,
      render: (_, item) => ["missing", "model_only"].includes(item.coverageStatus)
        ? <Button type="link" onClick={() => setConfigureClass(item.className)}>配置同步</Button> : <Tag color="success">已配置</Tag> },
    {
      title: "本体对象", dataIndex: "className", width: 170,
      render: (value, item) => <div className="data-sync-class"><strong>{value}</strong><small>{item.role || "—"}</small></div>,
    },
    {
      title: "同步范围", dataIndex: "coverageStatus", width: 125,
      render: (value) => { const label = coverageLabels[value] || { color: "default", text: value }; return <Tag color={label.color}>{label.text}</Tag>; },
    },
    {
      title: "源表", key: "source", width: 230,
      render: (_, item) => item.sourceTable ? <div className="data-sync-source"><strong>{item.sourceTable}</strong><small>{item.sourceSchema} · 目录约 {Number(item.catalogRows || 0).toLocaleString()} 行</small></div> : "—",
    },
    {
      title: "采集策略", key: "strategy", width: 160,
      render: (_, item) => <div className="data-sync-strategy"><span>{strategyLabels[item.strategy || ""] || item.strategy || "—"}</span><small>{extractionLabels[item.extractionMode || ""] || item.extractionMode || (item.coverageStatus === "synchronized" ? "等待计划" : "不采集实例")}</small></div>,
    },
    {
      title: "数据合同", key: "contract", width: 155,
      render: (_, item) => item.contractKey ? <Space size={4}><Tag color={item.contractStatus === "approved" ? "success" : "warning"}>v{item.contractVersion}</Tag><span>{item.selectedColumns} 字段</span></Space> : <Typography.Text type="secondary">未建立</Typography.Text>,
    },
    {
      title: "活动 / 隔离", dataIndex: "activeObjectCount", align: "right", width: 125,
      render: (value, item) => <Space size={4}><Typography.Text type={item.coverageStatus === "synchronized" && Number(value) === 0 ? "warning" : undefined}>{Number(value || 0).toLocaleString()}</Typography.Text>{item.scopeExclusionCount > 0 && <Tag color="default">隔离 {item.scopeExclusionCount}</Tag>}</Space>,
    },
    {
      title: "源/版本对账", key: "reconciliation", width: 185,
      render: (_, item) => {
        const reconciliation = item.reconciliation;
        if (!reconciliation) return <Tag>等待首次同步</Tag>;
        if (reconciliation.status === "failed") return <Tag color="error">差异 {reconciliation.difference}</Tag>;
        return <div className="data-sync-reconciliation"><Tag color="success">已核对</Tag><small>{Number(reconciliation.source_count ?? reconciliation.release_count).toLocaleString()} → {Number(reconciliation.release_count).toLocaleString()}</small></div>;
      },
    },
    {
      title: "变更事件", key: "events", align: "right", width: 120,
      render: (_, item) => item.pendingEvents ? <Tag color="processing">待处理 {item.pendingEvents}</Tag> : <Typography.Text type="secondary">无待处理</Typography.Text>,
    },
  ];

  return (
    <div className="page-stack data-sync-page">
      <section className="section-intro operations-heading">
        <div>
          <Typography.Title level={2}>制造数据同步</Typography.Title>
          <Typography.Paragraph>本体版本保持不变时，持续把 Camstar 业务实例同步到受治理的 PostgreSQL 不可变版本。Graph Studio 正式发布仍在“数据发布管理”单独执行。</Typography.Paragraph>
        </div>
        <Space wrap>
          <Button icon={<ReloadOutlined />} loading={status.isFetching} onClick={() => void status.refetch()}>刷新状态</Button>
          <Button icon={<SettingOutlined />} onClick={() => {
            const schedule = data?.automation.schedule;
            setScheduleEnabled(Boolean(schedule?.enabled));
            setIntervalMinutes(Number(schedule?.interval_minutes || 15));
            setMaxAttempts(Number(schedule?.max_attempts || 3));
            setRetryBackoff(Number(schedule?.retry_backoff_seconds || 60));
            setScheduleOpen(true);
          }}>自动同步设置</Button>
          <Button type="primary" icon={<CloudSyncOutlined />} loading={run.isPending} disabled={coverageIncomplete || !data} onClick={() => { setActor("local-console"); setConfirmation(""); setDialogOpen(true); }}>执行数据同步</Button>
        </Space>
      </section>

      <Alert
        showIcon type="info" icon={<SafetyCertificateOutlined />}
        message="数据同步与 Graph Studio 发布已经解耦"
        description="此页面只冻结源窗口、幂等采集、质量检查、数量对账并激活 PostgreSQL 数据版本，不会启停 Graph Studio Layer，也不会改变 BLUE / GREEN 槽位。"
        action={<Button href="/app/publish">进入数据发布管理</Button>}
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} xl={6}><Card className="metric-card"><Statistic title="本体覆盖" value={data ? `${data.summary.synchronized}/${data.summary.classes}` : "—"} prefix={<CheckCircleOutlined />} /></Card></Col>
        <Col xs={24} sm={12} xl={6}><Card className="metric-card"><Statistic title="活动数据版本" value={data?.activeRelease ? `R${data.activeRelease.release_no}` : "无"} prefix={<FileProtectOutlined />} /></Card></Col>
        <Col xs={24} sm={12} xl={6}><Card className="metric-card"><Statistic title="活动实例" value={data?.summary.activeObjects || 0} prefix={<DatabaseOutlined />} /></Card></Col>
        <Col xs={24} sm={12} xl={6}><Card className="metric-card"><Statistic title="待处理事件" value={data?.summary.pendingEvents || 0} prefix={<ClockCircleOutlined />} /></Card></Col>
      </Row>

      <Card className="data-sync-flow-card" title={<Space><SyncOutlined /><span>一次同步如何保证不重不漏</span></Space>}>
        <Steps
          responsive
          items={[
            { title: "冻结窗口", description: "先读取上界" },
            { title: "幂等采集", description: "事件 ID 防重复" },
            { title: "质量与对账", description: "源数＝版本数" },
            { title: "原子激活", description: "验证后提交 checkpoint" },
          ]}
        />
      </Card>

      {coverageIncomplete && <Alert type="error" showIcon icon={<ExclamationCircleOutlined />} message={`仍有 ${data?.summary.missing} 个本体对象未配置数据同步`} description={(data?.blockers || []).join("；")}
        action={<Space wrap>{data?.classes.filter(item => item.coverageStatus === "missing").map(item => <Button key={item.className} type="primary" onClick={() => setConfigureClass(item.className)}>配置 {item.className}</Button>)}</Space>} />}
      {!coverageIncomplete && !!data?.blockers.length && <Alert type="warning" showIcon message="同步前置检查待刷新" description={`${data.blockers.join("；")}。点击“执行数据同步”会先重新运行质量检查，再决定是否生成新版本。`} />}
      {!!data?.summary.pendingRelationships && <Alert type="warning" showIcon message={`${data.summary.pendingRelationships} 条源关系引用尚未解析`} description={`当前活动版本共有 ${data.summary.relationships} 条关系记录，其中 ${data.summary.resolvedRelationships} 条已关联到目标对象。未解析引用会保留审计证据，但不会伪造成 Graph Studio 边。`} />}
      {!!data?.summary.scopeExclusions && <Alert type="info" showIcon message={`${data.summary.scopeExclusions} 条系统记录已与制造业务图谱隔离`} description="源记录仍保存在不可变数据版本中用于审计，但不会作为 Graph Studio 节点或关系发布。当前规则要求 WorkflowStep.WorkflowId 必须存在于受治理的制造 Workflow 集合。" />}

      {!!data?.scopePolicies.length && <Card title="业务图谱作用域规则">
        {data.scopePolicies.map((policy) => <div className="data-sync-scope-policy" key={policy.policy_key}>
          <Space wrap><Tag color={policy.enabled ? "success" : "default"}>{policy.enabled ? "已启用" : "已停用"}</Tag><strong>{policy.config?.labelZh || policy.policy_key}</strong><Typography.Text code>v{policy.version}</Typography.Text></Space>
          <Typography.Text type="secondary">{policy.source_class}.{policy.source_columns.join("+")} 必须关联到 {policy.anchor_class}.{policy.anchor_columns.join("+")}；不匹配的数据仅保留审计。</Typography.Text>
        </div>)}
      </Card>}

      <Card title="自动同步与运行记录" extra={data?.automation.schedule?.enabled ? <Tag color="processing">每 {data.automation.schedule.interval_minutes} 分钟</Tag> : <Tag>未启用</Tag>}>
        {data?.automation.schedule?.enabled && !data?.automation.worker?.online && <Alert type="warning" showIcon message="自动同步已配置，但工作进程未在线" description="启动 python -m src.graphstudio_sync.cli data-sync-worker 后，工作进程会通过 PostgreSQL 租约领取任务；多个实例同时运行也不会重复同步。" />}
        {data?.automation.worker?.online && <Alert type="success" showIcon message={`工作进程在线：${data.automation.worker.worker_id}`} description={data.automation.schedule?.next_run_at ? `下次计划：${new Date(data.automation.schedule.next_run_at).toLocaleString("zh-CN")}` : "等待计划"} />}
        <Table
          className="data-sync-run-table" size="small" rowKey="run_id"
          dataSource={data?.automation.recentRuns || []} pagination={false}
          locale={{ emptyText: "暂无运行记录" }}
          columns={[
            { title: "触发", dataIndex: "trigger_type", width: 100, render: (value: string) => ({ manual: "手工", scheduled: "计划", retry: "重试" }[value] || value) },
            { title: "状态", dataIndex: "status", width: 110, render: (value: string) => <Tag color={value === "succeeded" ? "success" : value === "failed" ? "error" : value === "running" ? "processing" : "default"}>{value}</Tag> },
            { title: "尝试", dataIndex: "attempt", width: 80, render: (value: number) => `第 ${value} 次` },
            { title: "计划时间", dataIndex: "scheduled_for", width: 190, render: (value: string) => new Date(value).toLocaleString("zh-CN") },
            { title: "结果", key: "result", render: (_: unknown, item: NonNullable<typeof data>["automation"]["recentRuns"][number]) => item.error?.message || (item.release_id ? `数据版本 ${item.release_id.slice(0, 8)}` : "—") },
          ]}
        />
      </Card>

      <Card title="对象级同步清单" extra={<Tag color={data?.coverage.complete ? "success" : "error"}>{data?.coverage.complete ? "覆盖完整" : "覆盖不完整"}</Tag>} loading={status.isLoading}>
        <Table rowKey="className" columns={columns} dataSource={data?.classes || []} pagination={false} scroll={{ x: 1250 }} />
      </Card>

      {configureClass && <SyncClassConfigurationDialog key={configureClass} profileKey={profileKey} className={configureClass} close={() => setConfigureClass(undefined)} saved={async () => {
        await Promise.all(["data-sync", "sync-materialization", "sync-class-configuration"].map(key => queryClient.invalidateQueries({ queryKey: [key] })));
      }} />}
      {data?.activeRelease?.finished_at && <Typography.Text type="secondary">最近数据版本完成于 {new Date(data.activeRelease.finished_at).toLocaleString("zh-CN")}</Typography.Text>}

      <Modal
        open={dialogOpen}
        title="执行受治理数据同步"
        okText="确认同步"
        cancelText="取消"
        confirmLoading={run.isPending}
        okButtonProps={{ disabled: actor.trim().length < 2 || confirmation !== "同步数据" }}
        onCancel={() => !run.isPending && setDialogOpen(false)}
        onOk={() => run.mutate()}
      >
        <Alert showIcon type="warning" message="将读取 Camstar 源数据并激活新的 PostgreSQL 数据版本" description="本操作不会写入 Graph Studio。若质量、数量或 checkpoint 连续性验证失败，活动版本保持不变。" />
        <div className="data-sync-confirm-form">
          <label><span>操作人标识</span><Input value={actor} onChange={(event) => setActor(event.target.value)} /></label>
          <label><span>请输入确认短语：<strong>同步数据</strong></span><Input value={confirmation} onChange={(event) => setConfirmation(event.target.value)} /></label>
        </div>
      </Modal>

      <Modal
        open={scheduleOpen} title="自动数据同步设置" okText="保存设置" cancelText="取消"
        confirmLoading={configure.isPending} onCancel={() => !configure.isPending && setScheduleOpen(false)}
        onOk={() => configure.mutate()}
      >
        <Alert type="info" showIcon message="自动同步只生成 PostgreSQL 不可变数据版本" description="它不会发布或切换 Graph Studio Layer。每个计划窗口由 PostgreSQL 租约唯一领取，失败按指数退避重试。" />
        <div className="data-sync-confirm-form">
          <label><span>启用自动同步</span><Switch checked={scheduleEnabled} onChange={setScheduleEnabled} /></label>
          <label><span>同步间隔（分钟）</span><InputNumber min={1} max={10080} value={intervalMinutes} onChange={(value) => setIntervalMinutes(Number(value || 15))} /></label>
          <label><span>最多尝试次数</span><InputNumber min={1} max={10} value={maxAttempts} onChange={(value) => setMaxAttempts(Number(value || 3))} /></label>
          <label><span>首次重试等待（秒）</span><InputNumber min={5} max={86400} value={retryBackoff} onChange={(value) => setRetryBackoff(Number(value || 60))} /></label>
        </div>
      </Modal>
    </div>
  );
}
