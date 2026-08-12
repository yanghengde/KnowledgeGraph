# HistoryMainline → HAS_RESOURCE_STATUS_CODE → ResourceStatusCode

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[HistoryMainline]`（别名 `src`）
- 目标表：`[ResourceStatusCode]`（别名 `tgt`）
- JOIN 条件：`src.[ResourceStatusCodeId] = tgt.[ResourceStatusCodeId]`
- 物理外键：`[HistoryMainline].[ResourceStatusCodeId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [HistoryMainline] AS src
LEFT JOIN [ResourceStatusCode] AS tgt
    ON src.[ResourceStatusCodeId] = tgt.[ResourceStatusCodeId]
WHERE src.[HistoryMainlineId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`HistoryMainline --[HAS_RESOURCE_STATUS_CODE]--> ResourceStatusCode`
- 基数：`MANY_TO_ONE`
- 物理定义：`HistoryMainline.ResourceStatusCodeId`
- 源表主键：`HistoryMainline.HistoryMainlineId`
- 目标表主键：`ResourceStatusCode.ResourceStatusCodeId`
