# Camstar → Graph Studio 持续同步架构

## 结论

建议增加 PostgreSQL，但它应该是**同步控制面**，不是 Camstar 数据的全量中转仓库。
业务数据仍然从 Camstar SQL Server 读取，Neo4j 仍然是本体和映射的事实来源，
同步工具将两者编译为 RDF 批次，经共享文件区导入 Graph Studio。

不建议默认走 `SQL Server → PostgreSQL 全量镜像 → RDF`，因为这会引入第二套业务
Schema、双写一致性、更多存储和额外时延。只有当后续需要多源联表、长周期历史拉链、
数据质量修复或隔离 Camstar 负载时，才单独增加可选的 staging schema。

## 当前盘点

使用 `python scripts/graphstudio_sync.py plan` 对当前环境进行了只读盘点：

- Neo4j：318 个本体类、4,483 个属性、796 条本体关系。
- SQL Server：318/318 个本体类都能匹配物理表。
- 属性与物理列的可确定映射为 4,451/4,483（99.29%），剩余 32 个需要显式映射或确认为计算属性。
- 当前已映射的 318 张表中 70 张非空，总行数约 632。
- Graphmart `Opcenter2607` 在线，已发现 Graph Lakehouse 可访问的共享文件连接 `localShare`。

因此，当前阶段每小时生成一份完整 RDF 快照的成本很低，而且可以自然处理新增、
更新和删除。在数据规模或 SLA 明显增长前，不建议过早引入 CDC/Kafka。

## 目标架构

```mermaid
flowchart LR
    SQL["Camstar SQL Server<br/>业务数据"]
    NEO["Neo4j<br/>本体、属性、关系"]
    RUN["graphstudio-sync Runner<br/>映射编译、抽取、RDF 校验"]
    PG["PostgreSQL Control Plane<br/>任务、运行、检查点、产物"]
    SHARE["共享文件区<br/>不可变 RDF ZIP"]
    API["Graph Studio REST API<br/>模型、Dataset、Layer、Step"]
    GM["Opcenter2607 Graphmart"]
    VERIFY["SPARQL 验收<br/>计数、关系、完整性"]
    CRON["Kubernetes CronJob / systemd timer"]

    CRON --> RUN
    SQL --> RUN
    NEO --> RUN
    RUN <--> PG
    RUN --> SHARE
    SHARE --> API
    RUN --> API
    API --> GM
    GM --> VERIFY
    VERIFY -->|"成功后提交 checkpoint"| PG
```

### 各组件责任

| 组件 | 责任 | 不承担的责任 |
|---|---|---|
| SQL Server | Camstar 业务数据的唯一事实来源 | 不保存 Graph Studio 运行状态 |
| Neo4j | 本体类、属性、关系和物理映射 | 不复制 Camstar 全量数据 |
| PostgreSQL | 任务配置、run ledger、checkpoint、锁、artifact URI | 默认不存业务全表 |
| Runner | 生成映射清单、抽取、RDF 序列化、发布、验收 | 不长期持有调度循环 |
| CronJob | 定时触发、失败重试、禁止重叠 | 不决定 checkpoint |

## 每次同步的事务边界

1. 获取 PostgreSQL advisory lock，创建 `run` 记录。
2. 从 Neo4j 编译出确定的 manifest：类、物理表、主键、属性列、外键关系。
3. 计算 ontology hash 和 source schema hash；出现不明确映射时失败，不猜测。
4. 从 SQL Server 以一致性视图抽取，生成 Turtle/N-Triples 和 manifest。
5. 本地解析回读，并执行 SHACL/必填、URI 唯一性和引用完整性检查。
6. 生成不可变的 `run_id.zip`，上传到 Graph Studio 与 Graph Lakehouse 共享的文件连接。
7. 通过 API 创建新 Dataset，将现有 LoadDatasetStep 原子切换到新 catalog entry，然后 reload。
8. 用 SPARQL 检查类数、实例数、关系数和关键样本。
9. 只有第 8 步成功后才提交 checkpoint；失败时保留旧 Dataset/Step 和旧 checkpoint。
10. 按保留策略清理旧产物，默认保留最近 3 个成功版本和所有失败 manifest。

## 全量与增量策略

### 当前：原子全量快照

- 全部 318 个类使用稳定 URI：`namespace/class/primary-key`。
- 每次生成完整快照，并用 Dataset 版本切换；删除语义不需要 tombstone。
- 可先按领域分层，但一次 run 只有在所有层验收成功后才算成功。

### 触发升级到增量的条件

任一条连续出现时再升级：快照超过 5 GB、单次超过 30 分钟、源库压力不可接受，
或业务要求 5 分钟内可见。升级路径是：

- 优先使用 SQL Server Change Tracking/CDC，没有 CDC 的低频表才使用 watermark + row hash。
- 按领域和变化率分区：配置/建模数据低频，WIP/历史数据高频。
- 增量批次和周期性全量 reconciliation 并存，避免长期漂移。
- 若要求秒级，使用 CDC 事件流/Kafka，不再使用 cron 作数据通道。

## 调度和运维

- Kubernetes 环境优先 CronJob，设置 `concurrencyPolicy: Forbid`；非 K8s 使用 systemd timer 或 Windows Task Scheduler。
- Runner 仍需要 PostgreSQL advisory lock，因为调度器重试和手工触发仍可能重叠。
- 密码放入 Kubernetes Secret/Vault，生产不使用镜像内 `.env`。
- 输出结构化日志和 metrics：run 时长、源行数、RDF 三元组数、失败阶段、数据新鲜度。
- 告警条件：连续失败、超过 SLA 未成功、行数异常变化、本体/Schema hash 未审批变更。

## 工具边界和路线图

### 已落地

- `doctor`：只读检查 Neo4j、SQL Server、Graph Studio 和 PostgreSQL 连通性。
- `plan`：输出类/表覆盖、属性映射率、行数估算和推荐模式。
- PostgreSQL 控制面 DDL，本地 Compose 和暂停状态的 Kubernetes CronJob 模板。
- Product/MfgOrder 子图的 RDF 导出和 API 导入已作为端到端概念验证。

### 下一个实现里程碑

1. 将 32 个未确定属性放入显式 mapping override，并为每个关系保存 sourceFieldId。
2. 实现全量 manifest compiler 和分片 RDF writer，避免一次将大数据全部放入内存。
3. 实现幂等的 `sync --job camstar-full --apply`，包含蓝绿 Dataset 切换、SPARQL 验收和回滚。
4. 通过 UAT 后取消 CronJob 模板的 `suspend: true`。
5. 运行一个观察周期，再依据实测时间和体积决定是否增加 CDC。

## 命令

```powershell
python scripts/graphstudio_sync.py doctor --output outputs/graphstudio/sync_doctor.json
python scripts/graphstudio_sync.py plan --output outputs/graphstudio/full_sync_plan.json

# 启动可选 PostgreSQL 控制面
$env:GRAPHSYNC_POSTGRES_PASSWORD = '<secret>'
docker compose -f deploy/graphstudio-sync/compose.postgres.yaml up -d
```

Kubernetes 调度模板现在故意处于暂停状态，避免在全量 `sync` 命令完成前误调度。
