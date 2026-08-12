# 半导体物理位置与资源BOM / Semiconductor Physical Position and Resource BOM

## 中文

补齐旧逻辑类在半导体套件中的明确物理替代实体，采用真实CDOName。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_PhysicalLocationPosition`（物理位置关联）：物理位置与位置定义之间的顺序关联明细。
- `A_PhysicalPosition`（物理位置定义）：定义可用于厂内物理位置配置的位置主数据。
- `A_ResourceBOM`（资源BOM）：资源所需物料清单的版本化定义。
- `A_ResourceBOMBase`（资源BOM基础）：资源BOM各修订版本的基础记录。

## English

Adds verified semiconductor physical replacements for legacy logical position and resource BOM classes.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
