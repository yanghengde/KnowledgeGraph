import { Spin,Typography } from "antd";
import { forwardRef,useEffect,useImperativeHandle,useRef,useState } from "react";
import type { SemanticGraphEdge,SemanticGraphNode,SemanticGraphOverview } from "../../../types";

declare global {
  interface Window {
    G6?: { Graph: new (options: Record<string, unknown>) => G6Graph };
    __semanticG6Promise?: Promise<void>;
  }
}

type GraphNodeData = SemanticGraphNode & { style: Record<string, unknown> };
type GraphEdgeData = SemanticGraphEdge & { id: string };
type GraphEvent = { target?: { id?: string }; client?: { x?: number; y?: number } };
type G6Graph = {
  render: () => Promise<void> | void; draw: () => Promise<void> | void; destroy: () => void;
  on: (event: string, handler: (event: GraphEvent) => void) => void;
  fitView: () => Promise<void> | void; focusElement: (id: string, animation?: boolean) => Promise<void> | void;
  setElementState: (states: Record<string, string[]>) => Promise<void> | void;
  setLayout: (layout: Record<string, unknown>) => void;
  setData: (data: { nodes: GraphNodeData[]; edges: GraphEdgeData[] }) => void;
  getNodeData: (id?: string) => GraphNodeData[] | GraphNodeData | undefined;
  getEdgeData: () => GraphEdgeData[];
  updateNodeData: (nodes: Array<{ id: string; style: Record<string, unknown> }>) => void;
  removeEdgeData: (ids: string[]) => void; addEdgeData: (edges: GraphEdgeData[]) => void;
  getCanvasByClient: (position: { x: number; y: number }) => { x: number; y: number };
  getElementPosition: (id: string) => [number, number]; resize: (width: number, height: number) => void;
};

export type SemanticG6Handle = {
  fitView: () => void; focusNode: (id: string) => void; setFollowedNodes: (ids: string[]) => void;
  setLayout: (layout: "preset" | "dagre-tb" | "dagre-lr" | "radial" | "force") => void;
  clearFocus: () => void;
};

type Props = {
  data?: SemanticGraphOverview; mode: "light" | "dark"; selectedNodeId?: string;
  followedNodeIds: string[]; onNodeSelect: (id: string | null) => void;
};
type IndexedGraph = {
  nodes: GraphNodeData[]; allEdges: GraphEdgeData[]; overviewEdges: GraphEdgeData[];
  nodeById: Map<string, SemanticGraphNode>;
  adjacency: Map<string, { neighbors: Set<string>; outgoing: GraphEdgeData[]; incoming: GraphEdgeData[] }>;
};

const CORE_NODE_IDS = new Set(["Workflow", "Product", "MfgOrder"]);
const MAX_OVERVIEW_EDGES = 360;
const baseColors: Record<string, { fill: string; stroke: string }> = {
  workflow: { fill: "#009999", stroke: "#00b8b8" }, operation: { fill: "#ff6600", stroke: "#ff8833" },
  spec: { fill: "#862996", stroke: "#a040b0" }, workcenter: { fill: "#2e86c1", stroke: "#5dade2" },
  factory: { fill: "#27ae60", stroke: "#52d68c" }, mfgline: { fill: "#00897b", stroke: "#4db6ac" },
  product: { fill: "#f39c12", stroke: "#f5b041" }, container: { fill: "#3498db", stroke: "#5dade2" },
  quality: { fill: "#e74c3c", stroke: "#ec7063" }, resource: { fill: "#c59f08", stroke: "#f7dc6f" },
  material: { fill: "#16a085", stroke: "#48c9b0" }, bom: { fill: "#673ab7", stroke: "#9575cd" },
  employee: { fill: "#e67e22", stroke: "#eb984e" }, role: { fill: "#37474f", stroke: "#78909c" },
  mfgorder: { fill: "#34495e", stroke: "#718596" }, organization: { fill: "#c62828", stroke: "#ef5350" },
  tool: { fill: "#795548", stroke: "#a1887f" }, document: { fill: "#607d8b", stroke: "#90a4ae" },
  other: { fill: "#52636a", stroke: "#82969e" },
};
const fallbackPalette = ["#007f86", "#4456a6", "#a4436c", "#5e7c32", "#8058a5", "#a75b32", "#23719b"];

