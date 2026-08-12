# WorkCenter → CONTAINS_PART → Part

> **产品线**: 洗碗机产线  
> **基数**: ONE_TO_MANY  
> **生成时间**: 2026-05-07  
> **来源**: LLM 自动生成  

## 关系说明

在 Siemens Opcenter MES (Camstar) 中，`WorkCenter`（工作中心）和 `Part`（部件/资源）之间的 `CONTAINS_PART` 关系用于将物理或逻辑资源（如设备、工位、工装、模具）归属于特定工作中心。在洗碗机产线场景下，这一关系意味着一个工作中心（例如“内胆装配区”、“总装线”、“性能测试站”）可以包含多个具体的生产资源 Part，每个 Part 可能是一个独立的工位、一台设备或一个可替换的工具。这些 Part 作为工作中心的子资源，参与具体的生产工序（Step），并可以被调度、维护、统计 OEE 等。

在洗碗机制造过程中，流程长且工序复杂，包含钣金成型、内胆焊接、喷涂、电机组装、门体装配、电气测试、包装等。通过 `WorkCenter → CONTAINS_PART → Part` 建模，企业可以将每个物理工位（如“内胆安装工位1”、“门板压合机”）作为一个 Part 对象，绑定到对应的 WorkCenter（如“总装线A”）。这样既实现了资源层级管理，又为后续生产报工、设备状态监控、质量追溯提供了基础数据模型。特别地，当产线需要柔性地替换、增加或调整工位时，只需在对应 WorkCenter 下更新 Part 列表即可，无需重新设计整个工作中心结构。

此关系强调“工作中心包含资源”，而资源 Part 本身还可以具有独立的属性（如设备编号、型号、维护周期）和状态（在线、离线、停机）。在洗碗机产线中，不同工种的 Part（如自动焊接机器人、人工装配台、测试仪表）可以混合归属于同一 WorkCenter，方便生产主管在 Opcenter 中统一查看该工作中心所有资源的负载与产能。

## 业务场景

### 何时需要配置此关系？

**1. 新建一条洗碗机产线时需要定义工作中心下的资源清单**  
当企业新建一条洗碗机总装线（如“总装线2号”），需要明确该工作中心包含哪些具体工位：内胆上线工位、碗篮安装工位、门体安装工位、控制面板安装工位、泄漏测试机、最终检查台等。每个工位作为一个 Part 对象，通过 `CONTAINS_PART` 关联到该 WorkCenter，以便后续配置工序、分配人员、跟踪设备状态。

**2. 产线改造或工位移动时需更新资源归属**  
例如，洗碗机产线为提高效率，将原先从属于“总装线1号”的“碗篮安装工位”物理搬迁至“总装线2号”。此时 Opcenter 中无需删除 Part，只需修改该 Part 的所属 WorkCenter（即断开原有关系并建立新的 `CONTAINS_PART` 关系），同时相关工艺路线、资源配置会自动同步。

**3. 共享资源需归属多个工作中心（特殊场景需变通）**  
某些资源（如中央供胶系统、公共测试仪）可能被多个 WorkCenter 使用。由于 `CONTAINS_PART` 关系本身是“属于”关系（一个 Part 只能属于一个 WorkCenter），Opcenter 标准模型中不支持多对多。此时可考虑将共享资源建模为“虚拟工作中心”下的 Part，或者通过独立 Resource Pool 方式管理。但在多数洗碗机产线中，建议将此类资源单独放在一个“公共资源工作中心”下，再用其他关系（如 `USES_PART`）关联到实际产线。

### 洗碗机产线 典型示例

**示例：为“总装线A”工作中心配置三个典型工位 Part**

- **前置条件**：Opcenter 中已创建 WorkCenter 名为 `WC_TOTAL_ASSEMBLY_A`，且已存在 Part 类型 `TRANSFER_PART`（或自定义资源类型，如 `RESOURCE_PART`）。
- **操作步骤**（Opcenter System Setup → 关系配置）：
  1. 导航到 WorkCenter 对象 `WC_TOTAL_ASSEMBLY_A`，选择“Relationships”标签。
  2. 添加新关系 `CONTAINS_PART`，选择 Part 对象 `P_INNER_TANK_FIXTURE`（内胆安装夹具工位）。
  3. 同样方法，依次添加 Part `P_DOOR_HINGE_PRESS`（门铰链压装机）和 `P_LEAK_TEST_STATION_01`（泄漏测试站）。
- **参数设置**：每个 Part 可能需要配置 `Sequence` 序号（例如 10, 20, 30）来指定在工作中心内的顺序，其他属性如 `Description`、`Capacity`（每小时产能）可酌情填写。
- **结果**：此后，在建立工艺路线（Route）时，可以将工序（Step）绑定到这些具体的 Part 上，系统会自动校验 Part 是否属于当前工序所在的工作中心。

## 配置要点

