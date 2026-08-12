Chapter : Package Creation Template Modeling
Introduction
The PackageCreationTemplate entity predefines the configuration for creating change packages
in the Change Management module. It specifies the package type, approval template, collaborator
template, workflow, source/target systems, priority, and owner assignments, ensuring consistent
and traceable change management processes.

In This Chapter
- PackageCreationTemplate (Change Package Creation Template)

PackageCreationTemplate
A PackageCreationTemplate is a modeling entity used to standardize the creation of change
management packages. It bundles all the configuration needed to create a change package,
including type, approval workflow, collaboration rules, and system routing.

Relationship to other modules:

    PackageCreationTemplate --(HAS_PACKAGE_TYPE)--> PackageType
    PackageCreationTemplate --(HAS_APPROVAL_TEMPLATE)--> ApprovalSheetTemplate
    PackageCreationTemplate --(HAS_COLLABORATOR_TEMPLATE)--> CollaboratorTemplate
    PackageCreationTemplate --(HAS_WORKFLOW)--> Workflow
    PackageCreationTemplate --(HAS_PACKAGE_OWNER)--> Owner

Field Definitions:
- Name (String, Required): Unique template name.
- Description (String): Description of this template. Defaults to name if not specified.
- Notes (String): Internal notes and comments.
- FilterTags (String): Filter tags, comma separated list.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- ChangeHistory (Navigation): Change history tracking.
- IconId (Integer): Identifier for the associated icon.
- ApprovalTemplate (Navigation): Associated approval sheet template.
- CollaboratorTemplate (Navigation): Associated collaborator template for review/sign-off.
- EcoEcn (String): Engineering Change Order / Engineering Change Notice identifier.
- OwnerRole (Navigation): Role assigned as the package owner role.
- PackageCreationReason (Navigation): Package creation reason code.
- PackageDescription (String): Package description text.
- PackageOwner (Navigation): Owner responsible for this package.
- PackagePriorityCode (Navigation): Package priority code definition.
- PackageType (Navigation): Package type definition.
- SourceSystem (Navigation): Source system definition.
- TargetSystems (Array): List of target system definitions.
- UseContentCollaborators (Boolean): Whether to use content collaborators for approval.
- Workflow (Navigation): Change management workflow for approval routing.
- WorkflowAssignApprovers (Boolean): Whether the workflow allows assigning approvers.
