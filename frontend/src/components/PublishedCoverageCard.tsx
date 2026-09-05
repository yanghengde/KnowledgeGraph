import { ReloadOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Collapse, Space, Table, Tag, Typography } from "antd";
import { useState } from "react";
import { manufacturingApi } from "../api";

export function PublishedCoverageCard({ profileKey }: { profileKey: string }) {
  const [refreshing, setRefreshing] = useState(false);
  const coverage = useQuery({ queryKey: ["published-coverage"], queryFn: () => manufacturingApi.coverage(), staleTime: 30_000 });
  const data = coverage.data;
  const names = new Map(data?.classes.map((item) => [item.uri, item.name]) || []);
  const count = (value: number | null) => value == null ? <Tag>未核实</Tag> : value > 0 ? <Tag color="success">{value.toLocaleString()} 条</Tag> : <Tag>已定义，暂无数据</Tag>;
  const refresh = async () => {
    setRefreshing(true);
    try { await manufacturingApi.coverage(true); await coverage.refetch(); }
    finally { setRefreshing(false); }
  };
  return <Card title="当前问数版本 · 本体与关联验收" loading={coverage.isLoading} extra={<Button icon={<ReloadOutlined />} loading={refreshing} onClick={() => void refresh().catch(() => coverage.refetch())}>重新核实</Button>}>
    {coverage.isError ? <Alert type="warning" showIcon title="暂时无法读取已发布版本" description={(coverage.error as Error).message} /> : data && data.runtime.profileKey === profileKey ? <Space orientation="vertical" size={16} style={{ width: "100%" }}>
      <Space wrap>
        <Tag color="cyan">本体 R{data.runtime.ontologyReleaseNo}</Tag><Tag color="blue">数据 R{data.runtime.curatedReleaseNo}</Tag>
        <Tag>{data.runtime.environmentKey || data.runtime.routeKey}</Tag>
        <Typography.Text>已发布 {data.summary.definedClasses} 类对象、{data.summary.definedRelationships} 种关系；其中 {data.summary.classesWithData} 类对象、{data.summary.relationshipsWithData} 种关系已查到数据。</Typography.Text>
      </Space>
      <Typography.Text type="secondary">核实范围是当前 Graph Studio 问数数据层。关系定义存在，不代表源数据已填充该关系；暂无数据也不等于发布失败。与问数相同版本的快照会复用，点击“重新核实”可检查最新状态。</Typography.Text>
      <Collapse items={[
        { key: "classes", label: "查看对象与数据数量", children: <Table size="small" rowKey="uri" dataSource={data.classes} pagination={{ pageSize: 10 }} columns={[
          { title: "业务对象", dataIndex: "name" }, { title: "已发布属性", dataIndex: "propertyCount" }, { title: "对象数据", dataIndex: "count", render: count },
        ]} /> },
        { key: "relations", label: "查看关系方向与数据数量", children: <Table size="small" rowKey={(item) => `${item.source}:${item.uri}:${item.target}`} dataSource={data.relationships} pagination={{ pageSize: 10 }} scroll={{ x: 650 }} columns={[
          { title: "起点", dataIndex: "source", render: (v: string) => names.get(v) || v },
          { title: "关系", dataIndex: "name" }, { title: "终点", dataIndex: "target", render: (v: string) => names.get(v) || v },
          { title: "关联数据", dataIndex: "count", render: count },
        ]} /> },
      ]} />
      {(data.summary.unknownClassCounts > 0 || data.summary.unknownRelationshipCounts > 0) && <Alert type="warning" showIcon title="部分数据数量未核实，请重新核实后再判断关联是否完整。" />}
    </Space> : <Typography.Text type="secondary">当前问数路由未对应此业务范围，请先发布并配置问数路由。</Typography.Text>}
  </Card>;
}
