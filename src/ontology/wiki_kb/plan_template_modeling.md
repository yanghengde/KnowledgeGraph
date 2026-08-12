Chapter : Plan Template Modeling
Introduction
The PlanTemplate entity defines the configuration template for quality action plans
(e.g., corrective actions, preventive actions) in Opcenter Execution. Plan templates
specify assignee policies, approval workflows, business rules to execute on start/complete,
checklists, document sets, time limits, and organizational applicability.
PlanTemplateDisposition is a specialized subtype for disposition plans.

In This Chapter
- PlanTemplate (Action Plan Template)

PlanTemplate
A PlanTemplate is a reusable template for quality action plan workflows (CdoId: 7672).
It controls how a plan step behaves, who is responsible, what approvals are needed,
and which business rules fire on entry and exit.

Relationship to other modules:

    PlanTemplate --(HAS_CHECKLIST)--> ChecklistTemplate
    PlanTemplate --(APPLIES_TO_ORG)--> Organization
    PlanTemplate --(HAS_ON_START_RULE)--> BusinessRule
    PlanTemplate --(HAS_ON_COMPLETE_RULE)--> BusinessRule

Field Definitions (same structure as PhaseTemplate):
- Name (String, Required): Unique plan template name.
- Description (String): Description.
- Notes (String): Internal notes.
- FilterTags (String): Filter tags.
- IsFrozen (Boolean): Whether frozen.
- InstanceLocked (Boolean): Change Management lock.
- ChangeHistory (Navigation): Change history.
- IconId (Integer): Icon ID.
- Status (Integer): 1=Active, 2=Inactive.
- IsRequired (Boolean): Whether plan is mandatory.
- AutoStart (Boolean): Auto-start on route/approval.
- AutoComplete (Boolean): Auto-close on complete.
- DefaultAssigneeInfo (Boolean): Inherit assignee from parent.
- Assignee (Navigation): Default assignee → Employee.
- AssigneeOption (Integer): 1=Assignee, 2=Owner, 3=Collaborator.
- AssigneeRole (Navigation): Assignee role → Role.
- AllowReassignment (Integer): 1=Within roles, 2=Any, 3=Not allowed.
- ApprovalRequired (Boolean): Approval before processing.
- CompleteWithinQty (Integer): Time limit quantity.
- CompleteWithinUOM (Float): Time unit (1=Hour, 24=Day, 168=Week).
- DocumentSet (Navigation): Document set → DocumentSet.
- RuleList (String): Business rule field name.
- ExecutionContextType (Integer): Rule execution context.
- Organizations (Array): Applicable organizations → Organization.
- ApprovalSheets (SubentityList): Approval sheets → ApprovalSheet.
- Checklist (Navigation): Checklist → ChecklistTemplate.
- Details (SubentityList): Sub-plans → ProcessObject.
- OnStartRules (SubentityList): Start rules → BusinessRule.
- OnCompleteRules (SubentityList): Complete rules → BusinessRule.
