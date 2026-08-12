Chapter 10: Product and Material Modeling
Introduction
In Opcenter Execution (Camstar), the Product Information Model defines what is being manufactured. 
It establishes the master data for finished goods, sub-assemblies, and raw materials, as well as 
how these components are assembled together using Bills of Materials (BOMs).

In This Chapter
• Defining Products and Product Families
• Product Revisions and Lifecycle
• Bills of Materials (BOMs)
• Material Definitions

Product
A Product represents a finished good, sub-assembly, or component that is manufactured, tracked, or 
consumed within the MES. Products are the core entity around which WIP (Work in Process) containers 
are created.

Field Definitions:
- Name (String): Unique identifier for the product (产品名称).
- Revision (String): Revision version (修订版本).
- ProductRevision (String): Product revision alias (产品修订版本).
- Description (String): Description of the product (描述).
- ProductType (String): Type, e.g., FinishedGood, SubAssembly, RawMaterial (产品类型).
- DefaultWorkflow (String): The default workflow used to manufacture this product.
- UOM (String): Unit of Measure, e.g., Each, Kg, Liter (计量单位).
- Status (Integer): Active (1), Inactive (2) (状态).
- IsFrozen (Boolean): Whether the product is frozen from editing (是否已冻结).
- IsPhantom (Boolean): Whether this is a phantom part (是否为虚拟件).
- LotControlled (Boolean): Whether the product is lot controlled (是否批次控制).
- SerialControlled (Boolean): Whether the product is serial controlled (是否序列号控制).
- InventoryControlled (Boolean): Whether the product is inventory controlled (是否库存控制).
- ExternallyControlled (Boolean): Whether the product is controlled by an external ERP/PLM system (是否外部系统控制).
- StdCost (Float): Standard manufacturing cost of the product (标准成本).
- PlannedCost (Float): Planned cost of the product (计划成本).
- CurrentCost (Float): Current cost of the product (当前成本).
- StdStartQty (Float): Standard start quantity for production (标准起产数量).
- CustomerProductNumber (String): Product number assigned by the customer (客户产品料号).
- BrandName (String): Brand name under which product is sold (品牌名称).
- CatalogNumber (String): Catalog number of the product (目录编号).
- DeviceType (String): Medical device or component type (器件/设备类型).
- ModelNumber (String): Model number (型号).
- ProductVariation (String): Product variation identifier (产品变体).
- TargetUnitsPerHour (Float): Target throughput in units per hour (目标小时产出数量).
- TargetFinalYield (Float): Target final yield percentage (目标终结良率).
- TargetRolledThroughputYield (Float): Target rolled throughput yield (目标滚动通过良率).
- TargetCycleTime (Float): Target cycle time duration (目标生产周期时长).

Product Family
A Product Family groups related products together. It is used to apply common business rules, 
routing logic, or specifications to multiple products at once without configuring each individually.

Field Definitions:
- Name (String): Unique family name.
- Description (String): Description of the family.
- DefaultWorkflow (String): Default workflow for all products in this family.

Product Revision
Products often undergo engineering changes. A Product Revision tracks different versions of the same 
product, allowing the MES to enforce which revision is currently approved for manufacturing.

Field Definitions:
- RevisionName (String): Identifier for the revision (e.g., 'A', '1.0').
- Product (String): The parent product.
- IsCurrent (Boolean): Indicates if this is the active manufacturing revision.
- EffectiveDate (Date): When this revision becomes active.

BOM (Bill of Materials)
A BOM defines the list of materials and sub-assemblies required to manufacture a specific product. 
In Camstar, a BOM can be associated with a Product or a specific Workflow step to enforce material 
consumption at the correct operation.

The key material relationship chain is:

    Product ──(HAS_BOM)──▶ BOM ──(HAS_ITEM)──▶ BOMItem ──(REFERENCES)──▶ Material

A Product typically has one manufacturing BOM. A MfgOrder then resolves its material requirements 
through this chain: MfgOrder → Product → BOM → BOMItem → Material. A MfgOrder may optionally 
override the Product's BOM via its eS_ProductionBOM field.

Field Definitions:
- Name (String): Unique BOM identifier.
- Description (String): Description of the BOM.
- Product (String): The target product being manufactured.
- BOMType (String): Type (e.g., Engineering, Manufacturing, Phantom).

Material
A Material defines raw inputs or consumables used during production. Unlike products, materials are 
typically purchased rather than manufactured, and are consumed against a BOM.

Field Definitions:
- Name (String): Unique material identifier.
- Supplier (String): Preferred supplier for the material.
- ShelfLife (Integer): Days before the material expires.

Product / Product Family Relationships to Quality:
- USES_DEFAULT_SAMPLING (from Product / ProductFamily, MANY_TO_ONE): 产品或产品家族上配置的默认质量抽样计划。当制造工单 (MfgOrder) 或容器 (Container) 处于此产品或产品家族的上下文时，自动继承和执行对应的抽样检验规则。

Product Relationship to Bill of Process:
- USES_DEFAULT_BOP (from Product, MANY_TO_ONE): 产品指定的默认工艺路线清单 (BOP)。在非 Workflow 模式下，产品默认使用此 BOP 配置进行制造工艺和流程管控。


