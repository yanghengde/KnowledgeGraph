Chapter : Phase Template Modeling
Introduction
The PhaseTemplate entity defines the configuration template for a workflow phase or step
in Opcenter Execution. Phase templates specify assignee policies, approval workflows,
business rules to execute on start/complete, checklists, document sets, time limits, and
organizational applicability. PhaseTemplateDisposition is a specialized subtype used for
disposition actions in quality processing.

In This Chapter
- PhaseTemplate (Process Phase Template)

PhaseTemplate
A PhaseTemplate is a reusable template that defines the complete configuration for a
workflow phase. It controls how a process step behaves, who is responsible, what approvals
are needed, and which business rules fire on entry and exit.

Relationship to other modules:

    PhaseTemplate --(HAS_CHECKLIST)--> ChecklistTemplate
    PhaseTemplate --(APPLIES_TO_ORG)--> Organization
    PhaseTemplate --(HAS_ON_START_RULE)--> BusinessRule
    PhaseTemplate --(HAS_ON_COMPLETE_RULE)--> BusinessRule

Field Definitions:
- Name (String, Required): Unique phase template name.
- Description (String): Description of this template. Defaults to name if not specified.
- Notes (String): Internal notes.
- FilterTags (String): Filter tags, comma separated.
- IsFrozen (Boolean, ReadOnly): Whether frozen.
- InstanceLocked (Boolean): Whether locked by Change Management.
- ChangeHistory (Navigation): Change history tracking.
- IconId (Integer): Associated icon ID.
- Status (Integer): Status: 1=Active, 2=Inactive.
- IsRequired (Boolean): Whether this phase cannot be removed from the process.
- AutoStart (Boolean): Whether to auto-start once routed/approved.
- AutoComplete (Boolean): Whether to auto-transition from Completed to Closed.
- DefaultAssigneeInfo (Boolean): Whether to inherit assignee info from parent.
- Assignee (Navigation): Default assignee employee → Employee.
- AssigneeOption (Integer): Assignee option: 1=Assignee, 2=Owner, 3=Collaborator.
- AssigneeRole (Navigation): Assignee role → Role.
- AllowReassignment (Integer): Reassignment policy: 1=Within specified roles, 2=Any user, 3=Not allowed.
- ApprovalRequired (Boolean): Whether approval is required before processing.
- CompleteWithinQty (Integer): Completion time limit quantity.
- CompleteWithinUOM (Float): Completion time limit unit: 1=Hour, 24=Day, 168=Week.
- DocumentSet (Navigation): Associated document set → DocumentSet.
- RuleList (String): Name of field containing business rules.
- ExecutionContextType (Integer): Execution context type for business rules.
- Organizations (Array): List of organizations this template applies to → Organization.
- ApprovalSheets (SubentityList): Approval sheets for collecting signatures → ApprovalSheet.
- Checklist (Navigation): Associated checklist → ChecklistTemplate.
- Details (SubentityList): Process objects/sub-phases → ProcessObject.
- OnStartRules (SubentityList): Business rules executed when phase starts → BusinessRule.
- OnCompleteRules (SubentityList): Business rules executed when phase completes → BusinessRule.
