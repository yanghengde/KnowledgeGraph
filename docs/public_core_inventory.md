# Camstar 公共核心本体盘点

本报告从当前项目文件生成；归组是治理建议，不是已经生效的发布配置。未修改模型、数据库或活动发布版本。

## 当前事实

- ontologyFiles: 192
- uniqueClasses: 593
- classDefinitions: 911
- classesWithDuplicateDefinitions: 318
- relationshipDeclarations: 2386
- uniqueRelationshipTriples: 1677
- classesWithPropertyTypeConflicts: 9
- conflictingClassProperties: 9

重复定义不等于数据库存在重复节点，但同名属性、中文名和模块归属可能在加载时被不同文件覆盖。权威来源必须逐类确认，不能按文件顺序裁决。

## 建议公共核心与首期业务骨架

### 组织与位置

| 类 | 中文名 | 属性数（按文件） | 主键候选（物理声明） | 引用它的类数 | 重复/类型冲突 |
|---|---|---|---|---|---|
| Enterprise | 企业/集团 | 11/11 | EnterpriseId | 1 | 重复定义 / 0 |
| Site | 站点 | 13/13 | SiteId | 2 | 重复定义 / 0 |
| Factory | 工厂 | 82/79 | FactoryId | 12 | 重复定义 / 0 |
| WorkCenter | 工作中心 | 18/18 | WorkCenterId | 6 | 重复定义 / 0 |
| ss_MfgLine | 半导体制造线 | 8 | ss_MfgLineId | 4 | 单一定义 / 0 |
| Organization | 组织 | 17/17 | OrganizationId | 12 | 重复定义 / 0 |

### 产品与计量

| 类 | 中文名 | 属性数（按文件） | 主键候选（物理声明） | 引用它的类数 | 重复/类型冲突 |
|---|---|---|---|---|---|
| Product | 产品 | 158/145 | ProductId | 69 | 重复定义 / 1 |
| ProductBase | 产品基线 | 4/4 | ProductBaseId | 1 | 重复定义 / 0 |
| ProductFamily | 产品族 | 45/24 | ProductFamilyId | 3 | 重复定义 / 0 |
| UOM | 计量单位 | 9/9 | UOMId | 30 | 重复定义 / 0 |

### 人员与职责

| 类 | 中文名 | 属性数（按文件） | 主键候选（物理声明） | 引用它的类数 | 重复/类型冲突 |
|---|---|---|---|---|---|
| Employee | 员工 | 44/41 | EmployeeId | 36 | 重复定义 / 0 |
| RoleDef | 角色定义 | 9/9 | RoleId | 20 | 重复定义 / 0 |
| Team | 班组/团队 | 8/8 | TeamId | 1 | 重复定义 / 0 |

### 设备与资源

| 类 | 中文名 | 属性数（按文件） | 主键候选（物理声明） | 引用它的类数 | 重复/类型冲突 |
|---|---|---|---|---|---|
| ResourceDef | 资源定义 | 94/114 | ResourceId | 47 | 重复定义 / 0 |
| ResourceFamily | 资源家族 | 31/25 | ResourceFamilyId | 15 | 重复定义 / 0 |
| ResourceType | 资源类型 | 10/10 | ResourceTypeId | 2 | 重复定义 / 0 |

### 后续共享对象

| 类 | 中文名 | 属性数（按文件） | 主键候选（物理声明） | 引用它的类数 | 重复/类型冲突 |
|---|---|---|---|---|---|
| Vendor | 供应商 | 8/8 | VendorId | 8 | 重复定义 / 0 |
| Customer | 客户 | 19/19 | CustomerId | 7 | 重复定义 / 0 |
| Owner | Owner 责任人 | 9/9 | OwnerId | 30 | 重复定义 / 0 |
| Location | 位置 | 7/7 | LocationId | 8 | 重复定义 / 0 |

### 首期业务骨架（不归公共主数据）

