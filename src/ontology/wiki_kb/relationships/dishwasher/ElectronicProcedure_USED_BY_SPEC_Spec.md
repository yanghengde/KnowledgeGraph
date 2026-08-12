# ElectronicProcedure → USED_BY_SPEC → Spec

> **产品线**: 洗碗机产线  
> **基数**: MANY_TO_ONE  
> **生成时间**: 2026-05-06  
> **来源**: LLM 自动生成  

## 关系说明

在 Siemens Opcenter (Camstar) MES 中，`ElectronicProcedure`（电子程序）通过 `USED_BY_SPEC` 关系与 `Spec`（规范）关联。该关系定义了**多个电子程序可以被一个规范引用**，即一个 Spec 可以引用多个 ElectronicProcedure，而一个 ElectronicProcedure 只能属于一个 Spec（但实际建模中通过 Relation 的多对一方向实现）。这种设计用于将离散的操作指导（如作业指导书、视频、检查清单）绑定到产品、工艺或工位的 Specification 上，从而在执行生产步骤时向操作员提供精准的电子化指引。

在洗碗机产线场景中，`Spec` 通常代表**某一机型或某一工序的工艺规范**（如“内胆组装规范”“电气安全测试规范”），而 `ElectronicProcedure` 则承载该规范下具体的操作内容，例如：  
- 装配顺序的动画演示文件  
- 扭矩枪设定参数及验证步骤  
- 密封圈安装的检查要点图片  
- 防水测试的操作视频  

多个 ElectronicProcedure 可以共存于同一个 Spec 下，以覆盖不同视角或不同技能层次的操作引导。当制造工单引用该 Spec 时，MES 会自动将关联的 ElectronicProcedure 推送至工位终端，确保操作员获得一致、最新的信息。

## 业务场景

### 何时需要配置此关系？

**1. 新机型导入或设计变更**  
当洗碗机产线引入新型号（如带自清洁功能的机型）或关键部件（如新型喷淋臂）时，工艺工程师需创建或更新对应的 `Spec`，并将操作指导文件（新建的 ElectronicProcedure）与 Spec 关联，确保现场执行的是最新版本。

**2. 分步式复杂工序**  
对于需要多个步骤且依赖不同技能或设备的工序（例如“洗碗机门板总装”分为：铰链安装、门封条嵌入、控制面板接线），每个步骤可独立配置 ElectronicProcedure（如步骤视频、力矩检查表），但所有步骤共享同一个顶层 Spec，便于追溯和版本控制。

**3. 多语言 / 多技能操作引导**  
同一台洗碗机的装配规范，可能需要为熟练工提供精简版 Checklist（一个 EP），为新员工提供详细动画（另一个 EP），或为不同语言区域提供不同语言版本的指导文件。此时都通过同一个 Spec 引用多个 EP 实现。

### 洗碗机产线 典型示例

**场景**：洗碗机内胆组件密封性测试工序（`Spec_SealTest`）  
**配置步骤**：

1. 在 Opcenter 中创建 Spec 对象，名称为 `Spec_WD500_SealTest`，对应某型号洗碗机内胆密封测试规范。
2. 创建三个 ElectronicProcedure：
   - `EP_Seal_Test_Video`（内容：MP4 视频，展示标准操作动作）
   - `EP_Seal_Test_Parameters`（内容：PDF，定义测试压力、保压时间、合格判定标准）
   - `EP_Seal_Test_Checklist`（内容：平板上的勾选框列表，包含气密性、外观检查项）
3. 使用 `USED_BY_SPEC` 关系将三个 EP 分别指向 `Spec_WD500_SealTest`。
4. 在实际生产时，MES 为工单分配该 Spec，工位终端依次显示三个 EP，操作员可按顺序执行或按需切换。

**参数示例**：
- Relation 方向：ElectronicProcedure → USED_BY_SPEC → Spec  
- 基数：一个 Spec 可关联多个 EP，一个 EP 只能归属一个 Spec（逻辑上可复用，但实际建议独占避免混乱）  
- 启用版本控制：每个 EP 均可独立版本化，Spec 引用时可指定版本号或默认最新。

## 配置要点

1. **避免一对多造成冗余**：虽然基数允许一个 Spec 引用多个 EP，但不要把相同内容的 EP 重复关联，应保持每个 EP 职责单一（如“仅包含安装图”或“仅包含视频”），提高可维护性。
2. **版本控制策略**：当 Spec 或 EP 有修订时，建议同时更新两者的版本，并清理旧关联。可使用 Opcenter 的版本化功能，确保生产环境使用 Superseded 标记的旧版本不在工位显示。
3. **与工步/操作数的映射**：在工序建模时，一个 Spec 可能对应多个工步（Operations），而 ElectronicProcedure 可能只对应特定工步。可在 Spec 中设置属性字段（如 `StepName`）来区分不同 EP 的适用位置，或在 UIF 中通过标签过滤。
4. **命名规范**：建议采用 `EP_{SpecName}_{序号}_{内容类型}` 的命名规则，例如 `EP_SealTest_01_Video`，方便检索。
5. **权限控制**：ElectronicProcedure 的创建和修改建议只开放给工艺工程师，操作员只有执行权限，防止误修改影响生产。
6. **文件大小与加载性能**：如果 EP 包含大文件（如高清视频），需考虑 MES 终端的网络带宽和本地缓存策略。建议将大型媒体文件存放于 CDN 或共享文件夹，EP 仅存储链接。
7. **多语言支持**：若产线需要多语言界面，每个语言版本的 EP 应单独创建并关联到同一个 Spec，或通过 EP 属性 `Language` 区分，由终端根据用户偏好动态加载。
8. **回收规则**：当 Spec 被废弃或替换时，应及时解除其与 EP 的 `USED_BY_SPEC` 关联，并标记 EP 为 Inactive，避免出现孤立的电子程序。

## 常见问题 FAQ

**Q: 一个 ElectronicProcedure 能否被多个 Spec 引用？**  
A: 根据基数 `MANY_TO_ONE`，在标准本体中一个 EP 只能被一个 Spec 通过 `USED_BY_SPEC` 关系引用。若需要复用到其他 Spec，建议**复制** EP 为新实例后再关联，或通过 Opcenter 的 “Reference” 功能间接实现（需自定义扩展）。在洗碗机产线中，建议为每个 Spec 独立维护 EP，避免修改一个 EP 影响多个 Spec。

**Q: 如何批量将多个 EP 关联到同一个 Spec？**  
A: 在 Opcenter 建模工具（如 MES Admin Console）中，先选中 Spec，再使用 “Add Existing” 功能选择多个 ElectronicProcedure 一次性关联。也可通过导入 Excel 表单（若支持自定义导入模板）批量创建 Relation 记录。注意批量操作前检查版本一致性。

**Q: 删除 Spec 或 EP 后，关联关系会自动清理吗？**  
A: 不会自动清理。删除 Spec 时，与之关联的 EP 并不会被删除，但会变成无归属的孤点（Orphan）。删除 EP 时，Spec 下的关联记录会被标记为无效（如果系统配置了级联删除则可能直接删除）。建议在删除前先手动解除所有 `USED_BY_SPEC` 关联，或使用 Opcenter 的 “Delete with Dependencies” 选项（需谨慎）。在洗碗机产线中，推荐先废弃 Spec 再逐个清理 EP，保留历史审计所需。