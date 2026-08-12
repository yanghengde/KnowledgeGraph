Chapter 9: Manufacturing Line Modeling
Introduction
A Manufacturing Line (MfgLine) represents a sequenced grouping of work centers that together 
form a complete production flow. MfgLines organize production capacity under a Factory and are 
assigned to manufacturing orders to direct where work is executed.

In This Chapter
• MfgLine (Manufacturing Line)

MfgLine
A Manufacturing Line (MfgLine / ProductionLine) is the primary production organization unit 
within the factory model. It connects multiple WorkCenters into a logical production flow and 
acts as the target for shop floor execution. An MfgOrder can be assigned to a specific MfgLine 
to determine which production line will handle the order.

Relationship chain:

    Factory ──(HAS_PRODUCTION_LINE)──▶ MfgLine ──(CONTAINS_WORKCENTER)──▶ WorkCenter
    MfgOrder ──(ASSIGNED_TO_LINE)──▶ MfgLine

Field Definitions:
- Name (String, Required): Unique identifier for the manufacturing line.
- Description (String): Description of the line's purpose and configuration.
- Notes (String): Internal notes and comments.
- IsFrozen (Boolean, ReadOnly): Whether the line is frozen from editing.
- InstanceLocked (Boolean): Whether this instance is locked by Change Management.
- FilterTags (String): Comma-separated filter tags for categorization.
- ChangeHistory (Navigation): Change history tracking for this line.
- IconId (Integer): Icon identifier for UI display.
- AssociatedPackages (Integer): Count of associated packages.
