# ElectronicProcedureBase → HAS_REV_OF_RCD → ElectronicProcedure

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[ElectronicProcedureBase]`（别名 `src`）
- 目标表：`[ElectronicProcedure]`（别名 `tgt`）
- JOIN 条件：`src.[RevOfRcdId] = tgt.[ElectronicProcedureId]`
- 物理外键：`[ElectronicProcedureBase].[RevOfRcdId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [ElectronicProcedureBase] AS src
LEFT JOIN [ElectronicProcedure] AS tgt
    ON src.[RevOfRcdId] = tgt.[ElectronicProcedureId]
WHERE src.[ElectronicProcedureBaseId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`ElectronicProcedureBase --[HAS_REV_OF_RCD]--> ElectronicProcedure`
- 基数：`MANY_TO_ONE`
- 物理定义：`ElectronicProcedureBase.RevOfRcdId`
- 源表主键：`ElectronicProcedureBase.ElectronicProcedureBaseId`
- 目标表主键：`ElectronicProcedure.ElectronicProcedureId`
