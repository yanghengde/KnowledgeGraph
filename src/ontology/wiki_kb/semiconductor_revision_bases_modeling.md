# 版本控制Base实体建模 / Revision-Control Base Entity Modeling

## 中文

本批次补齐已建版本控制实体直接依赖的物理Base表，形成版本记录与当前修订之间的双向基础。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `MasterRecipeBase`（主配方Base）：管理主配方修订记录。
- `ProcessModelTemplateBase`（过程模型模板Base）：管理过程模型模板修订记录。
- `BusinessProcessSpecBase`（业务过程规格Base）：管理业务过程规格修订记录。
- `BusinessProcessWorkflowBase`（业务过程工作流Base）：管理业务过程工作流修订记录。
- `ProcessTimerBase`（过程计时器Base）：管理过程计时器修订记录。
- `isImageBase`（图像Base）：管理图像对象修订记录。
- `BOMBase`（BOM Base）：管理BOM修订记录。
- `DataCollectionDefBase`（数据采集定义Base）：管理数据采集定义修订记录。
- `SetupBase`（Setup Base）：管理Setup修订记录。
- `MaintenanceReqBase`（维护需求Base）：管理维护需求修订记录。
- `ERPBOMBase`（ERP BOM Base）：管理ERP BOM修订记录。
- `MfgOrderProcedureBase`（制造工单程序Base）：管理制造工单程序修订记录。
- `MfgOrderTaskListBase`（制造工单任务列表Base）：管理制造工单任务列表修订记录。
- `SchedulingRouteBase`（排程路线Base）：管理排程路线修订记录。
- `CIOTemplateBase`（CIO模板Base）：管理CIO模板修订记录。

## English

This batch adds physical Base tables directly required by modeled revision-controlled entities.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
