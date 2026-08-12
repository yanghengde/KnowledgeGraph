Chapter 9: Factory Information Model
Introduction
The Factory Information Model is the foundational framework in Opcenter Execution (Camstar) that defines 
the digital representation of your physical manufacturing environment. It establishes the organizational 
hierarchy from enterprise level down to individual resources, enabling WIP tracking, production control, 
and full traceability across global operations.

The Factory Information Model is divided into two complementary parts:
•
Physical Model – Defines WHERE production occurs (the hierarchy of locations and assets).
•
Process Model – Defines HOW production occurs (workflows, specs, and operations).

This chapter focuses on the Physical Model, which establishes the hierarchical structure that controls 
container movement, resource allocation, and production visibility.

In This Chapter
This chapter contains these topics:
•
Understanding the Factory Hierarchy
•
Defining Enterprises and Sites
•
Defining Factories and Departments
•
Defining Manufacturing Areas and Production Lines
•
Managing Shift Calendars
•
Configuring Object Groups
•
Working with WIP Messages

Understanding the Factory Hierarchy
The factory hierarchy in Opcenter follows a multi-level structure that mirrors the physical and 
organizational layout of your manufacturing operations. Each level can inherit configurations from its 
parent while allowing overrides at the child level.

Standard Factory Hierarchy
The standard hierarchy follows this structure:
•
Enterprise – The top-level organizational entity representing the entire company or division.
•
Site – A geographic location or campus. A single enterprise can have multiple sites.
•
Factory – A manufacturing facility or building within a site. Each site can contain multiple factories.
•
Department – A logical functional area within a factory (e.g., Assembly, Testing, Packaging).
•
Manufacturing Area – A physical zone or area within a department (e.g., Clean Room, ESD Zone).
•
Production Line – A specific production line or cell within an area.
•
Work Center – The location where operations are performed (defined in WorkCenter Modeling).
•
Resource – The machines, tools, and operators (defined in WorkCenter Modeling).

Enterprise
An Enterprise represents the highest level in the factory hierarchy. It defines the organizational 
boundary for your Opcenter Execution instance. All factories, users, and production data exist within 
the context of an enterprise.

Enterprise Page Field Definitions
This table defines the fields on the Enterprise page.
Field                        Definition                                                              Type
Name                         Unique name for this enterprise.                                       Required
Description                  Description of the enterprise. Maximum 255 characters.                 Optional
DefaultSite                  The default site for this enterprise.                                  Optional
DefaultCurrency              The default currency used for cost calculations.                       Optional
TimeZone                     The default time zone for enterprise-level reporting.                  Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Site
A Site represents a geographic location within the enterprise. Sites are used to organize factories 
by physical location and to manage region-specific configurations such as time zones, currencies, 
and regulatory requirements.

Site Page Field Definitions
This table defines the fields on the Site page.
Field                        Definition                                                              Type
Name                         Unique name for this site.                                             Required
Description                  Description of the site. Maximum 255 characters.                       Optional
Enterprise                   The enterprise to which this site belongs.                             Required
Location                     Geographic location or address of the site.                            Optional
Country                      Country where the site is located.                                     Optional
TimeZone                     Local time zone for this site.                                         Optional
DefaultFactory               The default factory for this site.                                     Optional
DefaultCurrency              The currency used at this site.                                        Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Factory
A Factory represents a specific manufacturing facility within a site. Each factory is an independent 
production unit with its own set of departments, work centers, and production configurations.

The Factory definition is central to the physical model because it establishes the scope for:
•
WIP tracking and dispatch lists
•
Resource availability and capacity
•
Shift calendar assignments
•
Production reporting boundaries

Factory Page Field Definitions
This table defines the fields on the Factory page.
Field                        Definition                                                              Type
Name                         Unique name for this factory.                                          Required
Description                  Description of the factory. Maximum 255 characters.                    Optional
Site                         The site to which this factory belongs.                                Required
Calendar                     The shift calendar applied to this factory.                            Optional
TimeZone                     The local time zone for this factory.                                  Optional
Status                       Current status: Active, Inactive, or UnderConstruction.                Required
Address                      Physical address of the factory.                                       Optional
PlantCode                    ERP plant code for integration with enterprise systems.                Optional
DefaultDepartment            The default department for this factory.                               Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Manufacturing Area
A Manufacturing Area defines a physical zone or subdivision within a factory or department. Areas 
are used to model environmental or functional distinctions on the shop floor.

Examples of manufacturing areas include:
•
Clean Room – Controlled environment for sensitive manufacturing
•
ESD Protected Zone – Electrostatic discharge protected area
•
Hazardous Materials Area – Area for handling hazardous substances
•
Cold Storage – Temperature-controlled storage area

