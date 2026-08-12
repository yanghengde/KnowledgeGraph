# A_WIPDataSetup → HAS_FAILURE_REASON → ResourceStatusReason

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[A_WIPDataSetup]`（别名 `src`）
- 目标表：`[ResourceStatusReason]`（别名 `tgt`）
- JOIN 条件：`src.[FailureReasonId] = tgt.[ResourceStatusReasonId]`
- 物理外键：`[A_WIPDataSetup].[FailureReasonId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [A_WIPDataSetup] AS src
LEFT JOIN [ResourceStatusReason] AS tgt
    ON src.[FailureReasonId] = tgt.[ResourceStatusReasonId]
WHERE src.[WIPDataSetupId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`A_WIPDataSetup --[HAS_FAILURE_REASON]--> ResourceStatusReason`
- 基数：`MANY_TO_ONE`
- 物理定义：`A_WIPDataSetup.FailureReasonId`
- 源表主键：`A_WIPDataSetup.WIPDataSetupId`
- 目标表主键：`ResourceStatusReason.ResourceStatusReasonId`
