Chapter 13: Quality and Defect Modeling
Introduction
The Quality module tracks defects, nonconformances, holds, and corrective actions (CAPA) to ensure 
that bad product does not reach the customer.

In This Chapter
• Defects
• Nonconformances
• CAPA (Corrective and Preventive Action)
• Hold Reasons

Defect
A Defect represents a specific failure mode observed during production or inspection (e.g., Scratch, Short Circuit).

Field Definitions:
- DefectName (String): Name of the defect.
- Severity (String): Minor, Major, Critical.

Nonconformance
When defects are found, a Nonconformance record (NCR) is generated. This is a formal quality record 
that groups multiple defects for review by a Quality Engineer.

Field Definitions:
- NCRNumber (String): Unique identifier.
- Status (String): Open, InReview, Closed.

CAPA
A CAPA represents the process of investigating the root cause of a Nonconformance and implementing corrective and preventive measures to prevent defect recurrence.

Field Definitions:
- CapaName (String): Unique CAPA identifier or name.
- BriefDescription (String): Short summary of the quality issue or corrective action.
- Description (String): Detailed description of the CAPA investigation, findings, and plan.
- ProposedResolution (String): Action plan proposed to resolve the root cause.
- CloseDescription (String): Notes and explanation written when closing the CAPA.
- Status (Integer): Numeric status code representing the current workflow phase of the CAPA.
- Category (Integer): Classification category of the CAPA (e.g., equipment, training, material).
- IsSubmitted (Boolean): Flag indicating if the CAPA has been submitted for review.
- SystemicIssue (Boolean): True if the investigation shows the problem is systemic across lines or products.
- TriageComplete (Boolean): True if the initial routing and classification triage is complete.
- IsFrozen (Boolean): Indicates whether the modeling instance is frozen (read-only).
- OccurrenceDate (Date): The date and time when the defect or nonconformance occurred.
- ReportedDate (Date): The date and time when the issue was formally logged.
- CloseDate (Date): The date and time when all corrective actions were validated and the CAPA was closed.
- CDOTypeId (Integer): Common Domain Object type ID.
- ChangeCount (Integer): Change counter for the record.

HoldReason
Defines why a container is placed on hold (prevented from further processing).

Field Definitions:
- HoldReasonName (String): Name of the reason (e.g., Quality Review, Engineering Hold).
- Description (String): Description of the hold reason.
- Notes (String): Detailed comments or logic associated with the hold reason.
- IsFrozen (Boolean): Indicates whether the modeling instance is frozen (read-only).
- CDOTypeId (Integer): Common Domain Object type ID.
- IconId (Integer): ID of the icon associated with the hold reason.
- ChangeCount (Integer): Change counter for the record.
- FilterTags (String): Classification filter tags.

CARSeverity
Represents the severity level assigned to a Corrective and Preventive Action (CAPA) record (e.g., Critical, Major, Minor), defining its urgency and follow-up timeline.

Field Definitions:
- Name (String, Required): Unique severity level name.
- Description (String): Description of the severity.
- Notes (String): Detailed comments.
- IconId (Integer): ID of the visual status icon.
- IsFrozen (Boolean): Read-only frozen indicator.
- CDOTypeId (Integer): Common Domain Object type ID.
- ChangeCount (Integer): Change counter.
- FilterTags (String): Filter tags.
- ChangeHistory (Navigation): Change tracking reference.

Classification
Represents high-level quality event categorization (e.g., Defect, Process Deviation, CAPA, Customer Complaint) used globally to determine the triage and execution lifecycle of quality objects.

Field Definitions:
- Name (String, Required): Unique classification category name.
- Description (String): Description of the category.
- Notes (String): Detailed comments or configuration instructions.
- IconId (Integer): ID of the associated icon.
- IsFrozen (Boolean): Read-only frozen indicator.
- CDOTypeId (Integer): Common Domain Object type ID.
- ChangeCount (Integer): Change counter.
- FilterTags (String): Filter tags.
- ChangeHistory (Navigation): Change tracking reference.

Subclassification
Finer-grained subcategories paired with high-level classifications to refine the exact routing spec, failure mode groupings, and workflow templates.

Field Definitions:
- Name (String, Required): Unique subclassification name.
- Description (String): Description of the subclassification.
- Notes (String): Detailed comments.
- IconId (Integer): ID of the associated icon.
- IsFrozen (Boolean): Read-only frozen indicator.
- CDOTypeId (Integer): Common Domain Object type ID.
- ChangeCount (Integer): Change counter.
- FilterTags (String): Filter tags.
- ChangeHistory (Navigation): Change tracking reference.

CommentType
Categorizes the type of comment or annotation attached to quality event logs (EventLog). Used to distinguish between different kinds of remarks such as internal review notes, customer feedback, inspection observations, or audit findings.

Field Definitions:
- Name (String, Required): Unique comment type name.
- Description (String): Description of the comment type.
- Notes (String): Detailed comments or notes.
- IconId (Integer): ID of the associated icon.
- IsFrozen (Boolean): Read-only frozen indicator.
- CDOTypeId (Integer): Common Domain Object type ID.
- ChangeCount (Integer): Change counter.
- FilterTags (String): Filter tags.
- ChangeHistory (Navigation): Change tracking reference.

