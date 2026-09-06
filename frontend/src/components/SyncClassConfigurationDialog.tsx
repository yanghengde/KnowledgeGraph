import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, App, Descriptions, Input, Modal, Radio, Space, Spin, Table, Typography } from "antd";
import { syncApi, type SyncClassConfiguration } from "../api";

export function SyncClassConfigurationDialog({ profileKey, className, close, saved }: {
  profileKey: string; className: string; close: () => void; saved: () => Promise<void>;
}) {
  const query = useQuery({ queryKey: ["sync-class-configuration", profileKey, className],
    queryFn: () => syncApi.syncClassConfiguration(profileKey, className), staleTime: 0, retry: false });
  if (!query.data) return <Modal open title={`配置同步 · ${className}`} onCancel={close} footer={null}>
    {query.isError ? <Alert type="error" title="配置读取失败" description={(query.error as Error).message} /> : <Spin />}
  </Modal>;
  return <ConfigurationForm key={query.data.fingerprint} plan={query.data} profileKey={profileKey} close={close} saved={saved} />;
}

function ConfigurationForm({ plan, profileKey, close, saved }: {
  plan: SyncClassConfiguration; profileKey: string; close: () => void; saved: () => Promise<void>;
}) {
  const { message } = App.useApp();
  const [mode, setMode] = useState<"data" | "model_only">(plan.currentMode === "model_only" ? "model_only" : "data");
  const [selected, setSelected] = useState(plan.fields.map(f => f.physical_column));
  const [actor, setActor] = useState("local-console");
  const mutation = useMutation({ mutationFn: () => syncApi.saveSyncClassConfiguration(profileKey, plan.className,
    { mode, selected_columns: selected, fingerprint: plan.fingerprint, actor: actor.trim() }),
    onSuccess: async () => { await saved(); message.success(mode === "data" ? "同步配置已保存，可执行数据同步进行质量检查" : "已设为仅发布模型"); close(); },
    onError: (error: Error) => message.error(error.message),
  });
  const required = new Set([...plan.primaryKeys, ...plan.businessKeys,
    ...plan.fields.filter(f => f.required).map(f => f.physical_column),
    ...plan.relationships.filter(r => r.source === plan.className && r.column).map(r => r.column!)]);
  const blocked = mode === "data" ? plan.blockers.length > 0 : !plan.modelOnlyAllowed;
  return <Modal open width={820} title={`配置同步 · ${plan.className}`} onCancel={close}
    closable={!mutation.isPending} maskClosable={!mutation.isPending} keyboard={!mutation.isPending}
    cancelButtonProps={{ disabled: mutation.isPending }} confirmLoading={mutation.isPending}
    okText={mode === "data" ? "确认并保存同步配置" : "保存为仅发布模型"} cancelText="取消"
    okButtonProps={{ disabled: blocked || !actor.trim() }} onOk={() => mutation.mutate()}>
    <Space orientation="vertical" size={16} style={{ width: "100%" }}>
      <Radio.Group value={mode} disabled={mutation.isPending} onChange={e => setMode(e.target.value)} options={[
        { value: "data", label: "同步业务数据" }, { value: "model_only", label: "仅发布模型", disabled: !plan.modelOnlyAllowed },
      ]} />
      {mode === "model_only" ? <Alert type="info" title="保留对象定义，不采集该对象的业务实例" description="保存后该对象不再阻塞覆盖检查；未来需要实例数据时，可再次打开此配置。" /> : <>
        <Descriptions size="small" column={2} items={[
          { key: "table", label: "源表", children: plan.sourceTable ? `${plan.sourceSchema}.${plan.sourceTable}` : "尚未映射" },
          { key: "strategy", label: "采集方式", children: "小表快照（首次完整采集）" },
          { key: "keys", label: "主键", children: plan.primaryKeys.join("、") || "未识别" },
          { key: "count", label: "采集字段", children: selected.length },
        ]} />
        {plan.blockers.length > 0 && <Alert type="warning" title="需要先补齐以下配置" description={plan.blockers.join("；")} />}
        <Typography.Text type="secondary">字段来自已解析的物理映射与 CSV 主键定义。主键、必填字段和关联所需字段自动保留。</Typography.Text>
        <Table size="small" rowKey="physical_column" dataSource={plan.fields} pagination={{ pageSize: 8 }}
          rowSelection={{ selectedRowKeys: selected, onChange: keys => setSelected(keys as string[]),
            getCheckboxProps: row => ({ disabled: mutation.isPending || required.has(row.physical_column) }) }}
          columns={[{ title: "源字段", dataIndex: "physical_column" }, { title: "本体属性", dataIndex: "property_name" }, { title: "类型", dataIndex: "data_type" }]} />
        {plan.relationships.length > 0 && <Table size="small" rowKey={r => `${r.source}:${r.name}:${r.target}`} dataSource={plan.relationships} pagination={false}
          columns={[{ title: "同时建立的关联", render: (_, r) => `${r.source} → ${r.target} · ${r.name}` },
            { title: "物理外键", dataIndex: "column" }, { title: "检查", render: (_, r) => r.blocker || "映射已解析" }]} />}
        <Alert type="info" title="保存配置后，再执行数据同步" description="本次确认建立数据契约和采集策略。实际数据仍需通过质量检查与数量核对，才会生成活动数据版本。" />
      </>}
      <label>操作人标识<Input value={actor} disabled={mutation.isPending} onChange={e => setActor(e.target.value)} /></label>
    </Space>
  </Modal>;
}
