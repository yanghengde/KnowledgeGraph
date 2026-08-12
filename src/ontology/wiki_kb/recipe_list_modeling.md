Chapter : Recipe List Modeling
Introduction
The RecipeList entity (CdoId: 6798) defines a task list for recipe execution contexts.
Same underlying CDO type as ProcessList.

In This Chapter
- RecipeList (Recipe Task List)

Relationships: Self-referencing prerequisite (HAS_PREREQUISITE).

Field Definitions (same as ProcessList):
- Name (String, Required), Revision (String, Required)
- ExecutionMode (Integer, Required): 1=Sequential, 2=Non-Sequential
- Instruction, ReportInstruction, IsImage, PrerequisiteTaskList
- Workstation, WorkstationGroup, Tasks (SubentityList, Required)
- Plus standard revisioned entity fields.
