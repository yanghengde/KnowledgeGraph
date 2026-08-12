Chapter 12: Data Collection
Introduction
Data Collection in Opcenter Execution allows manufacturers to gather parametric data (temperatures, 
dimensions, test results) during production. It is critical for quality control and statistical 
process control (SPC).

In This Chapter
• Defining Data Collection Definitions (DCDefs)
• Defining Data Points and Limits
• Data Collection History

Data Collection Def
A DataCollectionDef defines a logical group of data points that need to be collected together at a 
specific step in the workflow.

Field Definitions:
- Name (String): Unique identifier.
- Revision (String): Version of the definition.
- Status (String): Active/Inactive.

Data Point
A Data Point represents a single measurement or input value.

Field Definitions:
- PointName (String): Name of the value to collect.
- DataType (String): Integer, Float, String, Boolean.
- IsRequired (Boolean): Whether the operator must fill this in.

Data Limit
Limits define the acceptable range for a Data Point. If a collected value falls outside these limits, 
the system can automatically place the container on hold or log a defect.

Field Definitions:
- UpperLimit (Float): Maximum allowed value.
- LowerLimit (Float): Minimum allowed value.
- Action (String): What to do on failure (e.g., Hold Container).

Data Collection History
When data is actually collected against a container, it is saved as history.

Field Definitions:
- HistoryID (String): Unique transaction ID.
- CollectedValue (String): The actual value inputted by the operator.
- CollectionTime (Date): Timestamp.
