Chapter: Change Management (MOC)
Introduction
Change Management handles Engineering Change Orders (ECOs) and deployment of new modeling versions. It ensures that changes to processes, bills of materials, or quality plans are formally reviewed, approved, and deployed in a traceable manner.

Classes:
- ChangePackage: A bundled set of modifications to the ontology/modeling data intended for deployment.
- ChangePackageStatus: The workflow state of the change package (e.g., Draft, Pending Approval, Approved, Closed).
- ApprovalRouting: The signature matrix required to authorize the deployment of a ChangePackage.
- CollaboratorTemplate: A configuration template pre-defining a workflow sequence of collaborative review, audit, or co-signature steps.
- CollaboratorEntry: An individual slot or role within a CollaboratorTemplate, mapping to an Employee or Role, carrying sequence priorities (Sheet Level) and durations.
