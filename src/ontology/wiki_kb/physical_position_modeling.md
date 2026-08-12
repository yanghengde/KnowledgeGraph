Chapter : Physical Position Modeling
Introduction
The PhysicalPosition entity defines individual physical positions or slots within a
manufacturing environment. These positions represent granular locations such as
equipment slots, carrier grid positions, or workstation numbers. PhysicalPositions
are grouped and sequenced within PhysicalLocations to form hierarchical spatial
models of the factory floor.

In This Chapter
- PhysicalPosition (Physical Position/Slot)

PhysicalPosition
A PhysicalPosition is a named catalog entry representing a single physical position.
It is referenced by PhysicalLocation through the positions subentity list, which
assigns a sequence number to each position within the location.

Relationship to other modules:

    PhysicalLocation --(CONTAINS_POSITION)--> PhysicalPosition

Field Definitions:
- Name (String, Required): Unique position name.
- Description (String): Description of this position. Defaults to name if not specified.
- Notes (String): Internal notes and comments.
- FilterTags (String): Filter tags, comma separated list.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- ChangeHistory (Navigation): Change history tracking.
- IconId (Integer): Identifier for the associated icon.
