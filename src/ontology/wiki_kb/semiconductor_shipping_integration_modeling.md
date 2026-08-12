# 半导体出货、集成与监控建模 / Semiconductor Shipping, Integration, and Monitoring Modeling

## 中文

本批次覆盖出货工厂/工序、集成映射点、Quantix配置、状态模型、监控与追踪标签。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_ShipErrors`（出货错误配置）：定义出货校验错误和消息。
- `A_ShipFromFactory`（发货工厂）：定义发货来源工厂。
- `A_ShipPlantCode`（出货工厂代码）：定义出货Plant代码。
- `A_ShipToFactory`（收货工厂）：定义出货目标工厂。
- `A_ShipToProcess`（出货目标工序）：定义出货后的目标工序。
- `I_IntegrationMap`（集成映射）：定义外部集成对象和字段映射。
- `I_IntegrationPoint`（集成点）：定义系统集成端点。
- `scsMapData`（半导体Map数据）：定义Map数据配置。
- `scsQuantixMatrix`（Quantix矩阵）：按工艺上下文选择Quantix配置。
- `scsQuantixRecipe`（Quantix配方）：定义Quantix配方和关联参数。
- `scsStatusModel`（半导体状态模型）：定义半导体专用状态模型。
- `ss_Surveillance`（过程监控）：定义半导体过程监控和告警规则。
- `ss_SurveillanceReason`（监控原因）：定义过程监控原因目录。
- `ss_TrackLabel`（追踪标签）：定义WIP和设备追踪标签配置。

## English

This batch covers shipping factories and processes, integration mapping points, Quantix configuration, status models, surveillance, and tracking labels.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