function moduleColor(moduleName: string) {
  if (baseColors[moduleName]) return baseColors[moduleName];
  let hash = 0;
  for (const character of moduleName) hash = ((hash << 5) - hash + character.charCodeAt(0)) | 0;
  const fill = fallbackPalette[Math.abs(hash) % fallbackPalette.length];
  return { fill, stroke: fill };
}

function loadG6() {
  if (window.G6?.Graph) return Promise.resolve();
  if (!window.__semanticG6Promise) {
    window.__semanticG6Promise = new Promise<void>((resolve, reject) => {
      const existing = document.querySelector<HTMLScriptElement>('script[data-semantic-g6="true"]');
      if (existing) {
        existing.addEventListener("load", () => resolve(), { once: true });
        existing.addEventListener("error", () => reject(new Error("G6 图形引擎加载失败")), { once: true }); return;
      }
      const script = document.createElement("script");
      script.src = "/static/lib/g6.js"; script.async = true; script.dataset.semanticG6 = "true";
      script.onload = () => resolve(); script.onerror = () => reject(new Error("G6 图形引擎加载失败"));
      document.head.appendChild(script);
    });
  }
  return window.__semanticG6Promise;
}

function indexGraph(data: SemanticGraphOverview, followedIds: Set<string>): IndexedGraph {
  const nodeById = new Map(data.nodes.map((node) => [node.id, node]));
  const adjacency = new Map<string, { neighbors: Set<string>; outgoing: GraphEdgeData[]; incoming: GraphEdgeData[] }>();
  data.nodes.forEach((node) => adjacency.set(node.id, { neighbors: new Set(), outgoing: [], incoming: [] }));
  const allEdges = data.edges.map((edge, index) => ({ ...edge, id: edge.id || `semantic-edge-${index}` }));
  allEdges.forEach((edge) => {
    const source = adjacency.get(edge.source); const target = adjacency.get(edge.target);
    if (!source || !target) return;
    source.neighbors.add(edge.target); source.outgoing.push(edge);
    target.neighbors.add(edge.source); target.incoming.push(edge);
  });

  const ordered = [...data.nodes].sort((a, b) => {
    const rank = (node: SemanticGraphNode) => followedIds.has(node.id) ? 0 : CORE_NODE_IDS.has(node.id) ? 1 : 2;
    return rank(a) - rank(b) || (a.data.module || "other").localeCompare(b.data.module || "other") || a.id.localeCompare(b.id);
  });
  const followed = ordered.filter((node) => followedIds.has(node.id));
  const core = ordered.filter((node) => !followedIds.has(node.id) && CORE_NODE_IDS.has(node.id));
  const regular = ordered.filter((node) => !followedIds.has(node.id) && !CORE_NODE_IDS.has(node.id));
  const positions = new Map<string, { x: number; y: number }>();
  let anchor = followed.findIndex((node) => node.id === "Workflow");
  let anchorNode = anchor >= 0 ? followed.splice(anchor, 1)[0] : undefined;
  if (!anchorNode) { anchor = core.findIndex((node) => node.id === "Workflow"); anchorNode = anchor >= 0 ? core.splice(anchor, 1)[0] : undefined; }
  if (anchorNode) positions.set(anchorNode.id, { x: 0, y: 0 });
  const followedRadius = followed.length ? Math.max(145, followed.length * 115 / (2 * Math.PI)) : 0;
  followed.forEach((node, index) => {
    const angle = followed.length === 1 ? -Math.PI / 2 : index / followed.length * Math.PI * 2 - Math.PI / 2;
    positions.set(node.id, { x: Math.cos(angle) * followedRadius * 1.12, y: Math.sin(angle) * followedRadius });
  });
  const coreRadius = Math.max(followedRadius + 165, 270, core.length * 130 / (2 * Math.PI));
  core.forEach((node, index) => {
    const angle = index / Math.max(1, core.length) * Math.PI * 2;
    positions.set(node.id, { x: Math.cos(angle) * coreRadius * 1.2, y: Math.sin(angle) * coreRadius * .78 });
  });
  const goldenAngle = Math.PI * (3 - Math.sqrt(5)); const innerRadius = coreRadius + 110;
  regular.forEach((node, index) => {
    const radius = Math.sqrt(innerRadius * innerRadius + index * 34 * 34); const angle = index * goldenAngle;
    positions.set(node.id, { x: Math.cos(angle) * radius * 1.25, y: Math.sin(angle) * radius * .78 });
  });
  const nodes = data.nodes.map((node) => {
    const position = positions.get(node.id) || { x: 0, y: 0 }; const color = moduleColor(node.data.module || "other");
    return { ...node, style: { ...position, size: followedIds.has(node.id) || CORE_NODE_IDS.has(node.id) ? 76 : 52, fill: color.fill, stroke: color.stroke, shadowColor: color.fill, opacity: 1, labelOpacity: 1, iconOpacity: 1 } };
  });

  const uniquePairs = new Map<string, GraphEdgeData>();
  allEdges.forEach((edge) => {
    const key = edge.source < edge.target ? `${edge.source}\0${edge.target}` : `${edge.target}\0${edge.source}`;
    if (!uniquePairs.has(key)) uniquePairs.set(key, edge);
  });
  const score = (edge: GraphEdgeData) => {
    const coreScore = (CORE_NODE_IDS.has(edge.source) ? 1 : 0) + (CORE_NODE_IDS.has(edge.target) ? 1 : 0);
    const followedScore = (followedIds.has(edge.source) ? 1 : 0) + (followedIds.has(edge.target) ? 1 : 0);
    return followedScore * 20000 + coreScore * 10000 + (adjacency.get(edge.source)?.neighbors.size || 0) + (adjacency.get(edge.target)?.neighbors.size || 0);
  };
  const scored = [...uniquePairs.values()].sort((a, b) => score(b) - score(a) || a.source.localeCompare(b.source) || a.target.localeCompare(b.target));
  const overviewEdges: GraphEdgeData[] = []; const selectedIds = new Set<string>(); const covered = new Set<string>();
  const add = (edge: GraphEdgeData) => {
    if (overviewEdges.length >= MAX_OVERVIEW_EDGES || selectedIds.has(edge.id)) return;
    overviewEdges.push(edge); selectedIds.add(edge.id); covered.add(edge.source); covered.add(edge.target);
  };
  scored.forEach((edge) => { if (!covered.has(edge.source) || !covered.has(edge.target)) add(edge); }); scored.forEach(add);
  return { nodes, allEdges, overviewEdges, nodeById, adjacency };
}

