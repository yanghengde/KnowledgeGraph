Chapter : Product Conversion Plan Modeling
Introduction
The ProductConversionPlan entity (CdoId: 4792605) defines product conversion/change plans
specifying the rules and steps for converting products from one state or specification to another.

In This Chapter
- ProductConversionPlan (Product Conversion Plan)

Field Definitions:
- Name (String, Required): Unique plan name.
- Details (SubentityList): Product conversion detail entries → ProdConvertPlanDetail.
- SetupAccess (Navigation): Setup access configuration.
- Plus standard fields: Description, Notes, FilterTags, IsFrozen, InstanceLocked, ChangeHistory, IconId.
