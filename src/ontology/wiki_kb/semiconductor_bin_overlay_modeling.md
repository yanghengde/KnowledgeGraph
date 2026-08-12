# 半导体Bin与Overlay / Semiconductor Bin and Overlay

## 中文

补齐晶圆分Bin和Overlay配置使用的半导体物理主数据。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `scsBinCode`（Bin代码）：晶圆或测试结果分Bin使用的代码定义。
- `scsBinDefinition`（Bin定义）：半导体分Bin规则引用的Bin主数据。
- `scsOverlay`（Overlay定义）：晶圆图和工艺数据使用的Overlay配置。

## English

Adds semiconductor physical master data for wafer binning and overlay configuration.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
