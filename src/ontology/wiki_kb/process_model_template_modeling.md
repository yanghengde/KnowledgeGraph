Chapter : Process Model Template Modeling
Introduction
The ProcessModelTemplate entity (CdoId: 7700) is the top-level process model template.
It provides the complete configuration for a process model including assignee policies,
approval workflows, business rules, checklists, time limits, and additional BOM-related
query settings.

In This Chapter
- ProcessModelTemplate (Process Model Template)

ProcessModelTemplate
Top-level process model template with all ProcessObjectTemplate fields plus
phantom BOM query and MaterialListItem type settings.

Relationship to other modules:

    ProcessModelTemplate --(HAS_CHECKLIST)--> ChecklistTemplate
    ProcessModelTemplate --(APPLIES_TO_ORG)--> Organization
    ProcessModelTemplate --(HAS_ON_START_RULE)--> BusinessRule
    ProcessModelTemplate --(HAS_ON_COMPLETE_RULE)--> BusinessRule

Field Definitions: Same as ProcessObjectTemplate plus:
- QueryName (String): Query name for phantom BOM items.
- QueryName1 (String): Query name for MaterialListItems.
- TypeName (String): MaterialListItem type name (e.g., ProductMaterialListItem).
