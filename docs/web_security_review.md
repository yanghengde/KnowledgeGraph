# Web 层安全与代码质量评审报告
**项目**: D:\Deepseek\camstar\Knowledge（FastAPI + 原生 JS 前端）
**评审范围**: web/server.py、web/shared.py、web/designer_metadata.py、web/routers/*（sync_center/chat/graph/wiki/sql_builder/ontology_import/i18n）、web/static/*（sync.js/app.js/chat.js/i18n.js）、以及被调用链上的 src/qa/* 与 src/graphstudio_sync/* 关键执行点
**结论日期**: 本次评审会话

---

## 1. 整体评价

系统整体架构清晰、分层合理，且**后端在若干高危点上有自觉的纵深防御**（SQL 生成只回显不执行、SQL 校验器、连接标识符白名单、action 可信身份机制、session_id 正则校验、原子写文件），值得肯定。但**整个应用没有任何认证/授权层**（server.py 无任何鉴权中间件），叠加 3 个可被未认证调用者直接利用的高危漏洞，使得整体风险为**高危**：

- **严重**：wiki 接口参数未校验 → 任意 .md 文件读写 + 存储型 XSS 链；
- **严重**：未认证可修改连接配置 → SSRF / 生产凭据外泄；
- **严重**：破坏性端点（清空 Neo4j、部署、激活）与 LLM 高成本端点全部裸奔；
- **中等**：CORS 配置错误、日志 date 参数路径遍历、actor 审计可伪造、聊天会话与日志完全公开等。

用户特别关注的问题（/ontology 是否执行 LLM 生成的 SQL）：**答案是不执行**。SQL 助手只生成 SQL 文本，经确定性校验后回显；全 Web 层没有任何"运行 SQL"的端点（详见 §3.4）。

---

## 2. 发现清单（按严重程度）

### 🔴 严重（Critical/High）

#### C-1 无认证 + Wiki 接口路径遍历 → 任意 .md 文件读写（并可升级为存储型 XSS）
- **位置**: web/routers/wiki.py:33-39（GET /api/wiki/relationship）、63-74（POST /api/wiki/save）、77-117（generate-one）、120-182（generate-batch）；src/ontology/wiki_manager.py:124-132（_wiki_filename/_wiki_filepath）、135-138（_ensure_product_dir）、145-234（read_wiki）、237-271（save_wiki）
- **描述**: product_line、source/rel/target（from_class/rel_name/to_class）四个参数**完全没有校验**，直接拼接进文件路径：`os.path.join(RELATIONSHIPS_DIR, product_line, f"{from_class}_{rel_name}_{to_class}.md")`。
- **为什么危险**:
  - **任意读**：`GET /api/wiki/relationship?product_line=../../../../etc&source=x&rel=y&target=z` 可读取磁盘上任意存在的 `*.md` 文件（AGENTS.md、docs/*.md 等），响应还会回显解析后的绝对路径（read_wiki 返回 "path": filepath, wiki.py:57）。
  - **任意写**：`POST /api/wiki/save` 的 content 完全可控，可覆写任意 *.md 与 *.meta.json（如项目根目录下的 AGENTS.md、docs 文档），破坏数据完整性；写入的 wiki 内容后续会被 /ontology 页面渲染（见 C-4）→ **存储型 XSS 链**。
- **修复建议**: 对 4 个参数统一做白名单校验（如 `^[A-Za-z0-9_\-]{1,120}$`），拒绝 `..`、`/`、`\\`；写前用 `Path.resolve()` 并断言 `relative_to(RELATIONSHIPS_DIR)`；读接口同样校验。

#### C-2 无认证修改连接配置 → SSRF / 生产凭据外泄
- **位置**: web/routers/sync_center.py:481-499（PUT /api/sync/connections/{connection_key}）；src/graphstudio_sync/connections.py:33-69（settings_from_profiles）、72-73（resolved_settings）、127-151（_test_graphstudio）
- **描述**: 任意未认证调用者可修改 camstar-source / ontology-neo4j / publish-ontology-neo4j / graph-studio 的 endpoint、username、database_name 与自由 dict config（密码不存 PG，来自环境变量）。
- **为什么危险**:
  - `resolved_settings` 被 preview/materialization/incremental/curation/schema_drift/attribute_projection 等管道使用（materialization.py:540、preview.py:1117、incremental.py:359/384 等）。攻击者把 camstar-source 的 endpoint 指向自己搭建的 SQL Server/Oracle → 触发 `/api/sync/jobs/camstar-full/preview` 等端点 → **服务器用环境变量中的 SRC_DB_USER/SRC_DB_PASSWORD 连接攻击者数据库**（凭据外泄 + 内网 SSRF 探测）。
  - 更直接的例子：改 graph-studio endpoint → `POST /api/sync/connections/graph-studio/test`（sync_center.py:508-513）→ `_test_graphstudio` 以 `Basic auth(graphstudio_user, graphstudio_password)` 向攻击者 URL 发 GET（connections.py:143-148）。
  - Neo4j 同理（connections.py:51-60 覆盖 neo4j_uri/publish_neo4j_uri）。
- **修复建议**: 整个 sync_center API 增加认证（见 C-3）；连接配置修改仅管理员可操作并留审计；连接测试目标做内网/公网白名单约束；生产凭据不要随任意 endpoint 下发。

#### C-3 认证缺失整体风险面（破坏性操作 + LLM 成本滥用）
- **位置**: server.py（无任何鉴权中间件/依赖注入）；破坏性端点：web/routers/ontology_import.py:710-748（POST /api/ontology-import/clear，清空整个 Neo4j，确认词写死在前端 UI，攻击者直接 POST 即命中）；sync_center.py:1078-1108（部署 apply）、986-996（release activate）、973-983（materialization apply）、872-893（schema change apply/rollback）、1441-1446（改系统设置）；LLM 成本端点：wiki.py:120-182（generate-batch 对全部关系逐个调 LLM）、chat.py:109-297（每次问答一次 LLM）、i18n.py:403-459（sync-descriptions 批量翻译）。
- **为什么危险**: 无认证 = 任何能触达 5050 端口的人都能：清空生产图谱、向 Graph Studio 发布/激活不可回滚版本、修改连接与系统设置、无限消耗 LLM API 费用。
- **修复建议**: 加认证层（反向代理 OIDC / 静态 Token / Basic），写操作强制鉴权；破坏性操作二次确认 + 审批；LLM 端点加频率限制与并发上限。

#### C-4 存储型 XSS：marked v15 无 sanitize 渲染用户/LLM 可控 wiki 内容
- **位置**: web/static/app.js:2711-2723（renderRelationshipWiki → `container.innerHTML = marked.parse(markdown)`）；web/static/lib/marked.js:2（marked v15.0.12，已无 sanitize 选项，HTML 原样透传）
- **数据来源**: /api/wiki/relationship 返回的 wiki 内容（wiki.py:49-60），该内容既可由用户通过 /api/wiki/save 写入（C-1），也可由 LLM 生成（wiki_manager.py:907-952 把用户可控的 from_class/rel_name/cardinality/description 拼进 prompt，存在提示注入空间）。
- **为什么危险**: 攻击者写入（或诱导 LLM 输出）含 `<img src=x onerror=...>` 的 wiki 后，任何打开 /ontology 页面的用户浏览器执行脚本（会话内无凭据但可盗取页面数据、触发同源 API 破坏性调用）。
- **修复建议**: marked.parse 之前对 HTML 做白名单清洗（DOMPurify），或先 escapeHtml 再渲染受控子集；wiki 写入时禁止原始 HTML。

### 🟠 中等（Medium）

#### M-1 CORS 配置错误：allow_origins=["*"] + allow_credentials=True
- **位置**: web/server.py:19-25
- **描述/为什么**: 该组合下 Starlette 会回显任意 Origin 并允许携带凭据。当前无 Cookie 认证，实际数据面影响有限，但：任意恶意网页可通过浏览器直接跨站调用本 API（JSON POST 预检会被放行）；一旦未来接入 Cookie/Session 认证即成全局 CSRF 面。属于明确的配置错误。
- **修复建议**: 显式 Origin 白名单（或与凭据二选一），生产环境关闭 `allow_credentials`。

#### M-2 日志接口 date 参数路径遍历
- **位置**: web/routers/chat.py:320-331（/api/logs）、334-340（/api/logs/{trace_id}）；src/qa/logger.py:33-37（_log_file_path：`os.path.join(CHAT_LOG_DIR, f"chat-{date_str}.jsonl")`，date 无格式校验）
- **描述/为什么**: date=`../../../../tmp/chat-test` 可跨目录读取任意 `chat-*.jsonl` 文件（文件名模式受限，但目录可越界）。真实风险低于任意读，但属于未校验输入进入文件系统的典型漏洞。
- **修复建议**: date 用 `^\d{4}-\d{2}-\d{2}$` 白名单校验；禁止 `..` 与路径分隔符。

#### M-3 越权/审计伪造：actor 全部为客户端自报
- **位置**: sync_center.py:986-996（ReleaseActivation.actor）、1093-1098（approve_deployment）、1124-1129（acknowledge_alert）、1268-1276（initialize_governance）、1370-1383（review/approve workspace）、1386-1395（activate release）、872-893（schema change review/apply）；模型定义 415-416（ActorRequest.actor）
- **描述/为什么**: 审批/激活/回滚的"操作人"来自请求体，未认证也未校验 → 任何人可冒用任意身份（如他人工号）完成审批并留下伪造审计记录。注意：actions 系列端点（sync_center.py:1147-1257）已通过 action_principal/trusted_headers 做了可信身份边界，其余端点未复用该机制。
- **修复建议**: 把 action_identity 的可信代理身份机制推广到所有审批类端点；无可信代理时拒绝真实写操作（与 C-3 一并治理）。

#### M-4 聊天会话与日志完全公开（无认证 + 无用户隔离）
- **位置**: chat.py:55-57（GET /api/chat/sessions 列出全部会话含预览）、60-68（GET /api/chat/sessions/{id} 返回完整问答历史）、309-311（/logs 页面）、320-331 与 334-340（/api/logs 全文检索）
- **描述/为什么**: 会话文件（data/chat_sessions/*.json）包含用户所有业务问答、生成的 SQL、上下文；日志 JSONL 含完整 question/answer。任何能访问服务器的人都能读取全部用户的对话与日志，且无归属隔离（session_store.py:211-249 list_sessions 遍历目录全部文件）。
- **修复建议**: 认证 + 会话按用户归属隔离；日志页/接口仅管理员可见。

#### M-5 错误处理：异常详情直接回显（信息泄露）
- **位置**: sync_center.py:105（`detail=f"PostgreSQL control plane unavailable: {exc}"`）、566/576/586/796/950/1265/1284/1296 等大量 `detail=str(exc)`；ontology_import.py:706/733/843/400 等；wiki.py:108；chat.py:272-273
- **描述/为什么**: 响应会把数据库驱动错误、内部路径、LLM 调用细节等透传给未认证客户端，辅助攻击者侦察内网与系统结构。
- **修复建议**: 记录完整异常到日志，对外只返回通用错误码/摘要。

#### M-6 导入接口内存 DoS
- **位置**: ontology_import.py:49（40MB 上限）、412-517（/analyze 把两张 CSV 全量存进程内 _sessions，52）、158-161（TTL 清理仅在新 analyze/translation 时触发）
- **描述/为什么**: 未认证并发 /analyze 可在内存中堆积数十 MB×N 的表/字段 dict，进程内存被耗尽。
- **修复建议**: 会话数上限、后台定期清理、并发限制。

#### M-7 提示注入放大面：wiki 生成无输出校验
- **位置**: wiki_manager.py:907-916（prompt 拼接用户可控 from_class/rel_name/cardinality/description）、928-952（LLM 输出直接落盘）
- **描述/为什么**: 与 C-4 组合后，攻击者可诱导 LLM 输出恶意 HTML/指令写回 wiki；SQL 助手有 sql_validator 兜底，wiki 通道没有任何输出侧校验。
- **修复建议**: wiki 生成增加输出校验（拒绝 HTML/脚本片段、长度限制），渲染侧 sanitize（C-4）。

### 🟡 轻微（Low）

- **L-1** server.py:85-94：直接以 `uvicorn.run(reload=True)` 启动，生产不建议 reload（代码变更即生效、进程管理粗放）；建议显式 worker/日志配置。
- **L-2** chat.py:321-322：`limit/offset` 未做约束（内部部分兜底），`date` 无校验（见 M-2）。
- **L-3** chat.js:679：SSE status 消息 `payload.content` 未转义插入 innerHTML（当前内容服务器可控为主，属纵深防御缺失）；chat.js:723 `err.message` 未转义。
- **L-4** logs.html:7、index.html:11-12、industry.html:9-10：依赖 Google Fonts 外部 CDN，内网/离线环境不可用且引入供应链与隐私依赖；建议本地化字体。
- **L-5** graph.py:124-130/195-203：`refresh=true` 可无条件清空 LRU 缓存（轻微 DoS 放大）；class_name 未校验但 Neo4j 参数化，无注入。
- **L-6** connections.py:197：连接测试错误截断 1000 字符回显（低危信息泄露，与 M-5 同源）。
- **L-7** chat.py:109-297：question 无长度上限，超长输入直接进 LLM（费用/超时）。

---

## 3. 重点关注项详析

### 3.1 认证缺失的风险面（最高优先级）
server.py 无任何鉴权中间件、无 Session/Token/Cookie；C-3/M-3/M-4 均由此产生。最小可行修复：前置反向代理做 OIDC/Basic，应用侧增加依赖注入校验 + 操作审计；破坏性端点（clear、deploy apply、activate、materialization apply、settings/connections 写）单独收紧。

### 3.2 CORS 配置
见 M-1。`allow_origins=["*"] + allow_credentials=True`（server.py:21-22）是明确的错误组合，Starlette 会反射任意 Origin。当前因无凭据机制影响有限，但必须修复以支撑后续认证。

### 3.3 SQL 注入：LLM 生成 SQL 的执行路径（用户重点问题）
**结论：LLM 生成的 SQL 当前不会被执行。** 证据链：
1. chat.js:634 调 /api/chat（chat.py:109）→ src/qa/engine.py:156 query_stream → assistant_mode="sql" 时 417-497：DeepSeek 生成 SQL 文本 → `sql_validator.validate_sql_answer` 确定性校验（两次尝试）→ 作为 markdown 文本 yield 回前端；前端 chat.js:750-765 `renderMarkdown` 先 escapeHtml 再渲染，仅提供"复制 SQL"按钮（767-784），无执行按钮。
2. app.js:1813 调 /api/sql-builder/plan（sql_builder.py:34-43）→ src/qa/sql_query_builder.py:318 build_query_builder_plan：纯 Schema 驱动的只读 SELECT 骨架，标识符必须命中 docs/Database_Fields.csv（_validate_reference_plan 182-230 fail-closed），join_overrides 必须是已登记物理外键（61-95）；前端 app.js:1777-1779 用 textContent 展示。
3. 全 web/ 目录 grep 无任何执行生成 SQL 的代码（仅 designer_metadata.py 用白名单标识符 + 参数化查询读 CDODefinition 元数据；server.py:78 healthz 静态 SQL）。src/qa 下存在 `oracle_sql_executor.cpython-313.pyc` 但源文件已不存在，说明执行能力已被移除（或从未合入）。
**残余风险与建议**：
- 校验器 sql_validator.py:38-43（_UNSAFE 黑名单）+ 表/列/JOIN 结构校验是正则黑名单 + 结构白名单的混合，存在被混淆绕过的理论空间（如多语句注释分割、方言差异），**当前安全完全依赖"只生成不执行"**；
- 一旦未来增加"运行 SQL"能力，必须：专用只读 DB 账号（连接锁定）、sqlglot/词法白名单解析、行数/超时/结果大小限制、禁止 UNION/子查询堆叠；切勿复用连接配置（见 C-2）。
- graphstudio_sync 各执行点防护良好（attribute_projection.py:34/63-73 标识符白名单 + 全参数化、curation.py:66-82 _safe_identifier、preview.py:197-198 SAFE_IDENTIFIER、incremental.py/schema_drift.py 静态 SQL），主要风险仍是 C-2 的连接配置被篡改后以生产凭据外联。

### 3.4 路径遍历
- **Wiki（严重）**：见 C-1。唯一未设防的文件路径拼接点。
- **日志 date（中等）**：见 M-2。
- **session_id（安全）**：src/qa/session_store.py:19/27-34 用 `^[a-zA-Z0-9_-]{8,80}$` 校验，无遍历。
- **ontology-import（安全）**：文件名用 tempfile.mkstemp + os.replace（ontology_import.py:635-643, 660-662, i18n.py:107-115），上传为 UploadFile 不落盘自定义路径。
- **OpenAPI source_file（安全）**：actions.py:216-221 断言 `path.parent == SWAGGER_ROOT`。

### 3.5 越权（多用户场景）
当前没有用户概念，唯一"身份"是自报 actor（M-3）。多用户部署后：会话无归属（M-4）、审批可伪造（M-3）、审计不可信。action 系列端点（sync_center.py:1148-1257）已示范可信身份方案（action_identity.py:20-37，trusted_headers + HMAC secret + x-authenticated-user/roles），应推广。

### 3.6 敏感信息暴露
- 聊天日志/会话全公开（M-4）；连接测试错误回显（L-6）；异常详情回显（M-5）；密码不落 PG（connections 表只存 secret_ref 标记，符合 AGENTS.md 约定，这点做得好）；`GET /api/sync/connections`（sync_center.py:472-478）只返回 username/secret_configured，不含密码。

### 3.7 错误处理
总体"异常→HTTPException(detail=str(exc))"模式（M-5）；wiki/chat 的 SSE 生成器把异常 str 推给客户端（wiki.py:108、chat.py:272-273）；无统一异常处理器与结构化日志。建议加全局 exception handler + 统一错误码 + 日志埋点。

### 3.8 XSS（前端渲染用户内容）
- **高危**：app.js:2717 `marked.parse` 无 sanitize 渲染 wiki（C-4）。
- **低危**：chat.js:679 status 未转义（L-3）；chat.js:723 err.message 未转义。
- **安全**：chat.js renderMarkdown（750-765）先 escapeHtml 再正则替换；sync.js 数据字段普遍用 escapeHtml（80-82、97、455、1224、1528、1616-1623 等）；i18n.js 主要用 textContent/DOM 构建（681-710、921-928 等），是本项目最规范的渲染方式；app.js SQL 预览用 textContent（1777-1779）。

---

## 4. 前端代码质量问题

1. **单文件过大、职责混杂**：sync.js ~3457 行、app.js ~4745 行、chat.js ~832 行，全部 IIFE + 全局 state；renderXxx 函数 + 事件委托 + 对话框生成混在一起，审计与维护成本高。建议按页签拆分模块（原生 ES Modules），状态用单一 store。
2. **模板字符串内嵌 HTML 的转义纪律**：sync.js 整体执行得好（escapeHtml 覆盖绝大多数数据字段），但 3457 行靠"自觉"维持转义纪律，建议引入统一的渲染函数（如 h()/html() 转义所有插值）或升级为框架/模板引擎，消灭漏转义可能。
3. **两套 markdown 渲染**：app.js 用 marked.parse（未 sanitize），chat.js 自写正则迷你渲染器（750-765，不支持表格/链接/列表嵌套，正则替换脆弱）。建议统一为 marked + DOMPurify，删除自写渲染器。
4. **错误处理不一致**：app.js fetchJSON（435-442）只抛 `HTTP ${status}` 不带 detail；sync.js request（106-115）解析 detail；chat.js 对 SSE 吞异常（700 `catch (_) {}`）。建议统一 fetch 封装。
5. **全局桥接**：window._getCurrentProductLine、_getSelectedNodeId、_locateNodeWithoutEdges、_highlightGraph 等（app.js:2697-2698、chat.js:791-793）跨文件耦合，建议用事件/模块接口替代。
6. **性能**：chat.js RENDER_THROTTLE_MS=100 内整段 innerHTML 重建（674）在大回答时 CPU 高；建议只增量渲染尾部。
7. **依赖外部 CDN**：Google Fonts（L-4），内网部署应本地化。
8. **静态版本号**：index.html:486-487 用 `?v=20260802-query-join-choice` 手工版本号，易漏更新导致缓存旧代码；建议构建期指纹。

---

## 5. 修复优先级建议

1. **立即**：C-1（wiki 参数白名单 + 路径锚定）、C-2（sync API 认证 + 连接配置保护）、C-3（认证层 + 破坏性端点收紧）、C-4（wiki 渲染 sanitize）。
2. **尽快**：M-1（CORS）、M-2（date 校验）、M-3（actor 可信化）、M-4（会话/日志访问控制）、M-5（错误回显收敛）。
3. **排期**：M-6/M-7/L-1~L-7 及前端质量问题。
