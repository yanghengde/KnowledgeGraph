import {
ApiOutlined,ArrowRightOutlined,CheckCircleFilled,ClockCircleOutlined,
CloudUploadOutlined,CommentOutlined,DatabaseOutlined,ExclamationCircleFilled,
RocketOutlined,SafetyCertificateOutlined,SyncOutlined,
} from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Button,Card,Col,Row,Space,Statistic,Tag,Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { manufacturingApi,syncApi } from "../../../api";
import { useModelScope } from "../../../app/modelScope";
import type { DeploymentRelease,PublicationRoute,SyncRun } from "../../../types";

const environmentLabels: Record<string, string> = { dev: "开发验证", uat: "业务验收", prod: "生产环境" };
const runStatusLabels: Record<string, { color: string; text: string }> = {
  succeeded: { color: "success", text: "成功" }, failed: { color: "error", text: "失败" },
  running: { color: "processing", text: "运行中" }, started: { color: "processing", text: "运行中" },
  queued: { color: "warning", text: "排队中" },
};

function formatTime(value?: string | null, fallback = "暂无记录") {
  if (!value) return fallback;
  return new Date(value).toLocaleString("zh-CN", {
    month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false,
  });
}

function runTitle(run: SyncRun) {
  if (run.trigger_type === "dry_run") return "发布前检验";
  if (run.trigger_type === "preview") return "发布预览";
  if (run.trigger_type === "schedule") return "定时数据同步";
  return run.job_name || "数据同步任务";
}

function latestDeployment(route: PublicationRoute, items: DeploymentRelease[]) {
  return items.find((item) => item.route_key === route.route_key);
}

