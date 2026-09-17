import {
ApiOutlined,
CheckCircleFilled,
EditOutlined,
LinkOutlined,
} from "@ant-design/icons";
import { useMutation,useQuery,useQueryClient } from "@tanstack/react-query";
import {
Alert,
App,
Button,
Card,
Col,
Descriptions,
Empty,
Form,
Input,
Modal,
Row,
Space,
Spin,
Switch,
Tag,
Typography,
} from "antd";
import { useState } from "react";
import { syncApi } from "../../../api";
import type { SyncConnection } from "../../../types";

const kindLabels: Record<string, string> = {
  camstar_sqlserver: "Camstar · SQL Server",
  camstar_oracle: "Camstar · Oracle",
  state_postgresql: "控制面 · PostgreSQL",
  graph_studio: "发布端 · Graph Studio",
};

function connectionStatus(connection: SyncConnection) {
  if (!connection.enabled) return { color: "default", text: "已停用" };
  if (connection.status === "online") return { color: "success", text: "在线" };
  if (connection.status === "unknown") return { color: "default", text: "待检测" };
  if (connection.status === "testing") return { color: "processing", text: "检测中" };
  return { color: "error", text: "异常" };
}

export function ConnectionsPage() {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<SyncConnection | null>(null);
  const [form] = Form.useForm<SyncConnection>();
  const connections = useQuery({ queryKey: ["sync-connections"], queryFn: syncApi.connections });

  const testOne = useMutation({
    mutationFn: syncApi.testConnection,
    onSuccess: (result) => {
      result.ok ? message.success("连接验证通过") : message.error(result.detail || "连接验证失败");
      void queryClient.invalidateQueries({ queryKey: ["sync-connections"] });
    },
    onError: (error: Error) => message.error(error.message),
  });
  const testAll = useMutation({
    mutationFn: syncApi.testAllConnections,
    onSuccess: (result) => {
      result.ok ? message.success("全部连接验证通过") : message.warning("部分连接未通过，请查看状态与错误信息");
    },
    onError: (error: Error) => message.error(error.message),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["sync-connections"] }),
  });
  const saveConnection = useMutation({
    mutationFn: syncApi.updateConnection,
    onSuccess: () => {
      message.success("连接参数已更新");
      setEditing(null);
      void queryClient.invalidateQueries({ queryKey: ["sync-connections"] });
    },
    onError: (error: Error) => message.error(error.message),
  });

  const openEditor = (connection: SyncConnection) => {
    setEditing(connection);
    form.setFieldsValue(connection);
  };

  const submitEditor = async () => {
    if (!editing) return;
    const values = await form.validateFields();
    saveConnection.mutate({ ...editing, ...values, config: editing.config });
  };

  return (
    <div className="page-stack operations-page">
      <section className="section-intro operations-heading">
        <div>
          <Typography.Title level={2}>数据源与连接</Typography.Title>
          <Typography.Paragraph>统一维护制造业务源、同步控制面、语义模型与 Graph Studio 发布端连接。</Typography.Paragraph>
        </div>
        <Button type="primary" icon={<ApiOutlined />} loading={testAll.isPending} onClick={() => testAll.mutate()}>检测并刷新</Button>
      </section>

      {connections.isLoading ? <div className="page-loader"><Spin /></div> : connections.isError ? (
        <Alert type="error" showIcon message="连接信息读取失败" description={(connections.error as Error).message} />
      ) : !connections.data?.items.length ? <Empty description="暂无连接配置" /> : (
        <Row gutter={[16, 16]}>
          {connections.data.items.map((connection) => {
            const status = connectionStatus(connection);
            return (
              <Col xs={24} xl={12} key={connection.connection_key}>
                <Card
                  className="connection-card"
                  title={<Space><LinkOutlined /><span>{connection.display_name}</span></Space>}
                  extra={<Tag color={status.color}>{status.text}</Tag>}
                  actions={[
                    <Button key="test" type="text" icon={<CheckCircleFilled />} loading={testOne.isPending && testOne.variables === connection.connection_key} onClick={() => testOne.mutate(connection.connection_key)}>测试连接</Button>,
                    <Button key="edit" type="text" icon={<EditOutlined />} disabled={!connection.editable} onClick={() => openEditor(connection)}>{connection.editable ? "编辑参数" : "环境托管"}</Button>,
                  ]}
                >
                  <Typography.Text className="connection-kind">{kindLabels[connection.kind] || connection.kind}</Typography.Text>
                  <Descriptions column={2} size="small" className="connection-details">
                    <Descriptions.Item label="服务地址" span={2}><Typography.Text copyable ellipsis>{connection.endpoint}</Typography.Text></Descriptions.Item>
                    <Descriptions.Item label="数据库 / 目标">{connection.database_name || "—"}</Descriptions.Item>
                    <Descriptions.Item label="用户">{connection.username || "—"}</Descriptions.Item>
                    <Descriptions.Item label="密钥引用"><Typography.Text code>{connection.secret_ref || "未配置"}</Typography.Text></Descriptions.Item>
                    <Descriptions.Item label="最近检测">{connection.last_tested_at ? new Date(connection.last_tested_at).toLocaleString("zh-CN") : "尚未检测"}</Descriptions.Item>
                  </Descriptions>
                  {connection.last_error && <Alert className="connection-error" type="error" showIcon message={connection.last_error} />}
                </Card>
              </Col>
            );
          })}
        </Row>
      )}

      <Modal title={`编辑连接 · ${editing?.display_name || ""}`} open={Boolean(editing)} onCancel={() => setEditing(null)} onOk={() => void submitEditor()} confirmLoading={saveConnection.isPending} okText="保存参数" cancelText="取消">
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item name="display_name" label="显示名称" rules={[{ required: true, message: "请输入显示名称" }]}><Input /></Form.Item>
          <Form.Item name="endpoint" label="服务地址" extra="由服务器环境配置管理，修改 .env 后需重启服务。"><Input disabled /></Form.Item>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="database_name" label="数据库 / 发布目标"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="username" label="用户"><Input /></Form.Item></Col>
          </Row>
          <Form.Item name="enabled" label="启用状态" valuePropName="checked"><Switch checkedChildren="启用" unCheckedChildren="停用" /></Form.Item>
          <Alert type="warning" showIcon message="保存后建议立即执行一次连接测试；密码请在服务器环境变量中维护。" />
        </Form>
      </Modal>
    </div>
  );
}
