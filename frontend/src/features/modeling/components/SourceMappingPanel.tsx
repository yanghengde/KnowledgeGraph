import { RelationshipChangeReview } from "./RelationshipChangeReview";
import { useMutation,useQuery,useQueryClient } from "@tanstack/react-query";
import { Alert,App,Button,Card,Checkbox,Collapse,Drawer,Empty,Input,Popconfirm,Radio,Segmented,Select,Space,Steps,Table,Tag,Tooltip,Typography } from "antd";
import { useEffect,useRef,useState } from "react";
import { syncApi } from "../../../api";
import { useModelEditLock,useModelScope } from "../../../app/modelScope";
import { mappingApi,type MappingDetail,type MappingRow,type SimpleCheck } from "../../../mappingApi";
import { useMappingAutosave } from "./useMappingAutosave";

export function SourceMappingPanel({ onExplore, onReview }: { onExplore: () => void; onReview: () => void }) {
  const { profileKey } = useModelScope();
  const { message } = App.useApp();
  const client = useQueryClient();
  const list = useQuery({ queryKey: ["mapping-drafts"], queryFn: mappingApi.list });
  const [deleted, setDeleted] = useState(false);
  const trash = useQuery({ queryKey: ["mapping-deleted"], queryFn: mappingApi.deleted, enabled: deleted });
  const governance = useQuery({ queryKey: ["ontology-governance", profileKey], queryFn: () => syncApi.ontologyGovernance(profileKey) });
  const removal = useMutation({ mutationFn: (row: MappingRow) => mappingApi.remove(row.draftId, row.revision, !deleted), onSuccess: async () => {
    await Promise.all(["mapping-drafts", "mapping-deleted", "mapping-detail"].map(key => client.invalidateQueries({ queryKey: [key] })));
    message.success(deleted ? "草稿已恢复" : "草稿已删除，可在“已删除”中恢复");
  }, onError: (error: Error) => message.error(error.message) });
  const rows = (deleted ? trash.data : list.data)?.items || [];
  const releaseClasses = (governance.data?.activeReleaseGraph?.classes || []) as Array<{ class: { sourceClass?: string; role?: string } }>;
  const inRelease = (row: MappingRow) => releaseClasses.some(c => c.class.sourceClass === row.tableName && c.class.role !== "excluded");
  const inWorkspace = (row: MappingRow) => governance.data?.graph.nodes.some(n => n.data.sourceClass === row.tableName && n.data.role !== "excluded" && n.data.published !== false);
  const graphState = (row: MappingRow) => !governance.data || governance.isError ? "状态待核实" : inRelease(row) ? "已在启用本体中" : inWorkspace(row) ? "待发布" : "未加入模型";
  const [filter, setFilter] = useState("全部");
  const [selected, setSelected] = useState<string>();
  const [search, setSearch] = useState("");
  const flush = useRef<(() => Promise<void>) | null>(null);
  const close = async () => { try { await flush.current?.(); setSelected(undefined); await client.invalidateQueries({ queryKey: ["mapping-drafts"] }); } catch { message.error("修改尚未保存，请重试后关闭"); } };
  return <Card title={<Space><span>{deleted ? "已删除对象" : "我的业务对象"}</span><Typography.Text type="secondary">{rows.length}</Typography.Text></Space>} extra={<Button type="text" onClick={() => { setDeleted(!deleted); setFilter("全部"); }}>{deleted ? "返回业务对象" : "已删除"}</Button>}>
    <Space orientation="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Text type="secondary">来源草稿可跨模型复用；下方状态对应页头选择的当前模型。</Typography.Text>
      {governance.isError && <Alert type="warning" message="图谱状态读取失败，不能据此判断对象尚未发布" action={<Button onClick={() => void governance.refetch()}>重试</Button>} />}
      {trash.isError && deleted && <Alert type="error" message="已删除草稿读取失败" />}
      {list.isError && <Alert type="error" message={(list.error as Error).message} action={<Button onClick={() => void list.refetch()}>重试</Button>} />}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
        <Input.Search style={{ flex: "1 1 240px" }} allowClear placeholder="查找业务名称或表名" value={search} onChange={e => setSearch(e.target.value)} />
        {!deleted && <Select aria-label="筛选模型状态" style={{ width: 180 }} value={filter} onChange={setFilter} options={["全部", "未加入模型", "待发布", "已在启用本体中"].map(value => ({ value, label: value === "全部" ? "全部状态" : value }))} />}
      </div>
      <Table<MappingRow> rowKey="draftId" loading={deleted ? trash.isLoading : list.isLoading} dataSource={rows.filter(r => (filter === "全部" || graphState(r) === filter) && `${r.tableName} ${r.chineseName}`.toLowerCase().includes(search.toLowerCase()))}
        locale={{ emptyText: <Empty description={deleted ? "没有已删除草稿" : "没有匹配的业务对象"}>{!deleted && !search && filter === "全部" && <Button type="primary" onClick={onExplore}>添加业务对象</Button>}</Empty> }} columns={[
          { title: "业务对象", render: (_, r) => <Button type="link" disabled={deleted} onClick={() => setSelected(r.draftId)}>{r.chineseName || r.tableName}</Button> },
          { title: "来源表", dataIndex: "tableName" },
          { title: "状态", render: (_, r) => <Space wrap>
            <Tooltip title={graphState(r) === "状态待核实" ? "正在读取模型状态或读取失败，请刷新后重试。" : graphState(r) === "已在启用本体中" ? "启用版本包含此对象；草稿的新修改仍需检查发布，业务数据需另行同步。" : graphState(r) === "待发布" ? "对象已加入待发布模型，请到“检查发布”继续。" : "编辑对象并检查后，可加入待发布模型。"}><Tag color={graphState(r) === "已在启用本体中" ? "green" : graphState(r) === "待发布" ? "blue" : undefined}>{graphState(r)}</Tag></Tooltip>
            {["event", "relationship", "auxiliary"].includes(r.role) && <Tag color="orange">需要转换</Tag>}
            {r.role === "excluded" && <Tag>暂不使用</Tag>}
          </Space> },
          { title: "操作", width: 210, render: (_, r) => deleted ? <Button loading={removal.isPending} onClick={() => removal.mutate(r)}>恢复草稿</Button> : <Space><Button onClick={() => setSelected(r.draftId)}>编辑</Button><Popconfirm title={`删除 ${r.chineseName || r.tableName} 的草稿？`} description="仅移入已删除列表，可恢复。待发布模型和已发布图谱中的对象保持不变。" onConfirm={() => removal.mutateAsync(r)} okText="删除草稿" cancelText="取消"><Button danger loading={removal.isPending}>删除草稿</Button></Popconfirm></Space> },
        ]} />
    </Space>
    <Drawer title="编辑业务对象" size="large" open={!!selected} onClose={() => void close()} destroyOnHidden>
      {selected && <MappingEditor key={selected} id={selected} register={fn => { flush.current = fn; }} done={() => { setSelected(undefined); onReview(); }} />}
    </Drawer>
  </Card>;
}

