Chapter 7b: Bill of Process (BOP) Modeling
Introduction
The Bill of Process (BOP) defines the manufacturing process routing for a product, including
process overrides for product/factory-specific variations. BOP bridges Product and Workflow,
allowing MfgOrders to specify which process definition to use.

In This Chapter
• BillOfProcess (BOP Definition)
• BillOfProcessOverride (Process Override)

BillOfProcess
A Bill of Process (BOP) is a versioned manufacturing process definition. Unlike Workflow which defines the step-by-step routing, BOP focuses on process-level configuration with overrides for different products and factories. Product references BOP via its USES_DEFAULT_BOP relation, and MfgOrder references BOP via USES_BOP.

Relationship chain:

    Product ──(USES_DEFAULT_BOP)──▶ BillOfProcess ──(HAS_OVERRIDE)──▶ BillOfProcessOverride
    MfgOrder ──(USES_BOP)─────────▶ BillOfProcess

Field Definitions:
- Name (String, Required): Unique BOP name.
- Revision (String, Required): Revision version.
- Description (String): Description of the BOP.
- Status (Integer): 1=Active, 2=Inactive.
- IsRevOfRcd (Boolean): Whether this is the current Revision of Record.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- Notes (String): Internal notes.
- InstanceLocked (Boolean): Whether locked by Change Management.
- FilterTags (String): Filter tags.
- AssociatedPackages (Integer): Count of associated packages.
- ChangeHistory (Navigation): Change history tracking.
- ECO (String): Engineering Change Order number (工程变更单号).
- ChangeCount (Integer): Count of changes/revisions (变更计数).
- CDOTypeId (Integer): CDO Definition Type ID (CDO类型标识).

BillOfProcessOverride
A Bill of Process Override defines product/factory-specific variations to the base BOP configuration. This allows a single BOP to be adapted for different production scenarios without duplicating the entire process definition.

Field Definitions:
- Name (String): Override name.
- TargetProduct (Navigation): Product this override applies to.
- TargetFactory (Navigation): Factory this override applies to.
- OverrideValue (String): The specific parameter override value.
- CDOTypeId (Integer): CDO Definition Type ID (CDO类型标识).
- ChangeCount (Integer): Count of changes/revisions (变更计数).
- IsFrozen (Boolean): Whether frozen from editing (是否已冻结).
- ExportImportKey (String): Export/Import key (导出导入密钥).

BillOfProcessOverride Relationships:
- OVERRIDES_SPEC (to Spec, MANY_TO_ONE): 工艺覆盖指定的覆盖工艺规范(Spec)
- OVERRIDES_SETUP (to Setup, MANY_TO_ONE): 工艺覆盖指定的覆盖设备物理配置(Setup)
- OVERRIDES_RECIPE (to Document, MANY_TO_ONE): 工艺覆盖指定的覆盖配方文档(Recipe/Document)
- OVERRIDES_EPROCEDURE (to ElectronicProcedure, MANY_TO_ONE): 工艺覆盖指定的覆盖电子引导程序(ElectronicProcedure)
- OVERRIDES_RESOURCE_GROUP (to ResourceGroup, MANY_TO_ONE): 工艺覆盖指定的覆盖资源组(ResourceGroup)
- OVERRIDES_TRAINING_TEAM (to Team, MANY_TO_ONE): 工艺覆盖指定的覆盖培训考核班组(Team)
- TARGETS_PRODUCT (to Product, MANY_TO_ONE): 工艺覆盖针对特定产品生效
- TARGETS_FACTORY (to Factory, MANY_TO_ONE): 工艺覆盖针对特定工厂生效
