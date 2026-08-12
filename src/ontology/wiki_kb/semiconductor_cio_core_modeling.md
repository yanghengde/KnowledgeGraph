# CIO连接与消息核心建模 / CIO Connection and Messaging Core Modeling

## 中文

本批次覆盖Workspace 10中的CIO连接、通道、适配器、消息映射、模板、数据处理和基础函数配置。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `CIOSettings`（CIO全局设置）：定义CIO集成运行的全局配置。
- `CIOCamstarConnection`（Camstar连接）：定义CIO访问Camstar服务的连接参数。
- `CIOChannelSource`（通道源）：定义消息通道的数据源和通信参数。
- `CIOChannelAdapter`（通道适配器）：定义不同协议和系统的CIO通道适配配置。
- `CIOMessageChannel`（消息通道）：定义消息通道、源、适配器和消息类型关联。
- `CIOMessageType`（消息类型）：定义CIO消息格式、方向和处理配置。
- `CIOMessageMap`（消息映射）：定义输入输出消息字段和模板映射。
- `CIOTemplate`（CIO模板）：定义消息转换和生成模板。
- `CIOBinding`（CIO绑定）：定义集成数据绑定配置。
- `CIOBuffer`（CIO缓冲区）：定义集成消息缓冲和容量规则。
- `CIODataHandler`（数据处理器）：定义CIO数据处理器主配置。
- `CIODataPointType`（数据点类型）：定义集成数据点类型目录。
- `CIODataPointInstance`（数据点实例）：定义具体数据点实例及其类型。
- `CIOFilter`（CIO过滤器）：定义集成消息和数据过滤规则。
- `CIOFunction`（CIO函数）：定义集成工作流可调用的函数目录。

## English

This batch covers CIO connections, channels, adapters, message mapping, templates, data handling, and foundation functions in workspace 10.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
