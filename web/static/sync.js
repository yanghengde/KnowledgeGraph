(() => {
    "use strict";

    const state = {
        navigation: [],
        overview: null,
        connections: [],
        jobs: [],
        tablePolicies: [],
        incrementalProbe: null,
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
        return ({ dashboard: "OV", plug: "CN", schedule: "JB", mapping: "MP", history: "RN", settings: "ST" })[icon] || "•";
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
        return ({ online: "在线", offline: "离线", degraded: "降级", unknown: "未检查", disabled: "已停用", succeeded: "成功", failed: "失败", queued: "排队", started: "运行中", extracting: "抽取中", staged: "已暂存", loading: "加载中", verifying: "验证中", cancelled: "已取消" })[value] || value || "未知";
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
    async function loadMappings() { state.mappings = await request("/api/sync/mappings"); renderMappings(); renderOverview(); }
    async function loadRuns() { state.runs = (await request("/api/sync/runs?limit=100")).items; renderRuns(); }
    async function loadSettings() { state.settings = (await request("/api/sync/settings")).items; renderSettings(); }

    async function loadAll() {
        setAlert();
        try {
            await loadNavigation();
            await Promise.all([loadConnections(), loadJobs(), loadTablePolicies(), loadIncrementalCapabilities(), loadMappings(), loadRuns(), loadSettings()]);
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
