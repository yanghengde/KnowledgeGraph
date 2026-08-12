# Workflow → AFFECTED_BY → ChangePackage

> **产品线**: 空调产线  
> **基数**: MANY_TO_MANY  
> **生成时间**: 2026-05-08  
> **来源**: LLM 自动生成  

## 关系说明

在 Siemens Opcenter (Camstar) MES 中，Workflow 定义了产品在制造过程中的工艺路线，包括各个工序、检验点、物料消耗和参数采集等。ChangePackage 则用于管理生产过程中的工程变更、工艺优化或物料替换等受控调整。`AFFECTED_BY` 关系将 Workflow 与 ChangePackage 关联，表示某个生产工艺路线受到一个或多个变更包的影响，同时一个变更包也可能影响多个工艺路线。

在空调产线场景中，这种关系尤为重要。家用空调和中央空调的生产涉及大量零部件（如压缩机、换热器、管路）和复杂的装配、充注、测试工序。当设计变更、供应商切换或法规要求更新时，必须确保受影响的 Workflow 被及时标记并追溯，以便质量部门审核、计划部门切换执行版本，并确保现场按最新工艺操作。MANY_TO_MANY 的基数反映了现实中的复杂性：一次变更（如统一更换制冷剂类型）可能同时影响多条产线的多个 Workflow；而一个 Workflow（如中央空调室外机装配）可能在不同时间点受到多个变更包的影响，例如先更换压缩机型号，再调整真空干燥参数。

通过配置此关系，Opcenter 可以在 ChangePackage 激活时自动识别受影响的 Workflow，并触发对应的审批、通知或强制版本升级逻辑，从而保证空调生产的工艺合规性和可追溯性。

## 业务场景

### 何时需要配置此关系？

1. **制冷剂切换引起的工艺变更**：家用空调从 R22 切换为 R32 时，充注压力、泄漏检测阈值、干燥要求均可能变化，需更新对应 Workflow 并关联变更包。
2. **压缩机型谱升级**：中央空调采用新型变频压缩机，装配扭矩、冷媒管路走向、电气测试程序需调整，变更包需同时影响多个机型 Workflow。
3. **供应商物料替换**：因供应商业绩或环保要求，某型号四通阀替换为兼容型号，对应装配步骤和来料检验项需修改，且可能影响多条产线的公用 Workflow。

### 空调产线 典型示例

**场景**：家用空调分体外机产线因环保法规要求，将制冷剂从 R410A 切换为 R290（丙烷）。生产部门需修改“总装-充注-检漏” Workflow。

**操作步骤**：

1. **创建 ChangePackage**  
   - 导航至 **Change Management > Change Package**，点击“新建”。  
   - 输入名称：`R290_Refrigerant_Switch_202605`  
   - 描述：`R410A to R290 for split outdoor unit, effective 2026-06-01`  
   - 设置状态为“Draft”

2. **识别受影响的 Workflow**  
   - 在 Opcenter 中查询所有涉及 R410A 相关的 Workflow，例如：  
     - `Outdoor_Unit_Assembly & Leak_Test_R410A`（版本 2.1）  
     - `Charging_Line_R410A_VacDry`（版本 1.3）  
   - 确认需要修改的步骤：充注压力从 1.2MPa 改为 0.8MPa，泄漏检测从检漏仪型号 A 改为 B。

3. **配置 AFFECTED_BY 关系**  
   - 在 Workflow 属性中，选择 **Relationships** 标签页，添加“AFFECTED_BY”关系。  
   - 选择 ChangePackage `R290_Refrigerant_Switch_202605`。  
   - 重复为另一个 Workflow 添加。

4. **更新 Workflow 版本**  
   - 基于原 Workflow 创建新版本（如 3.0），修改充注参数和检漏步骤。  
   - 保存并提交审批。  
   - 在 ChangePackage 中关联新版本 Workflow，标记旧版本为“失效”。

