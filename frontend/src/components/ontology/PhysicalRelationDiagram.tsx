import { useMemo, useState } from "react";
import { Button, Empty, Modal, Tag } from "antd";
import type { ImportCandidate, PhysicalEdge } from "../../authorityApi";

type Props = {
  active: string;
  edges: PhysicalEdge[];
  candidates: ImportCandidate[];
  used: Set<string>;
  usageKnown: boolean;
  onSelect: (name: string) => void;
};

/** Physical relationships retain every field, including self references and missing targets. */
export function PhysicalRelationDiagram({ active, edges, candidates, used, usageKnown, onSelect }: Props) {
  const [expanded, setExpanded] = useState(false);
  const related = useMemo(() => edges.filter(e => e.source === active || e.target === active), [edges, active]);
  const catalog = new Map(candidates.map(c => [c.className, c]));
  const neighbors = new Set(related.flatMap(e => [e.source, e.target]).filter(name => name !== active));
  const groups = (direction: "in" | "out") => {
    const result = new Map<string, PhysicalEdge[]>();
    for (const edge of related) {
      // Show self references once, in the outgoing column.
      if (direction === "in" ? edge.target !== active || edge.source === active : edge.source !== active) continue;
      const name = direction === "in" ? edge.source : edge.target;
      result.set(name, [...(result.get(name) || []), edge]);
    }
    return [...result].sort(([a], [b]) => a.localeCompare(b));
  };
  const incoming = groups("in");
  const outgoing = groups("out");
  const column = (items: [string, PhysicalEdge[]][], direction: "in" | "out") => <section className={`physical-relation-column ${direction}`}>
    <h4>{direction === "in" ? "引用当前表" : "当前表引用"}<span>{items.length} 张表 · {items.reduce((sum, [, list]) => sum + list.length, 0)} 条关联</span></h4>
    <div className="physical-relation-nodes">
      {items.length === 0 && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无此方向的关联" />}
      {items.map(([name, list]) => <article className="physical-relation-node" key={name}>
        <Button type="link" disabled={!catalog.has(name) || name === active} onClick={() => onSelect(name)}>{name}</Button>
        <div className="physical-relation-status">{name === active && <Tag>自身关联</Tag>}{!catalog.has(name) ? <Tag color="warning">未导入表结构</Tag> : used.has(name) ? <Tag color="blue">已用于建模</Tag> : <Tag>{usageKnown ? "未使用" : "状态待核实"}</Tag>}</div>
        {(catalog.get(name)?.descriptionZh || catalog.get(name)?.descriptionEn) && <p>{catalog.get(name)?.descriptionZh || catalog.get(name)?.descriptionEn}</p>}
        <details><summary>{list.length} 条字段关联 · 展开查看</summary><ul>{list.map((edge, index) => <li key={`${edge.fieldId}:${index}`}><span>{edge.source}.{edge.fieldName}</span><span aria-label="引用"> → </span><span>{edge.target}{edge.targetField ? `.${edge.targetField}` : ""}</span></li>)}</ul></details>
      </article>)}
    </div>
  </section>;
  const diagram = () => <div className="physical-relation-scroll" key={active} tabIndex={0} aria-label={`${active} 完整双向物理关联图`}>
    <div className="physical-relation-layout">
      {column(incoming, "in")}
      <div className="physical-relation-center"><div><span>当前表</span><strong>{active}</strong><span>左侧表 → 当前表 → 右侧表</span></div></div>
      {column(outgoing, "out")}
    </div>
  </div>;
  return <div className="physical-relation-diagram">
    <div className="physical-relation-toolbar"><div><strong>{neighbors.size} 张关联表 · {related.length} 条字段关联</strong><p>全部直接关联均已展示，向下滚动浏览。点击表名继续探索，展开查看字段。</p></div><Button onClick={() => setExpanded(true)}>放大查看</Button></div>
    {diagram()}
    <Modal title={`${active} · ${neighbors.size} 张关联表 · ${related.length} 条字段关联`} open={expanded} onCancel={() => setExpanded(false)} footer={null} width="94vw" className="physical-relation-modal" destroyOnHidden>{expanded && diagram()}</Modal>
  </div>;
}
