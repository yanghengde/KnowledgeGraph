import { ArrowLeftOutlined, ArrowRightOutlined, PlusOutlined, SearchOutlined } from "@ant-design/icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, App, Button, Card, Collapse, Empty, Input, Modal, Progress, Select, Space, Table, Tabs, Tag, Typography } from "antd";
import { useState } from "react";
import { authorityApi, type ImportAnalysis, type ImportCandidate, type PhysicalEdge } from "../../authorityApi";

export function ImportDialog({ open, close, done }: { open: boolean; close: () => void; done: () => Promise<void> }) {
  const { message } = App.useApp();
  const [tables, setTables] = useState<File>();
  const [fields, setFields] = useState<File>();
  const [database, setDatabase] = useState("sqlserver");
  const [analysis, setAnalysis] = useState<ImportAnalysis>();
  const [selected, setSelected] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [trail, setTrail] = useState<string[]>([]);
  const [onlySelected, setOnlySelected] = useState(false);
  const active = trail.at(-1);
  const accept = (data: ImportAnalysis) => {
    setAnalysis(data); setSelected([]); setTrail([]); setSearch(""); setOnlySelected(false);
  };
  const analyze = useMutation({ mutationFn: (standard: boolean) => {
    if (standard) return authorityApi.standard(database);
    const form = new FormData(); form.append("tables", tables!); form.append("fields", fields!); form.append("database", database);
    return authorityApi.analyze(form);
  }, onSuccess: accept, onError: (e: Error) => message.error(e.message) });
  const descriptions = useQuery({
    queryKey: ["import-translations", analysis?.importId],
    queryFn: () => authorityApi.importTranslations(analysis!.importId), enabled: open && !!analysis,
    refetchInterval: query => {
      const state = query.state.data?.translation;
      return !state || ["waiting", "pending", "running"].includes(state.status) ? 2000 : false;
    },
  });
  const detail = useQuery({ queryKey: ["import-object", analysis?.importId, active, descriptions.data?.translation.status],
    queryFn: () => authorityApi.importObject(analysis!.importId, active!), enabled: open && !!analysis && !!active });
  const retry = useMutation({ mutationFn: () => authorityApi.retryTranslations(analysis!.importId),
    onSuccess: () => descriptions.refetch(), onError: (e: Error) => message.error(e.message) });
  const enrich = useMutation({ mutationFn: (name: string) => authorityApi.enrichObject(analysis!.importId, name),
    onSuccess: data => { if (data.warning) message.warning(data.warning); else message.success("中英文说明已保存"); void detail.refetch(); },
    onError: (e: Error) => message.error(e.message) });
  const stage = useMutation({ mutationFn: () => authorityApi.stage(analysis!.importId, selected),
    onSuccess: async () => { setAnalysis(undefined); setTrail([]); setSelected([]); await done(); }, onError: (e: Error) => message.error(e.message) });
  const busy = analyze.isPending || stage.isPending || enrich.isPending;
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
      { title: "候选", width: 95, render: (_, edge) => { const name = incoming ? edge.source : edge.target; return <Button size="small" disabled={busy || !byName.has(name)} onClick={() => toggle(name)}>{selected.includes(name) ? "移除" : "加入"}</Button>; } },
    ]} locale={{ emptyText: "CSV 中没有该方向的外键关系" }} />;
  return <Modal title="探索原始对象 · 逐步建立本体" open={open} onCancel={close} closable={!busy} maskClosable={!busy} keyboard={!busy}
    width="min(1500px, 96vw)" footer={null} style={{ top: 24 }}>
    <div className="import-explorer">
      <div className="import-source-bar">
        <Space wrap><Select aria-label="系统说明来源" value={database} disabled={busy} onChange={value => { setDatabase(value); setAnalysis(undefined); setTrail([]); }}
          options={[{ value: "sqlserver", label: "Camstar SQL Server" }, { value: "oracle", label: "Camstar Oracle" }]} style={{ width: 210 }} />
          <Button type={analysis ? "default" : "primary"} loading={analyze.isPending} disabled={stage.isPending || enrich.isPending} onClick={() => analyze.mutate(true)}>读取项目标准表结构</Button>
          <Typography.Text type="secondary">从一个对象开始，沿外键发现相关表，再加入候选。</Typography.Text></Space>
        <Collapse ghost items={[{ key: "upload", label: "使用其他 CSV 文件", children: <Space wrap>
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
          <Card size="small" title="原始对象目录" className="import-object-directory" extra={<Button size="small" onClick={() => setOnlySelected(v => !v)}>{onlySelected ? "显示全部" : `已选 ${selected.length}`}</Button>}>
            <Input allowClear prefix={<SearchOutlined />} placeholder="搜索表名、中文或英文说明" value={search} onChange={e => setSearch(e.target.value)} />
            <Table<ImportCandidate> size="small" rowKey="className" dataSource={candidates.filter(c => (!onlySelected || selected.includes(c.className)) && `${c.className} ${c.descriptionZh} ${c.descriptionEn}`.toLowerCase().includes(search.toLowerCase()))}
              rowSelection={{ selectedRowKeys: selected, preserveSelectedRowKeys: true, onChange: keys => setSelected(keys as string[]), getCheckboxProps: () => ({ disabled: busy }) }}
              pagination={{ pageSize: 8, showSizeChanger: false, showTotal: total => `${total} 个对象` }}
              rowClassName={c => c.className === active ? "import-active-row" : ""}
              columns={[{ title: "对象 / 系统说明", render: (_, c) => <div className="import-candidate"><Button type="link" onClick={() => visit(c.className)}>{c.className}</Button>
                <Typography.Paragraph ellipsis={{ rows: 2, tooltip: c.descriptionZh || c.descriptionEn }}>{c.descriptionZh || c.descriptionEn || "暂无系统说明"}</Typography.Paragraph>
                <Typography.Text type="secondary">{c.propertyCount} 字段 · {c.relationshipCount} 引用 · {c.incomingCount} 被引用</Typography.Text></div> }]} />
          </Card>
          <Card size="small" title="对象与关联探索" className="import-object-detail">
            {!current ? <Empty description="点击左侧对象，查看字段和双向关联" /> : <>
              <Space wrap className="import-trail"><Button size="small" icon={<ArrowLeftOutlined />} disabled={trail.length < 2} onClick={() => setTrail(path => path.slice(0, -1))}>返回</Button>
                {trail.map((name, index) => <Button size="small" type={index === trail.length - 1 ? "primary" : "text"} key={`${index}:${name}`} onClick={() => setTrail(path => path.slice(0, index + 1))}>{index > 0 && "› "}{name}</Button>)}</Space>
              <div className="import-detail-heading"><div><Typography.Title level={4}>{current.className}</Typography.Title><Typography.Text type="secondary">{current.workspace || "默认工作区"} · {current.propertyCount} 个字段</Typography.Text></div>
                <Button icon={<PlusOutlined />} disabled={busy} type={selected.includes(current.className) ? "default" : "primary"} onClick={() => toggle(current.className)}>{selected.includes(current.className) ? "从候选移除" : "加入候选"}</Button></div>
              <div className="import-bilingual"><Typography.Text strong>中文说明</Typography.Text><Typography.Paragraph>{current.descriptionZh || "暂无中文译文"}</Typography.Paragraph>
                <Typography.Text type="secondary">英文原文 · Camstar Designer</Typography.Text><Typography.Paragraph className="import-original">{current.descriptionEn || "系统未提供说明，或正在读取"}</Typography.Paragraph></div>
              {detail.isError ? <Alert type="error" message={(detail.error as Error).message} /> : <Tabs items={[
                { key: "outgoing", label: `引用对象 (${current.relationshipCount})`, children: detail.isLoading ? <Card loading /> : related(detail.data?.outgoing || [], false) },
                { key: "incoming", label: `被哪些对象引用 (${current.incomingCount})`, children: related(detail.data?.incoming || [], true) },
                { key: "fields", label: "物理字段", children: <><Button loading={enrich.isPending} disabled={busy} onClick={() => enrich.mutate(current.className)}>读取并保存字段中英文说明</Button>
                  <Table rowKey="physicalName" size="small" dataSource={detail.data?.fields || []} pagination={{ pageSize: 8, showSizeChanger: false }} columns={[
                    { title: "原始字段", dataIndex: "physicalName" }, { title: "类型", dataIndex: "type" },
                    { title: "系统说明", render: (_, field) => <><div>{field.descriptionZh || "—"}</div><Typography.Text type="secondary">{field.descriptionEn || "—"}</Typography.Text></> },
                  ]} /></> },
              ]} />}
            </>}
          </Card>
        </div>
        <div className="import-selection-footer"><Space wrap><Typography.Text strong>已选 {selected.length} 个对象</Typography.Text><Button size="small" disabled={busy || !selected.length} onClick={() => setSelected([])}>清空选择</Button></Space>
          <div className="import-selected-tags">{selected.map(name => <Tag key={name} closable={!busy} onClose={() => toggle(name)}><a onClick={() => visit(name)}>{name}</a></Tag>)}</div>
          <Button type="primary" disabled={!selected.length || analyze.isPending || enrich.isPending} loading={stage.isPending} onClick={() => stage.mutate()}>提交 {selected.length} 个对象为待审阅候选</Button></div>
      </>}
    </div>
  </Modal>;
}