1. **Part 类型选择**：Opcenter 中的 Part 模块通常用于物料或成品，但 `CONTAINS_PART` 关系中的 Part 亦可用于资源。建议在 Opcenter 设置中创建专门的 Part 子类型（如 `ResourcePart`），或者通过 `PartCategory` 区分。避免将物料类型的 Part 错误地添加到此关系中。

2. **基数约束**：一个 WorkCenter 可以包含多个 Part，但一个 Part 只能属于一个 WorkCenter。若要将某 Part 从一个 WorkCenter 移到另一个，必须先删除原关系再添加新关系，不可直接修改其所属 WorkCenter 属性。

3. **顺序控制**：如果在工作中心内 Part 有逻辑次序（如流水线工位顺序），可通过 `CONTAINS_PART` 关系上的 `Sequence` 字段设置。注意该字段只影响展示顺序，不影响 Opcenter 工序执行顺序（工序顺序由 Step 的 Sequence 决定）。

4. **生命周期管理**：当 Part 所代表的物理设备被淘汰或报废时，建议先解除其与 WorkCenter 的关系（即删除 `CONTAINS_PART`），再将其状态设为“Inactive”或删除。避免在运行期间引用到失效资源。

5. **与 PartRevision 的关系**：如果 Part 启用了版本管理（PartRevision），则 `CONTAINS_PART` 关系默认指向当前活动版本。如需引用特定版本，可在关系属性中指定 `PartRevision`。在洗碗机产线中，设备升级（如更换新型号夹具）通常建议新增一个 PartRevision，再更新关系指向，保持历史追溯。

6. **权限配置**：创建或修改 `CONTAINS_PART` 关系需要对应的安全角色权限。建议分配 MES 系统管理员或产线建模角色，避免普通操作员误操作。

7. **性能影响**：大规模产线（如包含数百个工位）时，频繁查询 WorkCenter 下所有 Part 可能会影响性能。可考虑缓存策略或利用 Opcenter 的 Material/Resource 查询优化特性。对于洗碗机产线，通常一个工作中心包含 10-30 个 Part，无需特殊优化。

8. **扩展属性**：可根据需要向 `CONTAINS_PART` 关系添加自定义属性，例如 `WorkCenterPartType`（区分工位、设备、模具）、`PriorityLevel`（维护优先级）等，以支持更精细的管理。

## 常见问题 FAQ

**Q: Part 作为资源与作为物料有什么区别？`CONTAINS_PART` 关系中的 Part 能否同时用于物料清单（BOM）？**  
A:  Opcenter 的 Part 对象是多功能的，既可作为物料（制造件、原材料），也可作为资源（设备、工位）。区别在于功能角色：BOM 中的 Part 用于消耗清单，而 `CONTAINS_PART` 中的 Part 代表工作中心内可重复使用的资源。**理论上同一个 Part 可以同时出现在 BOM 和 `CONTAINS_PART` 中**，但实际管理中极易造成混淆（例如“内胆安装夹具”既作为物料被消耗，又作为资源被占用）。建议在实施中严格区分：通过 Part 类型（Category）或不同的序列号体系（Serialized vs Non-Serialized）来避免混用。洗碗机产线中，推荐将 `CONTAINS_PART` 中的 Part 标记为“Resource”类型，BOM 中的 Part 标记为“Material”类型。

**Q: 如何快速确认某个 WorkCenter 下当前所有 Part 的列表？**  
A:  在 Opcenter 客户端，可进入该 WorkCenter 对象的“Relationships”选项卡，选择 `CONTAINS_PART` 关系，系统会列出所有关联 Part。也可通过 Opcenter REST API（示例：`GET /WorkCenters/{workCenterName}/ContainsPart`）获取。如需在报表中展示，可配置 Opcenter 的报表查询，基于 `WorkCenterContainsPart` 表左连接 Part 表。

**Q: 一个工位 Part 在多个 WorkCenter 中轮流使用，如何建模？**  
A:  Opcenter 标准 `CONTAINS_PART` 关系不支持一个 Part 属于多个 WorkCenter。对于此类共享资源（如可移动的测试仪器、中央供料系统），建议采用以下两种方式之一：  
1. **创建 Representational Part**：将该共享资源建模为一个虚拟 Part，只归属于一个“共享资源工作中心”。然后在实际使用的工作中心中，通过其他关系（如 `USES_PART` 或 `DEPENDS_ON_PART`）关联，但需注意这两个关系不带有物理归属语义，仅用于表示依赖。  
2. **使用 Resource 对象而非 Part**：Opcenter 中另有独立的 Resource 实体（如 `Equipment`、`Tool`），它们可以关联到多个 WorkCenter（通过 Resource Assignment）。如果资源管理的要求主要是状态监控和 OEE，更推荐使用 Resource 模型。`CONTAINS_PART` 通常保留给产线内固定工位的建模。

---