Chapter : Product Family Modeling
Introduction
The ProductFamily entity (CdoId: 4760) groups similar products for unified configuration management.
It defines numbering rules, serial number policies, cost tracking, material exposure controls,
and is referenced by PartIdealCycle and PartFamilyIdealCycle for cycle time configuration.

In This Chapter
- ProductFamily (Product Family)

ProductFamily
A revisioned entity grouping similar products with shared manufacturing configurations.

Relationship to other modules:
    PartIdealCycle --(APPLIES_TO_PRODUCT_FAMILY)--> ProductFamily
    PartFamilyIdealCycle --(APPLIES_TO_PRODUCT_FAMILY)--> ProductFamily

Key Fields: containerNumberingRule, serial number configs (1-4), cost, material exposure propagation.
