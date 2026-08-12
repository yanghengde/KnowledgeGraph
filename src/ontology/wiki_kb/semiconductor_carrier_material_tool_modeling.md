# 半导体载具、物料与工装建模 / Semiconductor Carrier, Material, and Tooling Modeling

## 中文

本批次覆盖载具验证、产品BOM、资源图标、工装矩阵、供料器、参数矩阵及属性访问配置。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_AttributeAccess`（属性访问）：定义对象属性的访问控制。
- `A_CarrierValidationSetup`（载具验证配置）：定义载具装载与使用验证规则。
- `A_ModifyAttrsReason`（属性修改原因）：定义修改属性时使用的原因代码。
- `A_ParamName`（参数名称）：定义半导体参数名称和类型。
- `A_ProcessData`（工艺数据）：定义工艺数据主目录。
- `A_ProductBOM`（半导体产品BOM）：定义半导体产品BOM及工艺上下文。
- `A_ResourceIcon`（资源图标）：定义设备资源显示图标。
- `A_ToolPlanMatrix`（工装计划矩阵）：按产品、设备、规格和步骤选择工装计划。
- `scsCarrierFamilyMatrix`（载具家族矩阵）：按产品和工艺上下文选择载具家族。
- `ss_ContainerDimension`（容器尺寸）：定义半导体容器尺寸主数据。
- `ss_FeederPlan`（供料器计划）：定义设备供料器计划。
- `ss_FeederSlot`（供料器槽位）：定义供料器槽位主数据。
- `ss_ParameterMatrix`（参数矩阵）：按产品、设备、规格和步骤选择参数配置。
- `ss_ToolAction`（工装动作）：定义工装使用和状态动作。

## English

This batch covers carrier validation, product BOM, resource icons, tooling matrices, feeders, parameter matrices, and attribute-access configuration.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
