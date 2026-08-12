# Workflow → HAS_GATE → ProcessingGate

> **产品线**: 通用 (无产品线)
> **基数**: ONE_TO_MANY
> **生成时间**: 2026-05-23
> **来源**: LLM 自动生成

## 关系说明

此关系定义了一个 Workflow（工作流）可以关联零个或多个 ProcessingGate（加工闸门），每个 ProcessingGate 仅属于一个 Workflow。ProcessingGate 是工作流中的关键控制节点，用于在物料流转路径上插入决策点、状态检查、自动触发执行或人工干预操作。在 Opcenter Execution (原 Camstar) 通用建模中，Workflow 通常代表一组有序的操作步骤或路径，而 ProcessingGate 则作为这些步骤间的“闸口”，负责在物料进入或离开某个阶段时执行预设逻辑（如校验、激活子工作流、发送事件等）。

在通用场景（不绑定特定产品线）中，此关系使模型具备高度的灵活性和可扩展性。例如，一个名为“AssemblyFlow”的工作流可关联多个不同类型的 ProcessingGate（如“InspectionGate”、“TestGate”、“ReworkGate”），每个闸门独立配置触发条件、执行动作和后续路由逻辑。此设计将工作流的线性序列与闸门的条件分支解耦，便于实现复杂生产流程中的动态路径选择和自动化控制。

由于基数为 ONE_TO_MANY，建模时需注意一个 ProcessingGate 不能同时隶属于多个 Workflow，但同一个 Workflow 允许按顺序或并行挂载多个闸门。这种结构适用于从简单流水线到多分支并行生产的各类业务场景。

## 业务场景

### 何时需要配置此关系？
- **多路径路由**：当生产流程中存在基于物料属性、质量结果或设备状态的分支决策时，需要为 Workflow 配置 ProcessingGate 来定义不同分支的进入/退出条件。
- **工序间自动触发**：需要在工序切换时自动执行特定逻辑（如数据采集、通知、设备联锁），可在 Workflow 中插入 ProcessingGate 作为执行节点。
- **权限与防错控制**：对于需要操作员在特定步骤前完成签核、校验或培训认证的业务场景，可通过 ProcessingGate 绑定用户审批步骤来强制控制流程走向。

### 通用 (无产品线) 典型示例

**示例：电子产品组装线的主流程建模**

1. 创建一个名为“MainAssemblyFlow”的标准 Workflow。
2. 在 Workflow 步骤序列中新增三个 ProcessingGate：
   - “PreSolderCheckGate”：放置于焊接工序前，配置条件：仅当物料序列号已通过前站检查（属性 `PrevCheckPassed = True`）时允许进入焊接工序。
   - “PostTestGate”：放置于测试工序后，配置两条分支：若测试通过，路由至“PassRoute”；若失败，路由至“ReworkRoute”。
   - “FinalPackGate”：放置于包装前，自动触发“InventoryUpdate”事件，并调用一个 DataCollection（数据收集）模板要求操作员录入包装数量。
3. 在 Opcenter Modeler 中：右键 Workflow → “新建 ProcessingGate” → 分别填写门名称、执行顺序、条件表达式及后续路由。每个闸门的“关联 Workflow”字段自动指向“MainAssemblyFlow”。

**参数示例**（以 PreSolderCheckGate 为例）：
- Name: PreSolderCheckGate
- SequenceNumber: 10（表示执行顺序）
- ConditionExpression: `{MESPR}.Attributes.PrevCheckPassed == True`
- NextRoutingMethod: 指定路由目标为下一工序 ID。
- EnableAutomaticMove: True（满足条件时自动放行）

## 配置要点

1. **基数约束**：一个 ProcessingGate 只能关联一个 Workflow，但一个 Workflow 可以关联多个闸门。若需让闸门在不同工作流中复用，应复制闸门对象或通过 Workflow 分支设计实现。
2. **闸门执行顺序**：通过每个 ProcessingGate 的 `SequenceNumber` 属性控制其在 Workflow 中的执行顺序。当物料进入流程时，闸门按序号依次触发，序号可跳步，建议保留间隔便于后续插入。
3. **条件表达式编写**：条件表达式基于 MES 数据模型（如对象属性、容器状态）编写，推荐先在测试环境中验证表达式正确性。注意字段大小写敏感，可使用 `{MESPR}`、`{MESContainer}` 等内置变量。
4. **路由目标配置**：每个 ProcessingGate 必须指定 `NextRoutingMethod`（路由方法），常见选项为固定工序、表达式路由或基于资源的分发。若不配置，流程将无法继续。
5. **与 Workflow Step 的区别**：ProcessingGate 是额外的控制节点，不属于 Workflow 的标准步骤列表。它附着在 Workflow 的路径上，不影响步骤本身的属性，但可以阻断或分流物料。通常将其置于步骤之间，而不是替代步骤。
6. **版本管理**：对已发布的 Workflow 修改 ProcessingGate 配置时，需注意版本控制。新闸门或条件变更应通过模型版本升级（Model Revision）发布，避免影响正在执行的生产订单。
7. **性能影响**：每个 ProcessingGate 均会在物料流转时触发引擎执行。若闸门数量过多（如超过 50 个），或条件表达式涉及复杂跨对象查询，可能影响系统吞吐率。建议合并不必要的闸门，或使用“Branch Gate”等高级节点。
8. **撤销与回滚**：ProcessingGate 的默认执行是事务性的，若后续步骤回滚，闸门执行的动作（如状态修改、事件发送）不会自动逆转。需在自定义动作中设计补偿逻辑。

## 常见问题 FAQ

**Q1: 我能否在同一个 Workflow 中为不同的物料类型配置不同的 ProcessingGate 组合？**
A: 可以。ProcessingGate 本身可以通过条件表达式（`ConditionExpression`）判断物料属性（如产品类型、批次），从而实现仅对特定物料激活。也可以为不同产品创建不同版本的 Workflow，每个版本挂载各自所需的闸门。推荐使用表达式方式，以保持模型简洁。

**Q2: ProcessingGate 和 Workflow Step 中的 Entry/Exit Action 有何区别？**
A: Entry/Exit Action 是绑定到 Workflow Step 自身的脚本或事件，通过数据采集 (DataCollection) 触发。而 ProcessingGate 是独立于 Step 的控制节点，可以放置在步骤之间，不依赖于步骤的生命周期。Gate 更侧重于流程路由控制（条件放行、分流），而 Action 更侧重于步骤执行时的业务逻辑。通常两者可结合使用：Action 执行数据操作，Gate 控制下一步走向。

**Q3: 如果 ProcessingGate 的条件表达式返回 False，物料会停留在哪里？**
A: 若条件不满足且未配置“失败路由”，默认情况下物料会停留在 ProcessingGate 绑定的前一步骤（即流程路径上的上一个操作位置）并触发错误导致流程挂起。建议为每个 Gate 配置 `FalseRoutingMethod` 或启用重试策略，比如设置 `MaxRetries` 和 `RetryInterval`，或定义一条进入暂停队列的备选路由。

---
*本文档由 Siemens Opcenter MES 领域专家根据通用（无产品线）场景撰写，适用于 Camstar/Opcenter 本体建模参考。*