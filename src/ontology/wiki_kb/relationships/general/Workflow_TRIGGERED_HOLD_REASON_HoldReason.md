# Workflow → TRIGGERED_HOLD_REASON → HoldReason

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-05-28
> **来源**: LLM 自动生成

## 关系说明

此关系定义了一个工作流（Workflow）中的特定节点（Node）在执行“冻结（Hold）”操作时，所关联的冻结原因（HoldReason）。在 Opcenter MES 中，当工作流节点配置的“WIP 消息”触发了一个 `Hold` 操作时，系统需要自动为该冻结操作选择一个标准原因代码。此关系正是用于将工作流节点与一个预设的 HoldReason 实例绑定，从而实现冻结操作的自动化和标准化。

在通用（无产品线）场景中，此关系扮演了“业务规则链接”角色。它使得 MES 管理员可以通过建模配置，将特定的业务场景（如“来料检验不合格”、“设备故障”、“工艺参数异常”）与一个固定的冻结原因关联起来。一旦工作流中的判定逻辑（如检验失败）导致节点执行“Hold”动作，系统就会自动引用此处配置的 HoldReason，无需操作员手动选择，确保了业务流程的严谨性和数据一致性。

一个 Workflow 可以配置多个节点，每个节点都可能触发 Hold 操作，但每个节点只能对应一个 HoldReason（MANY_TO_ONE 的 User Perspective：多个 Workflow 节点可指向同一个 HoldReason，反之一个 HoldReason 可被多个节点引用）。这降低了重复配置的工作量，便于统一管理“最常见”的冻结原因。

## 业务场景

### 何时需要配置此关系？

1.  **自动化质量门控**：当 Workflow 中包含“检验”或“测试”节点，且检验结果判定为“不合格（Fail）”时，需要自动将当前 WIP 对象（如批次、工单）冻结。此时需为 Workflow 中触发 Hold 的节点配置一个“检验不合格”的 HoldReason。

2.  **设备故障触发冻结**：Workflow 中集成了“自动设备接口（SECS/GEM）”节点，当设备上报“故障（Equipment Fault）”信号时，Workflow 需要自动冻结在其上加工的对象。此时可配置“设备故障”为关联的 HoldReason，以便后续工程人员快速识别冻结原因。

3.  **工艺参数异常**：Workflow 中包含“工艺参数验证”节点，当采集到的实时工艺参数（如温度、压力）超出规格范围时，自动触发冻结。此时需配置一个“工艺参数超规”的 HoldReason，配合 Workflow 的自动判定逻辑，实现即时拦截。

### 通用 (无产品线) 典型示例

**场景**：在半导体封装测试环境中，一个名为“FinalTestWorkflow”的工作流包含“功能测试节点”。该节点通过设备接口自动执行测试，并将结果（Pass/Fail）写回 MES。当测试结果为 Fail 时，Workflow 需要自动将当前批次置于 Hold 状态，并标记原因为“功能测试不良”。

**配置步骤**：
1.  在 Opcenter Modeling 中，创建或确认一个 HoldReason。例如：`HoldReason.Code = "FT_FAIL"`, `HoldReason.Description = "功能测试不良"`。建议设置 `HoldReason.IsPreassigned = True` 以要求用户后续进一步输入，或设置为 `False` 让系统自动分配。
2.  在 Workflow“FinalTestWorkflow”的“功能测试节点”属性中，定位到“WIP Message”或“Triggers”选项卡。
3.  新增一个 WIP 消息，消息类型选择“Hold”。
4.  在“Hold Reason”字段中，选择刚才创建的 `FT_FAIL` 冻结原因。
5.  保存生效。

**结果**：当批次在该节点触发 Hold 动作时，系统会自动分配 `FT_FAIL` 作为冻结原因。操作员在“待处理冻结”队列中可以看到该批次，并立即知晓原因是功能测试失败。

## 配置要点

1.  **HoldReason 的初始化状态**：创建的 HoldReason 需要设置初始分配状态（`Preassigned`）。若设为 `True`，冻结后用户必须输入备注或前置原因；若设为 `False`，则系统直接锁定，适合完全自动化的场景。
2.  **工作流节点差异化**：即使是同一个 Workflow，不同的节点触发 Hold，应该配置不同的 HoldReason，以精确反映冻结发生的工艺步骤。切勿将所有触发冻节点都指向同一个通用原因。
3.  **错误处理**：配置 HoldReason 后，建议在 Workflow 节点中添加 Error Handling，确保当无法分配 HoldReason 时（如原因已被禁用），Workflow 不会失败，而是记录异常日志。
4.  **多语言支持**：HoldReason 的描述（Description）支持多语言。在全球化部署中，应确保多语言描述被正确设置，以便不同地区的用户理解。
5.  **流程状态一致性**：HoldReason 的状态（有效/无效）应与 Workflow 版本绑定。确保 Workflow 的新版本发布时，关联的 HoldReason 仍然有效，绝不要直接删除一个正在被 Workflow 引用的 HoldReason。
6.  **命名规范**：建议采用有意义的命名约定，例如 `{工艺节点}_{原因}`（如 `SolderPrint_Short`），便于在 Workflow 维护和报表分析时快速识别。
7.  **避免过度配置**：不要为每一个细微的异常原因都创建 HoldReason。应遵循“80/20”原则，只对最重要的、可预期且常见的自动化场景配置此关系。不常见的异常可留给操作员手动选择原因。

## 常见问题 FAQ

**Q: 如果我不配置这个关系，工作流还能冻结对象吗？**
A: 能。当 Workflow 节点触发 Hold 操作但未关联 HoldReason 时，系统会弹出选择对话框，要求操作员手动选择一个 HoldReason。配置此关系是为了实现自动化，减少人工干预。

**Q: 配置了此关系后，操作员还能更改冻结原因吗？**
A: 取决于 Workflow 中“WIP Message”的具体配置和系统设置。通常，如果设置 `Preassigned = False`，操作员可以更改。如果设置 `Preassigned = True` 且 Workflow 消息配置为“强制”，则操作员无法更改。建议根据业务合规性要求进行设置。

**Q: 多个不同的工作流（Workflow）可以共用一个 HoldReason 吗？**
A: 可以，这正是 MANY_TO_ONE 关系的优势。例如，不同产品线的检验工作流都可以统一指向“检验不合格”的 HoldReason，便于报表汇总分析。但需注意，如果不同产品线对原因有更细粒度的要求，建议创建差异化的 HoldReason。