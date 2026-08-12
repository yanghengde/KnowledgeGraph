# Workflow → HAS_WORKFLOW_BASE → WorkflowBase

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[Workflow]`（别名 `src`）
- 目标表：`[WorkflowBase]`（别名 `tgt`）
- JOIN 条件：`src.[WorkflowBaseId] = tgt.[WorkflowBaseId]`
- 物理外键：`[Workflow].[WorkflowBaseId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [Workflow] AS src
LEFT JOIN [WorkflowBase] AS tgt
    ON src.[WorkflowBaseId] = tgt.[WorkflowBaseId]
WHERE src.[WorkflowId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`Workflow --[HAS_WORKFLOW_BASE]--> WorkflowBase`
- 基数：`MANY_TO_ONE`
- 物理定义：`Workflow.WorkflowBaseId`
- 源表主键：`Workflow.WorkflowId`
- 目标表主键：`WorkflowBase.WorkflowBaseId`
