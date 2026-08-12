# 半导体排程与工艺流控制建模 / Semiconductor Scheduling and Process-Flow Control Modeling

## 中文

本批次覆盖日历、派工、排程、步骤逻辑、周期时间、Send Ahead及制造线等配置。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_AreaGroup`（区域组）：定义制造区域分组。
- `A_AutomationPlan`（自动化计划）：定义自动化执行计划。
- `A_Calendar`（半导体日历）：定义班次、工作周和节假日生产日历。
- `A_CalendarHolidays`（日历节假日）：定义生产日历节假日规则。
- `A_CalendarShiftsCycle`（日历班次周期）：定义日历班次轮换周期。
- `A_CycleTimeHolidays`（周期时间节假日）：定义周期时间计算使用的节假日。
- `A_DispatchPlan`（派工计划）：定义半导体派工计划。
- `A_EqpDispatchQueryMatrix`（设备派工查询矩阵）：按设备、产品和工艺上下文选择派工查询。
- `A_ScheduleInstructions`（排程指令）：定义排程使用的作业指令。
- `A_StepCycleTimeSetup`（步骤周期时间配置）：按产品和工艺步骤配置标准周期时间。
- `A_StepLogic`（步骤逻辑）：定义工作流步骤上的半导体控制逻辑。
- `scsSchedulingMatrix`（排程矩阵）：按产品、设备、规格和步骤选择排程配置。
- `ss_MfgLine`（半导体制造线）：定义半导体制造线主数据。
- `ss_ProcessTimerMatrix`（工艺计时器矩阵）：按工艺上下文选择过程计时器。
- `ss_SendAheadMatrix`（Send Ahead矩阵）：定义批次提前送往后续步骤的控制矩阵。

## English

This batch covers calendars, dispatch, scheduling, step logic, cycle time, send-ahead, and manufacturing-line configuration.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
