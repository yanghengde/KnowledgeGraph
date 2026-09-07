import { CheckCircleFilled, SearchOutlined, TagsOutlined, WarningOutlined } from "@ant-design/icons";
import { useMutation } from "@tanstack/react-query";
import { Alert, App, Button, Card, Empty, Form, Input, Radio, Select, Space, Switch, Table, Tag, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";
import { syncApi } from "../../api";
import type { OntologyClass, OntologyGraph, OntologyPresentationInput, OntologyProperty } from "../../types";

type Props = {
  graph?: OntologyGraph;
  workspaceKey?: string;
  selectedId: string;
  onSelect: (id: string) => void;
  onSaved: () => Promise<void>;
};

const nonScalarTypes = new Set(["navigation", "array", "subentity", "subentitylist"]);

function scalarProperties(properties: OntologyProperty[]) {
  return properties.filter((item) => item.published !== false && !nonScalarTypes.has(String(item.dataType || "string").toLocaleLowerCase()));
}

function suggestedTemplate(properties: OntologyProperty[]) {
  const names = scalarProperties(properties).map((item) => item.targetName);
  const byFold = new Map(names.map((name) => [name.toLocaleLowerCase(), name]));
  const displayName = byFold.get("displayname");
  if (displayName) return `{${displayName}}`;
  const name = byFold.get("name");
  const revision = byFold.get("revision");
  if (name && revision) return `{${name}} / Rev {${revision}}`;
  if (name) return `{${name}}`;
  for (const suffix of ["name", "code", "number", "no"]) {
    const candidate = names.find((item) => item.toLocaleLowerCase().endsWith(suffix));
    if (candidate) return `{${candidate}}`;
  }
  const description = byFold.get("description");
  return description ? `{${description}}` : "";
}

function defaults(item: OntologyClass, properties: OntologyProperty[]): OntologyPresentationInput {
  const names = scalarProperties(properties).map((property) => property.targetName);
  const byFold = new Map(names.map((name) => [name.toLocaleLowerCase(), name]));
  return {
    labelMode: item.labelMode || "auto",
    labelField: item.labelField || undefined,
    labelTemplate: item.labelTemplate || suggestedTemplate(properties) || undefined,
    labelFallbacks: item.labelFallbacks || [byFold.get("name"), byFold.get("description"), "$businessKey", "$primaryKey"].filter(Boolean) as string[],
    searchFields: item.searchFields || [byFold.get("displayname"), byFold.get("name"), byFold.get("description"), byFold.get("revision")].filter(Boolean) as string[],
    emitRdfsLabel: item.emitRdfsLabel !== false,
  };
}

function modeLabel(item: OntologyClass, properties: OntologyProperty[]) {
  const mode = item.labelMode || "auto";
  if (mode === "field") return { text: `字段 · ${item.labelField || "未配置"}`, color: item.labelField ? "blue" : "error" };
  if (mode === "template") return { text: "人工模板", color: item.labelTemplate ? "purple" : "error" };
  return suggestedTemplate(properties)
    ? { text: "自动推荐", color: "success" }
    : { text: "回退主键", color: "warning" };
}

export function OntologyPresentationPanel({ graph, workspaceKey, selectedId, onSelect, onSaved }: Props) {
  const { message } = App.useApp();
  const [form] = Form.useForm<OntologyPresentationInput>();
  const [search, setSearch] = useState("");
  const selected = graph?.nodes.find((item) => item.id === selectedId);
  const properties = useMemo(
    () => (graph?.properties || []).filter((item) => item.classUid === selectedId),
    [graph?.properties, selectedId],
  );
  const available = useMemo(() => scalarProperties(properties), [properties]);
  const suggestion = useMemo(() => suggestedTemplate(properties), [properties]);
  const mode = Form.useWatch("labelMode", form) || selected?.data.labelMode || "auto";
  const labelField = Form.useWatch("labelField", form);
  const template = Form.useWatch("labelTemplate", form);
  const filtered = useMemo(() => {
    const keyword = search.trim().toLocaleLowerCase();
    return (graph?.nodes || []).filter((node) => !keyword || [node.data.targetName, node.data.sourceClass, node.data.labelField, node.data.labelTemplate].some((value) => String(value || "").toLocaleLowerCase().includes(keyword)));
  }, [graph?.nodes, search]);

  useEffect(() => {
    if (!selected) return;
    form.setFieldsValue(defaults(selected.data, properties));
  }, [form, properties, selected]);

  const save = useMutation({
    mutationFn: (input: OntologyPresentationInput) => syncApi.updateOntologyPresentation(workspaceKey!, selectedId, input),
    onSuccess: async () => {
      message.success("显示与检索配置已保存");
      await onSaved();
    },
    onError: (error: Error) => message.error(error.message),
  });

  const insertToken = (name: string) => {
    const current = String(form.getFieldValue("labelTemplate") || "");
    form.setFieldValue("labelTemplate", `${current}${current ? " " : ""}{${name}}`);
  };
  const option = (name: string) => ({
    value: name,
    label: name === "$businessKey" ? "业务键" : name === "$primaryKey" ? "主键" : name,
  });

  return <div className="ontology-presentation-grid">
    <Card className="ontology-presentation-list" title={<Space><TagsOutlined /><span>对象显示策略</span></Space>} extra={<Tag>{filtered.length} 个</Tag>}>
      <Input allowClear prefix={<SearchOutlined />} placeholder="搜索对象、字段或模板" value={search} onChange={(event) => setSearch(event.target.value)} />
      <Table
        rowKey="id" size="small" pagination={false} scroll={{ y: 560 }} dataSource={filtered}
        columns={[{
          title: "发布对象", key: "name", render: (_, item) => {
            const ownProperties = (graph?.properties || []).filter((property) => property.classUid === item.id);
            const status = modeLabel(item.data, ownProperties);
            return <div className="presentation-object-name"><strong>{item.data.targetName}</strong><small>{item.data.sourceClass || "自定义对象"}</small><Tag color={status.color}>{status.text}</Tag></div>;
          },
        }]}
        onRow={(item) => ({ onClick: () => onSelect(item.id) })}
        rowClassName={(item) => item.id === selectedId ? "selected-row" : ""}
      />
    </Card>
    <Card className="ontology-presentation-editor" title={selected ? <div className="semantic-detail-title"><span>{selected.data.targetName}</span><small>Graph Studio 节点显示与问答识别</small></div> : "显示配置"}>
      {!selected ? <Empty description="选择左侧对象进行配置" /> : <Form form={form} layout="vertical" onFinish={(values) => save.mutate(values)}>
        <Alert type={suggestion ? "info" : "warning"} showIcon icon={suggestion ? <CheckCircleFilled /> : <WarningOutlined />} message={suggestion ? `自动建议：${suggestion}` : "没有找到适合展示的业务属性"} description={suggestion ? "自动模式会在发布时计算 displayLabel，并同时写入 rdfs:label。" : "建议新增业务名称属性，或使用业务键/主键作为回退。"} />
        <Form.Item name="labelMode" label="显示模式">
          <Radio.Group optionType="button" buttonStyle="solid" options={[{ label: "自动推荐", value: "auto" }, { label: "选择字段", value: "field" }, { label: "组合模板", value: "template" }]} />
        </Form.Item>
        {mode === "field" && <Form.Item name="labelField" label="显示字段" rules={[{ required: true, message: "请选择显示字段" }]}>
          <Select showSearch placeholder="选择一个已发布的文本或数值字段" options={available.map((item) => option(item.targetName))} />
        </Form.Item>}
        {mode === "template" && <>
          <Form.Item name="labelTemplate" label="显示模板" rules={[{ required: true, message: "请输入包含 {字段} 的模板" }, { pattern: /\{[^{}]+\}/, message: "模板至少需要一个 {字段} 占位符" }]}>
            <Input placeholder="例如：{name} / Rev {revision}" />
          </Form.Item>
          <div className="presentation-token-list"><Typography.Text type="secondary">插入字段：</Typography.Text><Select showSearch allowClear value={undefined} placeholder="搜索并插入 {字段}" options={available.map((item) => option(item.targetName))} onChange={(value) => value && insertToken(value)} /></div>
        </>}
        <Form.Item name="labelFallbacks" label="回退顺序" tooltip="当前规则无法生成名称时，按顺序尝试这些字段">
          <Select mode="multiple" options={[...available.map((item) => option(item.targetName)), option("$businessKey"), option("$primaryKey")]} />
        </Form.Item>
        <Form.Item name="searchFields" label="问答检索字段" tooltip="名称、编码、描述和别名等可用于识别实体的属性">
          <Select mode="multiple" options={available.map((item) => option(item.targetName))} />
        </Form.Item>
        <Form.Item name="emitRdfsLabel" label="标准 RDF 标签" valuePropName="checked">
          <Switch checkedChildren="发布 rdfs:label" unCheckedChildren="不发布" />
        </Form.Item>
        <div className="presentation-preview">
          <small>发布预览</small>
          <strong>{mode === "auto" ? suggestion || "业务键 / 主键" : mode === "field" ? `{${labelField || "字段"}}` : template || "请输入模板"}</strong>
          <span>实例 URI 仍由稳定主键生成，显示配置不会改变关系身份。</span>
        </div>
        <Button type="primary" htmlType="submit" loading={save.isPending} disabled={!workspaceKey}>保存显示配置</Button>
      </Form>}
    </Card>
  </div>;
}
