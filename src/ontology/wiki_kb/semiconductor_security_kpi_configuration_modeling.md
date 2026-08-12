# 安全、KPI与公共配置 / Security, KPI, and Shared Configuration

## 中文

补齐安全权限、KPI、通知、代码组和公共建模配置实体。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `ESigRoleGroup`（电子签名角色组）：电子签名允许角色的分组配置。
- `ExternalPermission`（外部权限）：外部系统或功能权限定义。
- `FilterTag`（过滤标签）：建模对象过滤和分类使用的标签。
- `ErrorMsg`（错误消息）：系统错误消息和显示内容配置。
- `KPIMatrix`（KPI矩阵）：KPI指标组合与矩阵配置。
- `KPITimeframe`（KPI时间范围）：KPI统计和展示使用的时间范围。
- `KPIType`（KPI类型）：KPI指标类型主数据。
- `NamedObjectGroup`（命名对象组）：命名建模对象的通用分组定义。
- `NotifVar`（通知变量）：通知模板可引用的变量定义。
- `ReprintReason`（重新打印原因）：标签或文档重新打印的原因代码。
- `RevisionedObjectGroup`（版本对象组）：版本化建模对象的通用分组。
- `SummaryTableDef`（汇总表定义）：汇总数据表结构与展示配置。
- `SystemSecurityGroup`（系统安全组）：系统级用户和权限安全组。
- `TextVariable`（文本变量）：消息与模板中的文本变量定义。
- `UserCodeGroup`（用户代码组）：用户自定义代码的分组配置。

## English

Adds physical security, KPI, notification, code-group, and shared modeling configuration entities.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
