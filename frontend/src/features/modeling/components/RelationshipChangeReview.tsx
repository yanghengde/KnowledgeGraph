import { Alert, Space, Table, Tag, Typography } from "antd";
import type { RelationshipChange } from "../../../mappingApi";

const labels = { added: "新增", retained: "保留已有设置", removed: "移除" };
export function RelationshipChangeReview({ items }: { items: RelationshipChange[] }) {
  if (!items.length) return <Typography.Text type="secondary">本次没有新增、保留或移除的物理关系。</Typography.Text>;
  return <Space orientation="vertical" style={{ width: "100%" }}>
    <Typography.Text strong>本次关系变化</Typography.Text>
    <Alert showIcon type="info" message="请按来源字段逐条核对，指向同一对象的关系也可能含义不同。"
      description="保留关系沿用已有业务名称和治理设置。这里检查模型结构，未验证 Camstar 实例数据。" />
    <Table<RelationshipChange> size="small" pagination={false} dataSource={items}
      rowKey={item => `${item.sourceField}:${item.targetTable}:${item.change}:${item.businessNames.join(",")}`}
      columns={[
        { title: "变化", width: 130, render: (_, item) => <Tag color={item.change === "removed" ? "orange" : item.change === "added" ? "blue" : "default"}>{labels[item.change]}</Tag> },
        { title: "物理依据", render: (_, item) => <Space orientation="vertical" size={2}>
          <Typography.Text>{item.sourceTable}.{item.sourceField}</Typography.Text>
          <Typography.Text>→ {item.targetTable}{item.targetField ? `.${item.targetField}` : "（目标字段未提供）"}</Typography.Text>
          {item.targetAvailable === false && <Tag color="error">目标尚未纳入模型</Tag>}
        </Space> },
        { title: "业务关系", render: (_, item) => item.businessNames.join("、") },
      ]} />
  </Space>;
}
