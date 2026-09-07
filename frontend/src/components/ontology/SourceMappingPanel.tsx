import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, App, Button, Card, Drawer, Empty, Input, Select, Space, Table, Tag, Typography } from "antd";
import { mappingApi, type FieldRole, type MappingDetail, type MappingField, type MappingPreview, type MappingRow, type SourceDesign, type SourceRole } from "../../mappingApi";

const sourceLabels: Record<SourceRole, string> = { pending: "待评估", entity: "实体来源", event: "事件来源", relationship: "关系来源", auxiliary: "辅助来源", excluded: "暂不采用" };
const fieldLabels: Record<FieldRole, string> = { pending: "待评估", property: "业务属性", relationship: "业务关系", internal: "仅内部使用", excluded: "不纳入本体" };

export function SourceMappingPanel({ onExplore, onReview }: { onExplore: () => void; onReview: () => void }) {
  const list = useQuery({ queryKey: ["mapping-drafts"], queryFn: mappingApi.list });
  const [selected, setSelected] = useState<string>();
  const [search, setSearch] = useState("");
  return <Card title="来源与转换" extra={<Button onClick={onExplore}>选择 Opcenter 来源表</Button>}>
    <Space orientation="vertical" size={16} style={{ width: "100%" }}>
      <Alert type="info" showIcon message="先定义来源用途，再生成本体候选" description="物理表保留完整字段与外键。实体来源可明确选择业务属性和关系；历史、桥接和辅助来源先保存转换设计。保存草稿不会修改已批准或已发布的模型。" />
      {list.isError ? <Alert type="error" showIcon message={(list.error as Error).message} action={<Button onClick={() => void list.refetch()}>重试</Button>} /> : null}
      <Input.Search allowClear placeholder="搜索表名或业务中文名" value={search} onChange={e => setSearch(e.target.value)} />
      <Table<MappingRow> rowKey="draftId" loading={list.isLoading} dataSource={(list.data?.items || []).filter(r => `${r.tableName} ${r.chineseName}`.toLowerCase().includes(search.toLowerCase()))}
        locale={{ emptyText: <Empty description="从 Opcenter 数据模型选择来源表，开始设计" /> }} columns={[
          { title: "来源表", render: (_, row) => <Button type="link" onClick={() => setSelected(row.draftId)}>{row.tableName}</Button> },
          { title: "用途", render: (_, row) => <Tag>{sourceLabels[row.role]}</Tag> },
          { title: "业务名称", render: (_, row) => row.chineseName || "待定义" },
          { title: "物理版本", render: (_, row) => <Typography.Text title={row.snapshotId}>{row.snapshotId.slice(0, 12)}</Typography.Text> },
          { title: "草稿修订", render: (_, row) => `R${row.revision}` },
          { title: "操作", render: (_, row) => <Button onClick={() => setSelected(row.draftId)}>设计映射</Button> },
        ]} />
    </Space>
    <Drawer title="来源映射设计" size="large" open={!!selected} onClose={() => setSelected(undefined)} destroyOnHidden>
      {selected && <MappingEditor key={selected} id={selected} onReview={() => { setSelected(undefined); onReview(); }} />}
    </Drawer>
  </Card>;
}

function MappingEditor({ id, onReview }: { id: string; onReview: () => void }) {
  const detail = useQuery({ queryKey: ["mapping-detail", id], queryFn: () => mappingApi.detail(id) });
  if (detail.isError) return <Alert type="error" message={(detail.error as Error).message} />;
  return detail.data ? <MappingForm key={detail.data.revision} detail={detail.data} onReview={onReview} /> : <Card loading />;
}

