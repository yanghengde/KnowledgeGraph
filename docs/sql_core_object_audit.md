# SQL 核心业务对象本体覆盖审计

## 审计范围

- 事实来源：`docs/Database_Tables.csv`、`docs/Database_Fields.csv`
- 审计前物理表：1555
- 审计前本体类：510
- 审计前仅存在于物理层的表：1045
- 直接通过物理外键关联 `HistoryMainline`、但尚未建模的表：142

物理层包含大量运行时子表、集成表、排程临时表和半导体专用明细表。
本次没有把所有物理表直接提升为图谱顶级节点，而是按以下条件筛选：

1. 已被 SQL 助手的领域提示或生成结果使用；
2. 是开工、移动、产出、数量、拆分合并、Hold/Release 或资源状态查询的事实表；
3. 与 `HistoryMainline`、`Container`、`MfgOrder`、`Product`、`ResourceDef`
   等核心对象存在明确物理外键；
4. 具有独立业务查询价值，而非纯技术中间表。

## 本次新增对象

### A 级：SQL 助手已经使用或明确引用

| 物理表 / 本体类 | 中文名 | 非系统属性数 | 主要用途 |
|---|---|---:|---|
| `MoveHistory` | 移动历史 | 49 | Move/过站起止步骤、工序、路径和数量 |
| `MoveInHistory` | 移入历史 | 18 | Move In 产品、位置、数量和设置 |
| `A_TrackInLotHistory` | 批次进站历史 | 11 | 半导体批次 Track In |
| `A_TrackOutLotHistory` | 批次出站历史 | 11 | 半导体批次 Track Out |
| `ThruputHistory` | 产出历史 | 19 | 容器级产出事实 |
| `ThruputHistoryDetail` | 产出历史明细 | 13 | 产出按容器、产品、工序拆分 |
| `ResourceThruputHistory` | 资源产出历史 | 13 | 设备、资源和工单产出统计 |
| `ResourceThruputHistoryDetails` | 资源产出历史明细 | 4 | 资源产出附属明细 |

### B 级：生产生命周期核心事实

| 物理表 / 本体类 | 中文名 | 非系统属性数 | 主要用途 |
|---|---|---:|---|
| `StartHistoryDetail` | 开工历史明细 | 89 | 开工时工单、产品、批次、资源和工艺快照 |
| `QtyHistory` | 数量变更历史 | 15 | 数量调整事务主记录 |
| `QtyHistoryDetails` | 数量变更历史明细 | 28 | 数量调整的容器、产品和工序明细 |
| `SplitHistory` | 拆分历史 | 24 | 批次/容器拆分事务 |
| `SplitHistoryDetails` | 拆分历史明细 | 42 | 拆分目标容器和数量明细 |
| `CombineHistory` | 合并历史 | 19 | 批次/容器合并事务 |
| `CombineHistoryDetail` | 合并历史明细 | 25 | 合并源容器和数量明细 |
| `HoldReleaseHistory` | 暂停与释放历史 | 19 | Hold/Release 原因和位置 |
| `HoldReleaseHistoryDetail` | 暂停与释放历史明细 | 9 | Hold/Release 影响的容器 |
| `ResourceStatusHistory` | 资源状态历史 | 47 | 设备状态、原因、位置和预留变化 |

本次共新增 18 个物理同名本体类、455 个非系统属性和 132 条物理外键关系。

## 暂不提升为核心节点的对象

- `A_WIP*`、`A_Lot*` 等专用运行时子表：数量多，需按具体半导体业务场景分批审核。
- 排程、扫描、集成和打印历史：属于独立业务域，不应混入通用生产事务核心层。
- `*Details`、`*RI`、映射和列表表：只有在能解释主表查询粒度时才建模。
- UI、权限、消息和集成基础设施：继续保留在物理 CSV，不进入 SQL 业务关系图。

## Swagger 对齐情况

本批 18 个运行时历史对象在当前 `src/Swagger` 文件中没有可强匹配的
`<ClassName>Entity` 或 `<ClassName>` Schema，因此无法从 Swagger 获取可靠字段说明。
类中文名和业务用途已完成审核；属性名、类型和外键严格来自物理 CSV。
对 Swagger 未覆盖的字段不推测枚举值或业务含义。

## 校验结果

- 审计后本体类：528
- 物理同名精确匹配：528
- 缺失物理属性：0
- 属性类型错误：0
- 缺失物理外键关系：0
- 无效关系端点：0
- 重复类、属性或关系：0

