# Workflow → AFFECTED_BY → ChangePackage

> **产品线**: 洗碗机产线  
> **基数**: MANY_TO_MANY  
> **生成时间**: 2026-05-06  
> **来源**: LLM 自动生成

## 关系说明

在 Siemens Opcenter MES 中，`Workflow` 代表产品在生产过程中必须遵循的标准化工艺路线（如装配、测试、包装等步骤的顺序和参数）。`ChangePackage` 则是一个用于集中管理工程变更、工艺优化或客户特殊要求的容器，可以包含多个变更命令（Change Order）及其关联的物料、文档、设备参数等。`AFFECTED_BY` 关系表示一个或多个 `Workflow` 正在或将要受到某个 `ChangePackage` 的影响，同时一个 `ChangePackage` 也可能同时作用于多个 `Workflow`。该关系的本质是记录变更的传播范围，确保生产执行时能够准确切换到受影响的工艺版本。

在洗碗机产线环境下，这一关系尤为重要。洗碗机产品迭代频繁，例如内胆材料从不锈钢改为涂层材料、喷淋臂结构优化、能效等级升级等，都会直接影响对应的装配工作流、气密性测试工作流或最终包装工作流。通过 `AFFECTED_BY` 关系，MES 系统能够自动识别哪些作业中心（如预装线、总装线、测试站）需要执行新版本的 Workflow，从而保证变更的闭环追溯和防错执行。

## 业务场景

### 何时需要配置此关系？

1. **因材料或部件变更导致工艺路线调整**：例如洗碗机内胆材质由普通不锈钢改为抗菌涂层不锈钢，导致内胆清洗和烘干工序的作业参数（温度、时间、清洁剂种类）发生变化。此时需要将受影响的“内胆装配 Workflow”与对应的材料变更 `ChangePackage` 关联。

2. **引入新型号或产品平台时**：当产线新增一款大容量洗碗机（如16套洗碗机）时，其喷淋系统、碗篮结构和控制逻辑均与原有12套型号不同。新型号的完整工艺流程（从预装到包装）需作为一个整体 Workflow 与型号引入变更包绑定。

3. **质量改进或客户投诉后的工艺调整**：例如产线发现某批次洗碗机漏水率偏高，经分析是密封圈压装工序的力度不足。优化后的压装力参数和检测标准需要以 `ChangePackage` 形式发布，并关联到“密封圈压装与气密测试 Workflow”。

### 洗碗机产线 典型示例

**场景**: 因供应链调整，洗碗机主控板（PCB）的固件版本从 v2.1 升级到 v2.2，同时主控板的安装方式从卡扣式改为螺丝固定式。这将影响三个 Workflow：  
- **WF_Pre_Assembly**: 预装工段（安装主控板）  
- **WF_Firmware_Flash**: 固件烧录与功能测试  
- **WF_Final_Test**: 整机老化与安规测试

**操作步骤**:  
1. 在 Opcenter 中创建 `ChangePackage`，命名为 `CP-2026-05-06_MainPCB_Update`，描述为“主控板固件升级 v2.2 + 安装方式变更”。  
2. 在 `ChangePackage` 属性中引用新的固件文件（如 `MainController_v2.2.hex`）、安装说明书（`Installation_Guide_v2.pdf`）以及新的扭矩值参数（`Screw_Torque=0.8Nm`）。  
3. 分别在三个 Workflow 的“affected_by”选项卡中添加该 `ChangePackage`：  
   - `WF_Pre_Assembly`：设置影响起始日期为 2026-05-10，影响结束日期为空（长期有效）。  
   - `WF_Firmware_Flash`：设置影响起始日期为 2026-05-10，并更新固件烧录步骤中的“文件路径”属性为新的固件。  
   - `WF_Final_Test`：由于固件升级后测试项不变，仅标记为受影响（无需修改步骤）。  
