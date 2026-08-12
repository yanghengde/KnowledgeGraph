# Swagger 字段翻译对齐报告

本报告仅统计原说明以 `物理字段 ` 开头的占位字段。已有人工说明未被覆盖。

## 汇总

| 指标 | 数量 |
|---|---:|
| 本体属性 | 6807 |
| 当前剩余占位字段 | 4122 |
| Swagger 强匹配 | 349 |
| 其中：英文注释匹配 | 208 |
| 其中：引用目标匹配 | 141 |
| 已对齐中文字段 | 349 |
| 仍待其他资料补充 | 4122 |

## 匹配规则

- 类名仅匹配 Swagger 的 `<ClassName>Entity` 或 `<ClassName>` schema。
- `A_` 前缀物理类额外允许匹配去前缀后的同名 schema。
- 属性名必须完全一致；不使用全局 FieldId，避免不同 CDO 复用 FieldId 导致错配。
- 仅替换占位说明，不覆盖现有人工中文说明。

## 已对齐字段最多的类

| 类 | 字段数 |
|---|---:|
| `Container` | 50 |
| `ScheduledBusinessRule` | 22 |
| `Product` | 18 |
| `Spec` | 13 |
| `A_ResourceBOM` | 12 |
| `A_PhysicalLocation` | 9 |
| `A_PhysicalPosition` | 8 |
| `ComponentDefectReason` | 8 |
| `ResourceStatusCode` | 8 |
| `Vendor` | 8 |
| `Setup` | 7 |
| `ShipmentDestination` | 7 |
| `MfgOrderTaskList` | 6 |
| `ProcessTimer` | 6 |
| `SchedulingRoute` | 6 |
| `Workflow` | 6 |
| `BusinessProcessWorkflow` | 4 |
| `ChecklistTemplate` | 4 |
| `ProcessModelTemplate` | 4 |
| `ResourceFamily` | 4 |
| `BusinessProcessSpec` | 3 |
| `BuyReasonGroup` | 3 |
| `CARSeverity` | 3 |
| `Document` | 3 |
| `ERPBOM` | 3 |
| `Employee` | 3 |
| `MfgOrder` | 3 |
| `ResourceLayout` | 3 |
| `ResourceType` | 3 |
| `SampleDataPoint` | 3 |
| `SampleTest` | 3 |
| `SamplingPlan` | 3 |
| `A_ToolPlan` | 2 |
| `BOM` | 2 |
| `BuyReason` | 2 |
| `MfgOrderTaskStatus` | 2 |
| `Operation` | 2 |
| `PriorityCode` | 2 |
| `RecipeList` | 2 |
| `RegulatoryAgency` | 2 |

完整的 Swagger 原文、来源文件和中文结果保存在 `src/ontology/swagger_field_translations.json`。
