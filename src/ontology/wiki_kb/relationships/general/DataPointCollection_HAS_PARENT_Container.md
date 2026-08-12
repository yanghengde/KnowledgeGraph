# DataPointCollection → HAS_PARENT → Container

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[DataPointCollection]`（别名 `src`）
- 目标表：`[Container]`（别名 `tgt`）
- JOIN 条件：`src.[ParentId] = tgt.[ContainerId]`
- 物理外键：`[DataPointCollection].[ParentId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [DataPointCollection] AS src
LEFT JOIN [Container] AS tgt
    ON src.[ParentId] = tgt.[ContainerId]
WHERE src.[DataPointCollectionId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`DataPointCollection --[HAS_PARENT]--> Container`
- 基数：`MANY_TO_ONE`
- 物理定义：`DataPointCollection.ParentId`
- 源表主键：`DataPointCollection.DataPointCollectionId`
- 目标表主键：`Container.ContainerId`
