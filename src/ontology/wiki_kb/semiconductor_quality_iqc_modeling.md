# 半导体质量、IQC与分选建模 / Semiconductor Quality, IQC, and Sorting Modeling

## 中文

本批次覆盖检查表矩阵、PDA限制、规格Bin、IQC检查与参数、分选代码及失败Hold配置；运行时IQC数据不作为顶级配置实体。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_CheckSheetMatrix`（检查表矩阵）：按产品、规格、设备和步骤选择检查表。
- `A_CountVarianceLimits`（数量差异限制）：定义数量差异允许范围。
- `A_PDALimits`（PDA限制）：定义PDA质量限制及失败动作。
- `A_ProcessSpecBins`（工艺规格Bin）：定义工艺规格关联的Bin规则。
- `A_RejectCategory`（拒收类别）：定义质量拒收类别。
- `A_ResortNoteCode`（重分选备注代码）：定义重分选备注代码。
- `A_SortNoteCode`（分选备注代码）：定义分选备注代码。
- `A_SortIQCLotCheck`（IQC批次检查）：定义IQC批次检查配置。
- `A_SortIQCWaferCheck`（IQC晶圆检查）：定义IQC晶圆检查配置。
- `A_SortSQAFailure`（SQA失败配置）：定义分选SQA失败处理配置。
- `A_TestIQCOption`（IQC测试选项）：定义IQC测试选项。
- `A_TestIQCParams`（IQC测试参数）：定义IQC测试参数。
- `A_TestIQCSetup`（IQC测试配置）：定义IQC测试总体配置。
- `A_VarianceReason`（差异原因）：定义数量或质量差异原因。
- `scsFailureHoldSetup`（失败Hold配置）：定义质量失败后的Hold动作。

## English

This batch covers check-sheet matrices, PDA limits, specification bins, IQC checks and parameters, sorting codes, and failure-hold setup. Runtime IQC data is excluded.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
