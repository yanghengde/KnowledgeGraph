Chapter 8: Manufacturing Calendar Modeling
Introduction
The Manufacturing Calendar (MfgCalendar) provides the time management backbone for shop floor
execution. It defines shift schedules, manufacturing date conventions, and fiscal accounting
periods used for production planning, OEE calculation, and capacity management.

In This Chapter
• MfgCalendar (Manufacturing Calendar)
• CalendarShift (Calendar Shift Entry)

MfgCalendar
A Manufacturing Calendar (MfgCalendar) is an MES-level time model that extends the generic 
Calendar concept with manufacturing-specific attributes: shifts with start/end times, 
manufacturing date logic (where a shift may span two calendar days), and fiscal period 
grouping (year/quarter/month/week). Factories and WorkCenters reference MfgCalendar to 
determine available production time.

Relationship chain:

    Factory ──(USES_CALENDAR)──▶ MfgCalendar ──(HAS_SHIFT)──▶ CalendarShift ──(REFERENCES_SHIFT_PATTERN)──▶ ShiftPattern
    WorkCenter ──(USES_CALENDAR)──▶ MfgCalendar

Field Definitions:
- Name (String, Required): Unique name for this manufacturing calendar.
- Description (String): Description of the calendar's purpose.
- Notes (String): Internal notes.
- IsFrozen (Boolean, ReadOnly): Whether the calendar is frozen from editing.
- InstanceLocked (Boolean): Whether this instance is locked by Change Management.
- FilterTags (String): Comma-separated filter tags.
- ChangeHistory (Navigation): Change history tracking.
- IconId (Integer): Icon identifier for UI display.
- AssociatedPackages (Integer): Count of associated packages.
- MaxShiftDuration (Float, ReadOnly): Maximum duration of any shift in the calendar.
- MfgCalendarShifts (SubentityList): List of CalendarShift entries.

CalendarShift
A CalendarShift defines a specific time window within the manufacturing calendar, linking
a ShiftPattern to a start/end time and assigning fiscal period attributes.

Field Definitions:
- CalendarDate (DateTime): The manufacturing date for this shift (may differ from clock date).
- ShiftStart (DateTime): Start time of the shift.
- ShiftEnd (DateTime): End time of the shift.
- Shift (Navigation): Reference to the ShiftPattern (e.g., Day, Night, Swing).
- FiscalYear (Integer): Fiscal year.
- FiscalQuarter (Integer): Fiscal quarter.
- FiscalMonth (Integer): Fiscal month.
- FiscalWeek (Integer): Fiscal week.
- IsNonScheduledTime (Float): Non-scheduled time (e.g., shutdown affecting multiple resources).
- IsFrozen (Boolean): Whether this shift entry is frozen.