Manufacturing Area Page Field Definitions
This table defines the fields on the Manufacturing Area page.
Field                        Definition                                                              Type
Name                         Unique name for this area.                                             Required
Description                  Description of the area. Maximum 255 characters.                       Optional
AreaType                     Type of area: CleanRoom, ESD, Hazardous, ColdStorage, or General.      Optional
Factory                      The factory to which this area belongs.                                Required
Department                   The department to which this area belongs (optional if factory set).    Optional
EnvironmentClass             Environmental classification (e.g., ISO 14644 class).                  Optional
TemperatureRange             Required temperature range (e.g., "20-25°C").                          Optional
HumidityRange                Required humidity range (e.g., "40-60%").                              Optional
AccessRestriction            Whether special access credentials are required.                       Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Production Line
A Production Line represents a specific manufacturing line or cell within a factory. Production lines 
are logical groupings of work centers that process containers in a sequential flow. They are used for 
capacity planning, throughput tracking, and line-level performance analysis.

Production Line Page Field Definitions
This table defines the fields on the Production Line page.
Field                        Definition                                                              Type
Name                         Unique name for this production line.                                  Required
Description                  Description of the line. Maximum 255 characters.                       Optional
Factory                      The factory to which this line belongs.                                Required
LineType                     Type of line: Assembly, SMT, Test, Packaging, or Custom.               Optional
Status                       Current status: Active, Inactive, or Maintenance.                      Required
Capacity                     Maximum throughput capacity (units per hour).                           Optional
PlannedOutput                Planned daily output quantity.                                          Optional
DefaultWorkflow              The default workflow used on this production line.                      Optional
Area                         The manufacturing area where this line is located.                     Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Shift Calendars
Shift calendars define the operational schedule for factories, departments, and work centers. They 
are essential for accurate capacity planning, throughput calculations, OEE metrics, and labor tracking.

A shift calendar consists of one or more shift patterns that define the working hours for different 
days of the week.

Calendar Page Field Definitions
This table defines the fields on the Calendar page.
Field                        Definition                                                              Type
Name                         Unique name for this calendar.                                         Required
Description                  Description of the calendar. Maximum 255 characters.                   Optional
CalendarType                 Type: Production, Maintenance, or Custom.                              Optional
EffectiveFromDate            Date from which this calendar is effective.                             Optional
EffectiveToDate              Date until which this calendar is effective.                            Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Shift Pattern
A Shift Pattern defines the working hours for a specific shift within a calendar. Multiple shift 
patterns can be associated with a single calendar to define multi-shift operations.

Shift Pattern Page Field Definitions
This table defines the fields on the Shift Pattern page.
Field                        Definition                                                              Type
Name                         Unique name for this shift pattern (e.g., "Day Shift").                Required
Description                  Description. Maximum 255 characters.                                   Optional
Calendar                     The calendar to which this shift pattern belongs.                      Required
StartTime                    Shift start time (e.g., "07:00").                                      Required
EndTime                      Shift end time (e.g., "15:00").                                        Required
DaysOfWeek                   Days of the week this shift applies (e.g., Mon-Fri).                   Required
BreakDuration                Total break time in minutes.                                           Optional
PlannedEfficiency            Planned efficiency percentage for this shift.                          Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Object Groups
Object Groups provide a way to categorize modeling objects for easier management, access control, 
and reporting. You can group factories, work centers, resources, or any other modeling objects 
into logical collections.

Object Groups are commonly used for:
•
User access control – Restrict visibility of certain factories or lines to specific users.
•
Reporting – Generate reports filtered by specific object groups.
•
Scheduling – Apply scheduling rules to groups of work centers or resources.
•
Configuration deployment – Deploy configuration changes to specific groups.

WIP Messages
WIP Messages are configurable notifications that display to operators during production transactions. 
They can be associated with any level of the factory hierarchy:
•
Enterprise-level messages – Display across all factories.
•
Factory-level messages – Display only within a specific factory.
•
Work Center-level messages – Display only at a specific work center.
•
Step-level messages – Display at specific workflow steps (using WIP Message Labels).

WIP Message Page Field Definitions
This table defines the fields on the WIP Message page.
Field                        Definition                                                              Type
Name                         Unique name for this message.                                          Required
MessageText                  The message content displayed to operators. Maximum 2000 characters.    Required
MessageType                  Type: Information, Warning, or Critical.                               Optional
DisplayScope                 Scope: Enterprise, Factory, WorkCenter, or Step.                       Optional
EffectiveFromDate            Date from which this message is active.                                Optional
EffectiveToDate              Date until which this message is active.                               Optional
WipMsgLabel                  Label for associating this message with workflow steps.                 Optional
Notes                        Any relevant comments. Maximum 2000 characters.                         Optional

Working with the Factory Model
When Defining a Complete Factory Model
Follow these steps to establish a factory information model:
1. Create an Enterprise definition as the top-level organizational entity.
2. Create Site definitions for each geographic location within the enterprise.
3. Create Factory definitions within each site for individual manufacturing facilities.
4. Create Department definitions to organize functional areas within each factory.
5. Create Manufacturing Area definitions for zones with special requirements.
6. Create Production Line definitions for each line or cell within a factory.
7. Configure Shift Calendars and assign them to factories and work centers.
8. Set up WIP Messages for operator communications at the appropriate hierarchy levels.
9. Configure Object Groups for access control and reporting.

The factory model must be established before defining the process model (workflows, specs) and 
before creating production execution transactions.
