Chapter : Print Queue Modeling
Introduction
The PrintQueue entity defines printer queue configurations for label printing in
Opcenter Execution. It specifies the print queue location, character encoding,
output mode (file vs. printer), and file path templates. Organizations, Parts,
and PartFamilies reference PrintQueues to define their default printing behavior.

In This Chapter
- PrintQueue (Printer Queue)

PrintQueue
A PrintQueue is a named printer queue configuration (CdoId: 7288). It identifies
the printer queue location and controls how labels are encoded and delivered.

Relationship to other modules:

    Organization --(USES_PRINT_QUEUE)--> PrintQueue
    Part --(USES_PRINT_QUEUE)--> PrintQueue
    PartFamily --(USES_PRINT_QUEUE)--> PrintQueue

Field Definitions:
- Name (String, Required): Unique print queue name.
- PrintQueue (String, Required): Identifies the location of the print queue.
- Description (String): Description of this print queue.
- EncodingType (Integer): Character encoding: 1=UTF-16 LE, 2=UTF-16 BE, 3=UTF-8, 4=ASCII.
- OutputToFile (Boolean): Whether to serialize labels to file instead of sending to printer.
- PrintFile (String): Path and template name for serializing labels.
- Notes (String): Internal notes.
- FilterTags (String): Filter tags.
- IsFrozen (Boolean): Whether frozen.
- InstanceLocked (Boolean): Change Management lock.
- ChangeHistory (Navigation): Change history.
- IconId (Integer): Icon ID.
