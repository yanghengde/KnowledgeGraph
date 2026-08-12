Chapter 13b: Role and Permission Modeling
Introduction
Roles define system-level access control through permission assignments. Each Role contains
a set of Permissions that grant specific operation modes (Create/Read/Update/Delete) on
system objects. EmployeeRole links employees to roles within organizational contexts.

In This Chapter
• Role (System Role)
• RolePermission (Permission Assignment)

Role
A Role is a named collection of permissions. Roles are assigned to employees via EmployeeRole
within an organization context. Role types include Shopfloor (operator) and Admin roles.

Field Definitions:
- Name (String, Required): Unique role name.
- Description (String): Description of this role.
- RoleType (Integer): 1=Shopfloor, 2=Admin.
- PermissionType (Integer): RBAC permission type.
- Notes (String): Internal notes.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- FilterTags (String): Filter tags.
- IconId (Integer): UI icon identifier.
- AssociatedPackages (Integer): Count of associated packages.
- ChangeHistory (Navigation): Change history tracking.
- Members (SubentityList): EmployeeRole members assigned to this role.
- Permissions (SubentityList): RolePermission entries.

RolePermission
A RolePermission defines a specific access right on a system object type. Each permission
specifies which object metadata type it applies to and which operation modes are allowed.

Field Definitions:
- Name (String): Permission entry name.
- PermissionType (Integer): RBAC permission type.
- ObjectMetaId (Integer): CDO Definition ID of the target object type.
- ObjectInstanceId (String): Optional instance-level constraint.
- Modes (Navigation): Operation modes (Create/Read/Update/Delete).
