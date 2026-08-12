# CIO编排与派工建模 / CIO Orchestration and Dispatch Modeling

## 中文

本批次覆盖CIO列表处理、派工、出站消息、工作流、测试对象和查询门户页面配置。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `CIOListProcessor`（列表处理器）：定义集成列表数据的迭代和处理规则。
- `CIODispatchRule`（CIO派工规则）：定义消息和工作流派工规则。
- `CIOSystemDispatchRule`（系统派工规则）：定义按目标系统执行的派工规则。
- `CIOOutboundMsgDef`（出站消息定义）：定义CIO出站消息和发送配置。
- `CIOWorkflow`（CIO工作流）：定义集成处理工作流及步骤编排。
- `CIOTestObject`（CIO测试对象）：定义集成配置验证使用的测试对象。
- `cioQueryPortalPage`（CIO查询门户页面）：定义CIO查询门户页面配置。

## English

This batch covers CIO list processing, dispatch, outbound messages, workflows, test objects, and query portal-page configuration.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
