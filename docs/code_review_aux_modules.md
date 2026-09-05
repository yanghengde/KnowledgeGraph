# CamstarOntology 辅助模块代码评审报告

> 本文保留评审时的历史结论，部分实现及行号已变化。2026-09-05 已清理 scratch 探针、`get_shortest_path_details` 和 `_chat_sessions`，当前精简范围见 [项目精简记录](project_cleanup.md)。

评审范围：src/ontology（loader/wiki/runtime_state/llm_builder/explorer/validator）、src/qa（engine、graph_retriever、sql_*、semantic/、session_store、logger、vectorizer）、src/etl（旧中转 ETL）、scripts/validate_ontology_vs_csv.py、scripts/rebuild_indexes.py、scripts/check/*。所有结论均基于实际读取的代码，附文件:行号证据。

## 1. 整体评价

辅助模块的整体工程质量明显高于一般内部项目，核心设计取向值得肯定：

- 「只生成、不执行」的 SQL 安全边界非常清晰：prompt_builder.py:68 明确写入系统提示（本系统不连接业务数据库，也不执行 SQL）；chat 路由只回传文本（web/routers/chat.py:254-270），sql_builder 路由只返回计划（web/routers/sql_builder.py:34-43）。LLM 生成的 SQL 无法在现有架构下触达任何数据库执行面。
- 确定性校验 + 失败关闭（fail-closed）：sql_validator.py 对表名/列名/外键 JOIN/方言/时间半开区间做正则级校验；指标语义层（src/qa/semantic/）用不可变 Golden SQL + 契约校验 + 近邻一致性裁决（example_index.py:166-180），是整套代码里最严谨的部分。
- 凭据不落库：graphstudio_sync 控制面只存 secret_ref（env://NEO4J_PASSWORD 等，repository.py:99,144、database.py:81-136），符合 AGENTS.md「密码不得写入 PostgreSQL」；.env 已被 gitignore。
- 好实践：原子文件写入（runtime_state.py:34-36、session_store.py:37-44）、会话 id 白名单校验（session_store.py:19,27-30）、标识符转义（wiki_manager.py:468-475 的 _sql_identifier 正确处理 ] 与 "）、change_capture.py:26-30 的标识符 fail-fast 正则。

主要问题集中在：Web 层无鉴权 + 通配 CORS + 0.0.0.0 绑定、wiki 写接口路径穿越、「连接测试」脚本会清空 Neo4j、SQL 模式对 Neo4j 的隐式强依赖、一批死代码，以及若干资源清理/静默吞错问题。

## 2. 分级问题清单

### 严重

**S1. Web 服务无鉴权、CORS 通配 + 允许凭据、默认绑定 0.0.0.0**
- 位置：web/server.py:19-25（CORSMiddleware allow_origins=["*"] + allow_credentials=True）；web/server.py:87-92（uvicorn host="0.0.0.0", port=5050）。
- 为什么：所有 API（图谱、chat 含 LLM 调用、wiki 读写、sql-builder、sync_center 含 Graph Studio 操作）对网络内任意来源开放；CORS * + credentials 组合本身违反 CORS 规范。
- 建议：默认绑定 127.0.0.1 或加认证中间件；CORS 改为显式来源列表。

**S2. Wiki 写接口存在路径穿越/任意文件写风险**
- 位置：web/routers/wiki.py:63-74（save_wiki_endpoint 直接把请求的 product_line/source/rel/target 传入）；src/ontology/wiki_manager.py:129-138（_wiki_filepath 用 os.path.join(RELATIONSHIPS_DIR, product_line, filename)、_ensure_product_dir 用 os.makedirs）；wiki_manager.py:265-269（写文件）。
- 为什么：product_line 未做任何校验。Windows 下 product_line 传绝对路径（如 C:\Temp）时 os.path.join 会直接采用绝对路径；传 ../ 可越出 RELATIONSHIPS_DIR 写任意位置（save 会建目录+写文件）；read_wiki（wiki_manager.py:145-234）配合可读任意 .md 内容回显（信息泄露）。类名（source/rel/target）同样未校验即可进入文件名。
- 建议：product_line 必须属于 load_product_lines() 的 id 集合；from/rel/to 只允许 [A-Za-z_][A-Za-z0-9_]*；写入后校验 os.path.realpath 仍在 RELATIONSHIPS_DIR 下。可复用 sql_schema_retriever 的标识符校验思路。

**S3. scripts/check/demo_connection.py 会把非空 Neo4j 库整个清空**
- 位置：scripts/check/demo_connection.py:21-29。
- 为什么：该脚本名义是「测试连接」，却在 count>0 时执行 MATCH (n) DETACH DELETE n，清空整个图库（所有标签，不只 OntologyClass）。任何人在验证连接时跑一下就会造成数据丢失，且无确认提示。
- 建议：删除清理逻辑，连接测试只保留 verify_connectivity()。同类破坏性操作（neo4j_loader.py:174 的 --clear 全库 DETACH DELETE）建议限定标签范围或二次确认。

### 中等

**M1. SQL 问答模式隐式依赖 Neo4j 在线**
- 位置：src/qa/engine.py:325-338（query_stream 对 SQL 模式也无条件执行 search_graph）；engine.py:101-105、117-122（extract_keywords 依赖 _get_class_names() → Neo4j 查询）。
- 为什么：SQL 模式明确不使用向量与图谱上下文（chat.py:130 跳过 ChromaDB），但 Neo4j 宕机时整个 SQL 助手（含关键词解析）直接不可用，且无降级路径。
- 建议：类名缓存到本地（启动时快照），search_graph 失败时降级为空上下文并记录告警。

**M2. LLM client 生命周期与 key 校验不一致**
- 位置：src/ontology/wiki_manager.py:1045（每次流式调用 new AsyncOpenAI，从不关闭）；src/ontology/llm_builder.py:9-13（模块导入时即构建 OpenAI client，DEEPSEEK_API_KEY 缺失时无任何校验）。
- 建议：统一惰性单例 + 导入时校验 key 存在（参考 web/routers/i18n.py:383-387 的 503 处理）。

**M3. ETL 水位线读写吞掉所有异常**
- 位置：src/etl/etl_engine.py:13-22（get_watermark except Exception → 返回 2020-01-01）、24-41（set_watermark 同样吞错）。
- 为什么：连接失败与表不存在被同样对待，静默回退到全量起点，导致每次增量都扫全表（性能+数据正确性隐患），且故障完全不可见。
- 建议：区分连接异常与业务异常，连接失败上抛；水位线写失败应告警。

**M4. ETL upsert 用 f-string 拼接表名/列名**
- 位置：src/etl/etl_engine.py:43-61（MERGE {table} ... {cols} ... {merge_key} 全部直接插值；cols 来自 DataFrame 列名，即源查询结果）。
- 为什么：当前输入受控（配置/静态 SQL 别名），但属「数据驱动 SQL 构造」，一旦列名被源侧污染即形成注入面；SQL Server 方括号标识符未转义。
- 建议：列名经白名单/标识符转义后拼接，或改用 SQLAlchemy 结构生成。

**M5. neo4j_loader 通过 sys.path 注入导入 scripts 顶层模块**
- 位置：src/ontology/loader/neo4j_loader.py:12-14（sys.path.insert scripts 目录）、40-45 与 171（from rebuild_indexes import ensure_indexes）。
- 建议：把 ensure_indexes 移入 src/ontology/loader/ 或共享层，脚本只留 CLI 壳。

**M6. ChromaDB PersistentClient 从不 close，Windows 下有锁库风险**
- 位置：src/qa/vectorizer.py:104；src/qa/semantic/example_index.py:50-54（_client() 每次新建）；web/shared.py:29-40（懒加载单例持有整个进程生命周期）。
- 建议：进程级单例 + 应用关闭钩子 close()。

**M7. 会话与日志无上限、日志明文存敏感内容**
- 位置：src/qa/session_store.py:167-208（append_exchange 消息无限累积）；src/qa/logger.py:144（仅截断 2000 字符，内容含完整问答与 SQL 文本，无脱敏）。
- 建议：会话按轮数/字节截断归档；日志加脱敏与保留策略。

**M8. SQL 安全门为正则启发式（可绕过），但受「不执行」约束缓解**
- 位置：src/qa/engine.py:68-75（UNSAFE_SQL_REQUEST）；src/qa/sql_validator.py:38-43（_UNSAFE）。
- 建议：保持现状并补充绕过样本的回归测试；未来若增加预览执行，必须参数化 + 只读连接 + LIMIT 硬上限。

**M9. 新核心模块对辅助模块的代码依赖**
- 位置：src/graphstudio_sync/publish_ontology.py:19,152（import src.qa.sql_query_builder）；src/qa/sql_query_builder.py:7（import src.ontology.wiki_manager._sql_identifier）。
- 为什么：依赖链 graphstudio_sync → qa → ontology.wiki_manager。不违反「新代码不得依赖 etl」，但与 graphstudio_sync 为核心独立模块的定位存在张力；目前仅用于只读 discovery 计划。
- 建议：文档化依赖方向并加防护测试。

**M10. web 层反向依赖 scripts/ 顶层脚本**
- 位置：web/routers/ontology_import.py:28-33（from scripts.generate_ontology_batch import relation_name；from scripts.validate_ontology_vs_csv import ...）。
- 建议：把 relation_name / canonical_physical_fields 等迁入 src/ontology/ 包内。

**M11. Neo4j driver 配置缺省值静默降级**
- 位置：src/qa/graph_retriever.py:22-25（默认 bolt://localhost:7687 / neo4j / 空密码）；web/shared.py:15-17；scripts/rebuild_indexes.py:132-134,146-148。
- 建议：关键路径用 _required 语义（同 graphstudio_sync/config.py:16-20），脚本路径至少打印告警。

### 轻微

- m1 死代码（详见第 3 节死代码段落）。
- m2 src/ontology/wiki_manager.py:960-1006 strip_markdown_code_blocks_stream：头部检测逻辑复杂且首行非代码块时 buffer 处理有边界缺陷，建议重写为简单状态机。
- m3 src/qa/engine.py:414 硬编码默认模型 deepseek-v4-flash，与 wiki_manager.py:32 默认 deepseek-chat 不一致，建议统一 env 默认。
- m4 src/qa/vectorizer.py:69 chunk id 为 f(title[:30]_idx) 且 idx 每章重置：两个标题前 30 字符相同的章节会产生重复 id，ChromaDB add 会抛错。
- m5 src/etl/aggregations/aggregations.py:14-18：compute_cycletime_records 自连接无「最近一次 MoveIn」约束，同容器同步骤多次通过会笛卡尔配对，cycle_sec 可能为负或异常大；建议限制 mi.EventTime < mo.EventTime 且取 MAX(mi.EventTime)。
- m6 scripts/check/check_camstar.py:9：f-string 拼表名（本地只读脚本，风险极低）。
- m7 src/qa/semantic/example_index.py:134：query_metric_examples 捕获所有异常静默返回 []，向量索引损坏时无任何可见告警直接降级到 LLM 生成。
- m8 src/etl/etl_engine.py:83-84,96：run_entity 捕获所有异常并截断后跳过，「表不存在」与真实故障不可区分。
- m9 src/ontology/wiki_manager.py:21 与 src/qa/engine.py:61 使用 load_dotenv(override=True)，会覆盖显式环境变量；与 web/shared.py:13（override=False）不一致，建议统一为 False。
- m10 src/etl/config/db_config.py:23-26 与 web/designer_metadata.py:44：TrustServerCertificate=yes 为默认值，生产环境应显式配置证书校验。

## 3. 重点关注项

### 3.1 Neo4j 密码处理
- 合规点：全部经 os.getenv + .env（已 gitignore）；新模块控制面只存 secret_ref 引用（database.py:81,95,105-108,119,136；repository.py:99,144），明文密码从未写入 PostgreSQL；未发现硬编码密码。
- 风险点：graph_retriever.py:24、web/shared.py:17、rebuild_indexes.py:134/148 在 env 缺失时回退到 bolt://localhost:7687 / neo4j / 空密码静默降级；连接均用 bolt:// 明文（未强制 bolt+s）。

### 3.2 LLM API Key 处理
- 合规点：所有 key 来自 env；ontology_import.py:219-224 与 i18n.py:383-387 有缺失校验（返回 503/禁用），属于正确示范。
- 风险点：llm_builder.py:9-13 模块导入即建 client、无 key 校验；wiki_manager.py:1045 流式路径每次新建 client。

### 3.3 SQL 注入（LLM 生成的 SQL 如何校验与执行）
- 结论：LLM 生成的 SQL 在当前架构下从不执行，SQL 注入不可达。证据：prompt_builder.py:68（系统提示明示不连接不执行）、engine.py:424-469（生成→校验→修复一次→仍失败则不展示）、web/routers/sql_builder.py:34-43（只返回计划文本）、chat.py:254-270（只回 SSE 文本）。
- 校验链（质量良好）：engine.py 的 validate_sql_answer（sql_validator.py:118-289）做表名/列名/物理外键 JOIN/方言/时间半开区间校验，失败关闭；指标路径走不可变 Golden SQL + 契约校验（engine.py:210-323、metric_validator.py）。
- 弱点：validator 是文本级正则，_UNSAFE（sql_validator.py:38-43）可被变体绕过；但因不执行，影响限于展示错误 SQL。真正的执行面在 graphstudio_sync（参数化查询 + 标识符白名单，见 change_capture.py:26-30、attribute_projection.py:234-254）和 etl（config 静态 SQL + text() 参数化，但 upsert f-string 拼接列名见 M4）。
- 建议：保持「不执行」红线；为 sql_validator 补充绕过样本回归测试；若未来新增试运行，必须只读连接 + 参数化 + 硬 LIMIT。

### 3.4 嵌入/向量库使用
- 正确性：vectorizer.py 用 sentence-transformers MiniLM（多语言）本地 CPU 嵌入、500 字/80 重叠分块、cosine 空间，参数合理；example_index.py 的语义指标检索用 0.26 距离阈值 + 3 近邻一致性裁决（example_index.py:166-180），防误匹配设计优秀；SQL 模式刻意跳过向量（chat.py:130、engine.py:343-346）符合产品设计。
- 问题：client 不 close（M6）；rebuild_semantic_example_index 全删重建无并发/失败保护（example_index.py:65-98）；重复 chunk id 边界（m4）；索引损坏时静默降级（m7）。

### 3.5 资源清理
- 好：neo4j_loader.py:226 与 rebuild_indexes.py:197 的 driver.close() 正确执行；运行时状态与会话文件均为原子替换。
- 不足：web/shared.py:19 与 graph_retriever.py:16-26 的模块级 driver 单例无关闭钩子（服务器场景可接受）；wiki_manager.py:1045 每流新建 AsyncOpenAI 不关闭；ChromaDB client 不关闭（M6）；ETL create_engine 从不 dispose（scheduler.py 常驻进程）。

### 3.6 旧 ETL 与新同步模块耦合
- 代码层零相互 import：grep 全仓证实 etl 仅被 run_etl_full.py、scripts/etl、scripts/check、scripts/maintenance/run_ddl.py、tests/test_queries.py 引用；graphstudio_sync 无任何 etl import；run_etl_full.py:4 与 src/etl/__init__.py:3 仅是文档注释提及对方。
- 残留耦合：scripts/check/*（check_camstar.py:1、check_tables.py:2、check_columns.py:2、check_views.py:2、demo_connection.py:6）与 scripts/maintenance/run_ddl.py:6 仍 import src.etl.config.db_config —— 辅助脚本对旧模块有依赖（不违反新核心模块约束，但建议后续迁移）。
- 共享数据面：etl 与 graphstudio_sync 都消费 docs/Database_Tables.csv、Database_Fields.csv（事实来源），这是数据共享而非代码耦合，符合 AGENTS.md。

### 3.7 死代码（实据）
- src/ontology/loader/neo4j_loader.py:19-114 load_ontology_to_neo4j() 从未被调用（__main__ 走 load_ontologies_to_neo4j），且功能被后者完全覆盖 —— 应删除或合并。
- src/ontology/explorer/ontology_explorer.py 整个模块（58 行 pyodbc 扫描）无任何 import（web/server.py:60 的 ontology_explorer 只是同名路由函数）。
- web/shared.py:22 _chat_sessions = {} 定义后从未读写（实际会话走 session_store.py 文件存储）。
- src/etl/extractor/、src/etl/loader/ 仅含空 __init__.py（目录结构占位）。
- src/qa/graph_retriever.py:464-527 get_shortest_path_details 仅被 scratch/test_reasonable_path.py 引用。
- src/ontology/validator/__init__.py、src/ontology/llm_prompts/__init__.py 为空文件。

### 3.8 硬编码
- src/qa/engine.py:414 默认模型 deepseek-v4-flash（与 wiki_manager 默认 deepseek-chat 不一致）。
- src/qa/vectorizer.py:20 与 semantic/example_index.py:21 嵌入模型名硬编码（建议 env 可覆盖）。
- src/etl/config/etl_config.py 全部 448 行静态 SQL/表名。
- src/graphstudio_sync/config.py:107-110 Graphmart URI 默认值、source_default_port（source_database.py:17-18）。
- src/qa/graph_retriever.py:23 默认 bolt://localhost:7687。

## 4. 新旧模块（etl vs graphstudio_sync）是否真的无相互依赖

结论：是——代码层完全解耦。证据：
1. 无任何 etl → graphstudio_sync 或 graphstudio_sync → etl 的 import（全仓 grep 结果）。
2. run_etl_full.py 文档字符串（第 3-4 行）和 src/etl/__init__.py（第 3 行）明确声明兼容保留、禁止新代码依赖，二者仅是注释层面的互提。
3. 唯一跨边界的共享是：辅助脚本（scripts/check、scripts/maintenance/run_ddl.py）import src.etl.config.db_config；以及两者都读取 docs/ 下同一份 CSV 事实来源。

但需要注意的边界情况：graphstudio_sync 并非完全自包含——publish_ontology.py:19 依赖 src.qa.sql_query_builder（→ src.ontology.wiki_manager）。这属于新核心模块对辅助模块的代码依赖（依赖方向为 graphstudio_sync → qa → ontology，不含 etl）。若项目对「新代码不得依赖旧 ETL」的理解是字面（不依赖 etl），则现状合规；若期望 graphstudio_sync 零辅助依赖，则该处需重构（将 build_query_builder_plan 下沉为共享层）。

## 5. 修复优先级建议

1. P0（立即）：S1 鉴权/绑定、S2 wiki 路径校验、S3 demo_connection 清库逻辑。
2. P1（本周）：M1 SQL 模式 Neo4j 降级、M3 ETL 水位线异常可见性、M5 索引模块下沉、S2 相关回归测试。
3. P2（本月）：M2/M6/M7 资源与生命周期、M4 upsert 标识符转义、M9/M10 依赖边界整理、死代码清理（neo4j_loader 首函数、explorer 模块、_chat_sessions、空包）。
4. P3（持续）：m2-m10 风格与健壮性条目、sql_validator 绕过样本测试、日志脱敏。
