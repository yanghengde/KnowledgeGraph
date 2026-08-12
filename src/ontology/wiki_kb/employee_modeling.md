Chapter 13: Employee and Security Modeling
Introduction
The Employee module defines personnel who can log into Opcenter Execution (InSite), perform
transactions, and be credited with work. Employees are linked to Windows domain accounts, roles,
organizations, certifications, and UI preferences.

In This Chapter
• Employee (Personnel)
• EmployeeLoginInfo (Login Session)
• EmployeeRole (Role Assignment)
• Role (Role Definition)
• Certification (Skill Certification)

Employee
An Employee represents a person with login access to InSite. Employees must have a Windows NT/domain
account. Once defined, the employee appears in the Modeler Security window for permission assignment.

Field Definitions:
- Name (String, Required): Unique login name.
- FullName (String): Employee's full name for identification.
- Description (String): Description of this employee.
- EmailAddress (String): Email address for notifications.
- DomainName (String): Windows domain for authentication (optional).
- CanLogin (Boolean): Whether this employee is allowed to log into InSite.
- ModelerAccess (Boolean): Whether the employee can open the Modeler application.
- DocManagerUser (String): External document repository username (e.g., TeamCenter).
- DocManagerPassword (String, Encrypted): External document repository password.
- PrimaryOrganization (Navigation): Primary organizational unit.
- ESigRoleGroup (Navigation): E-Signature role group for authorization.
- LanguageDictionary (Navigation): UI language dictionary preference.
- MenuDefinition (Navigation): Menu layout definition.
- PortalMenuDefinition (Navigation): Portal menu layout.
- PortalMobileMenuDefinition (Navigation): Mobile portal menu layout.
- EscalationRecipients (Navigation): List of escalation notification recipients.
- AllowOverrideOfSessionValues (Boolean): Whether session values can be overridden.
- FilterTags (String): Filter tags for categorization.
- FilterTagAccess (Integer): Filter tag access control.
- Notes (String): Internal notes.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- IconId (Integer): UI icon identifier.
- AssociatedPackages (Integer): Count of associated packages.
- ChangeHistory (Navigation): Change history tracking.
- Roles (SubentityList): List of EmployeeRole entries for role-organization assignments.
- EmployeeLoginInfo (Navigation): Login session information.

EmployeeLoginInfo
Login session information for an employee, tracking the last login timestamp and time zone.

Field Definitions:
- LastLoginDateGMT (DateTime): Last successful login timestamp (GMT).
- TimeZone (String): Employee's time zone setting.
- IsFrozen (Boolean): Whether this login info is frozen.

EmployeeRole
An EmployeeRole is the role assignment entity linking an Employee to a Role within an Organization
context. This is distinct from the Role definition itself — EmployeeRole is the membership record.

Field Definitions:
- Employee (Navigation): The employee this assignment belongs to.
- Role (Navigation): The role being assigned.
- Organization (Navigation): Organizational context (Department/Factory) for this role.
- PropagateToChildOrgs (Boolean): Whether this role propagates to child organizations.
- IsFrozen (Boolean, ReadOnly): Whether frozen.

Role
A Role defines a job function and its associated system permissions (e.g., Operator, Supervisor,
Engineer). Roles can be linked to E-Signature rules and security policies.

Field Definitions:
- RoleName (String): Role name identifier.

Certification
A Certification represents a qualification or skill required to perform specific operations
or operate equipment (e.g., welding certification, forklift license). Certifications have
expiration management.

Field Definitions:
- CertName (String): Certification name.
- ExpirationDays (Integer): Validity period in days.
