# 半导体WIP、Hold与时间窗口建模 / Semiconductor WIP, Hold, and Time-Window Modeling

## 中文

本批次覆盖WIP数据定义、Hold位置与未来Hold、最小/最大时间窗口、WIP指令，以及跨批次复用的邮件组、排程和失败处理配置。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_EmailGroup`（邮件组）：定义半导体业务通知使用的邮件接收组。
- `A_WIPDataSetup`（WIP数据配置）：定义WIP数据采集、显示、验证和失败处理规则。
- `A_WIPDataName`（WIP数据名称）：定义WIP数据项目录及其属性配置。
- `A_WIPDataDisplayFilter`（WIP数据显示过滤器）：定义WIP数据的显示过滤配置。
- `A_AdHocWIPDataSetup`（临时WIP数据配置）：定义临时WIP数据采集配置。
- `A_FutureHoldSetup`（未来Hold配置）：定义未来工步触发Hold的位置、原因、规格和通知规则。
- `A_HoldLocation`（Hold位置）：定义半导体在制品Hold位置目录。
- `A_MinTimeWindowSetup`（最小时间窗口配置）：定义工艺步骤间最小等待时间及失败处理规则。
- `A_MaxTimeWindowSetup`（最大时间窗口配置）：定义工艺步骤间最大等待时间及失败处理规则。
- `A_RunNumberSetup`（运行号配置）：定义WIP运行号生成与管理规则。
- `A_WIPInstructions`（WIP指令）：按产品、工艺规格、标准规格和工作流步骤配置WIP作业指令。
- `ss_WIPDataSetupMatrix`（WIP数据配置矩阵）：按产品、设备、规格和工作流步骤选择WIP数据配置。
- `ss_FailureFutureHoldSetup`（失败未来Hold配置）：定义失败后使用的未来Hold配置。
- `ss_FailureNCRSetup`（失败NCR配置）：定义失败时创建NCR的规则和分类。
- `A_ScheduleSSPlan`（半导体排程计划）：定义半导体特殊排程计划目录。

## English

This batch covers WIP data definitions, hold locations and future holds, minimum and maximum time windows, WIP instructions, and shared email, scheduling, and failure-handling configurations.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
