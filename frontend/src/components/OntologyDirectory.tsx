import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, App, Button, Card, Collapse, Descriptions, Drawer, Input, Modal, Select, Space, Table, Tabs, Tag, Typography } from "antd";
import { useState } from "react";
import { authorityApi, type AuthorityRow, type Decision, type Detail, type ImportAnalysis, type Plan } from "../authorityApi";
import { manufacturingApi } from "../api";

const stateLabel: Record<string, string> = { review: "待确认", approved: "已确认，待同步", synced: "已同步建模库", changed: "来源变化，待复核" };
const sourceLabel = (id: string) => id === "approved" ? "当前权威版本" : id.startsWith("candidate:") ? `导入候选 ${id.slice(10, 18)}` : id;
const coreGroups = ["组织与位置", "产品与计量", "人员与职责", "设备与资源"];

export function OntologyDirectory({ importOpen, closeImport }: { importOpen: boolean; closeImport: () => void }) {
  const { message } = App.useApp();
  const client = useQueryClient();
  const list = useQuery({ queryKey: ["ontology-directory"], queryFn: authorityApi.directory });
  const coverage = useQuery({ queryKey: ["published-coverage"], queryFn: () => manufacturingApi.coverage(), retry: false, staleTime: 30_000 });
  const [scope, setScope] = useState("core");
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState<string>();
  const [selected, setSelected] = useState<AuthorityRow>();
  const rows = (list.data?.items || []).filter(r => (!search || `${r.className} ${r.chineseName}`.toLowerCase().includes(search.toLowerCase())) && (!group || group === r.group) && (scope === "all" || scope === "core" && coreGroups.includes(r.group) || scope === "pending" && (r.status === "review" || r.status === "changed" || r.pendingCandidateCount > 0)));
  const published = new Map(coverage.data?.classes.map(c => [c.uri.split("#").pop(), c.count]));
  const reload = async () => { await Promise.all(["ontology-directory", "authority-detail", "semantic-graph-overview", "semantic-graph-stats", "semantic-class-detail"].map(key => client.invalidateQueries({ queryKey: [key] }))); };
  return <Card title="本体目录与差异审阅">
    <Space orientation="vertical" size={16} style={{ width: "100%" }}>
      <Alert type="info" showIcon title="从 CSV 建立制造模型" description="点击页面顶部“导入 CSV”，上传表定义与字段定义。选择对象后审阅候选，确认并同步到建模库，即可在“制造语义主图”查看；再到“模型工作区”选择 Graph Studio 发布范围。" />
      {list.isError && <Alert type="error" title="目录读取失败" description={(list.error as Error).message} />}
      <Space wrap><Tag>{list.data?.summary.classes ?? "—"} 个类</Tag><Tag color="orange">{list.data?.summary.duplicates ?? "—"} 个类有多份来源</Tag><Tag color="red">{list.data?.summary.conflicts ?? "—"} 个类存在来源类型差异</Tag><Tag color="green">{list.data?.summary.approved ?? "—"} 个已确认</Tag></Space>
      <Space wrap><Select value={scope} onChange={setScope} style={{ width: 180 }} options={[{ value: "core", label: "公共核心优先" }, { value: "pending", label: "待确认与导入候选" }, { value: "all", label: "全部本体" }]} /><Select allowClear placeholder="业务领域" value={group} onChange={setGroup} style={{ width: 240 }} options={list.data?.groups.map(g => ({ value: g, label: g }))} /><Input.Search allowClear placeholder="搜索中文名或类名" value={search} onChange={e => setSearch(e.target.value)} style={{ width: 260 }} /></Space>
      {coverage.isError && <Typography.Text type="secondary">当前发布状态未核实，本体目录仍可使用。</Typography.Text>}
      <Table<AuthorityRow> rowKey="className" loading={list.isLoading} dataSource={rows} pagination={{ pageSize: 16, showTotal: total => `共 ${total} 个对象` }} scroll={{ x: 1000 }} columns={[
        { title: "对象", key: "name", render: (_, r) => <Button type="link" onClick={() => setSelected(r)}>{r.chineseName}<Typography.Text type="secondary"> · {r.className}</Typography.Text></Button> },
        { title: "领域", dataIndex: "group" }, { title: "来源 / 属性", render: (_, r) => `${r.sourceCount} / ${r.propertyCount}` },
        { title: "治理状态", render: (_, r) => <Space wrap><Tag color={r.status === "synced" ? "green" : "gold"}>{stateLabel[r.status]}{r.revision > 0 ? ` R${r.revision}` : ""}</Tag>{r.pendingCandidateCount > 0 && <Tag color="blue">{r.pendingCandidateCount} 份候选</Tag>}</Space> },
        { title: "当前问数版本", render: (_, r) => !coverage.data ? "未核实" : !published.has(r.className) ? "未在当前问数层发现" : published.get(r.className) == null ? "已发布，数量未核实" : `已发布 · ${published.get(r.className)} 条` },
        { title: "操作", render: (_, r) => <Button onClick={() => setSelected(r)}>查看模型卡</Button> },
      ]} />
      <Typography.Text type="secondary">目录中的权威版本与 Graph Studio 发布版本分别管理。显示“已确认”不代表已发布；历史来源差异保留用于追溯。</Typography.Text>
    </Space>
    <Drawer title={selected ? `${selected.chineseName} · ${selected.className}` : "模型卡"} open={!!selected} onClose={() => setSelected(undefined)} size="large" destroyOnHidden>
      {selected && <ModelCard key={selected.className} row={selected} reload={reload} />}
    </Drawer>
    <ImportDialog open={importOpen} close={closeImport} done={async () => { closeImport(); setScope("pending"); await reload(); message.success("候选已保存，请打开模型卡审阅差异"); }} />
  </Card>;
}

