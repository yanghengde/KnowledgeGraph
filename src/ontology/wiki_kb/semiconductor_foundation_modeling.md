# 半导体基础主数据建模 / Semiconductor Foundation Master-Data Modeling

## 中文

本批次覆盖半导体访问权限、产品线、工艺分类、设备与工序分组、光罩及物料分类基础主数据。

本模块完全依据 `Database_Tables.csv` 和 `Database_Fields.csv` 生成。主键、`CDOTypeId`、`ChangeCount` 和 `ExportImportKey` 作为系统字段过滤；所有物理外键均映射为 `Navigation`。

### 实体

- `A_SetupAccess`（半导体建模访问权限）：定义半导体建模对象使用的访问权限。
- `A_ProductLine`（半导体产品线）：定义半导体制造产品线主数据。
- `A_ProcessArea`（半导体工艺区域）：定义半导体工艺区域分类。
- `A_ProcessType`（半导体工艺类型）：定义半导体生产使用的工艺类型。
- `A_ProcessCode`（半导体工艺代码）：定义半导体制造工艺代码目录。
- `A_MachineGroup`（半导体机台组）：定义半导体生产机台的业务分组。
- `A_OperationGroup`（半导体工序组）：定义半导体工序的业务分组。
- `A_MaskSet`（光罩集合）：定义半导体制造使用的光罩集合。
- `A_MaskLayer`（光罩层）：定义半导体光罩层主数据。
- `A_MaterialCategory`（半导体物料类别）：定义半导体物料类别目录。
- `A_MaterialType`（半导体物料类型）：定义半导体物料消耗、序列化和批次属性匹配规则。

## English

This batch covers semiconductor setup access, product lines, process classification, equipment and operation groups, masks, and material classification.

The module is generated directly from the semiconductor physical schema. Infrastructure fields are excluded and every physical foreign key is represented as a Navigation property.
