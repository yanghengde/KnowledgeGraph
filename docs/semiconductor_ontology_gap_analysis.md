# 半导体套件本体差异初步分析

## 1. 分析范围

- 半导体物理表：`docs/Database_Tables.csv`
- 半导体物理字段：`docs/Database_Fields.csv`
- 现有本体：`src/ontology/wiki_kb/*_ontology.json`
- 旧电子套件基线：Git 历史 `ae6a27f^` 中的 `docs/Database_Tables.csv` 与 `docs/Database_Fields.csv`

本报告先记录初始事实盘点和分批方案，后续章节持续记录各批次的实际生成与校验结果。

## 2. 初始总体盘点

| 项目 | 数量 |
|---|---:|
| 半导体物理表 | 1,555 |
| 半导体物理字段 | 21,963 |
| 现有 ontology JSON 文件 | 161 |
| 现有类声明 | 383 |
| 现有唯一类名 | 370 |
| 现有关系声明 | 1,141 |
| 与半导体 CDOName 完全同名的现有类 | 267 |
| 半导体表中没有同名本体类的表 | 1,288 |
| 现有类中没有同名半导体物理表的类 | 103 |
| 重复定义的类名 | 13 |

“没有同名本体类”不等于必须新建本体。物理表中包含大量列表子表、历史表、事务运行表、映射表和系统内部表，这些应映射为属性、关系或暂不纳入，而不是全部作为顶级本体类。

### 最终状态（批次25、逻辑类治理及Neo4j重载后）

| 项目 | 数量 |
|---|---:|
| 本体 JSON 文件 | 186 |
| 唯一本体类 | 579 |
| 与物理表精确同名的类 | 579 |
| 逻辑类（无同名物理表） | 0 |
| 未提升为顶级本体的物理表 | 976 |
| 唯一属性 | 7,749 |
| 本体关系 | 2,163 |
| 物理一致性告警 | 0 |

## 3. 电子套件与半导体套件差异

| 项目 | 旧电子套件 | 新半导体套件 |
|---|---:|---:|
| 物理表 | 1,149 | 1,555 |
| 物理字段 | 15,140 | 21,963 |
| 工作区 | `csi`, `10`, `15`, `60` | `csi`, `10`, `40` |

- 两套套件共有 1,005 张表。
- 半导体新增 550 张表。
- 电子套件移除 144 张表。
- 旧工作区 `15`、`60` 的扩展表已退出，新半导体扩展主要集中在工作区 `40`。
- 半导体新增表中，535 张属于工作区 `40`，15 张属于 `csi`。
- 新增表前缀分布：`A_` 416 张、`ss_` 62 张、`scs` 32 张、其他 40 张。

当前本体中有 13 个类能匹配旧电子套件物理表、但已不在半导体 CSV 中：

`ES_AddressPool`、`ES_CADInstructions`、`ES_DisplayOptions`、`ES_MfgOrderReassignPlan`、`ES_NPIJob`、`ES_Settings`、`ES_ToolPlanMatrix`、`ES_ToolPlanMatrixDetails`、`isAutoStartSettings`、`isInventoryLocation`、`isOEESettings`、`isRecipePlan`、`isUOMConversion`。

这些类应进入“删除、替换或归档”复核清单，不能继续直接加载到半导体 Neo4j。

## 4. 如何判断物理表是否应具备 Ontology

### A. 顶级建模实体

优先生成独立本体类。典型特征：

- 有独立主键；
- 包含 `IsFrozen`、`ChangeHistoryId`；
- 有名称、描述或备注字段；
- 被其他建模对象外键引用；
- 不是明显的 History、Detail、Entries、Map 子表。

半导体新增 550 张表中，初筛约 150 张属于此类。

### B. 支撑建模实体

可能需要独立类，也可能并入所属模块。典型特征：

- 有独立主键和建模字段，但缺少部分标准字段；
- 是版本 Base、状态、类型、规则或矩阵配置；
- 是多个顶级实体的外键目标。

半导体新增表中，初筛约 85 张属于此类。

### C. 子实体、关联表和历史表

通常不生成独立顶级本体文件，应转成：

- `SubentityList` / `Array` 属性；
- `HAS_DETAIL`、`HAS_ENTRY` 等关系；
- 或仅作为运行历史，不进入配置本体。

半导体新增表中，初筛约 291 张属于此类。

### D. 运行时或内部基础设施表

