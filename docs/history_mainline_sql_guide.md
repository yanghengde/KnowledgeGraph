# HistoryMainline SQL 查询指南

## 定位

`HistoryMainline` 是 Camstar WIP 交易历史的主线表，保存容器、产品、工艺位置、资源、人员、
交易时间、数量和交易服务等公共上下文。它适合构建容器事务时间线，但不能等同于“所有 Move
详情和产出都只在这一张表”。

| 查询目的 | 主表/明细表 | 连接依据 |
|---|---|---|
| 容器完整交易时间线 | `HistoryMainline` | 按 `ContainerId` 或 `ContainerName` 过滤 |
| 过站、前后 Spec/Step、路径 | `MoveHistory` | `MoveHistory.HistoryMainlineId = HistoryMainline.HistoryMainlineId` |
| Move-In 信息 | `MoveInHistory` | `MoveInHistory.HistoryMainlineId = HistoryMainline.HistoryMainlineId` |
| 半导体 Track In | `A_TrackInLotHistory` | `A_TrackInLotHistory.HistoryMainlineId = HistoryMainline.HistoryMainlineId` |
| 半导体 Track Out | `A_TrackOutLotHistory` | `A_TrackOutLotHistory.HistoryMainlineId = HistoryMainline.HistoryMainlineId` |
| 容器/工序产出 | `ThruputHistory` | `ThruputHistory.HistoryMainlineId = HistoryMainline.HistoryMainlineId` |
| 产出明细容器 | `ThruputHistoryDetail` | `ThruputHistoryDetail.ThruputHistoryId = ThruputHistory.ThruputHistoryId` |
| 资源级产出 | `ResourceThruputHistory` | `ResourceThruputHistory.HistoryMainlineId = HistoryMainline.HistoryMainlineId` |
| 当前 WIP 状态 | `Container` | 当前快照，不代替历史表 |

上述表名、字段名及外键均来自 `Database_Tables.csv` 和 `Database_Fields.csv`。

## SQL 助手的选表规则

当聊天上下文包含 `HistoryMainline` 时，助手根据问题自动补充物理表：

- “Move、过站、工艺流转、轨迹”：补充 `MoveHistory`、`MoveInHistory`。
- “Track In、Track Out、进站、出站、上机、下机”：补充半导体 Track 历史表。
- “产出、产量、Throughput、良率”：补充 Throughput 主表、明细表和资源级表。
- 泛问 `HistoryMainline`：加载一组精简的核心伴随表，帮助先确认查询口径。

这些历史明细表不需要全部显示成图节点，因此不会增加知识图谱的视觉复杂度。

## 写 SQL 前必须确认的口径

1. **时间列**：`TxnDate`/`TxnDateGMT` 是交易时间候选，`SystemDate`/`SystemDateGMT`
   是系统记录时间候选。最终含义、工厂时区和报表日切规则需要现场确认。
2. **交易类型**：物理 CSV 没有给出 `TxnType`、`BaseTxnType`、`CompoundTxnType`
   的枚举映射。获取权威映射前，不应猜数值；可先使用 `TxnServiceName` 和对应子历史表确认。
3. **产量**：不要用 `COUNT(HistoryMainlineId)` 代替产量。产量应根据业务粒度聚合
   `ThruputHistory.Qty`/`Qty2`，并明确 UOM。
4. **撤销和重复**：需要定义 Reversal、复合事务、拆分/合并、返工、批次子容器的处理规则。
5. **粒度**：必须说明需要“交易次数、过站次数、批次数、主容器数、子容器数还是产出数量”。

## 建议补充的现场资料

为了让 SQL 助手从“字段正确”提升到“业务口径正确”，建议按优先级提供：

1. `TxnType`、`BaseTxnType`、`CompoundTxnType`、`ReversalStatus` 的现场枚举和值说明。
2. 3–5 个真实但脱敏的生命周期样本：Start → Track In → Track Out/Move → Hold/Rework → Close。
3. 现有生产日报、过站报表、WIP 报表的 SQL 和字段口径。
4. 工厂时区、班次切日、产出归属日期、主/副 UOM 规则。
5. Split、Combine、Rework、Reversal 时如何计数和去重的业务规则。
6. DBA 提供的现有索引清单与典型慢 SQL 执行计划。不要未经厂商和 DBA 审核直接修改 MES 生产库索引。
