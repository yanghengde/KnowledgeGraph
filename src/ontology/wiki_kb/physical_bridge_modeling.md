# 物理桥接与事务事实对象 / Physical Bridge and Transaction Fact Objects

## 中文

补充连接现有游离业务对象所必需的物理桥接表、事务历史表和明细表。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_AdHocWIPDataSetupDetails`（临时WIP数据配置明细）：连接临时WIP数据配置与WIP数据设置。
- `A_CalendarHolidaysShifts`（日历节假日班次）：连接日历节假日与班次。
- `A_ExpParameterOverrides`（实验参数覆盖）：记录实验参数覆盖及相关文档、工具和WIP配置。
- `A_Job`（作业）：记录资源作业、阶段、症状、原因和维修代码。
- `A_LotAttributes`（批次属性）：记录批次出货、包装、供应商和产品BOM等扩展属性。
- `A_LotItems`（批次物项）：连接容器批次与物项类别、物项类型。
- `A_LotWafers`（批次晶圆）：记录批次晶圆、分选备注、产品和设备信息。
- `A_RoleAccess`（角色访问）：连接属性访问、角色和打印配置。
- `A_ScanningData`（扫描数据）：记录容器、工序、载具和事务主线的扫描事实。
- `A_SPCTxnDataDetails`（SPC事务数据明细）：记录SPC事务数据、图表和规则明细。
- `A_SPCTxnDataPoint`（SPC事务数据点）：连接SPC排除原因与注释类别。
- `A_WIPLot`（在制批次扩展）：记录半导体在制批次、工艺步骤和插入原因。
- `A_WIPLotRejectsHistory`（WIP批次拒收历史）：记录批次拒收类别、损失原因、产品和设备历史。
- `ActionDefActionRules`（动作定义规则）：连接动作定义与动作规则。
- `ComponentDefectHistoryDetail`（组件缺陷历史明细）：记录组件缺陷原因、容器和产品历史。
- `ComponentReplaceHistoryDetail`（组件替换历史明细）：记录替换原因与替代原因历史。
- `ContainerStatusChangeHistory`（容器状态变更历史）：记录容器状态、状态变更原因和事务主线。
- `EventLog`（事件日志）：记录事件评论类型、人员和事件数据。
- `ExecuteMfgOrderTaskHistory`（工单任务执行历史）：记录制造工单任务状态及执行事务。
- `ExecuteSamplingLotHistory`（抽样批次执行历史）：记录抽样批次的报废与返工原因。
- `FailureActionTypeGroupEntries`（失效动作类型组条目）：连接失效处理动作类型组和动作类型。
- `I_IntegrationMapDetails`（集成映射明细）：连接集成映射与集成点。
- `IssueActualsHistory`（物料发行实际历史）：记录物料发行原因、差异原因、替代原因、容器、产品和资源。
- `isImage`（图像）：连接图像Base、文档附件和文档查看器。
- `KPIEntry`（KPI条目）：连接KPI矩阵、类型、时间范围及制造维度。
- `MaintenanceReqss_UsageReqSetup`（维护需求使用配置）：连接维护需求与使用需求配置明细。
- `NamedObjectGroupGroups`（命名对象组层级）：记录命名对象组的父子层级。
- `NCRFailureCodeGroupEntries`（NCR失效代码组条目）：连接NCR失效代码组和失效代码。
- `NonconformanceReportNCRFailure`（不合格报告NCR失效）：连接不合格报告与NCR失效代码。
- `PauseReasonGroupEntries`（暂停原因组条目）：连接暂停原因组和暂停原因。
- `PauseTaskHistory`（暂停任务历史）：记录暂停原因、容器、电子程序、任务和事务主线。
- `RegulatoryReportHistoryDetail`（监管报告历史明细）：记录监管机构、报告类型、附件和提交人员。
- `RemoveHistoryDetail`（移除历史明细）：记录差异消除原因、容器、产品、位置和数量单位。
- `ReprintLabelHistory`（标签重印历史）：记录重印原因、打印队列和事务主线。
- `SessionValues`（会话值）：记录资源布局与工厂、工序、资源、规格和工作中心。
- `SPCRuleViolations`（SPC规则违规）：连接SPC异常事件与SPC规则。
- `StartHistoryDetailIssueConditi`（开工历史发行条件）：连接开工历史明细与物料发行条件。
- `UIAction`（UI动作）：连接动作类别和动作定义。
- `UserCodeGroupEntries`（用户代码组条目）：记录用户代码组及原因代码条目。

## English

Physical bridge, transaction history, and detail tables required to connect previously isolated business objects.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