默认不进入第一阶段本体，例如纯事务缓存、集成错误、临时运行数据和 UI 内部表。半导体新增表中初筛约 24 张。

以上数量为规则初筛，最终结论必须逐表检查字段和外键。

## 5. 不能仅按类名判断的迁移映射

半导体套件存在明显的物理命名变化，需要建立别名映射后再校验：

| 现有逻辑类 | 半导体物理表候选 |
|---|---|
| `Resource` | `ResourceDef` |
| `SetupAccess` | `A_SetupAccess` |
| `MfgLine` | `ss_MfgLine` |
| `PhysicalLocation` | `A_PhysicalLocation` |
| `PhysicalPosition` | `A_PhysicalPosition` |
| `PhysicalLocationPosition` | `A_PhysicalLocationPosition` |
| `Printer` | `A_Printer` |
| `ToolPlan` | `A_ToolPlan` |
| `ES_ToolPlanMatrix` | `A_ToolPlanMatrix` |
| `ResourceBOM` | `A_ResourceBOM` / `A_ResourceBOMBase`，待字段确认 |
| `TimerDef` | `Timer`，待确认 |

不能直接把逻辑类名批量改成物理表名。应决定是保留业务友好的 `className` 并增加物理映射元数据，还是统一采用物理 `CDOName`。现有校验规范要求 `className` 对齐物理表，因此后续优先采用物理名，并在中文名和描述中保留业务别名。

## 6. 建议的短批次任务

每批控制在 8–15 个顶级实体，完成 JSON、文档、关系和校验后再进入下一批。

1. **批次 0：迁移治理**
   - 处理 13 个仅属于旧电子套件的类。
   - 处理 13 个重复类定义。
   - 建立逻辑类到半导体物理 CDO 的别名/替换清单。
2. **批次 1：半导体基础主数据**
   - `A_ProductLine`、`A_ProcessArea`、`A_ProcessType`、`A_ProcessCode`
   - `A_MachineGroup`、`A_OperationGroup`
   - `A_MaskSet`、`A_MaskLayer`
   - `A_MaterialType`、`A_MaterialCategory`
3. **批次 2：工艺与设备能力**
   - `A_ProcessSpec`、`A_ProcessSpecStatus`、`A_ProcessCapability`
   - `A_EquipmentMatrix`、`A_EqpConstraintMatrix`
   - `A_RecipeMatrix`、`ss_RecipeGroup`
4. **批次 3：晶圆、批次与实验**
   - 晶圆属性、批次扩展、实验计划及其必要 Base/Detail 结构。
5. **批次 4：SPC、良率与抽样**
   - `A_SPCSetup`、`A_SPCMatrix`、`A_SPCRules`
   - `A_YieldLimits`、`A_YieldType`
   - 半导体抽样与监控配置。
6. **批次 5：WIP、Hold 与时间窗口**
   - `A_WIPDataSetup`、`A_WIPDataName`
   - Future Hold、Min/Max Time Window、运行号和在制品指令。
7. **批次 6：打印、标签、包装与出货**
8. **批次 7：CIO 集成工作区 `10`**
9. **批次 8：剩余支撑实体和跨模块关系闭环**
10. **最终批次：全量物理一致性校验、Neo4j 重载和数量验收**

## 7. 当前结论

- 不应为 1,555 张物理表逐一生成顶级本体。
- 第一阶段应先治理旧电子套件残留和物理命名迁移。
- 半导体净新增 550 张表中，约 235 张是顶级或支撑建模候选；其中仍需通过字段和外键逐个确认。
- 约 291 张新增表明显属于子表、映射表或历史表，应主要转化为属性和关系。
- 建议下一轮只执行“批次 0”，产出明确的删除、替换、保留清单，不直接开始 200 多个实体的生成。

## 8. 执行进度

### 批次 0：已完成

- 增加 `scripts/validate_ontology_vs_csv.py`，建立可重复运行的物理一致性校验基线。
- 删除 13 个确认仅属于旧电子套件的类定义。
- 删除 42 条指向上述旧类的关系。
- 合并 13 个重复类定义，重复类数量从 13 降为 0。
- 增加 `src/ontology/semiconductor_migration_manifest.json`，固化旧类、重复类所有者和待确认的物理重命名。

### 批次 1：已完成

创建 `semiconductor_foundation_ontology.json` 和中英文建模文档，新增 11 个经过物理字段校验的基础实体：