function ModelCard({ row, reload }: { row: AuthorityRow; reload: () => Promise<void> }) {
  const query = useQuery({ queryKey: ["authority-detail", row.className], queryFn: () => authorityApi.detail(row.className) });
  if (query.isError) return <Alert type="error" title="模型卡读取失败" description={(query.error as Error).message} />;
  if (!query.data) return <Card loading />;
  return <ReviewForm key={query.data.fingerprint} row={row} detail={query.data} reload={reload} />;
}

function ReviewForm({ row, detail, reload }: { row: AuthorityRow; detail: Detail; reload: () => Promise<void> }) {
  const { message } = App.useApp();
  const initial = detail.authority ? "approved" : detail.sources.find(s => !s.id.startsWith("candidate:") && s.id !== "csv_business_import_ontology.json" && s.definition.chineseName)?.id || detail.sources[0].id;
  const [preferredSource, setSource] = useState(initial);
  const initialClass = detail.sources.find(s => s.id === initial)!.definition;
  const [chineseName, setChineseName] = useState(initialClass.chineseName || "");
  const [description, setDescription] = useState(initialClass.description || "");
  const [domain, setDomain] = useState(detail.authority?.domain || row.group);
  const [choices, setChoices] = useState<Record<string, string>>({});
  const [plan, setPlan] = useState<Plan>();
  const definition = detail.sources.find(s => s.id === preferredSource)!.definition;
  const body = (): Decision => ({ preferredSource, domain, choices, fingerprint: detail.fingerprint, chineseName, description });
  const error = (e: Error) => message.error(e.message);
  const preview = useMutation({ mutationFn: () => authorityApi.preview(row.className, body()), onSuccess: setPlan, onError: error });
  const approve = useMutation({ mutationFn: () => authorityApi.approve(row.className, { ...body(), planHash: plan?.planHash }), onSuccess: async () => { message.success("权威版本已保存，请同步建模库后再发布"); await reload(); }, onError: error });
  const sync = useMutation({ mutationFn: () => authorityApi.sync(row.className, detail.revision), onSuccess: async () => { message.success("已同步建模库，当前 Graph Studio 发布版本保持不变"); await reload(); }, onError: error });
  const busy = preview.isPending || approve.isPending || sync.isPending;
  return <Space orientation="vertical" size={16} style={{ width: "100%" }}>
    <Descriptions size="small" column={1} items={[{ key: "definition", label: "业务定义", children: definition.description || "来源未填写业务定义" }, { key: "key", label: "物理主键候选", children: detail.primaryKeys.join("、") || "未找到，需核实" }, { key: "revision", label: "权威版本", children: detail.revision ? `R${detail.revision}` : "尚未确认" }]} />
    <Typography.Text strong>1. 选择权威来源与领域</Typography.Text>
    <Select disabled={busy} value={preferredSource} onChange={v => { const next = detail.sources.find(s => s.id === v)!.definition; setSource(v); setChineseName(next.chineseName || chineseName); setDescription(next.description || description); setPlan(undefined); }} style={{ width: "100%" }} options={detail.sources.map(s => ({ value: s.id, label: `${sourceLabel(s.id)}（${s.definition.properties.length} 个属性）` }))} />
    <Input disabled={busy} addonBefore="所属领域" value={domain} maxLength={80} onChange={e => { setDomain(e.target.value); setPlan(undefined); }} />
    <Input disabled={busy} addonBefore="业务中文名" value={chineseName} maxLength={200} onChange={e => { setChineseName(e.target.value); setPlan(undefined); }} />
    <Input.TextArea disabled={busy} aria-label="业务定义" placeholder="用业务语言说明这个对象是什么" value={description} maxLength={16000} autoSize={{ minRows: 3, maxRows: 8 }} onChange={e => { setDescription(e.target.value); setPlan(undefined); }} />
    <Typography.Text type="secondary">所选来源优先提供中文名、描述和关系元数据；其余来源独有的属性与关系保留。类型冲突需要逐项选择。</Typography.Text>
    <Typography.Text strong>2. 处理类型冲突</Typography.Text>
    {detail.conflicts.length === 0 ? <Tag color="green">未发现类型冲突</Tag> : detail.conflicts.map(c => <Card size="small" key={c.property} title={c.property}>
      <Space orientation="vertical" style={{ width: "100%" }}><Typography.Text>物理依据：{c.physicalField || "未匹配字段"}；期望类型：{c.expectedType || "需人工判断"}</Typography.Text>
        <Select disabled={busy} placeholder="明确选择本次采用的定义" value={choices[c.property]} style={{ width: "100%" }} onChange={v => { setChoices({ ...choices, [c.property]: v }); setPlan(undefined); }} options={Object.entries(c.variants).map(([id, p]) => ({ value: id, label: `${p.type} — ${sourceLabel(id)}` }))} />
      </Space></Card>)}
    <Button type="primary" disabled={busy || detail.conflicts.some(c => !choices[c.property])} loading={preview.isPending} onClick={() => preview.mutate()}>3. 预览合并结果</Button>
    {plan && <>
      <Alert type={plan.blockers.length ? "error" : "info"} title={`合并后 ${plan.model.class.properties.length} 个属性、${plan.model.relationships.length} 条关系；${plan.changes.length} 项属性差异`} description={plan.blockers.join("；") || plan.note} />
      {plan.extensionProperties.length > 0 && <Alert type="warning" title={`${plan.extensionProperties.length} 个属性未匹配物理字段，请确认其业务扩展含义`} description={plan.extensionProperties.join("、")} />}
      <Tabs items={[
        { key: "changes", label: "属性差异", children: <Table rowKey="property" size="small" dataSource={plan.changes} pagination={{ pageSize: 8 }} columns={[{ title: "属性", dataIndex: "property" }, { title: "原定义", render: (_, r) => r.before ? `${r.before.type} · ${r.before.description || "无说明"}` : "新增" }, { title: "合并后", render: (_, r) => `${r.after.type} · ${r.after.description || "无说明"}` }]} /> },
        { key: "properties", label: "完整属性", children: <Table rowKey="name" size="small" dataSource={plan.model.class.properties} pagination={{ pageSize: 10 }} columns={[{ title: "属性", dataIndex: "name" }, { title: "类型", dataIndex: "type" }, { title: "说明", dataIndex: "description" }]} /> },
        { key: "relations", label: "合并后关联", children: <Table rowKey={r => `${r.fromClass}:${r.relationName}:${r.toClass}`} size="small" dataSource={plan.model.relationships} pagination={{ pageSize: 8 }} columns={[{ title: "关系", dataIndex: "relationName" }, { title: "终点", dataIndex: "toClass" }, { title: "基数", dataIndex: "cardinality" }, { title: "说明", dataIndex: "description" }]} /> },
      ]} />
      <Button type="primary" disabled={busy || plan.blockers.length > 0} loading={approve.isPending} onClick={() => approve.mutate()}>确认此合并，保存权威版本</Button>
    </>}
    {detail.revision > 0 && <Button disabled={busy} loading={sync.isPending} onClick={() => sync.mutate()}>同步权威 R{detail.revision} 到建模库</Button>}
    <Collapse items={[{ key: "history", label: `历史版本（${detail.history.length}）`, children: detail.history.map(h => <p key={h.revision}>R{h.revision} · {new Date(h.created_at).toLocaleString()} · {h.snapshot.domain} · {h.snapshot.model.class.properties.length} 个属性 / {h.snapshot.model.relationships.length} 条关系</p>) }]} />
  </Space>;
}

