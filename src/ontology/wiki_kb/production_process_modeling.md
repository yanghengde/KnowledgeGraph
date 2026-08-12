Chapter : Production Process (Electronic Procedure) Modeling
Introduction
The ProductionProcess entity (CdoId: 6794) defines an electronic procedure containing
ordered task lists for manufacturing execution. It supports DrillDown and Outline display
modes for shop floor UI and can execute task lists sequentially or non-sequentially.

In This Chapter
- ProductionProcess (Electronic Procedure)

ProductionProcess
A revisioned entity organizing ProcessLists into a complete manufacturing procedure.

Relationship:
    ProductionProcess --(HAS_TASK_LIST)--> ProcessList

Field Definitions:
- Name (String, Required): Procedure name.
- Revision (String, Required): Version number.
- DisplayMode (Integer): 1=DrillDown, 2=Outline.
- ExecutionMode (Integer, Required): 1=Sequential, 2=Non-Sequential.
- EProcedureDetails (SubentityList, Required): Task lists to execute → ProcessList.
- Plus standard revisioned entity fields.
