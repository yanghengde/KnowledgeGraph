# Opcenter Graph Sync

Opcenter Graph Sync 是一个将 Siemens Opcenter Execution（Camstar）的本体与业务数据持续发布到 RapidMiner/Altair Graph Studio 的同步平台。

> 项目主线已统一为 **Camstar SQL Server/Oracle + Neo4j Ontology → RDF → Graph Studio Graphmart**。
> Neo4j 本体编辑、SQL 查询、Wiki、RAG 问答与旧 SQL Server ETL 仍保留，但它们是辅助工具，不再是平台主入口。

## 主流程

```text
Camstar SQL Server/Oracle ─┐
                      ├──> Mapping Compiler ──> RDF Snapshot ──> Graph Studio API
Neo4j Ontology      ─┘                  │                         │
                                           PostgreSQL Control Plane <── SPARQL Verify
```

- **Camstar SQL Server/Oracle**：可配置的业务数据唯一事实来源。
- **Neo4j**：本体类、属性、关系及 Camstar 物理映射。
- **PostgreSQL**：控制面，保存连接档案、菜单、任务、映射编译快照、运行日志、检查点和产物 URI。
- **Graph Studio**：最终本体、Dataset、Layer 和 Graphmart 服务。

当前发布适配基线为 **Graph Studio 2026.1.2 / REST API 6.3**。连接测试与正式发布优先读取
`/api/utils/serverVersion`。若该端点在部署入口中返回启动页或 404，则改用 REST API 6.3 核心读接口和已配置 FLDS
共享目录的只读浏览能力进行判定；任一检查失败时，系统会在任何 Graph Studio 写入前停止。

PostgreSQL 默认不镜像 Camstar 全量业务表，避免第二套业务 Schema 和双库一致性问题；
它只保存表级同步策略、分片台账、检查点和发布审计信息。

## 当前盘点

- 318 个 Neo4j 本体类，全部可匹配 Camstar 物理表。
- 4,483 个本体属性，4,451 个已解析物理列，覆盖率 99.29%。
- 796 条本体关系，其中 565 条已唯一解析物理外键，159 条存在多候选，72 条待显式映射。
- 当前已映射 Camstar 表约 632 行，稳态同步建议使用原子全量快照。

## 页面入口

- `/` 或 `/sync`：Camstar → Graph Studio 同步中心。
- `/ontology`：原本体可视化、SQL 助手、Wiki 和导入工作台。
- `/docs`：FastAPI OpenAPI 文档。
- `/healthz`：Neo4j 和 PostgreSQL 核心依赖健康检查。

同步中心菜单由 PostgreSQL `graphsync.menu_item` 管理，可在“系统设置 → 菜单配置”中修改显示名、排序和启用状态。

## 快速启动

### 1. 配置

```powershell
Copy-Item .env.example .env
```

至少配置：

```dotenv
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

SRC_DB_TYPE=sqlserver # 或 oracle
SRC_DB_HOST=...
SRC_DB_PORT=1433
SRC_DB_NAME=...
SRC_DB_USER=...
SRC_DB_PASSWORD=...
SRC_DB_SCHEMA=       # Oracle Schema；SQL Server 可留空
SRC_DB_ORACLE_MODE=service_name # 或 sid

GRAPHSTUDIO_BASE_URL=https://graphstudio.example.com
GRAPHSTUDIO_USER=...
GRAPHSTUDIO_PASSWORD=...
GRAPHSTUDIO_GRAPHMART_URI=http://cambridgesemantics.com/Graphmart/...
GRAPHSTUDIO_FILE_CONNECTION=http://cambridgesemantics.com/File_Connection/localShare

PGSQL_ENABLED=true
PGSQL_HOST=...
PGSQL_PORT=5432
PGSQL_DATABASE=OpcenterGraph
PGSQL_USER=postgres
PGSQL_PASSWORD=...
```

密码始终由环境变量管理。PostgreSQL `connection_profile` 只保存 `env://...` 引用，不存明文密码。Camstar 数据源支持 SQL Server 和 Oracle；管理页面切换类型后，连接测试、盘点和 RDF 预览会使用对应驱动。

### 2. 安装与初始化

