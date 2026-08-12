# Box → LOADED_ONTO → Pallet

> **产品线**: 储能系统(ESS)装配线  
> **基数**: MANY_TO_ONE  
> **生成时间**: 2026-05-28  
> **来源**: LLM 自动生成

## 关系说明

在储能系统(ESS)装配线中，`Box` 指用于承载单个电池模组(Module)或关键零部件（如BMS控制单元、高压连接器组件）的独立包装箱或工装托盘，而 `Pallet` 是产线上标准化的物流栈板（通常为铁质或高密度塑料材质，适配AGV与滚轴输送线）。`LOADED_ONTO` 关系表示多个 `Box`（例如多个模组包装箱或多个BMS组件盒）被精确装载到同一个 `Pallet` 上，形成一个可整体运输的物料单元。

这一关系在储能系统制造中至关重要，因为模组与Rack的装配需要大量小批量、多品种的物料流转。通过将多个 `Box` 组合到一个 `Pallet` 上，可大幅减少AGV运送频次，同时便于在产线缓存区（如Buffer Station）进行成组投料。每个 `Pallet` 上的 `Box` 物理位置（如Slot编号）通常会被记录，以便后续抓取或安装时能准确识别物料与相应产品（例如：Pallet上Slot 1的Box内装有A型模组，Slot 2的Box内装有BMS模块）。

## 业务场景

### 何时需要配置此关系？

1. **模组成组上线**：当从原材料仓库或前道工序（如电芯分选）将多个电池模组运送到ESS总装线时，需要将每个模组的Box装载到同一个Pallet上，以形成“一板多件”的配送批次，供给后续簇(Rack)装配工位。

2. **BMS组件预载**：BMS系统调试前，需要将电池管理单元、采集板、线束包等分置于独立Box中，再将这些Box装载到特定Pallet上，跟随模组Pallet一起流转至调试工位，避免物料错混。

3. **高压连接器及辅料配送**：高压线束、汇流排、绝缘垫等体积小但种类多的物料，通常先分拣入Box，再将多个Box组板到一个Pallet上，通过AGV一次性配送至多个装配工位，提升线边物料周转效率。

### 储能系统(ESS)装配线 典型示例

**场景**：模组上线至Rack装配工位  
**步骤**：  
1. 质检完成的A型储能模组（每箱一个，Box ID: MOD-BOX-001~008）经扫码出库。  
2. 在组板工作站，操作员将8个Box依次放置在标准物流栈板（Pallet ID: PLT-220503）的指定槽位（Slot 1~8）。  
3. 在Opcenter系统中，通过扫描Pallet ID后，逐个扫描Box ID，执行 `LOADED_ONTO` 关系绑定，记录每个Box的Slot位置。  
4. 系统自动生成一个Pallet单号，绑定8个Box的物料批次、生产日期等追溯信息。  
5. AGV将此Pallet运送至Rack装配工位，操作员根据系统指引抓取指定Slot的Box，完成模组安装。  
6. 当Box被取空后，系统自动解除Box与Pallet的绑定（或标记为Removed）。

## 配置要点

1. **Box与Pallet的容器类型定义**：必须在Opcenter中分别定义Box和Pallet为不同的Container类型，并明确Box为子容器（Child），Pallet为父容器（Parent），且允许一个Pallet有多个Box（基数MANY_TO_ONE）。建议开启子容器的位置（Location/Slot）追踪功能。

2. **Slot（槽位）管理**：如果产线需要精确记录每个Box在Pallet上的物理位置（如格口编号），需在Pallet Container类型下配置Slot List，并在绑定操作时传入Slot ID。Slot未定义时也可简单绑定，但不利于精确抓取。

3. **自动组板规则**：对于高重复性的场景（如固定8个模组Box组一个Pallet），可配置自动组板Resource或Service，按配方自动将Box装载到Pallet上，减少人工扫描步骤。但需注意校验Box物料是否相同。

4. **解除绑定逻辑**：当Box从Pallet上被取下（如投入生产工位），需执行 `REMOVED_FROM` 或反操作 `UNLOAD`，否则Pallet上的子容器数量会错误累积。建议在工位触发事件或扫描退库时自动执行。

5. **追溯关联**：每一个Box内部的物料批次（如电芯、BMS板）需通过Box传递给Pallet，确保Pallet的虚拟批次能追溯到所有子件的谱系。可在Container属性的Search Path中设置向上继承。

6. **性能考虑**：当Pallet上装载大量Box（如超过50个）时，频繁的 `LOADED_ONTO` 操作可能影响事务响应。建议采用批量绑定API或延迟写入策略（如FIFO队列处理）。

7. **安全隔离**：不同产品系列（如50kWh模组与100kWh模组）的Box不应混装在同一Pallet上，否则会引发混淆。可通过验证Business Rule（如物料类匹配）在绑定前阻止违规操作。

8. **可视化看板**：在车间显示屏上，建议将Pallet与Box的绑定关系以表格或3D图形呈现，帮助线长快速识别哪些Box已就位、哪些正在使用中，提升目视化管理水平。

## 常见问题 FAQ

**Q: 一个Pallet上最多可以装载多少个Box？**  
A: 由Pallet的物理尺寸与Slot数量决定。在Opcenter中，如果你在Pallet Container定义了Slot List（如8个Slot），则最多绑定8个Box。如果未定义Slot，则数量只受Container类型的Max Children属性限制（默认无上限）。建议根据物流托盘标准统一设置，例如ESS产线常用1200x1000mm托盘，可放置4个标准模组箱或8个BMS盒。

**Q: 如果已经绑定了多个Box，但生产紧急需要替换其中一个Box的内容，如何处理？**  
A: 无法直接替换。需要先执行 `Unload` 操作（使用 `REMOVED_FROM` Event）解除该Box与Pallet的绑定，然后物理移除旧Box，再物理放置新Box并重新执行 `LOADED_ONTO` 绑定。系统会记录整个操作日志，追溯信息仅保留当前绑定的Box。建议在组板工作站预留“替换”工作流，避免数据错误。

**Q: 为什么在工位扫描Box取下时，系统提示“Box尚未关联Pallet”？**  
A: 这通常是因为操作顺序颠倒——先扫描了Pallet之外的动作。正确的物流流程是：Box必须首先通过 `LOADED_ONTO` 绑定到Pallet，才能在后续环节（如工位接管）通过Pallet间接识别Box。如果Box直接投入生产而未经组板绑定，系统会认为该Box是“孤立容器”，无法正常流转。解决方法：在组板工作站强制绑定，或在产线入口处增加校验规则：未绑定Pallet的Box不得通过扫描枪确认进入工位。

---