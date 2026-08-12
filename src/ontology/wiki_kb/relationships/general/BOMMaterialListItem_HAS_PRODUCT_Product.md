# BOMMaterialListItem → HAS_PRODUCT → Product

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[BOMMaterialListItem]`（别名 `src`）
- 目标表：`[Product]`（别名 `tgt`）
- JOIN 条件：`src.[ProductId] = tgt.[ProductId]`
- 物理外键：`[BOMMaterialListItem].[ProductId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [BOMMaterialListItem] AS src
LEFT JOIN [Product] AS tgt
    ON src.[ProductId] = tgt.[ProductId]
WHERE src.[BOMMaterialListItemId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`BOMMaterialListItem --[HAS_PRODUCT]--> Product`
- 基数：`MANY_TO_ONE`
- 物理定义：`BOMMaterialListItem.ProductId`
- 源表主键：`BOMMaterialListItem.BOMMaterialListItemId`
- 目标表主键：`Product.ProductId`
