Chapter : Recurring Date Requirement Modeling
Introduction
The RecurringDateReq entity (CdoId: 7329) defines periodic equipment maintenance requirements
including BOMs, checklists, data collection definitions, document sets, and email notifications.

In This Chapter
- RecurringDateReq (Recurring Maintenance Requirement)

Relationships:
    RecurringDateReq --(USES_BOM)--> BOM
    RecurringDateReq --(HAS_DOCUMENT_SET)--> DocumentSet

Field Definitions:
- Name (String, Required), Revision (String, Required)
- BOM (Navigation): Maintenance material BOM.
- DataCollectionDef (Navigation): Data collection definition template.
- DocumentSet (Navigation): Associated document set.
- Checklist (SubentityList): Maintenance checklist items.
- DueEmailTarget (Array): Due-date notification email recipients.
- Plus standard revisioned entity fields.
