Chapter : Process Object Template Modeling
Introduction
The ProcessObjectTemplate entity is the base template for process objects (PhaseTemplate,
PlanTemplate). It defines the common configuration shared by all process-level templates
including assignee policies, approval workflows, business rules, checklists, time limits,
and organizational applicability.

In This Chapter
- ProcessObjectTemplate (Process Object Template)

ProcessObjectTemplate
A base template entity defining the common fields for PhaseTemplate and PlanTemplate.

Relationship to other modules:

    ProcessObjectTemplate --(HAS_CHECKLIST)--> ChecklistTemplate
    ProcessObjectTemplate --(APPLIES_TO_ORG)--> Organization
    ProcessObjectTemplate --(HAS_ON_START_RULE)--> BusinessRule
    ProcessObjectTemplate --(HAS_ON_COMPLETE_RULE)--> BusinessRule

Field Definitions: Same structure as PhaseTemplate and PlanTemplate.
Refer to phase_template_modeling.md for full field descriptions.
