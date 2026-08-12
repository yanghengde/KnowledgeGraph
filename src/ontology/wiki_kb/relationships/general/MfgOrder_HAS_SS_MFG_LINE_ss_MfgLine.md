# MfgOrder → HAS_SS_MFG_LINE → ss_MfgLine

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[MfgOrder]`（别名 `src`）
- 目标表：`[ss_MfgLine]`（别名 `tgt`）
- JOIN 条件：`src.[ss_MfgLineId] = tgt.[ss_MfgLineId]`
- 物理外键：`[MfgOrder].[ss_MfgLineId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [MfgOrder] AS src
LEFT JOIN [ss_MfgLine] AS tgt
    ON src.[ss_MfgLineId] = tgt.[ss_MfgLineId]
WHERE src.[MfgOrderId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`MfgOrder --[HAS_SS_MFG_LINE]--> ss_MfgLine`
- 基数：`MANY_TO_ONE`
- 物理定义：`MfgOrder.ss_MfgLineId`
- 源表主键：`MfgOrder.MfgOrderId`
- 目标表主键：`ss_MfgLine.ss_MfgLineId`
