# 半导体晶圆与实验配置建模 / Semiconductor Wafer and Experiment Configuration Modeling

## 中文

本批次覆盖晶圆属性、物料分类、实验计划及其实验自动动作配置，仅纳入具备独立建模生命周期的主实体。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_AttributeType`（属性类型）：定义半导体对象可配置属性的类型目录。
- `A_BinType`（Bin类型）：定义晶圆或产品Bin分类及其关联属性。
- `A_ItemCategory`（物项类别）：定义半导体物项的类别主数据。
- `A_ItemType`（物项类型）：定义物项类型、保管期限、序列化和数量控制规则。
- `A_WaferAttributeSetup`（晶圆属性配置）：定义晶圆属性的配置主数据。
- `scsWaferDataSampling`（晶圆数据抽样）：定义晶圆数据抽样及数量选择规则。
- `A_ExperimentPlan`（实验计划）：定义可版本控制的半导体实验计划及审批组、工艺规格和消息配置。
- `A_ExpAutoHold`（实验自动Hold）：定义实验过程自动Hold的位置、原因和通知规则。
- `A_ExpAutoSS`（实验自动排程计划）：定义实验过程自动应用的排程计划。
- `A_ExpAutoSplit`（实验自动拆分）：定义实验批次自动拆分和后续合并规则。
- `A_ExpSpecialCheckSheet`（实验特殊检查表）：定义实验使用的特殊检查表配置。
- `A_ExpSpecialInstructions`（实验特殊指令）：定义实验过程的特殊作业指令。
- `ss_BlanketExperiments`（批量实验配置）：按工单、产品、设备、规格和工作流步骤配置批量实验。

## English

This batch covers wafer attributes, item classification, experiment plans, and experiment automation configurations that have independent modeling lifecycles.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
