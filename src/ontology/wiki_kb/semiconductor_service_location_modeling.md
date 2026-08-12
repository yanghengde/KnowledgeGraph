# 半导体服务、位置与账户建模 / Semiconductor Service, Location, and Account Modeling

## 中文

本批次覆盖外部接口与位置、扫描、服务规则、扣留类型及账户终止相关配置。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_ExternalInterface`（外部接口）：定义半导体外部系统接口。
- `A_ExternalLocation`（外部位置）：定义外部业务位置。
- `A_ExternalLocationType`（外部位置类型）：定义外部位置类型目录。
- `A_ImpoundType`（扣留类型）：定义物料或在制品扣留类型。
- `A_InsertionReason`（插入原因）：定义工艺步骤插入原因。
- `A_LocationMap`（位置映射）：定义内部与外部位置映射。
- `A_ScanningName`（扫描名称）：定义扫描数据项目录。
- `A_ScanningSetup`（扫描配置）：定义扫描采集和验证配置。
- `A_ServiceAttrsSetup`（服务属性配置）：定义服务可用属性配置。
- `A_ServiceRules`（服务规则）：定义服务执行规则。
- `A_ServiceSetup`（服务配置）：定义服务属性、规则和访问配置。
- `A_TerminateAccount`（账户终止配置）：定义账户终止处理配置。
- `A_TerminateReason`（终止原因）：定义账户或业务终止原因。
- `A_UTAReason`（UTA原因）：定义UTA处理原因。
- `A_UnTerminateReason`（取消终止原因）：定义撤销终止操作原因。

## English

This batch covers external interfaces and locations, scanning, service rules, impound types, and account-termination configuration.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
