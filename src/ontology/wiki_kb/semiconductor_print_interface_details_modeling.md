# 半导体打印、接口与标签明细建模 / Semiconductor Printing, Interface, and Label Detail Modeling

## 中文

本批次覆盖打印数据项、外部接口、服务规则、标签计划和追踪标签的配置明细。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_PrintDataItem`（打印数据项）：定义打印数据项目。
- `A_PrintDataItemParams`（打印数据项参数）：定义打印数据项参数。
- `A_PrintingSetupParameters`（打印配置参数）：定义打印配置参数。
- `A_ExternalInterfaceDetail`（外部接口明细）：定义外部接口动作明细。
- `A_ExternalInterfaceDetailParam`（外部接口明细参数）：定义外部接口明细参数。
- `A_ExternalInterfaceDetailRule`（外部接口明细规则）：定义外部接口明细规则。
- `A_RunNumberSetupData`（运行号配置数据）：定义运行号配置数据项。
- `A_ServiceRulesValidations`（服务规则验证）：定义服务规则验证项。
- `A_ServiceSetupBusinessRules`（服务业务规则）：定义服务配置关联业务规则。
- `ss_LabelPlanDetails`（标签计划明细）：定义标签计划步骤明细。
- `ss_LabelSourceInput`（标签源输入）：定义标签数据源输入。
- `ss_TrackLabelDetails`（追踪标签明细）：定义追踪标签明细。
- `ss_TrackLabelDetailsSource`（追踪标签明细来源）：定义追踪标签明细数据源。
- `ss_TrackLabelSource`（追踪标签来源）：定义追踪标签数据源。
- `ss_SlotWaferInstruction`（槽位晶圆指令）：定义槽位和晶圆作业指令。

## English

This batch covers configuration details for print data items, external interfaces, service rules, label plans, and tracking labels.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
