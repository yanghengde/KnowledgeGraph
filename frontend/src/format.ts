import type { SavedQuery } from "./types";

const QUERY_LABELS: Record<string, string> = {
  "product-order": "产品—制造订单统计",
  "query-test": "制造订单属性查询",
};

export function queryBusinessTitle(query: Pick<SavedQuery, "title">): string {
  return QUERY_LABELS[query.title] || query.title;
}

export function queryBusinessDescription(query: SavedQuery): string {
  const description = (query.description || "").trim();
  if (!description || /\b(?:PREFIX|SELECT|WHERE)\b/i.test(description)) {
    return "从 Graph Studio 同步的受控制造查询；建议在 Query 中补充业务说明。";
  }
  return description.replace(/^[“”"']+|[“”"']+$/g, "");
}
