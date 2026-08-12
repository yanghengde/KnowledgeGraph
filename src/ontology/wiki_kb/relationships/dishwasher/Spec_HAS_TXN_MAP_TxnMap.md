# Spec → HAS_TXN_MAP → TxnMap

> **产品线**: 洗碗机产线
> **基数**: ONE_TO_MANY
> **生成时间**: 2026-05-06
> **来源**: LLM 自动生成

## 关系说明

在 Siemens Opcenter MES (Camstar) 中，`Spec`（规格）定义了在特定工位或制造环节中，对产品需要完成的检查、测试或操作的项目列表。`TxnMap`（事务映射）则定义了当 `Spec` 执行时，某些特定数据或结果应该被如何处理和记录到系统中——例如是记录用户输入，还是自动从设备采集，或者是输出到标签打印机。

`HAS_TXN_MAP` 关系将一个 `Spec` 与一组 `TxnMap` 绑定，表示在这个规格的执行流程中，需要触发哪些特定的数据事务或外部动作。对于洗碗机产线来说，这个关系至关重要，因为它将“应该检查什么”（Spec 中的参数项）与“如何记录/处理检查结果”（TxnMap）关联起来，实现了从工艺要求到系统数据流的桥接。

以此洗碗机产线为例，每个 `Spec` 可能包含上百个检查项，但只有关键数据项需要被持久化记录、触发 SPC 分析或发送给外部系统。`HAS_TXN_MAP` 关系就是用来精确指定这些关键数据流的。例如，在洗碗机气密性测试工位的规格中，测试压力值、泄漏率等关键参数需要通过专门的 TxnMap 映射到数据采集系统；而一些辅助性的目检结果可能就只需要简单的 Pass/Fail 记录，不需要单独的事务映射。

## 业务场景

### 何时需要配置此关系？

1.  **关键参数自动采集场景**：当洗碗机产线上的某个测试工位（如门密封性测试、电机电流测试）需要将测试仪器产生的数值自动录入 MES 系统，并触发 SPC 监控时，需要在 Spec 中为该参数配置一个 TxnMap，指定数据源（如 OPC UA 路径）和目标字段。
2.  **数据追溯与质量拦截场景**：为了建立完整的洗碗机生产追溯链，如记录每个洗碗机内胆的焊接温度曲线或发泡层厚度，需要将设备 PLC 数据通过 TxnMap 映射到 Lot 或 Container 的特定 Data Collection 记录，用于后续质量分析和不良拦截。
3.  **输出指令与条码打印场景**：在产线末端的包装工位，当某台洗碗机符合所有规格检查后，需要自动触发条码打印机生成一台唯一的、包含生产序列号和关键参数的标签，此时需要配置 TxnMap 来调用打印服务并传递必要的打印数据。

### 洗碗机产线 典型示例

**场景**：在洗碗机总装线的“门锁吸合测试”工位，需要使用一台力传感器测量用户打开洗碗机门时所需的拉力。

**操作步骤如下**：

1.  **创建 Spec (规格)**：
    -   进入 Opcenter MES → Model → Specs → 新建 Spec，命名为 `SW_DOOR_LATCH_TEST_V1`。
    -   在 Data Collection 中，添加一个名为 `Door Open Force (N)` 的参数，数据类型设置为 Float。
    -   添加一个名为 `Latch Engagement` 的参数，数据类型为 Boolean (Pass/Fail)。