export function OverviewPage() {
  const { profileKey, profile } = useModelScope();
  const navigate = useNavigate();
  const statusQuery = useQuery({ queryKey: ["manufacturing-status"], queryFn: () => manufacturingApi.status() });
  const savedQueries = useQuery({ queryKey: ["saved-queries"], queryFn: () => manufacturingApi.queries() });
  const connections = useQuery({ queryKey: ["sync-connections"], queryFn: syncApi.connections });
  const jobs = useQuery({ queryKey: ["sync-jobs"], queryFn: syncApi.jobs });
  const runs = useQuery({ queryKey: ["sync-runs"], queryFn: () => syncApi.runs(20) });
  const materialization = useQuery({
    queryKey: ["sync-materialization", profileKey], queryFn: () => syncApi.materialization(profileKey),
  });
  const deployments = useQuery({
    queryKey: ["sync-deployments", profileKey], queryFn: () => syncApi.deployments(profileKey),
  });

  const serviceReady = statusQuery.data?.status === "ready";
  const connectionItems = connections.data?.items || [];
  const enabledConnections = connectionItems.filter((item) => item.enabled);
  const offlineConnections = enabledConnections.filter((item) => item.status !== "online");
  const runItems = (runs.data?.items || []).filter(run => run.job_name === profile?.job_name);
  const latestRun = runItems[0];
  const latestSuccessfulRun = runItems.find((item) => item.status === "succeeded");
  const latestFailedRun = latestRun?.status === "failed" ? latestRun : undefined;
  const activeRelease = materialization.data?.releases.find((item) => item.is_active)
    || deployments.data?.activeCuratedRelease;
  const blockers = materialization.data?.plan.blockers || [];
  const deploymentItems = deployments.data?.deployments || [];
  const routes = deployments.data?.routes || [];
  const productionDeployment = deploymentItems.find(
    (item) => item.environment_key === "prod" && item.status === "active",
  );
  const latestFailedDeployment = routes
    .map((route) => latestDeployment(route, deploymentItems))
    .find((item) => item?.status === "failed");
  const businessHealthy = serviceReady && offlineConnections.length === 0
    && !latestFailedRun && !latestFailedDeployment && blockers.length === 0;

  const attentionItems = [
    ...(offlineConnections.length ? [{
      level: "error", title: `${offlineConnections.length} 个数据连接需要检查`,
      detail: offlineConnections.map((item) => item.display_name).join("、"), route: "/connections",
    }] : []),
    ...(latestFailedRun ? [{
      level: "error", title: "最近存在失败的数据运行",
      detail: `${runTitle(latestFailedRun)} · ${formatTime(latestFailedRun.started_at)}`, route: "/publish",
    }] : []),
    ...(latestFailedDeployment ? [{
      level: "error", title: `${environmentLabels[latestFailedDeployment.environment_key]}最近一次发布失败`,
      detail: `失败发生于 ${formatTime(latestFailedDeployment.finished_at || latestFailedDeployment.started_at)}`, route: "/publish",
    }] : []),
    ...(blockers.length ? [{
      level: "warning", title: `${blockers.length} 项质量门禁待处理`, detail: blockers[0], route: "/publish",
    }] : []),
    ...(!activeRelease ? [{
      level: "warning", title: "尚未激活业务数据版本", detail: "完成发布前检验后生成并激活首个不可变版本", route: "/publish",
    }] : []),
    ...(activeRelease && !productionDeployment ? [{
      level: "info", title: `数据版本 R${activeRelease.release_no} 尚未发布到生产`,
      detail: "可按开发验证、业务验收、生产环境顺序晋级", route: "/publish",
    }] : []),
  ];

  return (
    <div className="page-stack overview-page">
      <section className="overview-hero business-hero">
        <div>
          <Tag color="cyan">MANUFACTURING DATA OPERATIONS</Tag>
          <Typography.Title>制造数据发布与知识服务</Typography.Title>
          <Typography.Paragraph>
            从 Camstar 数据接入、质量验证到 Graph Studio 发布，集中掌握当前业务数据是否可用、可信和最新。
          </Typography.Paragraph>
          <Space wrap>
            <Button type="primary" icon={<CloudUploadOutlined />} onClick={() => navigate("/publish")}>管理数据发布</Button>
            <Button icon={<CommentOutlined />} onClick={() => navigate("/assistant")}>进入制造问答</Button>
          </Space>
        </div>
        <div className={`hero-health ${businessHealthy ? "business-ready" : "business-attention"}`}>
          <span className={`health-ring ${businessHealthy ? "ready" : ""}`}>
            {businessHealthy ? <CheckCircleFilled /> : <ExclamationCircleFilled />}
          </span>
          <div>
            <strong>{businessHealthy ? "业务数据服务正常" : "有事项需要关注"}</strong>
            <small>{businessHealthy
              ? `当前 R${activeRelease?.release_no || "—"} · 数据链路与质量门禁正常`
              : `${attentionItems.length || 1} 项状态可能影响数据发布或知识服务`}</small>
          </div>
        </div>
      </section>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} xl={6}><Card className="metric-card business-metric">
          <Statistic title="生产发布" value={productionDeployment ? "已发布" : "待发布"} prefix={<RocketOutlined />} />
          <span>{productionDeployment ? `数据版本 R${activeRelease?.release_no || "—"}` : "尚无活动生产版本"}</span>
        </Card></Col>
        <Col xs={24} sm={12} xl={6}><Card className="metric-card business-metric">
          <Statistic title="当前数据版本" value={activeRelease ? `R${activeRelease.release_no}` : "—"} prefix={<DatabaseOutlined />} />
          <span>{activeRelease ? `${Number(activeRelease.object_count || 0).toLocaleString()} 个业务对象` : "等待生成首个版本"}</span>
        </Card></Col>
        <Col xs={24} sm={12} xl={6}><Card className="metric-card business-metric">
          <Statistic title="最近数据运行" value={latestRun ? (runStatusLabels[latestRun.status]?.text || latestRun.status) : "—"} prefix={<SyncOutlined />} />
          <span>{formatTime(latestRun?.finished_at || latestRun?.started_at)}</span>
        </Card></Col>
        <Col xs={24} sm={12} xl={6}><Card className="metric-card business-metric">
          <Statistic title="数据质量门禁" value={blockers.length ? `${blockers.length} 项待处理` : "已通过"} prefix={<SafetyCertificateOutlined />} />
          <span>{activeRelease ? `隔离数据 ${Number(activeRelease.quarantine_count || 0).toLocaleString()} 条` : "随数据版本持续校验"}</span>
        </Card></Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={15}>
          <Card className="overview-panel release-status-card"
            title={<div className="overview-card-title"><span>数据发布态势</span><small>同一数据版本按环境逐级验证和发布</small></div>}
            extra={<Button type="link" onClick={() => navigate("/publish")}>查看发布管理 <ArrowRightOutlined /></Button>}
            loading={deployments.isLoading || materialization.isLoading}>
            <div className="environment-overview">
              {routes.length ? routes.map((route, index) => {
                const deployment = latestDeployment(route, deploymentItems);
                const isActive = deployment?.status === "active";
                const failed = deployment?.status === "failed";
                const stateText = isActive ? "已发布" : failed ? "发布失败" : deployment ? "发布处理中" : "等待发布";
                return <div className={`environment-stage ${isActive ? "active" : failed ? "failed" : "pending"}`} key={route.route_key}>
                  <div className="stage-index">{isActive ? <CheckCircleFilled /> : index + 1}</div>
                  <div className="stage-copy"><div><strong>{environmentLabels[route.environment_key] || route.title}</strong><Tag color={isActive ? "success" : failed ? "error" : "default"}>{stateText}</Tag></div>
                    <span>{deployment ? `版本 ${deployment.curated_release_id === activeRelease?.release_id ? `R${activeRelease.release_no}` : String(deployment.curated_release_id).slice(0, 8)} · ${formatTime(deployment.finished_at || deployment.started_at)}` : "完成前置环境后可继续晋级"}</span></div>
                  {index < routes.length - 1 && <ArrowRightOutlined className="stage-arrow" />}
                </div>;
              }) : <div className="overview-empty">尚未配置环境发布路线，请先在数据发布管理中完成配置。</div>}
            </div>
            <div className="release-summary-strip">
              <span><DatabaseOutlined /><small>业务数据版本</small><strong>{activeRelease ? `R${activeRelease.release_no}` : "未激活"}</strong></span>
              <span><SyncOutlined /><small>最近成功同步</small><strong>{formatTime(latestSuccessfulRun?.finished_at || latestSuccessfulRun?.started_at, "暂无")}</strong></span>
              <span><ApiOutlined /><small>知识查询能力</small><strong>{savedQueries.data?.count ?? "—"} 条</strong></span>
              <span><CloudUploadOutlined /><small>启用同步任务</small><strong>{jobs.data?.items.filter((item) => item.enabled).length ?? "—"} 个</strong></span>
            </div>
          </Card>
        </Col>

        <Col xs={24} xl={9}>
          <Card className="overview-panel attention-card"
            title={<div className="overview-card-title"><span>业务关注与待办</span><small>优先显示可能影响数据使用的问题</small></div>}
            extra={<Tag color={attentionItems.length ? "warning" : "success"}>{attentionItems.length ? `${attentionItems.length} 项` : "暂无风险"}</Tag>}>
            <div className="attention-list">
              {attentionItems.length ? attentionItems.slice(0, 4).map((item) => <button className={`attention-item ${item.level}`} key={`${item.title}-${item.route}`} onClick={() => navigate(item.route)}>
                <span className="attention-dot">{item.level === "info" ? "i" : "!"}</span>
                <span><strong>{item.title}</strong><small>{item.detail}</small></span><ArrowRightOutlined />
              </button>) : <div className="all-clear"><CheckCircleFilled /><strong>当前没有发布阻断</strong><span>数据连接、最近运行和版本质量状态均正常。</span></div>}
            </div>
          </Card>
        </Col>
      </Row>

      <Card className="overview-panel recent-runs-card"
        title={<div className="overview-card-title"><span>最近数据运行</span><small>查看数据何时更新、处理规模与执行结果</small></div>}
        extra={<Button type="link" onClick={() => navigate("/publish")}>全部运行记录 <ArrowRightOutlined /></Button>}
        loading={runs.isLoading}>
        <div className="recent-run-list">
          {runItems.slice(0, 4).map((run) => {
            const state = runStatusLabels[run.status] || { color: "default", text: run.status };
            return <div className="recent-run-row" key={run.run_id}>
              <span className={`run-icon ${run.status}`}><ClockCircleOutlined /></span>
              <span className="run-main"><strong>{runTitle(run)}</strong><small>{formatTime(run.started_at)} · {run.trigger_type}</small></span>
              <span className="run-volume"><small>业务对象</small><strong>{Number(run.row_count || 0).toLocaleString()}</strong></span>
              <span className="run-volume"><small>图谱关系</small><strong>{Number(run.triple_count || 0).toLocaleString()}</strong></span>
              <Tag color={state.color}>{state.text}</Tag>
            </div>;
          })}
          {!runItems.length && <div className="overview-empty">尚无数据运行记录，完成首次发布前检验后将在这里展示。</div>}
        </div>
      </Card>
    </div>
  );
}
