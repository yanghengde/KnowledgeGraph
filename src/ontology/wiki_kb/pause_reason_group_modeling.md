Chapter : Pause Reason Group Modeling
Introduction
The PauseReasonGroup entity organizes PauseReason codes into hierarchical groups
for structured selection during manufacturing execution. Groups can nest sub-groups
to form a classification tree. The system automatically resolves entries from all nested
levels into the resolvedEntries list for efficient lookup.

In This Chapter
- PauseReasonGroup (Pause Reason Group)

PauseReasonGroup
A PauseReasonGroup is a container that organizes PauseReason entries into logical
categories (e.g., "Equipment Issues", "Material Issues", "Quality Issues") and supports
nested sub-grouping for fine-grained classification.

Relationship to other modules:

    PauseReasonGroup --(HAS_ENTRY)--> PauseReason
    PauseReasonGroup --(HAS_SUBGROUP)--> PauseReasonGroup (self-referencing)

Field Definitions:
- Name (String, Required): Unique group name.
- Description (String): Description of this group. Defaults to name if not specified.
- Notes (String): Internal notes and comments.
- FilterTags (String): Filter tags, comma separated list.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- ChangeHistory (Navigation): Change history tracking.
- IconId (Integer): Identifier for the associated icon.
- EntryType (String): CDO Definition Name of the object type contained in this group.
- Entries (SubentityList): List of PauseReason entries in this group.
- Groups (SubentityList): Nested sub-groups (PauseReasonGroup), enabling multi-level classification.
- DefaultForObjectTypes (Array): List of object type IDs that automatically get this group assigned.