| 类 | 中文名 | 属性数（按文件） | 主键候选（物理声明） | 引用它的类数 | 重复/类型冲突 |
|---|---|---|---|---|---|
| MfgOrder | 制造工单 | 89/75 | MfgOrderId | 12 | 重复定义 / 0 |
| Container | 容器 | 189/148 | ContainerId | 29 | 重复定义 / 0 |
| Workflow | 工作流 | 22/31 | WorkflowId | 41 | 重复定义 / 0 |
| WorkflowStep | 工作流步骤 | 24/22 | WorkflowStepId | 53 | 重复定义 / 0 |
| Spec | 规范/规格 | 106/114 | SpecId | 63 | 重复定义 / 0 |
| Operation | 工序/操作 | 39/44 | OperationId | 9 | 重复定义 / 0 |

主键列只是物理候选；实际对象 URI 必须确认复合键、版本和来源实例标识。引用次数仅辅助判断共享程度，不表示业务优先级。

## 跨文件同名属性类型冲突

| 类.属性 | 各类型与来源 |
|---|---|
| A_JobCauseCode.setupAccess | Integer: csv_business_import_ontology.json；Navigation: semiconductor_user_job_spc_configuration_ontology.json |
| A_JobModel.setupAccess | Integer: csv_business_import_ontology.json；Navigation: semiconductor_shared_support_ontology.json |
| A_JobRepairCode.setupAccess | Integer: csv_business_import_ontology.json；Navigation: semiconductor_user_job_spc_configuration_ontology.json |
| A_JobStage.setupAccess | Integer: csv_business_import_ontology.json；Navigation: semiconductor_user_job_spc_configuration_ontology.json |
| A_JobSymptomCode.setupAccess | Integer: csv_business_import_ontology.json；Navigation: semiconductor_user_job_spc_configuration_ontology.json |
| A_PhysicalLocation.setupAccess | Integer: csv_business_import_ontology.json；Navigation: semiconductor_shared_support_ontology.json |
| A_PhysicalPosition.setupAccess | Integer: csv_business_import_ontology.json；Navigation: semiconductor_physical_resource_replacements_ontology.json |
| A_ResourceBOM.setupAccess | Integer: csv_business_import_ontology.json；Navigation: semiconductor_physical_resource_replacements_ontology.json |
| Product.materialCategory | String: csv_business_import_ontology.json；Navigation: product_ontology.json |

## 如何最简单地落地

1. 全部 593 类留在目录中，先治理 16 个公共核心候选（前四组）；供应商、客户、所有者和位置 4 类后续纳入。订单、批次、工艺 6 类单独作为首期业务骨架。
2. 生成每类一张模型卡：业务定义、权威来源、物理键、常用属性、关系、发布状态。CSV 导入改为已有类的差异审阅候选，而非第二份自动生效定义；该机制本次仅建议，尚未实施。
3. 依据物理 CSV 逐项确认冲突，再合并业务说明与扩展属性。先保护版本标识、外键和关系终点；附加属性不直接删除，应区分业务扩展、计算属性与错误字段。
4. 问数按发布范围提供常用问题：有哪些对象、多少个、某订单对应什么产品。固定查询依据模型生成，仅开放已验证的单跳关系。用户不需要选查询语言或传输方式。
5. 完整本体治理与实例全量导入分开：先统一模型，数据先接一条业务链。未发布、无数据、查询失败三种状态明确区分。复杂分析、权限深化与亿级容量后续推进。

## 本项目的具体注意事项

- Material、MfgLine、Resource、Role、Supplier 不是当前同名本体类；material 和 mfgline 文件没有类定义。实际候选包括 ss_MfgLine、ResourceDef、RoleDef、Vendor。不要仅凭文件名或中文词新增重复实体。物料概念需结合 Product、BOM及物料类别关系确认，不能直接等同。
- Product.materialCategory 存在 Navigation/String 冲突。物理 Product.MaterialCategoryId 是指向 A_MaterialCategory 的外键，应保留导航语义；物理校验器合并同名属性后检查，因此总类型错误为零不能排除文件间冲突。
- Site 定义包含 password 属性：通用模型字段不应默认进入问数/业务发布属性集，应采用业务属性白名单。此盘点未读取密码值，也未证明该字段已被发布。
- 旧 docs/ontology_csv_validation_report.md 引用 CamstarSemiOntology 目录；本次重新校验结果见 ontology_current_inventory_validation.md。
- 全量可追溯来源、主键候选、出边及冲突见 public_core_inventory.json。canonicalSource 为 null，表示尚未裁决，不表示没有源文件。
