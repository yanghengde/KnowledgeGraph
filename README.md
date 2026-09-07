# Opcenter Graph Sync

将 Camstar 物理结构和业务数据发布到 Graph Studio，使用 PostgreSQL 保存模型与发布治理状态。

```text
CSV 物理结构 → PostgreSQL 本体候选 → 审阅与冻结模型
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

## 建模与发布

- 原始结构来自 `docs/Database_Tables.csv` 和 `docs/Database_Fields.csv`，这两个文件是只读事实源。
- `python scripts/graphstudio_sync.py import-csv-model --classes MfgOrder Product ProductBase` 预览候选；添加 `--apply` 保存候选。`--activate` 会替换源模型活动指针，仅在候选已经审阅且确认替换范围后使用。
- `/app/ontology-model` 提供来源目录、CSV/文档抽取、字段与关系审阅、发布工作区和版本管理。
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
| `src/qa/` | Graph Studio 问答、查询与物理关系规划 |
| `web/` | FastAPI 接口及图谱展示适配 |
| `frontend/` | 唯一 React 控制台 |
| `frontend/src/pages/` | 控制台业务页面与路由入口 |
| `frontend/src/components/layout/` | 应用布局与主题控件 |
| `frontend/src/components/ontology/` | 来源目录、模型工作区与图谱画布 |
| `frontend/src/components/publish/` | 发布覆盖情况 |
| `frontend/src/components/sync/` | 数据同步配置控件 |
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
- 前端组件按业务用途归类；页面统一放在 `pages/`，构建结果只输出到 `web/static/react/`。
- 当前架构写在本文，操作步骤写在 `docs/` 现有指南；不提交一次性评审报告、调试脚本、制作依赖或重复构建产物。
- `src/ontology/wiki_kb/*_ontology.json` 是有效的候选语义资料。CSV、用户数据、备份和 `outputs/graphstudio/` 中的版本制品及历史记录必须保留，不能作为缓存清理。
- 本地实验放在 `scratch/`，临时结果放在 `tmp/`；两者不进入版本控制。保留的演示交付文件不属于生产服务依赖。

## 验证

执行 `python -m pytest tests -q` 和前端 `npm run build`。真实 PostgreSQL 集成测试需显式设置 `RUN_MODEL_POSTGRES_TEST=1`、`RUN_AUTHORITY_POSTGRES_TEST=1`；测试使用独占临时 Schema。

可按分区运行测试，例如 `python -m pytest tests/ontology -q`。完整交付仍需执行全部后端测试与前端构建；真实远端发布须按操作指南验证。
