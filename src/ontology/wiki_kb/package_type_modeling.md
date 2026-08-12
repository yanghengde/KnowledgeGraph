Chapter : Package Type Modeling
Introduction
The PackageType entity defines the classification of change management packages in Opcenter
Execution. It serves as a lookup/catalog entity that categorizes packages (e.g., Engineering
Change, Document Change, Process Change) and is referenced by PackageCreationTemplate
to determine the business classification and processing path of change packages.

In This Chapter
- PackageType (Change Package Type)

PackageType
A PackageType is a named catalog entry that classifies change management packages.
It is used by PackageCreationTemplate to categorize and route change packages
appropriately within the Change Management module.

Relationship to other modules:

    PackageCreationTemplate --(HAS_PACKAGE_TYPE)--> PackageType

Field Definitions:
- Name (String, Required): Unique package type name.
- Description (String): Description of this package type. Defaults to name if not specified.
- Notes (String): Internal notes and comments.
- FilterTags (String): Filter tags, comma separated list.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- ChangeHistory (Navigation): Change history tracking.
- IconId (Integer): Identifier for the associated icon.
