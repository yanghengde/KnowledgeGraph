# Employee → HAS_TRAINING_PLAN → TrainingPlan

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[Employee]`（别名 `src`）
- 目标表：`[TrainingPlan]`（别名 `tgt`）
- JOIN 条件：`src.[TrainingPlanId] = tgt.[TrainingPlanId]`
- 物理外键：`[Employee].[TrainingPlanId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [Employee] AS src
LEFT JOIN [TrainingPlan] AS tgt
    ON src.[TrainingPlanId] = tgt.[TrainingPlanId]
WHERE src.[EmployeeId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`Employee --[HAS_TRAINING_PLAN]--> TrainingPlan`
- 基数：`MANY_TO_ONE`
- 物理定义：`Employee.TrainingPlanId`
- 源表主键：`Employee.EmployeeId`
- 目标表主键：`TrainingPlan.TrainingPlanId`
