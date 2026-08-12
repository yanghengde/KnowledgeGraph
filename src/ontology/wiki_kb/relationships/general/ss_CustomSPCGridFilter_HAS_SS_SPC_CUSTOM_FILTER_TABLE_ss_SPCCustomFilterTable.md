# ss_CustomSPCGridFilter → HAS_SS_SPC_CUSTOM_FILTER_TABLE → ss_SPCCustomFilterTable

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[ss_CustomSPCGridFilter]`（别名 `src`）
- 目标表：`[ss_SPCCustomFilterTable]`（别名 `tgt`）
- JOIN 条件：`src.[ss_SPCCustomFilterTableId] = tgt.[ss_SPCCustomFilterTableId]`
- 物理外键：`[ss_CustomSPCGridFilter].[ss_SPCCustomFilterTableId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [ss_CustomSPCGridFilter] AS src
LEFT JOIN [ss_SPCCustomFilterTable] AS tgt
    ON src.[ss_SPCCustomFilterTableId] = tgt.[ss_SPCCustomFilterTableId]
WHERE src.[ss_CustomSPCGridFilterId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`ss_CustomSPCGridFilter --[HAS_SS_SPC_CUSTOM_FILTER_TABLE]--> ss_SPCCustomFilterTable`
- 基数：`MANY_TO_ONE`
- 物理定义：`ss_CustomSPCGridFilter.ss_SPCCustomFilterTableId`
- 源表主键：`ss_CustomSPCGridFilter.ss_CustomSPCGridFilterId`
- 目标表主键：`ss_SPCCustomFilterTable.ss_SPCCustomFilterTableId`