function ImportDialog({ open, close, done }: { open: boolean; close: () => void; done: () => Promise<void> }) {
  const { message } = App.useApp();
  const [tables, setTables] = useState<File>();
  const [fields, setFields] = useState<File>();
  const [analysis, setAnalysis] = useState<ImportAnalysis>();
  const [selected, setSelected] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const analyze = useMutation({ mutationFn: () => { const form = new FormData(); form.append("tables", tables!); form.append("fields", fields!); form.append("database", "sqlserver"); return authorityApi.analyze(form); }, onSuccess: d => { setAnalysis(d); setSelected(d.candidates.filter(c => c.selected).map(c => c.className)); }, onError: (e: Error) => message.error(e.message) });
  const stage = useMutation({ mutationFn: () => authorityApi.stage(analysis!.importId, selected), onSuccess: async () => { setAnalysis(undefined); await done(); }, onError: (e: Error) => message.error(e.message) });
  const busy = analyze.isPending || stage.isPending;
  return <Modal title="导入 CSV · 表与字段定义" open={open} onCancel={close} closable={!busy} maskClosable={!busy} keyboard={!busy} width={900} footer={null}>
    <Space orientation="vertical" style={{ width: "100%" }}>
      <Alert type="info" showIcon title="上传 Camstar 数据库结构，不是业务数据记录" description="项目标准文件位于 docs/Database_Tables.csv 和 docs/Database_Fields.csv。导入生成待审阅候选，确认并同步后才更新制造语义主图。" />
      <label>表定义（Database_Tables.csv） <input aria-label="表定义 CSV" type="file" accept=".csv" disabled={busy} onChange={e => { setTables(e.target.files?.[0]); setAnalysis(undefined); }} /></label>
      <label>字段与外键（Database_Fields.csv） <input aria-label="字段与外键 CSV" type="file" accept=".csv" disabled={busy} onChange={e => { setFields(e.target.files?.[0]); setAnalysis(undefined); }} /></label>
      <Button disabled={!tables || !fields || stage.isPending} loading={analyze.isPending} onClick={() => analyze.mutate()}>分析业务对象</Button>
      {analysis && <><Input.Search placeholder="搜索对象" value={search} onChange={e => setSearch(e.target.value)} /><Table rowKey="className" size="small" dataSource={analysis.candidates.filter(c => c.className.toLowerCase().includes(search.toLowerCase()))} rowSelection={{ selectedRowKeys: selected, preserveSelectedRowKeys: true, onChange: keys => setSelected(keys as string[]) }} pagination={{ pageSize: 8 }} columns={[{ title: "对象", dataIndex: "className" }, { title: "建议", dataIndex: "reason" }]} /><Button type="primary" disabled={!selected.length || analyze.isPending} loading={stage.isPending} onClick={() => stage.mutate()}>提交 {selected.length} 个对象为候选</Button></>}
    </Space>
  </Modal>;
}
