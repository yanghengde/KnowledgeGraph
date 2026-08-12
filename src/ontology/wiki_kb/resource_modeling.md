Chapter 15: Resource and Equipment Modeling
Introduction
Resources represent the physical equipment, tools, and machines used to manufacture products.

In This Chapter
• Resources
• Resource Groups
• Resource Status

Resource
A Resource is an individual piece of equipment or tool.

Field Definitions:
- ResourceName (String): Name of the resource.
- Description (String): Description of the equipment.

Key Relationships:
- BELONGS_TO_FAMILY: Points to its Resource Family.
- HAS_PARENT_RESOURCE: Points to a parent Resource (for hierarchical equipment).
- LOCATED_IN_FACTORY: Points to the Factory.
- LOCATED_AT: Points to its Location or Inventory.
- HAS_MAINTENANCE_CLASS: Points to a Maintenance Class.
- SUPPLIED_BY: Points to a Vendor.
- ASSIGNED_TO: Points to Employees.
- HAS_STATUS: Points to its Resource Status.

ResourceGroup
Resources can be grouped into Resource Groups for scheduling and reporting purposes.

Field Definitions:
- GroupName (String): Name of the group.

ResourceFamily
Resource Families define a classification of resources that share similar capabilities, properties, or setup patterns.

Field Definitions:
- FamilyName (String): Name of the family.

ResourceStatus
Tracks the current operational status of a resource (e.g., Up, Down, In Maintenance).

Field Definitions:
- StatusName (String): Name of the status.
- IsAvailable (Boolean): Whether the resource can be used for production.
