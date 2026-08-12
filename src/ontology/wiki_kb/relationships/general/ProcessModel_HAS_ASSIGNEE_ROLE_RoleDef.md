# ProcessModel → HAS_ASSIGNEE_ROLE → RoleDef

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-07-28
> **来源**: 物理 Schema 自动生成

## SQL 关联示例

### 物理关联

- 源表：`[ProcessModel]`（别名 `src`）
- 目标表：`[RoleDef]`（别名 `tgt`）
- JOIN 条件：`src.[AssigneeRoleId] = tgt.[RoleId]`
- 物理外键：`[ProcessModel].[AssigneeRoleId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [ProcessModel] AS src
LEFT JOIN [RoleDef] AS tgt
    ON src.[AssigneeRoleId] = tgt.[RoleId]
WHERE src.[ProcessModelId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系事实

本页由本体关系和 `Database_Fields.csv` 自动生成，不包含未经物理 Schema 验证的业务推断。

- 本体关系：`ProcessModel --[HAS_ASSIGNEE_ROLE]--> RoleDef`
- 基数：`MANY_TO_ONE`
- 物理定义：`ProcessModel.AssigneeRoleId`
- 源表主键：`ProcessModel.ProcessModelId`
- 目标表主键：`RoleDef.RoleId`
