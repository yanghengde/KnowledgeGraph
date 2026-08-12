Chapter 8: Work Centers and Factory Model
Introduction
Work Centers are fundamental components of the Opcenter Execution (Camstar) factory information model. 
A work center represents a physical or logical area on the shop floor where manufacturing operations take 
place. The factory model uses a hierarchical structure to organize production from enterprise level down to 
specific equipment, enabling WIP (Work In Process) tracking, resource management, and dispatch control.

In This Chapter
This chapter contains these topics:
•
Understanding the Factory Model
•
Defining Work Centers
•
Managing Resources and Resource Groups
•
Dispatch Lists and Scheduling

Understanding the Factory Model
The Factory Information Model provides a digital representation of your manufacturing environment. 
It defines the organizational hierarchy that controls where and how production activities occur.

Factory Hierarchy
The standard factory hierarchy in Opcenter follows this structure:
•
Enterprise – The top-level organizational entity.
•
Site – A geographic location or campus.
•
Factory – A specific manufacturing facility or building within a site.
•
Department – A logical grouping or area within a factory (e.g., Assembly, Testing, Packaging).
•
Work Center – The specific location where work is performed. Can be physical or logical.
•
Resource – The actual assets (machines, tools, stations) that perform work within a work center.

Each level in the hierarchy inherits certain configurations and constraints from its parent, while 
allowing overrides at the child level for maximum flexibility.

Factory
A Factory represents a manufacturing facility. Each factory belongs to a site and contains one or more 
departments and work centers. The factory definition includes:
•
Factory Name – Unique identifier for the factory.
•
Description – Human-readable name for the facility.
•
Site – The site to which this factory belongs.
•
Calendar – The shift calendar applied to this factory.
•
Time Zone – The local time zone for the factory.

Department
A Department is a logical grouping within a factory. Departments help organize work centers by functional 
area. For example, a factory might have departments for Assembly, Test, and Packaging. The department 
definition includes:
•
Department Name – Unique identifier for the department.
•
Description – Human-readable description.
•
Factory – The parent factory.

Defining Work Centers
A Work Center defines a specific area on the shop floor where manufacturing operations are performed. 
Work Centers are the primary unit for organizing production activities and tracking WIP. Each work center 
can be associated with one or more resources.

Work Center Page
The Work Center modeling page allows you to create and configure work centers for your factory model.

Work Center Page Field Definitions
This table defines the fields on the Work Center page.
Field                        Definition                                                              Type
Name                         Unique name for this work center.                                       Required
Description                  Short description of the work center. Maximum 255 characters.          Optional
Factory                      The factory to which this work center belongs.                          Required
Department                   The department to which this work center belongs.                       Optional
WorkCenterType              Type of work center: Production, Inspection, Storage, or Shipping.       Optional
Status                       Current status: Active, Inactive, or Maintenance.                      Required
Calendar                     The shift calendar for this work center.                               Optional
DispatchRule                 The dispatch rule used to prioritize WIP at this work center.           Optional
Capacity                     Maximum number of containers that can be processed simultaneously.      Optional
PlannedEfficiency            The planned efficiency factor (percentage) for this work center.        Optional
DefaultResource              The default resource used when no specific resource is selected.        Optional
CostCenter                   The cost center associated with this work center for accounting.        Optional
Location                     Physical location identifier (floor, cell, or area code).              Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Work Center Types
Work centers can be classified into the following types:
•
Production – Standard manufacturing work center where product processing occurs.
•
Inspection – Work center dedicated to quality inspection and testing activities.
•
Storage – Work center for material storage and inventory management.
•
Shipping – Work center for outbound logistics and shipping activities.

Work Center Status
The status field controls the operational availability of the work center:
•
Active – The work center is available for production. Containers can be moved to operations at 
  this work center.
•
Inactive – The work center is not available. Attempting to process containers at this work center 
  will be blocked by the system.
•
Maintenance – The work center is temporarily unavailable due to scheduled or unscheduled 
  maintenance. The system can be configured to allow or block operations during maintenance.

Managing Resources
A Resource represents a physical asset (machine, tool, workstation) or human operator that performs 
manufacturing activities within a work center. Resources are the lowest level of the factory hierarchy 
and provide detailed tracking of equipment utilization and operator activities.

Resource Page Field Definitions
This table defines the fields on the Resource page.
Field                        Definition                                                              Type
Name                         Unique name for this resource.                                         Required
Description                  Short description of the resource. Maximum 255 characters.             Optional
ResourceType                 Type of resource: Equipment, Tool, Personnel, or Other.                Required
WorkCenter                   The work center to which this resource is assigned.                    Required
Status                       Current status: Available, InUse, Down, or Maintenance.                Required
Capacity                     Maximum throughput capacity of this resource.                           Optional
MaintenanceStatus            Current maintenance state: OK, PastDue, or Scheduled.                  Optional
NextMaintenanceDate          Date of next scheduled preventive maintenance.                         Optional
CalibrationStatus            Calibration status: Current, Expired, or NotRequired.                  Optional
CalibrationDueDate           Date when calibration expires.                                         Optional
SkillRequirement             Skill or certification required to operate this resource.              Optional
SetupTime                    Standard setup time (in minutes) for this resource.                    Optional
HourlyRate                   Cost per hour for this resource (used in cost accounting).             Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Resource Types
Resources can be classified into the following types:
•
Equipment – Physical machines (CNC, laser marker, SMT line, etc.)
•
Tool – Specialized tools or fixtures required for specific operations.
•
Personnel – Human operators with specific skills and certifications.
•
Other – Any other type of resource not covered by the above categories.

