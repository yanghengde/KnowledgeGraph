# ResourceDef → HAS_SCS_INQ_INNER_INPUT_CARRIER_FAMIL → ResourceFamily

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[ResourceDef]`（别名 `src`）
- 目标表：`[ResourceFamily]`（别名 `tgt`）
- JOIN 条件：`src.[scsInqInnerInputCarrierFamilId] = tgt.[ResourceFamilyId]`
- 物理外键：`[ResourceDef].[scsInqInnerInputCarrierFamilId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [ResourceDef] AS src
LEFT JOIN [ResourceFamily] AS tgt
    ON src.[scsInqInnerInputCarrierFamilId] = tgt.[ResourceFamilyId]
WHERE src.[ResourceId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`ResourceDef --[HAS_SCS_INQ_INNER_INPUT_CARRIER_FAMIL]--> ResourceFamily`
- 基数：`MANY_TO_ONE`
- 物理定义：`ResourceDef.scsInqInnerInputCarrierFamilId`
- 源表主键：`ResourceDef.ResourceId`
- 目标表主键：`ResourceFamily.ResourceFamilyId`
