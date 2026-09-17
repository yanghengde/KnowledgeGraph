import { ReloadOutlined } from "@ant-design/icons";
import { useQuery,useQueryClient } from "@tanstack/react-query";
import { Button,Card,Space,Table,Tag,Typography,type TableColumnsType } from "antd";
import dayjs from "dayjs";
import { manufacturingApi } from "../../../api";
import { queryBusinessDescription,queryBusinessTitle } from "../../../format";
import type { SavedQuery } from "../../../types";

export function QueryLibraryPage() {
  const queryClient = useQueryClient();
  const catalog = useQuery({ queryKey: ["saved-queries"], queryFn: () => manufacturingApi.queries() });
  const columns: TableColumnsType<SavedQuery> = [
    { title: "查询能力", dataIndex: "title", width: 240, render: (_, row) => <span className="query-name"><Typography.Text strong>{queryBusinessTitle(row)}</Typography.Text><Typography.Text type="secondary">{row.title}</Typography.Text></span> },
    { title: "业务说明", dataIndex: "description", ellipsis: true, render: (_, row) => queryBusinessDescription(row) },
    { title: "结果上限", dataIndex: "forced_limit", width: 110, render: (_, row) => <Tag>{row.forced_limit || "受控"}</Tag> },
    { title: "最后更新", dataIndex: "modified", width: 180, render: (_, row) => row.modified ? dayjs(row.modified).format("YYYY-MM-DD HH:mm") : "—" },
    { title: "执行策略", width: 130, render: () => <Tag color="success">只读 SELECT</Tag> },
  ];

  return (
    <div className="page-stack">
      <div className="section-intro">
        <div><Typography.Title level={3}>图谱查询能力库</Typography.Title><Typography.Paragraph>自动同步当前 Graphmart 中保存的 Queries，作为制造知识问答的优先检索能力。</Typography.Paragraph></div>
      </div>
      <Card
        title={`${catalog.data?.count ?? 0} 条受控查询`}
        extra={(
          <Button icon={<ReloadOutlined />} onClick={async () => {
            await manufacturingApi.queries(true);
            await queryClient.invalidateQueries({ queryKey: ["saved-queries"] });
          }}>同步 Graph Studio</Button>
        )}
      >
        <Space direction="vertical" size={14} style={{ width: "100%" }}>
          <Typography.Text type="secondary">仅展示通过只读安全校验的 SELECT Query。</Typography.Text>
          <Table<SavedQuery>
            rowKey="uri"
            columns={columns}
            dataSource={catalog.data?.items || []}
            loading={catalog.isLoading}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 900 }}
          />
        </Space>
      </Card>
    </div>
  );
}
