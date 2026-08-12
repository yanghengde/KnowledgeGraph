# 半导体打印、标签、包装与出货建模 / Semiconductor Printing, Labeling, Packaging, and Shipping Modeling

## 中文

本批次覆盖半导体打印基础设施、标签计划与配置、包装数量/类型，以及出货工厂代码。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_PrintData`（打印数据）：定义打印内容、模板和业务对象上下文。
- `A_Printer`（打印机）：定义半导体打印机及其类型和连接配置。
- `A_PrinterType`（打印机类型）：定义打印机类型目录。
- `A_PrintingAutomation`（打印自动化）：定义自动打印触发和处理配置。
- `A_PrintingComputer`（打印计算机）：定义承载打印服务的计算机配置。
- `A_PrintingConnection`（打印连接）：定义打印系统连接参数。
- `A_PrintingSetup`（打印配置）：定义打印机、连接、类型和自动化的组合配置。
- `A_PrintingType`（打印类型）：定义打印业务类型目录。
- `ss_LabelPlan`（标签计划）：定义半导体标签生成计划。
- `ss_LabelSetup`（标签配置）：定义标签类型、打印配置和业务规则。
- `ss_LabelType`（标签类型）：定义半导体标签类型目录。
- `A_PackingQty`（包装数量）：定义包装数量和相关包装类型。
- `A_PackingType`（包装类型）：定义半导体包装类型目录。
- `A_PackageGroup`（包装组）：定义包装业务分组。
- `A_ShipFactoryCode`（出货工厂代码）：定义出货使用的工厂代码目录。

## English

This batch covers semiconductor printing infrastructure, label plans and setup, packaging quantity and type configuration, and shipping factory codes.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
