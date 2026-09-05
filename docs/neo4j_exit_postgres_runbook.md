# Neo4j 逐步退出：PostgreSQL 模型主链路

## 本次已完成

- 增加 `ONTOLOGY_BACKEND=postgres|neo4j`。未设置时保留旧环境行为；新 `.env.example` 使用 postgres。
- PostgreSQL 保存源模型快照、源模型活动指针、工作区文档和不可变发布模型文档。沿用 `graphsync` 和现有 release 元数据。
- 目录编译、预览说明、实例物化/发布读取、G6 源图/详情、发布编辑与关系建议支持 PostgreSQL。
- 工作区编辑与 revision 原子提交；冻结模型与 release 元数据原子提交；活动版本读取验证内容哈希。未迁移模型报错，绝不回退读取 Neo4j。
- 已迁移当前环境的 318 类、4,483 属性、796 关系、1 个工作区、5 个历史模型版本。保留原 ID、内容、活动/回滚指针及 Neo4j 数据。
- 已实际将 MfgOrder/Product/ProductBase 的 CSV 模型导入 PG 为非活动候选：3 类、224 属性、5 关系。现有语义未被 CSV 骨架覆盖。
- 当前活动数据版本的 RDF 等价检查通过：模型 2,304 三元组，实例 852 三元组，发布对象 26、关系 17。两个后端的命名模型图及实例图内容相同。
- 本地 `.env` 已切为 `ONTOLOGY_BACKEND=postgres`，5050 服务已重启并核实返回 backend=postgres。健康、页面、模型及同步/发布状态共 10 个在线检查通过，活动模型 release ID 未变化。

CSV 只描述物理结构；真实实例仍来自 Camstar。PostgreSQL 源模型可保留导入并审阅后的 JSON 业务语义。移除 Neo4j 不移除本体治理、数据契约或发布验收。

## 已有环境的切换

1. 暂停模型编辑，保留数据库备份。切换期间不要并行使用两个后端编辑同一模型。
2. 预览：`python scripts/graphstudio_sync.py migrate-ontology --output outputs/graphstudio/neo4j_exit_migration_preview.json`。
3. 复制：`python scripts/graphstudio_sync.py migrate-ontology --apply --output outputs/graphstudio/neo4j_exit_migration_applied.json`。该命令仅添加 PG 模型内容；不删除 Neo4j、不发布 Graph Studio、不推进业务发布 checkpoint。重复执行时拒绝覆盖已产生差异的 PG 模型。
4. 核验：`python scripts/graphstudio_sync.py model-store-status`。须满足 ready=true，缺失工作区/历史版本/损坏版本均为 0。
5. 将运行环境设为 `ONTOLOGY_BACKEND=postgres`，重启 Web 与同步 worker。已有进程不会因为代码和配置已修改就自动完成切换；必须核验 `/api/sync/ontology-governance` 返回 backend=postgres。
6. 验证 `/healthz`、模型目录、图谱详情、工作区和数据同步状态；再按既有发布流程生成/发布业务版本。不要将“模型迁移成功”显示为“新 Graph Studio 发布成功”。

迁移期间旧 Neo4j 编辑进程必须退出或保持只读。复制后 PG 编辑发生变化时，不能直接把后端改回 neo4j 后继续发布；应先暂停发布并处理差异。迁移工具不做隐式双写。

## 新环境：CSV → PostgreSQL → Graph Studio

```powershell
$env:ONTOLOGY_BACKEND = 'postgres'
python scripts/graphstudio_sync.py init-db
python scripts/graphstudio_sync.py import-csv-model --classes MfgOrder Product ProductBase
# 仅新模型初始化时激活；已有模型建议只 --apply 保存候选，先审阅差异。
python scripts/graphstudio_sync.py import-csv-model --classes MfgOrder Product ProductBase --apply --activate
python scripts/graphstudio_sync.py compile-catalog
python scripts/graphstudio_sync.py model-store-status
python -m uvicorn web.server:app --host 0.0.0.0 --port 5050
```

不提供 `--classes` 时导入全部 CSV 类。CSV 导入结果记录源文件 SHA-256、物理字段 ID 和精确外键；不改两份源 CSV。主键/外键名称按现有规范处理，ProductId 与 BeginProductId 不因同指向 Product 而合并。

目录中审阅业务定义并同步到 PG，选择发布对象和字段后，继续现有的模型冻结/激活、契约、数据质量、数据版本与 Graph Studio 发布流程。第一阶段保留工程契约配置；后续再用统一发布计划生成这些草案。

旧 `compose.yaml` 保留原部署方式。新主链路可用 `docker compose -f compose.postgres-model.yaml up -d --build`，仅启动 Web，使用 `.env` 配置的 PG/Camstar/Graph Studio。先初始化/迁移模型存储；该部署不会自动改写现有模型或发布资产，也不要求 Neo4j 服务启动。

## 验证记录

