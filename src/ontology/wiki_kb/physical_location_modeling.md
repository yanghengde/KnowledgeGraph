Chapter : Physical Location Modeling
Introduction
The PhysicalLocation entity defines location groups or containers in a manufacturing
facility. It groups PhysicalPositions into ordered collections and can be typed by
scsStorageType (Mask or Tool storage). PhysicalLocations, together with
PhysicalPositions, form the hierarchical spatial topology model of the factory floor.

In This Chapter
- PhysicalLocation (Physical Location/Area)
- PhysicalLocationPosition (Location-Position Mapping)

PhysicalLocation
A PhysicalLocation is a named grouping container for physical positions. It organizes
multiple PhysicalPosition entries with sequence numbering and can differentiate between
mask storage libraries and tool storage libraries.

Relationship to other modules:

    PhysicalLocation --(HAS_POSITION_ENTRY)--> PhysicalLocationPosition
    PhysicalLocationPosition --(REFERENCES_POSITION)--> PhysicalPosition

Field Definitions:
- Name (String, Required): Unique location/area name.
- Description (String): Description of this location. Defaults to name if not specified.
- Notes (String): Internal notes and comments.
- FilterTags (String): Filter tags, comma separated list.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- ChangeHistory (Navigation): Change history tracking.
- IconId (Integer): Identifier for the associated icon.
- ScsStorageType (Integer): Storage type: 1=Mask, 2=Tool. Used to identify storage library type.
- Positions (SubentityList): Position entries within this location → PhysicalLocationPosition.

PhysicalLocationPosition
Maps a PhysicalPosition to a PhysicalLocation with a sequence number.

Field Definitions:
- Position (Navigation, Required): Physical position reference → PhysicalPosition.
- PositionSequence (Integer): Sequence order of this position within the location.
