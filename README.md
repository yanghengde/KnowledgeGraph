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

PostgreSQL 默认不镜像 Camstar 全量业务表，避免第二套业务 Schema 和双库一致性问题。

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
```

`init-db` 可创建目标 PostgreSQL 数据库和 `graphsync` Schema。已有连接档案默认不会被 `.env` 覆盖；只有显式传入 `--sync-connections` 才会重新同步环境变量中的连接元数据。

`preview` 会在 `outputs/graphstudio/previews/<run-id>/` 生成完整 OWL/Turtle 模型、分片 RDF ZIP、样本、manifest 和校验报告；它只读取 Camstar、Neo4j 与 PostgreSQL，不调用 Graph Studio 写接口。

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
| 编排 | `sync_job`, `sync_scope`, `sync_run`, `checkpoint` |
| 映射 | `catalog_snapshot`, `class_mapping`, `property_mapping`, `relationship_mapping`, `mapping_override` |
| 审计 | `artifact`, `validation_result`, `row_state` |

DDL 是幂等的，可重复执行。映射目录使用不可变 `catalog_snapshot`，新编译失败不会破坏当前 `ready` 版本。

## 同步安全边界

- `doctor`、`compile-catalog`、`dry-run` 都不会修改 Graph Studio。
- 发布命令必须使用 PostgreSQL advisory lock，并在 SPARQL 验收成功后才提交 checkpoint。
- Kubernetes CronJob 模板当前保持 `suspend: true`，完成全量发布 UAT 前不会定时修改 Graphmart。
- 共享 RDF ZIP 必须放在 Graph Studio 与 Graph Lakehouse 均可访问的 file connection。

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
