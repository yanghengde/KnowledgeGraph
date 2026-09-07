import { ArrowsAltOutlined } from "@ant-design/icons";
import { Button, Spin, Tag, Tooltip, Typography } from "antd";
import { useEffect, useRef, useState } from "react";
import type { OntologyGraph } from "../../types";

type GraphEvent = { target?: { id?: string }; client?: { x?: number; y?: number } };
type G6Graph = {
  render: () => Promise<void> | void; destroy: () => void; fitView: () => Promise<void> | void;
  on: (event: string, handler: (event: GraphEvent) => void) => void;
  setElementState: (states: Record<string, string[]>) => Promise<void> | void;
  resize: (width: number, height: number) => void;
};
type G6Runtime = { Graph: new (options: Record<string, unknown>) => G6Graph };
type GraphNode = { id: string; data: Record<string, unknown>; style: Record<string, unknown> };
type GraphEdge = { id: string; source: string; target: string; data: Record<string, unknown> };

type Props = {
  graph?: OntologyGraph;
  preview?: boolean;
  selectedId?: string;
  mode: "light" | "dark";
  onSelect: (id: string) => void;
};

const roleColors: Record<string, { fill: string; stroke: string }> = {
  core: { fill: "#087f86", stroke: "#27d4ba" },
  context: { fill: "#3769a8", stroke: "#70a8e8" },
  reference: { fill: "#7452a6", stroke: "#aa86d9" },
  on_demand: { fill: "#9a6a20", stroke: "#d9a84e" },
  excluded: { fill: "#5c686d", stroke: "#87969c" },
};

function runtime() {
  return (window as unknown as { G6?: G6Runtime }).G6;
}

function loadG6() {
  if (runtime()?.Graph) return Promise.resolve();
  const shared = (window as unknown as { __semanticG6Promise?: Promise<void> }).__semanticG6Promise;
  if (shared) return shared;
  const promise = new Promise<void>((resolve, reject) => {
    const script = document.createElement("script"); script.src = "/static/lib/g6.js"; script.async = true;
    script.onload = () => resolve(); script.onerror = () => reject(new Error("G6 图形引擎加载失败")); document.head.appendChild(script);
  });
  (window as unknown as { __semanticG6Promise?: Promise<void> }).__semanticG6Promise = promise;
  return promise;
}

function buildData(graph: OntologyGraph) {
  const byRole = new Map<string, typeof graph.nodes>();
  graph.nodes.forEach((node) => byRole.set(node.data.role, [...(byRole.get(node.data.role) || []), node]));
  const positions = new Map<string, { x: number; y: number }>();
  const placeRing = (nodes: typeof graph.nodes, radiusX: number, radiusY: number, offset = -Math.PI / 2) => {
    if (nodes.length === 1 && radiusX === 0) return positions.set(nodes[0].id, { x: 0, y: 0 });
    nodes.forEach((node, index) => {
      const angle = offset + index / Math.max(1, nodes.length) * Math.PI * 2;
      positions.set(node.id, { x: Math.cos(angle) * radiusX, y: Math.sin(angle) * radiusY });
    });
  };
  const core = byRole.get("core") || [];
  if (core.length === 1) placeRing(core, 0, 0); else placeRing(core, 125, 75, 0);
  placeRing(byRole.get("context") || [], 330, 205);
  placeRing(byRole.get("reference") || [], 430, 265, -Math.PI / 3);
  placeRing([...(byRole.get("on_demand") || []), ...(byRole.get("excluded") || [])], 510, 310);
  const unplaced = graph.nodes.filter((node) => !positions.has(node.id)); placeRing(unplaced, 390, 240);
  const propertyCount = new Map<string, number>();
  graph.properties.forEach((item) => { if (item.published !== false) propertyCount.set(item.classUid, (propertyCount.get(item.classUid) || 0) + 1); });
  const nodes: GraphNode[] = graph.nodes.map((node) => {
    const color = roleColors[node.data.role] || roleColors.context; const position = positions.get(node.id) || { x: 0, y: 0 };
    return { id: node.id, data: { ...node.data, propertyCount: propertyCount.get(node.id) || 0 }, style: { ...position, size: node.data.role === "core" ? 92 : 78, fill: color.fill, stroke: color.stroke, shadowColor: color.fill } };
  });
  const groups = new Map<string, typeof graph.edges>();
  graph.edges.forEach((edge) => { const key = `${edge.source}\0${edge.target}\0${Boolean(edge.data.preview)}`; groups.set(key, [...(groups.get(key) || []), edge]); });
  const edges: GraphEdge[] = [...groups.values()].map((items) => {
    const first = items[0]; const label = first.data.targetName || first.data.relationshipKey;
    return { id: first.id, source: first.source, target: first.target, data: { ...first.data, targetName: items.length > 1 ? `${label} (+${items.length - 1})` : label, relationshipCount: items.length } };
  });
  return { nodes, edges };
}

