Chapter 20b: Terminal (Shop Floor Terminal) Modeling
Introduction
The Terminal entity models the physical shop floor workstations used by operators to interact
with the MES. Each terminal is identified by IP address and can be configured with specific
operations, resources, specs, and UI preferences.

In This Chapter
• Terminal (Shop Floor Workstation)

Terminal
A Terminal represents a physical device on the shop floor where operators perform MES
transactions. Terminals are associated with WorkCenters, Operations, Resources, and Specs
to provide contextual defaults when operators log in. UI configuration (Portal menus,
profiles) can be customized per terminal.

Relationship chain:

    Terminal ──(LOCATED_AT_WORKCENTER)──▶ WorkCenter
             ──(ASSIGNED_OPERATION)──▶ Operation
             ──(ASSIGNED_RESOURCE)──▶ Resource
             ──(ASSIGNED_SPEC)──▶ Spec

Field Definitions:
- Name (String, Required): Unique terminal name.
- IpAddress (String, Required): IP address of the terminal device.
- Description (String): Description of the terminal.
- WorkCenter (Navigation): Associated work center where this terminal is located.
- Operation (Navigation): Default operation assigned to this terminal.
- Resource (Navigation): Associated equipment/resource.
- Spec (Navigation): Default spec/instruction loaded on this terminal.
- Workstation (Navigation): Physical workstation reference.
- PortalMenuDefinition (Navigation): Portal menu layout.
- PortalMobileMenuDefinition (Navigation): Mobile portal menu layout.
- PortalV8MenuDefinition (Navigation): Portal V8 menu layout.
- UiPortalProfile (Navigation): Portal UI profile configuration.
- ES_UseContainerList (Integer): Whether to use container grid list view.
- Notes (String): Internal notes.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- FilterTags (String): Filter tags.
- IconId (Integer): UI icon identifier.
- AssociatedPackages (Integer): Count of associated packages.
- ChangeHistory (Navigation): Change history tracking.
