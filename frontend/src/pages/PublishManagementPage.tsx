import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloudUploadOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  EyeOutlined,
  HistoryOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, App, Button, Card, Col, Descriptions, Popconfirm, Row, Space, Statistic, Table, Tag, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { syncApi } from "../api";
import type { PublicationRoute, SyncRun } from "../types";

const statusLabels: Record<string, { color: string; text: string }> = {
  succeeded: { color: "success", text: "成功" },
  running: { color: "processing", text: "运行中" },
  failed: { color: "error", text: "失败" },
  started: { color: "processing", text: "已启动" },
};

const environmentLabels: Record<string, string> = { dev: "开发验证", uat: "业务验收", prod: "生产" };

export function PublishManagementPage() {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const jobs = useQuery({ queryKey: ["sync-jobs"], queryFn: syncApi.jobs });
  const runs = useQuery({ queryKey: ["sync-runs"], queryFn: () => syncApi.runs(50) });
  const profiles = useQuery({ queryKey: ["sync-profiles"], queryFn: syncApi.profiles });
  const targets = useQuery({ queryKey: ["sync-targets"], queryFn: syncApi.targets });
  const activeJob = jobs.data?.items[0];

  const refreshRuns = () => void queryClient.invalidateQueries({ queryKey: ["sync-runs"] });
  const dryRun = useMutation({
    mutationFn: syncApi.dryRun,
    onSuccess: () => { message.success("发布前检验已完成，未写入 Graph Studio"); refreshRuns(); },
    onError: (error: Error) => message.error(error.message),
  });
  const preview = useMutation({
    mutationFn: syncApi.preview,
    onSuccess: (result) => {
      message.success(`发布预览已生成：${Number(result.instances || 0).toLocaleString()} 个实例`);
      refreshRuns();
    },
    onError: (error: Error) => message.error(error.message),
  });

  const runColumns: ColumnsType<SyncRun> = [
    { title: "运行时间", dataIndex: "started_at", width: 170, render: (value) => value ? new Date(value).toLocaleString("zh-CN") : "—" },
    { title: "类型", dataIndex: "trigger_type", width: 120, render: (value) => <Tag>{value === "dry_run" ? "发布前检验" : value}</Tag> },
    { title: "状态", dataIndex: "status", width: 100, render: (value) => { const status = statusLabels[value] || { color: "default", text: value }; return <Tag color={status.color}>{status.text}</Tag>; } },
    { title: "实例行", dataIndex: "row_count", align: "right", width: 110, render: (value) => Number(value || 0).toLocaleString() },
    { title: "RDF 三元组", dataIndex: "triple_count", align: "right", width: 130, render: (value) => Number(value || 0).toLocaleString() },
    { title: "质量信息", key: "quality", render: (_, run) => run.error ? <Typography.Text type="danger">{run.error}</Typography.Text> : <Typography.Text type="secondary">悬空引用 {Number(run.metrics?.danglingReferences || 0)} · 类型回退 {Number(run.metrics?.datatypeFallbacks || 0)}</Typography.Text> },
  ];

  return (
    <div className="page-stack operations-page">
      <section className="section-intro operations-heading">
        <div>
          <Typography.Title level={2}>数据发布管理</Typography.Title>
          <Typography.Paragraph>以“先检验、后审批、再发布”为主线管理 Camstar 到 Graph Studio 的可审计发布。</Typography.Paragraph>
        </div>
        <Space wrap>
          <Popconfirm title="执行发布前检验？" description="只生成校验产物，不会写入 Graph Studio。" onConfirm={() => activeJob && dryRun.mutate(activeJob.job_name)}>
            <Button icon={<ExperimentOutlined />} loading={dryRun.isPending} disabled={!activeJob}>执行发布前检验</Button>
          </Popconfirm>
          <Button type="primary" icon={<EyeOutlined />} loading={preview.isPending} disabled={!activeJob} onClick={() => activeJob && preview.mutate(activeJob.job_name)}>生成发布预览</Button>
        </Space>
      </section>

      <Alert
        showIcon
        type="info"
        icon={<SafetyCertificateOutlined />}
        message="当前迁移范围为发布准备区"
        description="本页已接管检验、预览、运行记录和路由可视化；审批与实际发布仍暂留旧中心，待第二轮验证后迁移。"
        action={<Button size="small" href="/sync">打开旧版完整功能</Button>}
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="同步任务" value={jobs.data?.items.length || 0} suffix="个" prefix={<CloudUploadOutlined />} /></Card></Col>
        <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="发布配置" value={profiles.data?.items.length || 0} suffix="个" prefix={<DatabaseOutlined />} /></Card></Col>
        <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="发布目标" value={targets.data?.items.length || 0} suffix="个" prefix={<CheckCircleOutlined />} /></Card></Col>
        <Col xs={24} md={12} xl={6}><Card className="metric-card"><Statistic title="历史运行" value={runs.data?.items.length || 0} suffix="次" prefix={<HistoryOutlined />} /></Card></Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={14}>
          <Card title="当前发布任务" extra={activeJob && <Tag color={activeJob.enabled ? "success" : "default"}>{activeJob.enabled ? "已启用" : "已停用"}</Tag>} loading={jobs.isLoading}>
            {activeJob ? (
              <Descriptions column={{ xs: 1, md: 2 }} size="small">
                <Descriptions.Item label="任务名称">{activeJob.title}</Descriptions.Item>
                <Descriptions.Item label="发布方式">{activeJob.mode === "atomic_snapshot" ? "原子快照" : "分区增量"}</Descriptions.Item>
                <Descriptions.Item label="调度计划"><Space><ClockCircleOutlined />{activeJob.schedule || "手动执行"}</Space></Descriptions.Item>
                <Descriptions.Item label="成功版本保留">最近 {activeJob.retention_success} 个</Descriptions.Item>
                <Descriptions.Item label="Graphmart" span={2}><Typography.Text copyable ellipsis>{activeJob.graphmart_uri || "—"}</Typography.Text></Descriptions.Item>
                <Descriptions.Item label="任务说明" span={2}>{activeJob.description || "—"}</Descriptions.Item>
              </Descriptions>
            ) : <Typography.Text type="secondary">暂无发布任务</Typography.Text>}
          </Card>
        </Col>
        <Col xs={24} xl={10}>
          <Card title="环境发布路由" loading={targets.isLoading}>
            <div className="route-list">
              {(targets.data?.routes || []).map((route: PublicationRoute) => (
                <div className="route-item" key={route.route_key}>
                  <div><strong>{environmentLabels[route.environment_key] || route.environment_key}</strong><small>{route.target_title || route.title}</small></div>
                  <Space size={6}><Tag color={route.apply_enabled ? "success" : "default"}>{route.apply_enabled ? "允许发布" : "已锁定"}</Tag>{route.requires_approval && <Tag color="warning">需审批</Tag>}</Space>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="最近运行记录" extra={<Button type="link" onClick={() => void runs.refetch()}>刷新记录</Button>}>
        <Table rowKey="run_id" columns={runColumns} dataSource={runs.data?.items || []} loading={runs.isLoading} pagination={{ pageSize: 8, showSizeChanger: false }} scroll={{ x: 900 }} />
      </Card>
    </div>
  );
}
