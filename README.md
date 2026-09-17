# Opcenter Graph Sync

将 Camstar 物理结构和业务数据发布到 Graph Studio，使用 PostgreSQL 保存模型与发布治理状态。

```text
CSV 完整物理结构 → PostgreSQL 物理快照 → 来源与字段用途映射 → 本体候选 → 审阅与冻结模型
Camstar SQL Server / Oracle → 业务数据版本 → RDF → Graph Studio
                         PostgreSQL 保存审计、checkpoint 与回滚指针
```

## 启动

1. 复制 `.env.example` 为 `.env`，配置 PostgreSQL、Camstar 和 Graph Studio。密码仅保存在环境配置中。
2. 安装依赖：`python -m pip install -r requirements.txt`。
3. 在 `frontend/` 执行 `npm ci` 和 `npm run build`。
4. 执行 `python scripts/graphstudio_sync.py init-db` 初始化控制面（具体参数见 `--help`）。
5. 执行 `python -m uvicorn web.server:app --host 127.0.0.1 --port 5050`。
6. 打开 `/app/overview`。`/`、`/sync`、`/ontology`、`/chat` 会转到对应控制台页面。

容器启动与本地 PostgreSQL 配置见 [部署指南](docs/deployment.md)。

连接页面和实际连接使用同一组运行环境地址：Camstar 使用 `SRC_DB_HOST` / `SRC_DB_PORT`，Graph Studio 使用 `GRAPHSTUDIO_BASE_URL`，PostgreSQL 使用 `SYNC_STATE_DATABASE_URL` 或 `PGSQL_HOST` / `PGSQL_PORT`。数据库中的历史连接地址不覆盖这些值。显式进程环境变量优先于 `.env`；修改配置后需重启服务（容器环境需重新创建容器），再刷新页面并测试连接。业务数据库名、Graphmart 目标及其他可编辑参数仍由连接配置管理。

## 建模与发布

- 控制台保留 React 与现有组件库，使用列表、详情和分步审核组织任务；没有迁移至 SAPUI5 或 Fiori elements。
- 页头统一选择当前模型。首次只有一个启用模型时自动选中；多个模型需明确选择。已选模型失效时停止该模型页面操作，不自动改用另一个模型。对象编辑和操作提交期间禁止切换。
- 来源草稿跨模型复用；对象列表的发布状态按当前模型计算。问答与查询库继续使用服务器配置的已发布查询服务，页头不显示建模范围选择器。
- 页头的控制面状态来自 `/healthz`，只表示 PostgreSQL 控制面可达；Graph Studio 与 Camstar 状态以连接页面为准。
- 来源模型图的“选择字段”进入物理表目录；业务字段与关系使用同一确认流程。关系审阅显示 CSV 来源字段、目标字段与草稿选择状态，实例正确性仍需另行核实。


- 原始结构来自 `docs/Database_Tables.csv` 和 `docs/Database_Fields.csv`，这两个文件是只读事实源。
- `python scripts/graphstudio_sync.py import-csv-model --classes MfgOrder Product ProductBase` 预览候选；添加 `--apply` 保存候选。`--activate` 会替换源模型活动指针，仅在候选已经审阅且确认替换范围后使用。
- `/app/object-explorer` 是 Opcenter 数据模型：完整展示主键、系统字段与双向物理关联，自动打开 PostgreSQL 物理快照，使用关联图和表目录选择表用于建模。选表不直接创建本体类。
- `/app/ontology-model` 主界面提供业务对象、查看模型和检查发布；版本记录、来源比较与审阅收在“更多”菜单。对象列表保留搜索、状态筛选和编辑操作，已删除草稿可恢复。来源用途区分实体、事件、关系、辅助及暂不采用。
- 一表一实体映射支持业务属性、Navigation 业务关系、仅内部使用和不纳入字段；身份键保留，未评估字段阻止生成候选。明确选择的字段范围随候选和权威版本保存，来源合并不能恢复排除字段。
- 编辑对象时，系统按物理结构和保守的基础字段规则推荐选择，并显示理由；仅为尚未评估的字段填入建议，已有选择及排除决定不被覆盖。常用业务外键展示为建议关联，需手动勾选；技术字段和用途不明确的字段默认收起，可用“查看其他字段”或搜索全部字段补充。推荐仅保存到草稿，“检查这个对象”将未选字段明确为不纳入；确认后才加入待发布模型。规则集中在 `src/graphstudio_sync/modeling/field_recommendations.py`，不修改 CSV，也不自动批准或发布模型。
- 字段选择列表不分页，连续滚动查看。Designer 描述按物理表名与字段名匹配，优先显示 PostgreSQL 中保存的中文；缺少中文时先按英文原文复用已有翻译缓存，再使用已配置的翻译服务补全并保存。英文原文可展开查看；翻译不可用时回退英文并提示。缺失描述从 Designer 元数据读取。说明异步加载，连接失败不影响字段选择，可重试；搜索支持中英文描述。
- 事件拆分、关系表转换和多表组合目前可保存来源用途与设计说明，尚不执行实例转换，也不能通过此生成器直接生成实体候选。具体 History 行为需核实判别字段、身份、时间及撤销规则后再实现。
- `/app/data-sync` 管理源数据同步，`/app/publish` 执行模型与数据发布。
- `/app/assistant` 和 `/app/queries` 基于已发布的 Graph Studio 版本问答和查询。
- 发布必须先校验、幂等写入、验证成功后提交 checkpoint，并保留数据版本和回滚指针。
- Graph Studio HTTPS 检查：`python scripts/check/diagnose_graphstudio_https.py`。通过只表示传输可用，不代表认证和发布检查已完成。

