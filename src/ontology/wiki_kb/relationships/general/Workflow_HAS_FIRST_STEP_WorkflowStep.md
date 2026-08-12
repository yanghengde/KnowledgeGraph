# Workflow → HAS_FIRST_STEP → WorkflowStep

> **产品线**: 通用 (无产品线)  
> **基数**: ONE_TO_ONE  
> **生成时间**: 2026-05-06  
> **来源**: LLM 自动生成


## SQL 关联示例

### 物理关联

- 源表：`[Workflow]`（别名 `src`）
- 目标表：`[WorkflowStep]`（别名 `tgt`）
- JOIN 条件：`src.[FirstStepId] = tgt.[WorkflowStepId]`
- 物理外键：`[Workflow].[FirstStepId]`

### 查询示例

```sql
SELECT
    src.*,
    tgt.*
FROM [Workflow] AS src
LEFT JOIN [WorkflowStep] AS tgt
    ON src.[FirstStepId] = tgt.[WorkflowStepId]
WHERE src.[WorkflowId] = @SourceId;
```

> `LEFT JOIN` 会保留没有关联记录的源对象；如果只需要已建立该关系的数据，可改为 `INNER JOIN`。`@SourceId` 是查询参数，请使用参数化查询传值。

## 关系说明

在 Siemens Opcenter (Camstar) MES 中，一个 Workflow（工作流）由多个有序或并行的 WorkflowStep（工作流步骤）组成。`HAS_FIRST_STEP` 关系用于明确指定该 Workflow 的起始步骤——即流程执行时第一个被激活的节点。由于基数为 `ONE_TO_ONE`，每个 Workflow 只能拥有一个 “第一步”，且该步骤必须唯一指向一个 WorkflowStep 实例。

这一关系是工作流建模的基础：没有定义起始步骤的工作流无法被有效启动。在实际 Opcenter 模型中，WorkflowStep 可以配置前置条件、执行动作、分支逻辑等，而 `HAS_FIRST_STEP` 则决定了执行引擎从何处开始遍历步骤图。对于通用（无产品线）场景，此关系适用于任何需要定义过程顺序的领域，如生产工序、检验步骤、返工路径或审批流程。

## 业务场景

### 何时需要配置此关系？

1. **新建一个生产工作流**：当您需要定义从原材料投入到成品产出的完整加工顺序时，必须指定第一个工序（如 “上线前检查” 或 “投料”）作为起始步骤。
2. **修改现有工作流的起点**：因工艺变更需要调整流程的起始点（例如将 “自动扫描” 改为 “人工录入批次号”），则需重新配置 `HAS_FIRST_STEP`。
3. **复用工作流模板**：当从一个通用模板复制工作流并为其分配不同的首个执行步骤时（例如同一条产线加工不同产品，起始步骤可能不同），此关系用于解耦模板与具体实例。

### 通用 (无产品线) 典型示例

假设您需要为一条通用装配线创建一个名为 “Assembly_Workflow” 的工作流，其第一步为 “Load_Pallet”（装载托盘）。操作步骤如下（通过 Opcenter Modeling 或 Web UI）：

1. **创建 WorkflowStep**  
   - 导航至 WorkflowStep 对象，新建一个步骤，名称为 “Load_Pallet”，描述为 “将空托盘放置到起始位置”。
   - 配置该步骤的 Execution Type 为 “User Task”，并关联一个 “托盘装载” 的 Standard Operation。

2. **创建 Workflow**  
   - 新建 Workflow 对象，名称为 “Assembly_Workflow”，描述为 “通用装配流水线工作流”。

3. **建立 HAS_FIRST_STEP 关系**  
   - 在 Workflow 的 First Step 属性中，选择刚才创建的 “Load_Pallet” WorkflowStep。
   - 保存并验证：系统应提示 “First Step 已成功关联”。

4. **验证关系**  
   - 通过 Opcenter API 或 UI 查看该 Workflow 的 “First Step” 字段，确认显示为 “Load_Pallet”。
   - 在事务测试中启动该工作流，系统应自动将当前步骤设置为 “Load_Pallet”，并显示装载托盘的任务。

## 配置要点

1. **唯一性约束**：每个 Workflow 只能有一个 `HAS_FIRST_STEP`，如果尝试设置第二个，系统会覆盖原来的值或抛出验证错误。
2. **步骤必须存在**：所引用的 WorkflowStep 必须已在系统中存在，且处于 “Active” 或 “Enabled” 状态，否则关系无法保存。
3. **步骤独立于工作流**：一个 WorkflowStep 可以被多个 Workflow 引用为第一步，但通常建议避免此设计，以免造成逻辑混乱。
4. **版本管理**：如果对 Workflow 进行版本升级，新版本的工作流需重新指定 `HAS_FIRST_STEP`，旧版本的起始步骤不会自动继承。
5. **与步骤类型的关系**：起始步骤不能是 “Wait” 或 “Stop” 类型，必须是一个可执行的步骤（如 User Task、Auto Task、Gateway）。
6. **图形建模工具**：在 Opcenter Modeling 工作流设计器中，拖拽第一个步骤到画布后，系统会自动将 `HAS_FIRST_STEP` 设置为该步骤；手动删除或替换该步骤时需同步更新关系。
7. **避免循环依赖**：起始步骤的前置步骤列表（Preceding Steps）必须为空，否则工作流启动时会因找不到前序步骤而报错。
8. **国际化/多语言**：Workflow 和 WorkflowStep 的名称支持多语言，但 `HAS_FIRST_STEP` 的引用是通过对象的 Internal ID 实现的，与显示语言无关。

## 常见问题 FAQ

**Q: 如果我删除作为第一步的 WorkflowStep，会发生什么？**  
A: 系统会阻止直接删除被引用的 WorkflowStep，并提示 “该步骤已被用作某个工作流的第一步”。您需要先移除 Workflow 中的 `HAS_FIRST_STEP` 关联（设置为空或替换为其他步骤），然后才能删除该步骤。

**Q: 能否在运行时动态更改某个 Workflow 实例的第一步？**  
A: 不可以。`HAS_FIRST_STEP` 是建模时定义的静态关系，运行时实例的起始步骤由模型定义决定。如果需要不同的起点，应创建多个工作流版本或使用 Workflow Variant。

**Q: 一个工作流可以没有第一步吗？**  
A: 技术上允许创建不指定 `HAS_FIRST_STEP` 的工作流，但该工作流将无法被任何 Transaction 启动。建议在创建 Workflow 后立即配置第一步，或者在 Step Editor 中明确第一步后保存。