export function PublishOntologyCanvas({ graph, selectedId, mode, onSelect, preview = false }: Props) {
  const [renderVersion, setRenderVersion] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null); const graphRef = useRef<G6Graph | null>(null);
  const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  useEffect(() => {
    if (!graph || !containerRef.current) return;
    let disposed = false; let resizeObserver: ResizeObserver | undefined; setLoading(true); setError("");
    void loadG6().then(async () => {
      const G6 = runtime(); if (!G6 || disposed || !containerRef.current) return;
      graphRef.current?.destroy(); const data = buildData(graph);
      const labelFill = mode === "light" ? "#203b45" : "#edf7f7"; const edgeColor = mode === "light" ? "#71949e" : "#4c8f92";
      const instance = new G6.Graph({
        container: containerRef.current, width: containerRef.current.clientWidth, height: containerRef.current.clientHeight,
        data, layout: { type: "preset" }, autoFit: "view", padding: preview ? [55, 60, 55, 60] : [86, 100, 86, 100], animation: false,
        node: { type: "circle", style: {
          size: (item: GraphNode) => item.style.size, fill: (item: GraphNode) => item.style.fill, stroke: (item: GraphNode) => item.style.stroke,
          lineDash: (item: GraphNode) => item.data.preview ? [6, 4] : [],
          lineWidth: 3, labelText: (item: GraphNode) => String(item.data.targetName || item.id), labelFill, labelFontSize: 12, labelFontWeight: 700,
          labelPlacement: "bottom", labelOffsetY: 9, iconText: (item: GraphNode) => String(item.data.targetName || "").slice(0, 2), iconFill: "#fff", iconFontWeight: 800,
          badge: true, cursor: "pointer", ports: [{ placement: "center" }],
        }, state: { selected: { stroke: "#ffffff", lineWidth: 5, shadowColor: "#13c6ad", shadowBlur: 18, zIndex: 20 }, neighbor: { stroke: "#39d4bc", lineWidth: 4, zIndex: 15 }, inactive: { opacity: .6, labelOpacity: 1 } } },
        edge: { type: "quadratic", style: {
          lineDash: (item: GraphEdge) => item.data.preview ? [7, 5] : [],
          stroke: (item: GraphEdge) => item.data.preview ? "#d28b20" : edgeColor, lineWidth: 1.7, endArrow: true, curveOffset: 18,
          labelText: (item: GraphEdge) => String(item.data.targetName || ""), labelFill, labelFontSize: 10,
          labelBackground: true, labelBackgroundFill: mode === "light" ? "rgba(255,255,255,.94)" : "rgba(7,24,32,.94)", labelPadding: [3, 5],
        }, state: { active: { stroke: "#15b99c", lineWidth: 3, shadowColor: "#15b99c", shadowBlur: 8, zIndex: 12 }, inactive: { opacity: .3 } } },
        behaviors: ["drag-canvas", "zoom-canvas", { type: "drag-element", state: null }],
      });
      graphRef.current = instance;
      instance.on("node:click", (event) => { const id = event.target?.id; if (id) onSelect(id); });
      await instance.render(); if (disposed) return; setLoading(false); setRenderVersion((value) => value + 1);
      resizeObserver = new ResizeObserver((entries) => { const rect = entries[0]?.contentRect; if (rect?.width && rect.height) instance.resize(rect.width, rect.height); });
      resizeObserver.observe(containerRef.current);
    }).catch((reason: Error) => { if (!disposed) { setError(reason.message); setLoading(false); } });
    return () => { disposed = true; resizeObserver?.disconnect(); graphRef.current?.destroy(); graphRef.current = null; };
  }, [graph, mode, preview]);

  useEffect(() => {
    const instance = graphRef.current; if (!instance || !graph) return;
    const renderedEdges = buildData(graph).edges;
    const neighbors = new Set<string>(); const activeEdges = new Set<string>();
    renderedEdges.forEach((edge) => { if (edge.source === selectedId || edge.target === selectedId) { neighbors.add(edge.source); neighbors.add(edge.target); activeEdges.add(edge.id); } });
    const states: Record<string, string[]> = {};
    graph.nodes.forEach((node) => { states[node.id] = !selectedId ? [] : node.id === selectedId ? ["selected"] : neighbors.has(node.id) ? ["neighbor"] : ["inactive"]; });
    renderedEdges.forEach((edge) => { states[edge.id] = !selectedId ? [] : activeEdges.has(edge.id) ? ["active"] : ["inactive"]; });
    void instance.setElementState(states);
  }, [graph, selectedId, renderVersion]);

  return <div className="publish-ontology-canvas-shell">
    <div className="publish-ontology-canvas-toolbar">
      <div className="publish-ontology-legend"><span><i className="core" />核心对象</span><span><i className="context" />上下文对象</span><span><i className="reference" />参考对象</span></div>
      <Tooltip title="适应全部发布本体"><Button size="small" icon={<ArrowsAltOutlined />} onClick={() => void graphRef.current?.fitView()}>适应画布</Button></Tooltip>
    </div>
    <div ref={containerRef} className="publish-ontology-canvas" />
    {loading && <div className="publish-ontology-canvas-overlay"><Spin /><Typography.Text type="secondary">正在生成发布本体图…</Typography.Text></div>}
    {error && <div className="publish-ontology-canvas-overlay"><Typography.Text type="danger">{error}</Typography.Text></div>}
    <div className="publish-ontology-storage-badge"><Tag color={preview ? "gold" : "cyan"}>{preview ? "只读预览" : "工作区本体"}</Tag><span>{preview ? "虚线内容待确认后加入草稿" : "对象和关系来自 PostgreSQL 模型存储"}</span></div>
  </div>;
}