```powershell
python -m pip install -r requirements.txt
python scripts/graphstudio_sync.py init-db
python scripts/graphstudio_sync.py compile-catalog
python scripts/graphstudio_sync.py doctor
python scripts/graphstudio_sync.py dry-run --job camstar-full
python scripts/graphstudio_sync.py preview --job camstar-full
python scripts/graphstudio_sync.py preview-curation --profile opcenter2607-core
python scripts/graphstudio_sync.py curation-cycle --profile opcenter2607-core
# 仅在全部契约/关系/质量门禁通过后才会物化和激活；否则返回失败且不写业务快照
python scripts/graphstudio_sync.py curation-cycle --profile opcenter2607-core --apply --actor scheduler
# 仅生成并激活治理数据版本，不发布 Graph Studio
python scripts/graphstudio_sync.py continuous-cycle --job camstar-full --profile opcenter2607-core --apply --actor scheduler
# 生产 CronJob 入口：冻结增量窗口 → 治理数据版本 → Graph Studio 蓝绿切换 → 验收 → 提交 checkpoint
python scripts/graphstudio_sync.py continuous-publish --job camstar-full --profile opcenter2607-core --environment dev --apply --actor scheduler
python scripts/graphstudio_sync.py materialize-curated --profile opcenter2607-core
python scripts/graphstudio_sync.py materialize-curated --profile opcenter2607-core --apply --activate --actor <user>
python scripts/graphstudio_sync.py release-status --profile opcenter2607-core
python scripts/graphstudio_sync.py rollback-curated --profile opcenter2607-core --actor <user>
python scripts/graphstudio_sync.py prepare-deployment --profile opcenter2607-core --environment dev --actor <user>
python scripts/graphstudio_sync.py deployment-status --profile opcenter2607-core
python scripts/graphstudio_sync.py health-check --profile opcenter2607-core
python scripts/graphstudio_sync.py health-status --profile opcenter2607-core
```

`init-db` 可创建目标 PostgreSQL 数据库和 `graphsync` Schema。已有连接档案默认不会被 `.env` 覆盖；只有显式传入 `--sync-connections` 才会重新同步环境变量中的连接元数据。

`preview` 会在 `outputs/graphstudio/previews/<run-id>/` 生成完整 OWL/Turtle 模型、分片 RDF ZIP、样本、manifest 和校验报告；它只读取 Camstar、Neo4j 与 PostgreSQL，不调用 Graph Studio 写接口。数据读取使用主键 keyset 分页，默认每批 10,000 行、RDF 分片目标 64 MiB，不会一次把整张大表读入内存。

### 3. 运行 Web 平台

```powershell
python -m uvicorn web.server:app --host 0.0.0.0 --port 5050
```

Docker Compose 会依次初始化 Neo4j 本体和 PostgreSQL 控制面：

```powershell
docker compose up -d --build
```

## 核心目录

```text
src/graphstudio_sync/
  config.py          环境配置
  database.py        PostgreSQL 初始化
  repository.py      控制面数据访问
  connections.py     脱敏连接档案与测试
  inventory.py       源库和本体盘点
  catalog.py         本体→物理列编译目录
  attribute_projection.py  通用关联属性投影
  run_manager.py     幂等锁和运行生命周期

web/routers/sync_center.py   同步管理 API
web/static/sync.*            同步中心界面
sql/graphstudio_sync_control_postgres.sql
deploy/graphstudio-sync/     PostgreSQL 和 CronJob 样例
```

## PostgreSQL 控制面

Schema：`graphsync`

