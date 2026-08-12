Chapter: Timer Management
Introduction
Timers enforce time-sensitive business rules in manufacturing. For example, solder paste must be used within 4 hours of being taken out of the fridge (Out-of-Freezer time), or a glued part must cure for at least 24 hours.

Classes:
- TimerDef: Defines the logic, max/min limits, and starting conditions of a timer.
- ActiveTimer: A running timer instantiated against a specific container or material.
- TimerAction: The automated action (like placing on hold) executed if a timer limit is breached.

TimerAction Field Definitions:
- ActionName (String): Name of the timer action definition.
- ActionType (String): Type of action to execute when timer breaches (Hold/Scrap/Warning).
- Description (String): Description of the action behavior.
- Notes (String): Detailed notes or instructions for operators.
- LabelName (String): UI label identifier for display.
- LabelText (String): UI label display text.
- Sequence (Integer): Execution order when multiple actions are configured.
- IsFrozen (Boolean): Whether the action definition is frozen (read-only).
- CDOTypeId (Integer): Common Domain Object type ID.
- ChangeCount (Integer): Change counter for version control.

TimerAction Relationship Definitions:
- TRIGGERS_ACTION (from TimerDef, ONE_TO_MANY): 時效規則觸發的超時/違規動作。
- TRIGGERS_HOLD (to HoldReason, MANY_TO_ONE): 超時/違规動作觸發容器凍結時關聯的具體凍結原因。
- ROUTES_TO_WORKFLOW (to Workflow, MANY_TO_ONE): 時效違规自動路由重工時，跳轉的目標工作流。
- ROUTES_TO_STEP (to WorkflowStep, MANY_TO_ONE): 時效違规自動跳轉的具體工作流步驟。
- TRIGGERS_RULE (to BusinessRule, MANY_TO_ONE): 時效違规自動觸發執行的系統業務邏輯規則。

