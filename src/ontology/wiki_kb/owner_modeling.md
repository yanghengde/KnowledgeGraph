Chapter : Owner Modeling
Introduction
The Owner entity represents the responsible party for quality object categories and event
classifications in Opcenter Execution. Owners are assigned within CategoryMap and
EventClassificationSpecMap sub-entities of Organization to define default responsibility
for handling specific quality object types. Owners can also be associated with WIP Message
Definitions to configure shop floor transaction messaging.

In This Chapter
- Owner (Responsible Party)

Owner
An Owner is a named entity that represents a responsible party for quality processing.
It is referenced by CategoryMap (within Organization) and EventClassificationSpecMap
to define who is responsible for a given Category or Event Classification/Subclassification
combination.

Relationship to other modules:

    CategoryMap --(HAS_OWNER)--> Owner
    EventClassificationSpecMap --(HAS_OWNER)--> Owner
    Owner --(HAS_WIP_MSG)--> WIPMsgEntity

Field Definitions:
- Name (String, Required): Unique owner name.
- Description (String): Description of this owner. Defaults to name if not specified.
- Notes (String): Internal notes and comments.
- FilterTags (String): Filter tags, comma separated list.
- IconId (Integer): Identifier for the icon associated with this entity.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- ChangeHistory (Navigation): Change history tracking.
- WipMsgDefMgr (Navigation): WIP Message Definition Manager for shop floor messaging.
