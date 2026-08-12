Chapter : Process List (Task List) Modeling
Introduction
The ProcessList entity defines a list of tasks to be executed in a workflow process.
It supports sequential and non-sequential execution modes, prerequisite task lists,
workstation assignment, user instructions, and linked image documents.

In This Chapter
- ProcessList (Task List)

ProcessList
A revisioned entity (CdoId: 6798) defining a task list for process execution.

Relationship to other modules:

    ProcessList --(HAS_PREREQUISITE)--> ProcessList (self-referencing)

Field Definitions:
- Name (String, Required): Task list name.
- Revision (String, Required): Version number.
- ExecutionMode (Integer, Required): 1=Sequential, 2=Non-Sequential.
- Instruction (String): User instructions with markup.
- ReportInstruction (String): Plain text instructions for reporting.
- IsImage (Navigation): Linked image document → Document.
- PrerequisiteTaskList (Navigation): Required prerequisite task list → ProcessList.
- Workstation (Navigation): Designated workstation → Workstation.
- WorkstationGroup (Navigation): Designated workstation group → WorkstationGroup.
- Tasks (SubentityList, Required): Task items → ProcessItem.
- Plus standard revisioned entity fields.
