# Factory → HAS_DEPARTMENT → Department

> **产品线**: 洗碗机产线  
> **基数**: ONE_TO_MANY  
> **生成时间**: 2026-05-06  
> **来源**: LLM 自动生成  

## 关系说明

在 Siemens Opcenter (Camstar) MES 中，`Factory` 与 `Department` 之间的 `HAS_DEPARTMENT` 关系定义了物理组织层级中的第一级分解。`Factory` 代表一个完整的制造基地（例如洗碗机整机生产厂），而 `Department` 则是该工厂内部按功能或区域划分的运营单元。在洗碗机产线场景下，一个工厂通常包含多个职能各异的部门，如钣金冲压部门、喷涂部门、装配部门、质量检验部门、物流仓储部门等。每个部门拥有独立的设备、人员、质检标准和物料缓冲区，并且会在制造工单的执行链条中扮演特定角色。

此关系的核心价值在于将生产管理从“全厂统一”细化为“部门级管控”，从而支持更精细的排产、物料追溯、工时统计和绩效分析。例如，当一张洗碗机组装工单下达时，系统可根据工单的目标 Department 自动匹配该部门的工艺路线、资源（机器、治具）和技能资质人员，同时将质检任务定向至对应的质检部门。在质量异常处理时，也能快速定位到具体部门所涉及的操作站、班次和操作员，极大提升了问题追溯效率。

## 业务场景

### 何时需要配置此关系？

- **新建洗碗机制造工厂**: 当企业部署一条全新的洗碗机产线或设立独立的分厂时，需要在 Opcenter 中先创建 Factory 实体，然后按实际物理布局（如冲压车间、喷涂车间、总装车间）逐一创建 Department，并关联至该 Factory。
- **产线重组或扩产**: 因产量提升或工艺变更，原有部门需要拆分（例如将原“装配部门”拆分为“内部装配部”和“总装部”）或新增（如引入机器人焊接车间），此时需新增 Department 并正确关联到工厂。
- **多工厂协作生产**: 当洗碗机某些零组件（如内胆）由兄弟厂生产，而整机总装在另一个工厂完成时，需确保各工厂内部的 Department 配置准确，以便跨厂物料流转和工单回传时能正确映射到目标部门的设备与人员。

### 洗碗机产线 典型示例

**场景**: 在 Opcenter 中创建一个名为“HomeDishFactory”的洗碗机工厂，并在其下创建“钣金车间 (SheetMetalDept)”、“喷涂车间 (PaintDept)”和“总装车间 (AssemblyDept)”三个部门。

**操作步骤** (以 Opcenter 管理界面为例):

1. 进入 **Modeling → Factory**，点击 **Add**，输入：
   - Name: `HomeDishFactory`
   - Code: `HDF001`
   - Description: `家用洗碗机制造基地`
2. 保存后，进入该工厂的编辑页面，找到 **Department** 子节点，点击 **Add Department**。
3. 创建第一个部门：
   - Name: `SheetMetalDept`
   - Code: `SM-DEPT`
   - Description: `钣金冲压与成型车间`
   - Attributes: 可选设置部门主管、产能阈值等
4. 重复步骤3创建 `PaintDept` (Code: `PT-DEPT`) 和 `AssemblyDept` (Code: `ASM-DEPT`)。
5. 验证：在 Factory 概览页面可看到三个部门已列在 `HAS_DEPARTMENT` 关系中。

**参数说明**:
- `Code` 建议使用简写+部门标识，确保全局唯一。
- `Description` 应包含明确的业务职能，便于日后检索和报表生成。
- 若部门需要关联特定工作日历，可在创建后另行配置 Calendar，与 Factory 的日历形成层次继承。

## 配置要点

1. **部门编码唯一性**：在同一个 Opcenter 实例中，Department Code 必须全局唯一（不限于同一工厂）。建议采用工厂代码+部门缩写，如 `HDF_SM`，避免跨工厂重复。
2. **部门类型区分**：Opcenter 支持给 Department 分配 Type (如 Production, Quality, Warehouse)，建议根据洗碗机产线实际分类设置，便于后续按类型筛选和权限控制。
3. **与工作中心 (WorkCenter) 的关系**：Department 下通常包含多个 WorkCenter。在配置 Department 前，应规划好哪些 WorkCenter 归属哪个部门。一个 WorkCenter 只能属于一个 Department，不能跨部门挂载。
4. **日历与班次继承**：每个 Department 可独立设置工作日历和班次规则。若未单独配置，则默认继承其所属 Factory 的日历。洗碗机产线中喷涂车间因设备特殊可能需要三班倒，而质检部门只需两班，应分别设定。
5. **人员与权限**：Department 可绑定员工技能矩阵和权限组。配置时需确保操作员、主管的角色已正确映射到对应部门，避免工单审批流程卡滞。
6. **物料流定义**：物料在部门间的流转（如冲压件从 SheetMetalDept 到 PaintDept）需在 Route 或 Material Flow 规则中明确起点和终点 Department，否则系统可能无法正确触发转移动作。
7. **数据归档与备份**：Department 一旦投入生产，其关联的工单、质检记录、设备日志等数据量巨大。建议在配置时为每个部门设置独立的数据库表空间或归档策略，提升查询性能。
8. **版本控制**：在 Opcenter 中，Factory 和 Department 结构变更（如重命名、转移子部门）可能影响历史数据。建议使用 Modeling 的版本管理功能，记录每一次变更，并通知下游业务系统。

## 常见问题 FAQ

**Q: 一个 Factory 下可以创建相同名称的 Department 吗？**  
A: 不可以。Opcenter 要求 Department Name 在同一 Factory 内必须唯一，Code 更要求全局唯一。若需要多个功能类似的部门（如“装配1线”和“装配2线”），应使用不同的 Name 和 Code，或通过 Department Type 进一步区分，而不是直接重复名称。

**Q: 删除一个 Department 后，已完成的工单和质检记录会怎样？**  
A: Department 删除属于物理删除（或软删除取决于配置）。已完成的工单及关联的质检记录会保留在系统中，但部门字段将变为空或显示“已删除”。建议使用“停用”而非“删除”功能，将部门状态设置为 Inactive，以保留历史数据的完整性。

**Q: 如何将某个 Department 下的 Workspace (工作站) 快速转移到另一个 Department？**  
A: 在 Opcenter 中，WorkCenter 与 Department 是多对一关系（WorkCenter 必属于一个 Department）。可通过 Modeling → WorkCenter 编辑界面修改其所属的 Department 属性。但请注意：如果该 WorkCenter 上有未关闭的工单或正在进行的生产活动，系统