- 新 PostgreSQL 模型测试使用独占的随机测试 Schema；覆盖幂等源快照、关系发现/应用/撤销、编辑回滚、冻结与活动版本、冻结后编辑不改变旧版本、无 Neo4j 隐式回退。
- 109 项模型/发布/配置/权威目录相关测试通过（包含实际 PostgreSQL 集成测试）。
- 全量测试：277 通过、2 跳过、2 失败。两个失败为既有 `test_relationship_sql.py` 校验；已将 HEAD 的原始文件归档到临时目录复跑，基线同样失败。
- 前端 `npm run build` 通过。
- 在禁止 `GraphDatabase.driver` 创建的进程中，健康、图概览、统计、Product 详情、本体目录、发布治理、数据同步共 7 个 API 返回 200。
- RDF 等价产物位于 `outputs/graphstudio/neo4j_exit_equivalence/`，独立输出目录，没有覆盖既有部署制品。测试未调用 Graph Studio 写接口。

## 后续观察与退出

### 第二阶段实际验证（2026-09-05）

- 全程禁止创建 Neo4j 驱动，使用 PostgreSQL 模型后端运行真实 Camstar 数据同步；生成治理版本 R19（`e6749e0f-22b9-4847-a3c7-f6a29db33d9a`）。
- 当前六类对象使用已批准的小表快照策略；没有待处理增量事件。本轮验证的是实际快照刷新，不是 CT/CDC 增量验收，也未人为修改 Camstar 数据。
- 为 Dev 准备部署 `7c2c7a78-665c-4842-a017-c8bc4d3701df`，模型版本仍为 R5；制品为 26 个发布对象、17 条关系，模型 2,304 三元组、实例 852 三元组。
- 发布在 `https://gs.siemens-icx.com.cn:8443/api/utils/serverVersion` 的 TLS 握手阶段收到 `UNEXPECTED_EOF_WHILE_READING`。默认网络与禁用环境代理直连均失败。未绕过 TLS 校验或修改证书指纹。
- 此失败发生在任何 Graph Studio 写入前，发布 checkpoint 保持不变。新增发布前异常记录：`stage=graphstudio_preflight`、`retryable=true`、`remoteMutated=false`，状态为 failed。
- 实际执行 PostgreSQL 数据回滚并验证成功，活动数据恢复为 `b2bc8201-5ea3-4b96-9254-ec120cea41b5`；R19 保留为 rolled_back，不删除制品和历史证据。
- 新增两项发布前检查测试，连同 inline 发布及平台测试共 78 项通过。
- 详细记录：`outputs/graphstudio/postgres_phase2_acceptance.json`。

继续验收前先恢复 Graph Studio HTTPS 入口，再重新运行数据同步生成经验证的新版本并走 Dev 发布流程。不要直接将 rolled_back 数据版本改为 active 来绕过校验。UAT/Prod 开关未改变。成功发布与真实增量验收仍未完成，不据此退役 Neo4j。

### HTTPS 复查与服务状态（2026-09-05）

- 用户确认 Graph Studio 服务已关机，当前发布验收等待服务启动；不再据 TLS EOF 推断应用代码或证书配置错误。
- 本机 DNS 经 Meta 隧道返回 `198.18.1.121`，公共 DNS 返回 `8.163.40.82`。本机域名、真实地址保留 SNI、显式本机代理路径均出现 TLS EOF；这些探测无法独立区分服务状态与中间网络影响。
- 新增只读诊断命令：`python scripts/check/diagnose_graphstudio_https.py --output outputs/graphstudio/https_diagnostics.json`。不连接 PG/Neo4j、不发送账号密码、不跟随重定向，沿用配置的证书指纹或系统 CA 校验。报告分开记录 DNS、TCP、HTTPS；忽略环境代理及 netrc，但仍受操作系统 VPN 路由影响。
- 最新诊断为 TCP 可连接、HTTPS 握手失败。TCP 可连接不能作为 Graph Studio 已启动的依据。退出码 0 仅表示 HTTPS 已通过校验（可能返回 401），不等于认证或发布就绪。
- 服务启动后先重跑上述命令，再执行原有认证与版本检查、生成新数据版本并发布到 Dev。当前没有新增数据版本或发布尝试，前一阶段回滚结果保持不变。
- 诊断及发布前异常测试共 6 项通过。详细网络报告见 `outputs/graphstudio/https_diagnostics.json`。

第一阶段完成模型存储替换与历史迁移；第二阶段观察至少一个真实业务更新、一次受控发布与一次回滚；第三阶段经用户确认后退役 Neo4j 服务及旧代码。

仍保留的旧 Wiki/RAG/Cypher 专家路径可能依赖 Neo4j，在 PG 模式调用会明确报错，不能把它们视为已迁移。主链路 G6、目录、发布和数据同步已支持 PG。`neo4j` Python 包及旧模块暂不删除。

不要在完成观察前删除原模型图、历史数据、旧 compose 或旧 loader。也不要把 CSV 新骨架直接替换已经审核、已发布的语义模型。
