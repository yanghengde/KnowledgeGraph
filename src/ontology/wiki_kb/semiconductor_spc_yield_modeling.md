# 半导体SPC与良率控制建模 / Semiconductor SPC and Yield Control Modeling

## 中文

本批次覆盖SPC连接、规则、宏、矩阵与配置，以及良率限制和半导体抽样配置。运行时SPC事务数据明确排除在顶级配置本体之外。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_SPCConnection`（SPC连接）：定义SPC系统连接和接口参数。
- `A_SPCExcludeReason`（SPC排除原因）：定义SPC数据点排除原因目录。
- `A_SPCMacro`（SPC宏）：定义SPC处理使用的宏文件。
- `A_SPCRules`（SPC规则）：定义SPC规则主数据。
- `A_SPCSetup`（SPC配置）：定义SPC图表、查询、失败动作、状态和文档配置。
- `A_SPCMatrix`（SPC矩阵）：按产品、规格、设备和工作流步骤选择SPC配置。
- `ss_SPCAnnotationCategory`（SPC注释类别）：定义SPC数据注释类别。
- `ss_SPCCustomFilterTable`（SPC自定义过滤表）：定义SPC自定义过滤表及别名。
- `A_YieldType`（良率类型）：定义良率类型和良率维度。
- `A_YieldLimits`（良率限制）：定义产品、工艺和工作流上下文中的上下限、Bin限制、Hold和通知动作。
- `A_LotSizeSamplingSetup`（批量大小抽样配置）：定义按批量大小和规格应用的抽样配置。
- `A_SamplingPlanSetup`（抽样计划配置）：按产品、产品家族、工艺规格和所有者选择抽样计划。

## English

This batch covers SPC connections, rules, macros, matrices, setup, yield limits, and semiconductor sampling configuration. Runtime SPC transaction data is explicitly excluded from the top-level configuration ontology.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