`A_SetupAccess`、`A_ProductLine`、`A_ProcessArea`、`A_ProcessType`、`A_ProcessCode`、`A_MachineGroup`、`A_OperationGroup`、`A_MaskSet`、`A_MaskLayer`、`A_MaterialCategory`、`A_MaterialType`。

这 11 个实体在模块级校验中缺失字段、类型错误、孤立关系端点均为 0。全局精确物理类覆盖由 267 增加至 278。

### 批次 2：已完成

创建 `semiconductor_process_equipment_ontology.json` 和双语建模文档，新增 10 个工艺与设备能力实体：

`A_ProcessSpec`、`A_ProcessSpecStatus`、`A_ProcessCapability`、`A_EquipmentMatrix`、`ss_EqpConstraintMatrix`、`A_RecipeMatrix`、`ss_RecipeGroup`、`A_ModifyAttrsSetup`、`A_EquipmentParamList`、`A_TestProgramSetup`。

本批次包含 151 个物理属性和 50 条当前可闭合的物理外键关系，模块级校验错误为 0。全局精确物理类覆盖由 278 增加至 288。

为控制后续批次的人工误差，新增 `scripts/generate_ontology_batch.py`。该工具只接受经过人工审核的批次实体清单，属性名称、类型、CDO ID、Workspace 和外键目标均从两份物理 CSV 自动提取。

### 批次 3：已完成

新增 13 个晶圆、物项分类与实验配置实体，包含 163 个物理属性和 40 条当前可闭合关系。`Details`、`History` 和Lot运行表未被误建为顶级类。全局精确物理类覆盖达到 301。

### 批次 4：已完成

新增 12 个SPC、良率和抽样配置实体，包含 203 个物理属性和 64 条当前可闭合关系。`A_SPCTxnData`、`A_SPCTxnDataPoint` 被识别为运行数据，明确排除在顶级配置本体之外。全局精确物理类覆盖达到 313。

### 批次 5：已完成

新增 15 个WIP、Hold、时间窗口及公共失败处理实体，包含 233 个物理属性。批次引入邮件组、Hold位置、排程计划、未来Hold和NCR失败配置后，重新生成早期批次关系，使后置依赖自动闭合。全局精确物理类覆盖达到 328。

### 批次 6：已完成

新增 15 个打印、标签、包装和出货配置实体。全局精确物理类覆盖达到 343。

新增 `scripts/generate_all_ontology_batches.py`，可按批次编号顺序重新生成全部已审核模块。每次新增外键目标后，全量重跑批次生成器可自动回填早期模块关系；当前6个半导体模块的模块级物理警告均为0。

### 批次 7–8：已完成

Workspace `10` 的 22 个CIO顶级建模实体已全部覆盖，拆分为连接/消息核心和编排/派工两个模块，共包含 487 个物理属性和 78 条当前闭合关系。CIO明细表、处理器子表和运行表没有被提升为顶级类。

### 批次 9–10：已完成

新增 15 个排程与工艺流实体，以及 15 个质量、IQC与分选实体。`A_TestIQCRuntimeData` 明确作为运行数据排除。

### 批次 11–13：已完成

新增 43 个载具/物料/工装、服务/位置/账户、出货/集成/监控实体。完成后，Workspace `40` 只剩 `A_SPCTxnData`、`A_SPCTxnDataPoint`、`A_TestIQCRuntimeData`、`I_IntegrationError` 四张符合标准字段外观但实质属于运行数据的表，均不创建顶级配置本体。

截至批次 13：

- 新增半导体/CIO顶级实体：171 个；
- 全局精确物理类覆盖：438；
- 重复类定义：0；
- 所有13个新增模块的缺失字段、类型错误、额外属性和可闭合关系警告：0。

### 批次 14–16：已完成

按照已建类指向未建物理目标的外键频次，新增45个高价值支撑实体：

- 公共支撑：`ResourceDef`、用户查询、菜单、状态、位置、审批模板、员工组等；
- 版本Base：BOM、数据采集、维护需求、制造工单程序、排程路线等15个物理Base表；
- CIO与半导体Base：CIO参数/Base，以及实验计划、工艺规格、产品BOM、供料器计划和监控Base。

`ResourceDef`此前被25个物理外键引用，本批次补齐后，新生成模块能够直接指向半导体套件真实资源表。全局精确物理类覆盖达到483；新增模块继续保持模块级物理警告为0。

### 批次 17–19：已完成

