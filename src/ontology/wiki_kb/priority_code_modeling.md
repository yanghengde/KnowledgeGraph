Chapter : Priority Code Modeling
Introduction
The PriorityCode entity defines priority code identifiers used in change management and
other modules to assign urgency levels to business objects. Unlike PriorityLevel (which
defines tier levels), PriorityCode provides named priority codes (e.g., P1-Critical)
and can be associated with WIP message definitions for shop floor notifications.

In This Chapter
- PriorityCode (Priority Code)

PriorityCode
A PriorityCode is a named catalog entry (CdoId: 4280) defining a priority identifier.
It is referenced by PackageCreationTemplate to set the default package priority,
and can be associated with WIP messages.

Relationship to other modules:

    PackageCreationTemplate --(HAS_PRIORITY)--> PriorityCode

Field Definitions:
- Name (String, Required): Unique priority code name.
- Description (String): Description.
- Notes (String): Internal notes.
- FilterTags (String): Filter tags.
- IsFrozen (Boolean, ReadOnly): Whether frozen.
- InstanceLocked (Boolean): Change Management lock.
- ChangeHistory (Navigation): Change history.
- IconId (Integer): Icon ID.
- WipMsgDefMgr (Navigation): WIP message definition manager → WIPMsgEntity.
