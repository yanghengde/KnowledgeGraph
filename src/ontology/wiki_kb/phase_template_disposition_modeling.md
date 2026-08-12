Chapter : Phase Template Disposition Modeling
Introduction
The PhaseTemplateDisposition entity is a specialized subtype of PhaseTemplate used
specifically for disposition actions in quality processing (Events, CAPA). It defines the
same assignee policies, approval workflows, business rules, and organizational
applicability as PhaseTemplate but is specifically designed for disposition phase
configuration in quality management workflows.

In This Chapter
- PhaseTemplateDisposition (Disposition Phase Template)

PhaseTemplateDisposition
A PhaseTemplateDisposition is a disposition-specific phase template (CdoId: 8017).
It configures how disposition actions are processed in quality events and CAPAs,
defining who executes the disposition, what approvals are needed, and which
business rules validate the disposition outcome.

Relationship to other modules:

    PhaseTemplateDisposition --(HAS_CHECKLIST)--> ChecklistTemplate
    PhaseTemplateDisposition --(APPLIES_TO_ORG)--> Organization
    PhaseTemplateDisposition --(HAS_ON_START_RULE)--> BusinessRule
    PhaseTemplateDisposition --(HAS_ON_COMPLETE_RULE)--> BusinessRule

Field Definitions (same as PhaseTemplate):
- Name (String, Required): Unique disposition phase template name.
- Description (String): Description of this template. Defaults to name if not specified.
- Notes (String): Internal notes.
- FilterTags (String): Filter tags, comma separated.
- IsFrozen (Boolean, ReadOnly): Whether frozen.
- InstanceLocked (Boolean): Whether locked by Change Management.
- ChangeHistory (Navigation): Change history tracking.
- IconId (Integer): Associated icon ID.
- Status (Integer): Status: 1=Active, 2=Inactive.
- IsRequired (Boolean): Whether this disposition phase cannot be removed.
- AutoStart (Boolean): Whether to auto-start once routed/approved.
- AutoComplete (Boolean): Whether to auto-transition from Completed to Closed.
- DefaultAssigneeInfo (Boolean): Whether to inherit assignee info from parent.
- Assignee (Navigation): Default assignee employee → Employee.
- AssigneeOption (Integer): Assignee option: 1=Assignee, 2=Owner, 3=Collaborator.
- AssigneeRole (Navigation): Assignee role → Role.
- AllowReassignment (Integer): Reassignment policy: 1=Within roles, 2=Any user, 3=Not allowed.
- ApprovalRequired (Boolean): Whether approval is required before processing.
- CompleteWithinQty (Integer): Completion time limit quantity.
- CompleteWithinUOM (Float): Completion time limit unit: 1=Hour, 24=Day, 168=Week.
- DocumentSet (Navigation): Associated document set → DocumentSet.
- RuleList (String): Name of field containing business rules.
- Organizations (Array): List of organizations this template applies to → Organization.
- ApprovalSheets (SubentityList): Approval sheets → ApprovalSheet.
- Checklist (Navigation): Associated checklist → ChecklistTemplate.
- Details (SubentityList): Process objects → ProcessObject.
- OnStartRules (SubentityList): Business rules on start → BusinessRule.
- OnCompleteRules (SubentityList): Business rules on complete → BusinessRule.
