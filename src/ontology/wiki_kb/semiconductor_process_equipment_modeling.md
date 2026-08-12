# 半导体工艺与设备能力建模 / Semiconductor Process and Equipment Capability Modeling

## 中文

本批次覆盖工艺规格、工艺能力、设备约束、配方矩阵、设备参数和测试程序等半导体核心配置。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_ProcessSpec`（半导体工艺规格）：定义可版本控制的半导体工艺规格及其有效期、周期时间、工作流和包装规则。
- `A_ProcessSpecStatus`（工艺规格状态）：定义工艺规格的可用状态目录。
- `A_ProcessCapability`（工艺能力）：定义设备可支持的工艺能力和多腔室条件。
- `A_EquipmentMatrix`（设备矩阵）：按产品、工艺规格、标准规格、设备组和工作流步骤配置可用设备。
- `ss_EqpConstraintMatrix`（设备约束矩阵）：定义具体设备或设备组的半导体约束矩阵。
- `A_RecipeMatrix`（配方矩阵）：按工艺能力、设备、产品、规格和工作流步骤选择生产配方与工装计划。
- `ss_RecipeGroup`（配方组）：定义半导体配方分组目录。
- `A_ModifyAttrsSetup`（属性修改配置）：定义可修改属性、字段类型、访问级别和修改原因要求。
- `A_EquipmentParamList`（设备参数列表）：定义设备参数列表主数据。
- `A_TestProgramSetup`（测试程序配置）：按产品线、产品、规格和工艺规格配置测试程序。

## English

This batch covers semiconductor process specifications, process capabilities, equipment constraints, recipe matrices, equipment parameters, and test-program configuration.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
