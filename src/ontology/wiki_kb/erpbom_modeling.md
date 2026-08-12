Chapter 17b: ERP BOM Modeling
Introduction
The ERP BOM (ERPBOM) represents Bills of Materials created and managed by an external ERP system
(e.g., SAP) and downloaded to Opcenter Execution (Camstar/InSite). ERPBOMs are externally controlled,
meaning edits originate from the ERP side and are restricted within InSite.

In This Chapter
• ERPBOM (ERP Bill of Materials)
• ERPBOMItem (ERP BOM Material Line Item)

ERPBOM
An ERPBOM is the ERP-side counterpart to the native Camstar BOM. It is marked as externally controlled
and contains ERP-specific attributes such as the ERP Route/Step reference. ERPBOM material items use a
dedicated table (BOMMaterialListItem) separate from native BOM and MfgOrder material lists.

Relationship to native BOM:

    ERP System ──▶ ERPBOM ──(HAS_ERP_BOM_ITEM)──▶ ERPBOMItem ──(REFERENCES_MATERIAL)──▶ Product
                           └──(erpRoute)──▶ ERP Route/WorkflowStep
    MfgOrder ──(can reference)──▶ ERPBOM

Field Definitions:
- Name (String, Required): Unique identifier for the ERP BOM.
- Revision (String, Required): Revision version.
- Description (String): Description of this ERP BOM.
- BillType (Navigation): BOM type (Manufacturing, Engineering, etc.).
- DefaultProductType (Navigation): Default product type.
- ExternallyControlled (Boolean): Always true for ERPBOMs — controlled by external ERP.
- ERPRoute (Navigation): Reference to the ERP Route/Step where this BOM's materials are consumed.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- IsRevOfRcd (Boolean): Whether this is the current Revision of Record.
- ECO (String): Engineering Change Order number.
- InstanceLocked (Boolean): Whether locked by Change Management.
- FilterTags (String): Comma-separated filter tags.
- Notes (String): Internal notes.
- AssociatedPackages (Integer): Count of associated packages.
- MatchingProds (Navigation): Products that match this ERP BOM.
- MaterialList (SubentityList): List of ERPBOMItem (BOMMaterialListItem) defining ERP-side materials.

ERPBOMItem
An ERPBOMItem represents a single material requirement line in the ERP BOM. Unlike native BOMItem
(ProductMaterialListItem), ERPBOMItem uses the BOMMaterialListItem type stored in a dedicated table.

Field Definitions:
- Name (String): Line item name.
- QtyRequired (Float, Required): Required quantity.
- Qty2Required (Float): Secondary quantity.
- UOM (Navigation): Primary unit of measure.
- UOM2 (Navigation): Secondary unit of measure.
- IssueControl (Integer, Required): Issue tracking policy (1-6).
- ScrapPercent (Float): Expected scrap percentage.
- AssemblySequence (Integer): Assembly order.
- ReferenceDesignator (String): Position identifier on the assembly.
- AllowOverConsumption (Boolean): Allow issuing more than required.
- AllowSubstitution (Boolean): Allow substitute materials.
- EffectiveFromDate (DateTime): Effective start date.
- EffectiveThruDate (DateTime): Effective end date.
- IsPhantom (Boolean): Whether this is a phantom item.
- AdjustmentType (Integer): Auto-adjustment type.
- AdjustmentValue (Float): Auto-adjustment value.
