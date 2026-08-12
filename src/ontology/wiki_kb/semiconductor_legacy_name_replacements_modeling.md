# 半导体旧名称物理替代 / Semiconductor Legacy Name Replacements

## 中文

补齐通过字段语义确认的旧逻辑名称对应物理实体。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `ComponentDefectReason`（组件缺陷原因）：组件缺陷业务原因的物理主数据。
- `QtyAdjustGroup`（数量调整原因组）：数量调整原因的物理分组实体。

## English

Adds physical entities confirmed as replacements for legacy logical names through field-level comparison.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
