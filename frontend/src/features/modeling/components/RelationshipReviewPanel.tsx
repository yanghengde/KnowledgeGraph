import { useState } from "react";
import { Alert, Button, Card, Input, Space, Tag, Typography } from "antd";
import type { MappingDetail, SourceDesign } from "../../../mappingApi";

export function RelationshipReviewPanel({ detail, design, busy, onConfirm }: {
  detail: MappingDetail; design: SourceDesign; busy: boolean;
  onConfirm: (field: string, meaning: string, actor: string) => void;
}) {
  const [meanings, setMeanings] = useState<Record<string, string>>({});
  const [actor, setActor] = useState("");
  const fields = detail.fields.filter(f => design.fields[f.name] === "relationship");
  if (!fields.length) return null;
  return <Card size="small" title="确认关系的业务含义">
    <Space orientation="vertical" style={{ width: "100%" }}>
      <Alert type="info" message="勾选仅代表采用关系，下面的确认会保存独立审核记录。"
        description="确认人是手工填写的审阅标识，不是登录身份认证；业务确认不替代实例数据验证。" />
      <Input aria-label="关系确认人" placeholder="确认人（用于审阅追溯）" maxLength={200} value={actor} onChange={e => setActor(e.target.value)} disabled={busy} />
      {fields.map(field => {
        const review = design.relationshipReviews?.[field.name];
        const unchanged = (meanings[field.name] === undefined || meanings[field.name] === review?.meaning) && design.role === detail.design.role && design.chineseName === detail.design.chineseName
          && design.description === detail.design.description && design.fields[field.name] === detail.design.fields[field.name];
        return <Card key={field.name} size="small" title={`${field.physicalName} → ${field.target}`}>
          <Space orientation="vertical" style={{ width: "100%" }}>
            <Tag color={review && unchanged ? "green" : "orange"}>{review && unchanged ? "业务含义已确认" : "待确认"}</Tag>
            {review && <Typography.Text type="secondary">上次确认：{review.actor} · {new Date(review.confirmedAt).toLocaleString()}</Typography.Text>}
            <Input.TextArea aria-label={`${field.physicalName} 业务含义`} placeholder="说明这条关系在业务上代表什么，不确定时先保留待确认。"
              maxLength={4000} value={meanings[field.name] ?? review?.meaning ?? ""} disabled={busy}
              onChange={e => setMeanings({ ...meanings, [field.name]: e.target.value })} />
            <Button disabled={busy || !actor.trim() || !(meanings[field.name] ?? review?.meaning ?? "").trim()}
              onClick={() => onConfirm(field.name, meanings[field.name] ?? review?.meaning ?? "", actor)}>确认这条关系</Button>
          </Space>
        </Card>;
      })}
      {!!detail.design.relationshipReviewHistory?.length && <details><summary>历史确认记录（{detail.design.relationshipReviewHistory.length}）</summary>
        {detail.design.relationshipReviewHistory.map((r, index) => <p key={index}>{r.sourceField} → {r.targetTable}：{r.meaning} — {r.actor}，{new Date(r.confirmedAt).toLocaleString()}</p>)}
      </details>}
    </Space>
  </Card>;
}
