import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, App, Button, Card, Checkbox, Collapse, Drawer, Empty, Input, Radio, Space, Table, Tag, Typography } from "antd";
import { mappingApi, type MappingDetail, type MappingRow, type SimpleCheck } from "../../mappingApi";
import { syncApi } from "../../api";
import { useMappingAutosave } from "./useMappingAutosave";

export function SourceMappingPanel({ onExplore, onReview }: { onExplore: () => void; onReview: () => void }) {
  const { message } = App.useApp();
  const client = useQueryClient();
  const list = useQuery({ queryKey: ["mapping-drafts"], queryFn: mappingApi.list });
  const [selected, setSelected] = useState<string>();
  const [search, setSearch] = useState("");
  const flush = useRef<(() => Promise<void>) | null>(null);
  const close = async () => { try { await flush.current?.(); setSelected(undefined); await client.invalidateQueries({ queryKey: ["mapping-drafts"] }); } catch { message.error("修改尚未保存，请重试后关闭"); } };
  return <Card title="我的业务对象" extra={<Button onClick={onExplore}>添加对象</Button>}>
    <Space orientation="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Paragraph>填写业务名称，勾选需要的字段。修改会自动保存。</Typography.Paragraph>
      {list.isError && <Alert type="error" message={(list.error as Error).message} action={<Button onClick={() => void list.refetch()}>重试</Button>} />}
      <Input.Search allowClear placeholder="查找业务名称或表名" value={search} onChange={e => setSearch(e.target.value)} />
      <Table<MappingRow> rowKey="draftId" loading={list.isLoading} dataSource={(list.data?.items || []).filter(r => `${r.tableName} ${r.chineseName}`.toLowerCase().includes(search.toLowerCase()))}
        locale={{ emptyText: <Empty description="还没有业务对象"><Button type="primary" onClick={onExplore}>从数据表开始</Button></Empty> }} columns={[
          { title: "业务对象", render: (_, r) => <Button type="link" onClick={() => setSelected(r.draftId)}>{r.chineseName || r.tableName}</Button> },
          { title: "来自哪张表", dataIndex: "tableName" },
          { title: "状态", render: (_, r) => <Tag>{["event", "relationship", "auxiliary"].includes(r.role) ? "需要转换" : r.role === "excluded" ? "暂不使用" : "建模中"}</Tag> },
          { title: "操作", render: (_, r) => <Button onClick={() => setSelected(r.draftId)}>编辑</Button> },
        ]} />
    </Space>
    <Drawer title="编辑业务对象" size="large" open={!!selected} onClose={() => void close()} destroyOnHidden>
      {selected && <Editor key={selected} id={selected} register={fn => { flush.current = fn; }} done={() => { setSelected(undefined); onReview(); }} />}
    </Drawer>
  </Card>;
}

function Editor({ id, register, done }: { id: string; register: (fn: (() => Promise<void>) | null) => void; done: () => void }) {
  const query = useQuery({ queryKey: ["mapping-detail", id], queryFn: () => mappingApi.detail(id), refetchOnWindowFocus: false, staleTime: 0 });
  if (query.isError) return <Alert type="error" message={(query.error as Error).message} />;
  return query.isFetching ? <Card loading /> : query.data ? <Form detail={query.data} register={register} done={done} /> : null;
}

