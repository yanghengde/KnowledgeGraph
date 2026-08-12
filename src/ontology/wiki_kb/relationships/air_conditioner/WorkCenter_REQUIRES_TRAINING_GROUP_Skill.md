# WorkCenter → REQUIRES_TRAINING_GROUP → Skill

> **产品线**: 空调产线  
> **基数**: MANY_TO_ONE  
> **生成时间**: 2026-05-08  
> **来源**: LLM 自动生成  

## 关系说明

在 Siemens Opcenter (Camstar) 中，`WorkCenter` 通过 `REQUIRES_TRAINING_GROUP` 关系指向 `Skill` 实体，用于定义该工作中心（即工位或生产区域）在执行生产任务时，操作人员必须满足的培训组或技能要求。一个 `Skill` 可以对应一个具体的培训组（例如“钎焊技能组”、“电气安全组”），而多个 `WorkCenter` 可以共享同一个 `Skill` 要求，体现了“多对一”的基数（MANY_TO_ONE）。

在空调产线（家用空调 + 中央空调）场景中，不同工位因工艺复杂度和安全风险不同，对操作人员的技能要求差异显著。例如，中央空调的冷凝器钎焊工位需要持有“特种钎焊操作证”的培训组，而家用空调的简单装配工位可能仅需“基础装配培训”。通过此关系，系统能够在派工、报工时自动校验操作人员的资格，确保只有具备相应 `Skill`（即完成对应培训组）的人员才能在该工位执行作业，从而降低质量事故和安全风险。

## 业务场景

### 何时需要配置此关系？

1. **高风险或关键工序的资质管控**  
   中央空调的制冷剂充注、管路钎焊、高压测试等工位对技能和认证有严格法规要求。当该工位只允许持证人员操作时，需要将 `WorkCenter` 与对应的 `Skill`（如“R32 空调制冷剂充注培训组”）关联。

2. **产线柔性排班与技能矩阵管理**  
   空调产线常根据订单换型（如从 1.5 匹挂机切换为 3 匹柜机），部分工序操作方式变化。此时可通过更换或增加 `WorkCenter` 所要求的 `Skill`，快速调整该工位对人员的技能要求，实现动态排班。

3. **新员工上岗前的资格预检**  
   新入职员工在分配到特定工位（如家用空调的贴标、检漏）前，需完成对应培训。系统中将该 `WorkCenter` 的 `REQUIRES_TRAINING_GROUP` 配置为“基础岗位培训组”，在员工首次扫描上线时报错，强制完成培训后才能生产。

### 空调产线 典型示例

**场景**：中央空调产线“冷凝器钎焊工位”要求操作人员具备“特种钎焊培训组”（Skill）。  

**操作步骤**（在 Opcenter 建模工具中）：

1. 打开 `Skill` 管理界面，创建 `Skill`：  
   - Name: `Brazing_Certification`  
   - Description: `中央空调冷凝器钎焊资格`  
   - Training Group: `特种钎焊培训组`（可勾选“需证书到期校验”）  

2. 打开目标 `WorkCenter`（如 `WC_Condenser_Brazing`）的“Requirements”选项卡。  
3. 添加一行：`REQUIRES_TRAINING_GROUP` → 选择 `Skill` = `Brazing_Certification`。  
4. 保存并发布。  

**运行效果**：当操作员 `OperatorA` 在该工位扫描工单并报工时，系统检查 `OperatorA` 是否已完成 `特种钎焊培训组`。若未完成，则弹窗禁止操作，并提示“缺少钎焊技能，请先完成培训”。

## 配置要点

- **Skill 应与培训组（Training Group）正确关联**：`Skill` 本身是逻辑概念，实际资格校验依赖关联的 `Training Group`。务必确保 `Skill` 引用了已定义且包含有效课程的培训组。
- **MANY_TO_ONE 的继承影响**：若多个 `WorkCenter` 同时要求同一个 `Skill`，更改该 `Skill` 的证书有效期或内容，将同时影响所有关联工位，需评估变更范围。
- **支持时间有效性**：可使用 `Valid From` / `Valid To` 控制 `REQUIRES_TRAINING_GROUP` 关系是否生效。例如，新工艺导入前 3 个月暂不强制要求新技能。
- **优先级与替代逻辑**：同一 `WorkCenter` 可配置多个 `REQUIRES_TRAINING_GROUP` 记录（相当于多个 Skill 要求），系统默认全部满足才通过。如需“或”逻辑（满足其一即可），需通过自定义规则或 `Skill Equivalency` 处理。
- **版本管理**：修改 `Skill` 或 `WorkCenter` 的关联关系后，务必发布新版本并通知培训部门，避免旧版本仍在产线使用。
- **报工规则集成**：在 `Operation` 或 `Route` 的报工规则中，可启用“校验操作员工位技能”开关，确保关系生效。
- **与 Personnel 的 Skill 赋值联动**：操作人员的 `Skill`（通过 Training 模块获得）必须与此处 `WorkCenter` 要求的 `Skill` 直接匹配（名称一致），系统不区分大小写。
- **生产排程（Scheduling）中的硬约束**：若启用高级排程，此关系可作为硬约束，自动过滤不具备对应技能的人员，避免计划锁死。

## 常见问题 FAQ

**Q: 一个 WorkCenter 可以要求多个不同的 Skill 吗？**  
A: 可以。在 `WorkCenter` 的 Requirements 列表中可添加多条 `REQUIRES_TRAINING_GROUP` 记录，每条指向不同的 `Skill`。系统默认要求操作人员同时满足所有指定的 Skill（逻辑“与”关系）。若需要“或”关系（如“持有甲证或乙证之一即可”），建议创建父 Skill 并配置等价关系，或通过自定义插件实现。

**Q: 如果操作人员已经离职，其 Skill 未及时从系统中移除，会不会导致仍在岗人员误操作？**  
A: 离职操作人员应通过 `Personnel` 管理模块将状态设置为“离职”或“禁用”，其 Skill 记录会自动失效。另外，建议定期运行 “Skill 过期检查报告”以清理无效关联。

**Q: 在空调产线中，家用空调与中央空调的 Skill 如何区分？**  
A: 推荐在 `Skill` 命名时加入前缀或产品族标识，例如：`Residential_Assembly_Basic`、`Central_HVAC_Brazing`。同时可在 `Skill` 的扩展属性中添加字段“适用产品线”（如“家用/中央”），便于报表分类和权限控制。配置 `REQUIRES_TRAINING_GROUP` 时，只需为对应工位的 `WorkCenter` 选择恰当的 Skill 即可。