function MappingForm({ detail, onReview }: { detail: MappingDetail; onReview: () => void }) {
  const { message } = App.useApp();
  const client = useQueryClient();
  const [design, setDesign] = useState<SourceDesign>(detail.design);
  const [preview, setPreview] = useState<MappingPreview>();
  const [dirty, setDirty] = useState(false);
  const [search, setSearch] = useState("");
  const [showExcluded, setShowExcluded] = useState(true);
  const error = (e: Error) => message.error(e.message);
  const save = useMutation({ mutationFn: () => mappingApi.save(detail.draftId, detail.revision, design), onSuccess: async data => {
    message.success("来源设计已保存");
    client.setQueryData(["mapping-detail", detail.draftId], data);
    await client.invalidateQueries({ queryKey: ["mapping-drafts"] });
  }, onError: error });
  const plan = useMutation({ mutationFn: () => mappingApi.preview(detail.draftId), onSuccess: setPreview, onError: error });
  const submit = useMutation({ mutationFn: () => mappingApi.submit(detail.draftId, detail.revision, preview!.planHash), onSuccess: async () => {
    await client.invalidateQueries({ queryKey: ["ontology-directory"] });
    message.success("映射候选已生成，请在本体设计中审阅"); onReview();
  }, onError: error });
  const busy = save.isPending || plan.isPending || submit.isPending;
  const change = (patch: Partial<SourceDesign>) => { setDesign({ ...design, ...patch }); setDirty(true); setPreview(undefined); };
  const bulkExclude = () => change({ fields: Object.fromEntries(detail.fields.map(f => [f.name, design.fields[f.name] === "pending" ? (f.primaryKey ? "internal" : "excluded") : design.fields[f.name]])) });
  return <Space orientation="vertical" size={16} style={{ width: "100%" }}>
    <Typography.Text strong>{detail.tableName} · 草稿 R{detail.revision}{dirty ? " · 有未保存修改" : ""}</Typography.Text>
    <Typography.Text type="secondary">物理快照 {detail.snapshotId.slice(0, 12)} · 表和字段原始定义完整保留</Typography.Text>
    <Select aria-label="来源用途" disabled={busy} style={{ width: "100%" }} value={design.role} onChange={role => change({ role })} options={Object.entries(sourceLabels).map(([value, label]) => ({ value, label }))} />
    {design.role !== "entity" && <Alert type="info" message="此用途先保存为来源设计" description="事件来源需明确行为判别、事件身份、时间和撤销规则；关系来源需明确两端身份。当前生成器只支持一表一实体映射，设计说明不会作为可执行转换规则。" />}
    <Input disabled={busy} addonBefore="业务中文名" value={design.chineseName} maxLength={200} onChange={e => change({ chineseName: e.target.value })} />
    <Input.TextArea disabled={busy} aria-label="业务定义" placeholder="这个业务对象是什么？" value={design.description} maxLength={16000} onChange={e => change({ description: e.target.value })} autoSize={{ minRows: 2, maxRows: 5 }} />
    <Input.TextArea disabled={busy} aria-label="转换设计说明" placeholder="转换设计说明：所需明细表、行为判别、对象身份、时间或撤销规则。此说明用于后续建模，不执行 SQL。" value={design.notes} maxLength={16000} onChange={e => change({ notes: e.target.value })} autoSize={{ minRows: 3, maxRows: 8 }} />
    <Alert type="info" message="字段用途决定本体内容" description="业务属性进入本体；业务关系使用 Navigation 外键；身份及关联所需字段可仅内部使用。不纳入的字段仍保留在物理快照中。隐藏行只改变此处的显示。" />
    <Space wrap>
      <Input.Search allowClear placeholder="查找字段" value={search} onChange={e => setSearch(e.target.value)} />
      <Button disabled={busy} onClick={bulkExclude}>剩余待评估字段设为不纳入</Button>
      <Button onClick={() => setShowExcluded(!showExcluded)}>{showExcluded ? "隐藏不纳入字段" : "显示全部字段"}</Button>
    </Space>
    <Table<MappingField> rowKey="name" size="small" pagination={{ pageSize: 12 }} dataSource={detail.fields.filter(f => (showExcluded || design.fields[f.name] !== "excluded") && `${f.name} ${f.physicalName}`.toLowerCase().includes(search.toLowerCase()))} columns={[
      { title: "物理字段 / 本体名称", render: (_, field) => <><div>{field.physicalName}{field.primaryKey && <Tag>身份键</Tag>}</div><Typography.Text type="secondary">{field.name}</Typography.Text></> },
      { title: "类型 / 外键终点", render: (_, field) => <>{field.type}<br />{field.target}</> },
      { title: "用途", width: 150, render: (_, field) => <Select aria-label={`${field.physicalName} 用途`} disabled={busy} style={{ width: "100%" }} value={design.fields[field.name]} onChange={role => change({ fields: { ...design.fields, [field.name]: role } })} options={Object.entries(fieldLabels).map(([value, label]) => ({ value, label,
        disabled: field.primaryKey ? !["internal", "property"].includes(value) || (value === "property" && field.type === "Navigation") : value === "relationship" ? field.type !== "Navigation" || !field.target : value === "property" && field.type === "Navigation" }))} /> },
    ]} />
    <Space wrap>
      <Button type="primary" disabled={busy || !dirty} loading={save.isPending} onClick={() => save.mutate()}>保存来源设计</Button>
      <Button disabled={busy || dirty || design.role !== "entity"} loading={plan.isPending} onClick={() => plan.mutate()}>预览本体候选</Button>
    </Space>
    {preview && <>
      <Alert type={preview.blockers.length ? "warning" : "success"} showIcon message={`${preview.counts.properties} 个业务属性 · ${preview.counts.relationships} 条关系 · ${preview.counts.internal} 个内部字段 · ${preview.counts.excluded} 个不纳入字段`} description={preview.blockers.join("；") || "候选仅包含明确选定的字段和关系，仍需审阅后才能进入发布工作区。"} />
      <Button type="primary" disabled={busy || dirty || !!preview.blockers.length} loading={submit.isPending} onClick={() => submit.mutate()}>生成候选并前往审阅</Button>
    </>}
  </Space>;
}
