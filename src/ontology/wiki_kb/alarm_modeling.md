Chapter: Equipment Alarms & Events
Introduction
The Alarm module captures automated signals from shop floor equipment via IoT or direct integration. It maps physical machine error codes to MES actions.

Classes:
- AlarmDef: Defines the logic for an incoming machine signal (e.g., Error 404: Spindle Jam).
- AlarmLog: The historical event trace of when an alarm was triggered and cleared.
- AlarmAction: The automatic MES transaction triggered (e.g., Hold the lot, Email Maintenance).

AlarmAction Field Definitions:
- ActionName (String): Name of the action definition.
- ActionType (String): Type of MES action to execute (Hold/Scrap/Email/Notify).
- Description (String): Description of what the action does.
- Notes (String): Detailed notes or instructions.
- LabelName (String): UI label identifier for display.
- LabelText (String): UI label display text.
- Sequence (Integer): Execution order when multiple actions are triggered.
- IsFrozen (Boolean): Whether the action definition is frozen (read-only).
- CDOTypeId (Integer): Common Domain Object type ID.
- ChangeCount (Integer): Change counter for version control.
