Chapter : Pause Reason Modeling
Introduction
The PauseReason entity defines reason codes for equipment/station pauses during
manufacturing execution. These codes (e.g., material shortage, equipment failure,
quality inspection) are grouped into PauseReasonGroup entries and are selected by
operators during shop floor transactions to categorize pause events.

In This Chapter
- PauseReason (Pause Reason Code)

PauseReason
A PauseReason is a named catalog entry that classifies the reason for production pauses.
It is organized into PauseReasonGroup collections for structured selection during
manufacturing execution.

Relationship to other modules:

    PauseReasonGroup --(HAS_ENTRY)--> PauseReason

Field Definitions:
- Name (String, Required): Unique pause reason code name.
- Description (String): Description of this pause reason. Defaults to name if not specified.
- Notes (String): Internal notes and comments.
- FilterTags (String): Filter tags, comma separated list.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- ChangeHistory (Navigation): Change history tracking.
- IconId (Integer): Identifier for the associated icon.