4. 激活 `ChangePackage` 后，系统自动将这三个 Workflow 标记为“待生效”，并在指定日期自动切换至新版本，同时记录所有受影响工单的工艺追溯。

## 配置要点

- **基数处理**：MANY_TO_MANY 要求 Workflow 和 ChangePackage 都支持多对多关联。在 Opcenter 模型中，需确保两个对象的 Reference 类型配置为“Multiple”。若默认是单一对象，需调整 Data Model 或在 UI 上使用 Link Collection。
- **影响范围精确性**：一个 `ChangePackage` 可能只影响 Workflow 中的某几个步骤，而非整个流程。建议在填写关系时附加生效条件（如“仅步骤10-15受影响”），可通过自定义属性或关联 `Step` 对象实现更细粒度控制。
- **版本与生效时间**：关系本身不强制版本历史，但通常需要记录影响起始日期（Effective Start Date）和结束日期（Effective End Date）。系统应根据该时间逻辑自动决定当前生产任务是使用旧版 Workflow 还是新版 Workflow。
- **验证与测试**：在激活影响关系前，应至少在一个虚拟生产线（或试运行环境）上验证变更后的 Workflow 是否能正常执行，避免因顺序或参数错误导致产线停机。
- **变更追溯**：关系应保留审计日志，记录谁在何时将某个 Workflow 关联到某 `ChangePackage`，以及为何修改。这有利于处理后续质量问题或合规审计。
- **与 BOM 变更的协同**：通常 `ChangePackage` 不仅影响 Workflow，还可能影响 BOM（物料清单）。建议在配置关系时，同步检查受影响的 Workflow 所使用的物料版本是否与变更包中的 BOM 版本一致。
- **多产线复用**：如果洗碗机产线有多个车间（如 A 线、B 线），同一个 `ChangePackage` 可能只影响其中一条线的 Workflow。应在关系定义中添加“车间”或“产线”筛选条件，避免影响范围意外扩大。
- **失效策略**：当 `ChangePackage` 被撤销（例如变更取消或回退）时，关联的 Workflow 应立即恢复到之前的状态。建议设置工作流自动回滚机制，或通过手动重新激活旧版 Workflow 来应对。

## 常见问题 FAQ

**Q: 配置了 AFFECTED_BY 关系后，生产订单会自动切换 Workflow 版本吗？**  
A: 不会自动切换。该关系仅记录变更的影响范围，实际 Workflow 版本切换需要通过 Opcenter 的“版本管理（Version Management）”功能或“执行生效（Execute Effectivity）”操作来完成。通常做法是：在 `ChangePackage` 被批准并激活后，手动或通过调度任务将受影响的 Workflow 升级到新版本（Version Increment），并更新关联关系中的生效时间。

**Q: 同一 Workflow 可以被多个 ChangePackage 同时影响吗？如果可以，如何决策哪个先执行？**  
A: 可以。由于是 MANY_TO_MANY，一个 Workflow 可以挂载多个 `ChangePackage`。系统需要根据每个关系的“生效起始日期”和优先级字段来确定执行顺序。例如，若 `ChangePackage A` 生效起始日为 2026-05-01，`ChangePackage B` 生效起始日为 2026-05-15，则系统将先应用 A 的变更，再叠加 B 的变更（或直接切换至 B 版本）。建议在设计 Workflow 时，为每一步骤添加版本号，并通过“基线（Baseline）”合并多个变更，避免冲突。

**Q: 如何快速查看某 Workflow 当前受哪些 ChangePackage 影响？**  
A: 在 Opcenter 的 Workflow 详细信息页面上，通常有一个“Affected By”选项卡（或类似的关联列表）。也可以在 `ChangePackage` 对象上查看其“Affected Workflows”列表。此外，可以在 Reporting 模块中建立视图，通过 SQL 查询 `WorkflowChangePackageLink` 表来获取完整列表。

---
*本文档基于 Siemens Opcenter 建模规范及洗碗机产线实际生产场景编写，用于指导系统配置与业务理解。*