function Form({ detail, register, done }: { detail: MappingDetail; register: (fn: (() => Promise<void>) | null) => void; done: () => void }) {
  const { message } = App.useApp();
  const client = useQueryClient();
  const autosave = useMappingAutosave(detail);
  const { design, flush, revision, status, error } = autosave;
  const [preview, setPreview] = useState<SimpleCheck>();
  const [workspace, setWorkspace] = useState("");
  const [search, setSearch] = useState("");
  const [showAll, setShowAll] = useState(true);
  useEffect(() => { register(flush); return () => register(null); }, [flush]);
  const change = (patch: Parameters<typeof autosave.change>[0]) => { autosave.change(patch); setPreview(undefined); };
  const check = useMutation({ mutationFn: async () => {
    autosave.change({ fields: Object.fromEntries(detail.fields.map(f => [f.name, design.fields[f.name] === "pending" ? (f.primaryKey ? "internal" : "excluded") : design.fields[f.name]])) });
    await flush();
    const governance = await syncApi.ontologyGovernance("opcenter2607-core");
    if (!governance.currentWorkspace) throw new Error("尚未配置发布模型，请在高级管理中初始化");
    const key = governance.currentWorkspace.workspace_key; setWorkspace(key); return mappingApi.check(detail.draftId, key);
  }, onSuccess: setPreview, onError: (e: Error) => message.error(e.message) });
  const apply = useMutation({ mutationFn: async () => { await flush(); return mappingApi.ready(detail.draftId, workspace, revision.current, preview!.planHash); }, onSuccess: async () => {
    done(); await Promise.all(["ontology-directory", "ontology-governance", "semantic-graph-overview", "semantic-graph-stats", "mapping-detail", "mapping-drafts"].map(key => client.invalidateQueries({ queryKey: [key] })));
    message.success("已加入待发布模型");
  }, onError: (e: Error) => { setPreview(undefined); message.error(e.message); } });
  const busy = check.isPending || apply.isPending;
  const chosen = (name: string) => ["property", "relationship"].includes(design.fields[name]);
  const fields = detail.fields.filter(f => !f.primaryKey);
  return <Space orientation="vertical" size={16} style={{ width: "100%" }}>
    <Space><Typography.Text type="secondary">来源：{detail.tableName}</Typography.Text><Tag>{status}</Tag></Space>
    {error && <Alert type="error" message={error} action={<Button onClick={() => void flush().catch(() => {})}>重试保存</Button>} />}
    <Typography.Text strong>这张表如何使用？</Typography.Text>
    <Radio.Group disabled={busy} value={design.role === "pending" ? undefined : design.role === "entity" ? "entity" : "event"} onChange={e => change({ role: e.target.value })} options={[{ value: "entity", label: "普通业务对象" }, { value: "event", label: "需要转换（历史记录等）" }]} />
    <Input disabled={busy} addonBefore="业务名称" placeholder="例如：产品、生产批次" value={design.chineseName} maxLength={200} onChange={e => change({ chineseName: e.target.value })} />
    <Input.TextArea disabled={busy} aria-label="业务说明" placeholder="用一句话说明这个对象的含义" value={design.description} maxLength={16000} onChange={e => change({ description: e.target.value })} autoSize={{ minRows: 2, maxRows: 4 }} />
    {design.role !== "entity" ? <>
      <Alert type="info" message={design.role === "pending" ? "先选择使用方式" : "先记下来，稍后处理"} description="历史记录等数据需要转换后才能使用。可以先写下希望得到的业务对象，说明会自动保存。" />
      <Input.TextArea disabled={busy} placeholder="例如：从历史记录中整理出每个批次的过站事件" value={design.notes} maxLength={16000} onChange={e => change({ notes: e.target.value })} autoSize={{ minRows: 3, maxRows: 6 }} />
    </> : <>
      <Typography.Text strong>选择需要的字段 · 已选 {fields.filter(f => chosen(f.name)).length} 项</Typography.Text>
      <Typography.Text type="secondary">勾选需要分析的内容即可。关联会自动识别，必要的身份字段由系统保留。</Typography.Text>
      <Space wrap><Input.Search allowClear placeholder="搜索字段" value={search} onChange={e => setSearch(e.target.value)} /><Checkbox checked={showAll} onChange={e => setShowAll(e.target.checked)}>显示未选字段</Checkbox></Space>
      <Table rowKey="name" size="small" pagination={{ pageSize: 10 }} dataSource={fields.filter(f => (showAll || chosen(f.name)) && `${f.name} ${f.physicalName}`.toLowerCase().includes(search.toLowerCase()))} columns={[
        { title: "使用", width: 55, render: (_, f) => <Checkbox aria-label={`使用 ${f.physicalName}`} disabled={busy} checked={chosen(f.name)} onChange={e => change({ fields: { ...design.fields, [f.name]: e.target.checked ? f.type === "Navigation" ? "relationship" : "property" : "excluded" } })} /> },
        { title: "字段", dataIndex: "physicalName" }, { title: "含义", render: (_, f) => f.target ? `关联 ${f.target}` : f.name },
      ]} />
      <Button type="primary" disabled={busy} loading={check.isPending} onClick={() => check.mutate()}>检查这个对象</Button>
      {preview && <Card size="small" title="检查结果"><Space orientation="vertical" style={{ width: "100%" }}>
        <Alert showIcon type={preview.blockers.length ? "warning" : "success"} message={preview.blockers.length ? "这些内容需要处理" : `${preview.counts.properties} 个字段、${preview.counts.relationships} 条关联，可以加入发布模型`} description={preview.blockers.join("；") || "确认后，系统会完成模型审阅和准备。"} />
        {preview.removedFields.length > 0 && <Alert type="warning" message={`将从待发布模型移除 ${preview.removedFields.length} 个字段`} description={preview.removedFields.join("、")} />}
        <Collapse items={[{ key: "fields", label: "查看本次字段", children: preview.fields.map(f => <Tag key={f.name}>{f.name}</Tag>) }]} />
        <Button type="primary" disabled={busy || !!preview.blockers.length} loading={apply.isPending} onClick={() => apply.mutate()}>确认并进入检查发布</Button>
      </Space></Card>}
    </>}
    <Collapse items={[{ key: "details", label: "技术信息", children: <Typography.Paragraph>结构版本：{detail.snapshotId}<br />身份字段：{detail.fields.filter(f => f.primaryKey).map(f => f.physicalName).join("、") || "待核实"}</Typography.Paragraph> }]} />
  </Space>;
}
