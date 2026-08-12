# BusinessRule → ASSIGNED_TO_SPEC → Spec

> **产品线**: 空调产线  
> **基数**: MANY_TO_ONE  
> **生成时间**: 2026-05-08  
> **来源**: LLM 自动生成  

## 关系说明

在 Siemens Opcenter (Camstar) 中，`BusinessRule`（业务规则）通过 `BizRuleTxnMap` 关联到 `Spec`（规范）的**事务事件**。该关系是**多对一**的，即一个 Spec 可以绑定多个业务规则，但每个业务规则实例只属于一个 Spec。业务规则在 Spec 执行的特定时刻（如 Start、Complete、Pass、Fail 等事件）被触发执行，用于实现生产过程中的逻辑控制、校验、数据采集和自动化决策。

在空调产线场景中，Spec 通常对应某个工站的操作规范或工艺流程步骤（例如“室外机电气测试”、“室内机管路焊接”）。通过将业务规则关联到这些 Spec，可以灵活地嵌入定制化验证逻辑，例如：检查产品序列号是否重复、强制扫描关键物料（压缩机、电机）的批次条码、依据前工序结果决定是否跳过当前步骤、或者自动触发数据上报到上层系统。这种机制使得 Opcenter 在不修改核心代码的前提下，能够适应空调产线对柔性生产和质量追溯的高要求。

## 业务场景

### 何时需要配置此关系？

1. **关键物料防呆校验**：在空调装配工站，需要确保每个整机绑定正确编码的关键零部件（例如压缩机、冷凝器）。配置业务规则在 Spec 的 `Start` 事件触发，校验扫描的物料条码是否在 BOM 的允许列表中，若不符合则阻止工件进入下一工序。
2. **质量门（Quality Gate）管控**：在中央空调的电气安全测试工站，需根据前工序测试结果决定当前工序是否允许执行。配置业务规则在 Spec 的 `BeforeStart` 事件触发，查询前工序 Spec 的通过状态，若未通过则报错并抛出异常。
3. **动态流程调整**：家用空调产线生产多种型号（如单冷、冷暖变频），不同型号在某个工站需要执行不同的操作内容。配置业务规则在 Spec 的 `Complete` 事件触发，根据产品属性动态修改后续 Spec 的执行顺序或跳过某些步骤。

### 空调产线 典型示例

**场景**：在室外机组装线“压缩机安装”工站，要求作业员每装一个压缩机必须扫描其序列号，并验证该压缩机是否已被其他整机使用（防止混装）。

**配置步骤与参数**：

1. **进入 Opcenter Admin → Business Rules → 新建规则**  
   - 规则名称：`R_Check_Compressor_Serial`  
   - 规则类型：`Validation Rule`  
   - 事件类型：`Start`（在工站开始操作时触发）  

2. **编写规则逻辑**（可通过内置脚本或表达式实现）  
   ```vb
   ' 获取当前扫描的压缩机条码
   Dim CompressorSN As String = GetUserScanResult("CompressorSN")
   ' 查询数据库是否存在该条码且状态为“已使用”
   Dim sql = "SELECT COUNT(1) FROM Compressor WHERE SerialNumber = '" & CompressorSN & "' AND Status='USED'"
   If ExecuteScalar(sql) > 0 Then
       Throw New BusinessRuleException("压缩机 " & CompressorSN & " 已被其他整机占用，请更换")
   End If
   ' 标记该压缩机为“已使用”
   ExecuteNonQuery("UPDATE Compressor SET Status='USED' WHERE SerialNumber='" & CompressorSN & "'")
   ```

3. **配置关联 Spec**  
   - 在 Spec 清单中找到 `Spec_Outdoor_Compressor_Install`（室外机压缩机安装规范）  
   - 进入 `Events` 标签页 → 选择 `Start` 事件 → 在 `Business Rule` 字段选择刚创建的 `R_Check_Compressor_Serial`  

4. **保存并部署**  
   - 规则生效后，当工件到达该工站并触发 Start 事件时，系统自动执行压缩机校验逻辑。  

## 配置要点

1. **事件类型选择**：根据业务触发时机选择正确的事件（`Start`、`BeforeStart`、`Complete`、`BeforeComplete`、`AfterComplete`、`Fail`、`Pass`）。常见错误是将校验放在 `Complete` 事件，导致工件完成后才发现问题。  
2. **规则执行顺序**：若一个 Spec 关联了多个业务规则，Opcenter 按规则在界面上的 **Sequence** 值（数字小先执行）依次运行。需仔细规划顺序，避免规则依赖错误（例如先写日志再校验）。  
3. **环境变量可用性**：在规则脚本中，可以访问当前工单、产品、资源等对象，但注意不同事件下可用数据不同（例如 `Start` 事件时尚未采集数据，`Complete` 时采完数据）。  
4. **性能影响**：避免在规则中执行长时间数据库查询或循环操作，尤其是高频工站（如流水线测试工位）。可将复杂逻辑封装成存储过程或用 Opcenter 的 Event Handler 替代。  
5. **版本管理**：每次修改业务规则后，需重新保存并部署 Spec 绑定关系，否则旧版本仍然生效。建议在测试环境验证无误后更新生产环境。  
6. **错误处理**：业务规则抛出 `BusinessRuleException` 会终止当前事务，并给用户提示错误信息。需确保异常信息清晰（中英文），便于现场人员处理。  
7. **事务隔离**：规则中执行的数据库更新操作与 Opcenter 主事务在同一事务内，若规则失败则所有更新回滚。注意不要在此处写入与主事务无关的操作（如外部系统调用），以免回滚范围超出预期。  
8. **跨 Spec 依赖**：若需要引用其他 Spec 的测试结果，可通过 `GetService("DataAccess")` 查询 `ResourceHistory` 表，但注意性能。建议配置“前工序完成”判断规则时，使用 Opcenter 的 Conditional Step 功能而非冗长脚本。

## 常见问题 FAQ

**Q: 我配置了业务规则但工站不生效，可能的原因是什么？**  
A: 首先检查 Spec 的 Events 标签页中是否已正确关联规则（注意区分事件类型）。其次确认业务规则状态为“启用”（Active）。最后验证部署是否已更新到运行环境，可尝试在 Admin 中重新生成 Spec 的部署文件。

**Q: 多个规则同时失败时，用户看到的错误提示是哪个？**  
A: Opcenter 会按 Sequence 顺序依次执行规则，遇到第一个抛出 `BusinessRuleException` 的规则会立即终止，并显示该规则的自定义错误信息。后续规则不再执行。因此建议将最重要的校验规则排在最前面。

**Q: 在规则中如何获取当前产品型号和工单号？**  
A: 可以通过内置对象获取，例如：  
```vb
Dim ProductId As String = CurrentObject.GetProperty("ProductId")  
Dim OrderNo As String = CurrentObject.GetProperty("OrderNo")  
``具体可用的变量取决于 Spec 关联的事务类型（如 Container Start / Resource Start），建议查阅 Opcenter 脚本开发手册。