| 分类 | 主要表 |
|---|---|
| 平台 | `schema_version`, `app_setting`, `menu_item`, `connection_profile` |
| 编排 | `sync_job`, `sync_scope`, `table_sync_policy`, `source_capability_snapshot`, `incremental_window`, `sync_run`, `sync_batch`, `checkpoint` |
| 映射 | `catalog_snapshot`, `class_mapping`, `property_mapping`, `relationship_mapping`, `mapping_override` |
| 业务图谱 | `graph_profile`, `profile_class`, `profile_relationship`, `context_validation`, `pending_reference` |
| 数据治理 | `data_contract`, `relationship_contract`, `curation_run`, `data_quality_result`；业务投影统一位于 `graphsync` schema |
| Schema 演进 | `data_contract_field`, `asset_dependency`, `schema_change_request`, `schema_change_item`, `schema_migration_run`, `source_schema_observation` |
| 属性投影 | `attribute_projection_contract`, `attribute_projection_field`, `attribute_projection_preview` |
| 治理版本 | `curated_release`, `curated_release_activation`, `materialization_batch`；业务快照位于 `graphsync.object_version/relationship_version` |
| 环境发布 | `deployment_environment`, `deployment_release` |
| 血缘与监控 | `runtime_lineage_event`, `health_check_run`, `health_metric`, `alert_rule`, `alert_event` |
| 业务动作 | `action_definition`, `action_invocation`, `action_event` |
| 审计 | `artifact`, `validation_result`, `row_state` |

DDL 是幂等的，可重复执行。映射目录使用不可变 `catalog_snapshot`，新编译失败不会破坏当前 `ready` 版本。

控制面 v6 还包含 `source_capability_snapshot` 和 `incremental_window`：前者记录 SQL Server CT/CDC 或 Oracle SCN/Flashback 的实际探测证据，后者在抽取前冻结可恢复的上下界。没有检查点、检查点已被源库清理或原生能力未启用时，窗口会进入 `baseline_required`/`blocked`，不会继续同步。

控制面 v7 增加业务图谱配置：完整本体仍可发布为模型层，实例层按核心/上下文/参考/按需对象和核心/上下文/弱关系构建受控闭包。初始草案以 `Product`、`MfgOrder` 为核心种子；关系必须来自实际映射目录并经过审核，弱关系不能驱动扩展。页面中的闭包预览不读取 Camstar 业务行，也不修改 Graph Studio。

控制面 v8 增加版本化数据契约。首批契约覆盖 Product、MfgOrder，并把 `ProductId → Product.ProductId`（订单目标产品）与 `BeginProductId → Product.ProductId`（订单起始产品）作为两条独立关系审核。`preview-curation` 只执行有上限的主键、业务键、必填字段、物理映射、增量水位和引用完整性检查；它仅在 PostgreSQL 记录聚合质量证据，不保存源行、不写治理业务表，也不写 Graph Studio。

控制面 v9 增加字段级 Schema 演进中心。每个治理字段使用稳定 `field_key` 管理来源、目标、类型、键角色、生命周期和本体属性；`asset_dependency` 显式记录它对 curated 列、关系、本体属性、Graph Studio 谓词及下游查询/API 的影响。新增、废弃、退役、重命名、改类型、改必填、改键、改来源和改转换都必须先生成兼容性分析，再经过复核和审批。有条件或破坏性变更必须提供迁移方案，破坏性变更还必须提供回滚方案。v9 只审批变更计划，不执行源库 DDL、不改 curated 业务表，也不发布 Graph Studio。

控制面 v10～v13 完成后续四个阶段：v10 使用主键 keyset 分批构建不可变治理版本，验证后原子切换活动指针；v11 管理 Dev/UAT/Prod 顺序晋级、不可变 RDF 制品、蓝绿槽位和 SPARQL 验收；v12 记录字段运行时血缘、健康指标及告警生命周期；v13 提供只走 Camstar API 的 Action Service，包含角色校验、双人审批、幂等键和审计事件。环境发布、Action 定义和全局 Action 开关均默认关闭，初始化数据库不会修改 Camstar 或 Graph Studio。

控制面 v14 增加通用属性投影：任何数据契约都可用“目标关联键 + 来源字段路径”从关联表补充属性，并可选配置声明式多跳 Join、过滤、排序及一对多策略。编译器只接受经过标识符校验的结构化配置，不接受原始 SQL；预览有严格行数上限，物化按主对象键分批查询，同时兼容 SQL Server 和 Oracle。规则修改后自动回到草案，必须经过成功源预览、复核和批准才进入治理版本。

控制面 v15 收敛为单库通用模型：`OpcenterGraph` 承载控制面与通用治理版本，业务实例只使用 `object_version` 和 `relationship_version`。早期 Product/MfgOrder 专属验证表及两条写死的 MfgOrder 演示 Action 已删除。Action 可手工配置或从本地 Camstar OpenAPI 选择性导入；导入项保持禁用草案，真实执行必须通过可信反向代理身份、不同人员复核/批准和全局执行开关。