详细操作见 [模型审阅指南](docs/ontology_authority_user_guide.md) 和 [HTTPS 发布说明](docs/graphstudio_https_publish.md)。

## 项目分区

根目录保留启动、部署、依赖配置与项目说明。开发代码、运维工具、测试和运行资产按以下边界存放：

| 目录 | 用途 |
| --- | --- |
| `src/graphstudio_sync/` | CSV 模型、PostgreSQL 存储、同步、RDF、发布与治理 |
| `src/ontology/` | 来源语义 JSON 与权威审阅规则 |
| `src/query/` | 已发布 Graph Studio 版本的问答与查询 |
| `src/planning/` | 物理 Schema 检索与 SQL 关系规划 |
| `src/graphstudio_sync/modeling/` | 物理模型、字段推荐、映射与候选确认 |
| `src/graphstudio_sync/storage/` | 按职责拆分的 PostgreSQL 持久化 |
| `src/graphstudio_sync/publishing/` | 数据版本、模型冻结与 Graph Studio 发布 |
| `web/schemas/` | API 请求校验契约 |
| `web/` | FastAPI 接口及图谱展示适配 |
| `frontend/` | 唯一 React 控制台 |
| `frontend/src/features/*/pages/` | 控制台业务页面与路由入口 |
| `frontend/src/components/layout/` | 应用布局与主题控件 |
| `frontend/src/features/modeling/components/` | 来源目录、模型工作区与图谱画布 |
| `frontend/src/features/publishing/components/` | 发布覆盖情况 |
| `frontend/src/features/sync/components/` | 数据同步配置控件 |
| `sql/` | 控制面及增量同步前置 SQL |
| `scripts/` | 模型导入 CLI 与 CSV 一致性校验入口 |
| `scripts/check/` | 只读 HTTPS 诊断工具 |
| `scripts/operations/` | 持续发布运维脚本（执行会发布数据） |
| `deploy/` | PostgreSQL Compose 与定时发布部署配置 |
| `docs/` | 操作指南与只读 CSV 事实源 |
| `data/` | 本地会话、查询、用户导入资料与备份 |
| `logs/` | 服务运行日志 |
| `outputs/graphstudio/` | 版本制品与发布审计，不能按临时文件清扫 |
| `tests/graphstudio_sync/` | 同步、发布、连接与运行控制测试 |
| `tests/ontology/` | 模型导入、审阅与 PostgreSQL 治理测试 |
| `tests/qa/` | 问答、查询能力与 SQL 规划测试 |

PostgreSQL 是唯一模型后端。项目不再包含旧图数据库驱动、旧中转 ETL、旧 Wiki/RAG、向量索引或历史页面。来源语义 JSON 仍用于候选比较，不等于已经批准发布的模型。

可选 Camstar API 动作的 OpenAPI 文档由用户放入 `data/openapi/`，不再捆绑静态 API 副本。

### 文件维护约定

- 新业务代码放入对应的 `src/` 模块，API 层不依赖 `scripts/` 中的命令行工具。
- 前端组件按业务用途归类；页面放在各自的 `features/<业务>/pages/`，业务组件放在同一分区的 `components/`，全局模型范围与主题放在 `app/`，构建结果只输出到 `web/static/react/`。
- 当前架构写在本文，操作步骤写在 `docs/` 现有指南；不提交一次性评审报告、调试脚本、制作依赖或重复构建产物。
- `src/ontology/semantic_references/*_ontology.json` 是有效的候选语义资料。CSV、用户数据、备份和 `outputs/graphstudio/` 中的版本制品及历史记录必须保留，不能作为缓存清理。
- 本地实验放在 `scratch/`，临时结果放在 `tmp/`；两者不进入版本控制。保留的演示交付文件不属于生产服务依赖。

## 验证

前端测试需要 Node.js 22.6+。执行 `python -m pytest tests -q` 和前端 `npm run test`、`npm run build`。真实 PostgreSQL 集成测试需显式设置 `RUN_MODEL_POSTGRES_TEST=1`、`RUN_AUTHORITY_POSTGRES_TEST=1`；测试使用独占临时 Schema。

可按分区运行测试，例如 `python -m pytest tests/ontology -q`。完整交付仍需执行全部后端测试与前端构建；真实远端发布须按操作指南验证。

## 当前重构进度与验收

- 已整理业务模块和前端业务分区，统一当前模型范围。继续沿用 React 与现有组件库。
- 对象检查显示关系增删与物理依据，保留已有关系的名称和治理设置，阻止指向被排除对象的关系确认。
- 关系业务确认单独保存含义、确认人、服务器时间及来源依据；修改对象定义或取消关系后确认失效。候选生成与对象确认共用审核门槛。
- 对象列表分别比较草稿与待发布模型、启用本体的来源版本；缺少追溯信息显示待核实。
- 后续以 MfgOrder 与 Product 的不同外键为验收场景，再完成隔离环境中的模型发布与回滚验证。实际业务含义由审阅确认，不能根据名称推断后自动批准。
