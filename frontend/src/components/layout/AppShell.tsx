import {
ApartmentOutlined,
ApiOutlined,
BranchesOutlined,
CloudSyncOutlined,
CloudUploadOutlined,
CommentOutlined,
DashboardOutlined,
DatabaseOutlined,
MenuFoldOutlined,
MenuUnfoldOutlined,
SafetyCertificateOutlined,
} from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Badge,Button,Layout,Menu,Space,Tag,Typography } from "antd";
import { useState } from "react";
import { Outlet,useLocation,useNavigate } from "react-router-dom";
import { useModelScope } from "../../app/modelScope";
import { ThemeToggle } from "./ThemeToggle";

const { Header, Sider, Content } = Layout;

const routeTitles: Record<string, { title: string; description: string }> = {
  "/overview": { title: "制造数据发布总览", description: "Graph Studio 发布、质量与知识服务运行态势" },
  "/queries": { title: "图谱查询能力库", description: "统一管理可复用、可审计的制造业务 Queries" },
  "/assistant": { title: "制造知识问答", description: "基于当前发布图谱与受控 Query 的上下文问答" },
  "/connections": { title: "数据源与连接", description: "制造数据链路、控制面与 Graph Studio 连接治理" },
  "/data-sync": { title: "制造数据同步", description: "源窗口、增量事件、质量对账与不可变数据版本" },
  "/publish": { title: "数据发布管理", description: "发布前检验、预览、路由与运行记录" },
  "/object-explorer": { title: "物理表目录", description: "物理表、完整字段与双向外键 · 选择语义建模来源" },
  "/ontology-model": { title: "业务模型与审核", description: "选择业务对象，确认字段与关系，审核后发布" },
  "/ontology-governance": { title: "业务模型与审核", description: "选择业务对象，确认字段与关系，审核后发布" },
};

export function AppShell() {
  const { profileKey, selector, unavailable } = useModelScope();
  const health = useQuery({ queryKey: ["control-health"], queryFn: async () => {
    const response = await fetch("/healthz");
    if (!response.ok) throw new Error("控制面暂不可用");
    const value = await response.json();
    if (value.dependencies?.postgresql !== "online") throw new Error("控制面状态待核实");
    return value;
  }, refetchInterval: 30000, retry: false });
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const relativePath = location.pathname.replace(/^\/app/, "") || "/overview";
  const page = routeTitles[relativePath] || routeTitles["/overview"];

  const primaryItems = [
    { key: "/overview", icon: <DashboardOutlined />, label: "工作总览" },
    { key: "/connections", icon: <DatabaseOutlined />, label: "数据源与连接" },
    { key: "/object-explorer", icon: <BranchesOutlined />, label: "物理表目录" },
    { key: "/ontology-model", icon: <ApartmentOutlined />, label: "业务模型与审核" },
    { key: "/data-sync", icon: <CloudSyncOutlined />, label: "制造数据同步" },
    { key: "/publish", icon: <CloudUploadOutlined />, label: "数据发布管理" },
    { key: "/queries", icon: <ApiOutlined />, label: "图谱查询能力" },
    { key: "/assistant", icon: <CommentOutlined />, label: "制造知识问答" },
  ];
  const onMenuClick = ({ key }: { key: string }) => navigate(key);

  return (
    <Layout className="app-shell">
      <Sider width={252} collapsedWidth={72} collapsed={collapsed} className="app-sider">
        <div className={`brand ${collapsed ? "collapsed" : ""}`}>
          <span className="brand-mark">MG</span>
          {!collapsed && (
            <span className="brand-copy">
              <strong>Opcenter Graph</strong>
              <small>Manufacturing Intelligence</small>
            </span>
          )}
        </div>
        <div className="nav-section-label">{collapsed ? "" : "建模与发布工作台"}</div>
        <Menu
          mode="inline"
          theme="dark"
          selectedKeys={[relativePath]}
          items={primaryItems}
          onClick={onMenuClick}
          className="app-menu"
        />
        <div className="sider-foot">
          {!collapsed && (
            <div className="governance-card">
              <SafetyCertificateOutlined />
              <span><strong>受治理发布</strong><small>只读问答 · 证据可追溯</small></span>
            </div>
          )}
        </div>
      </Sider>
      <Layout>
        <Header className="app-header">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed((value) => !value)}
            aria-label={collapsed ? "展开导航" : "收起导航"}
          />
          <div className="page-heading">
            <Typography.Title level={4}>{page.title}</Typography.Title>
            <Typography.Text type="secondary">{page.description}</Typography.Text>
          </div>
          <Space className="header-status" size={12}>
            {["/assistant", "/queries"].includes(relativePath) ? <Tag>已发布查询服务</Tag> : selector}
            <Badge status={health.isError ? "error" : health.isPending ? "default" : "success"}
              text={health.isError ? "控制面不可用" : health.isPending ? "检查连接中" : "控制面已连接"} />
          </Space>
          <ThemeToggle />
        </Header>
        <Content className="app-content">
          {profileKey || ["/connections", "/assistant", "/queries"].includes(relativePath)
            ? <Outlet key={profileKey} /> : unavailable}
        </Content>
      </Layout>
    </Layout>
  );
}
