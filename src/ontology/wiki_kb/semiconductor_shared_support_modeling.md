# 半导体公共支撑主数据建模 / Semiconductor Shared Supporting Master Data Modeling

## 中文

本批次补齐被多个已建实体引用的资源、菜单、查询、状态、位置、审批及公共类型实体。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `ResourceDef`（资源定义）：半导体套件中的物理资源/设备定义。
- `PortalMenuDefinition`（门户菜单定义）：定义门户端菜单配置。
- `TargetSystem`（目标系统）：定义集成或部署目标系统。
- `UserQuery`（用户查询）：定义可复用用户查询。
- `BillType`（清单类型）：定义BOM及相关清单类型。
- `A_EmployeeGroup`（员工组）：定义员工业务分组。
- `MenuDefinition`（菜单定义）：定义Web与客户端菜单。
- `ApprovalSheetTemplate`（审批单模板）：定义审批单模板。
- `DataPointCollection`（数据点集合）：定义可复用数据点集合。
- `CurrentStatus`（当前状态）：保存可追踪对象当前状态。
- `HoldStatus`（Hold状态）：定义对象Hold状态。
- `A_JobModel`（作业模型）：定义半导体作业执行模型。
- `ResourceStatusCodeGroup`（资源状态代码组）：定义资源状态代码分组。
- `A_PhysicalLocation`（物理位置）：定义半导体物理位置。
- `Location`（位置）：定义通用业务位置。

## English

This batch closes highly referenced resource, menu, query, status, location, approval, and common-type dependencies.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
