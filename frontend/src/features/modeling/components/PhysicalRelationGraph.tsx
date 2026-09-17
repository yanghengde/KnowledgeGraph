import { Button,Empty,Input,Modal,Tag } from "antd";
import { useEffect,useMemo,useState,type ReactNode } from "react";
import type { ImportCandidate,PhysicalEdge } from "../../../authorityApi";

type Props = {
  active: string;
  edges: PhysicalEdge[];
  candidates: ImportCandidate[];
  renderUsage: (name: string) => ReactNode;
  actionLabel: (name: string) => string;
  onAdd: (name: string) => void;
  busy: boolean;
  adding?: string;
  onSelect: (name: string) => void;
};

/** Physical relationships retain every field, including self references and missing targets. */
export function PhysicalRelationGraph({ active, edges, candidates, renderUsage, actionLabel, onAdd, busy, adding, onSelect }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [searches, setSearches] = useState({ in: "", out: "" });
  useEffect(() => { setSearches({ in: "", out: "" }); }, [active]);
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
  const column = (items: [string, PhysicalEdge[]][], direction: "in" | "out") => {
    const term = searches[direction].trim().toLocaleLowerCase();
    const visible = items.filter(([name, list]) => [name, catalog.get(name)?.descriptionZh, catalog.get(name)?.descriptionEn,
      ...list.flatMap(edge => [edge.fieldName, edge.targetField])].join(" ").toLocaleLowerCase().includes(term));
    return <section className={`physical-relation-column ${direction}`}>
    <div className="physical-relation-column-header"><h4>{direction === "in" ? "使用当前表的数据" : "当前表使用的数据"}<span>{term ? `${visible.length} / ${items.length}` : items.length} 张表 · {visible.reduce((sum, [, list]) => sum + list.length, 0)} 条关联</span></h4>
      <Input allowClear aria-label={direction === "in" ? "搜索左侧关联表" : "搜索右侧关联表"} placeholder="搜索表名、说明或字段" value={searches[direction]} onChange={event => setSearches(previous => ({ ...previous, [direction]: event.target.value }))} />
    </div>
    <div className="physical-relation-nodes">
      {visible.length === 0 && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={term ? "没有匹配的关联表，请调整或清空搜索" : "无此方向的关联"} />}
      {visible.map(([name, list]) => <article className="physical-relation-node" key={name}>
        <div className="physical-relation-node-header">
          <Button type="link" disabled={!catalog.has(name) || name === active} onClick={() => onSelect(name)}>{name}</Button>
          <Button size="small" disabled={!catalog.has(name) || busy} loading={adding === name} onClick={() => onAdd(name)} aria-label={`${actionLabel(name)} ${name}`}>{actionLabel(name)}</Button>
        </div>
        <div className="physical-relation-direction" aria-label="箭头指向使用该数据的表"><span>{direction === "in" ? active : name}</span><b aria-hidden="true">→</b><span>{direction === "in" ? name : active}</span></div>
        <div className="physical-relation-status">{name === active && <Tag>自身关联</Tag>}{!catalog.has(name) ? <Tag color="warning">未导入表结构</Tag> : renderUsage(name)}</div>
        {(catalog.get(name)?.descriptionZh || catalog.get(name)?.descriptionEn) && <p>{catalog.get(name)?.descriptionZh || catalog.get(name)?.descriptionEn}</p>}
        <details><summary>{list.length} 条字段关联 · 展开查看</summary><ul>{list.map((edge, index) => <li key={`${edge.fieldId}:${index}`}><span>{edge.target}{edge.targetField ? `.${edge.targetField}` : ""}</span><span aria-label="被使用于"> → </span><span>{edge.source}.{edge.fieldName}</span></li>)}</ul></details>
      </article>)}
    </div>
  </section>;
  };
  const diagram = () => <div className="physical-relation-scroll" key={active} tabIndex={0} aria-label={`${active} 完整双向物理关联图`}>
    <div className="physical-relation-layout">
      {column(incoming, "in")}
      <div className="physical-relation-center"><div><span>当前表</span><strong>{active}</strong><span>箭头指向使用方</span><span>左侧表 ← 当前表 ← 右侧表</span></div></div>
      {column(outgoing, "out")}
    </div>
  </div>;
  return <div className="physical-relation-diagram">
    <div className="physical-relation-toolbar"><div><strong>{neighbors.size} 张关联表 · {related.length} 条字段关联</strong><p>箭头表示“被谁使用”：例如 UOM → Product。左右可独立搜索，清空搜索显示全部直接关联。</p></div><Button onClick={() => setExpanded(true)}>放大查看</Button></div>
    {diagram()}
    <Modal title={`${active} · ${neighbors.size} 张关联表 · ${related.length} 条字段关联`} open={expanded} onCancel={() => setExpanded(false)} footer={null} width="94vw" className="physical-relation-modal" destroyOnHidden>{expanded && diagram()}</Modal>
  </div>;
}