function incidentEdges(indexed: IndexedGraph, nodeId: string) {
  const entry = indexed.adjacency.get(nodeId); const groups = new Map<string, GraphEdgeData[]>();
  [...(entry?.outgoing || []), ...(entry?.incoming || [])].forEach((edge) => {
    const neighbor = edge.source === nodeId ? edge.target : edge.source;
    groups.set(neighbor, [...(groups.get(neighbor) || []), edge]);
  });
  return [...groups.entries()].sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0])).map(([neighbor, edges]) => edges.length === 1 ? edges[0] : {
    ...edges[0], data: { ...edges[0].data, label: `${edges[0].data.label || "关系"} (+${edges.length - 1})`, description: `${nodeId} 与 ${neighbor} 之间共 ${edges.length} 条关系。` },
  });
}

export const SourceModelGraph = forwardRef<SemanticG6Handle, Props>(function SourceModelGraph(
  { data, mode, selectedNodeId, followedNodeIds, onNodeSelect }, ref,
) {
  const containerRef = useRef<HTMLDivElement>(null); const tooltipRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<G6Graph | null>(null); const indexedRef = useRef<IndexedGraph | null>(null);
  const overviewRef = useRef<SemanticGraphOverview | undefined>(data); const selectedRef = useRef<string | undefined>(selectedNodeId);
  const followedRef = useRef(new Set(followedNodeIds)); const onNodeSelectRef = useRef(onNodeSelect);
  const mutationRevisionRef = useRef(0); const mutationChainRef = useRef(Promise.resolve());
  const stateRevisionRef = useRef(0); const stateChainRef = useRef(Promise.resolve());
  const previousStatesRef = useRef<Record<string, string[]>>({});
  const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  selectedRef.current = selectedNodeId; onNodeSelectRef.current = onNodeSelect;

  const hideTooltip = () => tooltipRef.current?.classList.remove("visible");
  const showTooltip = (event: GraphEvent) => {
    const graph = graphRef.current; const tooltip = tooltipRef.current; const nodeId = event.target?.id;
    const clientX = event.client?.x; const clientY = event.client?.y;
    if (!graph || !tooltip || !nodeId || !Number.isFinite(clientX) || !Number.isFinite(clientY)) return hideTooltip();
    const raw = graph.getNodeData(nodeId) as GraphNodeData | undefined;
    if (!raw?.data) return hideTooltip();
    const canvas = graph.getCanvasByClient({ x: clientX!, y: clientY! }); const position = graph.getElementPosition(nodeId);
    const radius = Number(raw.style?.size || 52) / 2;
    if (Math.hypot(canvas.x - position[0], canvas.y - position[1]) > radius + 6) return hideTooltip();
    const node = indexedRef.current?.nodeById.get(nodeId) || raw;
    const setText = (selector: string, value: string) => { const element = tooltip.querySelector<HTMLElement>(selector); if (element) element.textContent = value; };
    setText("[data-tooltip-title]", node.data.chineseName || node.data.label || nodeId);
    setText("[data-tooltip-subtitle]", nodeId);
    setText("[data-tooltip-description]", node.data.description || "暂无业务说明");
    setText("[data-tooltip-meta]", `${node.data.propertyCount || 0} 个属性 · ${node.data.module || "other"}`);
    const rect = containerRef.current?.getBoundingClientRect(); if (!rect) return;
    tooltip.style.left = `${Math.max(12, Math.min(clientX! - rect.left + 16, rect.width - 306))}px`;
    tooltip.style.top = `${Math.max(12, Math.min(clientY! - rect.top - 10, rect.height - 150))}px`; tooltip.classList.add("visible");
  };

  const applyStates = (requested: Record<string, string[]>, force = false) => {
    const revision = ++stateRevisionRef.current;
    stateChainRef.current = stateChainRef.current.catch(() => undefined).then(async () => {
      const graph = graphRef.current; if (!graph || revision !== stateRevisionRef.current) return;
      const validIds = new Set([...(((graph.getNodeData() as GraphNodeData[]) || []).map((item) => item.id)), ...graph.getEdgeData().map((item) => item.id)]);
      const diff: Record<string, string[]> = {}; const ids = new Set([...Object.keys(previousStatesRef.current), ...Object.keys(requested)]);
      ids.forEach((id) => {
        if (!validIds.has(id)) return; const before = previousStatesRef.current[id] || []; const after = requested[id] || [];
        if (force || before.length !== after.length || before.some((value, index) => value !== after[index])) diff[id] = after;
      });
      if (Object.keys(diff).length) await graph.setElementState(diff);
      previousStatesRef.current = Object.fromEntries(Object.entries(requested).filter(([id]) => validIds.has(id)));
    });
    return stateChainRef.current;
  };

  const setBackdrop = (focusedId?: string, neighbors = new Set<string>()) => {
    const graph = graphRef.current; if (!graph) return;
    graph.updateNodeData(((graph.getNodeData() as GraphNodeData[]) || []).map((node) => {
      const visible = !focusedId || node.id === focusedId || neighbors.has(node.id);
      return { id: node.id, style: { ...node.style, opacity: visible ? 1 : .12, labelOpacity: visible ? 1 : .05, iconOpacity: visible ? 1 : .16 } };
    }));
  };

  const replaceEdges = (edges: GraphEdgeData[], focusId?: string) => {
    const revision = ++mutationRevisionRef.current;
    mutationChainRef.current = mutationChainRef.current.catch(() => undefined).then(async () => {
      const graph = graphRef.current; if (!graph || revision !== mutationRevisionRef.current) return;
      await applyStates({}); if (revision !== mutationRevisionRef.current) return;
      const currentIds = graph.getEdgeData().map((edge) => edge.id);
      if (currentIds.length) { graph.removeEdgeData(currentIds); await graph.draw(); }
      if (revision !== mutationRevisionRef.current) return;
      if (edges.length) graph.addEdgeData(edges); await graph.draw();
      if (revision !== mutationRevisionRef.current) return;
      if (!focusId) { setBackdrop(); await applyStates({}, true); return; }
      const neighbors = new Set<string>(); const states: Record<string, string[]> = { [focusId]: ["selected"] };
      edges.forEach((edge) => {
        if (edge.source === focusId) { neighbors.add(edge.target); states[edge.target] = ["active"]; states[edge.id] = ["activeOut"]; }
        else { neighbors.add(edge.source); states[edge.source] = ["active"]; states[edge.id] = ["activeIn"]; }
      });
      setBackdrop(focusId, neighbors); await applyStates(states, true);
    });
    return mutationChainRef.current;
  };

  const clearFocus = () => { const indexed = indexedRef.current; if (indexed) void replaceEdges(indexed.overviewEdges); };
  const selectNeighborhood = (id: string, locate = false) => {
    const indexed = indexedRef.current; const graph = graphRef.current;
    if (!indexed || !graph || !indexed.nodeById.has(id)) return;
    void replaceEdges(incidentEdges(indexed, id), id); if (locate) void graph.focusElement(id, true);
  };
  const updateFollowedNodes = (ids: string[]) => {
    if (!overviewRef.current || !graphRef.current) return;
    followedRef.current = new Set(ids); const indexed = indexGraph(overviewRef.current, followedRef.current); indexedRef.current = indexed;
    graphRef.current.setLayout({ type: "preset" });
    graphRef.current.updateNodeData(indexed.nodes.map((node) => ({ id: node.id, style: node.style })));
    void Promise.resolve(graphRef.current.draw()).then(() => { if (selectedRef.current) selectNeighborhood(selectedRef.current); });
  };

  useImperativeHandle(ref, () => ({
    fitView: () => { void graphRef.current?.fitView(); }, focusNode: (id) => selectNeighborhood(id, true), clearFocus,
    setFollowedNodes: updateFollowedNodes,
    setLayout: (layout) => {
      const graph = graphRef.current; const indexed = indexedRef.current; if (!graph || !indexed) return;
      const layouts: Record<string, Record<string, unknown>> = {
        preset: { type: "preset" }, "dagre-tb": { type: "dagre", rankdir: "TB", nodesep: 50, ranksep: 80 },
        "dagre-lr": { type: "dagre", rankdir: "LR", nodesep: 40, ranksep: 100 },
        radial: { type: "radial", unitRadius: 200, preventOverlap: true, nodeSize: 80, nodeSpacing: 50, focusNode: selectedRef.current || "Workflow", strictRadial: false },
        force: { type: "force", preventOverlap: true, nodeSize: 68, linkDistance: 160, nodeStrength: -400, edgeStrength: .3, collideStrength: .8, alphaDecay: .03, animation: false },
      };
      graph.setLayout(layouts[layout]); graph.setData({ nodes: indexed.nodes, edges: indexed.overviewEdges });
      previousStatesRef.current = {}; setBackdrop(); void graph.render();
    },
  }));

  useEffect(() => { overviewRef.current = data; }, [data]);
  useEffect(() => {
    if (!data || !containerRef.current) return;
    let disposed = false; let resizeObserver: ResizeObserver | undefined; setLoading(true); setError("");
    void loadG6().then(async () => {
      if (disposed || !containerRef.current || !window.G6?.Graph) return;
      graphRef.current?.destroy(); const indexed = indexGraph(data, followedRef.current); indexedRef.current = indexed;
      const labelFill = mode === "light" ? "#24404a" : "#e8f0f2";
      const edgeStroke = mode === "light" ? "rgba(0,95,120,.22)" : "rgba(40,215,181,.20)";
      const graph = new window.G6.Graph({
        container: containerRef.current, width: containerRef.current.clientWidth, height: containerRef.current.clientHeight,
        autoFit: "view", padding: [56, 56, 56, 56], culling: false, animation: false,
        data: { nodes: indexed.nodes, edges: indexed.overviewEdges },
        node: { type: "circle", style: {
          size: (datum: GraphNodeData) => datum.style?.size || 52, fill: (datum: GraphNodeData) => datum.style?.fill || "#52636a",
          stroke: (datum: GraphNodeData) => datum.style?.stroke || "#82969e", lineWidth: 2,
          labelText: (datum: GraphNodeData) => datum.data?.chineseName || datum.data?.label || datum.id,
          labelFill, labelFontSize: 10, labelFontWeight: 600, labelPlacement: "bottom", labelOffsetY: 7,
          iconText: (datum: GraphNodeData) => datum.id.substring(0, 2), iconFontSize: 12, iconFontWeight: 800, iconFill: "#ffffff",
          cursor: "pointer", ports: [{ placement: "center" }],
        }, state: {
          selected: { stroke: "#ffffff", lineWidth: 4, shadowColor: "#00bfa5", shadowBlur: 16, opacity: 1, labelOpacity: 1, zIndex: 30 },
          active: { stroke: "#00bfa5", lineWidth: 3, opacity: 1, labelOpacity: 1, zIndex: 20 },
        } },
        edge: { type: "line", style: {
          stroke: edgeStroke, lineWidth: 1, endArrow: false, labelText: (datum: GraphEdgeData) => datum.data?.label || "",
          labelFill, labelFontSize: 9, labelBackground: true, labelBackgroundFill: mode === "light" ? "rgba(255,255,255,.92)" : "rgba(6,19,27,.9)",
          labelPadding: [2, 4], labelOpacity: 0, cursor: "pointer",
        }, state: {
          activeOut: { stroke: "#20b895", lineWidth: 2.4, endArrow: true, opacity: 1, labelOpacity: 1, zIndex: 15 },
          activeIn: { stroke: "#df6c91", lineWidth: 2.4, endArrow: true, opacity: 1, labelOpacity: 1, zIndex: 15 },
        } }, behaviors: ["drag-canvas", "zoom-canvas", { type: "drag-element", state: null }],
      });
      graphRef.current = graph;
      graph.on("node:click", (event) => {
        hideTooltip(); const id = event.target?.id; if (!id) return;
        if (selectedRef.current === id) { selectedRef.current = undefined; onNodeSelectRef.current(null); clearFocus(); return; }
        selectedRef.current = id; onNodeSelectRef.current(id); selectNeighborhood(id);
      });
      graph.on("node:pointerenter", showTooltip); graph.on("node:pointermove", showTooltip); graph.on("node:pointerleave", hideTooltip);
      graph.on("canvas:click", () => { hideTooltip(); selectedRef.current = undefined; onNodeSelectRef.current(null); clearFocus(); });
      await graph.render(); if (disposed) return; setLoading(false);
      resizeObserver = new ResizeObserver((entries) => {
        const rect = entries[0]?.contentRect; if (rect && rect.width > 0 && rect.height > 0) graph.resize(rect.width, rect.height);
      });
      resizeObserver.observe(containerRef.current);
      if (selectedRef.current && data.nodes.some((node) => node.id === selectedRef.current)) selectNeighborhood(selectedRef.current);
    }).catch((reason: Error) => { if (!disposed) { setError(reason.message); setLoading(false); } });
    return () => {
      disposed = true; resizeObserver?.disconnect(); mutationRevisionRef.current += 1; stateRevisionRef.current += 1;
      graphRef.current?.destroy(); graphRef.current = null;
    };
  }, [data, mode]);

  useEffect(() => {
    if (selectedNodeId && data?.nodes.some((node) => node.id === selectedNodeId)) selectNeighborhood(selectedNodeId);
    else if (!selectedNodeId && graphRef.current) clearFocus();
  }, [selectedNodeId]);

  return <div className="semantic-canvas-shell">
    <div ref={containerRef} className="semantic-g6-canvas" />
    <div ref={tooltipRef} className="semantic-node-tooltip" aria-hidden="true">
      <strong data-tooltip-title /><span data-tooltip-subtitle /><p data-tooltip-description /><small data-tooltip-meta />
    </div>
    <div className="semantic-canvas-help"><span>滚轮缩放</span><span>拖动画布</span><span>点击查看一跳关系</span><span>再次点击恢复总览</span></div>
    {loading && <div className="semantic-canvas-overlay"><Spin /><Typography.Text type="secondary">正在构建完整制造语义图谱…</Typography.Text></div>}
    {error && <div className="semantic-canvas-overlay error"><Typography.Text type="danger">{error}</Typography.Text></div>}
  </div>;
});
