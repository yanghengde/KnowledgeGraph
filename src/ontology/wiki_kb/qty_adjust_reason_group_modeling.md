Chapter : Qty Adjust Reason Group Modeling
Introduction
The QtyAdjustReasonGroup entity (CdoId: 8988) organizes quantity adjustment reason codes
into hierarchical groups for structured selection during inventory transactions.

In This Chapter
- QtyAdjustReasonGroup (Quantity Adjust Reason Group)

Relationships:
    QtyAdjustReasonGroup --(HAS_ENTRY)--> QtyAdjustReason
    QtyAdjustReasonGroup --(HAS_SUBGROUP)--> QtyAdjustReasonGroup (self-referencing)

Field Definitions:
- Name (String, Required): Unique group name.
- EntryType (String): CDO Definition Name of contained object type.
- Entries (SubentityList): QtyAdjustReason entries.
- Groups (SubentityList): Nested sub-groups.
- DefaultForObjectTypes (Array): Auto-assign object type IDs.
- Plus standard base fields.
