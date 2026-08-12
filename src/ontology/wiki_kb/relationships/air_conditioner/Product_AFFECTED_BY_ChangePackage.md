# Product → AFFECTED_BY → ChangePackage

> **产品线**: 空调产线
> **基数**: MANY_TO_MANY
> **生成时间**: 2026-05-07
> **来源**: LLM 自动生成

## 关系说明

在 Siemens Opcenter (Camstar) 中，`Product` 与 `ChangePackage` 之间的 `AFFECTED_BY` 关系用于记录一个或多个产品受到某个变更包（Engineering Change Order, ECO）的影响。该关系是双向多对多的，即一个变更包可以影响多个产品，同时一个产品也可能受到多个变更包的影响。此关系是工程变更管理（Engineering Change Management, ECM）的核心建模要素，用于追溯产品设计或工艺更改的范围、原因及执行状态。

在空调产线场景中，该关系用来关联具体的产品型号（如家用空调的“KFR-35GW/XXXX”或中央空调的“MDVS-280W/XXXX”）与对应的变更指令。例如，由于压缩机型号升级或制冷剂切换（如 R22 切换到 R32），需要编号相应的工程变更单（ECO），并将所有受影响的成品产品（包括整机型号及物料编码）通过此关系关联到该 ECO。Opcenter 中的“Affected By”映射确保在后续生产排产、BOM 版本切换或工艺路线变更时，系统能够自动识别哪些产品需要遵循新变更包中的规范，避免混用旧版本导致的产线质量问题。

## 业务场景

### 何时需要配置此关系？

1. **设计规格变更（如压缩机、风机电机升级）**  
   当空调产品因性能优化或零部件替换需要调整 BOM 或工艺参数时，需创建 ChangePackage 并将所有受影响的成品产品（如不同能效等级或冷量规格的型号）与该包关联，以确保生产和质检环节按新版执行。

2. **法规与标准更新（如制冷剂环保法规、能效标准升级）**  
   中国能效标识标准（GB 21454-2021）更新或全球制冷剂管控变化（如欧盟 F-Gas 法规）要求空调产品必须切换至低 GWP 冷媒时，需通过 ChangePackage 一次性管理所有涉及的产品系列，并关联对应产品的物料主数据及工艺路线版本。

3. **物料替代或供应商变更影响多个产品**  
   由于核心零部件（如变频板、四通阀）被替代料替换且影响多款空调型号，需要统一发布 ECO 并在 Opcenter 中建立产品与 ChangePackage 的关系，确保产线 MES 系统在执行制造工单时能够自动校验物料版本是否匹配。

### 空调产线 典型示例

**场景**：某中央空调产线因上游铜管供应商质量事故，需将某系列模块机的换热器铜管壁厚从 0.6mm 变更为 0.8mm。该系列包含 3 个型号（MDVS-280W, MDVS-335W, MDVS-400W），且涉及 2 条总装线。工单编号为 WO20260507A 的生产任务将于 2026-05-10 执行。

**操作步骤**：

1. 在 Opcenter 中导航至 `Product` → `Product Maintenance`，确认三个型号的 Product ID 分别为 `MDVS-280W`、`MDVS-335W`、`MDVS-400W`。
2. 创建新的 ChangePackage：  
   - ID：`ECO-2026-05-07-CU`  
   - 描述：`Wall_thickness_change_for_CentralAC_series`  
   - 类型：`Quality_Critical_ECO`  
   - 生效日期：`2026-05-10`  
3. 进入 ChangePackage 的“Affected Products”选项卡，点击“Add”，分别输入三个 Product ID，并设置“Applicable Start Date”为 `2026-05-10`，“Applicable End Date”为空（长期有效）。
4. 保存关系，Opcenter 将自动创建三条 `AFFECTED_BY` 记录（Product 指向 ChangePackage）。
5. 审核并发布 ChangePackage，系统锁定受影响的旧 BOM/工艺版本，并生成新版本。
6. 对于工单 WO20260507A（计划 2026-05-10 生产），系统将应用该 ChangePackage 的最新 BOM 版本，确保铜管壁厚 0.8mm 的物料被调用。

