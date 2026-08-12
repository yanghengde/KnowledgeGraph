# LD 扩展本体建模说明 / LD Extension Ontology Modeling

## 中文

本模块根据新版 `Database_Tables.csv` 与 `Database_Fields.csv` 建模 Workspace 200 中以 `ld` 或 `A_ld` 开头的 24 个物理 CDO，覆盖：

- CSAM 数据与验证；
- 物料退回、物料请求及其历史明细；
- 返工状态及重入工作流；
- 检验计划、检验任务、WIP 数据及历史；
- 容器、标识变更和关联历史；
- 模型计划。

建模规则：

- 每个物理 CDO 映射为一个 `OntologyClass`。
- 普通字段按照 CSV `DataType` 映射为 String、Boolean、Integer、Float 或 DateTime。
- `IsForeignKey=True` 且存在 `FKTableName` 的字段映射为 Navigation。
- 主键与 `CDOTypeId`、`ChangeCount`、`ExportImportKey` 等系统字段不进入属性集合。
- 仅当外键目标已存在于本体中时创建 `ONTOLOGY_RELATION`，避免产生无效端点。

## English

This module models the 24 Workspace 200 physical CDOs whose names begin with `ld` or `A_ld`, based on the current database CSV schema.

- Each physical CDO is represented as an `OntologyClass`.
- Scalar types follow the CSV `DataType` mapping.
- Physical foreign keys with a valid `FKTableName` are represented as Navigation properties.
- Primary keys and infrastructure fields are excluded.
- Ontology relationships are emitted only when the target class is modeled.
