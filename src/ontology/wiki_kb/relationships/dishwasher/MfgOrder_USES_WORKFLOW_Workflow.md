# MfgOrder → USES_WORKFLOW → Workflow

> **产品线**: 洗碗机产线  
> **基数**: MANY_TO_ONE  
> **生成时间**: 2026-05-06  
> **来源**: LLM 自动生成

## 关系说明

在 Siemens Opcenter (Camstar) 中，`MfgOrder → USES_WORKFLOW → Workflow` 定义了制造工单（MfgOrder）与工艺路线（Workflow）之间的关联。每个制造工单必须绑定一个 Workflow，用于描述该工单在生产过程中需要执行的所有工序步骤、操作顺序、质量检验点以及物料消耗规则。基数 MANY_TO_ONE 表示多个不同的 MfgOrder 可以共用同一个 Workflow 实例，这在实际生产中非常常见。

以洗碗机产线为例，同一型号的洗碗机（如型号 DW-5000）可能被多个客户订单下达生产，每个工单（如“订单号20260506-001”、“订单号20260506-002”）都可以复用一个名为“DW-5000 标准装配与测试 Workflow”。这种设计减少了工艺重复定义的工作量，并在工艺变更时只需修改一个 Workflow 即可同步影响所有使用该 Workflow 的工单（需注意生效策略）。Workflow 通常包含预清洗、内胆组装、门板安装、电气接线、程序烧录、整机测试、包装等工序，每个工序可进一步关联 Spec（规范）、Resource（资源）和 Materials（物料）。

## 业务场景

### 何时需要配置此关系？

1. **新产品导入（NPI）**：当洗碗机产线引入一款新机型（如 DW-8000 Pro），需要创建对应的 Workflow 定义其装配、测试和包装步骤，然后为生产批次创建 MfgOrder 并关联此 Workflow。
2. **工艺变更或产线调整**：例如为了提升能效等级，需要在某型号洗碗机中增加“电机效率测试”工序。此时修改原有 Workflow（或创建新版本），后续所有引用该 Workflow 的 MfgOrder 将自动采用新工艺（取决于版本管理策略）。
3. **同型号不同批次要求微调**：尽管多数工单共享同一个 Workflow，但某些特殊订单（如出口欧洲需额外认证测试）需要微调工艺。此时可以基于标准 Workflow 复制并修改后用做该特定工单的专属 Workflow。

### 洗碗机产线典型示例

**背景**：洗碗机产线计划生产 100 台型号为“DW-7000”的产品，客户订单编号为“ORD-20260506-001”。  
**操作步骤**：

1. **创建或确认 Workflow**  
   - 在 Opcenter 中打开 Workflow 模块，确认存在名为“DW-7000 Standard Workflow v2.0”的 Workflow。该 Workflow 包含以下工序：  
     - 工序10：内胆上料  
     - 工序20：洗涤泵安装  
     - 工序30：电路板焊接  
     - 工序40：程序烧录与自检  
     - 工序50：整机泄露测试  
     - 工序60：门板组装  
     - 工序70：外观检查  
     - 工序80：打包入库  

2. **创建 MfgOrder**  
   - 进入 MfgOrder 模块，新建工单：
     - 工单号：MFG-20260506-001  
     - 产品：DW-7000  
     - 数量：100  
     - 计划开始日期：2026-05-07  
     - **Workflow 字段**：选择“DW-7000 Standard Workflow v2.0”  
   - 保存后，Opcenter 自动校验 Workflow 的启停状态，并关联该 MfgOrder。

3. **执行与跟踪**  
   - 产线操作员在 Opcenter MES 界面扫描工单条码，系统自动加载对应 Workflow，指导每个工位的操作。  
   - 质量人员可在工序50（泄露测试）记录测试数据，出现异常时触发强制返工或 Hold 工单。  
   - 当 100 台洗碗机完成所有工序后，工单状态更新为 Completed。

## 配置要点

- **Workflow 状态管理**：只有处于“Active”状态的 Workflow 才能被 MfgOrder 引用。若需要临时禁用某条工艺路线（例如产线改造期间），务必先将 Workflow 状态改为 Inactive，避免新工单误绑定。
- **版本控制策略**：推荐使用 Workflow 版本号管理工艺变更。Opcenter 允许在 MfgOrder 中指定 Workflow 的固定版本（如 v2.0）或“最新 Active 版本”。对于已开始执行的工单，可以设置“允许跳过版本检查”或“强制锁定当前版本”，根据业务规则选择。
- **工序依赖与平行流程**：洗碗机产线中有些工序可以并行（如电路板焊接与内胆预处理），在 Workflow 中需定义好 Predecessors（前置工序）和 Branches（分支），确保 MfgOrder 走通正确路径。
- **物料绑定**：Workflow 上的每个工序应关联所需物料（Material），并指定消耗数量与倒冲/正送策略。MfgOrder 使用该 Workflow 时，系统自动计算工单的物料需求量（基于数量 × 单位消耗）。
- **资源与工时约束**：在 Workflow 的工序属性中设置所需资源（Resource）如“装配工位A”、“泄露测试仪”，以及标准工时。这影响 MES 排程模块对 MfgOrder 的计划。
- **合规与归档**：投产后不要删除已使用的 Workflow（即使过时），建议标记为 Archive 状态，以支持追溯审计。可根据日期/批次查询某 MfgOrder 当时使用的 Workflow 内容。
- **多语言与多区域**：如果洗碗机销往不同国家，Workflow 中可添加多语言的操作指导（Instruction）和检验标准，MfgOrder 根据产品目标市场自动加载对应语言版本。
- **性能考虑**：当一个 Workflow 被成百上千 MfgOrder 引用后，若需修改工序结构（如增删步骤），建议创建新版本而非直接编辑原版，避免影响正在执行的工单。

## 常见问题 FAQ

**Q: 如果我修改了某个 Workflow，已经启动的 MfgOrder 会受影响吗？**  
A: 这取决于 Opcenter 的版本管理策略。默认情况下，已启动的 MfgOrder 仍然使用它被创建时所关联的 Workflow 版本，除非系统管理员设置了“自动更新到最新版本”选项。建议将重要生产的 MfgOrder 锁定到具体版本。

**Q: 一个 MfgOrder 可以同时使用多个 Workflow 吗？**  
A: 不能。MfgOrder → USES_WORKFLOW 是 MANY_TO_ONE 关系，一个工单只能关联一个 Workflow。但可以在单个 Workflow 内通过工序分支（Branches）实现不同路径（例如根据洗碗机颜色选择不同的门板安装工序）。

**Q: 如何在 Opcenter 中快速找到某个 MfgOrder 当前使用的 Workflow 版本？**  
A: 进入 MfgOrder 详情页，查看“Workflow”字段即可看到 Workflow 名称与版本号。也可以通过 Opcenter 的查询功能，使用“MfgOrder to Workflow”关系进行追溯，或查看工单历史记录（History）中的版本快照。

**Q: 如果我想让两个不同的工单（不同产品型号）共享 80% 相同的工序，只有最后几步不同，应该怎么配置？**  
A: 建议创建两个独立的 Workflow，但将公共部分设计为子 Workflow（Sub Workflow）或使用工序库（Process Library）复用公共步骤。Opcenter 支持在 Workflow 中嵌入子流程。例如