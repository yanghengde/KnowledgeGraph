# SamplingPlanDetails → ASSIGNED_SPEC → Spec

> **产品线**: 储能系统(ESS)装配线
> **基数**: MANY_TO_ONE
> **生成时间**: 2026-05-27
> **来源**: LLM 自动生成

## 关系说明

SamplingPlanDetails 与 Spec 之间的 ASSIGNED_SPEC 关系定义了在储能系统(ESS)装配线的抽样检验活动中，每一个具体的抽样计划明细项所绑定的检验规格标准。在 Opcenter MES (Camstar) 数据模型中，Spec 对象存储了特定的技术指标、上下限以及评估规则等质量规范，而 SamplingPlanDetails 则描述了在哪个生产节点、以何种频率（如每10个模组抽1个）执行检验。通过 ASSIGNED_SPEC 关系，系统将每次抽样动作与其对应的标准关联起来，确保检验活动有据可依。

在储能系统装配线场景中，这种关系的实际意义尤为突出。例如，电池模组在完成极片堆叠与焊接后，需要对电芯电压、内阻进行抽检；电池簇装配完成后，需要对高压绝缘阻抗进行抽检。不同的抽样步骤依赖不同的规格标准，但同一种规格（如“电芯电压范围 3.2V-3.65V”）可能被多个工序或产品的抽样明细所引用。MANY_TO_ONE 的基数意味着同一个 Spec 可以被多个 SamplingPlanDetails 记录引用，但每个 SamplingPlanDetails 只能指定一个 Spec，这符合实际生产中标准复用的需求。

## 业务场景

### 何时需要配置此关系？
1. **电芯分选/模组装配环节的抽样检验**：当ESS产线的电芯分选站需要按照AQL标准抽取一定比例的电芯进行电压、内阻检测时，需要为对应的SamplingPlanDetails绑定电芯单项性能Spec。
2. **BMS系统联调后的功能抽样验证**：在BMS系统调试完成并连接高压线束后，需要对整机通信、SOC校准等功能进行抽样测试，此时需将功能测试Spec关联到相应的抽样计划明细。
3. **整机测试（Final Test）的绝缘耐压抽检**：在电池簇整机测试中，根据法规或客户要求按批次抽样进行绝缘电阻、耐压测试，需要为抽样明细绑定绝缘与耐压Spec。

### 储能系统(ESS)装配线 典型示例

**场景：电芯分选后模组装配前的电压一致性抽样检验**

- **步骤1**：在Opcenter系统中创建Spec对象，命名为“ESS_电芯电压_内阻_Spec”，设置上下限参数：电压Min=3.20V, Max=3.65V；内阻Max=0.5mΩ。
- **步骤2**：创建SamplingPlan并添加SamplingPlanDetails，设定抽样频率为“每批次60pcs模组中抽取5pcs”，抽样规则为“连续批次”。
- **步骤3**：选中该SamplingPlanDetails，在ASSIGNED_SPEC字段中从Spec列表选择“ESS_电芯电压_内阻_Spec”。
- **步骤4**：在产线MES界面执行抽样时，操作员扫描模组条码，系统自动调取该Spec，并在UI上显示待测值的目标范围。
- **步骤5**：录入测试结果（如电芯电压3.45V），系统根据Spec自动判定Pass/Fail。

## 配置要点

1. **Spec版本管理**：ESS行业标准更新较快（如UL 1973、 IEC 62619），建议为每个版本的Spec创建独立记录，并定期通过ASSIGNED_SPEC关系重新绑定，避免使用过期标准。
2. **Spec复用规划**：同一个电压范围Spec可能同时用于电芯分选和模组装配后的抽检，请确保在Spec属性中设置清晰的“适用环节”标签，防止误绑定。
3. **抽样频率与Spec的匹配性**：若抽样计划按时间(如每2小时抽检一次)而非按数量设定，Spec中的样本容量（SampleSize）与抽样明细中的频次参数需一致。
4. **高压安全测试Spec的特殊处理**：绝缘耐压测试的Spec应包含“测试电压等级”和“漏电流上限”，对于不同簇（如48V、400V）必须使用不同的Spec，不可混用。
5. **BMS通信协议验证Spec的复杂性**：BMS调试后的抽样检验Spec通常包含多个子指标（如CAN通信成功率、SOC误差±2%），建议在Spec的“Description”字段中详细描述检查方法或引用外部文档ID。
6. **系统集成兼容性**：如果ESS产线使用第三方测试设备（如ATE），须确保设备返回的结果数据与Spec定义的Field名称一致，避免ASSIGNED_SPEC绑定后自动判定失效。
7. **多Site部署时的Spec维护**：当同一ESS产品在全球多个工厂生产时，不同产地的Spec可能有微小差异（如温度补偿），建议用Spec的“Division”或“WorkCenter”属性隔离，SamplingPlanDetails按工厂分别绑定。
8. **删除/停用限制**：一旦SamplingPlanDetails被创建并绑定Spec，该Spec不可直接删除，需先解除所有关联。建议对过时Spec使用“Disable”状态而非直接删除。

## 常见问题 FAQ

**Q: 如果多个SamplingPlanDetails需要引用同一个Spec，ASSIGNED_SPEC关系是否支持？**
A: 完全支持。MANY_TO_ONE基数允许同一个Spec被多个SamplingPlanDetails引用。例如，“ESS_绝缘阻抗_Spec”可同时用于模组抽检和簇抽检的SamplingPlanDetails，只需在各自的明细中分别选择该Spec即可，无需重复创建。

**Q: 在配置时，为什么下拉列表里看不到已创建的Spec？**
A: 可能原因：（1）Spec的“Status”未被设置为“Active”，必须为“Active”才能被选用于SamplingPlanDetails；（2）Spec的“Resource”或“WorkCenter”权限过滤导致不能跨区域显示；（3）SamplingPlanDetails所属的Product与Spec的Product层级不匹配，请检查Spec是否有Product限制。

**Q: 如果测试设备执行结果返回的数值超出了Spec范围，系统会怎样判定？**
A: 系统会根据Spec中定义的上下限与Data Collection规则自动判定为“FAIL(失败)”，并触发预设的失败处理流程（如弹出强制复测窗口、禁止流转至下一工站）。但请注意，如果测试结果在Spec边界值（如恰好等于3.65V），建议在Spec中设置“Include Min”和“Include Max”标记以确定判定逻辑。