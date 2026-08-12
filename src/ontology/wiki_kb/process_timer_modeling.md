Chapter : Process Timer Modeling
Introduction
The ProcessTimer entity defines time thresholds and color alerts for workflow process stages.
It supports revision control and configures min/max/warning time limits with associated display
colors for visual alerts when thresholds are approached or exceeded.

In This Chapter
- ProcessTimer (Process Timer)

ProcessTimer
A revisioned entity (CdoId: 8641/3620) that defines time limits for process stages.

Field Definitions:
- Name (String, Required): Timer name.
- Revision (String, Required): Version number.
- MaxTime (Float): Maximum allowed time threshold.
- MaxTimeColor (String): Display color when max time exceeded.
- MaxWarningTime (Float): Warning time threshold.
- MaxWarningTimeColor (String): Display color at warning threshold.
- MinTime (Float): Minimum allowed time threshold.
- MinTimeColor (String): Display color below min threshold.
- EndProcessTimerMapDtl (SubentityList): Timer mapping details.
- Plus standard fields: Description, Notes, Eco, Status, IsFrozen, IsRevOfRcd, etc.
