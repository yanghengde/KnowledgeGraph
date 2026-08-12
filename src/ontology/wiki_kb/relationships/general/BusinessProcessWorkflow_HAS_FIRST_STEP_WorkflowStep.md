# BusinessProcessWorkflow → HAS_FIRST_STEP → WorkflowStep

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[BusinessProcessWorkflow]`（别名 `src`）
- 目标表：`[WorkflowStep]`（别名 `tgt`）
- JOIN 条件：`src.[FirstStepId] = tgt.[WorkflowStepId]`
- 物理外键：`[BusinessProcessWorkflow].[FirstStepId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [BusinessProcessWorkflow] AS src
LEFT JOIN [WorkflowStep] AS tgt
    ON src.[FirstStepId] = tgt.[WorkflowStepId]
WHERE src.[BusinessProcessWorkflowId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`BusinessProcessWorkflow --[HAS_FIRST_STEP]--> WorkflowStep`
- 基数：`MANY_TO_ONE`
- 物理定义：`BusinessProcessWorkflow.FirstStepId`
- 源表主键：`BusinessProcessWorkflow.BusinessProcessWorkflowId`
- 目标表主键：`WorkflowStep.WorkflowStepId`
