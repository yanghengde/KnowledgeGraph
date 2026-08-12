Chapter : Qty Adjust Reason Modeling
Introduction
The QtyAdjustReason entity defines reason codes for inventory quantity adjustments.
These codes are organized into QtyAdjustReasonGroup collections for structured
selection during shop floor transactions.

In This Chapter
- QtyAdjustReason (Quantity Adjust Reason Code)

QtyAdjustReason
A named catalog entry classifying the reason for inventory quantity adjustments.

Relationship: QtyAdjustReasonGroup --(HAS_ENTRY)--> QtyAdjustReason

Field Definitions: Name (Required), Description, Notes, FilterTags, IsFrozen, InstanceLocked, ChangeHistory, IconId.
