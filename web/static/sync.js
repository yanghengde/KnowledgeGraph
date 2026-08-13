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
        activeProfile: null,
        profileCandidates: { classes: [], relationships: [] },
        closurePlan: null,
        governance: { contracts: [], relationships: [], latestRun: null, qualityResults: [] },
        contractSchema: null,
        schemaChanges: [],
        materialization: { plan: null, releases: [] },
        deployments: { environments: [], deployments: [], activeCuratedRelease: null },
        observability: { latestRun: null, metrics: [], alerts: [], lineage: [] },
        actions: { definitions: [], invocations: [], applyEnabled: false },
        mappings: null,
        runs: [],
        settings: [],
        dialogSubmit: null,
    };

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
        return ({ dashboard: "OV", plug: "CN", schedule: "JB", profile: "BG", database: "DB", rocket: "DP", pulse: "HL", action: "AC", mapping: "MP", history: "RN", settings: "ST" })[icon] || "•";
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
        return ({ online: "在线", offline: "离线", degraded: "降级", unknown: "未检查", disabled: "已停用", succeeded: "成功", failed: "失败", queued: "排队", started: "运行中", extracting: "抽取中", staged: "已暂存", loading: "加载中", verifying: "验证中", cancelled: "已取消", planned: "已规划", ready: "待激活", active: "活动", superseded: "已替代", rolled_back: "已回滚", approved: "已批准", pending_approval: "待审批", executing: "执行中", healthy: "健康", unhealthy: "异常", warning: "警告", critical: "严重", open: "未处理", acknowledged: "已确认", resolved: "已恢复" })[value] || value || "未知";
    }

    function connectionKindLabel(value) {
        return ({
            camstar_sqlserver: "Camstar · SQL Server",
            camstar_oracle: "Camstar · Oracle",
            ontology_neo4j: "Ontology · Neo4j",
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
            <a class="nav-item" href="${escapeHtml(item.route)}" data-section-key="${escapeHtml(item.menu_key)}">
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
        $("#actionCards").innerHTML = data.definitions.map(item => `<article class="job-card" data-action-key="${escapeHtml(item.action_key)}"><div class="card-top"><div><p>${escapeHtml(item.object_class)} · ${escapeHtml(item.http_method)}</p><h3>${escapeHtml(item.title)}</h3></div><span class="status-pill ${item.enabled ? "online" : "unknown"}">${item.enabled ? "已启用" : "定义关闭"}</span></div><div class="card-details"><div class="detail-field"><span>API</span><strong>${escapeHtml(item.endpoint_path)}</strong></div><div class="detail-field"><span>审批</span><strong>${item.approval_required ? "双人审批" : "无需审批"}</strong></div></div><div class="card-actions"><small>禁止数据库直写</small><button class="mini-btn" data-action="plan-action">创建预演</button></div></article>`).join("");
        $("#actionInvocationRows").innerHTML = data.invocations.map(item => {
            let actions = "—";
            if (item.status === "pending_approval") actions = '<button class="mini-btn" data-action="approve-action">批准</button>';
            else if (item.status === "approved") actions = '<button class="mini-btn" data-action="execute-action">执行</button>';
            return `<tr data-invocation="${escapeHtml(item.invocation_id)}"><td>${escapeHtml(item.action_key)}</td><td>${escapeHtml(item.actor)}</td><td>${item.dry_run ? "预演" : "真实"}</td><td>${escapeHtml(item.idempotency_key)}</td><td><span class="status-pill ${item.status === "succeeded" ? "online" : item.status === "failed" ? "failed" : "unknown"}">${escapeHtml(statusLabel(item.status))}</span></td><td>${formatDate(item.started_at, true)}</td><td>${actions}</td></tr>`;
        }).join("") || '<tr class="empty-row"><td colspan="7">尚无 Action 调用</td></tr>';
    }

    function openActionPlanDialog(item) {
        $("#dialogTitle").textContent = item.title;
        $("#dialogKicker").textContent = "ACTION PLAN";
        const example = Object.fromEntries((item.input_schema?.required || []).map(key => [key, key === "changes" ? {} : ""]));
        $("#dialogFields").innerHTML = [
            field("actor", "申请人", "", { placeholder: "工号或用户名" }),
            field("actor_roles", "角色（逗号分隔）", (item.allowed_roles || []).join(",")),
            field("idempotency_key", "幂等键", crypto.randomUUID(), { wide: true, help: "相同业务请求必须复用同一个幂等键" }),
            field("payload", "请求 JSON", JSON.stringify(example, null, 2), { type: "textarea", wide: true }),
            field("dry_run", "仅预演，不调用 Camstar", true, { type: "checkbox", wide: true }),
        ].join("");
        state.dialogSubmit = async form => {
            const payload = JSON.parse(form.get("payload"));
            const result = await request(`/api/sync/actions/${encodeURIComponent(item.action_key)}/plan`, { method: "POST", body: JSON.stringify({ payload, actor: form.get("actor"), actor_roles: String(form.get("actor_roles") || "").split(",").map(value => value.trim()).filter(Boolean), idempotency_key: form.get("idempotency_key"), dry_run: form.get("dry_run") === "on" }) });
            toast(result.replayed ? "返回已有幂等调用" : `Action ${result.status}；未发生数据库直写`);
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
            await Promise.all([loadConnections(), loadJobs(), loadTablePolicies(), loadIncrementalCapabilities(), loadMappings(), loadGraphProfiles(), loadMaterialization(), loadDeployments(), loadObservability(), loadActions(), loadRuns(), loadSettings()]);
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
        if (action.dataset.action === "approve-action") {
            const row = action.closest("[data-invocation]");
            openActorDialog("批准 Camstar Action", async actor => {
                await request(`/api/sync/actions/invocations/${encodeURIComponent(row.dataset.invocation)}/approve`, { method: "POST", body: JSON.stringify({ actor }) });
                toast("Action 已由独立人员批准"); await loadActions();
            }); return;
        }
        if (action.dataset.action === "execute-action") {
            const row = action.closest("[data-invocation]");
            action.disabled = true;
            try { await request(`/api/sync/actions/invocations/${encodeURIComponent(row.dataset.invocation)}/execute`, { method: "POST" }); toast("Camstar API Action 执行完成"); await loadActions(); }
            catch (error) { toast(error.message, true); }
            finally { action.disabled = false; }
            return;
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
