# ss_TrackLabel → HAS_SS_LABEL_TYPE → ss_LabelType

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[ss_TrackLabel]`（别名 `src`）
- 目标表：`[ss_LabelType]`（别名 `tgt`）
- JOIN 条件：`src.[ss_LabelTypeId] = tgt.[ss_LabelTypeId]`
- 物理外键：`[ss_TrackLabel].[ss_LabelTypeId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [ss_TrackLabel] AS src
LEFT JOIN [ss_LabelType] AS tgt
    ON src.[ss_LabelTypeId] = tgt.[ss_LabelTypeId]
WHERE src.[ss_TrackLabelId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`ss_TrackLabel --[HAS_SS_LABEL_TYPE]--> ss_LabelType`
- 基数：`MANY_TO_ONE`
- 物理定义：`ss_TrackLabel.ss_LabelTypeId`
- 源表主键：`ss_TrackLabel.ss_TrackLabelId`
- 目标表主键：`ss_LabelType.ss_LabelTypeId`
