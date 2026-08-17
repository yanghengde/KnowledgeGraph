import {
  ApartmentOutlined,
  ApiOutlined,
  CloudUploadOutlined,
  CommentOutlined,
  DashboardOutlined,
  DatabaseOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { Badge, Button, Layout, Menu, Space, Tag, Typography } from "antd";
import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { ThemeToggle } from "./ThemeToggle";

const { Header, Sider, Content } = Layout;

const routeTitles: Record<string, { title: string; description: string }> = {
  "/overview": { title: "制造数据发布总览", description: "Graph Studio 发布、质量与知识服务运行态势" },
  "/queries": { title: "图谱查询能力库", description: "统一管理可复用、可审计的制造业务 Queries" },
  "/assistant": { title: "制造知识问答", description: "基于当前发布图谱与受控 Query 的上下文问答" },
  "/connections": { title: "数据源与连接", description: "制造数据链路、控制面与 Graph Studio 连接治理" },
  "/publish": { title: "数据发布管理", description: "发布前检验、预览、路由与运行记录" },
};

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const relativePath = location.pathname.replace(/^\/app/, "") || "/overview";
  const page = routeTitles[relativePath] || routeTitles["/overview"];

  const primaryItems = [
    { key: "/overview", icon: <DashboardOutlined />, label: "制造数据总览" },
    { key: "/queries", icon: <ApiOutlined />, label: "图谱查询能力" },
    { key: "/assistant", icon: <CommentOutlined />, label: "制造知识问答" },
    { key: "/connections", icon: <DatabaseOutlined />, label: "数据源与连接" },
    { key: "/publish", icon: <CloudUploadOutlined />, label: "数据发布管理" },
  ];
  const legacyItems = [
    { key: "legacy-ontology", icon: <ApartmentOutlined />, label: "制造语义模型" },
  ];

  const onMenuClick = ({ key }: { key: string }) => {
    if (key === "legacy-ontology") window.location.href = "/ontology";
    else navigate(key);
  };

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
        <div className="nav-section-label">{collapsed ? "" : "制造知识平台"}</div>
        <Menu
          mode="inline"
          theme="dark"
          selectedKeys={[relativePath]}
          items={primaryItems}
          onClick={onMenuClick}
          className="app-menu"
        />
        <div className="nav-section-label legacy-label">{collapsed ? "" : "迁移中的工作台"}</div>
        <Menu
          mode="inline"
          theme="dark"
          selectedKeys={[]}
          items={legacyItems}
          onClick={onMenuClick}
          className="app-menu legacy-menu"
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
            <Tag icon={<DatabaseOutlined />} color="cyan">Graphmart R2</Tag>
            <Badge status="success" text="控制台在线" />
          </Space>
          <ThemeToggle />
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
