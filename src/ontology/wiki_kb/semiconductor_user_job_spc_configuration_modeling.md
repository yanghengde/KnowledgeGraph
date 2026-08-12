# 用户、作业与SPC配置 / User, Job, and SPC Configuration

## 中文

补齐用户常量、作业代码、SPC图表和CIO出站等配置实体。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `UserConstant`（用户常量）：用户可配置的命名常量。
- `UserLabel`（用户标签）：用户定义的界面和消息标签。
- `WhereUsedConfig`（使用位置配置）：建模对象Where-Used查询行为配置。
- `A_SPCChart`（SPC图表）：半导体SPC图表主数据。
- `A_JobCauseCode`（作业原因代码）：维修或服务作业的原因代码。
- `A_JobRepairCode`（作业维修代码）：维修作业采用的维修措施代码。
- `A_JobStage`（作业阶段）：维修或服务作业的阶段配置。
- `A_JobSymptomCode`（作业症状代码）：维修或服务作业的症状代码。
- `CIOOutboundDefinition`（CIO出站定义）：CIO出站消息、路由和转换配置。
- `WIPMsgConfig`（WIP消息配置）：在制品消息显示与处理配置。
- `PermissionDefinition`（权限定义）：系统权限项的物理定义。
- `ResourceStatusCodeGroupDef`（资源状态代码组定义）：资源状态代码组的定义记录。

## English

Adds physical user, job-code, SPC chart, CIO outbound, permission, and message configuration entities.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
