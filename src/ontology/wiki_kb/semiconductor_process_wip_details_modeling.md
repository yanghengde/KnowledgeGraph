# 半导体工艺与WIP配置明细建模 / Semiconductor Process and WIP Configuration Detail Modeling

## 中文

本批次覆盖工艺规格、实验计划、产品BOM、工装、WIP数据、未来Hold、供料器和排程矩阵的配置明细。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_ProcessSpecDetails`（工艺规格明细）：定义工艺规格的步骤和业务配置明细。
- `A_ProcessSpecDetailsAction`（工艺规格明细动作）：定义工艺规格明细关联动作。
- `A_ProcessSpecDetailsParams`（工艺规格明细参数）：定义工艺规格明细参数。
- `A_ProcessSpecParams`（工艺规格参数）：定义工艺规格级参数。
- `A_ProcessCodeParams`（工艺代码参数）：定义工艺代码参数。
- `A_ProcessDataDetails`（工艺数据明细）：定义工艺数据明细。
- `A_ExperimentPlanDetails`（实验计划明细）：定义实验计划步骤及自动动作明细。
- `A_ProductBOMMaterialList`（产品BOM物料清单）：定义半导体产品BOM物料明细。
- `A_ToolPlanItem`（工装计划项）：定义工装计划项目及配方。
- `A_TestProgramSetupDetails`（测试程序配置明细）：定义测试程序配置明细。
- `A_WIPDataSetupDetails`（WIP数据配置明细）：定义WIP数据字段、验证和失败动作明细。
- `ss_FutureHoldSetupDetails`（未来Hold配置明细）：定义未来Hold目标步骤明细。
- `ss_FeederPlanDetails`（供料器计划明细）：定义供料器计划槽位和物料明细。
- `scsSchedulingMatrixDetail`（排程矩阵明细）：定义排程矩阵具体调度参数。
- `ss_EqpConstraintDetails`（设备约束明细）：定义设备约束矩阵明细。

## English

This batch covers configuration details for process specifications, experiment plans, product BOMs, tooling, WIP data, future holds, feeders, and scheduling matrices.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