控制面 v16 将 `object_version`、`relationship_version` 及其活动视图统一迁入 `graphsync`，删除 `camstar_curated` schema。Neo4j Enterprise 内新增独立 `graphstudio-model` database：原 `neo4j` database 保留完整 Camstar 源本体，发布库保存可裁剪、改名、补充属性并区分 published/projection/context 关系的目标本体。同步中心新增 G6 本体治理工作台；编辑后的草案必须通过校验、不同人员复核/批准、冻结和激活，RDF 构建才会同时读取活动本体版本与活动数据版本。

控制面 v17 将“持续数据”和“模型变化”拆成两条独立通道。稳定本体使用 `continuous-publish` 冻结增量窗口、生成不可变数据版本、蓝绿切换 Graph Studio Layer，并且仅在 SPARQL 验收成功后提交 checkpoint；失败会恢复上一活动层。字段新增、废弃、改名、改类型或改来源时，系统先保存 Camstar 物理 Schema 观测，再生成受控 Schema 变更。迁移后只按主键和受影响源列执行字段级回填，不因一列变化重扫和重写整张亿级表；发布记录同时绑定本体版本、数据契约版本、Schema 变更 ID 与源 Schema hash。

`preview-incremental` 会将已规划窗口读取成统一 JSONL 变更包，支持 SQL Server CT、CDC、Oracle Flashback SCN 以及 watermark/append-only。事件包含主键、insert/update/upsert/delete 操作和数据库恢复位置；预览只生成审计产物，不提交 checkpoint，也不写 Graph Studio。

“同步任务 → 表级同步策略”可为每个本体类配置全量快照、水位增量、追加增量、CDC 或不导入。超过 `sync.snapshot_row_threshold` 且没有显式策略的表会在抽取前失败，避免误扫亿级表。水位/追加策略必须配置水位列；每个已验证 RDF 分片会写入 `sync_batch`，便于审计和后续断点续跑。

## 同步安全边界

- `doctor`、`compile-catalog`、`dry-run` 都不会修改 Graph Studio。
- 发布命令必须使用 PostgreSQL advisory lock，并在 SPARQL 验收成功后才提交 checkpoint。
- Kubernetes CronJob 模板当前保持 `suspend: true`，完成全量发布 UAT 前不会定时修改 Graphmart。
- 共享 RDF ZIP 必须放在 Graph Studio 与 Graph Lakehouse 均可访问的 file connection。
- 属性投影默认禁止覆盖主契约同名字段；只有显式选择“覆盖”或“空值补齐”才允许。同一关联键返回多行时必须选择隔离、确定性排序取值或数组合并。
- 当前已完成流式基线和策略保护，但 SQL Server CT/CDC LSN、Oracle SCN、删除事件消费及自动断点恢复仍是下一阶段；连接器上线前，`watermark`、`append_only`、`cdc` 会明确阻止预览，绝不会退化为全表扫描。
- 当前环境实测 SQL Server Change Tracking、CDC 和 Snapshot Isolation 均未启用。DBA 可先运行只读检查 [sql/sqlserver_incremental_prerequisites.sql](sql/sqlserver_incremental_prerequisites.sql)；Oracle 对应检查见 [sql/oracle_incremental_prerequisites.sql](sql/oracle_incremental_prerequisites.sql)。脚本中的启用语句保持注释，不会自动修改源库。

详细架构和演进阈值见 [docs/graphstudio_sync_architecture.md](docs/graphstudio_sync_architecture.md)。

## 保留的辅助模块

| 目录 | 当前定位 |
|---|---|
| `src/ontology/` | Graph Studio 模型和物理映射的中间建模层 |
| `web/static/index.html` | `/ontology` 辅助工作台 |
| `src/qa/` | 可选 SQL/RAG 辅助能力 |
| `src/etl/` | 旧 SQL Server 中转 ETL，仅兼容保留，新同步流程不得依赖 |
| `run_etl_full.py` | 旧入口，不用于 Graph Studio 发布 |

在完成一个生产观察周期前，不物理删除这些模块。待确认无外部依赖后，再单独执行归档或删除。
