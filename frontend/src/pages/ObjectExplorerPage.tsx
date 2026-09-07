import { useNavigate } from "react-router-dom";
import { ArrowLeftOutlined, ArrowRightOutlined, PlusOutlined, SearchOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, App, Button, Card, Collapse, Empty, Input, Progress, Select, Space, Table, Tabs, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { authorityApi, type ImportAnalysis, type ImportCandidate, type PhysicalEdge } from "../authorityApi";
import { mappingApi } from "../mappingApi";

const DRAFT_KEY = "camstar-object-explorer-draft";
type Draft = { analysis: ImportAnalysis; database: string; selected: string[]; trail: string[]; search: string; expiresAt: number };
function readDraft(): Draft | undefined {
  try {
    const draft = JSON.parse(sessionStorage.getItem(DRAFT_KEY) || "null") as Draft | null;
    if (draft && draft.expiresAt > Date.now() && Array.isArray(draft.analysis?.candidates)
        && Array.isArray(draft.selected) && Array.isArray(draft.trail)) return draft;
  } catch { /* Storage is optional; the explorer remains usable. */ }
}

export function ObjectExplorerPage() {
  const { message } = App.useApp();
  const client = useQueryClient();
  const navigate = useNavigate();
  const [draft] = useState(readDraft);
  const [expiresAt, setExpiresAt] = useState(draft?.expiresAt || 0);
  const [tables, setTables] = useState<File>();
  const [fields, setFields] = useState<File>();
  const [database, setDatabase] = useState(draft?.database || "sqlserver");
  const [analysis, setAnalysis] = useState<ImportAnalysis | undefined>(draft?.analysis);
  const [selected, setSelected] = useState<string[]>(draft?.selected || []);
  const [search, setSearch] = useState(draft?.search || "");
  const [trail, setTrail] = useState<string[]>(draft?.trail || []);
  const [onlySelected, setOnlySelected] = useState(false);
  const [snapshot, setSnapshot] = useState<string>();
  const [versionsOpen, setVersionsOpen] = useState(false);
  const versions = useQuery({ queryKey: ["physical-versions"], queryFn: mappingApi.physicalVersions, enabled: versionsOpen });
  const active = trail.at(-1);
  useEffect(() => {
    try {
      if (analysis) sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ analysis, database, selected, trail, search, expiresAt }));
      else sessionStorage.removeItem(DRAFT_KEY);
    } catch { /* Browser storage may be full or unavailable. */ }
  }, [analysis, database, selected, trail, search, expiresAt]);
  const accept = (data: ImportAnalysis) => {
    setExpiresAt(Date.now() + 55 * 60 * 1000); setAnalysis(data); setSelected([]); setTrail([]); setSearch(""); setOnlySelected(false);
  };
  const analyze = useMutation({ mutationFn: (standard: boolean) => {
    if (standard) return authorityApi.standard(database);
    const form = new FormData(); form.append("tables", tables!); form.append("fields", fields!); form.append("database", database);
    return authorityApi.analyze(form);
  }, onSuccess: accept, onError: (e: Error) => message.error(e.message) });
  const restore = useMutation({ mutationFn: () => mappingApi.restorePhysical(snapshot!, database), onSuccess: accept, onError: (e: Error) => message.error(e.message) });
  const persist = useMutation({ mutationFn: () => mappingApi.addSources(analysis!.importId, []), onSuccess: async () => {
    message.success("完整物理模型已保存到 PostgreSQL"); await client.invalidateQueries({ queryKey: ["physical-versions"] });
  }, onError: (e: Error) => message.error(e.message) });
  const descriptions = useQuery({
    queryKey: ["import-translations", analysis?.importId],
    queryFn: () => authorityApi.importTranslations(analysis!.importId), enabled: !!analysis,
    refetchInterval: query => {
      if (query.state.status === "error") return false;
      const state = query.state.data?.translation;
      return !state || ["waiting", "pending", "running"].includes(state.status) ? 2000 : false;
    },
  });
  const detail = useQuery({ queryKey: ["import-object", analysis?.importId, active, descriptions.data?.translation.status],
    queryFn: () => authorityApi.importObject(analysis!.importId, active!), enabled: !!analysis && !!active });
  const retry = useMutation({ mutationFn: () => authorityApi.retryTranslations(analysis!.importId),
    onSuccess: () => descriptions.refetch(), onError: (e: Error) => message.error(e.message) });
  const enrich = useMutation({ mutationFn: (name: string) => authorityApi.enrichObject(analysis!.importId, name),
    onSuccess: data => { if (data.warning) message.warning(data.warning); else message.success("中英文说明已保存"); void detail.refetch(); },
    onError: (e: Error) => message.error(e.message) });
  const stage = useMutation({ mutationFn: () => mappingApi.addSources(analysis!.importId, selected),
    onSuccess: async () => {
      setSelected([]);
      await client.invalidateQueries({ queryKey: ["mapping-drafts"] });
      await client.invalidateQueries({ queryKey: ["physical-versions"] });
      message.success("来源草稿与完整物理快照已保存，请前往来源与转换定义用途");
    }, onError: (e: Error) => message.error(e.message) });
  const busy = analyze.isPending || stage.isPending || enrich.isPending || restore.isPending || persist.isPending;
  const candidates = (analysis?.candidates || []).map(c => ({ ...c,
    descriptionEn: descriptions.data?.descriptions[c.className] || c.descriptionEn,
    descriptionZh: descriptions.data?.translations[c.className] || c.descriptionZh,
  }));
  const byName = new Map(candidates.map(c => [c.className, c]));
  const current = active ? byName.get(active) : undefined;
  const state = descriptions.data?.translation || analysis?.translation;
  const visit = (name: string) => { if (name !== active) setTrail(path => [...path, name]); };
  const toggle = (name: string) => setSelected(values => values.includes(name) ? values.filter(v => v !== name) : [...values, name]);
  const related = (edges: PhysicalEdge[], incoming: boolean) => <Table<PhysicalEdge> size="small"
    rowKey={r => `${r.source}:${r.fieldId}:${r.fieldName}:${r.target}`} dataSource={edges} pagination={{ pageSize: 6, showSizeChanger: false }}
    columns={[
      { title: incoming ? "引用此对象的表" : "关联对象", render: (_, edge) => {
        const name = incoming ? edge.source : edge.target;
        return <><Button type="link" disabled={!byName.has(name)} onClick={() => visit(name)}>{name}<ArrowRightOutlined /></Button>
          <div className="import-related-description">{byName.get(name)?.descriptionZh || byName.get(name)?.descriptionEn || (byName.has(name) ? "系统未提供说明" : "不在本次 CSV 中")}</div></>;
      } },
      { title: "物理外键", render: (_, edge) => <span>{edge.source}.{edge.fieldName}<br /><Typography.Text type="secondary">→ {edge.target}.{edge.targetField || "主键"}</Typography.Text></span> },
      { title: "建模来源", width: 95, render: (_, edge) => { const name = incoming ? edge.source : edge.target; return <Button size="small" disabled={busy || !byName.has(name)} onClick={() => toggle(name)}>{selected.includes(name) ? "移除" : "加入"}</Button>; } },
    ]} locale={{ emptyText: "CSV 中没有该方向的外键关系" }} />;
  return <div className="page-stack object-explorer-page">
    <section className="section-intro operations-heading">
      <div><Typography.Title level={2}>Camstar 数据模型</Typography.Title>
        <Typography.Paragraph>完整保留表、字段与物理外键 → 探索来源关联 → 加入语义建模草稿。表与本体类分别建模。</Typography.Paragraph></div>
      <Button onClick={() => navigate("/ontology-model?view=mapping")}>前往来源与转换<ArrowRightOutlined /></Button>
    </section>
    <div className="import-explorer">
      <div className="import-source-bar">
        <Space wrap><Select aria-label="系统说明来源" value={database} disabled={busy} onChange={value => { setDatabase(value); setAnalysis(undefined); setTrail([]); }}
          options={[{ value: "sqlserver", label: "Camstar SQL Server" }, { value: "oracle", label: "Camstar Oracle" }]} style={{ width: 210 }} />
          <Button type={analysis ? "default" : "primary"} loading={analyze.isPending} disabled={busy} onClick={() => analyze.mutate(true)}>读取项目标准表结构</Button>
          <Button disabled={busy || !analysis} loading={persist.isPending} onClick={() => persist.mutate()}>保存物理模型</Button>
          <Typography.Text type="secondary">从一张表开始沿外键探索；来源用途和业务字段在语义模型中定义。</Typography.Text></Space>
        <Collapse ghost onChange={keys => setVersionsOpen(keys.includes("versions"))} items={[{ key: "versions", label: "打开已保存的物理模型", children: <Space wrap>
          {versions.isError && <Alert type="error" message={(versions.error as Error).message} action={<Button onClick={() => void versions.refetch()}>重试</Button>} />}
          <Select aria-label="物理模型版本" placeholder="选择已保存的结构版本" loading={versions.isFetching} value={snapshot} onChange={setSnapshot} style={{ width: 360 }} options={versions.data?.items.map(v => ({ value: v.snapshotId, label: `${new Date(v.createdAt).toLocaleString()} · ${v.tableCount} 张表 · ${v.snapshotId.slice(0, 8)}` }))} />
          <Button disabled={busy || !snapshot} loading={restore.isPending} onClick={() => restore.mutate()}>打开模型</Button>
        </Space> }, { key: "upload", label: "使用其他 CSV 文件", children: <Space wrap>
          <label>表定义 <input aria-label="表定义 CSV" type="file" accept=".csv" disabled={busy} onChange={e => setTables(e.target.files?.[0])} /></label>
          <label>字段与外键 <input aria-label="字段与外键 CSV" type="file" accept=".csv" disabled={busy} onChange={e => setFields(e.target.files?.[0])} /></label>
          <Button disabled={!tables || !fields || busy} onClick={() => analyze.mutate(false)}>分析上传文件</Button>
        </Space> }]} />
      </div>
      {!analysis ? <Empty description="读取项目表结构，或上传表定义与字段 CSV，开始查找对象" /> : <>
        {descriptions.isError && <Alert type="error" showIcon message={(descriptions.error as Error).message} />}
        <div className="import-translation-status"><Space wrap><Tag>{candidates.length} 个对象</Tag>
          <Typography.Text type="secondary">系统说明 · {state?.completed || 0} / {state?.total || 0} 已翻译</Typography.Text>
          {state && ["waiting", "pending", "running"].includes(state.status) && <Progress size="small" percent={state.total ? Math.round(state.completed / state.total * 100) : 0} style={{ width: 150 }} />}
          <Button size="small" loading={retry.isPending} disabled={busy || state?.metadataStatus === "loading" || ["waiting", "pending", "running"].includes(state?.status || "")} onClick={() => retry.mutate()}>重试读取 / 翻译</Button>
          <Typography.Text type="secondary">中文译文与英文原文保留，提交后仍需审阅。</Typography.Text></Space>
          {state?.warning && <Alert type="warning" showIcon message={state.warning} />}</div>
        <div className="import-explorer-grid">
          <Card size="small" title="物理表目录" className="import-object-directory" extra={<Button size="small" onClick={() => setOnlySelected(v => !v)}>{onlySelected ? "显示全部" : `已选 ${selected.length}`}</Button>}>
            <Input allowClear prefix={<SearchOutlined />} placeholder="搜索对象名称（表名）" value={search} onChange={e => setSearch(e.target.value)} />
            <Table<ImportCandidate> size="small" rowKey="className" dataSource={candidates.filter(c => (!onlySelected || selected.includes(c.className)) && c.className.toLowerCase().includes(search.trim().toLowerCase()))}
              rowSelection={{ selectedRowKeys: selected, preserveSelectedRowKeys: true, onChange: keys => setSelected(keys as string[]), getCheckboxProps: () => ({ disabled: busy }) }}
              pagination={false}
              rowClassName={c => c.className === active ? "import-active-row" : ""}
              columns={[{ title: "对象 / 系统说明", render: (_, c) => <div className="import-candidate"><Button type="link" onClick={() => visit(c.className)}>{c.className}</Button>
                <Typography.Paragraph ellipsis={{ rows: 2, tooltip: c.descriptionZh || c.descriptionEn }}>{c.descriptionZh || c.descriptionEn || "暂无系统说明"}</Typography.Paragraph>
                <Typography.Text type="secondary">{c.propertyCount} 字段 · {c.relationshipCount} 引用 · {c.incomingCount} 被引用</Typography.Text></div> }]} />
          </Card>
          <Card size="small" title="表与物理关联" className="import-object-detail">
            {!current ? <Empty description="点击左侧对象，查看字段和双向关联" /> : <>
              <Space wrap className="import-trail"><Button size="small" icon={<ArrowLeftOutlined />} disabled={trail.length < 2} onClick={() => setTrail(path => path.slice(0, -1))}>返回</Button>
                {trail.map((name, index) => <Button size="small" type={index === trail.length - 1 ? "primary" : "text"} key={`${index}:${name}`} onClick={() => setTrail(path => path.slice(0, index + 1))}>{index > 0 && "› "}{name}</Button>)}</Space>
              <div className="import-detail-heading"><div><Typography.Title level={4}>{current.className}</Typography.Title><Typography.Text type="secondary">{current.workspace || "默认工作区"} · {current.propertyCount} 个字段</Typography.Text></div>
                <Button icon={<PlusOutlined />} disabled={busy} type={selected.includes(current.className) ? "default" : "primary"} onClick={() => toggle(current.className)}>{selected.includes(current.className) ? "移除来源选择" : "选择为建模来源"}</Button></div>
              <div className="import-bilingual"><Typography.Text strong>中文说明</Typography.Text><Typography.Paragraph>{current.descriptionZh || "暂无中文译文"}</Typography.Paragraph>
                <Typography.Text type="secondary">英文原文 · Camstar Designer</Typography.Text><Typography.Paragraph className="import-original">{current.descriptionEn || "系统未提供说明，或正在读取"}</Typography.Paragraph></div>
              {detail.isError ? <Alert type="error" message={(detail.error as Error).message} /> : <Tabs items={[
                { key: "outgoing", label: `引用对象 (${current.relationshipCount})`, children: detail.isLoading ? <Card loading /> : related(detail.data?.outgoing || [], false) },
                { key: "incoming", label: `被哪些对象引用 (${current.incomingCount})`, children: related(detail.data?.incoming || [], true) },
                { key: "fields", label: "物理字段", children: <><Button loading={enrich.isPending} disabled={busy} onClick={() => enrich.mutate(current.className)}>读取并保存字段中英文说明</Button>
                  <Table rowKey="physicalName" size="small" dataSource={detail.data?.fields || []} pagination={{ pageSize: 8, showSizeChanger: false }} columns={[
                    { title: "原始字段", render: (_, field) => <>{field.physicalName}{field.primaryKey && <Tag>主键</Tag>}</> }, { title: "类型", dataIndex: "type" },
                    { title: "系统说明", render: (_, field) => <><div>{field.descriptionZh || "—"}</div><Typography.Text type="secondary">{field.descriptionEn || "—"}</Typography.Text></> },
                  ]} /></> },
              ]} />}
            </>}
          </Card>
        </div>
        <div className="import-selection-footer"><Space wrap><Typography.Text strong>已选 {selected.length} 个对象</Typography.Text><Button size="small" disabled={busy || !selected.length} onClick={() => setSelected([])}>清空选择</Button></Space>
          <div className="import-selected-tags">{selected.map(name => <Tag key={name} closable={!busy} onClose={() => toggle(name)}><a onClick={() => visit(name)}>{name}</a></Tag>)}</div>
          <Button type="primary" disabled={!selected.length || busy} loading={stage.isPending} onClick={() => stage.mutate()}>将 {selected.length} 张表加入语义建模草稿</Button></div>
      </>}
    </div>
  </div>;
}
