Chapter 14: Electronic Procedures
Introduction
Electronic Procedures (E-Procedures) replace paper travelers and instructions on the shop floor. 
They guide operators step-by-step through manufacturing operations.

In This Chapter
• Task Lists
• Tasks
• Documents
• Instructions

TaskList
A TaskList is a collection of individual tasks that must be executed by an operator at a specific 
operation.

Field Definitions:
- Name (String): TaskList name.
- Sequence (String): Sequential or AnyOrder.

Task
A single action the operator must perform (e.g., Scan Material, Read Instructions, Collect Data).

Field Definitions:
- TaskName (String): Name of the task.
- TaskType (String): Instruction, MaterialIssue, DataCollection.

Document
A Document represents an external file (PDF, Image, Video) attached to a task to help the operator.

Field Definitions:
- FileName (String): Name of the file.
- URL (String): Link to the file.

Instruction
Rich text HTML instructions displayed directly on the screen.

Field Definitions:
- Content (String): The instruction text.
