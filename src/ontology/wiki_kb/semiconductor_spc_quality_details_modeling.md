# 半导体SPC与质量参数明细建模 / Semiconductor SPC and Quality Parameter Detail Modeling

## 中文

本批次覆盖SPC矩阵、规则、配置、WIP矩阵及IQC的配置参数和明细，不包含SPC事务采集明细。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_SPCMatrixParams`（SPC矩阵参数）：定义SPC矩阵参数。
- `A_SPCRulesParams`（SPC规则参数）：定义SPC规则参数。
- `A_SPCSetupDetails`（SPC配置明细）：定义SPC图表和数据项明细。
- `A_SPCSetupDetailsInlineParam`（SPC内联参数）：定义SPC配置内联参数。
- `A_SPCSetupDetailsParams`（SPC明细参数）：定义SPC明细参数。
- `A_SPCSetupDetailsTitle`（SPC明细标题）：定义SPC明细显示标题。
- `A_SPCSetupParams`（SPC配置参数）：定义SPC配置级参数。
- `A_SPCWIPDataMatrixParams`（SPC WIP矩阵参数）：定义SPC WIP数据矩阵参数。
- `ss_CustomSPCGridFilter`（SPC网格过滤器）：定义SPC网格自定义过滤配置。
- `ss_SPCGPCChartData`（SPC GPC图表配置）：定义SPC GPC图表数据配置。
- `ss_ParameterMatrixList`（参数矩阵列表）：定义参数矩阵列表明细。
- `ss_ParamNameDetails`（参数名称明细）：定义参数名称的可选项和规则。
- `scsInlineParams`（内联参数）：定义半导体内联参数。
- `A_TestIQCParamsDetails`（IQC参数明细）：定义IQC测试参数明细。
- `ss_UsageReqSetupDetails`（使用需求配置明细）：定义使用需求配置明细。

## English

This batch covers configuration parameters and details for SPC matrices, rules, setup, WIP matrices, and IQC, excluding runtime SPC transaction details.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
