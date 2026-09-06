# 开发指南

## 产品主线

CSV 物理结构 → PostgreSQL 本体与治理 → Graph Studio；Camstar SQL Server/Oracle 提供业务实例数据。

- PostgreSQL 是唯一模型后端。用户已明确要求删除历史功能；不再恢复旧图数据库兼容实现、旧 ETL、Wiki/RAG 或重复页面。
- `src/graphstudio_sync/` 是核心业务模块；`frontend/` 是唯一控制台，`web/` 提供 API。
- `src/ontology/wiki_kb/*_ontology.json` 是仍用于候选比较的来源语义定义，不是待清理的历史文档。
- `src/qa/sql_query_builder.py` 和物理 Schema 工具服务于字段/关系规划，Graph Studio 问答服务于已发布模型。

## 数据约束

- 绝不修改 `docs/Database_Tables.csv` 和 `docs/Database_Fields.csv`，它们是物理表、字段和外键的唯一事实来源。
- 物理外键采用 Navigation 类型；字段名规范化与 `scripts/validate_ontology_vs_csv.py` 一致。
- CSV 导入默认产生候选，不得覆盖已有批准的业务语义。关系需审阅后进入发布工作区。
- 模型内容、release ID、URI、审计与回滚指针必须保持一致。
- 密码仅由环境配置提供，不写入 PostgreSQL、代码或日志。
- 发布必须幂等、防重叠、先验证后提交 checkpoint，保留可回滚的 Dataset 版本。
- `outputs/graphstudio/` 与数据库中的发布历史是运行资产，不作为普通缓存删除。

## 验证

- 运行 `python -m pytest tests -q`；前端改动运行 `npm run build`。
- PG 集成测试使用唯一临时 Schema，禁止用生产 Schema 做测试数据清理。
- 不保留一次性评审报告、调试脚本、制作依赖或重复构建产物。当前架构和操作说明集中在 README 与 docs 操作指南。
