# SQL核心生产事务历史建模 / SQL Core Manufacturing Transaction History Modeling

## 中文

本批次覆盖SQL查询最常使用的生产事务事实表：开工、移动、进出站、产出、数量变更、拆分合并、Hold/Release以及资源状态历史。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `StartHistoryDetail`（开工历史明细）：记录容器开工时的工单、产品、数量、工艺步骤、资源和批次快照。
- `MoveHistory`（移动历史）：记录容器移动和过站事务的起止工序、步骤、路径、资源及数量信息。
- `MoveInHistory`（移入历史）：记录容器移入工艺步骤时的产品、数量、位置、设置和所有者信息。
- `A_TrackInLotHistory`（批次进站历史）：记录半导体批次Track In事务的设备端口、人员及数量信息。
- `A_TrackOutLotHistory`（批次出站历史）：记录半导体批次Track Out事务的处理数量和执行结果信息。
- `ThruputHistory`（产出历史）：记录容器级产出事务的数量、产品、工序、资源和计量单位。
- `ThruputHistoryDetail`（产出历史明细）：记录产出事务按容器、产品、工序和资源拆分的明细数量。
- `ResourceThruputHistory`（资源产出历史）：记录资源和制造工单维度的产出数量，是设备及工单产量统计的核心事实表。
- `ResourceThruputHistoryDetails`（资源产出历史明细）：记录资源产出事务关联的明细数据。
- `QtyHistory`（数量变更历史）：记录容器数量调整、批次汇总、载具及原因等数量事务主记录。
- `QtyHistoryDetails`（数量变更历史明细）：记录数量事务按容器、产品、工序和计量单位拆分的明细。
- `SplitHistory`（拆分历史）：记录从源容器拆分新容器的事务主记录。
- `SplitHistoryDetails`（拆分历史明细）：记录拆分目标容器、数量、库存工艺步骤及相关明细。
- `CombineHistory`（合并历史）：记录容器合并事务的目标容器、配方和设备信息。
- `CombineHistoryDetail`（合并历史明细）：记录参与合并的源容器和数量明细。
- `HoldReleaseHistory`（暂停与释放历史）：记录容器Hold与Release事务的原因、位置和主历史关联。
- `HoldReleaseHistoryDetail`（暂停与释放历史明细）：记录Hold或Release事务影响的容器明细。
- `ResourceStatusHistory`（资源状态历史）：记录设备资源状态、原因、位置、产品、设置和预留信息的变化历史。

## English

This batch covers the manufacturing transaction fact tables most frequently required by SQL queries: start, move, track-in/out, throughput, quantity changes, split/combine, hold/release, and resource status history.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
