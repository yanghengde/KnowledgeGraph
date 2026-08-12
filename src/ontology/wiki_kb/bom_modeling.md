Chapter 17: BOM (Bill of Materials) Modeling
Introduction
The BOM (Bill of Materials) module defines the master list of materials, components, and 
sub-assemblies required to manufacture a product. BOM is the central hub linking Products 
to Materials through BOMItem entries.

In This Chapter
• BOM (Bill of Materials)
• BOMItem (BOM Line Item)
• TDA (Traceability Data Assignment)

BOM
A Bill of Materials (BOM) is a versioned master list of all components needed to build a 
specific product. A BOM contains BOMItems specifying each required material with its quantity 
and issue control policy.

The material relationship chain flows through BOM:

    Product ──(HAS_BOM)──▶ BOM ──(HAS_BOM_ITEM)──▶ BOMItem ──(REFERENCES_MATERIAL)──▶ Material
    MfgOrder ──(RESOLVES_MATERIALS_FROM_BOM)──▶ BOM

Field Definitions:
- Name (String, Required): Unique identifier for the BOM.
- Revision (String, Required): Revision version of the BOM.
- Description (String): Description of this BOM.
- BillType (Navigation): BOM type (Manufacturing, Engineering, Phantom).
- DefaultProductType (Navigation): Default associated product type.
- Status (Integer): 1=Active, 2=Inactive.
- IsFrozen (Boolean, ReadOnly): Whether this BOM is frozen from editing.
- IsRevOfRcd (Boolean): Whether this is the current Revision of Record.
- ECO (String): Engineering Change Order number.
- InstanceLocked (Boolean): Whether locked by Change Management.
- FilterTags (String): Comma-separated filter tags.
- Notes (String): Internal notes.
- AssociatedPackages (Integer): Count of associated packages.
- MaterialList (SubentityList): List of BOMItem (ProductMaterialListItem) defining materials.
- TDAList (SubentityList): List of Traceability Data Assignment records.
- MatchingProds (Navigation): Products that match/use this BOM.

BOMItem
A BOMItem represents a single line in the BOM master list. Each BOMItem references a specific 
Product/Material and defines the quantity required, unit of measure, issue control policy, 
substitution rules, and applicable date range.

Field Definitions:
- Name (String): Name identifier for this BOM line item.
- QtyRequired (Float, Required): Required quantity of this material per unit of product.
- Qty2Required (Float): Secondary quantity (alternate UOM like weight).
- QtyIssued (Float, ReadOnly): Quantity already issued in production.
- UOM (Navigation): Primary unit of measure.
- UOM2 (Navigation): Secondary unit of measure.
- IssueControl (Integer, Required): Issue tracking policy:
  1=Serial (serial-level container tracking)
  2=Bulk (bulk-level container tracking)
  3=Quantity&Lot (quantity and lot tracked, no container)
  4=FloorStock (non-lot-controlled, location recorded)
  5=Quantity (quantities recorded only)
  6=DisplayOnly (displayed but not recorded)
- ScrapPercent (Float): Expected scrap percentage.
- SetupQty (Float): Quantity needed for machine/process setup.
- AssemblySequence (Integer): Order of assembly.
- ReferenceDesignator (String): Position identifier on the assembly (e.g., R1, C3 on PCB).
- AllowOverConsumption (Boolean): Whether to permit issuing more than required.
- AllowUnderConsumption (Boolean): Whether to permit issuing less than required.
- AllowSubstitution (Boolean): Whether substitute materials are allowed.
- AllowAllRevisionsAsSubstitute (Boolean): Whether all product revisions qualify as substitutes.
- VendorControl (Boolean): Whether vendor information is required during issue.
- EffectiveFromDate (DateTime): Date when this BOM item becomes effective.
- EffectiveThruDate (DateTime): Date when this BOM item expires.
- IsPhantom (Boolean, ReadOnly): Whether this is a phantom item (logical grouping, not a real material).
- IsFrozen (Boolean, ReadOnly): Whether this line is frozen from editing.
- AdjustmentType (Integer): Auto-adjustment type (percentage or fixed quantity).
- AdjustmentValue (Float): Auto-adjustment value.
- Product (Navigation): The Product/Material referenced by this BOM line.
- Substitutes (Navigation): List of substitute products/materials.
- PhantomBill (Navigation): For phantom items, references the sub-BOM to expand.
- Spec (Navigation): Optional Spec/step where this material is consumed.
- IssuePoint (Navigation): Point in the workflow where material is issued.

TDA (Traceability Data Assignment)
A TDA record assigns traceability data (PCB serial numbers, Panel containers, defect information) 
to BOM items. This is primarily used in electronics manufacturing for quality tracking.

Field Definitions:
- ListSequence (Integer): Order in the TDA list.
- ObjectName (String): Name of the BOMItem this TDA is assigned to.
- ObjectType (String): CDO type name of the assigned object.
- eS_PCBSerialNumber (String): Serial number of the PCB.
- eS_PanelSerialNumber (String): Serial number of the Panel.
- eS_PCBIndex (String): Index position of the PCB within the Panel.
- eS_Row (Integer): Row position in PCB layout.
- eS_Column (Integer): Column position in PCB layout.
- eS_Count (Integer): Count of open defects causing container failure.
- eS_QualityCheck (Boolean): Whether quality check failed for this serial number.
- eS_XOut (Boolean): Whether this PCB is marked as do-not-populate (no S/N).
- eS_Container (Navigation): Container reference (Panel/PCB serialized container).
- eS_DefectReason (Navigation): Reason code for defects.
- ResourceSlot (Navigation): Resource slot assignment.
- eS_RepairActions (Navigation): Valid repair action codes.
