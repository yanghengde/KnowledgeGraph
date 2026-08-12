Chapter : Printer Label Definition Modeling
Introduction
The PrinterLabelDefinition entity defines label printer templates and tag mappings
in Opcenter Execution. As a revisioned object (CdoId: 3620/7292), it supports version
control for label templates. It specifies the label template file path, begin/end
delimiters for tag substitution, and a list of label tags whose values are substituted
into the template at runtime. LabelTxnMap references this entity to
configure label printing strategies.

In This Chapter
- PrinterLabelDefinition (Printer Label Definition)

PrinterLabelDefinition
A PrinterLabelDefinition is a revisioned modeling entity that defines a label printing
template. It maps label tags to runtime values and specifies the template file used
for label generation.

Relationship to other modules:

    LabelTxnMap --(USES_LABEL_DEFINITION)--> PrinterLabelDefinition
    PrinterLabelDefinition --(HAS_LABEL_TAG)--> LabelTag

Field Definitions:
- Name (String, Required): Label definition name.
- Revision (String, Required): Revision number (unique per base entity).
- LabelTemplate (String, Required): External path and filename for the label template.
- Description (String): Description.
- Notes (String): Internal notes.
- FilterTags (String): Filter tags.
- Eco (String): Engineering Change Order number.
- Status (Integer): 1=Active, 2=Inactive.
- IsFrozen (Boolean, ReadOnly): Whether frozen.
- IsRevOfRcd (Boolean): Whether this is the current Revision of Record.
- CanChangeRevOfRcd (Boolean): Whether user can change RevOfRcd flag.
- InstanceLocked (Boolean): Change Management lock.
- ChangeHistory (Navigation): Change history.
- IconId (Integer): Icon ID.
- AssociatedPackages (Integer): Associated change package count.
- SetupAccess (Navigation): Setup access configuration.
- Base (Navigation): Base entity reference for version control.
- BeginDelimiter (String): Start delimiter for label tag substitution.
- EndDelimiter (String): End delimiter for label tag substitution.
- LabelTags (SubentityList): Label tag variables → LabelTag.
- WipMsgDefMgr (Navigation): WIP message definition manager → WIPMsgEntity.