新增45个高频明细与参数实体，分别归入工艺/WIP明细、SPC/质量明细、打印/接口/标签明细三个模块：

- 工艺与WIP：ProcessSpec、ProcessCode、实验计划、产品BOM、ToolPlan、测试程序、WIP数据、Future Hold、供料器计划和设备约束等明细；
- SPC与质量：SPC参数/规则/配置明细、自定义数据网格、参数矩阵和IQC参数明细；
- 打印与接口：打印数据项、外部接口明细、服务校验规则、标签追踪和晶圆槽位指令。

截至批次19：

- 已审核生成批次：19个；
- 新增半导体/CIO物理实体：261个；
- 全局精确物理类覆盖：528 / 1,555；
- 本体类总数：618；
- 重复类定义与JSON解析错误：0；
- 所有19个新增模块的缺失字段、额外属性、类型和关系警告：0。

全局剩余告警均来自历史本体模块：缺失物理属性1,391项、额外属性731项、类型不一致96项、缺失可闭合关系559条、无效关系14条。下一阶段应针对旧模块执行可审计的物理字段对齐，而不是继续无差别扩大顶级实体数量。

### 历史本体物理对齐：已完成

新增 `scripts/maintenance/align_existing_ontology_to_csv.py`。该工具默认仅预览，执行写入时会先为全部本体JSON创建带时间戳的完整备份，再依据两份物理CSV重建已有物理类的属性和外键关系；无物理表的逻辑类不在本阶段修改。

对齐528个已有物理类后，全量校验结果：

- 缺失物理属性：0；
- 本体额外属性：0；
- 属性类型不一致：0；
- 缺失可闭合外键关系：0；
- 无效关系端点：0；
- 重复类和解析错误：0。

当前仍有90个逻辑类没有同名物理表、1,027张物理表未提升为顶级本体。这两类差异不等同于错误：前者需要区分抽象语义类与旧套件残留，后者主要包含明细、映射、历史和运行表，应按业务价值继续分批审核。

### 批次 20–21 与逻辑类治理：已完成

- 新增 `A_PhysicalLocationPosition`、`A_PhysicalPosition`、`A_ResourceBOM`、`A_ResourceBOMBase`、`ComponentDefectReason`、`QtyAdjustGroup` 六个物理替代实体；
- 18个旧逻辑名称已映射到真实半导体CDO并删除旧定义；
- 72个既无同名物理表、也无可验证替代的旧逻辑类已从加载本体中清理；
- `TimerDef → Timer` 被明确否决：`Timer` 是运行时记录，不是配置定义；
- 最终534个本体类全部与 `Database_Tables.csv` 精确对齐。

### 最终关系重建与 Neo4j 验收：已完成

加载器改为两阶段批量加载：先创建全部类和属性，再统一创建跨文件关系，避免关系目标尚未加载时被静默跳过。对重复物理字段采用“具有有效外键目标的字段优先”规则，保证外键统一映射为 `Navigation`。

最终严格校验与数据库逐项比对结果：

- 本体文件：186个，全部注册且无重复加载项；
- 类：JSON 579 / Neo4j 579；
- 属性：JSON 7,749 / Neo4j 7,749；
- `HAS_PROPERTY`：7,749；
- `ONTOLOGY_RELATION`：JSON 2,163 / Neo4j 2,163；
- Neo4j 缺失类、额外类、缺失属性、额外属性、缺失关系、额外关系、孤立属性均为0；
- 缺失物理属性、额外本体属性、类型不一致、重复属性、重复关系、无效端点、解析错误均为0。

### 批次 22–25 与逐表覆盖收口：已完成

继续审核逐表覆盖矩阵中的高置信候选，新增45个配置实体：

- 动作、规则、活动、阶段、审批、告警和电子签名；
- 安全权限、KPI、通知变量、代码组和公共配置；
- 用户常量、作业原因/维修/症状代码、SPC图表、CIO出站和WIP消息；
- 半导体Bin代码、Bin定义和Overlay。

最终1,555张物理表的决策分类如下：

| 分类 | 数量 |
|---|---:|
| 已建顶级本体 | 579 |
| 子实体或关联表 | 200 |
| 运行、历史或状态记录 | 495 |
| 非顶级独立记录 | 126 |
| 内部基础设施 | 24 |
| 缺少稳定建模特征的内部/未分类表 | 131 |

完整逐表证据见 `docs/physical_ontology_coverage.csv`，当前没有遗留的顶级或支撑候选。