Resource Status
The status field tracks the current operational state of the resource:
•
Available – The resource is ready for use. Production can be started.
•
InUse – The resource is currently being used for an active production operation.
•
Down – The resource is not operational due to a breakdown or failure.
•
Maintenance – The resource is undergoing preventive or corrective maintenance.

Resource Groups
A Resource Group defines a collection of interchangeable resources that share similar capabilities. 
Resource groups are used in Spec definitions to specify which resources are valid for a particular 
operation, without requiring a specific individual resource.

When a Spec references a Resource Group, the system validates at runtime that the selected resource 
belongs to the specified group. If the resource is not a member of the group, the transaction is blocked.

Resource Group Page Field Definitions
This table defines the fields on the Resource Group page.
Field                        Definition                                                              Type
Name                         Unique name for this resource group.                                   Required
Description                  Short description of the resource group. Maximum 255 characters.       Optional
GroupType                    Type of resource group: Equipment, Personnel, or Mixed.                 Optional
IsExclusive                  Whether a resource can belong to only this group.                      Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Dispatch Lists and Scheduling
The Dispatch List provides a real-time, prioritized view of WIP waiting to be processed at a 
specific work center. It is the primary tool for shop-floor operators to manage their work queue.

Dispatch Rule
A Dispatch Rule defines the logic used to prioritize containers in the dispatch list for a work center.
Common dispatch strategies include:
•
FIFO (First In, First Out) – Containers are processed in the order they arrived.
•
Priority – Containers are ordered by their priority level (urgent orders first).
•
DueDate – Containers are ordered by their due date (earliest deadline first).
•
Custom – User-defined rules based on container attributes or business logic.

Dispatch Rule Page Field Definitions
This table defines the fields on the Dispatch Rule page.
Field                        Definition                                                              Type
Name                         Unique name for this dispatch rule.                                    Required
Description                  Short description. Maximum 255 characters.                             Optional
Strategy                     Dispatch strategy: FIFO, Priority, DueDate, or Custom.                 Required
CustomExpression             Expression for custom dispatch logic (only when Strategy = Custom).     Optional
SortDirection                Sort direction: Ascending or Descending.                               Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Skill and Certification Management
Opcenter enforces strict control over who can operate specific resources and perform specific tasks.
The Skill definition allows you to model required certifications and training requirements.

Skill Page Field Definitions
This table defines the fields on the Skill page.
Field                        Definition                                                              Type
Name                         Unique name for this skill or certification.                           Required
Description                  Short description. Maximum 255 characters.                             Optional
CertificationType            Type: License, Training, Certification, or Qualification.              Optional
ExpirationPeriod             Period after which the skill/certification expires.                    Optional
ExpirationUnit               Unit of expiration: Days, Months, or Years.                            Optional
RenewalRequired              Whether renewal is required upon expiration.                           Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

When a resource or operation has a skill requirement, the system automatically checks whether the 
current operator has the required skill and whether it is still valid (not expired) before allowing 
the transaction to proceed.

Maintenance Management
Preventive maintenance is tracked at the resource level. The system can be configured to:
•
Warn – Display a warning when a resource is approaching its maintenance due date.
•
Block – Prevent the resource from being used after the maintenance due date has passed.
•
Notify – Send notifications to maintenance personnel when maintenance is due.

The maintenance status is automatically updated based on the NextMaintenanceDate and the current date.

Working with the Factory Model
When Defining the Factory Hierarchy
Follow these steps to define a complete factory model:
1. Create a Factory definition with the appropriate site, calendar, and time zone.
2. Create Department definitions within the factory to organize functional areas.
3. Create Work Center definitions within each department.
4. Create Resource definitions and assign them to work centers.
5. Create Resource Groups to aggregate interchangeable resources.
6. Assign Dispatch Rules to work centers to control WIP prioritization.
7. Define Skills and assign them to resources that require operator certification.

When Assigning Resources to Operations
The relationship between resources and operations is established through the Spec. When defining a Spec:
1. Assign the appropriate Resource Group to the Spec.
2. The system will validate at runtime that the resource selected by the operator belongs to the 
   specified resource group.
3. If the resource is not in the group, the system blocks the transaction and displays an error.

Container Movement and Work Centers
When a container is moved through a workflow, the system tracks which work center and resource were 
used at each step. This provides:
•
Full traceability of which equipment processed each product.
•
Operator identification for compliance and audit purposes.
•
Equipment utilization metrics for OEE (Overall Equipment Effectiveness) calculations.
•
Cycle time analysis by work center for performance optimization.
