/**
 * Camstar Ontology Explorer – G6 v5 Graph Application
 * ────────────────────────────────────────────────────
 * Features:
 *   • Layered loading: L0 = OntologyClass overview → L1 = click to drill
 *   • Combo aggregation by module (Workflow / Operation / Spec / Other)
 *   • Siemens colour scheme
 */
(() => {
    "use strict";

    const i18nText = (key, fallback) => window.CamstarI18n?.t(key) || fallback || key;
    const ontologyLabel = (kind, key, original, zh = "", context = "inline") =>
        window.CamstarI18n?.entity(kind, key, { original, zh, context }) || original;
    const ontologyDescription = (className, fallback = "") =>
        window.CamstarI18n?.description(className, fallback) || fallback;
    const ontologyPropertyDescription = (key, fallback = "") =>
        window.CamstarI18n?.propertyDescription(key, fallback) || fallback;
    const htmlEscape = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
    })[char]);

    function applyOverviewTranslations(data) {
        for (const node of data?.nodes || []) {
            node.data ||= {};
            node.data.technicalLabel ||= node.id;
            node.data.displayLabel = ontologyLabel(
                "node", node.id, node.data.technicalLabel, node.data.chineseName || "", "graph",
            );
        }
        for (const edge of data?.edges || []) {
            edge.data ||= {};
            edge.data.technicalLabel ??= edge.data.label || "";
            edge.data.displayLabel = ontologyLabel(
                "relationship", edge.data.technicalLabel, edge.data.technicalLabel, "", "graph",
            );
        }
        return data;
    }

    function setIconContent(element, iconName, label, { size = 14, spin = false } = {}) {
        element.innerHTML = AppIcons.svg(iconName, {
            size,
            className: spin ? "app-icon-spin" : "",
        });
        const text = document.createElement("span");
        text.textContent = label;
        element.appendChild(text);
    }

    // ── Global SQL dialect ──
    // One selector controls every SQL surface: relationship examples and chat.
    const SQL_DIALECT_COOKIE = "camstar_sql_dialect";
    const SQL_DIALECTS = {
        oracle: { label: "Oracle" },
        sqlserver: { label: "SQL Server" },
    };

    function readCookie(name) {
        const prefix = `${encodeURIComponent(name)}=`;
        const item = document.cookie
            .split("; ")
            .find((part) => part.startsWith(prefix));
        return item ? decodeURIComponent(item.slice(prefix.length)) : "";
    }

    function normalizeSqlDialect(value) {
        return Object.hasOwn(SQL_DIALECTS, value) ? value : "oracle";
    }

    let currentSqlDialect = normalizeSqlDialect(readCookie(SQL_DIALECT_COOKIE));
    const globalSqlDialect = document.getElementById("globalSqlDialect");

    function applyGlobalSqlDialect(value, { persist = true, notify = true } = {}) {
        const next = normalizeSqlDialect(value);
        const changed = next !== currentSqlDialect;
        currentSqlDialect = next;
        globalSqlDialect.value = next;
        document.documentElement.dataset.sqlDialect = next;
        if (persist) {
            document.cookie = `${encodeURIComponent(SQL_DIALECT_COOKIE)}=${encodeURIComponent(next)}; Max-Age=31536000; Path=/; SameSite=Lax`;
        }
        if (notify && changed) {
            window.dispatchEvent(new CustomEvent("camstar:sql-dialect-change", {
                detail: { dialect: next, label: SQL_DIALECTS[next].label },
            }));
        }
    }

    window._getSqlDialect = () => currentSqlDialect;
    window._setSqlDialect = (value) => applyGlobalSqlDialect(value);
    window._getSqlDialectLabel = () => SQL_DIALECTS[currentSqlDialect].label;
    applyGlobalSqlDialect(currentSqlDialect, { persist: !readCookie(SQL_DIALECT_COOKIE), notify: false });
    globalSqlDialect.addEventListener("change", () => {
        applyGlobalSqlDialect(globalSqlDialect.value);
    });

    // ── Siemens Palette ──
    const COLORS = {
        workflow: { fill: "#009999", stroke: "#00B8B8", text: "#E8F0F2", comboFill: "rgba(0,153,153,0.08)", comboBorder: "rgba(0,153,153,0.3)" },
        operation: { fill: "#FF6600", stroke: "#FF8833", text: "#E8F0F2", comboFill: "rgba(255,102,0,0.08)", comboBorder: "rgba(255,102,0,0.3)" },
        spec: { fill: "#862996", stroke: "#A040B0", text: "#E8F0F2", comboFill: "rgba(134,41,150,0.08)", comboBorder: "rgba(134,41,150,0.3)" },
        workcenter: { fill: "#2E86C1", stroke: "#5DADE2", text: "#E8F0F2", comboFill: "rgba(46,134,193,0.08)", comboBorder: "rgba(46,134,193,0.3)" },
        factory: { fill: "#27AE60", stroke: "#52D68C", text: "#E8F0F2", comboFill: "rgba(39,174,96,0.08)", comboBorder: "rgba(39,174,96,0.3)" },
        mfgline: { fill: "#00897B", stroke: "#4DB6AC", text: "#E8F0F2", comboFill: "rgba(0,137,123,0.08)", comboBorder: "rgba(0,137,123,0.3)" },
        mfgcalendar: { fill: "#FF8F00", stroke: "#FFB74D", text: "#E8F0F2", comboFill: "rgba(255,143,0,0.08)", comboBorder: "rgba(255,143,0,0.3)" },
        product: { fill: "#F39C12", stroke: "#F5B041", text: "#E8F0F2", comboFill: "rgba(243,156,18,0.08)", comboBorder: "rgba(243,156,18,0.3)" },
        container: { fill: "#3498DB", stroke: "#5DADE2", text: "#E8F0F2", comboFill: "rgba(52,152,219,0.08)", comboBorder: "rgba(52,152,219,0.3)" },
        carrier: { fill: "#039BE5", stroke: "#4FC3F7", text: "#E8F0F2", comboFill: "rgba(3,155,229,0.08)", comboBorder: "rgba(3,155,229,0.3)" },
        businessrule: { fill: "#6A1B9A", stroke: "#AB47BC", text: "#E8F0F2", comboFill: "rgba(106,27,154,0.08)", comboBorder: "rgba(106,27,154,0.3)" },
        datacollection: { fill: "#9B59B6", stroke: "#AF7AC5", text: "#E8F0F2", comboFill: "rgba(155,89,182,0.08)", comboBorder: "rgba(155,89,182,0.3)" },
        quality: { fill: "#E74C3C", stroke: "#EC7063", text: "#E8F0F2", comboFill: "rgba(231,76,60,0.08)", comboBorder: "rgba(231,76,60,0.3)" },
        electronic_procedure: { fill: "#1ABC9C", stroke: "#48C9B0", text: "#E8F0F2", comboFill: "rgba(26,188,156,0.08)", comboBorder: "rgba(26,188,156,0.3)" },
        resource: { fill: "#F1C40F", stroke: "#F7DC6F", text: "#E8F0F2", comboFill: "rgba(241,196,15,0.08)", comboBorder: "rgba(241,196,15,0.3)" },
        material: { fill: "#16A085", stroke: "#48C9B0", text: "#E8F0F2", comboFill: "rgba(22,160,133,0.08)", comboBorder: "rgba(22,160,133,0.3)" },
        bom: { fill: "#673AB7", stroke: "#9575CD", text: "#E8F0F2", comboFill: "rgba(103,58,183,0.08)", comboBorder: "rgba(103,58,183,0.3)" },
        erpbom: { fill: "#7B1FA2", stroke: "#BA68C8", text: "#E8F0F2", comboFill: "rgba(123,31,162,0.08)", comboBorder: "rgba(123,31,162,0.3)" },
        employee: { fill: "#E67E22", stroke: "#EB984E", text: "#E8F0F2", comboFill: "rgba(230,126,34,0.08)", comboBorder: "rgba(230,126,34,0.3)" },
        role: { fill: "#37474F", stroke: "#78909C", text: "#E8F0F2", comboFill: "rgba(55,71,79,0.08)", comboBorder: "rgba(55,71,79,0.3)" },
        mfgorder: { fill: "#34495E", stroke: "#5D6D7E", text: "#E8F0F2", comboFill: "rgba(52,73,94,0.08)", comboBorder: "rgba(52,73,94,0.3)" },
        part: { fill: "#0277BD", stroke: "#4FC3F7", text: "#E8F0F2", comboFill: "rgba(2,119,189,0.08)", comboBorder: "rgba(2,119,189,0.3)" },
        organization: { fill: "#C62828", stroke: "#EF5350", text: "#E8F0F2", comboFill: "rgba(198,40,40,0.08)", comboBorder: "rgba(198,40,40,0.3)" },
        billofprocess: { fill: "#4527A0", stroke: "#7E57C2", text: "#E8F0F2", comboFill: "rgba(69,39,160,0.08)", comboBorder: "rgba(69,39,160,0.3)" },
        team: { fill: "#BF360C", stroke: "#FF7043", text: "#E8F0F2", comboFill: "rgba(191,54,12,0.08)", comboBorder: "rgba(191,54,12,0.3)" },
        terminal: { fill: "#00695C", stroke: "#4DB6AC", text: "#E8F0F2", comboFill: "rgba(0,105,92,0.08)", comboBorder: "rgba(0,105,92,0.3)" },
        salesorder: { fill: "#1B5E20", stroke: "#66BB6A", text: "#E8F0F2", comboFill: "rgba(27,94,32,0.08)", comboBorder: "rgba(27,94,32,0.3)" },
        maintenance: { fill: "#C0392B", stroke: "#D98880", text: "#E8F0F2", comboFill: "rgba(192,57,43,0.08)", comboBorder: "rgba(192,57,43,0.3)" },
        sampling: { fill: "#9C27B0", stroke: "#BA68C8", text: "#E8F0F2", comboFill: "rgba(156,39,176,0.08)", comboBorder: "rgba(156,39,176,0.3)" },
        document: { fill: "#607D8B", stroke: "#90A4AE", text: "#E8F0F2", comboFill: "rgba(96,125,139,0.08)", comboBorder: "rgba(96,125,139,0.3)" },
        label: { fill: "#FF9800", stroke: "#FFB74D", text: "#E8F0F2", comboFill: "rgba(255,152,0,0.08)", comboBorder: "rgba(255,152,0,0.3)" },
        tool: { fill: "#795548", stroke: "#A1887F", text: "#E8F0F2", comboFill: "rgba(121,85,72,0.08)", comboBorder: "rgba(121,85,72,0.3)" },
        change_management: { fill: "#F44336", stroke: "#E57373", text: "#E8F0F2", comboFill: "rgba(244,67,54,0.08)", comboBorder: "rgba(244,67,54,0.3)" },
        recipe: { fill: "#E91E63", stroke: "#F06292", text: "#E8F0F2", comboFill: "rgba(233,30,99,0.08)", comboBorder: "rgba(233,30,99,0.3)" },
        inventory: { fill: "#8BC34A", stroke: "#AED581", text: "#E8F0F2", comboFill: "rgba(139,195,74,0.08)", comboBorder: "rgba(139,195,74,0.3)" },
        rework: { fill: "#FF5722", stroke: "#FF8A65", text: "#E8F0F2", comboFill: "rgba(255,87,34,0.08)", comboBorder: "rgba(255,87,34,0.3)" },
        timer: { fill: "#00BCD4", stroke: "#4DD0E1", text: "#E8F0F2", comboFill: "rgba(0,188,212,0.08)", comboBorder: "rgba(0,188,212,0.3)" },
        checklist: { fill: "#5C6BC0", stroke: "#7986CB", text: "#E8F0F2", comboFill: "rgba(92,107,192,0.08)", comboBorder: "rgba(92,107,192,0.3)" },
        setup: { fill: "#7E57C2", stroke: "#9575CD", text: "#E8F0F2", comboFill: "rgba(126,87,194,0.08)", comboBorder: "rgba(126,87,194,0.3)" },
        packaging: { fill: "#8D6E63", stroke: "#A1887F", text: "#E8F0F2", comboFill: "rgba(141,110,99,0.08)", comboBorder: "rgba(141,110,99,0.3)" },
        supplier: { fill: "#3F51B5", stroke: "#5C6BC0", text: "#E8F0F2", comboFill: "rgba(63,81,181,0.08)", comboBorder: "rgba(63,81,181,0.3)" },
        esignature: { fill: "#00ACC1", stroke: "#26C6DA", text: "#E8F0F2", comboFill: "rgba(0,172,193,0.08)", comboBorder: "rgba(0,172,193,0.3)" },
        alarm: { fill: "#F50057", stroke: "#FF4081", text: "#E8F0F2", comboFill: "rgba(245,0,87,0.08)", comboBorder: "rgba(245,0,87,0.3)" },
        scrap: { fill: "#546E7A", stroke: "#78909C", text: "#E8F0F2", comboFill: "rgba(84,110,122,0.08)", comboBorder: "rgba(84,110,122,0.3)" },
        equipmentstate: { fill: "#29B6F6", stroke: "#4FC3F7", text: "#E8F0F2", comboFill: "rgba(41,182,246,0.08)", comboBorder: "rgba(41,182,246,0.3)" },
        shipping: { fill: "#827717", stroke: "#9E9D24", text: "#E8F0F2", comboFill: "rgba(130,119,23,0.08)", comboBorder: "rgba(130,119,23,0.3)" },
        environment: { fill: "#00BFA5", stroke: "#1DE9B6", text: "#E8F0F2", comboFill: "rgba(0,191,165,0.08)", comboBorder: "rgba(0,191,165,0.3)" },
        rma: { fill: "#D84315", stroke: "#F4511E", text: "#E8F0F2", comboFill: "rgba(216,67,21,0.08)", comboBorder: "rgba(216,67,21,0.3)" },
        consumable: { fill: "#FFB300", stroke: "#FFCA28", text: "#E8F0F2", comboFill: "rgba(255,179,0,0.08)", comboBorder: "rgba(255,179,0,0.3)" },
        spc: { fill: "#2979FF", stroke: "#82B1FF", text: "#E8F0F2", comboFill: "rgba(41,121,255,0.08)", comboBorder: "rgba(41,121,255,0.3)" },
        semiconductor_action_approval_esign: { fill: "#BE123C", stroke: "#FDA4AF", text: "#E8F0F2", comboFill: "rgba(190,18,60,0.08)", comboBorder: "rgba(190,18,60,0.3)" },
        semiconductor_bin_overlay: { fill: "#0369A1", stroke: "#7DD3FC", text: "#E8F0F2", comboFill: "rgba(3,105,161,0.08)", comboBorder: "rgba(3,105,161,0.3)" },
        semiconductor_cio_core: { fill: "#00695C", stroke: "#4DB6AC", text: "#E8F0F2", comboFill: "rgba(0,105,92,0.08)", comboBorder: "rgba(0,105,92,0.3)" },
        semiconductor_cio_orchestration: { fill: "#283593", stroke: "#7986CB", text: "#E8F0F2", comboFill: "rgba(40,53,147,0.08)", comboBorder: "rgba(40,53,147,0.3)" },
        semiconductor_carrier_material_tool: { fill: "#6D4C41", stroke: "#BCAAA4", text: "#E8F0F2", comboFill: "rgba(109,76,65,0.08)", comboBorder: "rgba(109,76,65,0.3)" },
        semiconductor_cio_bases: { fill: "#3949AB", stroke: "#9FA8DA", text: "#E8F0F2", comboFill: "rgba(57,73,171,0.08)", comboBorder: "rgba(57,73,171,0.3)" },
        semiconductor_foundation: { fill: "#00A6A6", stroke: "#36D1C4", text: "#E8F0F2", comboFill: "rgba(0,166,166,0.08)", comboBorder: "rgba(0,166,166,0.3)" },
        semiconductor_legacy_name_replacements: { fill: "#4F46E5", stroke: "#A5B4FC", text: "#E8F0F2", comboFill: "rgba(79,70,229,0.08)", comboBorder: "rgba(79,70,229,0.3)" },
        semiconductor_physical_resource_replacements: { fill: "#0F766E", stroke: "#5EEAD4", text: "#E8F0F2", comboFill: "rgba(15,118,110,0.08)", comboBorder: "rgba(15,118,110,0.3)" },
        semiconductor_print_interface_details: { fill: "#D97706", stroke: "#FBBF24", text: "#E8F0F2", comboFill: "rgba(217,119,6,0.08)", comboBorder: "rgba(217,119,6,0.3)" },
        semiconductor_print_pack_ship: { fill: "#5D4037", stroke: "#A1887F", text: "#E8F0F2", comboFill: "rgba(93,64,55,0.08)", comboBorder: "rgba(93,64,55,0.3)" },
        semiconductor_process_equipment: { fill: "#1565C0", stroke: "#42A5F5", text: "#E8F0F2", comboFill: "rgba(21,101,192,0.08)", comboBorder: "rgba(21,101,192,0.3)" },
        semiconductor_process_wip_details: { fill: "#0891B2", stroke: "#67E8F9", text: "#E8F0F2", comboFill: "rgba(8,145,178,0.08)", comboBorder: "rgba(8,145,178,0.3)" },
        semiconductor_quality_iqc: { fill: "#C62828", stroke: "#EF5350", text: "#E8F0F2", comboFill: "rgba(198,40,40,0.08)", comboBorder: "rgba(198,40,40,0.3)" },
        semiconductor_revision_bases: { fill: "#546E7A", stroke: "#B0BEC5", text: "#E8F0F2", comboFill: "rgba(84,110,122,0.08)", comboBorder: "rgba(84,110,122,0.3)" },
        semiconductor_scheduling_flow: { fill: "#2E7D32", stroke: "#66BB6A", text: "#E8F0F2", comboFill: "rgba(46,125,50,0.08)", comboBorder: "rgba(46,125,50,0.3)" },
        semiconductor_security_kpi_configuration: { fill: "#4338CA", stroke: "#A5B4FC", text: "#E8F0F2", comboFill: "rgba(67,56,202,0.08)", comboBorder: "rgba(67,56,202,0.3)" },
        semiconductor_service_location: { fill: "#455A64", stroke: "#90A4AE", text: "#E8F0F2", comboFill: "rgba(69,90,100,0.08)", comboBorder: "rgba(69,90,100,0.3)" },
        semiconductor_shared_support: { fill: "#00897B", stroke: "#80CBC4", text: "#E8F0F2", comboFill: "rgba(0,137,123,0.08)", comboBorder: "rgba(0,137,123,0.3)" },
        semiconductor_shipping_integration: { fill: "#AD1457", stroke: "#F06292", text: "#E8F0F2", comboFill: "rgba(173,20,87,0.08)", comboBorder: "rgba(173,20,87,0.3)" },
        semiconductor_spc_quality_details: { fill: "#A855F7", stroke: "#D8B4FE", text: "#E8F0F2", comboFill: "rgba(168,85,247,0.08)", comboBorder: "rgba(168,85,247,0.3)" },
        semiconductor_spc_yield: { fill: "#00838F", stroke: "#4DD0E1", text: "#E8F0F2", comboFill: "rgba(0,131,143,0.08)", comboBorder: "rgba(0,131,143,0.3)" },
        semiconductor_user_job_spc_configuration: { fill: "#7C3AED", stroke: "#C4B5FD", text: "#E8F0F2", comboFill: "rgba(124,58,237,0.08)", comboBorder: "rgba(124,58,237,0.3)" },
        semiconductor_wafer_experiment: { fill: "#7B1FA2", stroke: "#CE93D8", text: "#E8F0F2", comboFill: "rgba(123,31,162,0.08)", comboBorder: "rgba(123,31,162,0.3)" },
        semiconductor_wip_control: { fill: "#EF6C00", stroke: "#FFB74D", text: "#E8F0F2", comboFill: "rgba(239,108,0,0.08)", comboBorder: "rgba(239,108,0,0.3)" },
        other: { fill: "#505050", stroke: "#707070", text: "#E8F0F2", comboFill: "rgba(80,80,80,0.08)", comboBorder: "rgba(80,80,80,0.3)" },
    };

    const COMBO_LABELS = {
        workflow: "Workflow 工作流",
        operation: "Operation 工序",
        spec: "Spec 规范/参数",
        workcenter: "WorkCenter 工作中心",
        factory: "Factory 工厂模型",
        mfgline: "MfgLine 制造产线",
        mfgcalendar: "MfgCalendar 制造日历",
        product: "Product 产品物料",
        container: "Container 容器批次",
        carrier: "Carrier 载具管理",
        businessrule: "BusinessRule 业务规则",
        datacollection: "Data Collection 数据采集",
        quality: "Quality 质量",
        electronic_procedure: "E-Procedure 电子程序",
        resource: "Resource 设备资源",
        material: "Material 原材料/物料",
        bom: "BOM 物料清单",
        erpbom: "ERPBOM ERP物料清单",
        employee: "Employee 人员资质",
        role: "Role 角色权限",
        mfgorder: "MfgOrder 制造工单",
        part: "Part 设备资源",
        organization: "Organization 组织",
        billofprocess: "BillOfProcess 工艺清单",
        team: "Team 班组团队",
        salesorder: "SalesOrder 销售订单",
        maintenance: "Maintenance 维护保养",
        sampling: "Sampling 质量抽样",
        document: "Document 文档控制",
        tool: "Tool 工装工具",
        change_management: "Change Mgt 变更管理",
        recipe: "Recipe 设备配方",
        inventory: "Inventory 库存货位",
        checklist: "Checklist 检查表模板",
        setup: "Setup 换线准备",
        packaging: "Packaging 包装管理",
        spc: "SPC 统计过程控制",
        semiconductor_action_approval_esign: "Semiconductor 动作审批与电子签名",
        semiconductor_bin_overlay: "Semiconductor Bin与Overlay",
        semiconductor_cio_core: "系统集成（已清理）",
        semiconductor_cio_orchestration: "系统集成编排（已清理）",
        semiconductor_carrier_material_tool: "Semiconductor 载具物料工装",
        semiconductor_cio_bases: "半导体修订基础对象",
        semiconductor_foundation: "Semiconductor 半导体基础",
        semiconductor_legacy_name_replacements: "Semiconductor 旧名称物理替代",
        semiconductor_physical_resource_replacements: "Semiconductor 物理位置与资源BOM",
        semiconductor_print_interface_details: "Semiconductor 打印与接口明细",
        semiconductor_print_pack_ship: "Semiconductor 打印包装出货",
        semiconductor_process_equipment: "Semiconductor 工艺与设备",
        semiconductor_process_wip_details: "Semiconductor 工艺与WIP明细",
        semiconductor_quality_iqc: "Semiconductor 质量与IQC",
        semiconductor_revision_bases: "Revision Base 版本基础",
        semiconductor_scheduling_flow: "Semiconductor 排程与工艺流",
        semiconductor_security_kpi_configuration: "Semiconductor 安全与KPI配置",
        semiconductor_service_location: "Semiconductor 服务与位置",
        semiconductor_shared_support: "Semiconductor 公共支撑",
        semiconductor_shipping_integration: "Semiconductor 出货与集成",
        semiconductor_spc_quality_details: "Semiconductor SPC与质量明细",
        semiconductor_spc_yield: "Semiconductor SPC与良率",
        semiconductor_user_job_spc_configuration: "Semiconductor 用户作业与SPC配置",
        semiconductor_wafer_experiment: "Semiconductor 晶圆与实验",
        semiconductor_wip_control: "Semiconductor WIP控制",
        other: "Other 其他",
    };

    function localizedComboLabel(key) {
        const label = COMBO_LABELS[key] || key;
        if (window.CamstarI18n?.language !== "en-US") return label;
        return label.replace(/\s*[\u3400-\u9fff].*$/u, "").trim() || key;
    }

    // ── Globals ──
    let graph = null;
    let rawData = null;
    let comboEnabled = false;
    let relMode = false;  // Relationship focus mode
    let layoutMode = "preset";  // Fast deterministic initial layout
    let selectedNodeId = null;   // Persistent selection
    let queryPreviewGraph = null;
    let queryCopyFeedbackTimer = null;
    const queryBuilderState = {
        active: false,
        selectedNodes: [],
        activeNodeId: null,
        plan: null,
        loading: false,
        error: "",
        requestRevision: 0,
        previousSelectedNodeId: null,
        selectedPreviewJoin: null,
        activeJoinPairKey: null,
        joinOverrides: new Map(),
    };
    const API = "";  // same origin
    const classDetailCache = new Map(); // Client-side cache for class detail API responses
    const nodeInfoCache = new Map();
    const presetPositions = new Map();
    let adjacencyIndex = null;
    let edgeInfoById = new Map();
    let overviewApiEdges = [];
    let detailPrefetchPromise = null;
    let edgeRenderToken = 0;
    let pendingEdgeNodeId = null;
    let edgeRenderWorker = null;
    let graphMutationBusy = false;
    let pendingHighlightClear = false;
    let detailRenderToken = 0;
    const PRIORITY_NODE_STORAGE_KEY = "camstar_priority_nodes_v2";
    const DEFAULT_CORE_NODE_IDS = new Set(["Workflow", "Product", "MfgOrder"]);
    let priorityNodes = new Set();
    try {
        const saved = JSON.parse(localStorage.getItem(PRIORITY_NODE_STORAGE_KEY) || "[]");
        priorityNodes = new Set(Array.isArray(saved) ? saved : []);
        if (!priorityNodes.size) {
            const legacy = JSON.parse(
                localStorage.getItem("camstar_priority_node_sizes_v1") || "{}",
            );
            priorityNodes = new Set(Object.keys(legacy));
        }
    } catch (_) {
        priorityNodes = new Set();
    }

    // Parallel relationships to the same neighbor are collapsed, but every
    // direct neighbor remains visible on the canvas.
    const MAX_OVERVIEW_EDGES = 360;
    const INITIAL_PROPERTY_ROWS = 60;

    function hideNodeTooltip() {
        document.getElementById("nodeTooltip").classList.add("node-tooltip-hidden");
    }

    function showNodeTooltip(context) {
        const tooltip = document.getElementById("nodeTooltip");
        tooltip.replaceChildren();

        const title = document.createElement("div");
        title.className = "tt-title";
        title.textContent = context.data.displayLabel || context.data.label || context.nodeId;

        const subtitle = document.createElement("div");
        subtitle.className = "tt-sub";
        subtitle.textContent = context.data.technicalLabel || context.nodeId;

        const description = document.createElement("div");
        description.className = "tt-description";
        description.textContent = ontologyDescription(context.nodeId, context.data.description || "");

        tooltip.append(title, subtitle, description);
        const tooltipWidth = 300;
        tooltip.style.left = `${Math.min(
            context.clientX + 16,
            window.innerWidth - tooltipWidth - 12,
        )}px`;
        tooltip.style.top = `${Math.max(12, context.clientY - 10)}px`;
        tooltip.classList.remove("node-tooltip-hidden");
    }

    function getNodeTooltipContext(targetGraph, event, defaultSize = 52) {
        const nodeId = event.target?.id;
        const clientX = event.client?.x;
        const clientY = event.client?.y;
        if (!nodeId || !Number.isFinite(clientX) || !Number.isFinite(clientY)) return null;

        const nodeData = targetGraph.getNodeData(nodeId);
        if (!nodeData?.data) return null;
        const data = nodeData.data;
        if (!(data.type === "class" || data.module)) return null;

        // G6 treats a node label as part of the node element. Only show the
        // information card when the pointer is inside the circle itself.
        const canvasPos = targetGraph.getCanvasByClient({ x: clientX, y: clientY });
        const nodePos = targetGraph.getElementPosition(nodeId);
        const sizeValue = nodeData.style?.size ?? defaultSize;
        const resolvedSize = typeof sizeValue === "function"
            ? sizeValue(nodeData)
            : sizeValue;
        const radius = (typeof resolvedSize === "number" ? resolvedSize : defaultSize) / 2;
        const dx = canvasPos.x - nodePos[0];
        const dy = canvasPos.y - nodePos[1];
        if (Math.hypot(dx, dy) > radius + 6) return null;

        return { nodeId, data, clientX, clientY };
    }

    function defaultNodeSize(nodeOrData) {
        return DEFAULT_CORE_NODE_IDS.has(nodeOrData?.id) ? 76 : 52;
    }

    function getNodeSize(nodeId, nodeOrData) {
        return priorityNodes.has(nodeId) ? 76 : defaultNodeSize(nodeOrData);
    }

    function persistPriorityNodes() {
        localStorage.setItem(
            PRIORITY_NODE_STORAGE_KEY,
            JSON.stringify([...priorityNodes]),
        );
    }

    function isLargeNode(node) {
        return priorityNodes.has(node.id) || defaultNodeSize(node) >= 76;
    }

    // ── Layout presets ──
    const LAYOUTS = {
        "preset": {
            type: "preset",
        },
        "dagre-tb": {
            type: "dagre",
            rankdir: "TB",
            nodesep: 50,
            ranksep: 80,
            align: undefined,
        },
        "dagre-lr": {
            type: "dagre",
            rankdir: "LR",
            nodesep: 40,
            ranksep: 100,
            align: undefined,
        },
        "force": {
            type: "force",
            preventOverlap: true,
            nodeSize: 68,
            linkDistance: 160,
            nodeStrength: -400,
            edgeStrength: 0.3,
            collideStrength: 0.8,
            alphaDecay: 0.03,
        },
        "radial": {
            type: "radial",
            unitRadius: 200,
            linkDistance: 220,
            preventOverlap: true,
            nodeSize: 80,
            nodeSpacing: 50,
            focusNode: "Workflow",
            strictRadial: false
        },
    };

    const LAYOUT_LABELS = {
        "dagre-tb": "↓ 层次纵向",
        "dagre-lr": "→ 层次横向",
        "force": "⬤ 力导向",
        "radial": "◎ 径向",
    };
    const LAYOUT_KEYS = ["dagre-tb", "dagre-lr", "force", "radial"];

    // ══════════════════════════════════════════════════════
    //  Fetch helpers
    // ══════════════════════════════════════════════════════
    async function fetchJSON(url) {
        // Neo4j can be reloaded while the web service stays online. Let the
        // server-side LRU cache provide speed, but never reuse a stale browser
        // copy of graph data after an ontology scope change.
        const res = await fetch(API + url, { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    }

    function indexOverviewData(data) {
        nodeInfoCache.clear();
        presetPositions.clear();
        for (const node of data?.nodes || []) {
            nodeInfoCache.set(node.id, node);
        }

        // Compact deterministic sunflower layout. The former module-block
        // layout spread every module using the largest module's dimensions,
        // so fitView reduced the complete ontology to unreadable dots.
        const goldenAngle = Math.PI * (3 - Math.sqrt(5));
        const orderedNodes = [...(data?.nodes || [])].sort((a, b) => {
            const aRank = priorityNodes.has(a.id) ? 0 : (isLargeNode(a) ? 1 : 2);
            const bRank = priorityNodes.has(b.id) ? 0 : (isLargeNode(b) ? 1 : 2);
            if (aRank !== bRank) return aRank - bRank;
            const moduleOrder = (a.data?.module || "other")
                .localeCompare(b.data?.module || "other");
            return moduleOrder || a.id.localeCompare(b.id);
        });
        const followedNodes = orderedNodes.filter((node) =>
            priorityNodes.has(node.id),
        );
        const coreNodes = orderedNodes.filter((node) =>
            !priorityNodes.has(node.id) && isLargeNode(node),
        );
        const regularNodes = orderedNodes.filter((node) =>
            !priorityNodes.has(node.id) && !isLargeNode(node),
        );
        let anchorNode = null;
        const followedAnchorIndex = followedNodes.findIndex((node) => node.id === "Workflow");
        if (followedAnchorIndex >= 0) {
            anchorNode = followedNodes.splice(followedAnchorIndex, 1)[0];
        } else {
            const coreAnchorIndex = coreNodes.findIndex((node) => node.id === "Workflow");
            if (coreAnchorIndex >= 0) {
                anchorNode = coreNodes.splice(coreAnchorIndex, 1)[0];
            }
        }
        if (anchorNode) presetPositions.set(anchorNode.id, { x: 0, y: 0 });

        // Followed objects live in the central focus area, between Workflow
        // and the permanent core objects. This makes the switch visibly
        // meaningful without changing the user's current camera position.
        const followedRadius = followedNodes.length
            ? Math.max(145, followedNodes.length * 115 / (2 * Math.PI))
            : 0;
        followedNodes.forEach((node, index) => {
            const angle = followedNodes.length === 1
                ? -Math.PI / 2
                : index / followedNodes.length * Math.PI * 2 - Math.PI / 2;
            presetPositions.set(node.id, {
                x: Math.cos(angle) * followedRadius * 1.12,
                y: Math.sin(angle) * followedRadius,
            });
        });

        // Keep the permanent large objects on a ring outside the followed
        // area. Product and MfgOrder remain prominent while followed nodes
        // get the clearest part of the graph.
        const coreRadius = Math.max(
            followedRadius + 165,
            270,
            coreNodes.length * 130 / (2 * Math.PI),
        );
        coreNodes.forEach((node, index) => {
            // Offset the permanent core ring from the followed ring so a
            // newly followed node never sits directly on top of Product or
            // MfgOrder and its relationship line remains visible.
            const angle = index / Math.max(1, coreNodes.length) * Math.PI * 2;
            presetPositions.set(node.id, {
                x: Math.cos(angle) * coreRadius * 1.2,
                y: Math.sin(angle) * coreRadius * 0.78,
            });
        });

        const innerRadius = coreRadius + 110;
        regularNodes.forEach((node, index) => {
            const radius = Math.sqrt(
                innerRadius * innerRadius + index * 34 * 34,
            );
            const angle = index * goldenAngle;
            presetPositions.set(node.id, {
                x: Math.cos(angle) * radius * 1.25,
                y: Math.sin(angle) * radius * 0.78,
            });
        });

        adjacencyIndex = new Map();
        edgeInfoById = new Map();
        for (const node of data?.nodes || []) {
            adjacencyIndex.set(node.id, {
                neighbors: new Set(),
                outgoing: new Set(),
                incoming: new Set(),
            });
        }
        (data?.edges || []).forEach((edge, index) => {
            const edgeId = edge.id || `e-${index}`;
            edge.id = edgeId;
            edgeInfoById.set(edgeId, edge);
            const source = adjacencyIndex.get(edge.source);
            const target = adjacencyIndex.get(edge.target);
            if (!source || !target) return;
            source.neighbors.add(edge.target);
            source.outgoing.add(edgeId);
            target.neighbors.add(edge.source);
            target.incoming.add(edgeId);
        });
        overviewApiEdges = selectOverviewEdges(data?.edges || []);
    }

    function selectOverviewEdges(edges) {
        const uniquePairs = new Map();
        for (const edge of edges) {
            const pairKey = edge.source < edge.target
                ? `${edge.source}\u0000${edge.target}`
                : `${edge.target}\u0000${edge.source}`;
            if (!uniquePairs.has(pairKey)) uniquePairs.set(pairKey, edge);
        }

        const score = (edge) => {
            const sourceNode = nodeInfoCache.get(edge.source);
            const targetNode = nodeInfoCache.get(edge.target);
            const largeScore =
                (sourceNode && isLargeNode(sourceNode) ? 1 : 0)
                + (targetNode && isLargeNode(targetNode) ? 1 : 0);
            const degreeScore =
                (adjacencyIndex.get(edge.source)?.neighbors.size || 0)
                + (adjacencyIndex.get(edge.target)?.neighbors.size || 0);
            return largeScore * 10000 + degreeScore;
        };
        const scored = [...uniquePairs.values()].sort((a, b) =>
            score(b) - score(a)
            || a.source.localeCompare(b.source)
            || a.target.localeCompare(b.target),
        );

        const selected = [];
        const selectedIds = new Set();
        const coveredNodes = new Set();
        const addEdge = (edge) => {
            if (selectedIds.has(edge.id) || selected.length >= MAX_OVERVIEW_EDGES) return;
            selected.push(edge);
            selectedIds.add(edge.id);
            coveredNodes.add(edge.source);
            coveredNodes.add(edge.target);
        };

        // Cover the graph broadly first, then use the remaining budget for
        // core/high-degree relationships.
        for (const edge of scored) {
            if (!coveredNodes.has(edge.source) || !coveredNodes.has(edge.target)) {
                addEdge(edge);
            }
            if (selected.length >= MAX_OVERVIEW_EDGES) break;
        }
        for (const edge of scored) {
            addEdge(edge);
            if (selected.length >= MAX_OVERVIEW_EDGES) break;
        }
        return selected;
    }

    function scheduleDetailPrefetch() {
        if (detailPrefetchPromise) return;
        const prefetch = () => {
            detailPrefetchPromise = fetchJSON("/api/graph/details")
                .then((details) => {
                    for (const [className, detail] of Object.entries(details)) {
                        classDetailCache.set(className, detail);
                    }
                })
                .catch((error) => {
                    detailPrefetchPromise = null;
                    console.debug("Class detail prefetch skipped:", error);
                });
        };
        if ("requestIdleCallback" in window) {
            window.requestIdleCallback(prefetch);
        } else {
            window.setTimeout(prefetch, 2000);
        }
    }

    // ══════════════════════════════════════════════════════
    //  Build G6 graph data from API response
    // ══════════════════════════════════════════════════════
    function buildGraphData(apiData, useCombo) {
        const nodes = apiData.nodes.map((n) => {
            let mod = n.data.module || "other";
            if (!COMBO_LABELS[mod]) {
                mod = "other";
            }
            const c = COLORS[mod] || COLORS.other;
            const position = presetPositions.get(n.id);
            return {
                id: n.id,
                combo: useCombo ? mod : undefined,
                style: {
                    size: getNodeSize(n.id, n),
                    fill: c.fill,
                    stroke: c.stroke,
                    shadowColor: c.fill,
                    zIndex: 10,
                    x: position?.x,
                    y: position?.y,
                },
                data: {
                    ...n.data,
                    module: mod,
                },
            };
        });

        const edges = apiData.edges.map((e, i) => ({
            id: e.id || `e-${i}`,
            source: e.source,
            target: e.target,
            data: {
                ...e.data,
                type: "quadratic",
                style: {
                    stroke: "rgba(0,255,185,0.25)",
                    lineWidth: 1.5,
                    endArrow: true,
                    lineDash: e.data.lineStyle === "dashed" ? [5, 5] : undefined,
                    cursor: "pointer",
                    halo: 20,
                    haloOpacity: 0,
                    haloPointerEvents: "auto",
                },
                labelText: e.data.displayLabel || e.data.label || "",
                labelCfg: {
                    style: {
                        fill: "rgba(0,255,185,0.6)",
                        fontSize: 9,
                        fontFamily: "Inter",
                        background: {
                            fill: "rgba(0,0,40,0.8)",
                            padding: [2, 4, 2, 4],
                            radius: 3,
                        },
                    },
                    autoRotate: true,
                },
            },
        }));

        const combos = useCombo
            ? Object.keys(COMBO_LABELS).map((key) => {
                const c = COLORS[key] || COLORS.other;
                return {
                    id: key,
                    data: {
                        label: localizedComboLabel(key),
                        type: "rect",
                        style: {
                            fill: c.comboFill,
                            stroke: c.comboBorder,
                            lineWidth: 1.5,
                            radius: 12,
                            lineDash: [4, 4],
                        },
                        labelCfg: {
                            style: {
                                fill: c.stroke,
                                fontSize: 13,
                                fontWeight: 600,
                                fontFamily: "Inter",
                            },
                            position: "top",
                        },
                    },
                };
            })
            : [];

        return { nodes, edges, combos };
    }

    // ══════════════════════════════════════════════════════
    //  Initialise the G6 Graph
    // ══════════════════════════════════════════════════════
    function initGraph(container, data) {
        const width = container.clientWidth;
        const height = container.clientHeight;

        graph = new G6.Graph({
            container,
            width,
            height,
            autoFit: "view",
            padding: [60, 60, 60, 60],
            // The graph only keeps a compact overview edge layer, or the
            // currently selected node's direct-neighbor layer. G6 culling is
            // therefore unnecessary here. More importantly, its cached
            // bounds can drop newly-added long edges after a focus switch,
            // leaving a highlighted neighbor with no visible connection.
            culling: false,

            // ── Node defaults ──
            node: {
                type: "circle",
                style: {
                    zIndex: 10,
                    size: (d) => getNodeSize(d.id, d),
                    fill: (d) => (COLORS[d.data?.module] || COLORS.other).fill,
                    stroke: (d) => (COLORS[d.data?.module] || COLORS.other).stroke,
                    lineWidth: 2,
                    labelText: (d) => d.data?.displayLabel || d.data?.label || d.id,
                    labelFill: "#E8F0F2",
                    labelFontSize: 11,
                    labelFontWeight: 500,
                    labelFontFamily: "Inter, sans-serif",
                    labelPlacement: "bottom",
                    labelOffsetY: 8,
                    iconText: (d) => (d.data?.displayLabel || d.data?.label || d.id).substring(0, 2),
                    iconFontSize: (d) => getNodeSize(d.id, d) >= 76 ? 18 : 14,
                    iconFontWeight: 700,
                    iconFill: "#fff",
                    iconFontFamily: "Inter, sans-serif",
                    shadowBlur: 0,
                    cursor: "pointer",
                    ports: [{ placement: "center" }],
                },
                state: {
                    active: {
                        stroke: "#00FFB9",
                        lineWidth: 3,
                        shadowColor: "#00FFB9",
                        shadowBlur: 10,
                        opacity: 1,
                        zIndex: 20,
                    },
                    selected: {
                        stroke: "#FFFFFF",
                        lineWidth: 4,
                        shadowColor: "#00FFB9",
                        shadowBlur: 14,
                        lineDash: undefined,
                        opacity: 1,
                        zIndex: 20,
                    },
                    highlighted: {
                        stroke: "#00FFB9",
                        lineWidth: 4,
                        shadowColor: "#00FFB9",
                        shadowBlur: 12,
                        opacity: 1,
                        zIndex: 20,
                    },
                    querySelected: {
                        stroke: "#00FFB9",
                        lineWidth: 4,
                        shadowColor: "#00FFB9",
                        shadowBlur: 14,
                        opacity: 1,
                        zIndex: 60,
                    },
                    queryRelated: {
                        stroke: "#00FFB9",
                        lineWidth: 3,
                        shadowColor: "#00FFB9",
                        shadowBlur: 7,
                        opacity: 1,
                        labelOpacity: 1,
                        iconOpacity: 1,
                        zIndex: 50,
                    },
                    queryBridge: {
                        stroke: "#4CA6FF",
                        lineWidth: 3,
                        shadowColor: "#4CA6FF",
                        shadowBlur: 9,
                        opacity: 1,
                        zIndex: 52,
                    },
                    queryUnconnected: {
                        stroke: "#FF6B6B",
                        lineWidth: 4,
                        shadowColor: "#FF6B6B",
                        shadowBlur: 11,
                        opacity: 1,
                        zIndex: 60,
                    },
                    queryPreviousSelected: {
                        stroke: "rgba(0,255,185,0.55)",
                        lineWidth: 2,
                        shadowBlur: 0,
                        opacity: 0.34,
                        labelOpacity: 0.28,
                        iconOpacity: 0.34,
                        zIndex: 4,
                    },
                    queryRelatedSelected: {
                        stroke: "#00FFB9",
                        lineWidth: 3,
                        shadowColor: "#00FFB9",
                        shadowBlur: 7,
                        opacity: 1,
                        labelOpacity: 1,
                        iconOpacity: 1,
                        zIndex: 51,
                    },
                    queryInactive: {
                        opacity: 0.08,
                        labelOpacity: 0,
                        iconOpacity: 0.08,
                        zIndex: 1,
                    },
                    inactive: {
                        opacity: 0.45,
                        labelOpacity: 0.45,
                        iconOpacity: 0.45,
                        zIndex: 2,
                    },
                },
            },

            // ── Edge defaults ──
            edge: {
                type: "line",
                style: {
                    zIndex: 0,
                    stroke: "rgba(0,255,185,0.2)",
                    lineWidth: 1.0,
                    shadowBlur: 0,
                    halo: 6,
                    haloOpacity: 0,
                    haloPointerEvents: "auto",
                    endArrow: false,
                    labelText: "",
                    labelOpacity: 0,
                    labelBackgroundOpacity: 0,
                    labelFill: "rgba(0,255,185,0.55)",
                    labelFontSize: 9,
                    labelFontFamily: "Inter, sans-serif",
                    labelBackgroundFill: "rgba(0,0,40,0.85)",
                    labelPadding: [2, 4],
                    labelBackgroundRadius: 3,
                    curveOffset: 20,
                    cursor: "pointer",
                },
                state: {
                    active: {
                        stroke: "#00FFB9",
                        lineWidth: 2.5,
                        shadowColor: "#00FFB9",
                        shadowBlur: 10,
                        halo: 12,
                        haloOpacity: 0,
                        haloPointerEvents: "auto",
                        pointerEvents: "auto",
                        interactive: true,
                        zIndex: 15,
                        labelOpacity: 1,
                        labelBackgroundOpacity: 1,
                        labelFill: "#00FFB9",
                        opacity: 1,
                    },
                    activeOut: {
                        stroke: "#00FFB9",
                        lineWidth: 2.5,
                        shadowColor: "#00FFB9",
                        shadowBlur: 10,
                        labelOpacity: 1,
                        labelBackgroundOpacity: 1,
                        labelFill: "#00FFB9",
                        endArrowSize: 8,
                        halo: 12,
                        haloOpacity: 0,
                        haloPointerEvents: "auto",
                        pointerEvents: "auto",
                        interactive: true,
                        zIndex: 15,
                        opacity: 1,
                    },
                    activeIn: {
                        stroke: "#FF4081",
                        lineWidth: 2.5,
                        shadowColor: "#FF4081",
                        shadowBlur: 10,
                        labelOpacity: 1,
                        labelBackgroundOpacity: 1,
                        labelFill: "#FF4081",
                        endArrowSize: 8,
                        halo: 12,
                        haloOpacity: 0,
                        haloPointerEvents: "auto",
                        pointerEvents: "auto",
                        interactive: true,
                        zIndex: 15,
                        opacity: 1,
                    },
                    inactive: {
                        opacity: 0.4,
                        labelOpacity: 0,
                        labelBackgroundOpacity: 0,
                        halo: 0,
                        pointerEvents: "none",
                        haloPointerEvents: "none",
                        interactive: false,
                        zIndex: -2,
                    },
                    queryInactive: {
                        opacity: 0.08,
                        labelOpacity: 0,
                        labelBackgroundOpacity: 0,
                        halo: 0,
                        pointerEvents: "none",
                        haloPointerEvents: "none",
                        interactive: false,
                        zIndex: -3,
                    },
                    queryActiveEdge: {
                        stroke: "#00FFB9",
                        lineWidth: 2.5,
                        shadowColor: "#00FFB9",
                        shadowBlur: 10,
                        halo: 12,
                        haloOpacity: 0,
                        haloPointerEvents: "auto",
                        pointerEvents: "auto",
                        interactive: true,
                        labelOpacity: 1,
                        labelBackgroundOpacity: 1,
                        labelFill: "#00FFB9",
                        opacity: 1,
                        zIndex: 40,
                    },
                },
            },

            // ── Combo defaults ──
            combo: {
                type: "rect",
                style: {
                    zIndex: -5,
                    fill: (d) => (COLORS[d.id] || COLORS.other).comboFill,
                    fillOpacity: 1,
                    stroke: (d) => (COLORS[d.id] || COLORS.other).comboBorder,
                    lineWidth: 1.5,
                    lineDash: [6, 4],
                    radius: 16,
                    labelText: (d) => localizedComboLabel(d.id),
                    labelFill: (d) => (COLORS[d.id] || COLORS.other).stroke,
                    labelFontSize: 13,
                    labelFontWeight: 600,
                    labelFontFamily: "Inter, sans-serif",
                    labelPlacement: "top",
                    padding: 30,
                    cursor: "pointer",
                    collapsedMarker: false,
                },
                state: {
                    active: {
                        stroke: "#00FFB9",
                        lineWidth: 2,
                        zIndex: -3,
                    },
                    inactive: {
                        opacity: 0.15,
                        pointerEvents: "none",
                    },
                },
            },

            // ── Layout ──
            // Initial coordinates are already written into every node. Do
            // not ask G6 to resolve a non-existent "preset" layout plugin.
            layout: layoutMode === "preset"
                ? undefined
                : { ...LAYOUTS[layoutMode] },

            // ── Behaviours ──
            behaviors: [
                "drag-canvas",
                "zoom-canvas",
                {
                    type: "drag-element",
                    state: null, // Only drag the hovered node, not all 'selected' nodes
                },
            ],

            // ── Plugins ──
            plugins: [],

            // ── Animation (reduced duration for snappier interactions) ──
            animation: false,

            data,
        });

        const initialRender = graph.render();

        // Expose graph for chat.js linking
        window._g6Graph = graph;

        // ── Node click → add to query, or reactivate an existing query branch ──
        graph.on("node:click", async (evt) => {
            const nodeId = evt.target.id;

            if (queryBuilderState.active) {
                await selectOrActivateQueryNode(nodeId);
                return;
            }

            // Toggle off if clicking the already selected node
            if (selectedNodeId === nodeId) {
                clearSelection();
                closePanel();
                await restoreOverviewEdges();
                return;
            }

            selectNode(nodeId);
            // Open the panel immediately. Edge drawing is intentionally
            // serialized so rapid clicks cannot mutate G6 concurrently.
            queueIncidentEdgeRender(nodeId);
            if (relMode) {
                await showRelOnly(nodeId);
            } else {
                await showClassDetail(nodeId);
            }
        });

        // ── Shared tooltip: show on node hover, hide on leave ──
        const graphContainer = document.getElementById("graphContainer");

        graph.on("node:pointerenter", (evt) => {
            const context = getNodeTooltipContext(graph, evt);
            if (context) showNodeTooltip(context);
            else hideNodeTooltip();
        });

        graph.on("node:pointermove", (evt) => {
            const context = getNodeTooltipContext(graph, evt);
            if (context) showNodeTooltip(context);
            else hideNodeTooltip();
        });

        graph.on("node:pointerleave", hideNodeTooltip);
        graph.on("edge:pointermove", hideNodeTooltip);

        // G6 can miss node:pointerleave when an overlay such as the chat panel
        // takes over pointer targeting, so native boundaries also clear it.
        graphContainer.addEventListener("pointerleave", hideNodeTooltip, { passive: true });
        document.addEventListener("pointermove", (event) => {
            const previewCanvas = document.getElementById("queryPreviewCanvas");
            if (
                !graphContainer.contains(event.target)
                && !previewCanvas?.contains(event.target)
            ) {
                hideNodeTooltip();
            }
        }, { capture: true, passive: true });
        document.getElementById("chatPanel").addEventListener("pointerenter", hideNodeTooltip, { passive: true });
        window.addEventListener("blur", hideNodeTooltip);
        document.addEventListener("visibilitychange", () => {
            if (document.hidden) hideNodeTooltip();
        });

        // ── Canvas click → clear selection + close panel + hide edge popup ──
        // (skip if an edge was just clicked — guard prevents race condition)
        let edgeClickGuard = false;

        graph.on("canvas:click", async () => {
            if (edgeClickGuard) { edgeClickGuard = false; return; }
            if (queryBuilderState.active) return;
            clearSelection();
            closePanel();
            hideEdgePopup();
            await restoreOverviewEdges();
        });

        // ── Edge click → show action popup (preserve node selection) ──
        graph.on("edge:click", (evt) => {
            if (queryBuilderState.active) return;
            edgeClickGuard = true;
            setTimeout(() => { edgeClickGuard = false; }, 200);

            let edgeId = evt.target.id;
            let edgeData = graph.getEdgeData(edgeId);
            if (!edgeData) return;

            // Check if the clicked edge is inactive
            const edgeStates = graph.getElementState(edgeId);
            if (edgeStates.includes("inactive")) {
                // Try to find if there's any active edge directly underneath the click position
                const canvasEl = document.getElementById("graphContainer");
                const rect = canvasEl.getBoundingClientRect();
                const clientX = evt.client?.x ?? (evt.canvas?.x + rect.left) ?? rect.left + rect.width / 2;
                const clientY = evt.client?.y ?? (evt.canvas?.y + rect.top) ?? rect.top + rect.height / 2;

                const canvasPos = graph.getCanvasByClient({ x: clientX, y: clientY });
                let activeEdgeId = null;

                try {
                    const canvas = graph.getCanvas();
                    if (canvas && canvas.document && typeof canvas.document.elementsFromPointSync === "function") {
                        const picked = canvas.document.elementsFromPointSync(canvasPos.x, canvasPos.y) || [];
                        for (const shape of picked) {
                            if (shape && shape.id) {
                                const isEdge = !!graph.getEdgeData(shape.id);
                                if (isEdge) {
                                    const elStates = graph.getElementState(shape.id);
                                    if (elStates.includes("active") || elStates.includes("activeOut") || elStates.includes("activeIn")) {
                                        activeEdgeId = shape.id;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                } catch (err) {
                    console.warn("Fallback elements picking error:", err);
                }

                if (activeEdgeId) {
                    edgeId = activeEdgeId;
                    edgeData = graph.getEdgeData(edgeId);
                } else {
                    // No active edge under the cursor, treat it as a click on canvas (deselect)
                    clearSelection();
                    closePanel();
                    hideEdgePopup();
                    return;
                }
            }

            const relName = edgeData.data?.label || edgeId;
            const source = edgeData.source;
            const target = edgeData.target;
            const desc = edgeData.data?.description || "";
            const cardinality = edgeData.data?.cardinality || "";
            const relationships = edgeData.data?.relationships || null;

            // Position popup near the click
            const canvasEl = document.getElementById("graphContainer");
            const rect = canvasEl.getBoundingClientRect();
            const clientX = evt.client?.x ?? (evt.canvas?.x + rect.left) ?? rect.left + rect.width / 2;
            const clientY = evt.client?.y ?? (evt.canvas?.y + rect.top) ?? rect.top + rect.height / 2;

            showEdgePopup(
                relName,
                source,
                target,
                desc,
                cardinality,
                clientX,
                clientY,
                relationships,
            );
        });

        // ── Node click also hides edge popup ──
        graph.on("node:click", () => { hideEdgePopup(); });

        // ── Hover preview (only when nothing is selected) ──
        graph.on("node:mouseenter", (evt) => {
            if (queryBuilderState.active || selectedNodeId || graphMutationBusy) return;
            highlightNeighbors(evt.target.id, false);
        });

        graph.on("node:mouseleave", () => {
            if (queryBuilderState.active || selectedNodeId || graphMutationBusy) return;
            clearHighlight();
        });

        return initialRender;
    }

    // ══════════════════════════════════════════════════════
    //  Selection & Highlight
    // ══════════════════════════════════════════════════════
    function selectNode(nodeId) {
        selectedNodeId = nodeId;
        // Clear legend active states when focusing on a specific node
        document.querySelectorAll(".legend-item.active").forEach(el => el.classList.remove("active"));
    }
    // Expose for chat.js
    window._selectNode = selectNode;
    window._getSelectedNodeId = () => selectedNodeId;

    // ══════════════════════════════════════════════════════
    //  Transient SQL Query Builder
    // ══════════════════════════════════════════════════════
    function setQueryBuilderStatus(message, isError = false) {
        const status = document.getElementById("queryBuilderStatus");
        status.textContent = message || "";
        status.classList.toggle("error", isError);
    }

    function renderQuerySelectedNodes() {
        const container = document.getElementById("querySelectedNodes");
        const count = document.getElementById("querySelectedCount");
        container.replaceChildren();
        count.textContent = `${queryBuilderState.selectedNodes.length} / 16`;

        if (!queryBuilderState.selectedNodes.length) {
            const empty = document.createElement("span");
            empty.className = "query-empty-copy";
            empty.textContent = "请从右侧主图选择对象";
            container.appendChild(empty);
            return;
        }

        queryBuilderState.selectedNodes.forEach((nodeId, index) => {
            const chip = document.createElement("span");
            chip.className = "query-selected-chip";
            if (queryBuilderState.activeNodeId === nodeId) chip.classList.add("active");
            chip.title = queryBuilderState.activeNodeId === nodeId
                ? `${nodeId} 是当前关联起点`
                : `点击切换到 ${nodeId}，继续添加分支`;
            chip.addEventListener("click", () => activateQueryNode(nodeId));

            const order = document.createElement("span");
            order.className = "query-selected-chip-index";
            order.textContent = String(index + 1);

            const name = document.createElement("span");
            name.textContent = ontologyLabel(
                "node", nodeId, nodeId, nodeInfoCache.get(nodeId)?.data?.chineseName || "",
            );

            const remove = document.createElement("button");
            remove.type = "button";
            remove.textContent = "×";
            remove.title = `移出 ${nodeId}`;
            remove.setAttribute("aria-label", `移出 ${nodeId}`);
            remove.addEventListener("click", (event) => {
                event.stopPropagation();
                removeQueryNode(nodeId);
            });

            if (queryBuilderState.activeNodeId === nodeId) {
                const focus = document.createElement("span");
                focus.className = "query-selected-chip-focus";
                focus.textContent = "起点";
                chip.append(order, name, focus, remove);
            } else {
                chip.append(order, name, remove);
            }

            container.appendChild(chip);
        });
    }

    function queryPlanNodeSets() {
        const selected = new Set(queryBuilderState.selectedNodes);
        const bridge = new Set();
        const unconnected = new Set(queryBuilderState.plan?.unconnected || []);
        for (const node of queryBuilderState.plan?.nodes || []) {
            if (node.bridge) bridge.add(node.id);
        }
        return { selected, bridge, unconnected };
    }

    function applyQueryMainStates(searchQuery = "", force = false) {
        // The incident-edge layer is replaced asynchronously. Do not cache or
        // apply query states while that layer is temporarily empty; the render
        // worker performs one authoritative update after the new edges exist.
        if (!graph || !rawData || !queryBuilderState.active || graphMutationBusy) {
            return Promise.resolve();
        }
        const query = searchQuery.trim().toLowerCase();
        const { selected, bridge, unconnected } = queryPlanNodeSets();
        const activeNodeId = (
            queryBuilderState.activeNodeId
            && selected.has(queryBuilderState.activeNodeId)
        )
            ? queryBuilderState.activeNodeId
            : (queryBuilderState.selectedNodes.at(-1) || null);
        const relatedCandidates = new Set();
        // Only retain neighbors that have a relationship currently rendered
        // on the canvas. Using the full ontology adjacency here leaves bright
        // nodes whose corresponding edges are absent, which looks like
        // disconnected "floating" points.
        for (const edge of graph.getEdgeData()) {
            const sourceId = String(edge.source?.id || edge.source);
            const targetId = String(edge.target?.id || edge.target);
            if (sourceId === activeNodeId) relatedCandidates.add(targetId);
            if (targetId === activeNodeId) relatedCandidates.add(sourceId);
        }
        const states = {};
        const zOrder = {};
        for (const node of graph.getNodeData()) {
            if (selected.has(node.id)) {
                if (node.id === activeNodeId) {
                    states[node.id] = [
                        unconnected.has(node.id) ? "queryUnconnected" : "querySelected",
                    ];
                    zOrder[node.id] = 60;
                } else if (relatedCandidates.has(node.id)) {
                    // A previously selected object is still a direct neighbor
                    // of the current focus. Relationship visibility takes
                    // priority over its historical-selection state.
                    states[node.id] = ["queryRelatedSelected"];
                    zOrder[node.id] = 51;
                } else {
                    states[node.id] = ["queryPreviousSelected"];
                    zOrder[node.id] = 4;
                }
                continue;
            }
            if (bridge.has(node.id)) {
                states[node.id] = relatedCandidates.has(node.id)
                    ? ["queryBridge"]
                    : ["queryInactive"];
                zOrder[node.id] = relatedCandidates.has(node.id) ? 52 : 1;
                continue;
            }
            if (query) {
                const source = nodeInfoCache.get(node.id) || node;
                const label = String(source.data?.label || node.id).toLowerCase();
                const chineseName = String(source.data?.chineseName || "").toLowerCase();
                states[node.id] = (
                    label.includes(query) || chineseName.includes(query)
                ) ? ["active"] : ["queryInactive"];
                zOrder[node.id] = (
                    label.includes(query) || chineseName.includes(query)
                ) ? 50 : 1;
            } else if (selected.size && !relatedCandidates.has(node.id)) {
                states[node.id] = ["queryInactive"];
                zOrder[node.id] = 1;
            } else if (selected.size && relatedCandidates.has(node.id)) {
                // Match the normal browsing behavior: every endpoint of a
                // visible relationship is promoted together with its edge.
                states[node.id] = ["queryRelated"];
                zOrder[node.id] = 50;
            } else {
                states[node.id] = [];
                zOrder[node.id] = 10;
            }
        }
        const visibleQueryNodes = new Set([
            ...(activeNodeId ? [activeNodeId] : []),
            ...relatedCandidates,
        ]);
        for (const edge of graph.getEdgeData()) {
            const sourceId = String(edge.source?.id || edge.source);
            const targetId = String(edge.target?.id || edge.target);
            const touchesSelection = (
                sourceId === activeNodeId || targetId === activeNodeId
            );
            const staysInQueryFocus = (
                visibleQueryNodes.has(sourceId)
                && visibleQueryNodes.has(targetId)
            );
            states[edge.id] = (
                selected.size && touchesSelection && staysInQueryFocus
            ) ? ["queryActiveEdge"] : (selected.size ? ["queryInactive"] : []);
            zOrder[edge.id] = (
                selected.size && touchesSelection && staysInQueryFocus
            ) ? 40 : (selected.size ? -3 : 0);
        }
        for (const combo of graph.getComboData()) zOrder[combo.id] = -5;
        const focusAtRequest = activeNodeId;
        return _applyStates(states, { force }).then(async () => {
            if (
                !graph
                || !queryBuilderState.active
                || queryBuilderState.activeNodeId !== focusAtRequest
            ) return;
            const currentIds = new Set([
                ...graph.getNodeData().map((item) => item.id),
                ...graph.getEdgeData().map((item) => item.id),
                ...graph.getComboData().map((item) => item.id),
            ]);
            const currentZOrder = Object.fromEntries(
                Object.entries(zOrder).filter(([id]) => currentIds.has(id)),
            );
            await graph.setElementZIndex(currentZOrder);
        });
    }

    async function restoreDefaultGraphZOrder() {
        if (!graph) return;
        const zOrder = {};
        for (const node of graph.getNodeData()) zOrder[node.id] = 10;
        for (const edge of graph.getEdgeData()) zOrder[edge.id] = 0;
        for (const combo of graph.getComboData()) zOrder[combo.id] = -5;
        await graph.setElementZIndex(zOrder);
    }

    function destroyQueryPreviewGraph() {
        if (queryPreviewGraph) {
            try {
                queryPreviewGraph.destroy();
            } catch (error) {
                console.debug("Query preview graph cleanup skipped:", error);
            }
        }
        queryPreviewGraph = null;
        queryBuilderState.selectedPreviewJoin = null;
        const viewButton = document.getElementById("btnViewQueryRelationship");
        viewButton.disabled = true;
        viewButton.title = "请先在小图中选择 Relationship";
        hideNodeTooltip();
        document.getElementById("queryPreviewCanvas").replaceChildren();
    }

    function relationshipNameForPhysicalField(fieldName) {
        const baseName = String(fieldName || "").replace(/Id$/i, "");
        const snakeName = baseName
            .replace(/([A-Z]+)([A-Z][a-z])/g, "$1_$2")
            .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
            .replace(/[^A-Za-z0-9]+/g, "_")
            .replace(/^_+|_+$/g, "")
            .toUpperCase();
        return snakeName ? `HAS_${snakeName}` : "PHYSICAL_JOIN";
    }

    function relationshipForPhysicalJoin(join) {
        const expectedName = relationshipNameForPhysicalField(join?.from_field);
        const candidates = [...edgeInfoById.values()].filter((edge) => (
            edge.source === join?.from_table
            && edge.target === join?.to_table
        ));
        return (
            candidates.find((edge) => edge.data?.label === expectedName)
            || candidates[0]
            || null
        );
    }

    async function viewSelectedQueryRelationship() {
        const selectedJoin = queryBuilderState.selectedPreviewJoin;
        if (!selectedJoin) {
            setQueryBuilderStatus("请先在小图中点击一条 Relationship", true);
            return;
        }
        const relationship = relationshipForPhysicalJoin(selectedJoin);
        const relationshipName = (
            relationship?.data?.label
            || relationshipNameForPhysicalField(selectedJoin.from_field)
        );
        const description = (
            `${selectedJoin.from_table}.${selectedJoin.from_field} = `
            + `${selectedJoin.to_table}.${selectedJoin.to_field}`
        );
        const button = document.getElementById("btnViewQueryRelationship");
        const rect = button.getBoundingClientRect();
        await showEdgePopup(
            relationshipName,
            selectedJoin.from_table,
            selectedJoin.to_table,
            description,
            relationship?.data?.cardinality || "MANY_TO_ONE",
            rect.right,
            rect.bottom + 8,
        );
    }

    function queryJoinPairKey(left, right) {
        return [left, right].sort().join("|");
    }

    function samePhysicalJoin(left, right) {
        return ["from_table", "from_field", "to_table", "to_field"]
            .every((key) => left?.[key] === right?.[key]);
    }

    function queryJoinCandidateGroup(edge) {
        const pairKey = queryJoinPairKey(edge.from_table, edge.to_table);
        return (queryBuilderState.plan?.join_candidates || [])
            .find((item) => item.pair_key === pairKey) || null;
    }

    function setQueryRelationshipButton(edge) {
        const viewButton = document.getElementById("btnViewQueryRelationship");
        viewButton.disabled = !edge;
        viewButton.title = edge
            ? `查看 ${edge.from_table} → ${edge.to_table} Relationship`
            : "请先在小图中选择 Relationship";
    }

    function renderQueryJoinChoices(edge) {
        const edgeDetail = document.getElementById("queryEdgeDetail");
        const group = queryJoinCandidateGroup(edge);
        const pairKey = queryJoinPairKey(edge.from_table, edge.to_table);
        queryBuilderState.selectedPreviewJoin = { ...edge };
        queryBuilderState.activeJoinPairKey = pairKey;
        setQueryRelationshipButton(edge);
        edgeDetail.replaceChildren();

        if (!group || group.candidates.length <= 1) {
            edgeDetail.textContent = (
                `${edge.from_table}.${edge.from_field} = `
                + `${edge.to_table}.${edge.to_field}`
            );
            return;
        }

        const title = document.createElement("div");
        title.className = "query-join-choice-title";
        title.textContent = `${group.tables.join(" ↔ ")} 有 ${group.candidates.length} 条物理关联，请选择：`;
        edgeDetail.appendChild(title);

        const choices = document.createElement("div");
        choices.className = "query-join-choices";
        group.candidates.forEach((candidate, index) => {
            const label = document.createElement("label");
            label.className = "query-join-choice";
            if (samePhysicalJoin(candidate, group.selected)) label.classList.add("selected");

            const radio = document.createElement("input");
            radio.type = "radio";
            radio.name = `query-join-${pairKey}`;
            radio.value = String(index);
            radio.checked = samePhysicalJoin(candidate, group.selected);
            radio.addEventListener("change", async () => {
                if (!radio.checked) return;
                queryBuilderState.joinOverrides.set(pairKey, { ...candidate });
                queryBuilderState.activeJoinPairKey = pairKey;
                setQueryBuilderStatus(
                    `已选择 ${candidate.from_table}.${candidate.from_field} = ${candidate.to_table}.${candidate.to_field}`,
                );
                await requestQueryBuilderPlan();
            });

            const text = document.createElement("span");
            text.textContent = (
                `${candidate.from_table}.${candidate.from_field} = `
                + `${candidate.to_table}.${candidate.to_field}`
            );
            label.append(radio, text);
            choices.appendChild(label);
        });
        edgeDetail.appendChild(choices);
    }

    async function selectQueryPreviewEdge(edgeId, edge) {
        renderQueryJoinChoices(edge);
        const states = {};
        for (const item of queryPreviewGraph.getEdgeData()) {
            states[item.id] = item.id === edgeId ? ["selected"] : [];
        }
        await queryPreviewGraph.setElementState(states);
    }

    async function renderQueryPreviewGraph() {
        destroyQueryPreviewGraph();
        const plan = queryBuilderState.plan;
        const canvas = document.getElementById("queryPreviewCanvas");
        const empty = document.getElementById("queryPreviewEmpty");
        const edgeDetail = document.getElementById("queryEdgeDetail");
        if (!plan?.nodes?.length) {
            empty.hidden = false;
            edgeDetail.textContent = "点击关系线查看；橙色关系线可选择物理 JOIN 条件";
            return;
        }

        empty.hidden = true;
        if (!queryBuilderState.activeJoinPairKey) {
            edgeDetail.textContent = "点击关系线查看；橙色关系线可选择物理 JOIN 条件";
        }
        const selected = new Set(plan.selected_nodes || []);
        const unconnected = new Set(plan.unconnected || []);
        const previewNodes = plan.nodes.map((node) => {
            const sourceNode = nodeInfoCache.get(node.id);
            return {
                id: node.id,
                data: {
                    ...(sourceNode?.data || {}),
                    label: sourceNode?.data?.label || node.id,
                    type: sourceNode?.data?.type || "class",
                    selected: selected.has(node.id),
                    bridge: node.bridge,
                    unconnected: unconnected.has(node.id),
                },
            };
        });
        const ambiguousPairs = new Set(
            (plan.join_candidates || [])
                .filter((item) => item.candidates.length > 1)
                .map((item) => item.pair_key),
        );
        const previewEdges = plan.joins.map((edge, index) => ({
            id: `query-edge-${index}`,
            source: edge.from_table,
            target: edge.to_table,
            data: {
                edgeIndex: index,
                ambiguous: ambiguousPairs.has(
                    queryJoinPairKey(edge.from_table, edge.to_table),
                ),
            },
        }));

        queryPreviewGraph = new G6.Graph({
            container: canvas,
            width: canvas.clientWidth,
            height: canvas.clientHeight,
            autoFit: "view",
            padding: [34, 26, 38, 26],
            animation: false,
            behaviors: ["drag-element", "drag-canvas", "zoom-canvas"],
            layout: {
                type: "dagre",
                rankdir: "LR",
                nodesep: 22,
                ranksep: 72,
            },
            node: {
                type: "circle",
                style: {
                    size: (d) => d.data?.selected ? 38 : 30,
                    fill: (d) => {
                        if (d.data?.unconnected) return "#8F333D";
                        return d.data?.selected ? "#008C76" : "#245F91";
                    },
                    stroke: (d) => {
                        if (d.data?.unconnected) return "#FF6B6B";
                        return d.data?.selected ? "#00FFB9" : "#4CA6FF";
                    },
                    lineWidth: (d) => d.data?.selected ? 3 : 2,
                    labelText: (d) => d.data?.displayLabel || d.data?.label || d.id,
                    labelFill: "#DDEBF0",
                    labelFontSize: 9,
                    labelFontWeight: 600,
                    labelPlacement: "bottom",
                    labelOffsetY: 5,
                    cursor: "pointer",
                },
            },
            edge: {
                type: "line",
                style: {
                    stroke: (d) => d.data?.ambiguous ? "#FFB45C" : "#4CA6FF",
                    lineWidth: (d) => d.data?.ambiguous ? 2.4 : 1.6,
                    endArrow: true,
                    endArrowSize: 6,
                    cursor: "pointer",
                },
                state: {
                    selected: {
                        stroke: "#00FFB9",
                        lineWidth: 3,
                        shadowColor: "#00FFB9",
                        shadowBlur: 8,
                        zIndex: 5,
                    },
                },
            },
            data: {
                nodes: previewNodes,
                edges: previewEdges,
            },
        });

        queryPreviewGraph.on("edge:click", async (event) => {
            const edgeData = queryPreviewGraph.getEdgeData(event.target.id);
            const edge = plan.joins[edgeData?.data?.edgeIndex];
            if (!edge) return;
            await selectQueryPreviewEdge(event.target.id, edge);
        });

        queryPreviewGraph.on("node:click", (event) => {
            hideNodeTooltip();
            const nodeId = event.target.id;
            if (selected.has(nodeId)) {
                activateQueryNode(nodeId);
                return;
            }
            queryBuilderState.activeJoinPairKey = null;
            queryBuilderState.selectedPreviewJoin = null;
            setQueryRelationshipButton(null);
            edgeDetail.textContent = `${nodeId} 是系统补充的中间对象，仅用于连接物理 JOIN。`;
        });

        queryPreviewGraph.on("node:pointerenter", (event) => {
            const context = getNodeTooltipContext(queryPreviewGraph, event, 38);
            if (context) showNodeTooltip(context);
            else hideNodeTooltip();
        });
        queryPreviewGraph.on("node:pointermove", (event) => {
            const context = getNodeTooltipContext(queryPreviewGraph, event, 38);
            if (context) showNodeTooltip(context);
            else hideNodeTooltip();
        });
        queryPreviewGraph.on("node:pointerleave", hideNodeTooltip);
        queryPreviewGraph.on("edge:pointermove", hideNodeTooltip);
        canvas.addEventListener("pointerleave", hideNodeTooltip, { passive: true });

        try {
            await queryPreviewGraph.render();
            if (queryBuilderState.activeJoinPairKey) {
                const edgeIndex = plan.joins.findIndex((edge) => (
                    queryJoinPairKey(edge.from_table, edge.to_table)
                    === queryBuilderState.activeJoinPairKey
                ));
                if (edgeIndex >= 0) {
                    await selectQueryPreviewEdge(
                        `query-edge-${edgeIndex}`,
                        plan.joins[edgeIndex],
                    );
                }
            }
        } catch (error) {
            console.error("Query preview graph render failed:", error);
            empty.hidden = false;
            empty.textContent = "关联数据已生成，但小图渲染失败";
        }
    }

    function renderQueryBuilderPlan() {
        renderQuerySelectedNodes();
        const plan = queryBuilderState.plan;
        const previewSection = document.querySelector(".query-preview-section");
        const summary = document.getElementById("queryPlanSummary");
        const warning = document.getElementById("queryBuilderWarning");
        const sqlPreview = document.getElementById("querySqlPreview");
        const dialect = document.getElementById("querySqlDialect");
        const hasSql = Boolean(plan?.sql);
        const hasSelection = queryBuilderState.selectedNodes.length > 0;

        previewSection.classList.toggle("loading", queryBuilderState.loading);
        dialect.textContent = SQL_DIALECTS[currentSqlDialect].label;
        if (plan?.nodes?.length) {
            const bridgeCount = plan.nodes.filter((node) => node.bridge).length;
            summary.textContent = (
                `${plan.selected_nodes.length} 个已选 · ${bridgeCount} 个中间对象`
            );
        } else {
            summary.textContent = hasSelection ? "正在规划" : "等待选择";
        }

        const warningText = queryBuilderState.error
            || (plan?.warnings || []).join("\n");
        warning.hidden = !warningText;
        warning.textContent = warningText;

        sqlPreview.textContent = hasSql
            ? plan.sql
            : "-- 请选择至少一个查询对象";
        document.getElementById("btnClearQuery").disabled = !hasSelection;
        document.getElementById("btnClearQueryTop").disabled = !hasSelection;
        document.getElementById("btnCopyQuerySql").disabled = !hasSql;
        document.getElementById("btnFitQueryPreview").disabled = (
            queryBuilderState.loading || !plan?.nodes?.length
        );
        document.getElementById("btnContinueQuerySql").disabled = !hasSql;
        applyQueryMainStates(document.getElementById("searchInput").value);
    }

    async function requestQueryBuilderPlan() {
        const revision = ++queryBuilderState.requestRevision;
        queryBuilderState.error = "";
        queryBuilderState.selectedPreviewJoin = null;
        const viewRelationshipButton = document.getElementById("btnViewQueryRelationship");
        viewRelationshipButton.disabled = true;
        viewRelationshipButton.title = "请先在小图中选择 Relationship";
        hideEdgePopup();
        queryBuilderState.loading = queryBuilderState.selectedNodes.length > 0;
        if (!queryBuilderState.selectedNodes.length) {
            queryBuilderState.plan = null;
            queryBuilderState.loading = false;
            queryBuilderState.activeJoinPairKey = null;
            queryBuilderState.joinOverrides.clear();
            renderQueryBuilderPlan();
            await renderQueryPreviewGraph();
            setQueryBuilderStatus("");
            return;
        }

        renderQueryBuilderPlan();
        setQueryBuilderStatus("正在读取物理 Schema…");
        try {
            const response = await fetch("/api/sql-builder/plan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    selected_nodes: queryBuilderState.selectedNodes,
                    dialect: currentSqlDialect,
                    join_overrides: [...queryBuilderState.joinOverrides.values()],
                }),
            });
            const payload = await response.json();
            if (revision !== queryBuilderState.requestRevision) return;
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error("查询规划服务尚未加载，请重启后端服务");
                }
                throw new Error(payload.detail || payload.error || `HTTP ${response.status}`);
            }
            queryBuilderState.plan = payload;
            const validPairKeys = new Set(
                (payload.join_candidates || []).map((item) => item.pair_key),
            );
            for (const pairKey of queryBuilderState.joinOverrides.keys()) {
                if (!validPairKeys.has(pairKey)) {
                    queryBuilderState.joinOverrides.delete(pairKey);
                }
            }
            if (
                queryBuilderState.activeJoinPairKey
                && !validPairKeys.has(queryBuilderState.activeJoinPairKey)
            ) {
                queryBuilderState.activeJoinPairKey = null;
            }
            queryBuilderState.error = "";
            setQueryBuilderStatus(
                payload.warnings?.length
                    ? "参考 Schema 已校验，请检查关联语义提示"
                    : "参考 Schema 已校验 · 未连接当前运行库",
                Boolean(payload.unconnected?.length),
            );
        } catch (error) {
            if (revision !== queryBuilderState.requestRevision) return;
            queryBuilderState.plan = null;
            queryBuilderState.error = error.message || "查询规划失败";
            setQueryBuilderStatus(queryBuilderState.error, true);
        } finally {
            if (revision !== queryBuilderState.requestRevision) return;
            queryBuilderState.loading = false;
            renderQueryBuilderPlan();
            await renderQueryPreviewGraph();
        }
    }

    async function activateQueryNode(nodeId) {
        if (
            !queryBuilderState.active
            || !queryBuilderState.selectedNodes.includes(nodeId)
        ) return;
        queryBuilderState.activeNodeId = nodeId;
        renderQuerySelectedNodes();
        applyQueryMainStates();
        queueIncidentEdgeRender(nodeId);
        setQueryBuilderStatus(`已切换关联起点：${nodeId}，可继续选择其它分支`);
    }

    async function selectOrActivateQueryNode(nodeId) {
        if (!queryBuilderState.active) return;
        if (queryBuilderState.selectedNodes.includes(nodeId)) {
            await activateQueryNode(nodeId);
            return;
        }
        if (queryBuilderState.selectedNodes.length >= 16) {
            setQueryBuilderStatus("最多可选择 16 个查询对象", true);
            return;
        }
        queryBuilderState.selectedNodes.push(nodeId);
        queryBuilderState.activeNodeId = nodeId;
        renderQuerySelectedNodes();
        applyQueryMainStates();
        queueIncidentEdgeRender(nodeId);
        await requestQueryBuilderPlan();
    }

    async function removeQueryNode(nodeId) {
        if (!queryBuilderState.active) return;
        const index = queryBuilderState.selectedNodes.indexOf(nodeId);
        if (index < 0) return;
        queryBuilderState.selectedNodes.splice(index, 1);
        if (queryBuilderState.activeNodeId === nodeId) {
            queryBuilderState.activeNodeId = (
                queryBuilderState.selectedNodes.at(-1) || null
            );
        }
        renderQuerySelectedNodes();
        applyQueryMainStates();
        if (queryBuilderState.activeNodeId) {
            queueIncidentEdgeRender(queryBuilderState.activeNodeId);
        } else {
            await restoreOverviewEdges();
        }
        await requestQueryBuilderPlan();
    }

    async function enterQueryBuilderMode() {
        if (queryBuilderState.active) return;
        queryBuilderState.active = true;
        queryBuilderState.previousSelectedNodeId = selectedNodeId;
        queryBuilderState.selectedNodes = [];
        queryBuilderState.activeNodeId = null;
        queryBuilderState.plan = null;
        queryBuilderState.error = "";
        queryBuilderState.selectedPreviewJoin = null;
        queryBuilderState.activeJoinPairKey = null;
        queryBuilderState.joinOverrides.clear();
        selectedNodeId = null;

        document.body.classList.add("query-builder-mode");
        document.getElementById("queryBuilderPanel").classList.remove("query-builder-hidden");
        const toggle = document.getElementById("btnQueryMode");
        toggle.classList.add("active");
        toggle.setAttribute("aria-pressed", "true");
        closePanel();
        hideEdgePopup();
        await restoreOverviewEdges();
        renderQueryBuilderPlan();
        await renderQueryPreviewGraph();
        setQueryBuilderStatus("点击主图节点开始构建查询");
    }

    async function exitQueryBuilderMode() {
        if (!queryBuilderState.active) return;
        const previousNodeId = queryBuilderState.previousSelectedNodeId;
        queryBuilderState.requestRevision += 1;
        queryBuilderState.active = false;
        queryBuilderState.loading = false;
        queryBuilderState.selectedNodes = [];
        queryBuilderState.activeNodeId = null;
        queryBuilderState.plan = null;
        queryBuilderState.error = "";
        queryBuilderState.selectedPreviewJoin = null;
        queryBuilderState.activeJoinPairKey = null;
        queryBuilderState.joinOverrides.clear();
        queryBuilderState.previousSelectedNodeId = null;

        document.body.classList.remove("query-builder-mode");
        document.getElementById("queryBuilderPanel").classList.add("query-builder-hidden");
        const toggle = document.getElementById("btnQueryMode");
        toggle.classList.remove("active");
        toggle.setAttribute("aria-pressed", "false");
        hideEdgePopup();
        destroyQueryPreviewGraph();
        await _applyStates({});
        await restoreDefaultGraphZOrder();
        if (previousNodeId && nodeInfoCache.has(previousNodeId)) {
            selectNode(previousNodeId);
            queueIncidentEdgeRender(previousNodeId);
            await showClassDetail(previousNodeId);
        } else {
            selectedNodeId = null;
            await restoreOverviewEdges();
        }
    }

    async function toggleQueryBuilderMode() {
        if (queryBuilderState.active) await exitQueryBuilderMode();
        else await enterQueryBuilderMode();
    }

    async function copyQuerySql() {
        const sql = queryBuilderState.plan?.sql;
        if (!sql) return;
        try {
            await navigator.clipboard.writeText(sql);
        } catch (_) {
            const textarea = document.createElement("textarea");
            textarea.value = sql;
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand("copy");
            textarea.remove();
        }
        const copyButton = document.getElementById("btnCopyQuerySql");
        clearTimeout(queryCopyFeedbackTimer);
        setIconContent(copyButton, "check", "已复制", { size: 12 });
        copyButton.classList.add("success");
        queryCopyFeedbackTimer = setTimeout(() => {
            setIconContent(copyButton, "copy", "复制", { size: 12 });
            copyButton.classList.remove("success");
        }, 1600);
        setQueryBuilderStatus("SQL 已复制");
    }

    async function fitQueryPreview() {
        if (!queryPreviewGraph) {
            setQueryBuilderStatus("请先选择查询对象", true);
            return;
        }
        try {
            await queryPreviewGraph.fitView();
            setQueryBuilderStatus("小图已适应当前窗口");
        } catch (error) {
            setQueryBuilderStatus(error.message || "小图适应失败", true);
        }
    }

    async function continueQueryInAssistant() {
        const sql = queryBuilderState.plan?.sql;
        if (!sql) return;
        if (typeof window._continueSqlDraft !== "function") {
            setQueryBuilderStatus("SQL 助手尚未加载完成", true);
            return;
        }
        try {
            await window._continueSqlDraft(
                queryBuilderState.selectedNodes,
                sql,
            );
            setQueryBuilderStatus("已将对象和 SQL 草稿送入助手");
        } catch (error) {
            setQueryBuilderStatus(error.message || "无法打开 SQL 助手", true);
        }
    }

    async function clearQueryBuilderSelection() {
        queryBuilderState.selectedNodes = [];
        queryBuilderState.activeNodeId = null;
        queryBuilderState.activeJoinPairKey = null;
        queryBuilderState.joinOverrides.clear();
        await restoreOverviewEdges();
        await requestQueryBuilderPlan();
        setQueryBuilderStatus("查询已清空");
    }

    function setupQueryBuilder() {
        document.getElementById("btnQueryMode").addEventListener(
            "click",
            toggleQueryBuilderMode,
        );
        document.getElementById("btnCloseQueryMode").addEventListener(
            "click",
            exitQueryBuilderMode,
        );
        document.getElementById("btnClearQuery").addEventListener(
            "click",
            clearQueryBuilderSelection,
        );
        document.getElementById("btnClearQueryTop").addEventListener(
            "click",
            clearQueryBuilderSelection,
        );
        document.getElementById("btnCopyQuerySql").addEventListener(
            "click",
            copyQuerySql,
        );
        document.getElementById("btnFitQueryPreview").addEventListener(
            "click",
            fitQueryPreview,
        );
        document.getElementById("btnViewQueryRelationship").addEventListener(
            "click",
            viewSelectedQueryRelationship,
        );
        document.getElementById("btnContinueQuerySql").addEventListener(
            "click",
            continueQueryInAssistant,
        );
        document.addEventListener("keydown", (event) => {
            if (
                event.key === "Escape"
                && queryBuilderState.active
                && !["INPUT", "TEXTAREA", "SELECT"].includes(event.target?.tagName)
            ) {
                exitQueryBuilderMode();
            }
        });
        window.addEventListener("camstar:sql-dialect-change", () => {
            if (queryBuilderState.active && queryBuilderState.selectedNodes.length) {
                requestQueryBuilderPlan();
            } else if (queryBuilderState.active) {
                renderQueryBuilderPlan();
            }
        });
        if ("ResizeObserver" in window) {
            const previewCanvas = document.getElementById("queryPreviewCanvas");
            const previewObserver = new ResizeObserver(() => {
                if (queryPreviewGraph) {
                    queryPreviewGraph.resize(
                        previewCanvas.clientWidth,
                        previewCanvas.clientHeight,
                    );
                }
            });
            previewObserver.observe(previewCanvas);
        }
    }

    async function hideAllCanvasEdges() {
        if (!graph) return;
        edgeRenderToken++;
        pendingEdgeNodeId = null;
        if (edgeRenderWorker) {
            try { await edgeRenderWorker; } catch (_) {}
        }
        await clearHighlight();
        const edgeIds = graph.getEdgeData().map((edge) => edge.id);
        if (!edgeIds.length) return;
        graph.removeEdgeData(edgeIds);
        await graph.draw();
    }

    async function restoreOverviewEdges() {
        if (!graph || !rawData) return;
        await hideAllCanvasEdges();
        setFocusBackdrop(null);
        const overviewEdges = buildGraphData(
            { nodes: [], edges: overviewApiEdges },
            false,
        ).edges;
        if (overviewEdges.length) graph.addEdgeData(overviewEdges);
        await graph.draw();
    }

    async function locateNodeWithoutEdges(nodeId, openDetail = true) {
        if (!graph || !nodeInfoCache.has(nodeId)) return;
        selectNode(nodeId);
        await hideAllCanvasEdges();
        await _applyStates({ [nodeId]: ["selected"] });
        await graph.focusElement(nodeId, true);
        if (openDetail) await showClassDetail(nodeId);
    }

    window._locateNodeWithoutEdges = locateNodeWithoutEdges;

    async function focusRelationshipPair(sourceId, targetId, relationshipName) {
        if (!graph || !rawData || !nodeInfoCache.has(sourceId) || !nodeInfoCache.has(targetId)) return;
        const token = ++edgeRenderToken;
        pendingEdgeNodeId = null;
        graphMutationBusy = true;
        try {
            await clearHighlight();
            if (token !== edgeRenderToken) return;

            const currentEdgeIds = graph.getEdgeData().map((edge) => edge.id);
            if (currentEdgeIds.length) {
                graph.removeEdgeData(currentEdgeIds);
                await graph.draw();
            }
            if (token !== edgeRenderToken) return;

            const pairEdges = [...edgeInfoById.values()].filter((edge) => {
                const sameDirection = edge.source === sourceId && edge.target === targetId;
                const reverseDirection = edge.source === targetId && edge.target === sourceId;
                if (!sameDirection && !reverseDirection) return false;
                return !relationshipName || edge.data?.label === relationshipName;
            });
            const visiblePairEdges = pairEdges.length
                ? pairEdges
                : [...edgeInfoById.values()].filter((edge) => (
                    (edge.source === sourceId && edge.target === targetId)
                    || (edge.source === targetId && edge.target === sourceId)
                ));
            if (visiblePairEdges.length) {
                graph.addEdgeData(buildGraphData(
                    { nodes: [], edges: visiblePairEdges },
                    false,
                ).edges);
            }
            await graph.draw();
            if (token !== edgeRenderToken) return;

            const focusNodeId = selectedNodeId === targetId ? targetId : sourceId;
            const counterpartId = focusNodeId === sourceId ? targetId : sourceId;
            setFocusBackdrop(focusNodeId, new Set([counterpartId]), 0.015);
            const states = {
                [focusNodeId]: ["selected"],
                [counterpartId]: ["active"],
            };
            for (const edge of graph.getEdgeData()) {
                states[edge.id] = edge.source === focusNodeId ? ["activeOut"] : ["activeIn"];
            }
            await _applyStates(states, { force: true });

            if (typeof graph.focusElements === "function") {
                await graph.focusElements([focusNodeId, counterpartId], true);
            } else {
                await graph.focusElement(focusNodeId, true);
            }
        } finally {
            if (token === edgeRenderToken) graphMutationBusy = false;
        }
    }

    function queueIncidentEdgeRender(nodeId) {
        pendingEdgeNodeId = nodeId;
        edgeRenderToken++;
        if (edgeRenderWorker) return;
        edgeRenderWorker = drainIncidentEdgeRenders()
            .catch((error) => {
                console.error("Incident edge render failed:", error);
            })
            .finally(() => {
                edgeRenderWorker = null;
                // A click could arrive after the worker's last loop condition.
                if (pendingEdgeNodeId) queueIncidentEdgeRender(pendingEdgeNodeId);
            });
    }

    function isCurrentGraphFocus(nodeId) {
        return queryBuilderState.active
            ? queryBuilderState.activeNodeId === nodeId
            : selectedNodeId === nodeId;
    }

    async function drainIncidentEdgeRenders() {
        while (pendingEdgeNodeId) {
            // Coalesce rapid clicks: only the newest pending node is rendered.
            const nodeId = pendingEdgeNodeId;
            pendingEdgeNodeId = null;
            await renderIncidentEdges(nodeId);
        }
    }

    async function renderIncidentEdges(nodeId) {
        if (!graph || !rawData) return;
        const token = edgeRenderToken;
        graphMutationBusy = true;
        try {
            // Finish clearing the previous focus state before removing its
            // edges. Otherwise an older async G6 state update can repaint
            // stale neighbors after the new edge layer has been installed.
            await clearHighlight();
            if (token !== edgeRenderToken || !isCurrentGraphFocus(nodeId)) return;

            const currentEdgeIds = graph.getEdgeData().map((edge) => edge.id);
            if (currentEdgeIds.length) {
                graph.removeEdgeData(currentEdgeIds);
                // Commit removals before reusing any of the same ontology edge
                // IDs in the next focus layer. Removing and re-adding an edge
                // in one G6 draw cycle can leave its data present while its
                // canvas shape remains disposed.
                await graph.draw();
                if (token !== edgeRenderToken || !isCurrentGraphFocus(nodeId)) return;
            }

            const adjacency = adjacencyIndex?.get(nodeId);
            const incidentEdgeIds = [
                ...(adjacency?.outgoing || []),
                ...(adjacency?.incoming || []),
            ];
            const incidentApiEdges = incidentEdgeIds
                .map((edgeId) => edgeInfoById.get(edgeId))
                .filter(Boolean);

            // Collapse parallel relations to one representative edge per neighbor.
            // Prefer neighbors with more relations, then use a stable name order.
            const byNeighbor = new Map();
            for (const edge of incidentApiEdges) {
                const neighbor = edge.source === nodeId ? edge.target : edge.source;
                if (!byNeighbor.has(neighbor)) byNeighbor.set(neighbor, []);
                byNeighbor.get(neighbor).push(edge);
            }
            const visibleGroups = [...byNeighbor.entries()]
                .sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]));
            const visibleApiEdges = visibleGroups.map(([neighbor, edges]) => {
                const representative = edges[0];
                if (edges.length === 1) return representative;
                const firstLabel = representative.data?.label || "关系";
                return {
                    ...representative,
                    data: {
                        ...representative.data,
                        label: `${firstLabel} (+${edges.length - 1})`,
                        description: `${nodeId} 与 ${neighbor} 之间共 ${edges.length} 条关系；详情面板中可查看全部。`,
                        relationCount: edges.length,
                        relationships: edges.map((edge) => ({
                            source: edge.source,
                            target: edge.target,
                            relName: edge.data?.label || edge.id,
                            desc: edge.data?.description || "",
                            cardinality: edge.data?.cardinality || "",
                        })),
                    },
                };
            });

            // Yield once so the selected state and detail panel paint first.
            await new Promise((resolve) => requestAnimationFrame(resolve));
            if (token !== edgeRenderToken || !isCurrentGraphFocus(nodeId)) return;
            if (visibleApiEdges.length) {
                const incidentEdges = buildGraphData(
                    { nodes: [], edges: visibleApiEdges },
                    false,
                ).edges;
                graph.addEdgeData(incidentEdges);
            }
            await graph.draw();
        } finally {
            graphMutationBusy = false;
        }

        if (
            queryBuilderState.active
            && token === edgeRenderToken
            && isCurrentGraphFocus(nodeId)
            && !pendingEdgeNodeId
        ) {
            pendingHighlightClear = false;
            // Newly-created G6 edge shapes must receive their complete state,
            // even when their ontology IDs were present in an older layer.
            await applyQueryMainStates(
                document.getElementById("searchInput").value,
                true,
            );
        } else if (pendingHighlightClear || !selectedNodeId) {
            pendingHighlightClear = false;
            await clearHighlight();
        } else if (
            token === edgeRenderToken
            && selectedNodeId === nodeId
            && !pendingEdgeNodeId
        ) {
            await highlightNeighbors(nodeId, true);
        }
    }

    function clearSelection() {
        edgeRenderToken++;
        pendingEdgeNodeId = null;
        selectedNodeId = null;
        setFocusBackdrop(null);
        if (graphMutationBusy) {
            pendingHighlightClear = true;
        } else {
            clearHighlight();
        }
        // Clear legend active states
        document.querySelectorAll(".legend-item.active").forEach(el => el.classList.remove("active"));
    }

    // G6 state transitions are asynchronous. Serialize and coalesce them so
    // rapid clicks/hover changes cannot apply an obsolete highlight after a
    // newer selection has already replaced the visible edge layer.
    let _prevStates = Object.create(null);
    let stateRevision = 0;
    let stateApplyChain = Promise.resolve();

    function sameState(previous, next) {
        return Boolean(previous)
            && previous.length === next.length
            && previous.every((value, index) => value === next[index]);
    }

    function _applyStates(states, { force = false } = {}) {
        const requested = Object.create(null);
        for (const [id, values] of Object.entries(states || {})) {
            requested[id] = [...values];
        }
        const revision = ++stateRevision;

        stateApplyChain = stateApplyChain
            .catch((error) => {
                console.debug("Previous graph state update skipped:", error);
            })
            .then(async () => {
                if (!graph || revision !== stateRevision) return;

                const currentIds = new Set([
                    ...graph.getNodeData().map((item) => item.id),
                    ...graph.getEdgeData().map((item) => item.id),
                    ...graph.getComboData().map((item) => item.id),
                ]);
                const diff = {};
                const ids = new Set([
                    ...Object.keys(_prevStates),
                    ...Object.keys(requested),
                ]);
                for (const id of ids) {
                    if (!currentIds.has(id)) continue;
                    const previous = _prevStates[id] || [];
                    const next = requested[id] || [];
                    if (force || !sameState(previous, next)) diff[id] = next;
                }
                if (Object.keys(diff).length) {
                    await graph.setElementState(diff);
                }
                // Dynamic relationship layers remove and later re-add edges,
                // sometimes with the same ontology IDs. Never remember state
                // for an element that was absent at apply time; otherwise its
                // replacement can be mistaken for an already-styled edge and
                // remain in the default dim layer.
                const currentSnapshot = Object.create(null);
                for (const [id, values] of Object.entries(requested)) {
                    if (currentIds.has(id)) currentSnapshot[id] = values;
                }
                _prevStates = currentSnapshot;
            });

        return stateApplyChain;
    }

    function setFocusBackdrop(focusedNodeId, visibleNeighborIds = new Set(), backgroundOpacity = 0.12) {
        if (!graph) return;
        const enabled = Boolean(focusedNodeId);
        graph.updateNodeData(graph.getNodeData().map((node) => {
            const isVisible = !enabled
                || node.id === focusedNodeId
                || visibleNeighborIds.has(node.id);
            return {
                id: node.id,
                style: {
                    ...(node.style || {}),
                    opacity: isVisible ? 1 : backgroundOpacity,
                    labelOpacity: isVisible ? 1 : Math.min(0.06, backgroundOpacity),
                    iconOpacity: isVisible ? 1 : Math.min(0.16, backgroundOpacity * 2),
                },
            };
        }));
    }

    async function highlightNeighbors(nodeId, isSelection) {
        if (!graph) return;
        const edgesData = graph.getEdgeData();
        const states = {};
        states[nodeId] = isSelection ? ["selected"] : ["active"];

        // Use the actually rendered relationship layer as the focus scope.
        // Every direct neighbor is retained; only parallel relationships to
        // the same neighbor are collapsed into one representative edge.
        const visibleNeighborIds = new Set();
        for (let i = 0, len = edgesData.length; i < len; i++) {
            const edge = edgesData[i];
            if (edge.source === nodeId) {
                visibleNeighborIds.add(edge.target);
                states[edge.id] = ["activeOut"];
            } else if (edge.target === nodeId) {
                visibleNeighborIds.add(edge.source);
                states[edge.id] = ["activeIn"];
            }
        }
        for (const neighborId of visibleNeighborIds) {
            states[neighborId] = ["active"];
        }

        if (isSelection) {
            // Apply the shadow as base opacity rather than a persistent G6
            // state, so it can be restored deterministically on canvas clear.
            setFocusBackdrop(nodeId, visibleNeighborIds);
        }

        await _applyStates(states);
    }

    function clearHighlight() {
        if (!graph) return Promise.resolve();
        return _applyStates({});
    }

    // ══════════════════════════════════════════════════════
    //  GraphRAG Highlighting Logic
    // ══════════════════════════════════════════════════════
    function highlightGraph(highlightData) {
        if (!graph || !highlightData) return;

        const hlNodes = highlightData.nodes || [];
        const hlEdges = highlightData.edges || [];

        if (hlNodes.length === 0 && hlEdges.length === 0) {
            clearHighlight();
            return;
        }

        // Apply environment safety limit
        if (hlNodes.length > 50) {
            console.warn(`Highlight aborted: too many nodes (${hlNodes.length})`);
            return;
        }

        const states = {};
        let firstNodeId = null;

        graph.getNodeData().forEach((node) => {
            if (hlNodes.includes(node.id)) {
                states[node.id] = ["selected"];
                if (!firstNodeId) firstNodeId = node.id;
            } else {
                states[node.id] = ["inactive"];
            }
        });

        graph.getEdgeData().forEach((edge) => {
            const relName = edge.data?.label || edge.id;
            if (hlEdges.includes(relName) && hlNodes.includes(edge.source) && hlNodes.includes(edge.target)) {
                states[edge.id] = ["active"];
            } else {
                states[edge.id] = ["inactive"];
            }
        });

        // Apply graph-rag states (use differential update)
        _applyStates(states);

        // Focus camera on the subgraph
        if (firstNodeId) {
            selectedNodeId = firstNodeId; // Lock selection to prevent mouse hover from clearing highlight
            graph.focusElement(firstNodeId, true);
        }
    }

    window._highlightGraph = highlightGraph;

    // ══════════════════════════════════════════════════════
    //  Product Line State
    // ══════════════════════════════════════════════════════
    let currentProductLine = "general";
    let productLineList = [];

    function updateHeaderLinks() {
        const industryBtn = document.querySelector('a[href*="industry.html"]');
        if (industryBtn) {
            industryBtn.href = `/static/industry.html?product_line=${currentProductLine}`;
        }
    }

    // ══════════════════════════════════════════════════════
    //  Per-node priority switch
    // ══════════════════════════════════════════════════════
    function syncNodePrioritySwitch(nodeId) {
        const button = document.getElementById("btnNodePriority");
        const enabled = priorityNodes.has(nodeId);
        button.classList.toggle("active", enabled);
        button.setAttribute("aria-pressed", String(enabled));
        button.querySelector(".compact-switch-label").textContent = enabled ? "关注" : "关闭";
        button.title = enabled
            ? "取消关注，移出中央区域并恢复正常大小"
            : "关注并移到中央区域";
    }

    async function setSelectedNodePriority(enabled) {
        if (!selectedNodeId || !graph) return;
        const nodeId = selectedNodeId;
        graphMutationBusy = true;
        try {
            if (edgeRenderWorker) {
                try { await edgeRenderWorker; } catch (_) {}
            }
            if (selectedNodeId !== nodeId) return;

            if (enabled) priorityNodes.add(nodeId);
            else priorityNodes.delete(nodeId);
            persistPriorityNodes();

            // Rebuild deterministic positions, then update every node in one
            // draw. The followed node moves into/out of the focus area while
            // all other nodes close the gap and retain stable ordering.
            indexOverviewData(rawData);
            const updates = graph.getNodeData().map((node) => {
                const position = presetPositions.get(node.id);
                const sourceNode = nodeInfoCache.get(node.id) || node;
                return {
                    id: node.id,
                    style: {
                        ...(node.style || {}),
                        size: getNodeSize(node.id, sourceNode),
                        x: position?.x,
                        y: position?.y,
                    },
                };
            });
            graph.updateNodeData(updates);
            await graph.draw();

            if (selectedNodeId === nodeId) {
                await highlightNeighbors(nodeId, true);
            }
            syncNodePrioritySwitch(nodeId);
        } finally {
            graphMutationBusy = false;
        }
    }

    function setupNodePriorityControl() {
        const button = document.getElementById("btnNodePriority");
        button.addEventListener("click", () => {
            if (!selectedNodeId) return;
            setSelectedNodePriority(!priorityNodes.has(selectedNodeId));
        });
    }

    function syncChatContextButton(className) {
        const button = document.getElementById("btnAddChatContext");
        const isClass = Boolean(className && nodeInfoCache.has(className));
        button.hidden = !isClass;
        button.dataset.className = isClass ? className : "";
        if (!isClass) return;

        const added = typeof window._hasChatContextClass === "function"
            && window._hasChatContextClass(className);
        button.classList.toggle("active", added);
        button.disabled = added;
        button.querySelector("span").textContent = added ? "已加入" : "加入上下文";
        button.title = added
            ? "该对象已在当前 SQL 会话的上下文中"
            : "将当前对象加入 SQL 助手的已知对象";
    }

    function setupChatContextControl() {
        const button = document.getElementById("btnAddChatContext");
        button.addEventListener("click", async () => {
            const className = button.dataset.className;
            if (!className || button.disabled) return;
            button.disabled = true;
            try {
                if (typeof window._addChatContextClass !== "function") {
                    throw new Error("SQL 助手尚未加载完成");
                }
                await window._addChatContextClass(className);
                syncChatContextButton(className);
            } catch (error) {
                button.disabled = false;
                button.title = error.message || "加入上下文失败";
                console.error("Add SQL context failed:", error);
            }
        });
        window.addEventListener("chat-context-change", () => {
            syncChatContextButton(selectedNodeId);
        });
    }

    async function loadProductLines() {
        try {
            const data = await fetchJSON("/api/product-lines");
            productLineList = data.product_lines || [];
            const select = document.getElementById("productLineSelect");
            select.innerHTML = "";
            for (const pl of productLineList) {
                const opt = document.createElement("option");
                opt.value = pl.id;
                opt.textContent = pl.name;
                select.appendChild(opt);
            }
            // Read from URL params or fallback to localStorage
            const urlParams = new URLSearchParams(window.location.search);
            let plParam = urlParams.get("product_line") || localStorage.getItem("selected_product_line") || "general";
            if (plParam && productLineList.some(p => p.id === plParam)) {
                currentProductLine = plParam;
                select.value = plParam;
                localStorage.setItem("selected_product_line", currentProductLine);
            } else {
                currentProductLine = "general";
                if (select) select.value = "general";
                localStorage.setItem("selected_product_line", "general");
            }
            
            // Update links initially
            updateHeaderLinks();

            // On change
            select.addEventListener("change", (e) => {
                currentProductLine = e.target.value;
                const url = new URL(window.location);
                if (currentProductLine === "general") {
                    url.searchParams.delete("product_line");
                    localStorage.setItem("selected_product_line", "general");
                } else {
                    url.searchParams.set("product_line", currentProductLine);
                    localStorage.setItem("selected_product_line", currentProductLine);
                }
                window.history.replaceState({}, "", url);
                
                // Update links on change
                updateHeaderLinks();

                hideEdgePopup();
            });
        } catch (e) {
            console.warn("Failed to load product lines:", e);
        }
    }

    function getProductLineInfo(plId) {
        return productLineList.find(p => p.id === plId) || { id: plId, name: plId, icon: "package", color: "#999" };
    }

    // Expose for chat.js
    window._getCurrentProductLine = () => currentProductLine;

    // ══════════════════════════════════════════════════════
    //  Edge Action Popup (Wiki-First)
    // ══════════════════════════════════════════════════════
    let currentEdgeInfo = null;
    let currentWikiContent = null;  // raw markdown content for editing
    let currentRelationshipWikiResults = null;
    let edgeWikiLoadToken = 0;
    let edgeSqlLoadToken = 0;
    let edgeSqlCopyFeedbackTimer = null;
    let edgePopupWidth = 585;

    function renderRelationshipWiki(container, markdown) {
        container.style.whiteSpace = "";
        try {
            if (typeof marked === "undefined" || typeof marked.parse !== "function") {
                throw new Error("Markdown renderer unavailable");
            }
            container.innerHTML = marked.parse(markdown);
        } catch (error) {
            console.warn("Markdown render error, showing plain text:", error);
            container.textContent = markdown;
            container.style.whiteSpace = "pre-wrap";
        }
    }

    function relationshipWikiUrl({ source, relName, target }, productLine, sqlDialect = currentSqlDialect) {
        return `/api/wiki/relationship?source=${encodeURIComponent(source)}&rel=${encodeURIComponent(relName)}&target=${encodeURIComponent(target)}&product_line=${encodeURIComponent(productLine)}&sql_dialect=${encodeURIComponent(sqlDialect)}`;
    }

    function relationshipEntries(edgeInfo) {
        if (Array.isArray(edgeInfo?.relationships) && edgeInfo.relationships.length) {
            return edgeInfo.relationships;
        }
        return edgeInfo ? [edgeInfo] : [];
    }

    async function fetchRelationshipEntries(edgeInfo, productLine, sqlDialect) {
        const entries = relationshipEntries(edgeInfo);
        return Promise.all(entries.map(async (entry) => ({
            entry,
            wikiData: await fetchJSON(
                relationshipWikiUrl(entry, productLine, sqlDialect),
            ),
        })));
    }

    function relationshipSqlMarkdown(results, sqlDialect) {
        const dialectLabel = SQL_DIALECTS[sqlDialect].label;
        if (results.length === 1) {
            return results[0].wikiData.sql_content
                || `当前物理 Schema 无法生成 ${dialectLabel} SQL 关联示例。`;
        }
        return results.map(({ entry, wikiData }, index) => {
            const heading = (
                `#### 关系 ${index + 1}：${entry.relName}\n\n`
                + `\`${entry.source} → ${entry.target}\``
            );
            const sql = wikiData.sql_content
                || `> 当前物理 Schema 无法生成 ${dialectLabel} SQL 关联示例。`;
            return `${heading}\n\n${sql}`;
        }).join("\n\n---\n\n");
    }

    function hasRelationshipUsageWiki(wikiData) {
        return Boolean(wikiData?.found && wikiData.content);
    }

    function relationshipUsageMarkdown(results) {
        return results.map(({ entry, wikiData, generationStatus, generationError }, index) => {
            const heading = (
                `## 关系 ${index + 1}：${entry.relName}\n\n`
                + `\`${entry.source} → ${entry.target}\``
            );
            let usage = wikiData?.content || "";
            if (generationStatus === "generating" && !usage) {
                usage = "> AI 正在生成这条 Relationship 的用法 Wiki…";
            } else if (generationStatus === "error") {
                usage = `> 生成失败：${generationError || "未知错误"}`;
            } else if (!usage) {
                usage = "> 暂无用法 Wiki，点击下方按钮为这条 Relationship 生成。";
            }
            return `${heading}\n\n${usage}`;
        }).join("\n\n---\n\n");
    }

    function renderMultiRelationshipUsage(results, wikiContent, wikiEmpty) {
        currentRelationshipWikiResults = results;
        currentWikiContent = null;
        wikiEmpty.style.display = "none";
        renderRelationshipWiki(wikiContent, relationshipUsageMarkdown(results));
        wikiContent.style.display = "block";
    }

    function setMultiRelationshipGenerateButton(results, generateBtn) {
        const missing = results.filter(({ wikiData }) => !hasRelationshipUsageWiki(wikiData));
        if (!missing.length) {
            generateBtn.style.display = "none";
            generateBtn.disabled = false;
            return;
        }
        const failed = missing.filter(({ generationStatus }) => generationStatus === "error").length;
        const existing = results.length - missing.length;
        const action = failed ? "重试" : existing ? "补全" : "生成";
        generateBtn.style.display = "inline-flex";
        generateBtn.disabled = false;
        setIconContent(generateBtn, "bot", `${action} ${missing.length} 份 Wiki`, { size: 14 });
    }

    async function streamRelationshipUsageWiki(entry, productLine, onChunk) {
        const res = await fetch("/api/wiki/generate-one", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                source: entry.source,
                rel: entry.relName,
                target: entry.target,
                product_line: productLine,
                cardinality: entry.cardinality || "",
                description: entry.desc || "",
                overwrite: false,
            }),
        });
        if (!res.ok || !res.body) {
            throw new Error(`生成请求失败（HTTP ${res.status}）`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let fullText = "";
        let finalContent = "";
        let buffer = "";
        let streamError = "";

        const consumeLine = (line) => {
            if (!line.startsWith("data: ")) return;
            try {
                const payload = JSON.parse(line.slice(6));
                if (payload.type === "chunk") {
                    fullText += payload.content || "";
                    onChunk(fullText);
                } else if (payload.type === "done") {
                    finalContent = payload.content || fullText;
                } else if (payload.type === "error") {
                    streamError = payload.content || "生成失败";
                }
            } catch (_) {}
        };

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";
            lines.forEach(consumeLine);
        }
        buffer += decoder.decode();
        if (buffer.trim()) consumeLine(buffer.trim());
        if (streamError) throw new Error(streamError);
        const content = finalContent || fullText;
        if (!content) throw new Error("生成服务未返回 Wiki 内容");
        return content;
    }

    async function generateMissingRelationshipUsageWikis() {
        if (!currentEdgeInfo) return;
        const edgeInfoAtStart = currentEdgeInfo;
        const loadToken = edgeWikiLoadToken;
        const productLineAtStart = currentProductLine;
        const generateBtn = document.getElementById("edgePopupGenerate");
        const wikiContent = document.getElementById("edgeWikiContent");
        const wikiEmpty = document.getElementById("edgeWikiEmpty");
        const editBtn = document.getElementById("edgePopupEdit");

        generateBtn.disabled = true;
        editBtn.style.display = "none";
        let results = currentRelationshipWikiResults;
        if (!Array.isArray(results) || results.length !== relationshipEntries(edgeInfoAtStart).length) {
            results = await fetchRelationshipEntries(
                edgeInfoAtStart,
                productLineAtStart,
                currentSqlDialect,
            );
        }
        const missingResults = results.filter(({ wikiData }) => !hasRelationshipUsageWiki(wikiData));
        if (!missingResults.length) {
            renderMultiRelationshipUsage(results, wikiContent, wikiEmpty);
            setMultiRelationshipGenerateButton(results, generateBtn);
            return;
        }

        for (let index = 0; index < missingResults.length; index += 1) {
            const result = missingResults[index];
            result.generationStatus = "generating";
            result.generationError = "";
            result.wikiData = { ...result.wikiData, found: false, content: "" };
            renderMultiRelationshipUsage(results, wikiContent, wikiEmpty);
            setIconContent(
                generateBtn,
                "loader",
                `正在生成 ${index + 1}/${missingResults.length}：${result.entry.relName}`,
                { size: 14, spin: true },
            );

            let lastRenderTime = 0;
            try {
                const content = await streamRelationshipUsageWiki(
                    result.entry,
                    productLineAtStart,
                    (partialContent) => {
                        if (
                            loadToken !== edgeWikiLoadToken
                            || currentEdgeInfo !== edgeInfoAtStart
                        ) return;
                        result.wikiData = {
                            ...result.wikiData,
                            found: true,
                            content: partialContent,
                        };
                        const now = Date.now();
                        if (now - lastRenderTime >= 150) {
                            renderMultiRelationshipUsage(results, wikiContent, wikiEmpty);
                            lastRenderTime = now;
                        }
                    },
                );
                result.wikiData = { ...result.wikiData, found: true, content };
                result.generationStatus = "done";
            } catch (error) {
                result.wikiData = { ...result.wikiData, found: false, content: "" };
                result.generationStatus = "error";
                result.generationError = String(error.message || error);
            }

            if (
                loadToken !== edgeWikiLoadToken
                || currentEdgeInfo !== edgeInfoAtStart
                || currentProductLine !== productLineAtStart
            ) return;
            renderMultiRelationshipUsage(results, wikiContent, wikiEmpty);
        }

        setMultiRelationshipGenerateButton(results, generateBtn);
    }

    function setEdgeSqlDialectBadge(dialect = currentSqlDialect) {
        const badge = document.getElementById("edgeSqlDialectBadge");
        if (badge) badge.textContent = SQL_DIALECTS[normalizeSqlDialect(dialect)].label;
    }

    function setEdgeSqlExpanded(expanded) {
        const toggle = document.getElementById("edgeSqlToggle");
        const sqlArea = document.getElementById("edgeSqlArea");
        if (!toggle || !sqlArea) return;
        toggle.setAttribute("aria-expanded", String(expanded));
        toggle.title = expanded ? "折叠 SQL 关联示例" : "展开 SQL 关联示例";
        sqlArea.classList.toggle("edge-sql-collapsed", !expanded);
    }

    function setEdgeSqlCopyReady(ready) {
        const copyButton = document.getElementById("edgeSqlCopy");
        if (!copyButton) return;
        copyButton.disabled = !ready;
        if (!copyButton.classList.contains("success")) {
            setIconContent(copyButton, "copy", "复制", { size: 12 });
        }
    }

    async function copyRelationshipSql() {
        const sqlContent = document.getElementById("edgeSqlContent");
        const code = [...sqlContent.querySelectorAll("pre code")]
            .map((node) => node.textContent?.trim())
            .filter(Boolean)
            .join("\n\n");
        if (!code) return;
        try {
            await navigator.clipboard.writeText(code);
        } catch (_) {
            const textarea = document.createElement("textarea");
            textarea.value = code;
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand("copy");
            textarea.remove();
        }
        const copyButton = document.getElementById("edgeSqlCopy");
        clearTimeout(edgeSqlCopyFeedbackTimer);
        setIconContent(copyButton, "check", "已复制", { size: 12 });
        copyButton.classList.add("success");
        edgeSqlCopyFeedbackTimer = setTimeout(() => {
            setIconContent(copyButton, "copy", "复制", { size: 12 });
            copyButton.classList.remove("success");
        }, 1600);
    }

    async function refreshCurrentEdgeSql() {
        if (!currentEdgeInfo) return;
        const sqlToken = ++edgeSqlLoadToken;
        const edgeInfoAtRequest = currentEdgeInfo;
        const dialectAtRequest = currentSqlDialect;
        const sqlContent = document.getElementById("edgeSqlContent");
        setEdgeSqlCopyReady(false);
        setEdgeSqlDialectBadge(dialectAtRequest);
        sqlContent.textContent = `正在读取 ${SQL_DIALECTS[dialectAtRequest].label} 物理关联…`;
        sqlContent.style.whiteSpace = "";
        try {
            const results = await fetchRelationshipEntries(
                edgeInfoAtRequest,
                currentProductLine,
                dialectAtRequest,
            );
            if (
                sqlToken !== edgeSqlLoadToken
                || currentEdgeInfo !== edgeInfoAtRequest
                || currentSqlDialect !== dialectAtRequest
            ) return;
            renderRelationshipWiki(
                sqlContent,
                relationshipSqlMarkdown(results, dialectAtRequest),
            );
            setEdgeSqlCopyReady(Boolean(sqlContent.querySelector("code")));
        } catch (error) {
            if (sqlToken !== edgeSqlLoadToken || currentEdgeInfo !== edgeInfoAtRequest) return;
            sqlContent.textContent = `SQL 读取失败：${String(error.message || error)}`;
            setEdgeSqlCopyReady(false);
        }
    }

    window.addEventListener("camstar:sql-dialect-change", () => {
        if (currentEdgeInfo) refreshCurrentEdgeSql();
    });

    async function showEdgePopup(
        relName,
        source,
        target,
        desc,
        cardinality,
        x,
        y,
        relationships = null,
    ) {
        const loadToken = ++edgeWikiLoadToken;
        const sqlToken = ++edgeSqlLoadToken;
        const popup = document.getElementById("edgePopup");
        const titleEl = document.getElementById("edgePopupTitle");
        const metaEl = document.getElementById("edgePopupMeta");
        const plEl = document.getElementById("edgePopupPL");
        const sqlContent = document.getElementById("edgeSqlContent");
        const sqlCopyButton = document.getElementById("edgeSqlCopy");
        const wikiArea = document.getElementById("edgeWikiArea");
        const wikiLoading = document.getElementById("edgeWikiLoading");
        const wikiContent = document.getElementById("edgeWikiContent");
        const wikiEmpty = document.getElementById("edgeWikiEmpty");
        const generateBtn = document.getElementById("edgePopupGenerate");
        const editBtn = document.getElementById("edgePopupEdit");

        titleEl.textContent = ontologyLabel("relationship", relName, relName);
        const sourceNode = graph.getNodeData(source);
        const targetNode = graph.getNodeData(target);
        const sourceChinese = sourceNode?.data?.chineseName || "";
        const targetChinese = targetNode?.data?.chineseName || "";
        const sourceDisplay = ontologyLabel("node", source, source, sourceChinese);
        const targetDisplay = ontologyLabel("node", target, target, targetChinese);

        let metaText = `${sourceDisplay}  →  ${targetDisplay}`;
        if (cardinality) metaText += `  ·  ${cardinality}`;
        if (desc) metaText += `\n${desc}`;
        metaEl.textContent = metaText;

        // Show product line badge
        const plInfo = getProductLineInfo(currentProductLine);
        setIconContent(plEl, plInfo.icon || "package", plInfo.name, { size: 13 });

        // Store for buttons
        currentEdgeInfo = {
            relName,
            source,
            target,
            desc,
            cardinality,
            relationships,
        };
        currentWikiContent = null;
        currentRelationshipWikiResults = null;

        // SQL and relationship usage are two independent fields.
        const dialectAtOpen = currentSqlDialect;
        setEdgeSqlExpanded(true);
        clearTimeout(edgeSqlCopyFeedbackTimer);
        sqlCopyButton.classList.remove("success");
        setEdgeSqlCopyReady(false);
        setEdgeSqlDialectBadge(dialectAtOpen);
        sqlContent.textContent = `正在读取 ${SQL_DIALECTS[dialectAtOpen].label} 物理关联…`;
        sqlContent.style.whiteSpace = "";
        wikiLoading.style.display = "flex";
        wikiContent.style.display = "none";
        wikiContent.innerHTML = "";
        wikiContent.style.whiteSpace = "";
        wikiEmpty.style.display = "none";
        wikiEmpty.innerHTML = `
            <span class="wiki-empty-icon">${AppIcons.svg("inbox", { size: 26 })}</span>
            <span>暂无 Relationship 用法 Wiki</span>
            <span style="font-size:10px;color:var(--text-muted);margin-top:4px">点击下方「生成 Wiki」按钮，AI 将自动生成</span>
        `;
        generateBtn.style.display = "none";
        generateBtn.disabled = false;
        generateBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg> 生成 Wiki`;
        editBtn.style.display = "none";

        // Position popup near click, but keep within viewport
        const popupW = Math.min(edgePopupWidth, window.innerWidth - 32);
        const popupH = Math.min(900, window.innerHeight - 32);
        let left = Math.max(16, Math.min(x - popupW * 0.65, window.innerWidth - popupW - 16));
        let top = Math.max(16, Math.min(y - 60, window.innerHeight - popupH - 16));

        popup.style.width = popupW + "px";
        popup.style.left = left + "px";
        popup.style.top = top + "px";
        popup.classList.remove("edge-popup-hidden");

        // ── Auto-load wiki if exists (fast filesystem read, matches product line) ──
        try {
            const productLineAtOpen = currentProductLine;
            const relationshipResults = await fetchRelationshipEntries(
                currentEdgeInfo,
                productLineAtOpen,
                dialectAtOpen,
            );

            if (loadToken !== edgeWikiLoadToken) return;
            if (sqlToken === edgeSqlLoadToken && dialectAtOpen === currentSqlDialect) {
                renderRelationshipWiki(
                    sqlContent,
                    relationshipSqlMarkdown(relationshipResults, dialectAtOpen),
                );
                setEdgeSqlCopyReady(Boolean(sqlContent.querySelector("code")));
            }
            wikiLoading.style.display = "none";
            if (relationshipResults.length > 1) {
                renderMultiRelationshipUsage(relationshipResults, wikiContent, wikiEmpty);
                setMultiRelationshipGenerateButton(relationshipResults, generateBtn);
                editBtn.style.display = "none";
            } else if (
                relationshipResults[0].wikiData.found
                && relationshipResults[0].wikiData.content
            ) {
                const wikiData = relationshipResults[0].wikiData;
                currentWikiContent = wikiData.content;
                wikiEmpty.style.display = "none";
                renderRelationshipWiki(wikiContent, wikiData.content);
                wikiContent.style.display = "block";
                generateBtn.style.display = "none";
                editBtn.style.display = "inline-flex";
            } else {
                wikiEmpty.style.display = "flex";
                generateBtn.style.display = "inline-flex";
            }
        } catch (e) {
            if (loadToken !== edgeWikiLoadToken) return;
            sqlContent.textContent = `SQL 读取失败：${String(e.message || e)}`;
            setEdgeSqlCopyReady(false);
            wikiLoading.style.display = "none";
            wikiEmpty.innerHTML = `
                <span class="wiki-empty-icon">${AppIcons.svg("alert", { size: 26 })}</span>
                <span>Wiki 读取失败</span>
                <span style="font-size:10px;color:var(--text-muted);margin-top:4px">${String(e.message || e)}</span>
            `;
            wikiEmpty.style.display = "flex";
            generateBtn.style.display = "inline-flex";
            console.warn("Wiki read error:", e);
        }
    }

    function hideEdgePopup() {
        edgeWikiLoadToken += 1;
        edgeSqlLoadToken += 1;
        document.getElementById("edgePopup").classList.add("edge-popup-hidden");
        currentEdgeInfo = null;
        currentWikiContent = null;
        currentRelationshipWikiResults = null;
    }

    // Wire the "Generate Wiki" button — first try read, then generate
    document.getElementById("edgePopupGenerate").addEventListener("click", async () => {
        if (!currentEdgeInfo) return;
        if (relationshipEntries(currentEdgeInfo).length > 1) {
            try {
                await generateMissingRelationshipUsageWikis();
            } catch (error) {
                const generateBtn = document.getElementById("edgePopupGenerate");
                generateBtn.disabled = false;
                setIconContent(generateBtn, "alert", "生成失败，请重试", { size: 14 });
                console.error("Multi-relationship Wiki generation error:", error);
            }
            return;
        }
        const { relName, source, target, desc, cardinality } = currentEdgeInfo;
        const generateBtn = document.getElementById("edgePopupGenerate");
        const wikiLoading = document.getElementById("edgeWikiLoading");
        const wikiContent = document.getElementById("edgeWikiContent");
        const wikiEmpty = document.getElementById("edgeWikiEmpty");
        const editBtn = document.getElementById("edgePopupEdit");

        generateBtn.disabled = true;
        setIconContent(generateBtn, "loader", "加载中...", { spin: true });
        wikiEmpty.style.display = "none";
        wikiLoading.style.display = "flex";

        try {
            // Step 1: Try reading existing wiki first
            const wikiUrl = relationshipWikiUrl(currentEdgeInfo, currentProductLine);
            const wikiData = await fetchJSON(wikiUrl);

            if (wikiData.found && wikiData.content) {
                // Wiki exists — display it
                currentWikiContent = wikiData.content;
                wikiLoading.style.display = "none";
                renderRelationshipWiki(wikiContent, wikiData.content);
                wikiContent.style.display = "block";
                generateBtn.style.display = "none";
                editBtn.style.display = "inline-flex";
                return;
            }

            // Step 2: Wiki doesn't exist, generate via LLM
            setIconContent(generateBtn, "bot", "AI 生成中...");
            const res = await fetch("/api/wiki/generate-one", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    source, rel: relName, target,
                    product_line: currentProductLine,
                    cardinality: cardinality || "",
                    description: desc || "",
                    overwrite: false,
                }),
            });

            wikiLoading.style.display = "none";
            wikiContent.style.display = "block";
            wikiContent.innerHTML = `<div style="color:var(--si-green);display:flex;align-items:center;gap:8px;"><div class="wiki-spinner"></div>${AppIcons.svg("bot", { size: 15 })}<span>AI 正在规划撰写知识库...</span></div>`;

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let fullText = "";
            let buffer = "";
            let lastRenderTime = 0;
            const RENDER_THROTTLE_MS = 150; // Render at most once every 150ms to prevent browser thread freeze

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    try {
                        const payload = JSON.parse(line.slice(6));
                        if (payload.type === "chunk") {
                            fullText += payload.content;
                            const now = Date.now();
                            if (now - lastRenderTime > RENDER_THROTTLE_MS) {
                                renderRelationshipWiki(wikiContent, fullText);
                                lastRenderTime = now;
                            }
                        } else if (payload.type === "done") {
                            currentWikiContent = payload.content;
                        } else if (payload.type === "error") {
                            wikiContent.style.color = "#FF6666";
                            setIconContent(wikiContent, "xCircle", `生成失败: ${payload.content}`, { size: 15 });
                        }
                    } catch (_) {}
                }
            }

            if (fullText) {
                renderRelationshipWiki(wikiContent, currentWikiContent || fullText);
                generateBtn.style.display = "none";
                editBtn.style.display = "inline-flex";
            } else {
                wikiContent.style.display = "none";
                wikiEmpty.style.display = "flex";
                generateBtn.disabled = false;
                generateBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg> 重试`;
            }
        } catch (e) {
            wikiLoading.style.display = "none";
            wikiEmpty.style.display = "flex";
            generateBtn.disabled = false;
            generateBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg> 重试`;
            console.error("Wiki load error:", e);
        }
    });

    // Wire the "Edit Wiki" button
    document.getElementById("edgePopupEdit").addEventListener("click", () => {
        if (!currentEdgeInfo) return;
        openWikiEditor();
    });

    // Wire the close button
    document.getElementById("edgePopupClose").addEventListener("click", () => {
        hideEdgePopup();
    });

    document.getElementById("edgeSqlToggle").addEventListener("click", () => {
        const toggle = document.getElementById("edgeSqlToggle");
        setEdgeSqlExpanded(toggle.getAttribute("aria-expanded") !== "true");
    });

    document.getElementById("edgeSqlCopy").addEventListener("click", copyRelationshipSql);

    // Resize only the popup width from its right edge; height stays fixed.
    (function setupPopupWidthResize() {
        const popup = document.getElementById("edgePopup");
        const handle = document.getElementById("edgePopupResizeHandle");
        let resizing = false;
        let startX = 0;
        let startWidth = 0;
        let popupLeft = 0;

        function onStart(e) {
            resizing = true;
            const point = e.touches ? e.touches[0] : e;
            const rect = popup.getBoundingClientRect();
            startX = point.clientX;
            startWidth = rect.width;
            popupLeft = rect.left;
            popup.classList.add("resizing");
            e.stopPropagation();
            e.preventDefault();
        }

        function onMove(e) {
            if (!resizing) return;
            const point = e.touches ? e.touches[0] : e;
            const viewportLimit = Math.max(0, window.innerWidth - 32);
            const minWidth = Math.min(440, viewportLimit);
            const maxWidth = Math.max(minWidth, window.innerWidth - popupLeft - 16);
            const nextWidth = Math.min(maxWidth, Math.max(minWidth, startWidth + point.clientX - startX));
            edgePopupWidth = nextWidth;
            popup.style.width = nextWidth + "px";
            e.preventDefault();
        }

        function onEnd() {
            if (!resizing) return;
            resizing = false;
            popup.classList.remove("resizing");
        }

        handle.addEventListener("mousedown", onStart);
        handle.addEventListener("touchstart", onStart, { passive: false });
        document.addEventListener("mousemove", onMove);
        document.addEventListener("touchmove", onMove, { passive: false });
        document.addEventListener("mouseup", onEnd);
        document.addEventListener("touchend", onEnd);
    })();

    // ── Make the popup draggable (Edge compat + user repositioning) ──
    (function setupPopupDrag() {
        const popup = document.getElementById("edgePopup");
        let dragging = false;
        let startX, startY, startLeft, startTop;

        function onStart(e) {
            // Only start drag from title/meta area, not from buttons or wiki area
            const target = e.target;
            if (target.closest("button") || target.closest("textarea") || target.closest(".edge-popup-resize-handle") || target.closest(".edge-popup-actions") || target.closest(".edge-wiki-area") || target.closest(".edge-sql-area")) return;

            dragging = true;
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            startX = clientX;
            startY = clientY;
            startLeft = parseFloat(popup.style.left) || popup.getBoundingClientRect().left;
            startTop = parseFloat(popup.style.top) || popup.getBoundingClientRect().top;
            popup.style.transition = "none";
            popup.style.cursor = "grabbing";
            e.stopPropagation();
            e.preventDefault();
        }

        function onMove(e) {
            if (!dragging) return;
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            const dx = clientX - startX;
            const dy = clientY - startY;
            popup.style.left = (startLeft + dx) + "px";
            popup.style.top = (startTop + dy) + "px";
        }

        function onEnd() {
            if (!dragging) return;
            dragging = false;
            popup.style.transition = "";
            popup.style.cursor = "";
        }

        popup.addEventListener("mousedown", onStart);
        popup.addEventListener("touchstart", onStart, { passive: false });
        document.addEventListener("mousemove", onMove);
        document.addEventListener("touchmove", onMove, { passive: false });
        document.addEventListener("mouseup", onEnd);
        document.addEventListener("touchend", onEnd);
    })();

    // ══════════════════════════════════════════════════════
    //  Wiki Editor Modal
    // ══════════════════════════════════════════════════════
    function openWikiEditor() {
        const modal = document.getElementById("wikiEditorModal");
        const titleEl = document.getElementById("wikiEditorTitle");
        const textarea = document.getElementById("wikiEditorTextarea");

        if (!currentEdgeInfo) return;
        const { relName, source, target } = currentEdgeInfo;
        const plInfo = getProductLineInfo(currentProductLine);

        titleEl.textContent = `编辑 Wiki: ${source} → ${relName} → ${target}  (${plInfo.name})`;
        textarea.value = currentWikiContent || "";
        modal.classList.remove("wiki-editor-hidden");
        textarea.focus();
    }

    function closeWikiEditor() {
        document.getElementById("wikiEditorModal").classList.add("wiki-editor-hidden");
    }

    document.getElementById("wikiEditorClose").addEventListener("click", closeWikiEditor);
    document.getElementById("wikiEditorCancel").addEventListener("click", closeWikiEditor);

    document.getElementById("wikiEditorSave").addEventListener("click", async () => {
        if (!currentEdgeInfo) return;
        const { relName, source, target } = currentEdgeInfo;
        const textarea = document.getElementById("wikiEditorTextarea");
        const content = textarea.value.trim();
        const saveBtn = document.getElementById("wikiEditorSave");

        if (!content) return;

        saveBtn.disabled = true;
        setIconContent(saveBtn, "loader", "保存中...", { spin: true });

        try {
            const res = await fetch("/api/wiki/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    source, rel: relName, target,
                    product_line: currentProductLine,
                    content,
                    editor: "user",
                }),
            });
            const data = await res.json();

            if (data.saved) {
                // Update the popup content
                currentWikiContent = content;
                const wikiContentEl = document.getElementById("edgeWikiContent");
                renderRelationshipWiki(wikiContentEl, content);
                wikiContentEl.style.display = "block";
                document.getElementById("edgeWikiEmpty").style.display = "none";
                document.getElementById("edgePopupGenerate").style.display = "none";
                document.getElementById("edgePopupEdit").style.display = "inline-flex";

                closeWikiEditor();
            } else {
                alert("保存失败: " + JSON.stringify(data));
            }
        } catch (e) {
            console.error("Wiki save error:", e);
            alert("保存失败: " + e.message);
        } finally {
            saveBtn.disabled = false;
            setIconContent(saveBtn, "save", "保存");
        }
    });

    // ══════════════════════════════════════════════════════
    //  Detail Panel (Layered Loading – Level 1)
    // ══════════════════════════════════════════════════════
    async function showClassDetail(className) {
        const renderToken = ++detailRenderToken;
        if (nodeInfoCache.has(className) && selectedNodeId !== className) {
            selectNode(className);
        }
        // Expose for chat.js
        window._showClassDetail = showClassDetail;
        const panel = document.getElementById("detailPanel");
        const panelTitle = document.getElementById("panelTitle");
        const sectionMeta = document.getElementById("sectionMeta");
        const propTable = document.getElementById("propTable");
        const relList = document.getElementById("relList");
        const sectionProperties = document.getElementById("sectionProperties");

        const classNode = nodeInfoCache.get(className);
        panelTitle.textContent = ontologyLabel(
            "node", className, className, classNode?.data?.chineseName || "",
        );
        syncNodePrioritySwitch(className);
        syncChatContextButton(className);

        let detail;
        if (classDetailCache.has(className)) {
            detail = classDetailCache.get(className);
            sectionProperties.style.display = "";
            panel.classList.remove("panel-hidden");
        } else {
            // Show loading state for network fetch
            sectionMeta.innerHTML = `<div class="meta-row"><span class="meta-value" style="color:var(--text-muted)">加载中...</span></div>`;
            propTable.innerHTML = "";
            relList.innerHTML = "";
            sectionProperties.style.display = "";
            panel.classList.remove("panel-hidden");

            try {
                detail = await fetchJSON(`/api/graph/class/${encodeURIComponent(className)}`);
                classDetailCache.set(className, detail);
            } catch (err) {
                if (renderToken !== detailRenderToken) return;
                sectionMeta.innerHTML = `<div class="meta-row"><span class="meta-value" style="color:#FF6666">加载失败: ${err.message}</span></div>`;
                return;
            }
        }

        if (renderToken !== detailRenderToken) return;
        try {

            // ── Meta ──
            // find node in rawData for extra info
            const nodeInfo = nodeInfoCache.get(className);
            const module = nodeInfo?.data?.module || "other";
            const desc = ontologyDescription(className, nodeInfo?.data?.description || "");

            sectionMeta.innerHTML = `
                <div class="meta-row"><span class="meta-label">模块</span><span class="meta-value" style="color:${(COLORS[module] || COLORS.other).fill}">${module.toUpperCase()}</span></div>
                <div class="meta-row"><span class="meta-label">描述</span><span class="meta-value">${htmlEscape(desc || "—")}</span></div>
                <div class="meta-row"><span class="meta-label">图上邻居</span><span class="meta-value">${adjacencyIndex?.get(className)?.neighbors?.size || 0}（全部显示）</span></div>
                <div class="meta-row"><span class="meta-label">完整关系</span><span class="meta-value">${(detail.outgoing || []).length + (detail.incoming || []).length}（见下方清单）</span></div>
            `;

            // ── Properties ──
            if (detail.properties && detail.properties.length > 0) {
                const renderProperties = (showAll = false) => {
                    const visibleProperties = showAll
                        ? detail.properties
                        : detail.properties.slice(0, INITIAL_PROPERTY_ROWS);
                    let html = `<table class="prop-table"><thead><tr><th>属性名</th><th>类型</th><th>描述</th></tr></thead><tbody>`;
                    for (const p of visibleProperties) {
                        const propertyDescription = ontologyPropertyDescription(
                            `${className}.${p.name}`,
                            p.description || "",
                        );
                        html += `<tr>
                            <td style="color:var(--text-primary);font-weight:500;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${htmlEscape(p.name)}">${htmlEscape(ontologyLabel("property", `${className}.${p.name}`, p.name))}</td>
                            <td><span class="type-badge">${p.dataType || "String"}</span></td>
                            <td>${htmlEscape(propertyDescription || "—")}</td>
                        </tr>`;
                    }
                    html += `</tbody></table>`;
                    if (!showAll && detail.properties.length > INITIAL_PROPERTY_ROWS) {
                        html += `<button type="button" class="detail-expand-btn" style="width:100%;margin-top:8px;padding:8px;border:1px solid rgba(0,255,185,.35);border-radius:6px;background:rgba(0,255,185,.08);color:var(--si-green);cursor:pointer">
                            显示其余 ${detail.properties.length - INITIAL_PROPERTY_ROWS} 个字段
                        </button>`;
                    }
                    propTable.innerHTML = html;
                    propTable.querySelector(".detail-expand-btn")?.addEventListener(
                        "click",
                        () => renderProperties(true),
                        { once: true },
                    );
                };
                renderProperties();
            } else {
                propTable.innerHTML = `<div style="color:var(--text-muted);font-size:12px;">暂无属性</div>`;
            }

            // ── Relations ──
            let relHtml = "";
            if (detail.outgoing && detail.outgoing.length > 0) {
                relHtml += `<div class="rel-section-label">它引用的对象 →</div>`;
                for (const r of detail.outgoing) {
                    const relationLabel = ontologyLabel("relationship", r.relName, r.relName);
                    const targetLabel = ontologyLabel("node", r.targetClass, r.targetClass, nodeInfoCache.get(r.targetClass)?.data?.chineseName || "");
                    const fullLabel = `→ ${relationLabel} · ${targetLabel}${r.cardinality ? ` · ${r.cardinality}` : ""}`;
                    relHtml += `<div class="rel-item rel-item-out" data-source="${htmlEscape(className)}" data-target="${htmlEscape(r.targetClass)}" data-rel="${htmlEscape(r.relName)}" title="${htmlEscape(fullLabel)}">
                        <span class="rel-arrow">→</span>
                        <span class="rel-name">${htmlEscape(relationLabel)}</span>
                        <span class="rel-target">${htmlEscape(targetLabel)}</span>
                        <span class="rel-card">${r.cardinality || ""}</span>
                    </div>`;
                }
            }
            if (detail.incoming && detail.incoming.length > 0) {
                relHtml += `<div class="rel-section-label rel-section-label-in" style="margin-top:12px">被何处引用 ←</div>`;
                for (const r of detail.incoming) {
                    const relationLabel = ontologyLabel("relationship", r.relName, r.relName);
                    const sourceLabel = ontologyLabel("node", r.sourceClass, r.sourceClass, nodeInfoCache.get(r.sourceClass)?.data?.chineseName || "");
                    const fullLabel = `← ${relationLabel} · ${sourceLabel}${r.cardinality ? ` · ${r.cardinality}` : ""}`;
                    relHtml += `<div class="rel-item rel-item-in" data-source="${htmlEscape(r.sourceClass)}" data-target="${htmlEscape(className)}" data-rel="${htmlEscape(r.relName)}" title="${htmlEscape(fullLabel)}">
                        <span class="rel-arrow">←</span>
                        <span class="rel-name">${htmlEscape(relationLabel)}</span>
                        <span class="rel-target">${htmlEscape(sourceLabel)}</span>
                        <span class="rel-card">${r.cardinality || ""}</span>
                    </div>`;
                }
            }
            relList.innerHTML = relHtml || `<div style="color:var(--text-muted);font-size:12px;">暂无关系</div>`;

            // ── Click relation chip → focus only the two endpoints ──
            relList.querySelectorAll(".rel-item").forEach((el) => {
                el.addEventListener("click", () => {
                    relList.querySelectorAll(".rel-item.pair-focused").forEach((item) => item.classList.remove("pair-focused"));
                    el.classList.add("pair-focused");
                    focusRelationshipPair(el.dataset.source, el.dataset.target, el.dataset.rel);
                });
            });
        } catch (err) {
            sectionMeta.innerHTML = `<div class="meta-row"><span class="meta-value" style="color:#FF6666">加载失败: ${err.message}</span></div>`;
        }
    }

    function closePanel() {
        detailRenderToken++;
        document.getElementById("detailPanel").classList.add("panel-hidden");
    }

    // ══════════════════════════════════════════════════════
    // ══════════════════════════════════════════════════════
    //  Search
    // ══════════════════════════════════════════════════════
    function setupSearch() {
        const input = document.getElementById("searchInput");
        let debounceTimer;
        let isComposing = false;

        // 阻断拼音输入法输入期间的频繁检索重绘
        input.addEventListener("compositionstart", () => {
            isComposing = true;
        });

        input.addEventListener("compositionend", () => {
            isComposing = false;
            // 汉字选词上屏后立即执行检索
            triggerSearch(input.value.trim());
        });

        input.addEventListener("input", () => {
            if (isComposing) return; // 拼音打字过程中不触发检索

            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                triggerSearch(input.value.trim());
            }, 350); // 适度增加防抖时间至 350ms 减缓冲击
        });

        function triggerSearch(text) {
            const query = text.toLowerCase();
            if (!graph || !rawData) return;

            if (queryBuilderState.active) {
                applyQueryMainStates(query);
                return;
            }

            if (!query) {
                clearHighlight();
                return;
            }

            // Preserve the original text-search behavior.
            const states = {};
            const nodes = rawData.nodes;
            const len = nodes.length;
            for (let i = 0; i < len; i++) {
                const n = nodes[i];
                const label = (n.data?.label || n.id).toLowerCase();
                const cn = (n.data?.chineseName || "").toLowerCase();
                const match = label.indexOf(query) !== -1 || cn.indexOf(query) !== -1;
                states[n.id] = match ? ["active"] : ["inactive"];
            }
            _applyStates(states);
        }
    }

    // ══════════════════════════════════════════════════════
    //  Stats
    // ══════════════════════════════════════════════════════
    async function loadStats() {
        try {
            const s = await fetchJSON("/api/stats");
            document.querySelector("#statClasses .stat-num").textContent = s.classCount;
            document.querySelector("#statProps .stat-num").textContent = s.propertyCount;
            document.querySelector("#statRels .stat-num").textContent = s.relationCount;
        } catch (_) { /* silent */ }
    }

    // ══════════════════════════════════════════════════════
    //  Relationship Focus Mode
    // ══════════════════════════════════════════════════════
    function toggleRelMode() {
        relMode = !relMode;
        const btn = document.getElementById("btnRelMode");
        const body = document.body;

        if (relMode) {
            btn.classList.add("icon-btn-active");
            body.classList.add("rel-mode");
            closePanel();
            // Switch to dagre-LR for clean relationship view
            switchLayout("dagre-lr", true);
        } else {
            btn.classList.remove("icon-btn-active");
            body.classList.remove("rel-mode");
            // Restore to dagre-TB
            switchLayout("dagre-tb", true);
        }
    }

    // ── Rel-only panel (no properties, just relationships) ──
    async function showRelOnly(className) {
        const renderToken = ++detailRenderToken;
        const panel = document.getElementById("detailPanel");
        const panelTitle = document.getElementById("panelTitle");
        const sectionMeta = document.getElementById("sectionMeta");
        const propTable = document.getElementById("propTable");
        const relList = document.getElementById("relList");
        const sectionProperties = document.getElementById("sectionProperties");

        panelTitle.textContent = className + " — 关系视图";
        syncChatContextButton(className);

        let detail;
        if (classDetailCache.has(className)) {
            detail = classDetailCache.get(className);
            sectionProperties.style.display = "none";
            panel.classList.remove("panel-hidden");
        } else {
            // Show loading state for network fetch
            sectionMeta.innerHTML = `<div class="meta-row"><span class="meta-value" style="color:var(--text-muted)">加载中...</span></div>`;
            propTable.innerHTML = "";
            relList.innerHTML = "";
            sectionProperties.style.display = "none";
            panel.classList.remove("panel-hidden");

            try {
                detail = await fetchJSON(`/api/graph/class/${encodeURIComponent(className)}`);
                classDetailCache.set(className, detail);
            } catch (err) {
                if (renderToken !== detailRenderToken) return;
                sectionMeta.innerHTML = `<div class="meta-row"><span class="meta-value" style="color:#FF6666">加载失败: ${err.message}</span></div>`;
                return;
            }
        }

        if (renderToken !== detailRenderToken) return;
        try {
            const nodeInfo = nodeInfoCache.get(className);
            const module = nodeInfo?.data?.module || "other";

            sectionMeta.innerHTML = `
                <div class="meta-row"><span class="meta-label">类名</span><span class="meta-value" style="font-weight:600;color:var(--si-green)">${className}</span></div>
                <div class="meta-row"><span class="meta-label">模块</span><span class="meta-value" style="color:${(COLORS[module] || COLORS.other).fill}">${module.toUpperCase()}</span></div>
                <div class="meta-row"><span class="meta-label">引用了</span><span class="meta-value" style="color:var(--si-green);font-weight:700">${(detail.outgoing || []).length}</span></div>
                <div class="meta-row"><span class="meta-label">被引用</span><span class="meta-value" style="color:#FF4081;font-weight:700">${(detail.incoming || []).length}</span></div>
            `;

            // Relationships only
            let relHtml = "";
            if (detail.outgoing && detail.outgoing.length > 0) {
                relHtml += `<div class="rel-section-label">它引用的对象 →</div>`;
                for (const r of detail.outgoing) {
                    const fullLabel = `→ ${r.relName} · ${r.targetClass}${r.cardinality ? ` · ${r.cardinality}` : ""}`;
                    relHtml += `<div class="rel-item rel-item-out" data-source="${htmlEscape(className)}" data-target="${htmlEscape(r.targetClass)}" data-rel="${htmlEscape(r.relName)}" title="${htmlEscape(fullLabel)}">
                        <span class="rel-arrow">→</span>
                        <span class="rel-name">${htmlEscape(r.relName)}</span>
                        <span class="rel-target">${htmlEscape(r.targetClass)}</span>
                        <span class="rel-card">${r.cardinality || ""}</span>
                    </div>`;
                }
            }
            if (detail.incoming && detail.incoming.length > 0) {
                relHtml += `<div class="rel-section-label rel-section-label-in" style="margin-top:12px">被何处引用 ←</div>`;
                for (const r of detail.incoming) {
                    const fullLabel = `← ${r.relName} · ${r.sourceClass}${r.cardinality ? ` · ${r.cardinality}` : ""}`;
                    relHtml += `<div class="rel-item rel-item-in" data-source="${htmlEscape(r.sourceClass)}" data-target="${htmlEscape(className)}" data-rel="${htmlEscape(r.relName)}" title="${htmlEscape(fullLabel)}">
                        <span class="rel-arrow">←</span>
                        <span class="rel-name">${htmlEscape(r.relName)}</span>
                        <span class="rel-target">${htmlEscape(r.sourceClass)}</span>
                        <span class="rel-card">${r.cardinality || ""}</span>
                    </div>`;
                }
            }
            relList.innerHTML = relHtml || `<div style="color:var(--text-muted);font-size:12px;">暂无关系</div>`;

            // Keep the current detail context and focus only the selected pair.
            relList.querySelectorAll(".rel-item").forEach(el => {
                el.addEventListener("click", () => {
                    relList.querySelectorAll(".rel-item.pair-focused").forEach((item) => item.classList.remove("pair-focused"));
                    el.classList.add("pair-focused");
                    focusRelationshipPair(el.dataset.source, el.dataset.target, el.dataset.rel);
                });
            });
        } catch (err) {
            sectionMeta.innerHTML = `<div class="meta-row"><span class="meta-value" style="color:#FF6666">加载失败: ${err.message}</span></div>`;
        }
    }

    // ══════════════════════════════════════════════════════
    //  Toolbar Buttons & Export
    // ══════════════════════════════════════════════════════
    function setupToolbar() {
        document.getElementById("btnFitView").addEventListener("click", () => {
            if (graph) graph.fitView();
        });

        document.getElementById("btnToggleCombo").addEventListener("click", () => {
            comboEnabled = !comboEnabled;
            if (rawData && graph) {
                const data = buildGraphData(rawData, comboEnabled);
                graph.setData(data);
                graph.render();
            }
        });

        document.getElementById("btnRelMode").addEventListener("click", toggleRelMode);

        // Layout cycling button
        document.getElementById("btnLayout").addEventListener("click", () => {
            const idx = LAYOUT_KEYS.indexOf(layoutMode);
            const nextIdx = (idx + 1) % LAYOUT_KEYS.length;
            switchLayout(LAYOUT_KEYS[nextIdx]);
        });

        document.getElementById("btnClosePanel").addEventListener("click", () => {
            closePanel();
            // Restore properties section visibility
            document.getElementById("sectionProperties").style.display = "";
        });

        // ── Export Listeners ──


        document.getElementById("btnExportHTML").addEventListener("click", exportOfflineHTML);
    }

    /**
     * Generates a standalone HTML file with embedded data and viewer
     */
    async function exportOfflineHTML() {
        if (!rawData || !graph) return;

        let cssContent = "";
        try {
            const res = await fetch("/static/style.css");
            cssContent = await res.text();
        } catch (e) { console.warn(e); }

        let g6Script = "";
        try {
            const res = await fetch("/static/lib/g6.js");
            g6Script = await res.text();
        } catch (e) { console.warn(e); }

        // Capture current data and positions
        const currentData = graph.getData();

        // Flatten the data: remove combos and ensure x,y are at the root
        // Keep only clean JSON data properties to prevent G6 v5 circular structures
        const flattenedNodes = currentData.nodes.map(n => {
            const pos = graph.getElementPosition(n.id) || [0, 0];
            const x = pos[0];
            const y = pos[1];
            const { comboId, ...cleanData } = n.data || {};

            return {
                id: n.id,
                style: {
                    x: x,
                    y: y
                },
                data: {
                    label: cleanData.label,
                    chineseName: cleanData.chineseName,
                    description: cleanData.description,
                    module: cleanData.module,
                    layer: cleanData.layer
                }
            };
        });

        // Clean edges to strip G6 internal runtime styles/references
        const cleanEdges = currentData.edges.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            data: {
                label: e.data?.label || "",
                cardinality: e.data?.cardinality || "",
                description: e.data?.description || ""
            }
        }));

        // Capture all current states
        const currentStates = {};
        currentData.nodes.forEach(n => {
            currentStates[n.id] = graph.getElementState(n.id);
        });
        currentData.edges.forEach(e => {
            currentStates[e.id] = graph.getElementState(e.id);
        });

        const g6ImportBlock = g6Script 
            ? `<script>${g6Script}</script>` 
            : `<script src="https://unpkg.com/@antv/g6@5.0.24/dist/g6.min.js"></script>`;

        const htmlContent = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Opcenter Ontology Snapshot</title>
    <style>
        ${cssContent}
        body { background: #000D1A; font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
        #app { height: 100vh !important; margin-top: 0 !important; display: flex; overflow: hidden; }
        #graphContainer { flex: 1; height: 100%; position: relative; background: radial-gradient(circle at center, #001A33 0%, #000D1A 100%); }
        .dropdown, #chatToggleBtn, .icon-btn-chat, .topbar-divider { display: none !important; }
        #detailPanel { position: absolute; left: 0; right: auto; top: 0; bottom: 0; width: 320px; transition: transform 0.3s ease; border-left: 0; border-right: 1px solid rgba(0,153,153,.2); }
    </style>
    ${g6ImportBlock}
</head>
<body>
    <main id="app">
        <div id="graphContainer">
            <div style="position:absolute; top:20px; left:20px; z-index:10; color:rgba(255,255,255,0.5); font-size:12px; pointer-events:none;">
                Opcenter Ontology Explorer - 离线快照<br/>导出时间: ${new Date().toLocaleString()}
            </div>
        </div>
        <aside id="detailPanel" class="panel-hidden">
            <div class="panel-header">
                <h2 id="panelTitle">详情</h2>
                <button onclick="document.getElementById('detailPanel').classList.add('panel-hidden')" style="color:#fff;background:none;border:none;cursor:pointer;font-size:20px;">×</button>
            </div>
            <div class="panel-body">
                <div id="sectionMeta" class="panel-section"></div>
                <div id="sectionProperties" class="panel-section"></div>
                <div id="sectionRelations" class="panel-section"></div>
            </div>
        </aside>
    </main>
    <div id="legend" class="legend-collapsed">
        <div class="legend-header" onclick="document.getElementById('legend').classList.toggle('legend-collapsed')">
            <div class="legend-title">模块图例</div>
        </div>
        <div class="legend-list" id="legendList"></div>
    </div>

    <script>
        const graphData = {
            nodes: ${JSON.stringify(flattenedNodes)},
            edges: ${JSON.stringify(cleanEdges)}
        };
        const graphStates = ${JSON.stringify(currentStates)};
        const COLORS = ${JSON.stringify(COLORS)};
        const COMBO_LABELS = ${JSON.stringify(COMBO_LABELS)};
        
        window.addEventListener("load", () => {
            const container = document.getElementById('graphContainer');
            const width = container.clientWidth || window.innerWidth || 800;
            const height = container.clientHeight || window.innerHeight || 600;
            const graph = new G6.Graph({
                container: 'graphContainer',
                width: width,
                height: height,
                autoFit: 'view',
                node: {
                    type: 'circle',
                    style: {
                        size: 48,
                        fill: (d) => (COLORS[d.data?.module] || COLORS.other).fill,
                        stroke: (d) => (COLORS[d.data?.module] || COLORS.other).stroke,
                        lineWidth: 2,
                        labelText: (d) => d.data?.chineseName ? (d.data.label || d.id) + '\\n(' + d.data.chineseName + ')' : (d.data?.label || d.id),
                        labelFill: "#E8F0F2",
                        labelFontSize: 12,
                        labelPlacement: "bottom",
                        labelOffsetY: 5,
                        iconText: (d) => (d.data?.label || d.id).substring(0, 2),
                        iconFill: "#fff",
                        iconFontSize: 14,
                        iconFontWeight: 700,
                        cursor: "pointer",
                    },
                    state: {
                        highlighted: { lineWidth: 4, stroke: "#00FFB9", shadowBlur: 20, shadowColor: "#00FFB9", zIndex: 20 },
                        inactive: { opacity: 0.45, labelOpacity: 0.45, iconOpacity: 0.45, zIndex: 2 }
                    }
                },
                edge: {
                    type: 'quadratic',
                    style: {
                        stroke: "rgba(0,255,185,0.2)",
                        lineWidth: 1.0,
                        shadowBlur: 0,
                        halo: true,
                        haloLineWidth: 6,
                        haloStroke: "rgba(0,255,185,0.0)",
                        haloPointerEvents: "auto",
                        endArrowSize: 6,
                        endArrow: true,
                        labelText: (d) => d.data?.label || "",
                        labelFill: "rgba(0,255,185,0.75)",
                        labelFontSize: 10.5,
                        labelFontFamily: "Inter, sans-serif",
                        labelFontWeight: 500,
                        labelBackgroundFill: "rgba(0,0,40,0.88)",
                        labelBackgroundOpacity: 1,
                        labelPadding: [3, 6],
                        labelBackgroundRadius: 10,
                        curveOffset: 20,
                        cursor: "pointer",
                    },
                    state: {
                        active: {
                            stroke: "#00FFB9",
                            lineWidth: 1.7,
                            labelFill: "#00FFB9",
                            labelFontWeight: 600,
                            opacity: 1,
                            haloLineWidth: 45,
                            pointerEvents: "auto",
                            interactive: true,
                            zIndex: 12,
                        },
                        activeOut: {
                            stroke: "#00FFB9",
                            lineWidth: 2.0,
                            labelFill: "#00FFB9",
                            endArrowSize: 8,
                            labelFontWeight: 600,
                            opacity: 1,
                            haloLineWidth: 45,
                            pointerEvents: "auto",
                            interactive: true,
                            zIndex: 12,
                        },
                        activeIn: {
                            stroke: "#FF4081",
                            lineWidth: 2.0,
                            labelFill: "#FF4081",
                            endArrowSize: 8,
                            labelFontWeight: 600,
                            opacity: 1,
                            haloLineWidth: 45,
                            pointerEvents: "auto",
                            interactive: true,
                            zIndex: 12,
                        },
                        inactive: {
                            opacity: 0.4,
                            labelFill: "rgba(0,255,185,0.15)",
                            labelBackgroundFill: "rgba(0,0,40,0.2)",
                            pointerEvents: "none",
                            haloLineWidth: 0,
                            interactive: false,
                            zIndex: -2,
                        },
                    }
                },
                behaviors: [
                    'drag-canvas',
                    'zoom-canvas',
                    {
                        type: 'drag-element',
                        enableTransient: true,
                    },
                    'click-select'
                ],
            });

            graph.setData(graphData);
            graph.render().then(() => {
                graph.setElementState(graphStates);
            });

            // Legend Rendering
            const list = document.getElementById('legendList');
            Object.keys(COMBO_LABELS).forEach(k => {
                const item = document.createElement('div');
                item.className = 'legend-item';
                item.innerHTML = '<span class="legend-dot" style="background:'+COLORS[k].fill+'"></span>' + COMBO_LABELS[k];
                list.appendChild(item);
            });

            graph.on('node:click', (evt) => {
                const nodeId = evt.target.id;
                const nodeData = graph.getNodeData(nodeId);
                const d = nodeData?.data || {};
                const panel = document.getElementById('detailPanel');
                document.getElementById('panelTitle').innerText = d.label || nodeId;
                
                // Meta info
                document.getElementById('sectionMeta').innerHTML = \`
                    <div class="meta-row"><span class="meta-label">中文名</span><span class="meta-value">\${d.chineseName || '—'}</span></div>
                    <div class="meta-row"><span class="meta-label">模块</span><span class="meta-value" style="color:\${(COLORS[d.module] || COLORS.other).fill}">\${(d.module || 'other').toUpperCase()}</span></div>
                    <div class="meta-row"><span class="meta-label">描述</span><span class="meta-value">\${d.description || '—'}</span></div>
                \`;

                // Properties message
                document.getElementById('sectionProperties').innerHTML = \`
                    <h3>属性列表</h3>
                    <div style="color:rgba(255,255,255,0.4);font-size:12px;padding:8px 0;">离线快照暂不含详细属性字段</div>
                \`;

                // Relations traversal
                const outgoing = graphData.edges.filter(e => e.source === nodeId);
                const incoming = graphData.edges.filter(e => e.target === nodeId);
                
                let relHtml = "<h3>关系</h3>";
                if (outgoing.length > 0) {
                    relHtml += '<div class="rel-section-label">它引用的对象 →</div>';
                    outgoing.forEach(r => {
                        relHtml += \`<div class="rel-item rel-item-out" style="display:flex;align-items:center;gap:8px;padding:6px 8px;margin-bottom:4px;background:rgba(0,255,185,0.03);border:1px solid rgba(0,255,185,0.08);border-radius:4px;font-size:12px;">
                            <span class="rel-arrow" style="color:#00FFB9;">→</span>
                            <span class="rel-name" style="color:rgba(255,255,255,0.85);font-weight:500;">\${r.data?.label || ''}</span>
                            <span class="rel-target" style="color:#00FFB9;margin-left:auto;font-family:monospace;">\${r.target}</span>
                            <span class="rel-card" style="color:rgba(255,255,255,0.4);font-size:10px;">\${r.data?.cardinality || ''}</span>
                        </div>\`;
                    });
                }
                if (incoming.length > 0) {
                    relHtml += '<div class="rel-section-label" style="margin-top:12px;">被何处引用 ←</div>';
                    incoming.forEach(r => {
                        relHtml += \`<div class="rel-item rel-item-in" style="display:flex;align-items:center;gap:8px;padding:6px 8px;margin-bottom:4px;background:rgba(255,64,129,0.03);border:1px solid rgba(255,64,129,0.08);border-radius:4px;font-size:12px;">
                            <span class="rel-arrow" style="color:#FF4081;">←</span>
                            <span class="rel-name" style="color:rgba(255,255,255,0.85);font-weight:500;">\${r.data?.label || ''}</span>
                            <span class="rel-target" style="color:#FF4081;margin-left:auto;font-family:monospace;">\${r.source}</span>
                            <span class="rel-card" style="color:rgba(255,255,255,0.4);font-size:10px;">\${r.data?.cardinality || ''}</span>
                        </div>\`;
                    });
                }
                if (outgoing.length === 0 && incoming.length === 0) {
                    relHtml += '<div style="color:rgba(255,255,255,0.4);font-size:12px;padding:8px 0;">暂无关联关系</div>';
                }
                
                document.getElementById('sectionRelations').innerHTML = relHtml;
                panel.classList.remove('panel-hidden');
            });
        });
    </script>
</body>
</html>`;

        const blob = new Blob([htmlContent], { type: 'text/html' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `Opcenter_Ontology_Snapshot_${new Date().getTime()}.html`;
        link.click();
    }

    // ── Switch layout and re-render ──
    function switchLayout(key, skipLabelUpdate) {
        if (!LAYOUTS[key]) return;
        layoutMode = key;
        const data = buildGraphData(rawData, comboEnabled);

        // Adjust node size based on mode
        const nodeSize = relMode ? 36 : (key.startsWith("dagre") ? 44 : 56);
        const labelSize = relMode ? 10 : (key.startsWith("dagre") ? 10 : 11);

        data.nodes = data.nodes.map(n => ({
            ...n,
            style: { ...n.style, size: nodeSize, labelFontSize: labelSize },
        }));

        graph.setLayout({ ...LAYOUTS[key] });
        graph.setData(data);
        graph.render();

        // Update layout label indicator
        if (!skipLabelUpdate) {
            updateLayoutLabel();
        }
    }

    function updateLayoutLabel() {
        const el = document.getElementById("layoutLabel");
        if (el) el.textContent = LAYOUT_LABELS[layoutMode] || layoutMode;
    }

    // ══════════════════════════════════════════════════════
    //  Legend Interaction
    // ══════════════════════════════════════════════════════
    function setupLegend() {
        const legend = document.getElementById("legend");
        if (!legend || legend.classList.contains("legend-disabled")) return;
        const legendHeader = legend.querySelector(".legend-header");
        const legendSearch = document.getElementById("legendSearchInput");
        const legendList = document.getElementById("legendList");
        const legendCount = document.getElementById("legendCount");

        // Clear existing items
        legendList.innerHTML = "";

        // Keep track of active module filter
        let activeModuleKey = null;

        // Helper to save current order to localStorage
        function saveLegendOrder() {
            const currentKeys = [...legendList.querySelectorAll(".legend-item")].map(el => el.dataset.key);
            try {
                localStorage.setItem("camstar_ontology_legend_order", JSON.stringify(currentKeys));
            } catch (e) {
                console.error("Failed to save legend order:", e);
            }
        }

        // Determine sorted keys from localStorage or default
        let sortedKeys = Object.keys(COMBO_LABELS);
        try {
            const stored = localStorage.getItem("camstar_ontology_legend_order");
            if (stored) {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed)) {
                    const validParsed = parsed.filter(k => sortedKeys.includes(k));
                    const missing = sortedKeys.filter(k => !validParsed.includes(k));
                    sortedKeys = [...validParsed, ...missing];
                }
            }
        } catch (e) {
            console.error("Failed to load legend order:", e);
        }

        // Generate items dynamically in sorted order
        sortedKeys.forEach((key) => {
            const label = localizedComboLabel(key);
            const color = (COLORS[key] || COLORS.other).fill;

            const item = document.createElement("div");
            item.className = "legend-item";
            item.setAttribute("draggable", "true");
            item.dataset.module = label;
            item.dataset.key = key;
            item.innerHTML = `<span class="legend-dot" style="background:${color};"></span>${label}`;

            let wasDragged = false;

            // ── Drag & Drop Event Listeners ──
            item.addEventListener("dragstart", () => {
                item.classList.add("dragging");
                wasDragged = true;
            });

            item.addEventListener("dragend", () => {
                item.classList.remove("dragging");
                saveLegendOrder();
                // Small timeout to let any click event bubble and get ignored
                setTimeout(() => { wasDragged = false; }, 50);
            });

            // ── Click to Highlight Module ──
            item.addEventListener("click", (e) => {
                e.stopPropagation();
                if (wasDragged) return;

                // Toggle logic
                if (activeModuleKey === key) {
                    activeModuleKey = null;
                    item.classList.remove("active");
                    clearHighlight();
                } else {
                    // Deactivate previous
                    legendList.querySelectorAll(".legend-item.active").forEach(el => el.classList.remove("active"));

                    activeModuleKey = key;
                    item.classList.add("active");
                    highlightModule(key);
                }
            });

            legendList.appendChild(item);
        });

        // ── Dragover listener on list for vertical reordering ──
        legendList.addEventListener("dragover", (e) => {
            e.preventDefault();
            const draggingItem = legendList.querySelector(".dragging");
            if (!draggingItem) return;

            const siblings = [...legendList.querySelectorAll(".legend-item:not(.dragging)")];

            const nextSibling = siblings.find(sibling => {
                const rect = sibling.getBoundingClientRect();
                const offset = e.clientY - rect.top - rect.height / 2;
                return offset < 0;
            });

            legendList.insertBefore(draggingItem, nextSibling);
        });

        const legendItems = legendList.querySelectorAll(".legend-item");

        // Set initial count
        legendCount.textContent = `(${legendItems.length})`;

        // Toggle legend
        legendHeader.addEventListener("click", () => {
            legend.classList.toggle("legend-collapsed");
        });

        // Search legend
        legendSearch.addEventListener("input", (e) => {
            const query = e.target.value.trim().toLowerCase();
            let visibleCount = 0;

            legendItems.forEach((item) => {
                const moduleName = item.dataset.module.toLowerCase();
                const match = moduleName.includes(query);
                item.classList.toggle("hidden", !match);
                if (match) visibleCount++;
            });

            legendCount.textContent = `(${visibleCount}/${legendItems.length})`;
        });

        // Prevent click bubbling on search input
        legendSearch.addEventListener("click", (e) => e.stopPropagation());
    }

    /**
     * Highlights all nodes belonging to a specific module and its external connections.
     * Disconnected module nodes (no internal edges to other module nodes) are excluded
     * from highlighting to avoid showing orphan fragments.
     */
    function highlightModule(moduleKey) {
        if (!graph || !rawData) return;

        const targetModule = String(moduleKey).trim().toLowerCase();
        selectedNodeId = null;

        const states = {};
        const moduleNodeIds = new Set();
        const connectedNodeIds = new Set();

        // 1. Identify module nodes (case-insensitive)
        const allNodes = graph.getNodeData();
        const allCombos = graph.getComboData() || [];

        allNodes.forEach((node) => {
            const nodeMod = String(node.data?.module || "other").trim().toLowerCase();
            if (nodeMod === targetModule) {
                moduleNodeIds.add(String(node.id).trim());
            }
        });

        if (moduleNodeIds.size === 0) return;

        // 1.5 Build internal adjacency and find connected components within the module.
        // Only module nodes that are internally connected (directly or transitively)
        // should be highlighted. Isolated nodes (e.g. Site in the factory module)
        // are excluded so they don't appear as disconnected glowing fragments.
        const allEdges = graph.getEdgeData();
        const internalAdj = new Map();
        moduleNodeIds.forEach(id => internalAdj.set(id, new Set()));

        allEdges.forEach((edge) => {
            const sourceId = String(edge.source?.id || edge.source).trim();
            const targetId = String(edge.target?.id || edge.target).trim();
            if (!sourceId || !targetId || sourceId === "undefined" || targetId === "undefined") return;
            if (moduleNodeIds.has(sourceId) && moduleNodeIds.has(targetId)) {
                internalAdj.get(sourceId).add(targetId);
                internalAdj.get(targetId).add(sourceId);
            }
        });

        // BFS to find all module nodes reachable via internal edges
        const connectedModuleIds = new Set();
        const visited = new Set();
        for (const [id, neighbors] of internalAdj) {
            if (neighbors.size > 0 && !visited.has(id)) {
                const queue = [id];
                visited.add(id);
                connectedModuleIds.add(id);
                while (queue.length > 0) {
                    const cur = queue.shift();
                    for (const neighbor of internalAdj.get(cur)) {
                        if (!visited.has(neighbor)) {
                            visited.add(neighbor);
                            connectedModuleIds.add(neighbor);
                            queue.push(neighbor);
                        }
                    }
                }
            }
        }

        // If internal graph has no edges at all (single-node module or fully isolated),
        // fall back to all module nodes so single-node modules still get highlighted.
        const highlightNodeIds = connectedModuleIds.size > 0 ? connectedModuleIds : moduleNodeIds;

        // 2. Identify connected nodes, combos and edges (use highlightNodeIds)
        allEdges.forEach((edge) => {
            const sourceId = String(edge.source?.id || edge.source).trim();
            const targetId = String(edge.target?.id || edge.target).trim();

            // Robustness: Ignore malformed or missing IDs
            if (!sourceId || !targetId || sourceId === "undefined" || targetId === "undefined") return;

            const isSourceIn = highlightNodeIds.has(sourceId);
            const isTargetIn = highlightNodeIds.has(targetId);

            if (isSourceIn && isTargetIn) {
                states[edge.id] = ["active"];
            } else if (isSourceIn) {
                states[edge.id] = ["activeOut"];
                connectedNodeIds.add(targetId);
            } else if (isTargetIn) {
                states[edge.id] = ["activeIn"];
                connectedNodeIds.add(sourceId);
            } else {
                states[edge.id] = ["inactive"];
            }
        });

        // 3. Apply states to nodes
        allNodes.forEach((node) => {
            const nid = String(node.id).trim();
            if (highlightNodeIds.has(nid)) {
                states[node.id] = ["highlighted"];
            } else if (connectedNodeIds.has(nid)) {
                states[node.id] = ["active"];
            } else {
                states[node.id] = ["inactive"];
            }
        });

        // 4. Apply states to combos
        allCombos.forEach((combo) => {
            const cid = String(combo.id).trim();
            if (connectedNodeIds.has(cid)) {
                states[combo.id] = ["active"];
            } else {
                states[combo.id] = ["inactive"];
            }
        });

        // 5. Apply states using differential update
        _applyStates(states);

        // 6. Focus on the first connected module node
        graph.focusElement(Array.from(highlightNodeIds)[0], true);
        showModuleDetail(moduleKey);
    }

    /**
     * Shows a summary of the module in the detail panel
     */
    async function showModuleDetail(moduleKey) {
        const panel = document.getElementById("detailPanel");
        const panelTitle = document.getElementById("panelTitle");
        const sectionMeta = document.getElementById("sectionMeta");
        const propTable = document.getElementById("propTable");
        const relList = document.getElementById("relList");
        const sectionProperties = document.getElementById("sectionProperties");

        const label = localizedComboLabel(moduleKey);
        const color = (COLORS[moduleKey] || COLORS.other).fill;
        syncChatContextButton(null);

        panelTitle.innerHTML = `<span style="color:${color}">■</span> ${label} 概览`;
        sectionProperties.style.display = "none"; // Hide properties for module view
        panel.classList.remove("panel-hidden");

        // Calculate stats
        const modNodes = rawData.nodes.filter(n => (n.data?.module || "other") === moduleKey);
        const nodeIds = new Set(modNodes.map(n => n.id));

        const outgoingRels = [];
        const incomingRels = [];

        rawData.edges.forEach(e => {
            const sourceIn = nodeIds.has(e.source);
            const targetIn = nodeIds.has(e.target);

            if (sourceIn && !targetIn) {
                outgoingRels.push({ source: e.source, target: e.target, label: e.data?.label });
            } else if (!sourceIn && targetIn) {
                incomingRels.push({ source: e.source, target: e.target, label: e.data?.label });
            }
        });

        sectionMeta.innerHTML = `
            <div class="meta-row"><span class="meta-label">模块标识</span><span class="meta-value">${moduleKey}</span></div>
            <div class="meta-row"><span class="meta-label">包含类数</span><span class="meta-value" style="font-weight:700;color:var(--si-green)">${modNodes.length}</span></div>
            <div class="meta-row"><span class="meta-label">对外引用</span><span class="meta-value" style="color:var(--si-green)">${outgoingRels.length} 个关系</span></div>
            <div class="meta-row"><span class="meta-label">外部被引</span><span class="meta-value" style="color:#FF4081">${incomingRels.length} 个关系</span></div>
        `;

        // Build relations list
        let html = "";

        // Group by target class for outgoing
        if (outgoingRels.length > 0) {
            html += `<div class="rel-section-label">模块对外引用 (Outgoing)</div>`;
            // Take unique target classes or top N
            const targets = [...new Set(outgoingRels.map(r => r.target))].slice(0, 20);
            targets.forEach(t => {
                const rels = outgoingRels.filter(r => r.target === t);
                html += `<div class="rel-item rel-item-out" data-target="${t}">
                    <span class="rel-arrow">→</span>
                    <span class="rel-name">${rels[0].label}${rels.length > 1 ? '等' : ''}</span>
                    <span class="rel-target">${t}</span>
                </div>`;
            });
        }

        if (incomingRels.length > 0) {
            html += `<div class="rel-section-label rel-section-label-in" style="margin-top:12px">模块被外部引用 (Incoming)</div>`;
            const sources = [...new Set(incomingRels.map(r => r.source))].slice(0, 20);
            sources.forEach(s => {
                const rels = incomingRels.filter(r => r.source === s);
                html += `<div class="rel-item rel-item-in" data-target="${s}">
                    <span class="rel-arrow">←</span>
                    <span class="rel-name">${rels[0].label}${rels.length > 1 ? '等' : ''}</span>
                    <span class="rel-target">${s}</span>
                </div>`;
            });
        }

        relList.innerHTML = html || `<div style="color:var(--text-muted);font-size:12px;">无跨模块关系</div>`;

        // Click to navigate
        relList.querySelectorAll(".rel-item").forEach(el => {
            el.addEventListener("click", () => {
                const target = el.dataset.target;
                if (target) showClassDetail(target);
            });
        });
    }

    // ══════════════════════════════════════════════════════
    //  Resizable detail panel
    // ══════════════════════════════════════════════════════
    function setupDetailPanelResize() {
        const app = document.getElementById("app");
        const panel = document.getElementById("detailPanel");
        const handle = document.getElementById("detailPanelResizeHandle");
        if (!app || !panel || !handle) return;

        const storageKey = "camstar_detail_panel_width_v1";
        const defaultWidth = 380;
        const minimumWidth = 320;
        let dragStartX = 0;
        let dragStartWidth = defaultWidth;

        const widthLimits = () => {
            const maximum = Math.max(1, Math.floor(app.getBoundingClientRect().width / 2));
            return { minimum: Math.min(minimumWidth, maximum), maximum };
        };

        const applyWidth = (requested, persist = false) => {
            const { minimum, maximum } = widthLimits();
            const width = Math.round(Math.min(maximum, Math.max(minimum, Number(requested) || defaultWidth)));
            document.documentElement.style.setProperty("--panel-w", `${width}px`);
            handle.setAttribute("aria-valuemin", String(minimum));
            handle.setAttribute("aria-valuemax", String(maximum));
            handle.setAttribute("aria-valuenow", String(width));
            if (persist) {
                try { localStorage.setItem(storageKey, String(width)); } catch (_) { /* storage is optional */ }
            }
            return width;
        };

        let savedWidth = defaultWidth;
        try { savedWidth = Number(localStorage.getItem(storageKey)) || defaultWidth; } catch (_) { /* storage is optional */ }
        applyWidth(savedWidth);

        const finishDrag = (event) => {
            if (!document.body.classList.contains("detail-panel-resizing")) return;
            document.body.classList.remove("detail-panel-resizing");
            if (handle.hasPointerCapture?.(event.pointerId)) handle.releasePointerCapture(event.pointerId);
            applyWidth(panel.getBoundingClientRect().width, true);
        };

        handle.addEventListener("pointerdown", (event) => {
            if (event.button !== 0) return;
            event.preventDefault();
            event.stopPropagation();
            dragStartX = event.clientX;
            dragStartWidth = panel.getBoundingClientRect().width;
            document.body.classList.add("detail-panel-resizing");
            handle.setPointerCapture?.(event.pointerId);
        });

        handle.addEventListener("pointermove", (event) => {
            if (!document.body.classList.contains("detail-panel-resizing")) return;
            event.preventDefault();
            applyWidth(dragStartWidth + event.clientX - dragStartX);
        });
        handle.addEventListener("pointerup", finishDrag);
        handle.addEventListener("pointercancel", finishDrag);
        window.addEventListener("pointerup", finishDrag);
        window.addEventListener("pointercancel", finishDrag);

        handle.addEventListener("dblclick", (event) => {
            event.preventDefault();
            event.stopPropagation();
            applyWidth(defaultWidth, true);
        });

        handle.addEventListener("keydown", (event) => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
            event.preventDefault();
            const current = panel.getBoundingClientRect().width;
            const { minimum, maximum } = widthLimits();
            const requested = event.key === 'Home' ? minimum
                : event.key === 'End' ? maximum
                : current + (event.key === 'ArrowRight' ? 16 : -16);
            applyWidth(requested, true);
        });

        window.addEventListener("resize", () => applyWidth(panel.getBoundingClientRect().width));
    }

    // ══════════════════════════════════════════════════════
    //  Window resize
    // ══════════════════════════════════════════════════════
    function setupResize() {
        let resizeTimer;
        const container = document.getElementById("graphContainer");
        if ("ResizeObserver" in window) {
            const graphContainerObserver = new ResizeObserver(() => {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(() => {
                    if (graph) {
                        graph.resize(container.clientWidth, container.clientHeight);
                    }
                }, 60);
            });
            graphContainerObserver.observe(container);
        }
        window.addEventListener("resize", () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                if (graph) {
                    graph.resize(container.clientWidth, container.clientHeight);
                }
            }, 200);
        });
    }

    // ══════════════════════════════════════════════════════
    //  Bootstrap
    // ══════════════════════════════════════════════════════
    async function main() {
        const overlay = document.getElementById("loadingOverlay");
        const container = document.getElementById("graphContainer");

        try {
            if (window.CamstarI18n) await window.CamstarI18n.init();
            // Fetch overview data (Level 0)
            rawData = applyOverviewTranslations(await fetchJSON("/api/graph/overview"));
            window.rawData = rawData; // Expose for chat.js
            indexOverviewData(rawData);
            const data = buildGraphData(
                { ...rawData, edges: overviewApiEdges },
                comboEnabled,
            );

            // Init G6
            await initGraph(container, data);
            scheduleDetailPrefetch();

            // Load stats
            await loadStats();

            // Load UI config
            try {
                const cfg = await fetchJSON("/api/config");
                if (cfg.show_layout_switch) {
                    document.getElementById("btnLayout").style.display = "inline-flex";
                    document.getElementById("layoutLabel").style.display = "inline-block";
                }
            } catch (e) {
                console.warn("Failed to load config", e);
            }

            // Setup UI
            setupSearch();
            setupQueryBuilder();
            setupNodePriorityControl();
            setupChatContextControl();
            setupToolbar();
            setupLegend();
            setupDetailPanelResize();
            setupResize();
            await loadProductLines();
        } catch (err) {
            console.error("Failed to initialise graph:", err);
            container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#FF6666;font-size:14px;">
                加载失败: ${err.message}<br/>请确认后端服务已启动 (http://localhost:5050)
            </div>`;
        } finally {
            overlay.classList.add("hidden");
        }
    }

    window.addEventListener("camstar:i18n-change", async (event) => {
        if (!rawData || !graph) return;
        if (event.detail?.reason === "translation") {
            if (selectedNodeId) await showClassDetail(selectedNodeId);
            return;
        }
        applyOverviewTranslations(rawData);
        indexOverviewData(rawData);
        const data = buildGraphData(
            { ...rawData, edges: overviewApiEdges },
            comboEnabled,
        );
        graph.setData(data);
        await graph.render();
        document.querySelectorAll("#legendList .legend-item").forEach((item) => {
            const key = item.dataset.key;
            const label = localizedComboLabel(key);
            item.dataset.module = label;
            item.innerHTML = `<span class="legend-dot" style="background:${(COLORS[key] || COLORS.other).fill};"></span>${htmlEscape(label)}`;
        });
        if (queryBuilderState.active) {
            renderQuerySelectedNodes();
            if (queryBuilderState.plan) await renderQueryPreviewGraph();
        }
        if (selectedNodeId) await showClassDetail(selectedNodeId);
    });

    // Go
    document.addEventListener("DOMContentLoaded", main);
})();
