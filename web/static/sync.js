(() => {
    "use strict";

    const state = {
        navigation: [],
        overview: null,
        connections: [],
        jobs: [],
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
                <div class="card-top"><div><h3>${escapeHtml(item.display_name)}</h3><p>${escapeHtml(item.kind.replaceAll("_", " "))}</p></div><span class="status-pill ${item.status}">${statusLabel(item.status)}</span></div>
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
        if (options.type === "select") {
            return `<div class="${className}"><label for="dialog-${name}">${label}</label><select id="dialog-${name}" name="${name}">${options.items.map(([key, text]) => `<option value="${key}" ${key === value ? "selected" : ""}>${text}</option>`).join("")}</select></div>`;
        }
        if (options.type === "checkbox") {
            return `<div class="${className}"><label><input type="checkbox" name="${name}" ${value ? "checked" : ""}> ${label}</label></div>`;
        }
        return `<div class="${className}"><label for="dialog-${name}">${label}</label><input id="dialog-${name}" name="${name}" type="${options.type || "text"}" value="${escapeHtml(value ?? "")}" ${options.readonly ? "readonly" : ""}></div>`;
    }

    function openConnectionDialog(item) {
        $("#dialogTitle").textContent = `编辑 ${item.display_name}`;
        $("#dialogKicker").textContent = "CONNECTION PROFILE";
        $("#dialogFields").innerHTML = [
            field("display_name", "显示名称", item.display_name, { wide: true }),
            field("endpoint", "Endpoint", item.endpoint, { wide: true }),
            field("database_name", "数据库 / Graphmart URI", item.database_name || "", { wide: true }),
            field("username", "用户名", item.username || ""),
            field("enabled", "启用此连接", item.enabled, { type: "checkbox" }),
        ].join("");
        state.dialogSubmit = async (form) => {
            const payload = {
                display_name: form.get("display_name"), endpoint: form.get("endpoint"),
                database_name: form.get("database_name") || null, username: form.get("username") || null,
                enabled: form.get("enabled") === "on", config: item.config || {},
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
    async function loadMappings() { state.mappings = await request("/api/sync/mappings"); renderMappings(); renderOverview(); }
    async function loadRuns() { state.runs = (await request("/api/sync/runs?limit=100")).items; renderRuns(); }
    async function loadSettings() { state.settings = (await request("/api/sync/settings")).items; renderSettings(); }

    async function loadAll() {
        setAlert();
        try {
            await loadNavigation();
            await Promise.all([loadConnections(), loadJobs(), loadMappings(), loadRuns(), loadSettings()]);
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
    $("#compileMappings").addEventListener("click", async event => {
        const button = event.currentTarget; button.disabled = true; button.textContent = "编译中…";
        try {
            const result = await request("/api/sync/mappings/compile", { method: "POST" });
            toast(`映射目录已编译：${result.propertiesResolved}/${result.properties} 个属性`);
            await loadMappings();
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