export function MappingEditor({ id, register, done, inline = false, onBusy }: { id: string; register: (fn: (() => Promise<void>) | null) => void; done: () => void; inline?: boolean; onBusy?: (busy: boolean) => void }) {
  const query = useQuery({ queryKey: ["mapping-detail", id], queryFn: () => mappingApi.detail(id), refetchOnWindowFocus: false, staleTime: 0 });
  if (query.isError) return <Alert type="error" message={(query.error as Error).message} />;
  return query.isFetching ? <Card loading /> : query.data ? <Form detail={query.data} register={register} done={done} inline={inline} onBusy={onBusy} /> : null;
}

function Form({ detail, register, done, inline, onBusy }: { detail: MappingDetail; register: (fn: (() => Promise<void>) | null) => void; done: () => void; inline: boolean; onBusy?: (busy: boolean) => void }) {
  const { profileKey } = useModelScope();
  const { message } = App.useApp();
  const client = useQueryClient();
  useModelEditLock();
  const autosave = useMappingAutosave(detail);
  const descriptions = useQuery({ queryKey: ["mapping-descriptions", detail.draftId, detail.snapshotId], queryFn: () => mappingApi.descriptions(detail.draftId), staleTime: 300000, retry: false });
  const { design, flush, revision, status, error } = autosave;
  const [preview, setPreview] = useState<SimpleCheck>();
  const [workspace, setWorkspace] = useState("");
  const [search, setSearch] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [fieldView, setFieldView] = useState("properties");
  useEffect(() => { register(flush); return () => register(null); }, [flush]);
  const change = (patch: Parameters<typeof autosave.change>[0]) => { autosave.change(patch); setPreview(undefined); };
  const check = useMutation({ mutationFn: async () => {
    autosave.change({ fields: Object.fromEntries(detail.fields.map(f => [f.name, design.fields[f.name] === "pending" ? (f.primaryKey ? "internal" : "excluded") : design.fields[f.name]])) });
    await flush();
    const governance = await syncApi.ontologyGovernance(profileKey);
    if (!governance.currentWorkspace) throw new Error("尚未配置发布模型，请联系管理员初始化发布工作区");
    const key = governance.currentWorkspace.workspace_key; setWorkspace(key); return mappingApi.check(detail.draftId, key);
  }, onSuccess: setPreview, onError: (e: Error) => message.error(e.message) });
  const apply = useMutation({ mutationFn: async () => { await flush(); return mappingApi.ready(detail.draftId, workspace, revision.current, preview!.planHash); }, onSuccess: async () => {
    done(); await Promise.all(["ontology-directory", "ontology-governance", "semantic-graph-overview", "semantic-graph-stats", "mapping-detail", "mapping-drafts"].map(key => client.invalidateQueries({ queryKey: [key] })));
    message.success("已加入待发布模型");
  }, onError: (e: Error) => { setPreview(undefined); message.error(e.message); } });
  const busy = check.isPending || apply.isPending;
  useEffect(() => { onBusy?.(busy); return () => onBusy?.(false); }, [busy, onBusy]);
  const chosen = (name: string) => ["property", "relationship"].includes(design.fields[name]);
  const fields = detail.fields.filter(f => !f.primaryKey);
  const recommended = (name: string) => ["property", "relationship"].includes(detail.recommendations?.[name]?.role || "");
  const otherCount = fields.filter(f => !chosen(f.name) && !recommended(f.name)).length;
  const searchText = search.trim().toLowerCase();
  const visibleFields = fields.filter(f => (searchText || (fieldView === "relationships" ? f.type === "Navigation" : f.type !== "Navigation")) && (showAll || searchText || fieldView === "relationships" || chosen(f.name) || recommended(f.name))
    && `${f.name} ${f.physicalName} ${f.target} ${detail.recommendations?.[f.name]?.reason || ""} ${descriptions.data?.fields[f.physicalName.toLowerCase()]?.descriptionZh || ""} ${descriptions.data?.fields[f.physicalName.toLowerCase()]?.descriptionEn || ""}`.toLowerCase().includes(searchText));
  return <Space orientation="vertical" size={16} style={{ width: "100%" }}>
    <Steps size="small" current={preview ? 2 : design.role === "entity" ? 1 : 0} items={[
      { title: "定义业务对象" }, { title: "确认字段与关系" }, { title: "检查并加入模型" },
    ]} />
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
      <Typography.Text strong>业务字段 · 已选 {fields.filter(f => chosen(f.name)).length} 项</Typography.Text>
      <Typography.Text type="secondary">基础字段已推荐勾选，已有选择保留。关联按需勾选；未勾选字段不加入模型，主键由系统保留。</Typography.Text>
      <Segmented aria-label="字段类型" value={fieldView} onChange={setFieldView} options={[
        { value: "properties", label: `业务属性（${fields.filter(f => f.type !== "Navigation").length}）` },
        { value: "relationships", label: `关系审阅（${fields.filter(f => f.type === "Navigation").length}）` },
      ]} />
      {fieldView === "relationships" && <Alert showIcon type="info" message="物理关联需要业务确认"
        description="逐条核对来源字段、关联对象和业务含义。勾选表示纳入本次建模选择，不表示实例数据已经验证，也不会直接发布。" />}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}>
        <Input.Search style={{ flex: "1 1 220px" }} allowClear placeholder="搜索字段、描述或关联对象" value={search} onChange={e => setSearch(e.target.value)} />
        <Button type="link" onClick={() => setShowAll(!showAll)}>{showAll ? "收起其他字段" : `查看其他字段（${otherCount}）`}</Button>
      </div>
      {(descriptions.isError || descriptions.data?.warning) && <Alert type="warning" showIcon message={descriptions.data?.warning || "Designer 说明暂不可用，不影响字段选择"} action={<Button size="small" loading={descriptions.isFetching} onClick={() => void descriptions.refetch()}>重试</Button>} />}
      <Table rowKey="name" size="small" pagination={false}
        locale={{ emptyText: searchText ? "没有匹配字段" : "暂无推荐字段，可展开其他字段按需选择" }} dataSource={visibleFields} columns={[
        { title: "使用", width: 55, render: (_, f) => <Checkbox aria-label={`使用 ${f.physicalName}`} disabled={busy} checked={chosen(f.name)} onChange={e => change({ fields: { ...design.fields, [f.name]: e.target.checked ? f.type === "Navigation" ? "relationship" : "property" : "excluded" } })} /> },
        { title: "字段与关系依据", width: "38%", render: (_, f) => <Space orientation="vertical" size={4} style={{ overflowWrap: "anywhere" }}><span>{f.physicalName}</span>{f.type === "Navigation" && f.target && <><Typography.Text type="secondary">{detail.tableName}.{f.physicalName} → {f.target}{f.targetField ? `.${f.targetField}` : "（目标字段待核实）"}</Typography.Text><Tag color={chosen(f.name) ? "blue" : "default"}>{chosen(f.name) ? "已选入草稿" : "待确认关系"}</Tag><Typography.Text type="secondary">依据：CSV 物理结构；实例数据尚未在此验证</Typography.Text></>}<Typography.Text type="secondary" style={{ fontSize: 12 }}>{detail.recommendations?.[f.name]?.reason || "按业务需要选择"}</Typography.Text></Space> },
        { title: "Designer 描述（中文优先）", render: (_, f) => {
          const description = descriptions.data?.fields[f.physicalName.toLowerCase()];
          return <div style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
            {description?.descriptionZh?.trim() || description?.descriptionEn || <Typography.Text type="secondary">{descriptions.isPending ? "正在读取并补全中文说明…" : descriptions.isError || descriptions.data?.warning ? "说明暂不可用" : "Designer 暂无字段说明"}</Typography.Text>}
            {description?.descriptionZh && description.descriptionEn && <details className="field-source-description"><summary>英文原文</summary>{description.descriptionEn}</details>}
          </div>;
        } },
      ]} />
      <Button type="primary" disabled={busy} loading={check.isPending} onClick={() => check.mutate()}>检查这个对象</Button>
      {preview && <Card size="small" title="检查结果"><Space orientation="vertical" style={{ width: "100%" }}>
        <Alert showIcon type={preview.blockers.length ? "warning" : "success"} message={preview.blockers.length ? "这些内容需要处理" : `${preview.counts.properties} 个字段、${preview.counts.relationships} 条关联，可以加入发布模型`} description={preview.blockers.join("；") || "确认后，系统会完成模型审阅和准备。"} />
        <RelationshipChangeReview items={preview.relationshipChanges || []} />
        {preview.removedFields.length > 0 && <Alert type="warning" message={`将从待发布模型移除 ${preview.removedFields.length} 个字段`} description={preview.removedFields.join("、")} />}
        <Collapse items={[{ key: "fields", label: "查看本次字段与关联", children: preview.fields.map(f => {
          const field = detail.fields.find(item => item.name === f.name);
          return <Tag key={f.name}>{field?.physicalName || f.name}{f.type === "Navigation" && field?.target ? ` → ${field.target}` : ""}</Tag>;
        }) }]} />
        <Button type="primary" disabled={busy || !!preview.blockers.length} loading={apply.isPending} onClick={() => apply.mutate()}>{inline ? "确认加入待发布模型" : "确认并进入检查发布"}</Button>
      </Space></Card>}
    </>}
    <Collapse items={[{ key: "details", label: "技术信息", children: <Typography.Paragraph>结构版本：{detail.snapshotId}<br />身份字段：{detail.fields.filter(f => f.primaryKey).map(f => f.physicalName).join("、") || "待核实"}</Typography.Paragraph> }]} />
  </Space>;
}
