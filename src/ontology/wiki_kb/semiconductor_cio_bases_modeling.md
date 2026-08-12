# 半导体与CIO版本支撑建模 / Semiconductor and CIO Version Support Modeling

## 中文

本批次补齐CIO参数/Base表以及半导体实验、工艺规格、产品BOM、供料器和监控的Base实体。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `CIOJournalPersist`（CIO日志持久化）：定义CIO日志持久化配置。
- `CIODetailSection`（CIO明细区段）：定义通道适配器明细区段。
- `MessageNameParameter`（消息名称参数）：定义消息名称解析参数。
- `RequestIdParameter`（请求ID参数）：定义请求ID解析参数。
- `MessageTypeParameter`（消息类型参数）：定义消息类型解析参数。
- `TagDataParameter`（标签数据参数）：定义标签数据解析参数。
- `CIOMapSource`（CIO映射源）：定义消息映射数据源。
- `CIOMessageMapBase`（CIO消息映射Base）：管理消息映射修订记录。
- `CIOWorkflowBase`（CIO工作流Base）：管理CIO工作流修订记录。
- `CIOListProcessorBase`（CIO列表处理器Base）：管理列表处理器修订记录。
- `A_ExperimentPlanBase`（实验计划Base）：管理半导体实验计划修订记录。
- `A_ProcessSpecBase`（工艺规格Base）：管理半导体工艺规格修订记录。
- `A_ProductBOMBase`（产品BOM Base）：管理半导体产品BOM修订记录。
- `ss_FeederPlanBase`（供料器计划Base）：管理供料器计划修订记录。
- `ss_SurveillanceBase`（过程监控Base）：管理过程监控修订记录。

## English

This batch adds CIO parameter and Base tables plus semiconductor experiment, process-specification, product-BOM, feeder, and surveillance Base entities.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