5. **激活与通知**  
   - ChangePackage 通过审批后，设置生效日期 `2026-06-01`。  
   - 系统自动通知各生产线班组长，并限制旧版本 Workflow 在新订单中使用。

## 配置要点

1. **基数管理**：确认 Workflow 和 ChangePackage 均为 MANY_TO_MANY，配置时需注意双向关联：在 Workflow 侧添加 AFFECTED_BY 关系，同时在 ChangePackage 侧也应能查看受影响的 Workflow 列表。Opcenter 默认同步维护，但建议验证。

2. **版本控制策略**：当 ChangePackage 影响现有 Workflow 时，通常不建议直接修改原版本，而是创建新版本并通过关系关联。旧版本应被标记为“过期”或“失效”，并设定未来订单不可用的规则。

3. **生效日期与时间条件**：在 ChangePackage 中设置生效日期，可结合 Opcenter 的“有效期间”功能让系统自动在指定时间切换 Workflow 版本。空调产线需注意批次切割点，避免跨日或跨班次的混淆。

4. **权限与审批流程**：仅授权人员（如工艺工程师、质量经理）可创建/修改 ChangePackage 及关联 Workflow。建议在 Workflow 变更时强制触发审批工作流，确保变更受控。

5. **变更影响分析**：配置关系前，利用 Opcenter 的“影响分析”报表（Impact Analysis）预判该 ChangePackage 会影响多少 Workflow、多少在制品（WIP）订单。空调产线中，中央空调生产周期长，需特别关注已投产订单的返工或特采处理。

6. **物料与设备联动**：如果变更涉及物料替代或设备参数调整，除了关联 Workflow，还应在 ChangePackage 中关联相应的物料版本和设备校准记录。例如 R290 充注需防爆设备，需同步更新设备主数据。

7. **测试与模拟**：在生产切换前，建议在沙箱环境（Sandbox）中模拟配置关系，验证自动版本切换和通知是否按预期执行。尤其是空调多产线共用的 Workflow，需确保不会遗漏。

8. **归档与审计**：每个 AFFECTED_BY 关系都会记录在 Opcenter 的变更历史中。建议定期归档已关闭的 ChangePackage，并保留 Workflow 版本关系至少 5 年，以满足空调行业的安全性和环保法规审计要求。

## 常见问题 FAQ

**Q: 配置了 AFFECTED_BY 关系后，旧 Workflow 是否能继续用于当前在制品？**  
A: 可以。Opcenter 允许根据 ChangePackage 的生效日期和 Workflow 版本有效期决定。通常，已投产订单可继续沿用旧版本，新订单自动使用新版本。但需要根据业务规则（例如是否允许混用）在 ChangePackage 中设置“切换策略”。空调产线中，建议对制冷剂、压缩机等重大变更执行“硬切换”——所有在制品必须返工为最新版本。

**Q: 如果一个 Workflow 同时被多个 ChangePackage 影响，如何确定哪个版本是最终有效的？**  
A: Opcenter 使用“版本生效优先级”判断。通常以 ChangePackage 的生效日期和创建时间决定。如果多个变更包在同一日期生效，可手动排序或配置冲突解决规则。建议为每个 Workflow 维护一个“有效版本列表”，并在 ChangePackage 批准时自动刷新。在空调产线实践中，工艺工程师应审查所有关联变更包，避免因参数叠加导致错误。

**Q: 如何快速查找历史上某个 Workflow 受哪些 ChangePackage 影响？**  
A: 在 Opcenter 中，可以打开 Workflow 的“关系图”视图（Relationship Viewer），筛选关系类型为 AFFECTED_BY，即可列出所有关联的 ChangePackage 及其状态、生效日期。也可以在 ChangePackage 的“影响对象”选项卡中查看所有受影响的 Workflow。建议利用 Opcenter 的“审计追踪”功能生成报告，定期导出为 Excel 用于产线变更追溯。