# HistoryMainline → HAS_BATCH → Container

> **产品线**: 通用 (无产品线)
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-08-04
> **来源**: 物理 Schema + LLM

## 关系说明

在 Siemens Opcenter (Camstar) MES 的数据模型中，`HistoryMainline --[HAS_BATCH]--> Container` 定义了主历史记录（HistoryMainline）与容器（Container）之间的归属关系。每一条 HistoryMainline 记录代表一次针对某个业务对象（如 Container、Component 或 Resource）执行的服务（Service）调用痕迹，而 HAS_BATCH 关系将这种痕迹关联到具体执行批次所在的 Container 上。由于基数关系为 MANY_TO_ONE，意味着多个历史记录可以归属于同一个 Container，这正符合实际生产中一个 Container（如一个生产批次）在其生命周期内会经历大量服务操作的事实。

从通用 Camstar/Opcenter 本体视角来看，这个关系是“可追溯性”（Traceability）的基础骨架。Container 是物料流转的核心载体——它可以是单个物料、批次、装箱或工单；而 HistoryMainline 则是每一次业务操作留下的“黑匣子”记录。当 MES 执行诸如“物料接收”“工序报工”“质检放行”“包装”等服务时，系统自动在 HistoryMainline 中写入一条历史记录，并通过 HAS_BATCH 将记录指向当前操作的 Container。由此，业务用户可以从任一 Container 出发，回溯其从上线到完工的全部操作时间线。

该关系本身是系统自动维护的，建模人员通常不需要手工创建或删除实例。其核心价值在于：它为后续的电子批记录（EBR）、批次族谱查询、失效分析、质量追溯和监管合规审计提供了标准化的数据入口。理解该关系的语义，有助于正确设计自定义服务、事件订阅以及查询面板，确保在扩展系统功能时不会破坏追溯链的完整性。

## 业务场景

### 何时需要配置此关系？

- **生产追溯与反查**：当产线发生质量异常（如某道工序参数超差），质量工程师需要快速定位“哪些 Container 受影响”，此时必须通过 HAS_BATCH 从 HistoryMainline 反查所有关联的 Container，构建影响范围清单。
- **批次族谱（Genealogy）构建**：在制药或电子行业，需要完整记录一个 Container 从原材料入库到成品发货的全部历史操作。HAS_BATCH 支撑了“由容器查历史”和“由历史查容器”的双向导航，是族谱展示页面的核心数据来源。
- **电子批记录（EBR）合规**：审计要求每一批产品都有不可篡改的生产过程记录。每次服务执行产生 HistoryMainline 记录并关联到 Container，构成完整的电子签名与审计轨迹，满足 21 CFR Part 11 等法规要求。

### 通用 (无产品线) 典型示例

**场景：生产工单（Container）按流程执行多个工序，并追踪其完整历史。**

1. 计划员在 Opcenter 中创建生产工单，系统自动生成一个 Container（如工单号 `WO-2024-001`）。
2. 操作员在产线终端执行“开始生产”服务（Service: `Start Production`）。系统在 HistoryMainline 中写入一条记录（`History` 实例），并自动通过 HAS_BATCH 关联到 `WO-2024-001`。
3. 当物料经过第 10 道工序，操作员执行“工序完工”服务（Service: `Complete Operation`），输入实际数量、设备号及操作员电子签名。再次生成一条 HistoryMainline 记录，关联同一个 Container。
4. 质量部门执行“批次放行”（Service: `Release Container`）服务，生成包含放行结论和检验数据的另一条历史记录。
5. 三个月后，客户投诉该批次产品外观异常。质量工程师在 Opcenter 的“Container History”查询页面输入 `WO-2024-001`，系统通过 HAS_BATCH 关系在毫秒内返回该 Container 的全部 47 条 HistoryMainline 记录，逐条查看开始时间、操作人、设备参数及签核数据，最终定位到第 10 道工序的烘干温度偏差。

## 配置要点

1. **不要手工创建 HistoryMainline 实例**：该关系由 Opcenter 服务框架在运行时自动维护，手工创建会导致数据不一致和审计失败。所有历史记录应通过标准 Service 执行产生。
2. **确保 Service 正确传递 Container 引用**：在自定义服务中，必须将 `Container` 参数正确赋值给 `HistoryMainline` 的 `Container` 字段（即 HAS_BATCH 的目标端），否则历史记录会成为“孤儿记录”，无法关联到批次。
3. **注意 Container 对象的选择范围**：HAS_BATCH 可以关联到任意类型的 Container（如```Product``、``Batch``、``WorkOrder``）。在建模自定义操作时，应明确测试目标 Container 的类型，避免类型不匹配造成的运行时错误。
4. **关注历史记录的清理策略**：生产系统中 HistoryMainline 数据增长极快。虽然通常不配置自动删除，但需通过归档任务（如 Opcenter Archive Service）定期归档旧数据，否则会影响查询性能和数据库空间。
5. **利用事件订阅（Event Subscription）补充业务上下文**：如果需要在历史记录中额外保存业务字段（如批次备注、订单优先级），可通过事件订阅在 Service 执行完成后向 HistoryMainline 附属的对象写入扩展数据，但不建议修改 HAS_BATCH 关系本身。
6. **查询时优先使用 Container 视角**：对于批量追溯查询，应通过 Container 的导航属性获取 HistoryMainline 集合（而不是反向遍历），以获得更优的查询性能和更直观的建模语义。
7. **遵循工厂模型的数据范围约束**：在 Model 配置中，确保该关系没有不必要的模型限制（如按站点、工厂过滤），否则可能导致在多站点环境中历史记录无法跨站关联。
8. **在版本升级和迁移时验证关系完整性**：从旧版本 Camstar 升级至 Opcenter 时，应运行数据一致性检查脚本，确认所有 HistoryMainline 记录的 HAS_BATCH 引用均有效，避免因为历史数据迁移问题破环追溯链。

## 常见问题 FAQ

**Q: 为什么我在数据库中看到某些 HistoryMainline 记录的 Container 字段为空？**
A: 这是正常现象。并非所有服务都针对 Container 执行。例如，针对 Resource（设备）或 Employee（员工）的服务（如“设备点检”）所产生的历史记录，其 Container 引用可能为空。这类记录不参与批次追溯，但仍然是完整的审计轨迹。如果你在追溯查询时发现 Container 相关历史缺失，应先确认对应服务是否属于 Container 类服务。

**Q: 如何在 Opcenter 界面上查看某一个 Container 的全部历史记录？**
A: 有两条路径：第一种，在“Container 维护”页面（Container Maintenance）中打开目标 Container，然后点击“历史”（History）页签，系统会通过 HAS_BATCH 关系自动列出全部关联的 HistoryMainline 记录；第二种，通过“历史查询”页面（History Inquiry）输入 Container 名称（如工单号）进行搜索，在查询结果中筛选出 HAS_BATCH 关联的记录。第二条路径适合跨 Container 的批量追溯场景。

**Q: 我能否将一条 HistoryMainline 记录同时关联到两个 Container？**
A: 理论上不能。HAS_BATCH 是一对多关系的多端导航属性（MANY_TO_ONE），一条 HistoryMainline 记录只能指向一个 Container。如果你遇到一条记录需要关联两个批次的情况（例如“批次合并”操作），正确的建模方式是在 Service 中创建两条 HistoryMainline 记录——各关联一个 Container，或者使用中间对象（如 Transaction 对象）来记录批次间的关联关系，而不是试图修改 HAS_BATCH 的基数约束。