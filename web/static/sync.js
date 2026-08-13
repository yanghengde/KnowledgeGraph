(() => {
    "use strict";

    const state = {
        navigation: [],
        overview: null,
        connections: [],
        jobs: [],
        tablePolicies: [],
        incrementalProbe: null,
        profiles: [],
        ontologyGovernance: { workspaces: [], graph: { nodes: [], edges: [], properties: [] }, releases: [] },
        ontologySourceCandidates: [],
        ontologyValidation: null,
        selectedOntologyClassUid: null,
        ontologyPropertyFilter: "",
        ontologyGovernanceStage: "discover",
        ontologyDiscoveryCandidates: [],
        ontologyDiscoverySourceGraph: { nodes: [], edges: [] },
        ontologyDiscoverySelected: [],
        ontologyDiscoveryPlan: null,
        ontologyDiscoveryNodePolicies: {},
        ontologyDiscoveryJoinUsage: {},
        ontologyDiscoveryJoinNames: {},
        ontologyDiscoveryLoading: false,
        ontologyDiscoverySearchTerm: "",
        ontologyDiscoveryFocused: false,
        activeProfile: null,
        profileCandidates: { classes: [], relationships: [] },
        closurePlan: null,
        governance: { contracts: [], relationships: [], latestRun: null, qualityResults: [] },
        contractSchema: null,
        schemaChanges: [],
        attributeProjections: [],
        materialization: { plan: null, releases: [] },
        deployments: { environments: [], deployments: [], activeCuratedRelease: null },
        observability: { latestRun: null, metrics: [], alerts: [], lineage: [] },
        actions: { definitions: [], invocations: [], applyEnabled: false },
        mappings: null,
        runs: [],
        settings: [],
        dialogSubmit: null,
    };
    let ontologyGovernanceGraph = null;
    let ontologyDiscoveryGraph = null;

    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
    const escapeHtml = (value) => String(value ?? "")
        .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;").replaceAll("'", "&#039;");

    async function request(url, options = {}) {
        const response = await fetch(url, {
            headers: { "Content-Type": "application/json", ...(options.headers || {}) },
            ...options,
        });
        let payload = null;
        try { payload = await response.json(); } catch (_) { payload = {}; }
        if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
        return payload;
    }

    function toast(message, error = false) {
        const element = $("#toast");
        element.textContent = message;
        element.classList.toggle("error", error);
        element.hidden = false;
        window.clearTimeout(toast.timer);
        toast.timer = window.setTimeout(() => { element.hidden = true; }, 4200);
    }

    function setAlert(message = "") {
        const element = $("#pageAlert");
        element.textContent = message;
        element.hidden = !message;
    }

    function iconCode(icon) {
        return ({ dashboard: "OV", plug: "CN", schedule: "JB", ontology: "OG", profile: "BG", projection: "PX", database: "DB", rocket: "DP", pulse: "HL", action: "AC", mapping: "MP", history: "RN", settings: "ST" })[icon] || "•";
    }

    function formatDate(value, compact = false) {
        if (!value) return "—";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return String(value);
        return new Intl.DateTimeFormat("zh-CN", compact
            ? { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }
            : { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" }
        ).format(date);
    }

    function duration(start, end) {
        if (!start) return "—";
        const milliseconds = (end ? new Date(end) : new Date()) - new Date(start);
        if (!Number.isFinite(milliseconds) || milliseconds < 0) return "—";
        if (milliseconds < 1000) return `${milliseconds} ms`;
        if (milliseconds < 60000) return `${(milliseconds / 1000).toFixed(1)} s`;
        return `${(milliseconds / 60000).toFixed(1)} min`;
    }

    function statusLabel(value) {
        return ({ online: "在线", offline: "离线", degraded: "降级", unknown: "未检查", disabled: "已停用", succeeded: "成功", failed: "失败", queued: "排队", started: "运行中", extracting: "抽取中", staged: "已暂存", loading: "加载中", verifying: "验证中", cancelled: "已取消", planned: "已规划", ready: "待激活", active: "活动", draft: "草案", reviewed: "已复核", retired: "已退役", superseded: "已替代", rolled_back: "已回滚", approved: "已批准", pending_approval: "待审批", executing: "执行中", compensating: "补偿中", compensated: "已补偿", rejected: "已拒绝", healthy: "健康", unhealthy: "异常", warning: "警告", critical: "严重", open: "未处理", acknowledged: "已确认", resolved: "已恢复" })[value] || value || "未知";
    }

    function connectionKindLabel(value) {
        return ({
            camstar_sqlserver: "Camstar · SQL Server",
            camstar_oracle: "Camstar · Oracle",
            ontology_neo4j: "Ontology · Neo4j",
            publish_ontology_neo4j: "Publish Ontology · Neo4j",
            graph_studio: "Graph Studio",
            state_postgresql: "Control Plane · PostgreSQL",
        })[value] || String(value || "").replaceAll("_", " ");
    }

    function strategyLabel(value) {
        return ({
            snapshot: "全量快照",
            watermark: "水位增量",
            append_only: "追加增量",
            cdc: "CDC",
            excluded: "不导入",
        })[value] || "待配置";
    }

    function roleLabel(value) {
        return ({ core: "核心对象", context: "上下文对象", reference: "参考对象", on_demand: "按需对象", excluded: "不导入" })[value] || value;
    }

    function orphanLabel(value) {
        return ({ reject: "拒绝发布", quarantine: "隔离等待", allow: "允许孤立", referenced_only: "被引用时导入" })[value] || value;
    }

    function strengthLabel(value) {
        return ({ core: "核心关联", context: "上下文关联", weak: "弱关联", on_demand: "按需关联" })[value] || value;
    }

    function renderNavigation() {
        const nav = $("#syncNavigation");
        nav.innerHTML = state.navigation.map(item => `
            <a class="nav-item" href="${escapeHtml(item.route)}" data-section-key="${escapeHtml(item.menu_key)}" title="${escapeHtml(item.label_zh)}">
                <span class="nav-icon">${iconCode(item.icon)}</span>
                <span class="nav-label">${escapeHtml(item.label_zh)}</span>
            </a>`).join("");
        setActiveSection(location.hash.slice(1) || "overview");
    }

    function setActiveSection(key) {
        const available = state.navigation.some(item => item.menu_key === key);
        const selected = available ? key : "overview";
        $$(".page-section").forEach(section => section.classList.toggle("active", section.dataset.section === selected));
        $$(".nav-item").forEach(item => item.classList.toggle("active", item.dataset.sectionKey === selected));
        if (location.hash !== `#${selected}`) history.replaceState(null, "", `#${selected}`);
    }

    function renderOverview() {
        const data = state.overview || { summary: {}, connections: [], jobs: [], recentRuns: [] };
        const summary = data.summary || {};
        $("#metricConnections").textContent = `${summary.online_connections || 0}/${summary.enabled_connections || 0}`;
        $("#metricJobs").textContent = summary.enabled_jobs || 0;
        const mappingSnapshot = state.mappings?.catalog?.snapshot;
        $("#metricCoverage").textContent = mappingSnapshot ? `${Number(mappingSnapshot.mapping_coverage).toFixed(2)}%` : "—";
        $("#metricLastSuccess").textContent = summary.last_success_at ? formatDate(summary.last_success_at, true) : "尚无运行";
        const graph = data.connections.find(item => item.connection_key === "graph-studio");
        $("#graphmartStatus").textContent = graph?.status === "online" ? "Graphmart 在线" : `连接${statusLabel(graph?.status)}`;

        const healthy = summary.enabled_connections > 0 && summary.online_connections === summary.enabled_connections;
        $("#globalStatusDot").className = `status-dot ${healthy ? "online" : "unknown"}`;
        $("#globalStatusText").textContent = healthy ? "数据链路全部在线" : `${summary.online_connections || 0}/${summary.enabled_connections || 0} 连接在线`;

        const connectionContainer = $("#overviewConnections");
        connectionContainer.classList.remove("loading-list");
        connectionContainer.innerHTML = data.connections.map(item => `
            <div class="compact-row"><div><strong>${escapeHtml(item.display_name)}</strong><small>${escapeHtml(item.endpoint)}</small></div><span class="status-pill ${item.status}">${statusLabel(item.status)}</span></div>
        `).join("") || '<div class="compact-row"><small>暂无连接配置</small></div>';

        const runContainer = $("#overviewRuns");
        runContainer.classList.remove("loading-list");
        runContainer.innerHTML = data.recentRuns.map(item => `
            <div class="compact-row"><div><strong>${escapeHtml(item.job_name)}</strong><small>${formatDate(item.started_at, true)} · ${Number(item.row_count || 0).toLocaleString()} 行</small></div><span class="status-pill ${item.status}">${statusLabel(item.status)}</span></div>
        `).join("") || '<div class="compact-row"><div><strong>尚无运行记录</strong><small>完成首次 dry-run 后会显示在这里</small></div><span class="status-pill unknown">待运行</span></div>';
    }

    function ontologyRoleColor(role) {
        return ({ core: "#00b89c", context: "#2f86c9", reference: "#8b6fc5", on_demand: "#d99038", excluded: "#566b73" })[role] || "#2f86c9";
    }

    function ontologyDiscoveryDialect() {
        return state.connections.some(item => item.enabled && item.kind === "camstar_oracle") ? "oracle" : "sqlserver";
    }

    function ontologyDiscoveryJoinKey(join) {
        return [join.from_table, join.from_field, join.to_table, join.to_field].join("|");
    }

    function ontologyDiscoveryEffectiveJoin(join) {
        const key = ontologyDiscoveryJoinKey(join);
        const selectedName = state.ontologyDiscoveryJoinNames[key] || join.recommended_name;
        const semantic = (join.semantic_candidates || []).find(item => item.name === selectedName);
        return {
            name: selectedName,
            source: semantic?.source || join.recommended_source || join.from_table,
            target: semantic?.target || join.recommended_target || join.to_table,
            cardinality: semantic?.cardinality || join.cardinality || "many-to-one",
            semantic: Boolean(semantic),
        };
    }

    function ontologyDiscoveryExistingClass(className) {
        return (state.ontologyGovernance.graph?.nodes || []).find(node => node.data?.sourceClass === className);
    }

    function ontologyDiscoveryNodePolicy(node) {
        if (state.ontologyDiscoveryNodePolicies[node.id]) return state.ontologyDiscoveryNodePolicies[node.id];
        const existing = ontologyDiscoveryExistingClass(node.id);
        if (existing) return existing.data?.role || "context";
        if (node.bridge && !node.selected) return "path_only";
        const hasCore = Object.values(state.ontologyDiscoveryNodePolicies).includes("core")
            || (state.ontologyGovernance.graph?.nodes || []).some(item => item.data?.role === "core");
        return hasCore ? "context" : "core";
    }

    function ontologyDiscoveryJoinDefault(join) {
        const effective = ontologyDiscoveryEffectiveJoin(join);
        const source = (state.ontologyDiscoveryPlan?.nodes || []).find(item => item.id === effective.source);
        const target = (state.ontologyDiscoveryPlan?.nodes || []).find(item => item.id === effective.target);
        const sourcePolicy = source ? ontologyDiscoveryNodePolicy(source) : "path_only";
        const targetPolicy = target ? ontologyDiscoveryNodePolicy(target) : "path_only";
        return [sourcePolicy, targetPolicy].some(value => ["path_only", "excluded"].includes(value))
            ? "excluded"
            : (join.semantic_candidates || []).length ? "published_link" : "context_only";
    }

    function renderOntologyDiscoveryCandidates() {
        const graph = state.ontologyGovernance.graph || { nodes: [] };
        const selected = new Set(state.ontologyDiscoverySelected);
        const container = $("#ontologyDiscoveryCandidates");
        if (!container) return;
        $("#ontologyDiscoveryCatalogCount").textContent = `${state.ontologyDiscoveryCandidates.length} 个`;
        container.innerHTML = state.ontologyDiscoveryCandidates.map(item => {
            const existing = graph.nodes.some(node => node.data?.sourceClass === item.className);
            const isSelected = selected.has(item.className);
            const stateText = isSelected ? "已选入候选范围" : existing ? "已在发布草案" : "";
            return `<div class="ontology-source-item ${isSelected ? "selected" : ""} ${existing ? "existing" : ""}"><div><strong>${escapeHtml(item.className)}</strong><small>${escapeHtml(item.chineseName || item.layer || "")} · ${item.propertyCount} 属性</small>${stateText ? `<span class="source-state">${stateText}</span>` : ""}</div><button class="mini-btn" data-action="toggle-ontology-discovery" data-source-class="${escapeHtml(item.className)}">${isSelected ? "移除" : "选择"}</button></div>`;
        }).join("") || '<div class="ontology-discovery-empty">没有匹配的源本体对象</div>';
    }

    function ontologyDiscoveryModuleColor(module) {
        const palette = ["#167d96", "#356cb0", "#6f5aae", "#9b6a34", "#287d69", "#8d4f61", "#4f7783"];
        const key = String(module || "other");
        let hash = 0;
        for (let index = 0; index < key.length; index += 1) hash = ((hash << 5) - hash + key.charCodeAt(index)) | 0;
        return palette[Math.abs(hash) % palette.length];
    }

    async function renderOntologyDiscoveryGraph() {
        const container = $("#ontologyDiscoveryGraph");
        if (!container || !window.G6) return;
        if (ontologyDiscoveryGraph) {
            ontologyDiscoveryGraph.destroy();
            ontologyDiscoveryGraph = null;
        }
        const sourceGraph = state.ontologyDiscoverySourceGraph || { nodes: [], edges: [] };
        if (!sourceGraph.nodes.length) {
            container.innerHTML = '<div class="ontology-discovery-empty">正在读取完整源本体图谱…</div>';
            return;
        }
        const plan = state.ontologyDiscoveryPlan || { nodes: [], joins: [] };
        const selected = new Set(state.ontologyDiscoverySelected);
        const planNodes = new Map(plan.nodes.map(item => [item.id, item]));
        const active = state.ontologyDiscoverySelected.at(-1) || null;
        const search = state.ontologyDiscoverySearchTerm.trim().toLowerCase();
        const adjacency = new Map(sourceGraph.nodes.map(node => [node.id, new Set()]));
        const degree = new Map(sourceGraph.nodes.map(node => [node.id, 0]));
        sourceGraph.edges.forEach(edge => {
            adjacency.get(edge.source)?.add(edge.target);
            adjacency.get(edge.target)?.add(edge.source);
            degree.set(edge.source, (degree.get(edge.source) || 0) + 1);
            degree.set(edge.target, (degree.get(edge.target) || 0) + 1);
        });
        const related = new Set();
        selected.forEach(id => adjacency.get(id)?.forEach(neighbor => related.add(neighbor)));
        const visibleIds = new Set(sourceGraph.nodes.map(node => node.id));
        if (state.ontologyDiscoveryFocused && selected.size) {
            visibleIds.clear();
            selected.forEach(id => visibleIds.add(id));
            planNodes.forEach((_value, id) => visibleIds.add(id));
            related.forEach(id => visibleIds.add(id));
        }
        const visibleNodes = sourceGraph.nodes.filter(node => visibleIds.has(node.id));
        const orderedNodes = [...visibleNodes].sort((left, right) => {
            const rank = node => selected.has(node.id) ? 0 : planNodes.has(node.id) ? 1 : related.has(node.id) ? 2 : 3;
            return rank(left) - rank(right) || (degree.get(right.id) || 0) - (degree.get(left.id) || 0) || left.id.localeCompare(right.id);
        });
        const goldenAngle = Math.PI * (3 - Math.sqrt(5));
        const positions = new Map();
        const selectedNodes = orderedNodes.filter(node => selected.has(node.id));
        const anchorNodes = selectedNodes.length ? selectedNodes : orderedNodes.filter(node => node.id === "Workflow").slice(0, 1);
        anchorNodes.forEach((node, index) => {
            const angle = anchorNodes.length === 1 ? 0 : index / anchorNodes.length * Math.PI * 2;
            const radius = anchorNodes.length <= 1 ? 0 : Math.max(95, anchorNodes.length * 32);
            positions.set(node.id, { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius });
        });
        const anchorIds = new Set(anchorNodes.map(node => node.id));
        const otherNodes = orderedNodes.filter(node => !anchorIds.has(node.id));
        const innerRadius = 155;
        otherNodes.forEach((node, index) => {
            const radius = Math.sqrt(innerRadius * innerRadius + index * 31 * 31);
            const angle = index * goldenAngle;
            positions.set(node.id, { x: Math.cos(angle) * radius * 1.18, y: Math.sin(angle) * radius * .82 });
        });
        const rawPositions = [...positions.values()];
        const minX = Math.min(...rawPositions.map(item => item.x));
        const maxX = Math.max(...rawPositions.map(item => item.x));
        const minY = Math.min(...rawPositions.map(item => item.y));
        const maxY = Math.max(...rawPositions.map(item => item.y));
        const usableWidth = Math.max(200, container.clientWidth - 90);
        const usableHeight = Math.max(200, container.clientHeight - 90);
        const positionScale = Math.min(usableWidth / Math.max(1, maxX - minX), usableHeight / Math.max(1, maxY - minY));
        positions.forEach((position, id) => positions.set(id, {
            x: (position.x - (minX + maxX) / 2) * positionScale + container.clientWidth / 2,
            y: (position.y - (minY + maxY) / 2) * positionScale + container.clientHeight / 2,
        }));
        const existing = new Set((state.ontologyGovernance.graph?.nodes || []).map(item => item.data?.sourceClass).filter(Boolean));
        const graphNodes = visibleNodes.map(node => {
            const text = `${node.id} ${node.data?.chineseName || ""}`.toLowerCase();
            const searchMatch = Boolean(search && text.includes(search));
            const position = positions.get(node.id);
            return {
                id: node.id,
                style: { x: position?.x, y: position?.y },
                data: {
                    ...node.data,
                    selected: selected.has(node.id),
                    bridge: Boolean(planNodes.get(node.id)?.bridge && !selected.has(node.id)),
                    unconnected: Boolean(planNodes.get(node.id)?.unconnected),
                    related: related.has(node.id),
                    existing: existing.has(node.id),
                    searchMatch,
                    faded: Boolean(selected.size && !selected.has(node.id) && !planNodes.has(node.id) && !related.has(node.id)),
                },
            };
        });
        const effectivePlanEdges = plan.joins.map((join, index) => {
            const effective = ontologyDiscoveryEffectiveJoin(join);
            return { id: `physical-plan-${index}`, source: effective.source, target: effective.target, name: effective.name, semantic: effective.semantic };
        });
        const planEdgeKeys = new Set(effectivePlanEdges.map(edge => `${edge.source}|${edge.target}|${edge.name}`));
        const visibleSourceEdges = sourceGraph.edges.filter(edge => visibleIds.has(edge.source) && visibleIds.has(edge.target));
        const scoredEdges = visibleSourceEdges.sort((left, right) => {
            const score = edge => (selected.has(edge.source) || selected.has(edge.target) ? 10000 : 0) + (planNodes.has(edge.source) || planNodes.has(edge.target) ? 5000 : 0) + (degree.get(edge.source) || 0) + (degree.get(edge.target) || 0);
            return score(right) - score(left);
        });
        const edgeLimit = state.ontologyDiscoveryFocused ? 500 : selected.size ? 300 : 220;
        const graphEdges = scoredEdges.slice(0, edgeLimit).map((edge, index) => {
            const name = edge.data?.label || "";
            const isPlan = planEdgeKeys.has(`${edge.source}|${edge.target}|${name}`);
            return { id: `source-edge-${index}`, source: edge.source, target: edge.target, data: { name, plan: isPlan, semantic: true, faded: Boolean(selected.size && !isPlan && !selected.has(edge.source) && !selected.has(edge.target)) } };
        });
        const renderedPlanKeys = new Set(graphEdges.filter(edge => edge.data.plan).map(edge => `${edge.source}|${edge.target}|${edge.data.name}`));
        effectivePlanEdges.forEach(edge => {
            const key = `${edge.source}|${edge.target}|${edge.name}`;
            if (!renderedPlanKeys.has(key) && visibleIds.has(edge.source) && visibleIds.has(edge.target)) {
                graphEdges.push({ id: edge.id, source: edge.source, target: edge.target, data: { name: edge.name, plan: true, semantic: edge.semantic, faded: false } });
            }
        });
        container.innerHTML = "";
        ontologyDiscoveryGraph = new G6.Graph({
            container,
            width: container.clientWidth,
            height: container.clientHeight,
            autoFit: false,
            padding: [55, 65, 65, 65],
            culling: false,
            animation: false,
            behaviors: ["drag-element", "drag-canvas", "zoom-canvas"],
            node: { type: "circle", style: {
                size: d => d.data?.selected ? 50 : d.data?.bridge ? 36 : d.data?.related || d.data?.searchMatch ? 30 : 24,
                fill: d => d.data?.unconnected ? "#b64754" : d.data?.selected ? "#00ad94" : d.data?.bridge ? "#287fba" : d.data?.existing ? "#8061bd" : ontologyDiscoveryModuleColor(d.data?.module),
                stroke: d => d.data?.selected ? "#42f0cb" : d.data?.searchMatch ? "#f2b84b" : d.data?.related ? "#42cdb1" : "rgba(116,166,178,.65)",
                lineWidth: d => d.data?.selected ? 4 : d.data?.searchMatch || d.data?.related ? 2.5 : 1.3,
                opacity: d => d.data?.faded ? .11 : 1,
                labelText: d => d.id,
                labelOpacity: d => d.data?.faded ? .04 : state.ontologyDiscoveryFocused || d.data?.selected || d.data?.bridge || d.data?.related || d.data?.searchMatch ? 1 : .28,
                labelPlacement: "bottom", labelOffsetY: 7,
                labelFill: "#dfeff0", labelFontSize: d => d.data?.selected ? 10 : 8, labelFontWeight: 650,
                labelBackground: true, labelBackgroundFill: "#0a1d26", labelBackgroundRadius: 4, labelPadding: [2,5],
                iconText: d => String(d.id).slice(0,2).toUpperCase(),
                iconOpacity: d => d.data?.faded ? .06 : 1,
                iconFill: "#fff", iconFontSize: 10, iconFontWeight: 750,
                cursor: "pointer",
            }},
            edge: { type: "line", style: {
                stroke: d => d.data?.plan ? d.data?.semantic ? "#2ed9b5" : "#d99d48" : "rgba(58,126,139,.28)",
                lineWidth: d => d.data?.plan ? 2.5 : .8,
                lineDash: d => d.data?.plan && !d.data?.semantic ? [5,4] : undefined,
                opacity: d => d.data?.faded ? .08 : 1,
                endArrow: d => Boolean(d.data?.plan),
                labelText: d => d.data?.plan ? d.data?.name || "" : "",
                labelFill: "#a7c3ca", labelFontSize: 8, labelAutoRotate: false,
                labelBackground: true, labelBackgroundFill: "#0b232c", labelBackgroundRadius: 4, labelPadding: [3,5],
            }},
            data: { nodes: graphNodes, edges: graphEdges },
        });
        await ontologyDiscoveryGraph.render();
        ontologyDiscoveryGraph.on("node:click", event => toggleOntologyDiscoveryClass(event.target.id));
    }

    function renderOntologyDiscoverySelection() {
        const container = $("#ontologyDiscoverySelection");
        const plan = state.ontologyDiscoveryPlan;
        const button = $("#applyOntologyDiscovery");
        if (!state.ontologyDiscoverySelected.length) {
            container.innerHTML = '<div class="ontology-discovery-empty">直接点击中央源本体图谱选择业务对象；左侧搜索仅用于快速定位。系统会补充必要的中间对象，并将物理连接与源本体语义分别标识。</div>';
            button.disabled = true;
            return;
        }
        if (!plan) {
            container.innerHTML = `<div class="ontology-discovery-empty">${state.ontologyDiscoveryLoading ? "正在分析连接路径…" : "尚未形成候选路径"}</div>`;
            button.disabled = true;
            return;
        }
        const nodeRows = plan.nodes.map(node => {
            const policy = ontologyDiscoveryNodePolicy(node);
            state.ontologyDiscoveryNodePolicies[node.id] = policy;
            const existing = ontologyDiscoveryExistingClass(node.id);
            return `<div class="ontology-discovery-node" data-discovery-node="${escapeHtml(node.id)}"><div><strong>${escapeHtml(node.id)}</strong><small>${existing ? "已在草案" : node.bridge && !node.selected ? "系统补充的中间对象" : "直接选择对象"}</small></div><select data-discovery-node-policy><option value="core" ${policy === "core" ? "selected" : ""}>核心对象</option><option value="context" ${policy === "context" ? "selected" : ""}>上下文对象</option><option value="reference" ${policy === "reference" ? "selected" : ""}>参考对象</option><option value="path_only" ${policy === "path_only" ? "selected" : ""}>仅连接路径</option><option value="excluded" ${policy === "excluded" ? "selected" : ""}>忽略</option></select></div>`;
        }).join("");
        const joinRows = plan.joins.map(join => {
            const key = ontologyDiscoveryJoinKey(join);
            const usage = state.ontologyDiscoveryJoinUsage[key] || ontologyDiscoveryJoinDefault(join);
            state.ontologyDiscoveryJoinUsage[key] = usage;
            const effective = ontologyDiscoveryEffectiveJoin(join);
            const manuallyMatched = effective.name !== join.recommended_name;
            const relationChoices = (join.semantic_candidates || []).length > 1
                ? `<select data-discovery-join-name aria-label="匹配语义关系">${join.semantic_candidates.map(item => `<option value="${escapeHtml(item.name)}" ${item.name === effective.name ? "selected" : ""}>匹配：${escapeHtml(item.name)}</option>`).join("")}</select>`
                : "";
            const badgeClass = manuallyMatched ? "override" : effective.semantic ? "" : "physical";
            const badgeText = manuallyMatched ? "人工匹配 · 需复核" : effective.semantic ? "源本体语义" : "仅物理外键";
            return `<div class="ontology-discovery-join" data-discovery-join="${escapeHtml(key)}"><div class="ontology-discovery-join-head"><div><strong>${escapeHtml(effective.source)} → ${escapeHtml(effective.name)} → ${escapeHtml(effective.target)}</strong><small>${escapeHtml(join.from_table)}.${escapeHtml(join.from_field)} = ${escapeHtml(join.to_table)}.${escapeHtml(join.to_field)}</small></div><i class="ontology-semantic-badge ${badgeClass}">${badgeText}</i></div>${relationChoices}<select data-discovery-join-usage><option value="published_link" ${usage === "published_link" ? "selected" : ""}>发布为 Graph Studio 关系</option><option value="context_only" ${usage === "context_only" ? "selected" : ""}>仅用于上下文</option><option value="projection_only" ${usage === "projection_only" ? "selected" : ""}>仅用于属性投影</option><option value="excluded" ${usage === "excluded" ? "selected" : ""}>忽略此关系</option></select></div>`;
        }).join("") || '<p class="muted-copy ontology-list-empty">当前选择尚未形成连接关系</p>';
        const seenNeighbors = new Set();
        const neighbors = (plan.neighbor_suggestions || []).filter(item => {
            if (seenNeighbors.has(item.className)) return false;
            seenNeighbors.add(item.className); return true;
        }).slice(0, 10);
        const neighborRows = neighbors.map(item => `<div class="ontology-neighbor-row"><div><strong>${escapeHtml(item.className)}</strong><small>${escapeHtml(item.anchor)} · ${escapeHtml(item.relationship)}</small></div><button class="mini-btn" data-action="add-ontology-neighbor" data-source-class="${escapeHtml(item.className)}">加入</button></div>`).join("") || '<p class="muted-copy ontology-list-empty">暂无额外语义邻居建议</p>';
        container.innerHTML = `<section class="ontology-discovery-section"><div class="ontology-discovery-heading"><strong>对象处理方式</strong><span>${plan.selected_nodes.length} 已选 · ${plan.nodes.filter(item => item.bridge).length} 中间</span></div>${nodeRows}</section><section class="ontology-discovery-section"><div class="ontology-discovery-heading"><strong>关系处理方式</strong><span>${plan.joins.length} 条路径</span></div>${joinRows}</section><section class="ontology-discovery-section"><div class="ontology-discovery-heading"><strong>一跳语义邻居</strong><span>来自源 Neo4j</span></div>${neighborRows}</section>`;
        button.disabled = !plan.nodes.some(node => !["path_only", "excluded"].includes(ontologyDiscoveryNodePolicy(node)));
    }

    function renderOntologyDiscovery() {
        const selectedSource = state.ontologyDiscoverySelected[0];
        const existing = selectedSource ? ontologyDiscoveryExistingClass(selectedSource) : null;
        $("#ontologyDiscoveryPlanState").textContent = selectedSource
            ? `${selectedSource} · ${existing ? "已在草案" : "可加入"}`
            : `${state.ontologyDiscoverySourceGraph.nodes.length || 0} 对象 · 点击选择`;
        renderOntologyInspector();
        renderOntologyDiscoveryGraph().catch(error => toast(error.message, true));
    }

    async function requestOntologyDiscoveryPlan() {
        state.ontologyDiscoveryLoading = true;
        $("#ontologyDiscoveryPlanState").textContent = "分析路径";
        renderOntologyDiscoveryCandidates();
        renderOntologyDiscoverySelection();
        try {
            state.ontologyDiscoveryPlan = state.ontologyDiscoverySelected.length
                ? await request("/api/sync/ontology-governance/discovery-plan", { method: "POST", body: JSON.stringify({ selected_classes: state.ontologyDiscoverySelected, dialect: ontologyDiscoveryDialect() }) })
                : null;
        } finally {
            state.ontologyDiscoveryLoading = false;
            renderOntologyDiscovery();
        }
    }

    function toggleOntologyDiscoveryClass(className) {
        state.ontologyDiscoverySelected = [className];
        const existing = ontologyDiscoveryExistingClass(className);
        state.selectedOntologyClassUid = existing?.id || null;
        state.ontologyDiscoveryPlan = null;
        renderOntologyDiscovery();
    }

    async function applyOntologyDiscoveryProposal() {
        const plan = state.ontologyDiscoveryPlan;
        const workspace = state.ontologyGovernance.currentWorkspace;
        if (!workspace || !plan) return;
        const included = plan.nodes.filter(node => !["path_only", "excluded"].includes(ontologyDiscoveryNodePolicy(node)));
        if (!included.length) { toast("请至少选择一个需要进入发布模型的对象", true); return; }
        const existingGraph = state.ontologyGovernance.graph || { nodes: [], edges: [] };
        const existingBySource = new Map(existingGraph.nodes.map(node => [node.data?.sourceClass, node]));
        const includedNames = new Set(included.map(node => node.id));
        const hasCore = included.some(node => ontologyDiscoveryNodePolicy(node) === "core")
            || existingGraph.nodes.some(node => node.data?.role === "core");
        if (!hasCore) { toast("候选发布范围至少需要一个核心对象", true); return; }
        const button = $("#applyOntologyDiscovery");
        button.disabled = true;
        button.textContent = "正在加入…";
        let addedObjects = 0;
        let addedRelations = 0;
        try {
            for (const node of included) {
                const role = ontologyDiscoveryNodePolicy(node);
                const existing = existingBySource.get(node.id);
                if (existing) {
                    if (existing.data?.role !== role) {
                        await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace.workspace_key)}/classes/${encodeURIComponent(existing.id)}`, { method: "PUT", body: JSON.stringify({ targetName: existing.data.targetName, label: existing.data.label || existing.data.targetName, description: existing.data.description || null, role, orphanPolicy: existing.data.orphanPolicy || "quarantine" }) });
                    }
                    continue;
                }
                await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace.workspace_key)}/classes`, { method: "POST", body: JSON.stringify({ source_class: node.id, target_name: node.id, role, orphan_policy: role === "core" ? "reject" : "quarantine" }) });
                addedObjects += 1;
            }
            const uidFor = className => existingBySource.get(className)?.id || `${workspace.workspace_key}::${className}`;
            for (const join of plan.joins) {
                const usage = state.ontologyDiscoveryJoinUsage[ontologyDiscoveryJoinKey(join)] || ontologyDiscoveryJoinDefault(join);
                const effective = ontologyDiscoveryEffectiveJoin(join);
                const sourceName = effective.source;
                const targetName = effective.target;
                if (usage === "excluded" || !includedNames.has(sourceName) || !includedNames.has(targetName)) continue;
                const sourceUid = uidFor(sourceName);
                const targetUid = uidFor(targetName);
                const duplicate = existingGraph.edges.some(edge => edge.source === sourceUid && edge.target === targetUid && edge.data?.targetName === effective.name);
                if (duplicate) continue;
                await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace.workspace_key)}/relationships`, { method: "POST", body: JSON.stringify({ sourceUid, targetUid, sourceRelationship: effective.name, targetName: effective.name, usage, strength: usage === "published_link" ? "context" : "weak", cardinality: effective.cardinality, requiredContext: usage === "published_link", description: `物理依据：${join.from_table}.${join.from_field} = ${join.to_table}.${join.to_field}` }) });
                addedRelations += 1;
            }
            state.ontologyValidation = null;
            state.ontologyGovernanceStage = "model";
            state.ontologyDiscoverySelected = [];
            state.ontologyDiscoveryPlan = null;
            state.ontologyDiscoveryNodePolicies = {};
            state.ontologyDiscoveryJoinUsage = {};
            state.ontologyDiscoveryJoinNames = {};
            await loadOntologyGovernance();
            toast(`候选方案已加入发布模型：${addedObjects} 个新对象，${addedRelations} 条新关系`);
        } finally {
            button.disabled = false;
            button.textContent = "加入发布模型";
        }
    }

    function renderOntologyGovernanceStage() {
        const unified = $("#ontologyUnifiedWorkbench");
        if (unified) unified.hidden = !state.ontologyGovernance.currentWorkspace;
        if (!state.ontologyGovernance.currentWorkspace) return;
        renderOntologyDiscovery();
        renderOntologyGraph().catch(error => toast(error.message, true));
    }

    function activeReleaseClassKeys() {
        return new Set((state.ontologyGovernance.activeReleaseGraph?.classes || []).flatMap(item => {
            const data = item.class || {};
            return [data.sourceClass, data.sourceUid, data.targetName].filter(Boolean);
        }));
    }

    function isActiveReleaseNode(node) {
        const keys = activeReleaseClassKeys();
        return [node.id, node.data?.sourceClass, node.data?.targetName].some(value => value && keys.has(value));
    }

    function isActiveReleaseEdge(edge, graph) {
        const source = graph.nodes.find(node => node.id === edge.source)?.data || {};
        const target = graph.nodes.find(node => node.id === edge.target)?.data || {};
        return (state.ontologyGovernance.activeReleaseGraph?.relationships || []).some(item => {
            const releasedSource = item.source || {};
            const releasedTarget = item.target || {};
            const relation = item.relation || {};
            const sourceMatches = [source.sourceClass, source.targetName, edge.source].some(value => value && [releasedSource.sourceClass, releasedSource.targetName, releasedSource.sourceUid].includes(value));
            const targetMatches = [target.sourceClass, target.targetName, edge.target].some(value => value && [releasedTarget.sourceClass, releasedTarget.targetName, releasedTarget.sourceUid].includes(value));
            const relationMatches = [edge.data?.targetName, edge.data?.sourceRelationship, edge.id].some(value => value && [relation.targetName, relation.sourceRelationship, relation.relationshipKey].includes(value));
            return sourceMatches && targetMatches && relationMatches;
        });
    }

    async function renderOntologyGraph() {
        const container = $("#ontologyGovernanceGraph");
        if (!container || !window.G6) return;
        if (ontologyGovernanceGraph) {
            ontologyGovernanceGraph.destroy();
            ontologyGovernanceGraph = null;
        }
        const rawGraphData = state.ontologyGovernance.graph || { nodes: [], edges: [] };
        const pairCounts = new Map();
        const graphData = {
            nodes: rawGraphData.nodes.map(node => ({ ...node, data: { ...node.data, released: isActiveReleaseNode(node) } })),
            edges: rawGraphData.edges.map(edge => {
                const pair = `${edge.source}|${edge.target}`;
                const index = pairCounts.get(pair) || 0;
                pairCounts.set(pair, index + 1);
                return { ...edge, data: { ...edge.data, released: isActiveReleaseEdge(edge, rawGraphData), curveOffset: index === 0 ? -30 : 30 + (index - 1) * 22 } };
            }),
        };
        if (!graphData.nodes.length) {
            container.innerHTML = '<div class="muted-copy" style="padding:40px;text-align:center">从左侧源本体添加对象，或创建自定义业务对象</div>';
            return;
        }
        container.innerHTML = "";
        ontologyGovernanceGraph = new G6.Graph({
            container,
            width: container.clientWidth,
            height: container.clientHeight,
            autoFit: "view",
            padding: [72, 96, 82, 96],
            animation: false,
            behaviors: ["drag-element", "drag-canvas", "zoom-canvas"],
            layout: { type: "dagre", rankdir: "LR", nodesep: 86, ranksep: 210 },
            node: {
                type: "circle",
                style: {
                    size: d => d.data?.role === "core" ? 68 : 58,
                    fill: d => d.data?.released ? "#347fc5" : "#08b99d",
                    stroke: d => d.id === state.selectedOntologyClassUid ? "#ffffff" : d.data?.released ? "#74bdff" : "#42ebc9",
                    lineWidth: d => d.id === state.selectedOntologyClassUid ? 4 : 2,
                    labelText: d => d.data?.targetName || d.id,
                    labelFill: "#e7f4f5", labelFontSize: 12, labelFontWeight: 650,
                    labelPlacement: "bottom", labelOffsetY: 10,
                    labelBackground: true, labelBackgroundFill: "#0a1d26",
                    labelBackgroundRadius: 5, labelPadding: [3, 7],
                    iconText: d => String(d.data?.targetName || "OB").slice(0, 2).toUpperCase(),
                    iconFill: "#ffffff", iconFontSize: 14, iconFontWeight: 750,
                    cursor: "pointer",
                },
            },
            edge: {
                type: "quadratic",
                style: {
                    stroke: d => d.data?.released ? "#4b9fea" : d.data?.usage === "published_link" ? "#f2b84b" : "#557985",
                    lineWidth: d => d.data?.strength === "core" ? 3 : 1.5,
                    lineDash: d => d.data?.usage === "projection_only" ? [5, 5] : undefined,
                    endArrow: true,
                    curveOffset: d => d.data?.curveOffset || 0,
                    labelText: d => d.data?.targetName || "",
                    labelFill: "#a8c4ca", labelFontSize: 9, labelFontWeight: 600,
                    labelAutoRotate: false,
                    labelBackground: true, labelBackgroundFill: "#0b232c",
                    labelBackgroundRadius: 4, labelPadding: [3, 6],
                },
            },
            data: { nodes: graphData.nodes, edges: graphData.edges },
        });
        await ontologyGovernanceGraph.render();
        ontologyGovernanceGraph.on("node:click", event => {
            state.selectedOntologyClassUid = event.target.id;
            const selectedNode = state.ontologyGovernance.graph.nodes.find(item => item.id === event.target.id);
            state.ontologyDiscoverySelected = selectedNode?.data?.sourceClass ? [selectedNode.data.sourceClass] : [];
            renderOntologyDiscovery();
            renderOntologyGraph().catch(error => toast(error.message, true));
        });
    }

    function renderOntologyInspector() {
        const container = $("#ontologyInspector");
        const graph = state.ontologyGovernance.graph || { nodes: [], edges: [], properties: [] };
        const selectedSource = state.ontologyDiscoverySelected[0] || null;
        let node = graph.nodes.find(item => item.id === state.selectedOntologyClassUid);
        if (!node && selectedSource) node = graph.nodes.find(item => item.data?.sourceClass === selectedSource);
        if (!node) {
            if (!selectedSource) {
                container.innerHTML = '<p class="muted-copy">点击左侧源图谱中的对象，可直接加入 Graph Studio 发布本体；已加入的对象可在这里配置或移除。</p>';
                return;
            }
            const source = state.ontologyDiscoverySourceGraph.nodes.find(item => item.id === selectedSource);
            container.innerHTML = `<div class="ontology-source-selection"><div class="ontology-source-selection-head"><div><strong>${escapeHtml(selectedSource)}</strong><small>${escapeHtml(source?.data?.chineseName || source?.data?.module || "Camstar 源本体对象")}</small></div><span class="status-pill unknown">未加入</span></div><p class="ontology-source-selection-copy">加入后会复制源本体属性到当前发布草案。对象角色、孤立策略及发布属性仍可在此处继续调整。</p><button class="btn primary" data-action="add-source-ontology-class" data-source-class="${escapeHtml(selectedSource)}">加入 Graph Studio 发布本体</button></div>`;
            return;
        }
        state.selectedOntologyClassUid = node.id;
        const data = node.data || {};
        const released = isActiveReleaseNode(node);
        const properties = graph.properties.filter(item => item.classUid === node.id);
        const relations = graph.edges.filter(item => item.source === node.id || item.target === node.id);
        container.innerHTML = `
            <div class="ontology-inspector-form" data-ontology-class="${escapeHtml(node.id)}">
                <label><span>目标对象名称</span><input name="targetName" value="${escapeHtml(data.targetName || "")}"></label>
                <label><span>显示名称</span><input name="label" value="${escapeHtml(data.label || "")}"></label>
                <label><span>对象角色</span><select name="role">${[["core","核心对象"],["context","上下文对象"],["reference","参考对象"],["on_demand","按需对象"],["excluded","不发布"]].map(([key,text]) => `<option value="${key}" ${data.role === key ? "selected" : ""}>${text}</option>`).join("")}</select></label>
                <label><span>孤立策略</span><select name="orphanPolicy">${[["reject","拒绝发布"],["quarantine","隔离"],["allow","允许孤立"],["referenced_only","仅被引用时"]].map(([key,text]) => `<option value="${key}" ${data.orphanPolicy === key ? "selected" : ""}>${text}</option>`).join("")}</select></label>
                <label><span>说明</span><textarea name="description">${escapeHtml(data.description || "")}</textarea></label>
                <small class="muted-copy">来源：${escapeHtml(data.sourceClass || "自定义业务对象")} · ${released ? "已发布到 Graph Studio" : "本次新增草案"}</small>
                <div class="ontology-inspector-actions"><button class="mini-btn" data-action="save-publish-class">保存对象</button><button class="mini-btn danger" data-action="remove-publish-class">移除对象</button><button class="mini-btn" data-action="add-publish-property">新增属性</button></div>
            </div>
            <section class="ontology-property-section ontology-published-properties">
                <div class="ontology-subheading"><strong>发布属性</strong><span>${properties.filter(item => item.published).length}/${properties.length}</span></div>
                <label class="ontology-property-filter"><span aria-hidden="true">⌕</span><input id="ontologyPropertyFilter" value="${escapeHtml(state.ontologyPropertyFilter)}" placeholder="筛选名称、类型或来源字段"><small id="ontologyPropertyFilterCount"></small></label>
                <div class="ontology-property-list">${properties.map(prop => `
                <label class="ontology-property-row" data-property-search="${escapeHtml(`${prop.targetName} ${prop.dataType || "String"} ${prop.sourcePath || ""}`.toLowerCase())}" title="${escapeHtml(prop.sourcePath || "自定义属性")}">
                    <input type="checkbox" data-publish-property="${escapeHtml(prop.uid)}" ${prop.published ? "checked" : ""}>
                    <span><strong>${escapeHtml(prop.targetName)}</strong><small><b>${escapeHtml(prop.dataType || "String")}</b><em>${escapeHtml(prop.sourcePath || "无源字段")}</em></small></span>
                </label>`).join("") || '<p class="muted-copy ontology-list-empty">尚无属性</p>'}</div>
            </section>
            <section class="ontology-property-section ontology-relations">
                <div class="ontology-subheading"><strong>对象关联</strong><span>${relations.length}</span></div>
                <div class="ontology-relation-list">${relations.map(rel => `
                    <div class="ontology-release-row"><div><strong>${escapeHtml(rel.data.targetName)}</strong><small>${escapeHtml(rel.data.usage)} · ${escapeHtml(rel.data.strength)}</small></div><button class="mini-btn" data-action="remove-publish-relation" data-relation="${escapeHtml(rel.id)}">删除</button></div>`).join("") || '<p class="muted-copy ontology-list-empty">尚无关联</p>'}</div>
            </section>`;
        applyOntologyPropertyFilter();
    }

    function applyOntologyPropertyFilter() {
        const input = $("#ontologyPropertyFilter");
        if (!input) return;
        const term = input.value.trim().toLowerCase();
        const rows = $$(".ontology-property-row", $("#ontologyInspector"));
        let visible = 0;
        rows.forEach(row => {
            const matches = !term || row.dataset.propertySearch.includes(term);
            row.hidden = !matches;
            if (matches) visible += 1;
        });
        const count = $("#ontologyPropertyFilterCount");
        if (count) count.textContent = term ? `${visible} 项` : "";
    }

    function renderOntologyGovernance() {
        const data = state.ontologyGovernance;
        const workspace = data.currentWorkspace;
        $("#ontologyGovernanceEmpty").hidden = Boolean(workspace);
        $("#ontologyWorkspaceTitle").textContent = workspace?.title || "发布本体草案";
        const graph = data.graph || { nodes: [], edges: [], properties: [] };
        $("#ontologyGovernanceSummary").innerHTML = workspace ? `
            <span>发布库 <strong>${escapeHtml(data.database)}</strong></span>
            <span>工作区 <strong>${statusLabel(workspace.status)} · r${workspace.revision}</strong></span>
            <span>对象 <strong>${graph.nodes.length}</strong></span>
            <span>属性 <strong>${graph.properties.filter(item => item.published).length}</strong></span>
            <span>关系 <strong>${graph.edges.filter(item => item.data.usage === "published_link").length}</strong></span>
            <span>活动版本 <strong>${data.activeRelease ? `R${data.activeRelease.release_no}` : "无"}</strong></span>`
            : '<span>尚未初始化发布本体数据库和工作区</span>';
        $("#ontologyReleaseList").innerHTML = data.releases.map(item => `
            <div class="ontology-release-row" data-ontology-release="${item.ontology_release_id}"><div><strong>本体 R${item.release_no}</strong><small>${item.class_count} 对象 · ${item.property_count} 属性 · ${item.relationship_count} 关系</small></div><div class="card-action-buttons"><span class="status-pill ${item.status}">${statusLabel(item.status)}</span>${item.status !== "active" ? '<button class="mini-btn" data-action="activate-ontology-release">激活</button>' : ""}</div></div>`).join("") || '<div class="compact-row"><small>尚无冻结版本</small></div>';
        const validation = state.ontologyValidation;
        $("#ontologyValidationCount").textContent = validation ? (validation.valid ? "通过" : `${validation.errors.length} 阻断`) : "未校验";
        $("#ontologyValidationIssues").innerHTML = validation ? [...validation.errors, ...validation.warnings].map(item => `<div class="issue-row ${validation.errors.includes(item) ? "error" : "warning"}"><strong>${escapeHtml(item.code)}</strong><span>${escapeHtml(item.message)}</span></div>`).join("") || '<div class="issue-row success"><strong>通过</strong><span>对象、属性、关系和上下文完整性均通过</span></div>' : '<p class="muted-copy">编辑后运行校验，批准前必须消除全部阻断项。</p>';
        renderOntologyGovernanceStage();
    }

    function openCustomOntologyClassDialog() {
        $("#dialogTitle").textContent = "新建业务本体对象";
        $("#dialogKicker").textContent = "CUSTOM OBJECT TYPE";
        $("#dialogFields").innerHTML = [
            field("target_name", "目标对象名称", "", { wide: true }),
            field("label", "显示名称", ""),
            field("role", "对象角色", "context", { type: "select", items: [["core","核心对象"],["context","上下文对象"],["reference","参考对象"],["on_demand","按需对象"]] }),
            field("orphan_policy", "孤立策略", "quarantine", { type: "select", items: [["reject","拒绝发布"],["quarantine","隔离"],["allow","允许孤立"],["referenced_only","仅被引用时"]] }),
            field("description", "业务说明", "", { type: "textarea", wide: true }),
        ].join("");
        state.dialogSubmit = async form => {
            const workspace = state.ontologyGovernance.currentWorkspace.workspace_key;
            await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace)}/classes`, { method: "POST", body: JSON.stringify({ source_class: null, target_name: form.get("target_name"), label: form.get("label") || null, description: form.get("description") || null, role: form.get("role"), orphan_policy: form.get("orphan_policy") }) });
            state.ontologyValidation = null; await loadOntologyGovernance(); toast("自定义本体对象已加入草案");
        };
        $("#editDialog").showModal();
    }

    function openOntologyRelationshipDialog() {
        const nodes = state.ontologyGovernance.graph.nodes;
        if (nodes.length < 2) { toast("至少需要两个对象才能建立关系", true); return; }
        $("#dialogTitle").textContent = "新增发布关系";
        $("#dialogKicker").textContent = "LINK TYPE";
        const items = nodes.map(node => [node.id, node.data.targetName]);
        $("#dialogFields").innerHTML = [
            field("source_uid", "源对象", nodes[0].id, { type: "select", items }),
            field("target_uid", "目标对象", nodes[1].id, { type: "select", items }),
            field("target_name", "Graph Studio 关系名称", "RELATED_TO", { wide: true }),
            field("source_relationship", "源本体/契约关系", "", { help: "用于匹配治理实例中的 relationship_name" }),
            field("usage", "使用方式", "published_link", { type: "select", items: [["published_link","作为 Graph Studio 边"],["projection_only","仅用于属性投影"],["context_only","仅用于上下文"],["excluded","不发布"]] }),
            field("strength", "业务强度", "context", { type: "select", items: [["core","核心关联"],["context","上下文关联"],["weak","弱关联"],["on_demand","按需关联"]] }),
            field("cardinality", "基数", "many-to-one"),
            field("required_context", "必需上下文", false, { type: "checkbox", wide: true }),
        ].join("");
        state.dialogSubmit = async form => {
            const workspace = state.ontologyGovernance.currentWorkspace.workspace_key;
            await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace)}/relationships`, { method: "POST", body: JSON.stringify({ sourceUid: form.get("source_uid"), targetUid: form.get("target_uid"), targetName: form.get("target_name"), sourceRelationship: form.get("source_relationship") || null, usage: form.get("usage"), strength: form.get("strength"), cardinality: form.get("cardinality"), requiredContext: form.get("required_context") === "on" }) });
            state.ontologyValidation = null; await loadOntologyGovernance(); toast("发布关系已加入草案");
        };
        $("#editDialog").showModal();
    }

    function openPublishPropertyDialog(node) {
        $("#dialogTitle").textContent = `${node.data.targetName} 新增属性`;
        $("#dialogKicker").textContent = "PUBLISH PROPERTY";
        $("#dialogFields").innerHTML = [
            field("target_name", "目标属性名称", "", { wide: true }),
            field("source_name", "治理数据属性键", ""),
            field("source_path", "来源路径/血缘", "", { placeholder: "ProductAttribute.DisplayGroup" }),
            field("data_type", "数据类型", "String", { type: "select", items: [["String","String"],["Integer","Integer"],["Decimal","Decimal"],["Boolean","Boolean"],["DateTime","DateTime"]] }),
            field("required", "必填属性", false, { type: "checkbox" }),
            field("description", "说明", "", { type: "textarea", wide: true }),
        ].join("");
        state.dialogSubmit = async form => {
            const workspace = state.ontologyGovernance.currentWorkspace.workspace_key;
            await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace)}/classes/${encodeURIComponent(node.id)}/properties`, { method: "PUT", body: JSON.stringify({ targetName: form.get("target_name"), sourceName: form.get("source_name") || form.get("target_name"), sourcePath: form.get("source_path") || null, dataType: form.get("data_type"), description: form.get("description") || null, required: form.get("required") === "on", published: true, origin: form.get("source_path") ? "projection" : "custom" }) });
            state.ontologyValidation = null; await loadOntologyGovernance(); toast("发布属性已保存");
        };
        $("#editDialog").showModal();
    }

    function renderConnections() {
        $("#connectionGrid").innerHTML = state.connections.map(item => `
            <article class="connection-card" data-connection="${escapeHtml(item.connection_key)}">
                <div class="card-top"><div><h3>${escapeHtml(item.display_name)}</h3><p>${escapeHtml(connectionKindLabel(item.kind))}</p></div><span class="status-pill ${item.status}">${statusLabel(item.status)}</span></div>
                <div class="card-details">
                    <div class="detail-field"><span>Endpoint</span><strong title="${escapeHtml(item.endpoint)}">${escapeHtml(item.endpoint)}</strong></div>
                    <div class="detail-field"><span>Database / Target</span><strong title="${escapeHtml(item.database_name || "—")}">${escapeHtml(item.database_name || "—")}</strong></div>
                    <div class="detail-field"><span>User</span><strong>${escapeHtml(item.username || "—")}</strong></div>
                    <div class="detail-field"><span>Secret</span><strong>${escapeHtml(item.secret_ref)}</strong></div>
                </div>
                <div class="card-actions"><small>${item.last_tested_at ? `上次测试 ${formatDate(item.last_tested_at, true)}` : "尚未测试"}</small><div class="card-action-buttons">${item.editable ? '<button class="mini-btn" data-action="edit-connection">编辑</button>' : ''}<button class="mini-btn" data-action="test-connection">测试</button></div></div>
            </article>`).join("");
    }

    function renderJobs() {
        $("#jobGrid").innerHTML = state.jobs.map(item => `
            <article class="job-card" data-job="${escapeHtml(item.job_name)}">
                <div class="card-top"><div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.job_name)}</p></div><span class="mode-pill">${item.mode === "atomic_snapshot" ? "原子快照" : "分区增量"}</span></div>
                <p style="color:var(--muted);font-size:10px;line-height:1.55;margin:16px 0">${escapeHtml(item.description || "")}</p>
                <div class="card-details">
                    <div class="detail-field"><span>Schedule</span><strong>${escapeHtml(item.schedule || "手动")}</strong></div>
                    <div class="detail-field"><span>Timezone</span><strong>${escapeHtml(item.timezone)}</strong></div>
                    <div class="detail-field"><span>Scope</span><strong>${escapeHtml(item.scopes?.map(scope => scope.class_pattern).join(", ") || "—")}</strong></div>
                    <div class="detail-field"><span>Retention</span><strong>${item.retention_success} 个成功版本</strong></div>
                </div>
                <div class="card-actions"><small>${item.enabled ? "任务已启用" : "任务已停用"}</small><div class="card-action-buttons"><button class="mini-btn" data-action="dry-run-job">执行盘点</button><button class="mini-btn" data-action="preview-job">生成 RDF 预览</button><button class="mini-btn" data-action="edit-job">配置任务</button></div></div>
            </article>`).join("");
        renderTablePolicies();
    }

    function renderTablePolicies() {
        const rows = state.tablePolicies || [];
        const capabilities = new Map((state.incrementalProbe?.tables || []).map(item => [item.className, item]));
        const risky = rows.filter(item => item.requires_review);
        $("#tablePolicyRiskCount").textContent = `${risky.length} 个待审核`;
        $("#tablePolicyRows").innerHTML = rows.map(item => {
            const effective = item.effective_strategy;
            const status = item.requires_review
                ? '<span class="status-pill failed">大表未配置</span>'
                : item.explicitly_configured
                    ? '<span class="status-pill online">已配置</span>'
                    : '<span class="status-pill">默认安全策略</span>';
            const recommendation = item.requires_review ? `建议：${strategyLabel(item.recommended_strategy)}` : "";
            const capability = capabilities.get(item.class_name);
            const nativeAdapter = capability?.nativeAdapter
                ? capability.nativeAdapter.replace("sqlserver_", "").replaceAll("_", " ").toUpperCase()
                : "—";
            return `<tr data-policy-class="${escapeHtml(item.class_name)}">
                <td><strong>${escapeHtml(item.class_name)}</strong><br><small>${escapeHtml(`${item.physical_schema}.${item.physical_table}`)}</small></td>
                <td>${Number(item.approximate_rows || 0).toLocaleString()}</td>
                <td>${escapeHtml(strategyLabel(effective))}${recommendation ? `<br><small>${escapeHtml(recommendation)}</small>` : ""}</td>
                <td>${escapeHtml(nativeAdapter)}</td>
                <td>${Number(item.batch_rows || 0).toLocaleString()} 行</td>
                <td>${status}</td>
                <td><button class="mini-btn" data-action="edit-table-policy">配置</button></td>
            </tr>`;
        }).join("") || '<tr class="empty-row"><td colspan="7">请先编译本体映射目录</td></tr>';
    }

    function renderIncrementalCapabilities() {
        const probe = state.incrementalProbe;
        const container = $("#incrementalCapabilitySummary");
        if (!probe || probe.available === false) {
            container.innerHTML = "<span>尚未检测 SQL Server CT/CDC 或 Oracle SCN</span>";
            renderTablePolicies(); return;
        }
        const tables = probe.tables || [];
        const ready = tables.filter(item => item.nativeChangeCaptureReady).length;
        const position = probe.sourcePosition || {};
        const sourceCapabilities = probe.capabilities || {};
        const positionText = position.changeTrackingVersion != null
            ? `CT ${position.changeTrackingVersion}`
            : position.cdcMaxLsn ? `LSN ${position.cdcMaxLsn}`
                : position.scn != null ? `SCN ${position.scn}` : "无原生位置";
        const chips = [
            ["数据源", connectionKindLabel(probe.sourceKind)],
            ["原生增量就绪", `${ready}/${tables.length} 张表`],
            ["当前位置", positionText],
            ["检测时间", formatDate(probe.capturedAt, true)],
        ];
        if (probe.sourceKind === "camstar_sqlserver") {
            chips.push(
                ["Change Tracking", sourceCapabilities.changeTrackingEnabled ? "已启用" : "未启用", !sourceCapabilities.changeTrackingEnabled],
                ["CDC", sourceCapabilities.cdcEnabled ? "已启用" : "未启用", !sourceCapabilities.cdcEnabled],
                ["Snapshot Isolation", sourceCapabilities.snapshotIsolation || "未知", sourceCapabilities.snapshotIsolation !== "ON"],
            );
        } else {
            chips.push(
                ["Flashback SCN", sourceCapabilities.flashbackScnAvailable ? "可用" : "不可用", !sourceCapabilities.flashbackScnAvailable],
                ["Undo Retention", sourceCapabilities.undoRetentionSeconds ? `${sourceCapabilities.undoRetentionSeconds}s` : "未知", !sourceCapabilities.undoRetentionSeconds],
            );
        }
        const warning = ready === 0
            ? '<div class="capability-warning">当前源库没有可用的原生变更捕获。请先由 DBA 审核并启用相应能力；工具不会将 CDC 策略退化为全表扫描。</div>'
            : "";
        container.innerHTML = `<div class="capability-chips">${chips.map(([label, value, danger]) => `<span class="capability-chip ${danger ? "danger" : ""}">${escapeHtml(label)} <strong>${escapeHtml(value)}</strong></span>`).join("")}</div>${warning}`;
        renderTablePolicies();
    }

    function renderMappings() {
        const catalog = state.mappings?.catalog || {};
        const snapshot = catalog.snapshot || {};
        $("#mappingMetrics").innerHTML = [
            ["本体类", snapshot.ontology_class_count ?? "—", `${snapshot.physical_table_count ?? 0} 张表已匹配`],
            ["本体属性", snapshot.ontology_property_count ?? "—", `${(snapshot.ontology_property_count || 0) - (catalog.unresolvedProperties?.length || 0)} 个已映射`],
            ["本体关系", snapshot.relationship_count ?? "—", `${catalog.relationshipStatus?.resolved || 0} 条已解析物理关联`],
            ["映射覆盖率", snapshot.mapping_coverage != null ? `${Number(snapshot.mapping_coverage).toFixed(2)}%` : "—", `${catalog.unresolvedProperties?.length || 0} 个待确认`],
        ].map(([label, value, note]) => `<article class="metric-card"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`).join("");
        const unmapped = catalog.unresolvedProperties || [];
        $("#unmappedCount").textContent = unmapped.length;
        $("#mappingRows").innerHTML = unmapped.map(item => `
            <tr data-property-key="${escapeHtml(`${item.className}|${item.propertyName}`)}"><td>${escapeHtml(item.className)}</td><td>${escapeHtml(item.propertyName)}</td><td>${escapeHtml(item.dataType)}</td><td>${escapeHtml(item.sourceFieldId || "—")}</td><td><span class="status-pill unknown">待确认</span></td><td><button class="mini-btn" data-action="override-property">处理</button></td></tr>
        `).join("") || '<tr class="empty-row"><td colspan="6">全部属性映射已确认</td></tr>';
        const relationships = catalog.relationshipReview || [];
        $("#relationshipReviewCount").textContent = relationships.length;
        $("#relationshipRows").innerHTML = relationships.map(item => `
            <tr data-relationship-key="${escapeHtml(`${item.sourceClass}|${item.relationshipName}|${item.targetClass}`)}"><td>${escapeHtml(item.sourceClass)}</td><td>${escapeHtml(item.relationshipName)}</td><td>${escapeHtml(item.targetClass)}</td><td><span class="status-pill unknown">${item.mappingStatus === "ambiguous" ? "多候选" : "未解析"}</span></td><td title="${escapeHtml((item.candidateProperties || []).join(', '))}">${escapeHtml((item.candidateProperties || []).join(', ') || "—")}</td><td><button class="mini-btn" data-action="override-relationship">选择属性</button></td></tr>
        `).join("") || '<tr class="empty-row"><td colspan="6">全部关系映射已确认</td></tr>';
    }

    function renderGraphProfile() {
        const payload = state.activeProfile;
        if (!payload) return;
        const profile = payload.profile;
        const classes = payload.classes || [];
        const relationships = payload.relationships || [];
        const issues = payload.issues || [];
        const approved = issues.filter(item => item.severity === "error").length === 0
            && classes.length > 0 && classes.every(item => item.review_status === "approved")
            && relationships.every(item => item.review_status === "approved");
        $("#profileTitle").textContent = profile.title;
        $("#profileReviewStatus").className = `count-badge ${approved ? "approved" : ""}`;
        $("#profileReviewStatus").textContent = approved ? "可进入发布审批" : "草案 / 待审核";
        const roleCounts = Object.fromEntries(["core", "context", "reference", "on_demand"].map(role => [role, classes.filter(item => item.enabled && item.role === role).length]));
        $("#profileMetrics").innerHTML = [
            ["核心对象", roleCounts.core, "种子与主要业务实体"],
            ["上下文对象", roleCounts.context, "补齐业务语义"],
            ["可扩展关系", relationships.filter(item => item.enabled && item.traverse).length, "弱关联不参与扩展"],
            ["待处理问题", issues.length, `${issues.filter(item => item.severity === "error").length} 个阻断项`],
        ].map(([label, value, note]) => `<article class="metric-card"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`).join("");
        const closure = state.closurePlan;
        $("#profileBoundary").innerHTML = `
            <div class="boundary-cell"><span>种子对象</span><strong>${escapeHtml(classes.filter(item => item.seed_enabled).map(item => item.class_name).join("、") || "未配置")}</strong></div>
            <div class="boundary-cell"><span>最大关系深度</span><strong>${profile.max_depth} 层</strong></div>
            <div class="boundary-cell"><span>每个种子的上下文预算</span><strong>${Number(profile.max_context_nodes_per_seed).toLocaleString()} 节点</strong></div>
            <div class="boundary-cell"><span>单次运行总预算</span><strong>${Number(profile.max_total_nodes_per_run).toLocaleString()} 节点</strong></div>
            <div class="boundary-note">${closure ? `最近预览：${closure.summary.includedClassCount} 类、${closure.summary.traversalStepCount} 个扩展步骤；未读取 Camstar 数据，未修改 Graph Studio。` : "闭包预览只计算类与关系范围，不读取业务行，也不会修改 Graph Studio。"}</div>`;
        const query = ($("#profileClassSearch")?.value || "").trim().toLowerCase();
        const filteredClasses = classes.filter(item => !query || item.class_name.toLowerCase().includes(query) || String(item.chinese_name || "").toLowerCase().includes(query));
        $("#profileClassRows").innerHTML = filteredClasses.map(item => `
            <tr data-profile-class="${escapeHtml(item.class_name)}"><td><strong>${escapeHtml(item.class_name)}</strong><br><small>${escapeHtml(item.physical_table || "物理映射待解析")}</small></td><td>${escapeHtml(roleLabel(item.role))}</td><td>${item.seed_enabled ? '<span class="status-pill online">是</span>' : "—"}</td><td>${escapeHtml(orphanLabel(item.orphan_policy))}</td><td>${Number(item.approximate_rows || 0).toLocaleString()}</td><td><span class="status-pill ${item.review_status === "approved" ? "online" : "unknown"}">${item.review_status === "approved" ? "已批准" : "待审核"}</span></td><td><button class="mini-btn" data-action="edit-profile-class">配置</button></td></tr>
        `).join("") || '<tr class="empty-row"><td colspan="7">没有符合条件的对象</td></tr>';
        $("#profileRelationshipRows").innerHTML = relationships.map(item => `
            <tr data-profile-relationship="${escapeHtml(`${item.source_class}|${item.relationship_name}|${item.target_class}`)}"><td>${escapeHtml(item.source_class)}</td><td>${escapeHtml(item.relationship_name)}</td><td>${escapeHtml(item.target_class)}</td><td>${escapeHtml(strengthLabel(item.strength))}</td><td>${item.traverse ? '<span class="status-pill online">扩展</span>' : '<span class="status-pill">不扩展</span>'}</td><td><span class="status-pill ${item.mapping_status === "resolved" ? "online" : "unknown"}">${item.mapping_status === "resolved" ? "已解析" : "待映射"}</span></td><td><button class="mini-btn" data-action="edit-profile-relationship">配置</button></td></tr>
        `).join("") || '<tr class="empty-row"><td colspan="7">尚未配置关系。添加关系后默认仍需人工审核。</td></tr>';
        $("#profileIssueCount").textContent = `${issues.length} 项`;
        $("#profileIssues").innerHTML = issues.map(item => `<div class="profile-issue ${item.severity}"><span>${item.severity === "error" ? "阻断" : "提醒"}</span><strong>${escapeHtml(item.message)}</strong><small>${escapeHtml(item.rule)}</small></div>`).join("") || '<div class="profile-empty">业务图谱配置检查通过</div>';
        renderGovernance();
    }

    function reviewLabel(value) {
        return ({ draft: "草案", reviewed: "已复核", approved: "已批准", retired: "已退役" })[value] || value;
    }

    function renderGovernance() {
        const governance = state.governance || {};
        const contracts = governance.contracts || [];
        const relationships = governance.relationships || [];
        const latest = governance.latestRun;
        const gate = $("#curationPublishable");
        gate.className = `count-badge ${latest?.publishable ? "approved" : ""}`;
        gate.textContent = latest ? (latest.publishable ? "具备发布资格" : "未通过治理门禁") : "尚未预览";
        $("#dataContractRows").innerHTML = contracts.map(item => `
            <tr data-contract="${escapeHtml(item.contract_key)}"><td><strong>${escapeHtml(item.class_name)}</strong><br><small>v${item.version}</small></td><td>${escapeHtml(`${item.source_schema}.${item.source_table}`)}</td><td>${escapeHtml((item.primary_key_columns || []).join(", "))}<br><small>${escapeHtml((item.business_key_columns || []).join(", ") || "未配置业务键")}</small></td><td title="${escapeHtml((item.required_columns || []).join(', '))}">${escapeHtml((item.required_columns || []).join(", ") || "—")}</td><td>${Number(item.preview_row_limit).toLocaleString()} 行</td><td><span class="status-pill ${item.status === "approved" ? "online" : "unknown"}">${escapeHtml(reviewLabel(item.status))}</span></td><td><button class="mini-btn" data-action="edit-data-contract">配置</button></td></tr>
        `).join("") || '<tr class="empty-row"><td colspan="7">尚未配置数据契约</td></tr>';
        $("#relationshipContractRows").innerHTML = relationships.map(item => `
            <tr data-relationship-contract="${escapeHtml(item.relationship_contract_key)}"><td><strong>${escapeHtml(item.relationship_name)}</strong><br><small>v${item.version}</small></td><td>${escapeHtml(item.semantic_role)}</td><td>${escapeHtml((item.source_columns || []).join(", "))}</td><td>${escapeHtml(item.target_class)}.${escapeHtml((item.target_columns || []).join(", "))}</td><td>${item.required_context ? '<span class="status-pill online">必需</span>' : '<span class="status-pill">可选</span>'}</td><td><span class="status-pill ${item.status === "approved" ? "online" : "unknown"}">${escapeHtml(reviewLabel(item.status))}</span></td><td><button class="mini-btn" data-action="edit-relationship-contract">配置</button></td></tr>
        `).join("") || '<tr class="empty-row"><td colspan="7">尚未配置关系契约</td></tr>';
        const results = governance.qualityResults || [];
        $("#qualityResultCount").textContent = latest ? `${results.filter(item => !item.passed).length} 项未通过` : "0";
        $("#qualityResults").innerHTML = results.map(item => `<div class="profile-issue ${!item.passed && item.severity === "error" ? "error" : ""}"><span>${item.passed ? "通过" : item.severity === "error" ? "阻断" : "提醒"}</span><strong>${escapeHtml(item.message)}</strong><small>${Number(item.failed_rows || 0).toLocaleString()}/${Number(item.checked_rows || 0).toLocaleString()} · ${escapeHtml(item.rule_key)}</small></div>`).join("") || '<div class="profile-empty">运行治理预览后显示质量证据</div>';
        renderSchemaEvolution();
    }

    function compatibilityLabel(value) {
        return ({ non_breaking: "兼容", conditional: "有条件兼容", breaking: "破坏性" })[value] || value;
    }

    function fieldRoleLabel(value) {
        return ({ primary_key: "主键", business_key: "业务键", freshness: "增量水位", attribute: "属性", navigation: "关联字段", system: "系统字段" })[value] || value;
    }

    function schemaStatusLabel(value) {
        return ({ draft: "草案", analysis_ready: "分析完成", reviewed: "已复核", approved: "已批准待迁移", applying: "迁移中", applied: "已应用", rejected: "已拒绝", failed: "失败", rolled_back: "已回滚" })[value] || value;
    }

    function renderSchemaEvolution() {
        const contracts = state.governance?.contracts || [];
        const selector = $("#schemaContractSelect");
        const selectedKey = state.contractSchema?.contract?.contract_key || selector?.value || contracts[0]?.contract_key;
        selector.innerHTML = contracts.map(item => `<option value="${escapeHtml(item.contract_key)}" ${item.contract_key === selectedKey ? "selected" : ""}>${escapeHtml(item.class_name)} · v${item.version}</option>`).join("");
        const schema = state.contractSchema;
        const fields = schema?.fields || [];
        const active = fields.filter(item => item.lifecycle_status === "active").length;
        const deprecated = fields.filter(item => item.lifecycle_status === "deprecated").length;
        const dependencies = (schema?.dependencies || []).filter(item => item.active).length;
        $("#schemaEvolutionSummary").innerHTML = schema ? `<div class="capability-chips"><span class="capability-chip">当前版本 <strong>v${schema.contract.version}</strong></span><span class="capability-chip">活动字段 <strong>${active}</strong></span><span class="capability-chip">已废弃 <strong>${deprecated}</strong></span><span class="capability-chip">活动依赖 <strong>${dependencies}</strong></span></div>` : "<span>正在加载字段目录…</span>";
        $("#contractFieldRows").innerHTML = fields.map(item => `<tr><td><strong>${escapeHtml(item.target_field)}</strong><br><small>${escapeHtml(item.field_key)}</small></td><td>${escapeHtml(item.source_column || "计算字段")}</td><td>${escapeHtml(item.data_type)}</td><td>${escapeHtml(fieldRoleLabel(item.field_role))}</td><td><span class="status-pill ${item.lifecycle_status === "active" ? "online" : "unknown"}">${escapeHtml(item.lifecycle_status)}</span></td><td>${Number(item.dependency_count || 0)}</td><td>v${item.introduced_version}</td></tr>`).join("") || '<tr class="empty-row"><td colspan="7">暂无字段目录</td></tr>';
        const changes = state.schemaChanges || [];
        $("#schemaChangeCount").textContent = `${changes.length} 项`;
        $("#schemaChangeRows").innerHTML = changes.map(item => {
            const blockers = item.impact_summary?.blockers || [];
            const actions = item.status === "analysis_ready" ? '<button class="mini-btn" data-action="review-schema-change">复核</button>' : item.status === "reviewed" ? '<button class="mini-btn" data-action="approve-schema-change">批准</button>' : item.status === "approved" ? '<button class="mini-btn" data-action="apply-schema-change">执行迁移</button>' : item.status === "applied" ? '<button class="mini-btn" data-action="rollback-schema-change">回滚</button>' : "—";
            return `<tr data-schema-change="${escapeHtml(item.change_id)}"><td><strong>${escapeHtml(item.title)}</strong><br><small>${formatDate(item.created_at, true)}</small></td><td>${escapeHtml(item.contract_key)}<br><small>v${item.base_version} → v${item.target_version}</small></td><td><span class="status-pill ${item.compatibility === "non_breaking" ? "online" : item.compatibility === "breaking" ? "failed" : "unknown"}">${escapeHtml(compatibilityLabel(item.compatibility))}</span></td><td>${item.items?.length || 0}</td><td>${blockers.length ? `<span class="status-pill failed">${blockers.length} 项</span>` : "—"}</td><td>${escapeHtml(schemaStatusLabel(item.status))}</td><td>${actions}</td></tr>`;
        }).join("") || '<tr class="empty-row"><td colspan="7">尚无 Schema 变更申请</td></tr>';
    }

    function projectionPolicyLabel(value) {
        return ({ reject: "拒绝多值", first: "取第一条", latest: "取最新", array: "合并数组" })[value] || value;
    }

    function renderAttributeProjections() {
        const items = state.attributeProjections || [];
        const approved = items.filter(item => item.enabled && item.status === "approved").length;
        const waiting = items.filter(item => item.enabled && item.status !== "approved").length;
        $("#projectionCount").textContent = `${items.length} 项`;
        $("#projectionSummary").innerHTML = `<div class="capability-chips"><span class="capability-chip">已批准 <strong>${approved}</strong></span><span class="capability-chip ${waiting ? "danger" : ""}">待治理 <strong>${waiting}</strong></span><span class="capability-chip">执行方式 <strong>批量参数化 Join</strong></span><span class="capability-chip">源库写入 <strong>禁止</strong></span></div><div class="projection-guidance">扩展表发生独立变化时，应由定时治理版本重新物化；主对象的增量事件会即时刷新对应投影。所有规则均使用字段化配置，不接收原始 SQL。</div>`;
        $("#projectionRows").innerHTML = items.map(item => {
            const actions = [
                '<button class="mini-btn" data-action="edit-projection">编辑</button>',
                '<button class="mini-btn" data-action="preview-projection">预览</button>',
            ];
            if (item.status === "draft" && item.preview_status === "succeeded") actions.push('<button class="mini-btn" data-action="review-projection">复核</button>');
            if (item.status === "reviewed") actions.push('<button class="mini-btn" data-action="approve-projection">批准</button>');
            if (item.status === "approved") actions.push('<button class="mini-btn" data-action="retire-projection">退役</button>');
            const preview = item.preview_status === "succeeded"
                ? `${Number(item.preview_matched_rows || 0).toLocaleString()} 匹配 / ${Number(item.preview_owner_rows || 0).toLocaleString()} 对象`
                : statusLabel(item.preview_status);
            return `<tr data-projection="${escapeHtml(item.projection_key)}"><td><strong>${escapeHtml(item.class_name)}</strong><br><small>${escapeHtml(item.projection_key)} · v${item.version}</small></td><td>${escapeHtml(`${item.source_schema}.${item.source_table}`)}</td><td>${(item.join_plan || []).length} 跳<br><small>${(item.owner_mapping || []).length} 个关联键</small></td><td>${(item.fields || []).length}<br><small>${escapeHtml((item.fields || []).slice(0, 3).map(field => field.target_field).join(", "))}</small></td><td>${escapeHtml(projectionPolicyLabel(item.multiple_match_policy))}</td><td><span class="status-pill ${item.preview_status === "succeeded" ? "online" : "unknown"}">${escapeHtml(preview)}</span></td><td><span class="status-pill ${item.status === "approved" ? "online" : "unknown"}">${escapeHtml(statusLabel(item.status))}</span></td><td><div class="card-action-buttons">${actions.join("")}</div></td></tr>`;
        }).join("") || '<tr class="empty-row"><td colspan="8">尚无属性投影。点击“新增属性投影”，即可把关联表字段合并到 Product、Workflow 或任意对象。</td></tr>';
    }

    function renderMaterialization() {
        const plan = state.materialization?.plan;
        const blockers = plan?.blockers || [];
        $("#materializationPlan").innerHTML = plan ? `<div class="capability-chips"><span class="capability-chip ${plan.ready ? "" : "danger"}">门禁 <strong>${plan.ready ? "可执行" : `${blockers.length} 项阻断`}</strong></span><span class="capability-chip">批大小 <strong>${Number(plan.batchRows).toLocaleString()}</strong></span><span class="capability-chip">策略 <strong>不可变快照</strong></span><span class="capability-chip">回滚 <strong>指针切换</strong></span></div>${blockers.length ? `<div class="capability-warning">${blockers.map(escapeHtml).join("；")}</div>` : ""}` : "正在加载物化计划…";
        const releases = state.materialization?.releases || [];
        $("#releaseRows").innerHTML = releases.map(item => `<tr data-release="${escapeHtml(item.release_id)}"><td><strong>R${item.release_no}</strong><br><small>${String(item.release_id).slice(0, 8)}</small></td><td><span class="status-pill ${item.is_active || item.status === "ready" ? "online" : item.status === "failed" ? "failed" : "unknown"}">${item.is_active ? "活动" : escapeHtml(statusLabel(item.status))}</span></td><td>${Number(item.object_count || 0).toLocaleString()}</td><td>${Number(item.relationship_count || 0).toLocaleString()}</td><td>${Number(item.quarantine_count || 0).toLocaleString()}</td><td>${formatDate(item.started_at, true)}</td><td>${item.status === "ready" ? '<button class="mini-btn" data-action="activate-release">激活</button>' : "—"}</td></tr>`).join("") || '<tr class="empty-row"><td colspan="7">尚无治理快照；当前审批门禁会阻止实际写入</td></tr>';
    }

    function renderDeployments() {
        const data = state.deployments || { environments: [], deployments: [] };
        $("#environmentCards").innerHTML = data.environments.map(item => `<article class="job-card" data-environment="${escapeHtml(item.environment_key)}"><div class="card-top"><div><p>ENVIRONMENT ${item.promotion_order}</p><h3>${escapeHtml(item.title)}</h3></div><span class="status-pill ${item.apply_enabled ? "online" : "unknown"}">${item.apply_enabled ? "允许发布" : "发布关闭"}</span></div><div class="card-details"><div class="detail-field"><span>Graphmart</span><strong>${escapeHtml(String(item.graphmart_uri).split("/").pop())}</strong></div><div class="detail-field"><span>Approval</span><strong>${item.requires_approval ? "需要审批" : "自动批准"}</strong></div></div><div class="card-actions"><small>蓝绿制品 · 顺序晋级</small><button class="mini-btn" data-action="prepare-deployment">准备制品</button></div></article>`).join("");
        $("#deploymentRows").innerHTML = data.deployments.map(item => {
            let actions = "—";
            if (item.status === "planned") actions = '<button class="mini-btn" data-action="approve-deployment">批准</button>';
            else if (item.status === "approved") actions = '<button class="mini-btn" data-action="apply-deployment">发布</button>';
            return `<tr data-deployment="${escapeHtml(item.deployment_id)}"><td>${escapeHtml(item.environment_key.toUpperCase())}</td><td>${String(item.curated_release_id).slice(0, 8)}</td><td>${escapeHtml(item.slot)}</td><td>${item.artifact_hash ? String(item.artifact_hash).slice(0, 10) : "—"}</td><td><span class="status-pill ${item.status === "active" ? "online" : item.status === "failed" ? "failed" : "unknown"}">${escapeHtml(statusLabel(item.status))}</span></td><td>${formatDate(item.started_at, true)}</td><td>${actions}</td></tr>`;
        }).join("") || '<tr class="empty-row"><td colspan="7">活动治理快照产生后，才能准备发布制品</td></tr>';
    }

    function renderObservability() {
        const data = state.observability || { metrics: [], alerts: [], lineage: [] };
        $("#healthMetrics").innerHTML = data.metrics.slice(0, 8).map(item => `<article class="metric-card"><span>${escapeHtml(item.metric_key)}</span><strong>${item.value_numeric ?? "—"}</strong><small>${escapeHtml(item.message)}</small></article>`).join("") || '<article class="metric-card"><span>状态</span><strong>—</strong><small>运行健康检查生成指标</small></article>';
        $("#alertList").innerHTML = data.alerts.map(item => `<div class="profile-issue ${item.severity === "critical" ? "error" : ""}" data-alert="${escapeHtml(item.alert_event_id)}"><span>${escapeHtml(statusLabel(item.severity))}</span><div><strong>${escapeHtml(item.message)}</strong><small>${formatDate(item.opened_at, true)} · ${escapeHtml(statusLabel(item.status))}</small></div>${item.status === "open" ? '<button class="mini-btn" data-action="ack-alert">确认</button>' : ""}</div>`).join("") || '<div class="profile-empty">暂无告警</div>';
        $("#lineageList").innerHTML = data.lineage.map(item => `<div class="profile-issue"><span>${escapeHtml(item.run_type)}</span><div><strong>${escapeHtml(item.source_asset)} → ${escapeHtml(item.target_asset)}</strong><small>${Number(item.row_count || 0).toLocaleString()} 行 · ${formatDate(item.occurred_at, true)}</small></div></div>`).join("") || '<div class="profile-empty">物化或发布成功后生成运行时血缘</div>';
    }

    function renderActions() {
        const data = state.actions || { definitions: [], invocations: [], applyEnabled: false };
        $("#actionGlobalState").textContent = data.applyEnabled ? "实际执行已开启" : "实际执行关闭";
        $("#actionGlobalState").classList.toggle("approved", data.applyEnabled);
        const trustedIdentity = data.identityMode === "trusted_headers";
        $("#actionSecuritySummary").innerHTML = `<div class="capability-chips"><span class="capability-chip ${trustedIdentity ? "" : "danger"}">可信身份 <strong>${trustedIdentity ? "反向代理" : "未配置，仅允许预演"}</strong></span><span class="capability-chip">定义数量 <strong>${data.definitions.length}</strong></span><span class="capability-chip">写入边界 <strong>Camstar API Only</strong></span></div>`;
        $("#actionCards").innerHTML = data.definitions.map(item => {
            const buttons = ['<button class="mini-btn" data-action="edit-action-definition">配置</button>', '<button class="mini-btn" data-action="plan-action">创建预演</button>'];
            if (item.status === "draft") buttons.push('<button class="mini-btn" data-action="review-action-definition">复核</button>');
            if (item.status === "reviewed") buttons.push('<button class="mini-btn" data-action="approve-action-definition">批准</button>');
            if (item.status === "approved") buttons.push('<button class="mini-btn" data-action="retire-action-definition">退役</button>');
            return `<article class="job-card" data-action-key="${escapeHtml(item.action_key)}"><div class="card-top"><div><p>${escapeHtml(item.object_class)} · ${escapeHtml(item.http_method)} · ${escapeHtml(item.origin)}</p><h3>${escapeHtml(item.title)}</h3></div><span class="status-pill ${item.enabled ? "online" : "unknown"}">${escapeHtml(statusLabel(item.status))} · v${item.version}</span></div><div class="card-details"><div class="detail-field"><span>API</span><strong>${escapeHtml(item.endpoint_path)}</strong></div><div class="detail-field"><span>角色</span><strong>${escapeHtml((item.allowed_roles || []).join(", ") || "尚未配置")}</strong></div><div class="detail-field"><span>审批</span><strong>${item.approval_required ? "双人审批" : "无需审批"}</strong></div><div class="detail-field"><span>补偿</span><strong>${escapeHtml(item.compensation_action_key || "未配置")}</strong></div></div><div class="card-actions"><small>禁止数据库直写</small><div class="card-action-buttons">${buttons.join("")}</div></div></article>`;
        }).join("") || '<article class="panel profile-empty">没有写死的演示 Action。请手工新增，或从本地 Camstar OpenAPI 选择性导入。</article>';
        $("#actionInvocationRows").innerHTML = data.invocations.map(item => {
            let actions = "—";
            if (item.status === "pending_approval") actions = '<button class="mini-btn" data-action="approve-action">批准</button>';
            else if (item.status === "approved") actions = '<button class="mini-btn" data-action="execute-action">执行</button>';
            else if (item.status === "succeeded" && data.definitions.find(definition => definition.action_key === item.action_key)?.compensation_action_key) actions = '<button class="mini-btn" data-action="compensate-action">发起补偿</button>';
            return `<tr data-invocation="${escapeHtml(item.invocation_id)}"><td>${escapeHtml(item.action_key)}</td><td>${escapeHtml(item.actor)}</td><td>${item.dry_run ? "预演" : "真实"}</td><td>${escapeHtml(item.idempotency_key)}</td><td><span class="status-pill ${item.status === "succeeded" ? "online" : item.status === "failed" ? "failed" : "unknown"}">${escapeHtml(statusLabel(item.status))}</span></td><td>${formatDate(item.started_at, true)}</td><td>${actions}</td></tr>`;
        }).join("") || '<tr class="empty-row"><td colspan="7">尚无 Action 调用</td></tr>';
    }

    function openActionPlanDialog(item) {
        $("#dialogTitle").textContent = item.title;
        $("#dialogKicker").textContent = "ACTION PLAN";
        const example = Object.fromEntries((item.input_schema?.required || []).map(key => [key, key === "changes" ? {} : ""]));
        $("#dialogFields").innerHTML = [
            field("idempotency_key", "幂等键", crypto.randomUUID(), { wide: true, help: "相同业务请求必须复用同一个幂等键" }),
            field("payload", "请求 JSON", JSON.stringify(example, null, 2), { type: "textarea", wide: true }),
            field("dry_run", "仅预演，不调用 Camstar", true, { type: "checkbox", wide: true, help: "申请人和角色只能由服务端可信身份提供，不能在页面填写" }),
        ].join("");
        state.dialogSubmit = async form => {
            const payload = JSON.parse(form.get("payload"));
            const result = await request(`/api/sync/actions/${encodeURIComponent(item.action_key)}/plan`, { method: "POST", body: JSON.stringify({ payload, idempotency_key: form.get("idempotency_key"), dry_run: form.get("dry_run") === "on" }) });
            toast(result.replayed ? "返回已有幂等调用" : `Action ${result.status}；未发生数据库直写`);
            await loadActions();
        };
        $("#editDialog").showModal();
    }

    function openActionDefinitionDialog(item = null) {
        const actionKey = item?.action_key || "camstar.custom.action";
        const compensationItems = [["", "不配置补偿"], ...(state.actions.definitions || []).filter(definition => definition.action_key !== actionKey).map(definition => [definition.action_key, `${definition.object_class} · ${definition.title}`])];
        $("#dialogTitle").textContent = item ? `配置 ${item.title}` : "新增通用 Action";
        $("#dialogKicker").textContent = "ACTION DEFINITION";
        $("#dialogFields").innerHTML = [
            field("action_key", "Action 稳定 ID", actionKey, { wide: true, readonly: Boolean(item) }),
            field("title", "显示名称", item?.title || "", { wide: true }),
            field("object_class", "本体对象", item?.object_class || "", { placeholder: "Product / Workflow" }),
            field("http_method", "HTTP 方法", item?.http_method || "POST", { type: "select", items: [["POST", "POST"], ["PUT", "PUT"], ["PATCH", "PATCH"], ["DELETE", "DELETE"]] }),
            field("endpoint_path", "Camstar API 相对路径", item?.endpoint_path || "/api/Objects/{key}", { wide: true, help: "只允许相对路径，禁止数据库 SQL 和外部完整 URL" }),
            field("allowed_roles", "允许角色（逗号分隔）", (item?.allowed_roles || []).join(","), { wide: true }),
            field("input_schema", "输入 JSON Schema", JSON.stringify(item?.input_schema || { type: "object", required: ["key"], properties: { key: { type: "string" } } }, null, 2), { type: "textarea", wide: true }),
            field("path_parameters", "路径参数（逗号分隔）", (item?.config?.pathParameters || []).join(",")),
            field("timeout_seconds", "超时秒数", item?.timeout_seconds || 60, { type: "number" }),
            field("max_attempts", "最大尝试次数", item?.retry_policy?.maxAttempts || 1, { type: "number" }),
            field("compensation_action_key", "补偿 Action", item?.compensation_action_key || "", { type: "select", items: compensationItems }),
            field("approval_required", "真实执行需要双人审批", item?.approval_required !== false, { type: "checkbox", wide: true }),
            field("description", "业务说明", item?.description || "", { type: "textarea", wide: true }),
        ].join("");
        state.dialogSubmit = async form => {
            const key = String(form.get("action_key") || "").trim();
            const payload = {
                title: form.get("title"), description: form.get("description") || null,
                object_class: form.get("object_class"), endpoint_path: form.get("endpoint_path"),
                http_method: form.get("http_method"), input_schema: JSON.parse(form.get("input_schema")),
                allowed_roles: String(form.get("allowed_roles") || "").split(",").map(value => value.trim()).filter(Boolean),
                approval_required: form.get("approval_required") === "on",
                timeout_seconds: Number(form.get("timeout_seconds")),
                retry_policy: { maxAttempts: Number(form.get("max_attempts")), retryStatuses: [429, 502, 503, 504] },
                compensation_action_key: form.get("compensation_action_key") || null,
                config: { profileKey: "opcenter2607-core", pathParameters: String(form.get("path_parameters") || "").split(",").map(value => value.trim()).filter(Boolean) },
            };
            await request(`/api/sync/actions/definitions/${encodeURIComponent(key)}`, { method: "PUT", body: JSON.stringify(payload) });
            toast("Action 已保存为草案；真实执行需要可信身份下的复核与独立批准");
            await loadActions();
        };
        $("#editDialog").showModal();
    }

    async function openOpenApiImportDialog() {
        const sources = (await request("/api/sync/actions/openapi-sources")).items;
        if (!sources.length) { toast("没有找到本地 Camstar OpenAPI 文件", true); return; }
        $("#dialogTitle").textContent = "从 Camstar OpenAPI 导入";
        $("#dialogKicker").textContent = "SELECTIVE IMPORT";
        $("#dialogFields").innerHTML = [
            field("source_file", "对象 API", sources[0].sourceFile, { type: "select", items: sources.map(source => [source.sourceFile, source.objectClass]) }),
            field("operation_id", "写操作", "", { type: "select", items: [] }),
            field("import_note", "导入规则", "只导入选中的一个 POST/PUT/PATCH/DELETE，并保持草案和禁用状态。不会批量生成所有对象 CRUD。", { type: "textarea", wide: true, readonly: true }),
        ].join("");
        const loadOperations = async () => {
            const candidates = (await request(`/api/sync/actions/openapi-candidates?source_file=${encodeURIComponent($("#dialog-source_file").value)}`)).items;
            $("#dialog-operation_id").innerHTML = candidates.map(candidate => `<option value="${escapeHtml(candidate.operationId)}">${escapeHtml(`${candidate.httpMethod} ${candidate.endpointPath}`)}</option>`).join("");
        };
        $("#dialog-source_file").addEventListener("change", () => loadOperations().catch(error => toast(error.message, true)));
        await loadOperations();
        state.dialogSubmit = async form => {
            await request("/api/sync/actions/openapi-import", { method: "POST", body: JSON.stringify({ source_file: form.get("source_file"), operation_id: form.get("operation_id") }) });
            toast("OpenAPI 写操作已作为禁用草案导入；请配置角色后再复核批准");
            await loadActions();
        };
        $("#editDialog").showModal();
    }

    function openActorDialog(title, submit) {
        $("#dialogTitle").textContent = title;
        $("#dialogKicker").textContent = "AUDITED OPERATION";
        $("#dialogFields").innerHTML = field("actor", "操作人", "", { wide: true, placeholder: "工号或用户名" });
        state.dialogSubmit = async form => submit(form.get("actor"));
        $("#editDialog").showModal();
    }

    function openSchemaChangeDialog() {
        const schema = state.contractSchema;
        if (!schema) { toast("字段目录尚未加载", true); return; }
        const fields = schema.fields || [];
        $("#dialogTitle").textContent = `${schema.contract.class_name} Schema 变更申请`;
        $("#dialogKicker").textContent = "SCHEMA CHANGE";
        $("#dialogFields").innerHTML = [
            field("title", "申请标题", "", { wide: true, placeholder: "例如：增加产品品牌字段" }),
            field("operation", "操作类型", "add_field", { type: "select", items: [["add_field", "增加字段"], ["deprecate_field", "废弃字段"], ["retire_field", "退役字段"], ["rename_field", "重命名字段"], ["change_type", "修改类型"], ["change_required", "修改必填约束"], ["change_key", "修改键角色"], ["change_source", "修改源字段"], ["change_transform", "修改转换逻辑"]] }),
            field("existing_field", "现有字段", fields[0]?.field_key || "", { type: "select", items: fields.map(item => [item.field_key, `${item.target_field} · ${item.data_type}`]) }),
            field("new_field_key", "新字段稳定ID", `${schema.contract.contract_key}:new-field`, { help: "发布后不应随显示名称变化" }),
            field("target_field", "目标字段名", "", { placeholder: "brandName" }),
            field("source_column", "Camstar 源列", "", { placeholder: "BrandName" }),
            field("data_type", "目标类型", "String", { type: "select", items: [["String", "String"], ["Integer", "Integer"], ["Float", "Float"], ["Boolean", "Boolean"], ["DateTime", "DateTime"], ["Navigation", "Navigation"]] }),
            field("field_role", "字段角色", "attribute", { type: "select", items: [["attribute", "属性"], ["business_key", "业务键"], ["primary_key", "主键"], ["freshness", "增量水位"], ["navigation", "关联字段"]] }),
            field("required", "设为必填字段", false, { type: "checkbox", help: "新增必填字段必须提供默认值和回填方案" }),
            field("default_expression", "默认值表达式", "", { placeholder: "仅治理执行器可解析的表达式" }),
            field("transform_expression", "转换表达式", "", { wide: true }),
            field("migration_strategy", "迁移方案", "", { wide: true, help: "有条件或破坏性变更必填" }),
            field("rollback_strategy", "回滚方案", "", { wide: true, help: "破坏性变更必填" }),
            field("description", "说明", "", { wide: true }),
        ].join("");
        const updateChangeFields = () => {
            const adding = $("#dialog-operation").value === "add_field";
            $('[data-field-name="existing_field"]', $("#dialogFields")).hidden = adding;
            $('[data-field-name="new_field_key"]', $("#dialogFields")).hidden = !adding;
        };
        $("#dialog-operation").addEventListener("change", updateChangeFields);
        updateChangeFields();
        state.dialogSubmit = async form => {
            const operation = form.get("operation");
            const adding = operation === "add_field";
            const afterState = {};
            if (form.get("target_field")) afterState.target_field = form.get("target_field");
            if (form.get("source_column")) afterState.source_column = form.get("source_column");
            if (form.get("data_type")) afterState.data_type = form.get("data_type");
            if (form.get("field_role")) afterState.field_role = form.get("field_role");
            afterState.required = form.get("required") === "on";
            afterState.nullable = !afterState.required;
            if (form.get("default_expression")) afterState.default_expression = form.get("default_expression");
            if (form.get("transform_expression")) afterState.transform_expression = form.get("transform_expression");
            const result = await request(`/api/sync/profiles/${encodeURIComponent(state.activeProfile.profile.profile_key)}/schema-changes`, { method: "POST", body: JSON.stringify({ contract_key: schema.contract.contract_key, title: form.get("title"), description: form.get("description") || null, migration_strategy: form.get("migration_strategy") || null, rollback_strategy: form.get("rollback_strategy") || null, operations: [{ operation, field_key: adding ? form.get("new_field_key") : form.get("existing_field"), after_state: Object.keys(afterState).length ? afterState : null }] }) });
            toast(result.readyForReview ? `变更分析完成：${compatibilityLabel(result.compatibility)}` : `变更已保存为草案：${result.blockers.join("；")}`, !result.readyForReview);
            await loadSchemaEvolution(schema.contract.contract_key);
        };
        $("#editDialog").showModal();
    }

    function projectionLines(item) {
        return (item?.fields || []).map(fieldItem => [
            fieldItem.source_path,
            fieldItem.target_field,
            fieldItem.data_type || "String",
            fieldItem.required ? "required" : "optional",
        ].join(", ")).join("\n");
    }

    function openAttributeProjectionDialog(item = null) {
        const contracts = state.governance?.contracts || [];
        if (!contracts.length) { toast("请先建立 Camstar 数据契约", true); return; }
        const target = contracts.find(contract => contract.contract_key === item?.target_contract_key) || contracts[0];
        const projectionKey = item?.projection_key || `projection-${crypto.randomUUID()}`;
        $("#dialogTitle").textContent = item ? `编辑 ${item.title}` : "新增通用属性投影";
        $("#dialogKicker").textContent = "ATTRIBUTE PROJECTION";
        $("#dialogFields").innerHTML = [
            field("projection_key", "规则稳定 ID", projectionKey, { wide: true, readonly: Boolean(item), help: "用于版本、审批和血缘追踪；创建后不可修改" }),
            field("title", "规则名称", item?.title || `${target.class_name} 关联属性`, { wide: true }),
            field("target_contract_key", "目标本体对象", target.contract_key, { type: "select", items: contracts.map(contract => [contract.contract_key, `${contract.class_name} · ${contract.source_schema}.${contract.source_table}`]) }),
            field("cardinality", "关联基数", item?.cardinality || "one", { type: "select", items: [["one", "一对一"], ["many", "一对多"]] }),
            field("source_schema", "关联表 Schema", item?.source_schema || target.source_schema, { placeholder: "dbo / CAMSTAR" }),
            field("source_table", "关联表", item?.source_table || "", { placeholder: "A_ProductDetails" }),
            field("source_alias", "根表别名", item?.source_alias || "src", { help: "字段路径使用 别名.列名，例如 src.ProductId" }),
            field("preview_row_limit", "预览主对象数", item?.preview_row_limit || 200, { type: "number", help: "只读采样上限；不会扫描整个主表" }),
            field("owner_mapping", "主对象关联键（每行：目标列 = 来源路径）", (item?.owner_mapping || [{ targetColumn: target.primary_key_columns?.[0] || "InstanceId", sourcePath: "src.InstanceId" }]).map(mapping => `${mapping.targetColumn} = ${mapping.sourcePath}`).join("\n"), { type: "textarea", wide: true, help: "支持复合键，一行一个。例如：ProductId = src.ProductId" }),
            field("field_mappings", "投影字段（每行：来源路径, 目标属性, 类型, 是否必填）", projectionLines(item) || "src.AttributeValue, extendedAttribute, String, optional", { type: "textarea", wide: true, help: "类型：String / Integer / Float / Boolean / DateTime / Date / Navigation；是否必填写 required 或 optional" }),
            field("multiple_match_policy", "多值处理", item?.multiple_match_policy || "reject", { type: "select", items: [["reject", "发现多条则隔离"], ["first", "按排序取第一条"], ["latest", "按排序取最新一条"], ["array", "合并为数组"]] }),
            field("missing_policy", "无匹配处理", item?.missing_policy || "null", { type: "select", items: [["null", "保留空值"], ["quarantine", "隔离主对象"], ["reject", "拒绝该对象"]] }),
            field("collision_policy", "与主表属性同名时", item?.collision_policy || "reject", { type: "select", items: [["reject", "隔离并保留主表值"], ["overwrite", "使用关联表值覆盖"], ["coalesce", "仅主表为空时补齐"]] }),
            field("join_plan", "高级：多跳 Join JSON", JSON.stringify(item?.join_plan || [], null, 2), { type: "textarea", wide: true, help: '可选。示例：[{"joinType":"left","schema":"dbo","table":"A_Definition","alias":"def","left":"src.DefId","right":"def.InstanceId"}]' }),
            field("row_filters", "高级：过滤条件 JSON", JSON.stringify(item?.row_filters || [], null, 2), { type: "textarea", wide: true, help: '可选。示例：[{"path":"src.IsActive","operator":"eq","value":1}]' }),
            field("order_by", "高级：确定性排序 JSON", JSON.stringify(item?.order_by || [], null, 2), { type: "textarea", wide: true, help: 'first/latest 必填。示例：[{"path":"src.LastUpdatedDate","direction":"desc"}]' }),
            field("description", "业务说明", item?.description || "", { type: "textarea", wide: true }),
            field("enabled", "启用此投影", item?.enabled !== false, { type: "checkbox", wide: true, help: "启用的规则必须完成源预览、复核和批准后才能物化" }),
        ].join("");
        state.dialogSubmit = async form => {
            const key = String(form.get("projection_key") || "").trim();
            const ownerMapping = String(form.get("owner_mapping") || "").split(/\r?\n/).map(line => line.trim()).filter(Boolean).map(line => {
                const separator = line.indexOf("=");
                if (separator < 1) throw new Error(`关联键格式错误：${line}`);
                return { targetColumn: line.slice(0, separator).trim(), sourcePath: line.slice(separator + 1).trim() };
            });
            const fields = String(form.get("field_mappings") || "").split(/\r?\n/).map(line => line.trim()).filter(Boolean).map((line, index) => {
                const parts = line.split(",").map(value => value.trim());
                if (parts.length < 2) throw new Error(`投影字段格式错误：${line}`);
                const existing = (item?.fields || []).find(value => value.target_field === parts[1]);
                return {
                    field_key: existing?.field_key || `${key}:${parts[1]}`,
                    source_path: parts[0], target_field: parts[1], data_type: parts[2] || "String",
                    required: String(parts[3] || "optional").toLowerCase() === "required",
                    ontology_property: existing?.ontology_property || null,
                    lifecycle_status: "active", ordinal_position: (index + 1) * 10, config: {},
                };
            });
            const parseJsonArray = name => {
                let value;
                try { value = JSON.parse(String(form.get(name) || "[]")); }
                catch (_) { throw new Error(`${name} 必须是合法 JSON`); }
                if (!Array.isArray(value)) throw new Error(`${name} 必须是 JSON 数组`);
                return value;
            };
            const payload = {
                target_contract_key: form.get("target_contract_key"), title: form.get("title"),
                description: form.get("description") || null,
                source_schema: form.get("source_schema"), source_table: form.get("source_table"),
                source_alias: form.get("source_alias") || "src", owner_mapping: ownerMapping,
                join_plan: parseJsonArray("join_plan"), row_filters: parseJsonArray("row_filters"),
                cardinality: form.get("cardinality"), multiple_match_policy: form.get("multiple_match_policy"),
                missing_policy: form.get("missing_policy"), collision_policy: form.get("collision_policy"), order_by: parseJsonArray("order_by"),
                preview_row_limit: Number(form.get("preview_row_limit")), enabled: form.get("enabled") === "on",
                fields, config: { ...(item?.config || {}), refreshMode: "release_and_owner_change" },
            };
            await request(`/api/sync/profiles/opcenter2607-core/attribute-projections/${encodeURIComponent(key)}`, { method: "PUT", body: JSON.stringify(payload) });
            toast("属性投影已保存为草案；请先执行只读源预览");
            await Promise.all([loadAttributeProjections(), loadMaterialization()]);
        };
        $("#editDialog").showModal();
    }

    function openDataContractDialog(item) {
        $("#dialogTitle").textContent = `${item.class_name} 数据契约`;
        $("#dialogKicker").textContent = "DATA CONTRACT";
        $("#dialogFields").innerHTML = [
            field("source", "物理来源", `${item.source_schema}.${item.source_table}`, { readonly: true, wide: true }),
            field("primary_keys", "主键", (item.primary_key_columns || []).join(", "), { readonly: true }),
            field("business_key_columns", "业务键（逗号分隔）", (item.business_key_columns || []).join(", "), { help: "用于业务唯一性检查，不替代物理主键" }),
            field("required_columns", "必填字段（逗号分隔）", (item.required_columns || []).join(", "), { wide: true }),
            field("freshness_column", "增量时间列", item.freshness_column || "", { help: "为空表示尚未确认可靠水位列" }),
            field("preview_row_limit", "治理预览行数上限", item.preview_row_limit, { type: "number" }),
            field("publication_layer", "目标层", item.publication_layer, { type: "select", items: [["core", "核心层"], ["context", "上下文层"], ["reference", "参考层"], ["quarantine", "隔离层"]] }),
            field("status", "审核状态", item.status, { type: "select", items: [["draft", "草案"], ["reviewed", "已复核"], ["approved", "已批准"], ["retired", "已退役"]] }),
        ].join("");
        const parseColumns = value => String(value || "").split(",").map(column => column.trim()).filter(Boolean);
        state.dialogSubmit = async form => {
            await request(`/api/sync/data-contracts/${encodeURIComponent(item.contract_key)}`, { method: "PUT", body: JSON.stringify({ status: form.get("status"), business_key_columns: parseColumns(form.get("business_key_columns")), required_columns: parseColumns(form.get("required_columns")), freshness_column: form.get("freshness_column") || null, preview_row_limit: Number(form.get("preview_row_limit")), publication_layer: form.get("publication_layer") }) });
            toast(`${item.class_name} 数据契约已保存`); await loadGraphProfiles();
        };
        $("#editDialog").showModal();
    }

    function openRelationshipContractDialog(item) {
        $("#dialogTitle").textContent = `${item.relationship_name} 关系契约`;
        $("#dialogKicker").textContent = "SEMANTIC CONTRACT";
        $("#dialogFields").innerHTML = [
            field("source", "源对象与字段", `${item.source_class}.${(item.source_columns || []).join(",")}`, { readonly: true, wide: true }),
            field("target", "目标对象与字段", `${item.target_class}.${(item.target_columns || []).join(",")}`, { readonly: true, wide: true }),
            field("semantic_role", "业务语义", item.semantic_role, { wide: true }),
            field("required_context", "作为必需上下文", item.required_context, { type: "checkbox", help: "缺少或无法解析目标时阻止进入正式图谱" }),
            field("status", "审核状态", item.status, { type: "select", items: [["draft", "草案"], ["reviewed", "已复核"], ["approved", "已批准"], ["retired", "已退役"]] }),
        ].join("");
        state.dialogSubmit = async form => {
            await request(`/api/sync/relationship-contracts/${encodeURIComponent(item.relationship_contract_key)}`, { method: "PUT", body: JSON.stringify({ status: form.get("status"), semantic_role: form.get("semantic_role"), required_context: form.get("required_context") === "on" }) });
            toast(`${item.relationship_name} 关系契约已保存`); await loadGraphProfiles();
        };
        $("#editDialog").showModal();
    }

    function openGraphProfileDialog() {
        const profile = state.activeProfile.profile;
        $("#dialogTitle").textContent = "配置业务图谱边界";
        $("#dialogKicker").textContent = "CONTEXT BUDGET";
        $("#dialogFields").innerHTML = [
            field("title", "配置名称", profile.title, { wide: true }),
            field("description", "说明", profile.description || "", { wide: true }),
            field("max_depth", "最大关系深度", profile.max_depth, { type: "number", help: "建议 1～3；层数越大，扇出风险越高" }),
            field("max_context_nodes_per_seed", "每个种子的上下文节点上限", profile.max_context_nodes_per_seed, { type: "number" }),
            field("max_total_nodes_per_run", "单次运行总节点上限", profile.max_total_nodes_per_run, { type: "number" }),
            field("enabled", "启用此业务图谱", profile.enabled, { type: "checkbox", wide: true }),
        ].join("");
        state.dialogSubmit = async form => {
            await request(`/api/sync/profiles/${encodeURIComponent(profile.profile_key)}`, { method: "PUT", body: JSON.stringify({ title: form.get("title"), description: form.get("description") || null, max_depth: Number(form.get("max_depth")), max_context_nodes_per_seed: Number(form.get("max_context_nodes_per_seed")), max_total_nodes_per_run: Number(form.get("max_total_nodes_per_run")), enabled: form.get("enabled") === "on" }) });
            toast("业务图谱边界已保存"); await loadGraphProfiles();
        };
        $("#editDialog").showModal();
    }

    function openProfileClassDialog(item, adding = false) {
        $("#dialogTitle").textContent = adding ? "添加业务对象" : `配置 ${item.class_name}`;
        $("#dialogKicker").textContent = "OBJECT ROLE";
        const available = state.profileCandidates.classes.filter(candidate => !candidate.configured);
        $("#dialogFields").innerHTML = [
            adding ? field("class_name", "本体对象", available[0]?.class_name || "", { type: "select", items: available.map(candidate => [candidate.class_name, `${candidate.class_name} · ${Number(candidate.approximate_rows || 0).toLocaleString()} 行`]), wide: true }) : field("class_name", "本体对象", item.class_name, { readonly: true, wide: true }),
            field("role", "业务角色", item.role || "context", { type: "select", items: [["core", "核心对象"], ["context", "上下文对象"], ["reference", "参考对象"], ["on_demand", "按需对象"], ["excluded", "不导入"]] }),
            field("orphan_policy", "孤立数据策略", item.orphan_policy || "quarantine", { type: "select", items: [["quarantine", "隔离等待上下文"], ["reject", "拒绝发布"], ["referenced_only", "仅被引用时导入"], ["allow", "允许孤立"]] }),
            field("max_instances_per_run", "单次对象上限", item.max_instances_per_run || "", { type: "number", help: "留空表示仅受全局预算限制" }),
            field("priority", "加载优先级", item.priority ?? 100, { type: "number" }),
            field("seed_enabled", "作为闭包种子", item.seed_enabled || false, { type: "checkbox", help: "只有核心对象可以作为种子" }),
            field("enabled", "启用此对象", item.enabled !== false, { type: "checkbox" }),
            field("review_status", "审核状态", item.review_status || "draft", { type: "select", items: [["draft", "草案"], ["reviewed", "已复核"], ["approved", "已批准"]] }),
        ].join("");
        state.dialogSubmit = async form => {
            const className = form.get("class_name");
            await request(`/api/sync/profiles/${encodeURIComponent(state.activeProfile.profile.profile_key)}/classes/${encodeURIComponent(className)}`, { method: "PUT", body: JSON.stringify({ role: form.get("role"), orphan_policy: form.get("orphan_policy"), seed_enabled: form.get("seed_enabled") === "on", max_instances_per_run: form.get("max_instances_per_run") ? Number(form.get("max_instances_per_run")) : null, priority: Number(form.get("priority")), enabled: form.get("enabled") === "on", review_status: form.get("review_status") }) });
            toast(`${className} 的业务角色已保存`); await loadGraphProfiles();
        };
        $("#editDialog").showModal();
    }

    function openProfileRelationshipDialog(item, adding = false) {
        const candidates = state.profileCandidates.relationships.filter(candidate => !candidate.configured);
        const initial = adding ? candidates[0] : item;
        if (!initial) { toast("当前对象没有可添加的本体关系", true); return; }
        $("#dialogTitle").textContent = adding ? "添加业务关系" : `配置 ${item.relationship_name}`;
        $("#dialogKicker").textContent = "RELATIONSHIP STRENGTH";
        const relationshipKey = value => `${value.source_class}|${value.relationship_name}|${value.target_class}`;
        $("#dialogFields").innerHTML = [
            adding ? field("relationship_key", "本体关系", relationshipKey(initial), { type: "select", items: candidates.map(candidate => [relationshipKey(candidate), `${candidate.source_class} —${candidate.relationship_name}→ ${candidate.target_class} · ${candidate.mapping_status}`]), wide: true }) : field("relationship_key", "本体关系", relationshipKey(item), { readonly: true, wide: true }),
            field("strength", "业务强度", item?.strength || "context", { type: "select", items: [["core", "核心关联"], ["context", "上下文关联"], ["weak", "弱关联"], ["on_demand", "按需关联"]] }),
            field("direction", "扩展方向", item?.direction || "outgoing", { type: "select", items: [["outgoing", "正向"], ["incoming", "反向"], ["both", "双向"]] }),
            field("max_targets_per_source", "每个源对象最多目标数", item?.max_targets_per_source || 50, { type: "number" }),
            field("max_depth", "该关系最大深度", item?.max_depth || "", { type: "number", help: "留空时使用图谱全局深度" }),
            field("traverse", "用于上下文扩展", item?.traverse || false, { type: "checkbox", help: "弱关联不能开启；仅已解析的物理关系可执行" }),
            field("required_context", "作为必需上下文", item?.required_context || false, { type: "checkbox", help: "缺失时会按对象的孤立策略处理" }),
            field("enabled", "启用此关系", item?.enabled !== false, { type: "checkbox" }),
            field("review_status", "审核状态", item?.review_status || "draft", { type: "select", items: [["draft", "草案"], ["reviewed", "已复核"], ["approved", "已批准"]] }),
        ].join("");
        state.dialogSubmit = async form => {
            const [sourceClass, relationshipName, targetClass] = form.get("relationship_key").split("|");
            await request(`/api/sync/profiles/${encodeURIComponent(state.activeProfile.profile.profile_key)}/relationships/${encodeURIComponent(sourceClass)}/${encodeURIComponent(relationshipName)}/${encodeURIComponent(targetClass)}`, { method: "PUT", body: JSON.stringify({ strength: form.get("strength"), required_context: form.get("required_context") === "on", traverse: form.get("traverse") === "on", direction: form.get("direction"), max_depth: form.get("max_depth") ? Number(form.get("max_depth")) : null, max_targets_per_source: Number(form.get("max_targets_per_source")), enabled: form.get("enabled") === "on", review_status: form.get("review_status") }) });
            toast("关系业务策略已保存"); await loadGraphProfiles();
        };
        $("#editDialog").showModal();
    }

    function renderRuns() {
        $("#runRows").innerHTML = state.runs.map(item => `
            <tr><td title="${item.run_id}">${escapeHtml(String(item.run_id).slice(0, 8))}</td><td>${escapeHtml(item.job_name)}</td><td><span class="status-pill ${item.status}">${statusLabel(item.status)}</span></td><td>${escapeHtml(item.trigger_type)}</td><td>${formatDate(item.started_at)}</td><td>${duration(item.started_at, item.finished_at)}</td><td>${Number(item.row_count || 0).toLocaleString()}</td><td>${Number(item.triple_count || 0).toLocaleString()}</td></tr>
        `).join("") || '<tr class="empty-row"><td colspan="8">尚无同步运行记录</td></tr>';
    }

    function settingValue(value) {
        if (typeof value === "string") return value;
        return JSON.stringify(value);
    }

    function renderSettings() {
        $("#settingList").innerHTML = state.settings.map(item => `
            <div class="setting-row" data-setting="${escapeHtml(item.setting_key)}">
                <div class="setting-copy"><strong>${escapeHtml(item.setting_key)}</strong><small>${escapeHtml(item.description || "")}</small></div>
                <input class="field-input" value="${escapeHtml(settingValue(item.value))}" ${item.editable ? "" : "disabled"}>
                ${item.editable ? '<button class="mini-btn" data-action="save-setting">保存</button>' : '<span class="status-pill">受保护</span>'}
            </div>`).join("");
        renderMenuSettings();
    }

    function renderMenuSettings() {
        $("#menuSettings").innerHTML = state.navigation.map(item => `
            <div class="menu-setting-row" data-menu="${escapeHtml(item.menu_key)}">
                <input class="field-input menu-label" value="${escapeHtml(item.label_zh)}" aria-label="中文菜单名">
                <input class="field-input menu-order" type="number" min="0" max="10000" value="${item.sort_order}" aria-label="排序">
                <input class="toggle menu-enabled" type="checkbox" ${item.enabled ? "checked" : ""} aria-label="启用">
                <button class="mini-btn" data-action="save-menu">保存</button>
            </div>`).join("");
    }

    function field(name, label, value = "", options = {}) {
        const className = options.wide ? "dialog-field wide" : "dialog-field";
        const help = options.help ? `<small class="field-help">${escapeHtml(options.help)}</small>` : "";
        const attributes = `${options.hidden ? " hidden" : ""} data-field-name="${escapeHtml(name)}"`;
        if (options.type === "select") {
            return `<div class="${className}"${attributes}><label id="dialog-${name}-label" for="dialog-${name}">${label}</label><select id="dialog-${name}" name="${name}">${options.items.map(([key, text]) => `<option value="${escapeHtml(key)}" ${key === value ? "selected" : ""}>${escapeHtml(text)}</option>`).join("")}</select>${help}</div>`;
        }
        if (options.type === "checkbox") {
            return `<div class="${className} switch-field"${attributes}><label class="switch-row"><span class="switch-copy"><strong>${label}</strong><small>${escapeHtml(options.help || "关闭后不会参与自动测试和同步任务")}</small></span><input class="switch-input" type="checkbox" name="${name}" ${value ? "checked" : ""}><span class="switch-control" aria-hidden="true"></span></label></div>`;
        }
        if (options.type === "textarea") {
            return `<div class="${className}"${attributes}><label id="dialog-${name}-label" for="dialog-${name}">${label}</label><textarea id="dialog-${name}" name="${name}" placeholder="${escapeHtml(options.placeholder || "")}">${escapeHtml(value ?? "")}</textarea>${help}</div>`;
        }
        return `<div class="${className}"${attributes}><label id="dialog-${name}-label" for="dialog-${name}">${label}</label><input id="dialog-${name}" name="${name}" type="${options.type || "text"}" value="${escapeHtml(value ?? "")}" placeholder="${escapeHtml(options.placeholder || "")}" ${options.readonly ? "readonly" : ""}>${help}</div>`;
    }

    function openConnectionDialog(item) {
        const isSource = item.connection_key === "camstar-source";
        const config = item.config || {};
        $("#dialogTitle").textContent = isSource ? "编辑 Camstar 数据源" : `编辑 ${item.display_name}`;
        $("#dialogKicker").textContent = isSource ? "DATABASE CONNECTION" : "CONNECTION PROFILE";
        const fields = [field("display_name", "显示名称", item.display_name, { wide: true })];
        if (isSource) {
            fields.push(
                field("kind", "数据库类型", item.kind, { type: "select", items: [["camstar_sqlserver", "SQL Server"], ["camstar_oracle", "Oracle"]] }),
                field("endpoint", "主机与端口", item.endpoint, { placeholder: "db.example.com:1433", help: "SQL Server 默认 1433；Oracle 默认 1521" }),
                field("database_name", "数据库名称", item.database_name || "", { placeholder: "CamstarPRD" }),
                field("source_schema", "Oracle Schema", config.schema || "", { placeholder: "CAMSTAR", hidden: item.kind !== "camstar_oracle" }),
                field("oracle_connect_mode", "Oracle 连接标识", config.oracleConnectMode || "service_name", { type: "select", items: [["service_name", "Service Name"], ["sid", "SID"]], hidden: item.kind !== "camstar_oracle" }),
            );
        } else {
            fields.push(
                field("endpoint", "Endpoint", item.endpoint, { wide: true }),
                field("database_name", "数据库 / Graphmart URI", item.database_name || "", { wide: true }),
            );
        }
        fields.push(
            field("username", "用户名", item.username || ""),
            field("enabled", "启用此连接", item.enabled, { type: "checkbox", wide: true }),
        );
        $("#dialogFields").innerHTML = fields.join("");
        let previousSourceKind = item.kind;
        const updateSourceFields = () => {
            if (!isSource) return;
            const nextSourceKind = $("#dialog-kind").value;
            const oracle = nextSourceKind === "camstar_oracle";
            if (nextSourceKind !== previousSourceKind) {
                const endpoint = $("#dialog-endpoint");
                if (oracle && endpoint.value.endsWith(":1433")) endpoint.value = `${endpoint.value.slice(0, -5)}:1521`;
                if (!oracle && endpoint.value.endsWith(":1521")) endpoint.value = `${endpoint.value.slice(0, -5)}:1433`;
                const displayName = $("#dialog-display_name");
                if (["Camstar SQL Server", "Camstar Oracle"].includes(displayName.value)) {
                    displayName.value = oracle ? "Camstar Oracle" : "Camstar SQL Server";
                }
                previousSourceKind = nextSourceKind;
            }
            $$('[data-field-name="source_schema"], [data-field-name="oracle_connect_mode"]', $("#dialogFields")).forEach(element => { element.hidden = !oracle; });
            $("#dialog-database_name-label").textContent = oracle ? "Service Name / SID" : "数据库名称";
            $("#dialog-database_name").placeholder = oracle ? "ORCLPDB1" : "CamstarPRD";
            $("#dialog-endpoint").placeholder = oracle ? "db.example.com:1521" : "db.example.com:1433";
        };
        if (isSource) {
            $("#dialog-kind").addEventListener("change", updateSourceFields);
            updateSourceFields();
        }
        state.dialogSubmit = async (form) => {
            const kind = isSource ? form.get("kind") : item.kind;
            const nextConfig = isSource ? {
                ...config,
                schema: form.get("source_schema") || null,
                oracleConnectMode: form.get("oracle_connect_mode") || "service_name",
            } : config;
            const payload = {
                kind,
                display_name: form.get("display_name"), endpoint: form.get("endpoint"),
                database_name: form.get("database_name") || null, username: form.get("username") || null,
                enabled: form.get("enabled") === "on", config: nextConfig,
            };
            await request(`/api/sync/connections/${encodeURIComponent(item.connection_key)}`, { method: "PUT", body: JSON.stringify(payload) });
            toast("连接配置已保存，建议立即执行连接测试");
            await loadConnections(); await loadOverview();
        };
        $("#editDialog").showModal();
    }

    function openJobDialog(item) {
        $("#dialogTitle").textContent = `配置 ${item.title}`;
        $("#dialogKicker").textContent = "SYNC JOB";
        $("#dialogFields").innerHTML = [
            field("title", "任务名称", item.title, { wide: true }),
            field("mode", "同步模式", item.mode, { type: "select", items: [["atomic_snapshot", "原子全量快照"], ["partitioned_incremental", "分区增量"]] }),
            field("schedule", "Cron 表达式", item.schedule || ""),
            field("timezone", "时区", item.timezone),
            field("retention_success", "成功版本保留数", item.retention_success, { type: "number" }),
            field("enabled", "启用此任务", item.enabled, { type: "checkbox" }),
        ].join("");
        state.dialogSubmit = async (form) => {
            const payload = {
                title: form.get("title"), mode: form.get("mode"), schedule: form.get("schedule") || null,
                timezone: form.get("timezone"), retention_success: Number(form.get("retention_success")),
                enabled: form.get("enabled") === "on",
            };
            await request(`/api/sync/jobs/${encodeURIComponent(item.job_name)}`, { method: "PUT", body: JSON.stringify(payload) });
            toast("同步任务配置已保存"); await loadJobs(); await loadOverview();
        };
        $("#editDialog").showModal();
    }

    function openTablePolicyDialog(item) {
        const strategy = item.strategy || item.recommended_strategy || "snapshot";
        $("#dialogTitle").textContent = `${item.class_name} 同步策略`;
        $("#dialogKicker").textContent = "LARGE TABLE POLICY";
        $("#dialogFields").innerHTML = [
            field("strategy", "同步策略", strategy, { type: "select", items: [["snapshot", "全量快照"], ["watermark", "水位增量"], ["append_only", "追加增量"], ["cdc", "CDC"], ["excluded", "不导入"]] }),
            field("batch_rows", "每批读取行数", item.batch_rows || 10000, { type: "number", help: "建议 10,000～100,000；宽表使用更小批次" }),
            field("watermark_column", "水位列", item.watermark_column || "", { placeholder: "LastUpdatedDate", help: "水位增量和追加增量必须填写" }),
            field("partition_column", "分区列", item.partition_column || "", { placeholder: "TxnDate / 主键" }),
            field("target_shard_mb", "RDF 分片目标大小（MB）", Math.round(Number(item.target_shard_bytes || 67108864) / 1048576), { type: "number" }),
            field("hot_window_days", "热数据窗口（天）", item.hot_window_days || "", { type: "number", help: "留空表示不限制历史窗口" }),
            field("enabled", "启用此表策略", item.enabled !== false, { type: "checkbox", wide: true, help: "关闭后此表不会进入同步批次" }),
        ].join("");
        const updatePolicyFields = () => {
            const selected = $("#dialog-strategy").value;
            const needsWatermark = ["watermark", "append_only"].includes(selected);
            $('[data-field-name="watermark_column"]', $("#dialogFields")).classList.toggle("required-field", needsWatermark);
        };
        $("#dialog-strategy").addEventListener("change", updatePolicyFields);
        updatePolicyFields();
        state.dialogSubmit = async (form) => {
            const payload = {
                strategy: form.get("strategy"),
                watermark_column: form.get("watermark_column") || null,
                partition_column: form.get("partition_column") || null,
                batch_rows: Number(form.get("batch_rows")),
                target_shard_bytes: Number(form.get("target_shard_mb")) * 1048576,
                hot_window_days: form.get("hot_window_days") ? Number(form.get("hot_window_days")) : null,
                enabled: form.get("enabled") === "on",
                config: item.config || {},
            };
            await request(`/api/sync/jobs/camstar-full/table-policies/${encodeURIComponent(item.class_name)}`, { method: "PUT", body: JSON.stringify(payload) });
            toast(`${item.class_name} 同步策略已保存`);
            await loadTablePolicies();
        };
        $("#editDialog").showModal();
    }

    function openPropertyOverrideDialog(item) {
        $("#dialogTitle").textContent = `${item.className}.${item.propertyName}`;
        $("#dialogKicker").textContent = "PROPERTY OVERRIDE";
        $("#dialogFields").innerHTML = [
            field("mapping_kind", "处理方式", "property", { type: "select", items: [["property", "映射物理列"], ["relationship", "关系外键"], ["computed", "计算属性"], ["ignored", "忽略属性"]] }),
            field("physical_table", "物理表", item.physicalTable || item.className),
            field("physical_column", "物理列", ""),
            field("expression", "计算表达式", "", { wide: true }),
            field("notes", "备注", "", { wide: true }),
        ].join("");
        state.dialogSubmit = async (form) => {
            await request(`/api/sync/mappings/properties/${encodeURIComponent(item.className)}/${encodeURIComponent(item.propertyName)}/override`, { method: "PUT", body: JSON.stringify({ physical_table: form.get("physical_table"), physical_column: form.get("physical_column") || null, mapping_kind: form.get("mapping_kind"), expression: form.get("expression") || null, notes: form.get("notes") || null }) });
            toast("属性处理规则已保存；重新编译后生效");
        };
        $("#editDialog").showModal();
    }

    function openRelationshipOverrideDialog(item) {
        $("#dialogTitle").textContent = `${item.sourceClass} → ${item.targetClass}`;
        $("#dialogKicker").textContent = "RELATIONSHIP OVERRIDE";
        const candidates = item.candidateProperties || [];
        $("#dialogFields").innerHTML = [
            candidates.length ? field("source_property", "源导航属性", candidates[0], { type: "select", items: candidates.map(value => [value, value]), wide: true }) : field("source_property", "源导航属性", "", { wide: true }),
            field("notes", "备注", "", { wide: true }),
        ].join("");
        state.dialogSubmit = async (form) => {
            await request(`/api/sync/mappings/relationships/${encodeURIComponent(item.sourceClass)}/${encodeURIComponent(item.relationshipName)}/${encodeURIComponent(item.targetClass)}/override`, { method: "PUT", body: JSON.stringify({ source_property: form.get("source_property"), notes: form.get("notes") || null }) });
            toast("关系处理规则已保存；重新编译后生效");
        };
        $("#editDialog").showModal();
    }

    async function loadNavigation() {
        const payload = await request("/api/sync/navigation?include_disabled=true");
        state.navigation = payload.items;
        renderNavigation();
    }
    async function loadOverview() { state.overview = await request("/api/sync/overview"); renderOverview(); }
    async function loadConnections() { state.connections = (await request("/api/sync/connections")).items; renderConnections(); }
    async function loadOntologyGovernance() {
        state.ontologyGovernance = await request("/api/sync/ontology-governance?profile_key=opcenter2607-core");
        renderOntologyGovernance();
    }
    async function searchOntologySources() {
        const q = $("#ontologySourceSearch").value.trim();
        state.ontologySourceCandidates = (await request(`/api/sync/ontology-governance/source-candidates?q=${encodeURIComponent(q)}&limit=100`)).items;
        renderOntologyGovernance();
    }
    async function loadOntologyDiscoveryCandidates(query = "") {
        state.ontologyDiscoverySearchTerm = query;
        state.ontologyDiscoveryCandidates = (await request(`/api/sync/ontology-governance/source-candidates?q=${encodeURIComponent(query)}&limit=150`)).items;
        renderOntologyDiscoveryCandidates();
        if (state.ontologyGovernanceStage === "discover") renderOntologyDiscoveryGraph().catch(error => toast(error.message, true));
    }
    async function loadOntologyDiscoverySourceGraph() {
        state.ontologyDiscoverySourceGraph = await request("/api/graph/overview");
        renderOntologyDiscovery();
    }
    async function loadJobs() { state.jobs = (await request("/api/sync/jobs")).items; renderJobs(); }
    async function loadTablePolicies() { state.tablePolicies = (await request("/api/sync/jobs/camstar-full/table-policies")).items; renderTablePolicies(); }
    async function loadIncrementalCapabilities() { state.incrementalProbe = await request("/api/sync/jobs/camstar-full/incremental-capabilities"); renderIncrementalCapabilities(); }
    async function loadGraphProfiles() {
        state.profiles = (await request("/api/sync/profiles")).items;
        const profileKey = state.profiles[0]?.profile_key;
        if (!profileKey) return;
        [state.activeProfile, state.profileCandidates, state.governance, state.schemaChanges] = await Promise.all([
            request(`/api/sync/profiles/${encodeURIComponent(profileKey)}`),
            request(`/api/sync/profiles/${encodeURIComponent(profileKey)}/candidates`),
            request(`/api/sync/profiles/${encodeURIComponent(profileKey)}/governance`),
            request(`/api/sync/profiles/${encodeURIComponent(profileKey)}/schema-changes`).then(payload => payload.items),
        ]);
        const currentContract = state.contractSchema?.contract?.contract_key;
        const contractKey = state.governance.contracts.some(item => item.contract_key === currentContract)
            ? currentContract : state.governance.contracts[0]?.contract_key;
        state.contractSchema = contractKey
            ? await request(`/api/sync/data-contracts/${encodeURIComponent(contractKey)}/schema`)
            : null;
        renderGraphProfile();
    }
    async function loadSchemaEvolution(contractKey) {
        const profileKey = state.activeProfile.profile.profile_key;
        [state.contractSchema, state.schemaChanges] = await Promise.all([
            request(`/api/sync/data-contracts/${encodeURIComponent(contractKey)}/schema`),
            request(`/api/sync/profiles/${encodeURIComponent(profileKey)}/schema-changes`).then(payload => payload.items),
        ]);
        renderSchemaEvolution();
    }
    async function loadAttributeProjections() {
        state.attributeProjections = (await request("/api/sync/profiles/opcenter2607-core/attribute-projections")).items;
        renderAttributeProjections();
    }
    async function loadMaterialization() { state.materialization = await request("/api/sync/profiles/opcenter2607-core/materialization"); renderMaterialization(); }
    async function loadDeployments() { state.deployments = await request("/api/sync/profiles/opcenter2607-core/deployments"); renderDeployments(); }
    async function loadObservability() { state.observability = await request("/api/sync/profiles/opcenter2607-core/observability"); renderObservability(); }
    async function loadActions() { state.actions = await request("/api/sync/actions"); renderActions(); }
    async function loadMappings() { state.mappings = await request("/api/sync/mappings"); renderMappings(); renderOverview(); }
    async function loadRuns() { state.runs = (await request("/api/sync/runs?limit=100")).items; renderRuns(); }
    async function loadSettings() { state.settings = (await request("/api/sync/settings")).items; renderSettings(); }

    async function loadAll() {
        setAlert();
        try {
            await loadNavigation();
            await Promise.all([loadConnections(), loadOntologyGovernance(), loadOntologyDiscoverySourceGraph(), loadJobs(), loadTablePolicies(), loadIncrementalCapabilities(), loadMappings(), loadGraphProfiles(), loadAttributeProjections(), loadMaterialization(), loadDeployments(), loadObservability(), loadActions(), loadRuns(), loadSettings()]);
            await loadOverview();
        } catch (error) {
            setAlert(`同步中心加载失败：${error.message}`);
            $("#globalStatusDot").className = "status-dot offline";
            $("#globalStatusText").textContent = "控制面不可用";
        }
    }

    async function runConnectionTest(key, button) {
        button.disabled = true;
        button.textContent = "测试中…";
        try {
            const result = await request(`/api/sync/connections/${encodeURIComponent(key)}/test`, { method: "POST" });
            toast(result.ok ? `${key} 连接正常（${result.latencyMs} ms）` : `${key} 连接失败：${result.error}`, !result.ok);
            await loadConnections(); await loadOverview();
        } catch (error) { toast(error.message, true); }
        finally { button.disabled = false; button.textContent = "测试"; }
    }

    async function runAllConnectionTests(button) {
        button.disabled = true;
        const previous = button.textContent;
        button.textContent = "正在测试…";
        try {
            const result = await request("/api/sync/connections/test-all", { method: "POST" });
            toast(result.ok ? "全部连接测试通过" : "部分连接测试失败，请查看连接管理", !result.ok);
            await loadConnections(); await loadOverview();
        } catch (error) { toast(error.message, true); }
        finally { button.disabled = false; button.textContent = previous; }
    }

    document.addEventListener("click", async (event) => {
        const go = event.target.closest("[data-go]");
        if (go) { location.hash = go.dataset.go; setActiveSection(go.dataset.go); return; }
        const action = event.target.closest("[data-action]");
        if (!action) return;
        const connectionCard = action.closest("[data-connection]");
        const jobCard = action.closest("[data-job]");
        if (action.dataset.action === "toggle-ontology-discovery" || action.dataset.action === "add-ontology-neighbor") {
            toggleOntologyDiscoveryClass(action.dataset.sourceClass);
            return;
        }
        if (action.dataset.action === "select-publish-class") {
            state.selectedOntologyClassUid = action.dataset.nodeId;
            renderOntologyInspector();
            renderOntologyGraph().catch(error => toast(error.message, true));
            return;
        }
        if (action.dataset.action === "add-source-ontology-class") {
            const workspace = state.ontologyGovernance.currentWorkspace.workspace_key;
            action.disabled = true;
            try {
                await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace)}/classes`, { method: "POST", body: JSON.stringify({ source_class: action.dataset.sourceClass, target_name: action.dataset.sourceClass, role: "context", orphan_policy: "quarantine" }) });
                state.ontologyValidation = null; await loadOntologyGovernance(); toast(`${action.dataset.sourceClass} 已加入发布本体草案`);
            } catch (error) { toast(error.message, true); }
            return;
        }
        if (action.dataset.action === "save-publish-class") {
            const form = action.closest("[data-ontology-class]");
            const workspace = state.ontologyGovernance.currentWorkspace.workspace_key;
            try {
                await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace)}/classes/${encodeURIComponent(form.dataset.ontologyClass)}`, { method: "PUT", body: JSON.stringify({ targetName: $('[name="targetName"]', form).value, label: $('[name="label"]', form).value || null, description: $('[name="description"]', form).value || null, role: $('[name="role"]', form).value, orphanPolicy: $('[name="orphanPolicy"]', form).value }) });
                state.ontologyValidation = null; await loadOntologyGovernance(); toast("本体对象配置已保存");
            } catch (error) { toast(error.message, true); }
            return;
        }
        if (action.dataset.action === "remove-publish-class") {
            const form = action.closest("[data-ontology-class]");
            const workspace = state.ontologyGovernance.currentWorkspace.workspace_key;
            try {
                await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace)}/classes/${encodeURIComponent(form.dataset.ontologyClass)}`, { method: "DELETE" });
                state.selectedOntologyClassUid = null; state.ontologyValidation = null; await loadOntologyGovernance(); toast("本体对象已从草案移除");
            } catch (error) { toast(error.message, true); }
            return;
        }
        if (action.dataset.action === "add-publish-property") {
            const node = state.ontologyGovernance.graph.nodes.find(item => item.id === state.selectedOntologyClassUid);
            if (node) openPublishPropertyDialog(node);
            return;
        }
        if (action.dataset.action === "remove-publish-relation") {
            const workspace = state.ontologyGovernance.currentWorkspace.workspace_key;
            try {
                await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace)}/relationships/${encodeURIComponent(action.dataset.relation)}`, { method: "DELETE" });
                state.ontologyValidation = null; await loadOntologyGovernance(); toast("发布关系已删除");
            } catch (error) { toast(error.message, true); }
            return;
        }
        if (action.dataset.action === "activate-ontology-release") {
            const row = action.closest("[data-ontology-release]");
            openActorDialog("激活发布本体版本", async actor => {
                await request(`/api/sync/ontology-governance/releases/${encodeURIComponent(row.dataset.ontologyRelease)}/activate?profile_key=opcenter2607-core`, { method: "POST", body: JSON.stringify({ actor }) });
                toast("发布本体版本已激活，后续 RDF 将固定使用该版本"); await Promise.all([loadOntologyGovernance(), loadDeployments()]);
            });
            return;
        }
        if (action.dataset.action === "test-connection" && connectionCard) {
            await runConnectionTest(connectionCard.dataset.connection, action); return;
        }
        if (action.dataset.action === "edit-connection" && connectionCard) {
            openConnectionDialog(state.connections.find(item => item.connection_key === connectionCard.dataset.connection)); return;
        }
        if (action.dataset.action === "edit-job" && jobCard) {
            openJobDialog(state.jobs.find(item => item.job_name === jobCard.dataset.job)); return;
        }
        if (action.dataset.action === "edit-table-policy") {
            const row = action.closest("[data-policy-class]");
            openTablePolicyDialog(state.tablePolicies.find(item => item.class_name === row.dataset.policyClass)); return;
        }
        if (action.dataset.action === "edit-profile-class") {
            const row = action.closest("[data-profile-class]");
            openProfileClassDialog(state.activeProfile.classes.find(item => item.class_name === row.dataset.profileClass)); return;
        }
        if (action.dataset.action === "edit-profile-relationship") {
            const row = action.closest("[data-profile-relationship]");
            const [sourceClass, relationshipName, targetClass] = row.dataset.profileRelationship.split("|");
            openProfileRelationshipDialog(state.activeProfile.relationships.find(item => item.source_class === sourceClass && item.relationship_name === relationshipName && item.target_class === targetClass)); return;
        }
        if (action.dataset.action === "edit-data-contract") {
            const row = action.closest("[data-contract]");
            openDataContractDialog(state.governance.contracts.find(item => item.contract_key === row.dataset.contract)); return;
        }
        if (action.dataset.action === "edit-relationship-contract") {
            const row = action.closest("[data-relationship-contract]");
            openRelationshipContractDialog(state.governance.relationships.find(item => item.relationship_contract_key === row.dataset.relationshipContract)); return;
        }
        if (action.dataset.action === "edit-projection") {
            const row = action.closest("[data-projection]");
            openAttributeProjectionDialog(state.attributeProjections.find(item => item.projection_key === row.dataset.projection)); return;
        }
        if (action.dataset.action === "preview-projection") {
            const row = action.closest("[data-projection]");
            action.disabled = true; action.textContent = "预览中…";
            try {
                const result = await request(`/api/sync/attribute-projections/${encodeURIComponent(row.dataset.projection)}/preview`, { method: "POST" });
                toast(`只读预览完成：${result.matchedRows} 条匹配，${result.missingOwners} 个未匹配；未修改源库和 Graph Studio`);
                await Promise.all([loadAttributeProjections(), loadMaterialization()]);
            } catch (error) { toast(error.message, true); }
            finally { action.disabled = false; action.textContent = "预览"; }
            return;
        }
        if (["review-projection", "approve-projection", "retire-projection"].includes(action.dataset.action)) {
            const row = action.closest("[data-projection]");
            const nextStatus = ({ "review-projection": "reviewed", "approve-projection": "approved", "retire-projection": "retired" })[action.dataset.action];
            const title = ({ reviewed: "复核属性投影", approved: "批准属性投影", retired: "退役属性投影" })[nextStatus];
            openActorDialog(title, async actor => {
                await request(`/api/sync/attribute-projections/${encodeURIComponent(row.dataset.projection)}/review`, { method: "PUT", body: JSON.stringify({ status: nextStatus, actor }) });
                toast(`${title}完成`);
                await Promise.all([loadAttributeProjections(), loadMaterialization()]);
            }); return;
        }
        if (action.dataset.action === "review-schema-change" || action.dataset.action === "approve-schema-change") {
            const row = action.closest("[data-schema-change]");
            const nextStatus = action.dataset.action === "review-schema-change" ? "reviewed" : "approved";
            action.disabled = true;
            try {
                await request(`/api/sync/schema-changes/${encodeURIComponent(row.dataset.schemaChange)}/review`, { method: "PUT", body: JSON.stringify({ status: nextStatus }) });
                toast(nextStatus === "reviewed" ? "Schema 变更已复核，等待独立批准" : "Schema 变更已批准，仍需迁移执行器应用");
                await loadSchemaEvolution(state.contractSchema.contract.contract_key);
            } catch (error) { toast(error.message, true); }
            finally { action.disabled = false; }
            return;
        }
        if (action.dataset.action === "apply-schema-change" || action.dataset.action === "rollback-schema-change") {
            const row = action.closest("[data-schema-change]");
            const operation = action.dataset.action === "apply-schema-change" ? "apply" : "rollback";
            openActorDialog(operation === "apply" ? "执行 Schema 迁移" : "回滚 Schema 迁移", async actor => {
                const result = await request(`/api/sync/schema-changes/${encodeURIComponent(row.dataset.schemaChange)}/${operation}`, { method: "POST", body: JSON.stringify({ actor }) });
                toast(operation === "apply" ? `契约已升级到 v${result.contractVersion}；下一步生成不可变治理版本` : `契约已回滚到 v${result.contractVersion}`);
                await Promise.all([loadSchemaEvolution(state.contractSchema.contract.contract_key), loadMaterialization()]);
            }); return;
        }
        if (action.dataset.action === "activate-release") {
            const row = action.closest("[data-release]");
            openActorDialog("激活治理版本", async actor => {
                await request(`/api/sync/profiles/opcenter2607-core/releases/${encodeURIComponent(row.dataset.release)}/activate`, { method: "POST", body: JSON.stringify({ actor }) });
                toast("治理版本已原子激活"); await Promise.all([loadMaterialization(), loadDeployments(), loadObservability()]);
            }); return;
        }
        if (action.dataset.action === "prepare-deployment") {
            const card = action.closest("[data-environment]");
            openActorDialog(`准备 ${card.dataset.environment.toUpperCase()} 发布制品`, async actor => {
                const result = await request("/api/sync/profiles/opcenter2607-core/deployments", { method: "POST", body: JSON.stringify({ environment_key: card.dataset.environment, actor }) });
                toast(`不可变 RDF 制品已准备：${result.status}`); await loadDeployments();
            }); return;
        }
        if (action.dataset.action === "approve-deployment") {
            const row = action.closest("[data-deployment]");
            openActorDialog("批准环境发布", async actor => {
                await request(`/api/sync/deployments/${encodeURIComponent(row.dataset.deployment)}/approve`, { method: "POST", body: JSON.stringify({ actor }) });
                toast("发布已批准；目标环境开关仍控制实际写入"); await loadDeployments();
            }); return;
        }
        if (action.dataset.action === "apply-deployment") {
            const row = action.closest("[data-deployment]");
            action.disabled = true;
            try { await request(`/api/sync/deployments/${encodeURIComponent(row.dataset.deployment)}/apply`, { method: "POST" }); toast("Graph Studio 蓝绿发布与验收完成"); await loadDeployments(); }
            catch (error) { toast(error.message, true); }
            finally { action.disabled = false; }
            return;
        }
        if (action.dataset.action === "ack-alert") {
            const row = action.closest("[data-alert]");
            openActorDialog("确认告警", async actor => {
                await request(`/api/sync/alerts/${encodeURIComponent(row.dataset.alert)}/acknowledge`, { method: "POST", body: JSON.stringify({ actor }) });
                toast("告警已确认，恢复后会自动关闭"); await loadObservability();
            }); return;
        }
        if (action.dataset.action === "plan-action") {
            const card = action.closest("[data-action-key]");
            openActionPlanDialog(state.actions.definitions.find(item => item.action_key === card.dataset.actionKey)); return;
        }
        if (action.dataset.action === "edit-action-definition") {
            const card = action.closest("[data-action-key]");
            openActionDefinitionDialog(state.actions.definitions.find(item => item.action_key === card.dataset.actionKey)); return;
        }
        if (["review-action-definition", "approve-action-definition", "retire-action-definition"].includes(action.dataset.action)) {
            const card = action.closest("[data-action-key]");
            const status = ({ "review-action-definition": "reviewed", "approve-action-definition": "approved", "retire-action-definition": "retired" })[action.dataset.action];
            action.disabled = true;
            try {
                await request(`/api/sync/actions/definitions/${encodeURIComponent(card.dataset.actionKey)}/review`, { method: "PUT", body: JSON.stringify({ status }) });
                toast(`Action ${statusLabel(status)}`); await loadActions();
            } catch (error) { toast(error.message, true); }
            finally { action.disabled = false; }
            return;
        }
        if (action.dataset.action === "approve-action") {
            const row = action.closest("[data-invocation]");
            action.disabled = true;
            try { await request(`/api/sync/actions/invocations/${encodeURIComponent(row.dataset.invocation)}/approve`, { method: "POST" }); toast("Action 已由可信身份的独立人员批准"); await loadActions(); }
            catch (error) { toast(error.message, true); }
            finally { action.disabled = false; }
            return;
        }
        if (action.dataset.action === "execute-action") {
            const row = action.closest("[data-invocation]");
            action.disabled = true;
            try { await request(`/api/sync/actions/invocations/${encodeURIComponent(row.dataset.invocation)}/execute`, { method: "POST" }); toast("Camstar API Action 执行完成"); await loadActions(); }
            catch (error) { toast(error.message, true); }
            finally { action.disabled = false; }
            return;
        }
        if (action.dataset.action === "compensate-action") {
            const row = action.closest("[data-invocation]");
            $("#dialogTitle").textContent = "发起补偿 Action";
            $("#dialogKicker").textContent = "COMPENSATION";
            $("#dialogFields").innerHTML = [
                field("idempotency_key", "补偿幂等键", crypto.randomUUID(), { wide: true }),
                field("payload", "补偿请求 JSON", "{}", { type: "textarea", wide: true }),
            ].join("");
            state.dialogSubmit = async form => {
                await request(`/api/sync/actions/invocations/${encodeURIComponent(row.dataset.invocation)}/compensate`, { method: "POST", body: JSON.stringify({ idempotency_key: form.get("idempotency_key"), payload: JSON.parse(form.get("payload")) }) });
                toast("补偿 Action 已创建，并进入独立审批流程"); await loadActions();
            };
            $("#editDialog").showModal(); return;
        }
        if (action.dataset.action === "dry-run-job" && jobCard) {
            action.disabled = true; action.textContent = "盘点中…";
            try {
                const result = await request(`/api/sync/jobs/${encodeURIComponent(jobCard.dataset.job)}/dry-run`, { method: "POST" });
                toast(`盘点完成，Run ${result.runId.slice(0, 8)}`);
                await loadRuns(); await loadOverview();
            } catch (error) { toast(error.message, true); }
            finally { action.disabled = false; action.textContent = "执行盘点"; }
            return;
        }
        if (action.dataset.action === "preview-job" && jobCard) {
            action.disabled = true; action.textContent = "生成中…";
            try {
                const result = await request(`/api/sync/jobs/${encodeURIComponent(jobCard.dataset.job)}/preview`, { method: "POST" });
                toast(`RDF 预览已生成：${result.instances} 个实例，Graph Studio 未修改`);
                await loadRuns(); await loadOverview();
            } catch (error) { toast(error.message, true); }
            finally { action.disabled = false; action.textContent = "生成 RDF 预览"; }
            return;
        }
        if (action.dataset.action === "override-property") {
            const [className, propertyName] = action.closest("[data-property-key]").dataset.propertyKey.split("|");
            openPropertyOverrideDialog(state.mappings.catalog.unresolvedProperties.find(item => item.className === className && item.propertyName === propertyName));
            return;
        }
        if (action.dataset.action === "override-relationship") {
            const [sourceClass, relationshipName, targetClass] = action.closest("[data-relationship-key]").dataset.relationshipKey.split("|");
            openRelationshipOverrideDialog(state.mappings.catalog.relationshipReview.find(item => item.sourceClass === sourceClass && item.relationshipName === relationshipName && item.targetClass === targetClass));
            return;
        }
        if (action.dataset.action === "save-menu") {
            const row = action.closest("[data-menu]");
            const item = state.navigation.find(menu => menu.menu_key === row.dataset.menu);
            try {
                await request(`/api/sync/navigation/${encodeURIComponent(item.menu_key)}`, { method: "PUT", body: JSON.stringify({ label_zh: $(".menu-label", row).value.trim(), label_en: item.label_en, sort_order: Number($(".menu-order", row).value), enabled: $(".menu-enabled", row).checked }) });
                toast("菜单配置已保存"); await loadNavigation(); renderMenuSettings();
            } catch (error) { toast(error.message, true); }
            return;
        }
        if (action.dataset.action === "save-setting") {
            const row = action.closest("[data-setting]");
            const raw = $("input", row).value;
            let value = raw;
            try { value = JSON.parse(raw); } catch (_) { /* keep string */ }
            try {
                await request(`/api/sync/settings/${encodeURIComponent(row.dataset.setting)}`, { method: "PUT", body: JSON.stringify({ value }) });
                toast("系统设置已保存"); await loadSettings();
            } catch (error) { toast(error.message, true); }
        }
    });

    window.addEventListener("hashchange", () => setActiveSection(location.hash.slice(1)));
    $("#toggleSidebar").addEventListener("click", event => {
        const collapsed = $(".app-shell").classList.toggle("sidebar-collapsed");
        event.currentTarget.setAttribute("aria-label", collapsed ? "展开主菜单" : "折叠主菜单");
        event.currentTarget.title = collapsed ? "展开主菜单" : "折叠主菜单";
        window.setTimeout(() => {
            ontologyDiscoveryGraph?.fitView();
            ontologyGovernanceGraph?.fitView();
        }, 230);
    });
    $("#initializePublishOntology").addEventListener("click", () => openActorDialog("初始化发布本体工作区", async actor => {
        await request("/api/sync/ontology-governance/initialize?profile_key=opcenter2607-core", { method: "POST", body: JSON.stringify({ actor }) });
        toast("独立发布本体数据库和草案工作区已建立"); await Promise.all([loadOntologyGovernance(), loadConnections()]);
    }));
    $("#fitOntologyDiscoveryGraph").addEventListener("click", () => ontologyDiscoveryGraph?.fitView());
    $("#toggleOntologyDiscoveryFocus").addEventListener("click", event => {
        state.ontologyDiscoveryFocused = !state.ontologyDiscoveryFocused;
        event.currentTarget.textContent = state.ontologyDiscoveryFocused ? "显示完整图谱" : "聚焦所选";
        renderOntologyDiscoveryGraph().catch(error => toast(error.message, true));
    });
    $("#newCustomOntologyClass").addEventListener("click", openCustomOntologyClassDialog);
    $("#newOntologyRelationship").addEventListener("click", openOntologyRelationshipDialog);
    $("#fitOntologyGraph").addEventListener("click", () => ontologyGovernanceGraph?.fitView());
    $("#validatePublishOntology").addEventListener("click", async () => {
        const workspace = state.ontologyGovernance.currentWorkspace;
        if (!workspace) { toast("请先初始化工作区", true); return; }
        try {
            state.ontologyValidation = await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace.workspace_key)}/validate`, { method: "POST" });
            renderOntologyGovernance();
            $(".ontology-ledger").open = true;
            toast(state.ontologyValidation.valid ? "发布本体校验通过" : `存在 ${state.ontologyValidation.errors.length} 个阻断项`, !state.ontologyValidation.valid);
        } catch (error) { toast(error.message, true); }
    });
    $("#reviewPublishOntology").addEventListener("click", () => {
        const workspace = state.ontologyGovernance.currentWorkspace;
        if (!workspace) { toast("请先初始化工作区", true); return; }
        openActorDialog("提交本体复核", async actor => {
            state.ontologyValidation = await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace.workspace_key)}/review`, { method: "POST", body: JSON.stringify({ actor }) });
            toast("本体草案已复核，等待另一人员批准"); await loadOntologyGovernance();
        });
    });
    $("#approvePublishOntology").addEventListener("click", () => {
        const workspace = state.ontologyGovernance.currentWorkspace;
        if (!workspace) { toast("请先初始化工作区", true); return; }
        openActorDialog("批准并冻结本体版本", async actor => {
            const result = await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace.workspace_key)}/approve`, { method: "POST", body: JSON.stringify({ actor }) });
            toast(`不可变本体 R${result.releaseNo} 已冻结，激活后进入 RDF 构建`); await loadOntologyGovernance();
        });
    });
    $("#ontologyInspector").addEventListener("change", async event => {
        const checkbox = event.target.closest("[data-publish-property]");
        if (!checkbox) return;
        const graph = state.ontologyGovernance.graph;
        const prop = graph.properties.find(item => item.uid === checkbox.dataset.publishProperty);
        const workspace = state.ontologyGovernance.currentWorkspace.workspace_key;
        try {
            await request(`/api/sync/ontology-governance/workspaces/${encodeURIComponent(workspace)}/classes/${encodeURIComponent(prop.classUid)}/properties`, { method: "PUT", body: JSON.stringify({ uid: prop.uid, propertyKey: prop.sourceName || prop.targetName, sourceName: prop.sourceName || prop.targetName, targetName: prop.targetName, sourcePath: prop.sourcePath || null, dataType: prop.dataType || "String", description: prop.description || null, required: Boolean(prop.required), published: checkbox.checked, origin: prop.origin || "source" }) });
            state.ontologyValidation = null; await loadOntologyGovernance();
        } catch (error) { checkbox.checked = !checkbox.checked; toast(error.message, true); }
    });
    $("#ontologyInspector").addEventListener("input", event => {
        if (event.target.id !== "ontologyPropertyFilter") return;
        state.ontologyPropertyFilter = event.target.value;
        applyOntologyPropertyFilter();
    });
    $("#testConnectionsPage").addEventListener("click", event => runAllConnectionTests(event.currentTarget));
    $("#editGraphProfile").addEventListener("click", () => openGraphProfileDialog());
    $("#addProfileClass").addEventListener("click", () => openProfileClassDialog({ role: "context", orphan_policy: "quarantine", priority: 100, enabled: true }, true));
    $("#addProfileRelationship").addEventListener("click", () => openProfileRelationshipDialog(null, true));
    $("#profileClassSearch").addEventListener("input", () => renderGraphProfile());
    $("#planContextClosure").addEventListener("click", async event => {
        const button = event.currentTarget; button.disabled = true; button.textContent = "规划中…";
        try {
            state.closurePlan = await request(`/api/sync/profiles/${encodeURIComponent(state.activeProfile.profile.profile_key)}/closure-plan`, { method: "POST" });
            renderGraphProfile();
            toast(`闭包预览完成：${state.closurePlan.summary.includedClassCount} 类、${state.closurePlan.summary.traversalStepCount} 个扩展步骤`);
        } catch (error) { toast(error.message, true); }
        finally { button.disabled = false; button.textContent = "预览上下文闭包"; }
    });
    $("#previewCuration").addEventListener("click", async event => {
        const button = event.currentTarget; button.disabled = true; button.textContent = "检查中…";
        try {
            const result = await request(`/api/sync/profiles/${encodeURIComponent(state.activeProfile.profile.profile_key)}/curation-preview`, { method: "POST" });
            await loadGraphProfiles();
            toast(result.publishable ? "治理门禁通过，可进入发布审批" : `治理预览完成：${result.summary.failedErrors} 个阻断项，尚不可发布`, !result.publishable);
        } catch (error) { toast(error.message, true); }
        finally { button.disabled = false; button.textContent = "运行治理预览"; }
    });
    $("#schemaContractSelect").addEventListener("change", event => loadSchemaEvolution(event.currentTarget.value).catch(error => toast(error.message, true)));
    $("#newSchemaChange").addEventListener("click", () => openSchemaChangeDialog());
    $("#newAttributeProjection").addEventListener("click", () => openAttributeProjectionDialog());
    $("#newActionDefinition").addEventListener("click", () => openActionDefinitionDialog());
    $("#importOpenApiAction").addEventListener("click", () => openOpenApiImportDialog().catch(error => toast(error.message, true)));
    $("#planMaterialization").addEventListener("click", async event => {
        const button = event.currentTarget; button.disabled = true;
        try {
            const result = await request("/api/sync/profiles/opcenter2607-core/materialization", { method: "POST", body: JSON.stringify({ apply: false, activate: false }) });
            state.materialization.plan = result.plan; renderMaterialization();
            toast(result.plan.ready ? "物化计划已通过门禁" : `物化仍有 ${result.plan.blockers.length} 项阻断`, !result.plan.ready);
        } catch (error) { toast(error.message, true); }
        finally { button.disabled = false; }
    });
    $("#runMaterialization").addEventListener("click", () => openActorDialog("执行已审批物化", async actor => {
        const result = await request("/api/sync/profiles/opcenter2607-core/materialization", { method: "POST", body: JSON.stringify({ apply: true, activate: false, actor }) });
        toast(`治理版本 R${result.releaseNo} 已验证，等待激活`); await Promise.all([loadMaterialization(), loadObservability()]);
    }));
    $("#rollbackRelease").addEventListener("click", () => openActorDialog("回滚治理版本", async actor => {
        await request("/api/sync/profiles/opcenter2607-core/releases/rollback", { method: "POST", body: JSON.stringify({ actor }) });
        toast("活动版本已回滚到上一不可变快照"); await Promise.all([loadMaterialization(), loadDeployments(), loadObservability()]);
    }));
    $("#runHealthCheck").addEventListener("click", async event => {
        const button = event.currentTarget; button.disabled = true;
        try { const result = await request("/api/sync/profiles/opcenter2607-core/health-check", { method: "POST" }); toast(`健康检查完成：${statusLabel(result.status)}`, result.status === "unhealthy"); await loadObservability(); }
        catch (error) { toast(error.message, true); }
        finally { button.disabled = false; }
    });
    $("#probeIncremental").addEventListener("click", async event => {
        const button = event.currentTarget; button.disabled = true; button.textContent = "检测中…";
        try {
            state.incrementalProbe = await request("/api/sync/jobs/camstar-full/incremental-capabilities/probe", { method: "POST" });
            renderIncrementalCapabilities();
            toast(`增量能力检测完成：${state.incrementalProbe.summary.nativeChangeCaptureReady}/${state.incrementalProbe.summary.mappedTables} 张表原生就绪`);
        } catch (error) { toast(error.message, true); }
        finally { button.disabled = false; button.textContent = "重新检测"; }
    });
    $("#planIncremental").addEventListener("click", async event => {
        const button = event.currentTarget; button.disabled = true; button.textContent = "规划中…";
        try {
            const result = await request("/api/sync/jobs/camstar-full/incremental-plan", { method: "POST" });
            state.incrementalProbe = await request("/api/sync/jobs/camstar-full/incremental-capabilities");
            renderIncrementalCapabilities();
            toast(`增量窗口规划完成：${result.summary.incrementalTables} 张增量表`);
        } catch (error) { toast(error.message, true); }
        finally { button.disabled = false; button.textContent = "规划增量窗口"; }
    });
    $("#previewIncremental").addEventListener("click", async event => {
        const button = event.currentTarget; button.disabled = true; button.textContent = "生成中…";
        try {
            const result = await request("/api/sync/jobs/camstar-full/incremental-preview", { method: "POST" });
            toast(result.status === "no_incremental_windows"
                ? "当前没有可执行的增量窗口"
                : `增量预览已生成：${result.events} 个事件，${result.tombstones} 个删除`);
            await loadRuns();
        } catch (error) { toast(error.message, true); }
        finally { button.disabled = false; button.textContent = "生成增量预览"; }
    });
    $("#compileMappings").addEventListener("click", async event => {
        const button = event.currentTarget; button.disabled = true; button.textContent = "编译中…";
        try {
            const result = await request("/api/sync/mappings/compile", { method: "POST" });
            toast(`映射目录已编译：${result.propertiesResolved}/${result.properties} 个属性`);
            await loadMappings(); await loadTablePolicies();
        } catch (error) { toast(error.message, true); }
        finally { button.disabled = false; button.textContent = "重新编译映射"; }
    });
    $("#editForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!state.dialogSubmit) return;
        const save = $("#dialogSave");
        save.disabled = true;
        try {
            await state.dialogSubmit(new FormData(event.currentTarget));
            $("#editDialog").close();
        } catch (error) { toast(error.message, true); }
        finally { save.disabled = false; }
    });
    $("#dialogClose").addEventListener("click", () => $("#editDialog").close());
    $("#dialogCancel").addEventListener("click", () => $("#editDialog").close());

    loadAll();
})();
