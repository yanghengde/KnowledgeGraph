# 本体图谱游离类审计报告

本报告只依据当前本体 JSON 与 `Database_Fields.csv` 的物理外键事实。
Neo4j 已通过 JSON 一致性校验，因此这里的游离点不是加载失败，而是本体源关系缺失。

## 汇总

- 本体类：567
- 本体关系：1507
- 游离类：25（4.4%）

| 分类 | 数量 | 解释 |
|---|---:|---|
| `A0_direct_physical_fk_missing` | 0 | 存在当前类之间的直接物理FK，但本体未建关系 |
| `A1_bridge_to_connected_graph` | 0 | 经未建模桥接/历史表可连接主图 |
| `B_bridge_only_isolated` | 0 | 桥接表目前只连到其他游离类 |
| `C_unmodeled_reference_only` | 11 | 只有未建模引用表，尚未形成通往主图的事实路径 |
| `D_no_business_fk_evidence` | 14 | 没有可确认的业务外键证据 |

## 重点对象

### IssueReason

- 当前状态：已连接。
- 物理事实：`IssueActualsHistory.IssueReasonId → IssueReason.IssueReasonId`。
- `IssueActualsHistory` 同时关联 `Product`、`Container`、`ResourceDef`、`Location`、`SubstitutionReason`、`IssueDifferenceReason` 等对象。
- 修复路径：已建模 `IssueActualsHistory`，保留真实中间事实表。

### ChangeStatusReason

- 当前状态：已连接。
- 物理事实：`ContainerStatusChangeHistory.ChangeStatusReasonId → ChangeStatusReason.ChangeStatusReasonId`。
- `ContainerStatusChangeHistory.HistoryMainlineId → HistoryMainline.HistoryMainlineId`，可继续关联容器事务主线。
- 修复路径：已建模 `ContainerStatusChangeHistory`，并连接 `HistoryMainline`。

## 分组明细

### A0_direct_physical_fk_missing

存在当前类之间的直接物理FK，但本体未建关系。

| 类 | 中文名 | 模块 | 物理证据 |
|---|---|---|---|
| — | — | — | — |

### A1_bridge_to_connected_graph

经未建模桥接/历史表可连接主图。

| 类 | 中文名 | 模块 | 物理证据 |
|---|---|---|---|
| — | — | — | — |

### B_bridge_only_isolated

桥接表目前只连到其他游离类。

| 类 | 中文名 | 模块 | 物理证据 |
|---|---|---|---|
| — | — | — | — |

### C_unmodeled_reference_only

只有未建模引用表，尚未形成通往主图的事实路径。

| 类 | 中文名 | 模块 | 物理证据 |
|---|---|---|---|
| `A_SortIQCLotCheck` | IQC批次检查 | `semiconductor_quality_iqc` | `A_LotSortIQCFailures` |
| `A_SortIQCWaferCheck` | IQC晶圆检查 | `semiconductor_quality_iqc` | `A_LotSortIQCWafersFailures` |
| `A_SortSQAFailure` | SQA失败配置 | `semiconductor_quality_iqc` | `A_LotSortSQAWafersFailures` |
| `ContainerGroup` | 容器组 | `container` | `ContainerGroupEntries`, `ContainerGroupGroups`, `ContainerGrpDftForObjTypes` |
| `RevisionedObjectGroup` | 版本对象组 | `semiconductor_security_kpi_configuration` | `RevisionedObjectGroupEntries`, `RevisionedObjectGroupGroups` |
| `ShippingReason` | 出货原因 | `shipping_reason` | `WIPMsgDefMgr` |
| `WhereUsedConfig` | 使用位置配置 | `semiconductor_user_job_spc_configuration` | `WhereUsedConfigDetail`, `WhereUsedConfigWhereUsedConfig` |
| `scsBinCode` | Bin代码 | `semiconductor_bin_overlay` | `scsBinCodeMap` |
| `scsBinDefinition` | Bin定义 | `semiconductor_bin_overlay` | `scsBinCodeMap` |
| `scsMapData` | 半导体Map数据 | `semiconductor_shipping_integration` | `scsMapDataLayout`, `scsMapDataSubstrate`, `scsMapDataSubstrateMap` |
| `scsOverlay` | Overlay定义 | `semiconductor_bin_overlay` | `scsBinCodeMap`, `scsDeviceIdMap`, `scsMapDataSubstrateMap`, `scsReferenceDevice`, `scsTransferMap` |

### D_no_business_fk_evidence

没有可确认的业务外键证据。

| 类 | 中文名 | 模块 | 物理证据 |
|---|---|---|---|
| `A_AreaGroup` | 区域组 | `semiconductor_scheduling_flow` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `A_CycleTimeHolidays` | 周期时间节假日 | `semiconductor_scheduling_flow` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `A_ModifyAttrsReason` | 属性修改原因 | `semiconductor_carrier_material_tool` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `A_ProcessArea` | 半导体工艺区域 | `semiconductor_foundation` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `A_ShipErrors` | 出货错误配置 | `semiconductor_shipping_integration` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `A_TerminateAccount` | 账户终止配置 | `semiconductor_service_location` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `A_UnTerminateReason` | 取消终止原因 | `semiconductor_service_location` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `BonusReason` | 奖励原因 | `bonus_reasons` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `LocalReworkReason` | 本地返工原因 | `local_rework` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `QtyAdjustReason` | 数量调整原因 | `qty_adjust_reason` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `RemovalReason` | 移除原因 | `removal_reason` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `SellReason` | 销售原因 | `sell_reason` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `UserConstant` | 用户常量 | `semiconductor_user_job_spc_configuration` | 物理CSV中仅有基础设施外键，或没有业务外键。 |
| `ss_LabelSourceInput` | 标签源输入 | `semiconductor_print_interface_details` | 物理CSV中仅有基础设施外键，或没有业务外键。 |

## 建议顺序

1. 若 `A0` 或 `A1` 非零，优先补齐其中有直接FK或明确桥接路径的对象。
2. `C_unmodeled_reference_only` 需要继续建模其引用表，并确认这些表能否形成通向主图的业务路径。
3. `D_no_business_fk_evidence` 不应为了视觉效果强行连线；需要 Swagger、业务配置或多态列表定义提供额外证据。
