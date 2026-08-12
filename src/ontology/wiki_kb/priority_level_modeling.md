Chapter : Priority Level Modeling
Introduction
The PriorityLevel entity defines priority classification levels used throughout Opcenter Execution
to categorize urgency of business objects such as quality events, change packages, and
manufacturing orders.

In This Chapter
- PriorityLevel (Priority Level)

PriorityLevel
A PriorityLevel is a named catalog entry (CdoId: 7475) that defines a priority tier.

Field Definitions:
- Name (String, Required): Unique priority level name (e.g., High, Medium, Low).
- Description (String): Description.
- Notes (String): Internal notes.
- FilterTags (String): Filter tags.
- IsFrozen (Boolean, ReadOnly): Whether frozen.
- InstanceLocked (Boolean): Change Management lock.
- ChangeHistory (Navigation): Change history.
- IconId (Integer): Icon ID.
