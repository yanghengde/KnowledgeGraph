Chapter 19: Maintenance Modeling
Introduction
Maintenance ensures that Resources are kept in working condition, reducing unexpected downtime.

In This Chapter
• MaintenancePlan
• MaintenanceLog

MaintenancePlan
Defines preventive maintenance schedules for Resources based on time or usage.

Field Definitions:
- PlanName (String): Name of the maintenance plan.
- FrequencyType (String): TimeBased or UsageBased.
- Interval (Integer): How often it should occur.

MaintenanceLog
A record of a completed or ongoing maintenance activity on a Resource.

Field Definitions:
- LogId (String): Unique tracking number.
- MaintenanceDate (Date): When the maintenance was performed.
- Notes (String): Technician remarks.
