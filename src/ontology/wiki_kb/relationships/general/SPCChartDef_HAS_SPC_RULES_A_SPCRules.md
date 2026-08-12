# SPCChartDef → HAS_SPC_RULES → A_SPCRules

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[SPCChartDef]`（别名 `src`）
- 目标表：`[A_SPCRules]`（别名 `tgt`）
- JOIN 条件：`src.[SPCRulesId] = tgt.[SPCRulesId]`
- 物理外键：`[SPCChartDef].[SPCRulesId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [SPCChartDef] AS src
LEFT JOIN [A_SPCRules] AS tgt
    ON src.[SPCRulesId] = tgt.[SPCRulesId]
WHERE src.[SPCChartDefId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`SPCChartDef --[HAS_SPC_RULES]--> A_SPCRules`
- 基数：`MANY_TO_ONE`
- 物理定义：`SPCChartDef.SPCRulesId`
- 源表主键：`SPCChartDef.SPCChartDefId`
- 目标表主键：`A_SPCRules.SPCRulesId`