**关键参数说明**：  
- `Product` 的 `Material Code` 字段需与 ERP 中的物料号一致，便于变更包下发时同步更新 PLM/ERP 变更单。  
- `ChangePackage` 的 `Status` 需设置为 `Released` 才能在制造工单中生效。

## 配置要点

1. **基数明确**：`MANY_TO_MANY` 意味着变更包可影响多个产品，一个产品也可隶属于多个变更包。需注意避免循环依赖（如 A 包和 B 包对同一产品的同一属性定义矛盾），建议在 Opcenter 中通过版本控制（Version）和生效日期（Effective Date）实现时间维度隔离。
2. **生效日期与版本衔接**：关系中的 `Applicable Start Date` 和 `Applicable End Date` 应精准设定，最好以排产日期为准。对于空调产线，中央空调柜机生产周期较长（2-3 天），建议 Start Date 设为首个受影响工单计划开始日期，避免提前生效导致半成品错用。
3. **权限控制**：只有具备 `Change Administrator` 角色的用户才能创建/修改 ChangePackage 及关联产品。需设置审批工作流（如工程经理→质量经理→生产经理），防止误发布。
4. **物料替代联动**：若 ChangePackage 主要涉及物料替代（如不同品牌的压缩机），则需在 Opcenter 中同时维护 `Product – Has_Candidate – Material` 关系（替代料映射），但 `AFFECTED_BY` 仅负责标识受影响的成品层面，不要将替代料详情混入此关系。
5. **追溯与报表**：建议在 Opcenter 中启用变更历史审计日志（Audit Trail），以便后续质量追溯。当发生客诉时可快速查询某产品在特定时间点受哪些 ChangePackage 影响。
6. **与 ERP / PLM 集成**：空调产线常通过中间件同步 PLM 的 ECO，Opcenter 中此关系字段（如 `ChangePackage_ID`, `ECN_External_Ref`）应映射 ERP 的变更单编号，避免数据孤岛。
7. **测试环境模拟**：在正式上线前，使用非生产环境（如 Sandbox）创建模拟 ChangePackage，关联一个低风险产品（如售后备件型号），验证工单发料、工艺路线的切换逻辑无误后再应用于量产产品。
8. **清理与过期管理**：当变更包完成所有旧料消耗且新料稳定后，可对关系设置 `End Date` 或直接归档，避免系统长期保留已失效的大量关系记录影响查询性能。

## 常见问题 FAQ

**Q: 在空调产线中，一个产品被多个 ChangePackage 同时包含（例如同时涉及压缩机升级和冷媒切换），MES 如何处理冲突？**  
A: Opcenter 会按 Workflow 规则处理，通常以最新生效的 ChangePackage（按生效日期和版本号排序）为准。建议在创建包时明确定义优先级字段（如 `Priority`），或通过变更管理流程保证在同一时间维度下不出现矛盾。对于重大冲突，系统会锁定工单并要求用户手动确认应用哪个包。

**Q: 我修改了产品的 BOM，但忘记关联 ChangePackage，工单已经报工了，怎么办？**  
A: 首先，尽快创建 ChangePackage 并与该产品建立 `AFFECTED_BY` 关系，同时将生效日期设为当前日期。然后，对于已完成报工的工单，需在 Opcenter 中手动触发“变更后验证”（Post-Change Validation）流程，检查物料消耗、工艺执行是否符合新版本。空调产线常用“追溯工单重算”（Reprocess Traceability）功能来更新已消耗物料的版本记录。如果发现误用旧料，应发起不合格品处理（NCR）。

**Q: 如何将外部的 PLM ECO 编号自动映射到 Opcenter 的 ChangePackage？**  
A: 建议在 Opcenter 的 ChangePackage 主界面添加自定义字段（如 `EXT_ECO_ID` 或 `PLM_Ref`），并通过中间件（如 TIBCO、SAP PO）定时同步。配置时确保 Opcenter 的 `Product – AFFECTED_BY – ChangePackage` 关系触发器集成模块（Integration Service）能够根据 PLM 发送的物料清单（物料号清单）自动创建关系。如果暂未集成，也可通过 Excel 导入模板批量创建，字段名为 `Product_ID`, `ChangePackage_ID`, `Start_Date`。