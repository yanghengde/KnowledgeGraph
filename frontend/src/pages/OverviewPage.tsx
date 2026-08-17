import {
  ApiOutlined,
  CheckCircleOutlined,
  CloudServerOutlined,
  CommentOutlined,
  DeploymentUnitOutlined,
  RightOutlined,
} from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Button, Card, Col, Progress, Row, Space, Statistic, Steps, Tag, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { manufacturingApi } from "../api";

export function OverviewPage() {
  const navigate = useNavigate();
  const statusQuery = useQuery({ queryKey: ["manufacturing-status"], queryFn: manufacturingApi.status });
  const savedQueries = useQuery({ queryKey: ["saved-queries"], queryFn: () => manufacturingApi.queries() });
  const ready = statusQuery.data?.status === "ready";

  return (
    <div className="page-stack">
      <section className="overview-hero">
        <div>
          <Tag color="cyan">INDUSTRIAL KNOWLEDGE OPERATIONS</Tag>
          <Typography.Title>制造知识图谱控制台</Typography.Title>
          <Typography.Paragraph>
            统一管理 Camstar 数据、制造语义模型、Graph Studio 发布版本与基于证据的知识问答。
          </Typography.Paragraph>
          <Space>
            <Button type="primary" icon={<CommentOutlined />} onClick={() => navigate("/assistant")}>进入制造问答</Button>
            <Button icon={<ApiOutlined />} onClick={() => navigate("/queries")}>查看查询能力</Button>
          </Space>
        </div>
        <div className="hero-health">
          <span className={ready ? "health-ring ready" : "health-ring"}>{ready ? "在线" : "检查"}</span>
          <div><strong>知识服务</strong><small>{statusQuery.data?.detail || "正在读取服务状态"}</small></div>
        </div>
      </section>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} xl={6}>
          <Card className="metric-card"><Statistic title="Graph Studio" value={statusQuery.data?.graphstudio || "检查中"} prefix={<CloudServerOutlined />} /></Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="metric-card"><Statistic title="受控 Queries" value={savedQueries.data?.count ?? 0} suffix="条" prefix={<ApiOutlined />} /></Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="metric-card"><Statistic title="大模型服务" value={statusQuery.data?.llm || "检查中"} prefix={<DeploymentUnitOutlined />} /></Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className="metric-card"><Statistic title="数据版本" value="R2" prefix={<CheckCircleOutlined />} /></Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={15}>
          <Card title="前端现代化迁移路线" extra={<Tag color="processing">阶段 4 进行中</Tag>}>
            <Steps
              current={3}
              items={[
                { title: "平台框架", description: "统一导航、主题与接口层" },
                { title: "知识问答", description: "历史会话与 Query 路由" },
                { title: "发布中心", description: "任务、版本、质量门禁" },
                { title: "本体工作台", description: "语义建模与图谱视图" },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} xl={9}>
          <Card title="迁移完成度" extra="新旧页面并行">
            <Progress percent={90} strokeColor="#28d7b5" trailColor="#19333e" />
            <Typography.Paragraph type="secondary" className="migration-note">
              本体治理与版本流程已迁移；复杂图形化编辑暂保留旧版回退入口。
            </Typography.Paragraph>
            <Button type="link" icon={<RightOutlined />} onClick={() => navigate("/publish")}>查看发布管理页面</Button>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