2.  **创建 TxnMap (事务映射)**：
    -   进入 Model → TxnMaps → 新建两个 TxnMap。
    -   `TxnMap_Force`：
        -   用途：记录力传感器的实测值到 Spec data。
        -   Target Object：`Spec Data Collection`.
        -   Target Property：`Door Open Force (N)`.
        -   Data Source：`Equipment -> OPC UA Node ID={namespace:sw_door_tester;nodeid=f003}
    -   `TxnMap_Result`：
        -   用途：将人工操作的 Pass/Fail 结果映射到一个系统状态。
        -   Target Object：`Container.Attribute`.
        -   Target Property：`Latch Quality Status`.
        -   Data Source：`User Input`.

3.  **建立关系**：
    -   打开 Spec `SW_DOOR_LATCH_TEST_V1`。
    -   在 Relationships 页签下，找到 `HAS_TXN_MAP`，点击“添加”。
    -   添加 `TxnMap_Force` 和 `TxnMap_Result` 到列表中。
    -   **配置关键参数**：设置 Excution Order 以确定 TxnMap 的执行顺序（例如先采集力值，再询问人工结果），并且可以为 `TxnMap_Force` 设置 On Error Action 为 "Fail"（如果采集失败则立刻终止此工序）。

4.  **验证与上线**：
    -   在产线测试界面，当工人扫描洗碗机序列号并进入此工序时，系统会自动触发 `TxnMap_Force`，从PLC读取传感器值并填入参数框。然后弹出人工判定界面，结果通过 `TxnMap_Result` 记录。

## 配置要点

1.  **明确 TxnMap 的目标对象**：首先要区分目标是 **Spec Data Collection** (将结果记录在规格执行记录中)、**Container Attribute** (更新产品的永久属性)，还是**外部输出**（调用接口）。错误的Target会影响数据流向。
2.  **合理规划 Execution Order**：当一个 Spec 有多个 TxnMap 时，其执行顺序由 `Execution Order` 属性控制。需要确保数据依赖关系正确，例如，必须先采集数据，才能将其输出到标签。
3.  **注意 OPC UA / 设备路径的准确性**：在绑定设备数据源时，路径必须绝对正确且稳定。建议在正式环境前，使用 Test Connection 或仿真工具验证。
4.  **处理映射失败场景**：为每个 TxnMap 配置合适的 On Error Action。在洗碗机产线中，对于关键数据采集失败，通常应设为 "Fail"；对于非关键信息（如重复操作确认），可设为 "Warn"。
5.  **避免过度映射**：并非所有 Spec 参数都需要 TxnMap。只有需要系统自动处理、记录或触发后续动作的参数才需要映射。过多的 TxnMap 会增加系统复杂度和运行时负担。
6.  **与外部系统交互的 TxnMap 需要前置条件**：如果 TxnMap 需要调用一个外部服务（如打印、SAP接口），需要确保该服务在 MES 系统中已经正确注册，并且 TxnMap 中引用了正确的 Service Node。
7.  **版本管理**：对 Spec 的修改可能会影响其关联的 TxnMap 关系。修改后，务必将包含此 Spec 的 Mfg Routine 重新 Deploy（部署），确保运行时使用的是最新配置。
8.  **测试环境验证**：在正式上线前，务必在测试环境中创建一份与产线一模一样的 Spec 和 TxnMap 组合。通过模拟生产（Mfg Simulation）执行所有可能的数据流向，验证映射逻辑和异常处理是否正确。

## 常见问题 FAQ

**Q: 一个 Spec 下的 TxnMap 数量有上限吗？**
A: Opcenter 没有硬性的上限，但实践中建议不要超过 50 个。过多的 TxnMap 会导致工序执行时间过长，并增加配置维护的复杂性。如果遇到超过 20 个 TxnMap 的情况，建议重新审视 Spec 设计是否合理，考虑将其拆分为多个更小的 Spec。

**Q: 如果某个参数在测试设备中数值为 0，但我想在 MES 中记录为 "Not Tested"，如何通过 TxnMap 实现？**
A: TxnMap 本身不包含复杂的业务逻辑（如条件赋值）。要实现这样的转换，有两种常用方案：
1.  在 Opcenter 规则 (Rule) 中编写脚本。在工序结束后，脚本检查 Spec Data Collection 中的数值，如果为 `0`，则修改对应字段的值。
2.  在 Spec 的参数定义中，设置 Default Value 为 "Not Tested"，然后在这个 Data Collection 的 TxnMap 中，配置为 **不覆盖** 当设备返回 `0` 时的值（在 TxnMap 的属性中设置 "Override Data if Present" 为 False）。

**Q: 如何调试一个 TxnMap 是否按预期工作？**
A: 推荐在 Test 环境中使用 Mfg Test Tool 或 Workflow Viewer 功能。你可以手动为一个虚拟的 Container 执行该 Spec，并在执行后检查 Spec Execution History 和 Container 的属性列表。另一个有效方法是启用 MES 的详细日志记录（Log Level 设为 Debug），然后检查 Application Server 的日志文件中关于该 TxnMap 的执行记录，包括读取到的原始数据和映射后的数值。