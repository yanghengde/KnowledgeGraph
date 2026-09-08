import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, App, Button, Card, Collapse, Empty, Input, Segmented, Select, Space, Spin, Table, Tabs, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { authorityApi, type ImportAnalysis } from "../authorityApi";
import { mappingApi } from "../mappingApi";
import { syncApi } from "../api";
import { PhysicalRelationDiagram } from "../components/ontology/PhysicalRelationDiagram";

export function ObjectExplorerPage() {
  const { message } = App.useApp();
  const client = useQueryClient();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<ImportAnalysis>();
  const [database, setDatabase] = useState("sqlserver");
  const [active, setActive] = useState<string>();
  const [selected, setSelected] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [scope, setScope] = useState("all");
  const [view, setView] = useState("graph");
  const [advanced, setAdvanced] = useState(false);
  const [snapshot, setSnapshot] = useState<string>();
  const [tables, setTables] = useState<File>();
  const [fields, setFields] = useState<File>();
  const opening = useQuery({ queryKey: ["physical-open"], queryFn: mappingApi.openPhysical, enabled: !analysis, refetchOnWindowFocus: false, retry: false, staleTime: 0 });
  const drafts = useQuery({ queryKey: ["mapping-drafts"], queryFn: mappingApi.list });
  const governance = useQuery({ queryKey: ["ontology-governance", "opcenter2607-core"], queryFn: () => syncApi.ontologyGovernance("opcenter2607-core"), retry: false });
  const versions = useQuery({ queryKey: ["physical-versions"], queryFn: mappingApi.physicalVersions, enabled: advanced });
  const accept = (value: ImportAnalysis) => { setAnalysis(value); setSelected([]); setActive(value.candidates.find(c => c.className === "Product")?.className || value.candidates[0]?.className); };
  useEffect(() => { if (opening.data && !analysis) { accept(opening.data); setDatabase(opening.data.database); } }, [opening.data, analysis]);
  const descriptions = useQuery({ queryKey: ["import-translations", analysis?.importId], queryFn: () => authorityApi.importTranslations(analysis!.importId), enabled: !!analysis,
    refetchInterval: query => ["waiting", "pending", "running"].includes(query.state.data?.translation.status || "") ? 2500 : false });
  const detail = useQuery({ queryKey: ["import-object", analysis?.importId, active], queryFn: () => authorityApi.importObject(analysis!.importId, active!), enabled: !!analysis && !!active });
  const error = (e: Error) => message.error(e.message);
  const refresh = useMutation({ mutationFn: async () => {
    const result = await authorityApi.standard(database); await mappingApi.addSources(result.importId, []); return result;
  }, onSuccess: value => { accept(value); void versions.refetch(); }, onError: error });
  const restore = useMutation({ mutationFn: () => mappingApi.restorePhysical(snapshot!, database), onSuccess: accept, onError: error });
  const upload = useMutation({ mutationFn: async () => {
    const form = new FormData(); form.append("tables", tables!); form.append("fields", fields!); form.append("database", database);
    const result = await authorityApi.analyze(form); await mappingApi.addSources(result.importId, []); return result;
  }, onSuccess: accept, onError: error });
  const translate = useMutation({ mutationFn: () => authorityApi.retryTranslations(analysis!.importId), onSuccess: () => void descriptions.refetch(), onError: error });
  const add = useMutation({ mutationFn: (names: string[]) => mappingApi.addSources(analysis!.importId, names), onSuccess: async () => {
    setSelected([]); await client.invalidateQueries({ queryKey: ["mapping-drafts"] }); navigate("/ontology-model?view=mapping");
  }, onError: error });
  const busy = refresh.isPending || restore.isPending || upload.isPending || add.isPending;
  const candidates = (analysis?.candidates || []).map(c => ({ ...c, descriptionZh: descriptions.data?.translations[c.className] || c.descriptionZh, descriptionEn: descriptions.data?.descriptions[c.className] || c.descriptionEn }));
  const used = new Set([...(drafts.data?.items || []).map(d => d.tableName), ...(governance.data?.graph.nodes || []).map(n => n.data.sourceClass).filter((n): n is string => !!n)]);
  const usageKnown = !!drafts.data && !!governance.data;
  const filtered = candidates.filter(c => (scope === "all" || (scope === "used" ? used.has(c.className) : !used.has(c.className))) && `${c.className} ${c.descriptionZh} ${c.descriptionEn}`.toLowerCase().includes(search.toLowerCase()));
  const current = candidates.find(c => c.className === active);
  const edges = analysis?.edges || [];
  const usage = (name: string) => used.has(name) ? <Tag color="blue">已用于建模</Tag> : <Tag>{usageKnown ? "未使用" : "状态待核实"}</Tag>;
  return <div className="page-stack object-explorer-page">
    <section className="section-intro operations-heading"><div><Typography.Title level={2}>Opcenter 数据模型</Typography.Title><Typography.Paragraph>找到需要的表，点击“用于建模”。结构会自动保存，下次可以继续使用。</Typography.Paragraph></div><Button onClick={() => navigate("/ontology-model")}>我的业务模型</Button></section>
    <Collapse onChange={keys => setAdvanced(keys.length > 0)} items={[{ key: "settings", label: "数据来源与更新", children: <Space orientation="vertical" style={{ width: "100%" }}>
      <Typography.Text type="secondary">平时直接使用已保存的结构和说明。需要更新时，再连接来源数据库。</Typography.Text>
      <Space wrap><Select value={database} disabled={busy} onChange={setDatabase} options={[{ value: "sqlserver", label: "Opcenter SQL Server" }, { value: "oracle", label: "Opcenter Oracle" }]} /><Button loading={refresh.isPending} disabled={busy} onClick={() => refresh.mutate()}>更新项目表结构</Button><Button disabled={!analysis || busy} loading={translate.isPending} onClick={() => translate.mutate()}>刷新说明</Button><Button onClick={() => navigate("/connections")}>连接设置</Button></Space>
      {versions.isError && <Alert type="error" message={(versions.error as Error).message} />}
      <Space wrap><Select placeholder="查看其他结构版本" value={snapshot} onChange={setSnapshot} style={{ width: 340 }} options={versions.data?.items.map(v => ({ value: v.snapshotId, label: `${new Date(v.createdAt).toLocaleString()} · ${v.tableCount} 张表` }))} /><Button disabled={!snapshot || busy} loading={restore.isPending} onClick={() => restore.mutate()}>打开</Button></Space>
      <Collapse items={[{ key: "upload", label: "导入其他表结构文件", children: <Space wrap><label>表定义 <input type="file" accept=".csv" onChange={e => setTables(e.target.files?.[0])} /></label><label>字段定义 <input type="file" accept=".csv" onChange={e => setFields(e.target.files?.[0])} /></label><Button disabled={!tables || !fields || busy} loading={upload.isPending} onClick={() => upload.mutate()}>导入并保存</Button></Space> }]} />
    </Space> }]} />
    {!analysis ? opening.isError ? <Alert type="error" message={(opening.error as Error).message} action={<Button onClick={() => void opening.refetch()}>重新打开</Button>} /> : <Card><Spin /> 正在打开数据模型…</Card> : <>
      <Card size="small"><Space wrap><Typography.Text strong>共 {candidates.length} 张表</Typography.Text><Tag color="blue">{candidates.filter(c => used.has(c.className)).length} 张已用于建模</Tag><Typography.Text type="secondary">{usageKnown ? `${candidates.filter(c => !used.has(c.className)).length} 张未使用` : "使用状态尚未完全核实"}</Typography.Text><Tag>{edges.length} 条物理关联</Tag></Space></Card>
      {(drafts.isError || governance.isError) && <Alert type="warning" message="部分建模状态暂时无法读取，未标记的表不代表尚未使用" action={<Button onClick={() => { void drafts.refetch(); void governance.refetch(); }}>重试</Button>} />}
      <div className="import-explorer-grid">
        <Card size="small" title="查找数据表" className="import-object-directory">
          <Space orientation="vertical" style={{ width: "100%" }}><Input.Search allowClear placeholder="搜索表名或说明" value={search} onChange={e => setSearch(e.target.value)} /><Segmented value={scope} onChange={setScope} options={[{ label: "全部", value: "all" }, { label: "已使用", value: "used" }, { label: "未使用", value: "unused", disabled: !usageKnown }]} /></Space>
          <Table rowKey="className" size="small" dataSource={filtered} pagination={{ pageSize: 12, showSizeChanger: false }} rowSelection={{ selectedRowKeys: selected, preserveSelectedRowKeys: true, onChange: keys => setSelected(keys as string[]), getCheckboxProps: () => ({ disabled: busy }) }} columns={[{ title: "数据表", render: (_, c) => <><Button type="link" onClick={() => setActive(c.className)}>{c.className}</Button>{usage(c.className)}<Typography.Paragraph ellipsis={{ rows: 2, tooltip: true }}>{c.descriptionZh || c.descriptionEn || "暂无说明"}</Typography.Paragraph></> }]} />
          <Button type="primary" block disabled={!selected.length || busy} loading={add.isPending} onClick={() => add.mutate(selected)}>将所选 {selected.length} 张表用于建模</Button>
        </Card>
        <Card size="small" title={current ? <Space wrap>{current.className}{usage(current.className)}</Space> : "表之间的关联"} className="import-object-detail" extra={<Button type="primary" disabled={!active || busy} loading={add.isPending} onClick={() => add.mutate([active!])}>{active && used.has(active) ? "继续建模" : "用于建模"}</Button>}>
          {!current ? <Empty description="选择左侧表，查看它和哪些表有关联" /> : <>
            <Typography.Paragraph>{current.descriptionZh || current.descriptionEn || "暂无业务说明"}</Typography.Paragraph>
            <Tabs activeKey={view} onChange={setView} items={[
              { key: "graph", label: "关联图", children: <PhysicalRelationDiagram active={current.className} edges={edges} candidates={candidates} used={used} usageKnown={usageKnown} onSelect={setActive} /> },
              { key: "relations", label: "关联列表", children: <Table size="small" pagination={false} rowKey={e => `${e.source}:${e.fieldId}:${e.target}`} dataSource={edges.filter(e => e.source === active || e.target === active)} columns={[{ title: "来源表", render: (_, e) => <Button type="link" onClick={() => setActive(e.source)}>{e.source}</Button> }, { title: "字段", dataIndex: "fieldName" }, { title: "关联表", render: (_, e) => <Button type="link" disabled={!e.available} onClick={() => setActive(e.target)}>{e.target}</Button> }]} /> },
              { key: "fields", label: `字段 (${current.propertyCount})`, children: detail.isError ? <Alert type="error" message={(detail.error as Error).message} action={<Button onClick={() => { setAnalysis(undefined); void opening.refetch(); }}>重新打开模型</Button>} /> : <Table size="small" loading={detail.isLoading} rowKey="physicalName" dataSource={detail.data?.fields || []} columns={[{ title: "字段", render: (_, f) => <>{f.physicalName}{f.primaryKey && <Tag>身份字段</Tag>}</> }, { title: "说明", render: (_, f) => f.descriptionZh || f.descriptionEn || (f.target ? `关联 ${f.target}` : "—") }]} /> },
            ]} />
          </>}
        </Card>
      </div>
    </>}
  </div>;
}
