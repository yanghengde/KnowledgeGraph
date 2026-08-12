Chapter 3: Process Model Definitions
Introduction
The process model is the control portion of the application's Information Model. It contains the objects 
that represent your manufacturing process flow: Container Level, Operation, Spec, Product Family, 
Product, Bill of Materials (BOM), ERP BOM, ERP Route, Recipe List, Master Recipe, and Workflow. Refer to 
"Workflows" for information on the Workflow modeling object.
In This Chapter
This chapter contains these topics:
•
About the Process Model
•
Defining Container Levels
•
Defining Operations
•
Defining Specs
•
Defining Product Families
•
Defining Products
•
Defining Bills of Process
•
Defining Bills of Material (BOMs) and ERP BOMs
•
Defining ERP Routes
•
Defining Scheduling Routes
•
Defining Recipe Lists
•
Defining Master Recipes
Release 2510+ Rev. 1
Modeling User Guide
3-1
Chapter 3: Process Model Definitions
About the Process Model
Process Model definitions can be considered in two categories:
•
Workflow Definitions
•
Product Definitions
Workflow Definitions
A workflow defines a sequence of steps that are used to manufacture a product. Workflows are the 
fundamental components of modeling and the heart of the manufacturing process. You must define these 
objects in the order listed prior to defining a workflow:
1.
Resources
2.
Container Levels
3.
Operations
4.
Specs
Refer to "Defining Resources and Resource Setup" for  information on resources. Refer to "Workflows" for  
information on workflows.
You can also define ERP routes—the closest ERP concept to an Opcenter EX MDD or Opcenter EX CR 
workflow. The ERP Route object in Opcenter EX MDD or Opcenter EX CR  is meant to be a mirror of the 
route definitions in the ERP, where the definition stored in the ERP is the master. 
Product Definitions
Products are the materials produced in a factory, or provided by outside suppliers for a Factory. A product 
can be an end-item, subassembly, or component. Products can be grouped into a product family for easier 
maintenance.
A Bill of Materials (BOM) contains the components and quantities required to manufacture a product (end-
item or subassembly). An ERP BOM references steps in an ERP route instead of referencing steps in an 
Opcenter EX MDD or Opcenter EX CR  workflow.
3-2
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Defining Container Levels
A Container Level is the tracking designation assigned to a container. It is also referred to as thruput level. 
Commonly used level names are batch and lot. Levels are defined to meet the specific requirements of 
each company. Examples of some industry-specific levels are roll, bin, and cassette.
Opcenter EX MDD and Opcenter EX CR provide multilevel work-in-process (WIP) tracking capabilities that 
enable you to collect and report status genealogy and parametric information to any level of detail. 
Opcenter EX MDD and Opcenter EX CR use the generic term container to identify a unit of work. You 
decide the specific terminology that matches your operations; for example, a lot, batch, tray, tank, or serial 
number. Because the application supports multiple and unlimited levels of containers—containers within 
containers—you can define and track products to any level of detail.
Many companies also track smaller levels within the larger, parent container. In Opcenter EX MDD and 
Opcenter EX CR, this is accomplished through multilevel container tracking. Parent and child level 
containers are related to each other through the Associate or Start - Two Level transactions. Start - Two 
Level creates the containers and Associate establishes the parent-child relationship. A group of containers 
could have a parent with a batch level and associated child containers with tray levels. Container groups 
can also have more than two levels.
Additionally, you can assign custom, dynamic attributes to a container level. Storing information on the 
container itself prevents you and other users from having to search through the container’s history for the 
information. The application assigns the user-defined attributes when you start a container.
Specifying WIP Messages to Evaluate
Work in progress (WIP) messages can be defined for specific modeling objects so that the message appears 
to a user when a container of material with specific attributes reaches a certain processing point. For 
example, you may define a WIP message to appear when a container reaches the Start spec and a user 
executes a Move In transaction.
You must do the following to configure WIP messages:
•
Define the WIP message on the modeling object. Refer to "Defining WIP Messages" for 
information on defining and configuring WIP messages.
•
Add the modeling object for which you want the message evaluated to the container level 
modeling object, specifically the WIP Message Evaluation Entries grid.
Note:
The order in which you perform these tasks does not matter. You can define the WIP message 
first or add the modeling object to the container level modeling object first.
Release 2510+ Rev. 1
Modeling User Guide
3-3
Chapter 3: Process Model Definitions
The following are the valid values for the WIP Message Evaluation Entries grid:
•
BOM, for Bill of Materials
•
CurrentStatus.
ReworkStatus.ReworkReason, 
for Rework Reason
•
Customer
•
HoldReason, for Hold Reason
•
Level, for Container Level
•
MfgOrder, for Mfg Order
•
Operation
•
Operation.WorkCenter, for 
Work Center
•
Owner
•
Priority, for Priority Code
•
Product
•
Product.ERPBOM, for ERP BOM
•
Product.ProductFamily, for Product Family
•
Product.ProductType, for Product Type 
•
Resource
•
Sales Order, for Sales Order
•
ShippingReason, for Shipping Reason
•
Spec
•
Spec.Setup, for Setup
•
Spec.TxnMap.DataCollectionDef, for Data 
Collection Definition
•
StartReason, for Start Reason
•
UOM
•
Workflow
You must add Level to the WIP Message Evaluation Entries grid for all container transactions for which you 
want to configure WIP messages. 
Excluding WIP Message Evaluation from Specific Operations
When configuring WIP message evaluation, you may specify one or more operations for which you want 
WIP message evaluation excluded. For example, if you have a WIP message configured for the widget 
Product at the Move transaction, you can exclude the Packing operation so that the WIP message does not 
appear when the user executes the Move transaction against a container of the widget product at the 
Packing operation.
Understanding User-Defined Attributes
User-defined attributes are a dynamic set of properties that enable you to store information about a 
container that is easily accessible. For example, you may want to store lab results on the container itself to 
prevent having to search through the container’s history.  An attribute could be as simple as container 
color. User-defined attributes can be unique for each container and do not require a database update 
when assigned. 
Assigning User-Defined Attributes on a Container Start
When you start a container, the application copies the defined attributes to the container from the 
following: 
•
Container Level 
•
Product 
•
Mfg Order
3-4
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
The application copies from container level initially, then product, and then mfg order. If the lists contain 
attributes with the same name, the application overwrites the existing attribute value with the new value 
as long as the data types are the same. If the data types are not the same, the application displays an error 
message. 
Example:
Assume the following objects have these attributes associated:
Container Level
Product
Mfg Order
Model = AAA
Color = Red 
Year = 2015
Color = Blue
The application processes container level first, so the attribute list contains:
•
Model = AAA
The application processes Product next. Product has two new attributes, so the application appends them 
to the attribute list:
•
Model = AAA
•
Color = Red
•
Year = 2015
The application processes Mfg Order last. Mfg Order contains an attribute with the same name as an 
attribute on the container, specifically the Color attribute. The application overwrites the existing Color 
attribute value with the Mfg Order Color attribute value:
•
Model = AAA
•
Color = Blue
•
Year = 2015
The application will store the final attribute list on the container as part of the container’s start history. You 
can view the attributes assigned on a container start in the Manufacturing Audit Trail. Refer to 
"Manufacturing and Resource Audit Trails" for  information. 
When Defining a Container Level
Container is:
•
A required field in the definition of Operation (entered as Thruput Reporting Level), the Start 
transaction, and the Start Two-Level transaction.
•
An optional field in the Container Maintenance transaction. 
Release 2510+ Rev. 1
Modeling User Guide
3-5
Chapter 3: Process Model Definitions
Container Level Page
This image shows an example of the Container Level page. 
Container Level Page Field Definitions
This table defines the fields unique to the Container Level page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
Details
UI Display 
Configuration
UI preference to associate with this container level. A 
UI preference determines the information to display for a 
container in the Status tab on the Manufacturing Audit Trail page. 
UI preferences are defined in Modeling.
Optional
3-6
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field 
Definition
Type
Container 
Numbering Rule
List of all the numbering rules defined in the application. Use this 
field to associate a numbering rule with the container level for 
auto numbering when starting containers.
Note: The application uses this order of precedence to determine 
the numbering rule to use when numbering rules have been 
specified for multiple modeling objects referenced by the 
container: container level, mfg order, product, product family, and 
factory.
Optional
Container Levels
Parent Levels grid
Grid listing container levels that are valid parents of the current 
container level. 
Optional
Child Levels grid
Grid listing container levels that are valid children of the current 
container level.
Optional
WIP Message Configuration
WIP Message 
Evaluation Entries 
grid
Grid listing WIP message labels to be associated with this container 
level.
Optional
Operations Excluded 
grid
Grid listing operations for which you do not want WIP message to 
be included.
Optional
Check for WIP 
Messages in Child 
Containers
When selected, indicates that the application will look for WIP 
messages in child containers.
Optional
User Attributes
User Attribute List 
grid
Grid that displays the user-defined attributes that the application 
will assign when you start a container with this level. 
Optional
Attribute 
Name
Name of the attribute (up to 255 characters). Each attribute name 
must be unique.
Optional
Type
Type of attribute (Integer, Decimal, and so on). When adding an 
attribute, this field is a list that allows you to specify the data type.
Optional
Value
Default value for the attribute. When adding an attribute, enter 
static text or an expression to calculate the value. You can enter a 
maximum of 2000 characters.
Note: When the value is an expression, Siemens recommends you 
select the Is Expression check box to ensure the value is parsed 
correctly.
Optional
Is 
Expression
When selected, this check box indicates the value in the Value field 
is an expression. Selecting this check box ensures the application 
parses the expression correctly.
Note: This check box is applicable only when you specify String as 
the Type.
Optional
Release 2510+ Rev. 1
Modeling User Guide
3-7
Chapter 3: Process Model Definitions
How to Define a Container Level
Follow these steps to define a Container Level:
1.
Open the Container Level page. The Container Level page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this container level in the Container Level field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Refer to "How to Add a Parent or Child Container Level" to add a parent or child container level.
6.
Refer to "How to Add WIP Message Search Criteria to a Container Level"  to add WIP Message 
search criteria.
7.
Refer to "How to Add User-Defined Attributes to a Container Level" to add user-defined attributes.
8.
Click Save. The application saves the modeling object and displays a success message.
How to Add a Parent or Child Container Level
Follow these steps to add a parent or child Container Level:
1.
Perform the "How to Define a Container Level" procedure.
Or 
Select an existing Container Level instance.
2.
Click Add new row on the Parent Levels grid or the Child Levels grid. A new row appears.  
3.
Click in the row to display a list of levels.
4.
Select a level.
5.
Repeat steps 2-4 to add additional levels.
6.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Add WIP Message Search Criteria to a Container Level
Follow these steps to add WIP Message search criteria to a Container Level:
1.
Perform the "How to Define a Container Level" procedure.
Or
Select an existing Container Level instance.
2.
Expand the WIP Message Configuration section.
3.
Click Add new row on the WIP Message Evaluation Entries grid. A new row appears.
4.
Enter a WIP Message label.
5.
Click Add new row on the Operations Excluded grid. A new row appears.
6.
Click in the row to display a list of operations.
7.
Click the operation for which you do not want WIP Message to be included.
3-8
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
8.
Repeat steps 3-7 to add additional criteria.
9.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Add User-Defined Attributes to a Container Level
Follow these steps to add user-defined attributes to a Container Level:
1.
Perform the "How to Define a Container Level" procedure.
Or
Select an existing Container Level instance.
2.
Expand the User Attributes section.
3.
Click Add new row on the User Attribute List grid. A new row appears.
4.
Enter a name for the attribute in the Attribute Name field.
5.
Select the attribute type from the Type list.
6.
Enter a static value or an expression in the Value field.
7.
Select the Is Expression check box when the value is an expression to ensure the value is parsed 
correctly.
8.
Repeat steps 3-7 to add additional attributes.
9.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
3-9
Chapter 3: Process Model Definitions
Defining Operations
An Operation is a manufacturing or processing point where inventory and production activities are 
tracked. An operation is referenced by a specification at a workflow step.
The Operation definition describes items such as the reason codes, processing rules, and the allowed 
transactions for the movement of material through the operation. In contrast, specifications define the 
processing that is performed at an operation.
Some examples of operation information include:
•
References to user codes for recording of loss, bonus, rework, and shipping information
•
Optional designation of the operation as an inventory, in transit, or outside service point
•
Designation of allowed and disallowed transactions
•
Indication if the in-queue status is used, therefore requiring a Move In
The Portal user can specify an Operation when creating an event to identify the manufacturing or 
processing point where the event was detected.
When Defining an Operation
Operation contains:
•
The required modeling definition Container Level (entered as Thruput Reporting Level).
•
The optional modeling definitions Dispatch Rule, Shipment Destination, Training Requirement 
Group, Print Queue, Work Center, and User Code Groups (various reason code groups).
Operation is: 
•
A required field in the definition of Spec. 
•
An optional field in the definition of Employee. 
•
An optional field in the transactions Move In, Move Standard, Move NonStandard, Thruput, 
Transfer, Rework, Transfer Rework, Hold, Release, Container Maintenance, Change Quantity, 
Container Defect, Component Defect, Component Issue, and Component Remove.
The In Queue Containers grid may not appear on the Operational View page if Use Queue is not selected. 
This is determined by the Operation selected in the Line Assignment and the container selected. Refer to 
the Opcenter Execution Medical Device and Diagnostics Shop Floor User Guide or the Opcenter Execution 
Core Shop Floor User Guide for information.
Use the Disposition Details section to select the names of user code groups associated with the reasons for 
quantity changes, and defects. 
The Reject Incoming Nonconforming Container check box is applicable only if your organization has 
purchased the Nonconformance Management module. Selecting this check box enables the application to 
prevent a user from moving a container with open nonconformances to the operation.
Note:
An operation can have related WIP Messages if it is associated with a field from a container 
definition. Refer to "Defining WIP Messages" and the Opcenter Execution Medical Device and 
3-10
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Diagnostics Shop Floor User Guide or the Opcenter Execution Core Shop Floor User Guide for  
information. 
Operation Page
This image shows an example of the Operation page.
Release 2510+ Rev. 1
Modeling User Guide
3-11
Chapter 3: Process Model Definitions
Operation Page Field Definitions
This table defines the fields unique to the Operation page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
General
Work Center
Area of a shop floor where work of a similar nature is performed. For 
example, an area where different product packaging activities occur 
could be designated as a work center.
Optional
Disposition Details
Change Quantity Reasons
Loss Reasons
Name of the user code group that defines the reasons for losses 
during the operation. Losses refer to container units lost during 
processing. 
You can use the system-provided user code group, Loss Reason 
Group, or create a new group to accommodate operation-specific loss 
reasons.
Optional
Sell Reasons
Name of the user code group that defines sell reasons for the 
operation. A sell is a decrease in the quantity of a container and is 
typically attributed to an accounting entity and identified by an 
account number. 
You can use the system-provided user code group, Sell Reason Group, 
or create a new group to accommodate operation-specific sell 
reasons.
Optional
Quantity Adjust 
Reasons
Name of the user code group that defines reasons for adjusting the 
quantity of a container at the operation. Quantity adjust reasons are 
typically used to describe adjustments, either up or down, not related 
to processing activities. For example, you can adjust the quantity of a 
container on completion of an annual inventory count. 
You can use the system-provided user code group, Qty Adjust Reason 
Group, or create a new group to accommodate operation-specific 
quantity adjust reasons.
Optional
Bonus Reasons
Name of the user code group that defines bonus reasons for the 
operation. A bonus is an increase to the quantity of a container. 
You can use the system-provided user code group, Bonus Reason 
Group, or create a new group to accommodate operation-specific 
bonus reasons.
Optional
3-12
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field
Definition
Type
Buy Reasons
Name of the user code group that defines buy reasons for the 
operation. A buy is an increase to the quantity of a container, typically 
attributed to an accounting entity, such as the Engineering 
department. 
You can use the system-provided user code group, Buy Reason Group, 
or create a new group to accommodate operation-specific buy 
reasons.
Optional
Default Rollup 
Reason
Name of the user code group that defines rollup reasons for the 
operation. Container quantity changes are recorded at the lowest 
level (child) container and can use more than one reason code. The 
quantities are then rolled-up to intermediate and top-level parent 
containers. When the rollup occurs, only one reason code is applied to 
the parent containers. The application uses the rollup-reason 
referenced in the operation, unless overridden by the user during the 
quantity transaction. 
You can use the system-provided user code group, Rollup Reason 
Group, or create a new group to accommodate operation-specific 
rollup reasons.
Optional
Defect Reasons
Component 
Defect Reasons
Name of the user code group that defines component defect reasons 
for the operation. A component defect refers to a defective BOM 
component, not counted as a loss against the quantity of the 
associated container. 
You can use the system-provided user code group, Component Defect 
Reason Group, or create a new group to accommodate operation-
specific Component Defect Reasons.
Optional
Container Defect 
Reasons
Name of the user code group that defines Container Defect Reasons 
for the operation. A container defect is a container unit that is 
defective, but not counted as a loss. 
You can use the system-provided user code group, Container Defect 
Reason Group, or create a new group to accommodate operation-
specific defect reasons.
Optional
Defect Reasons
Defect Reason Group containing defect reasons available for the 
operation when a container at the operation is displayed in the 
Opcenter Execution Electronics Production Client Log Defect pop-up.
Note: This field appears only when Opcenter Execution Electronics is 
installed. Refer to the Opcenter Execution Electronics User Guide for 
information.
Optional
Rework Reasons
Release 2510+ Rev. 1
Modeling User Guide
3-13
Chapter 3: Process Model Definitions
Field
Definition
Type
Rework Reasons
Name of the user code group that defines rework reasons for the 
operation. 
You can use the system-provided user code group, Rework Reason 
Group, or create a new group to accommodate operation-specific 
rework reasons.
Optional
Details
Shipment 
Destinations
Named object group that represents a group of shipment 
destinations, a named data object defining the factory or customer to 
which the container is shipped. Used to set up operation with a 
particular shipment destination. For instance, the subassembly 
operation in a plant has to send its products to its designated 
subcontractor, or a final assembly operation ships its FGI to its 
customer (destination). 
Optional
Dispatch Rule
List of dispatch rule instances. Use this field to reference a specific 
Dispatch Rule for the work center. 
Optional
Training 
Requirement 
Group
Training group required before a user is authorized to perform a 
specific task.
Optional
Print Queue
Name of the network printer used to print container labels that are 
associated with this operation.
Optional
Attribute
In Transit
When selected, indicates that containers at the operation are 
considered in-transit for the purpose of movement and tracking 
between both factories and subcontractors. If selected, containers are 
considered in-transit.
Optional
Inventory Point
When selected, indicates that the operation is an inventory holding 
point. If selected, the operation is an inventory point. An inventory 
operation can be a step in a workflow or a stand-alone operation.
Optional
Outside Service 
Point
When selected, indicates that the operation is an outside service 
point, for example a subcontractor. If selected, the operation is an 
outside service point. This information is used for sorting and 
reporting of operation-related information.
Optional
Processing
Use Queue
When selected, indicates that the operation uses a queue status to 
track containers in queue (waiting for processing). If selected, the 
operation uses a queue status. If a queue is used, a MoveIn 
transaction is performed prior to container processing to change the 
status from in-queue to in-process.
Optional
Summary Thruput
When selected, indicates that thruput information at the container’s 
topmost level is recorded, regardless of the Thruput Reporting Level 
field entry.
Optional
3-14
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field
Definition
Type
Reject Incoming 
Nonconforming 
Container
When selected, indicates that containers with one or more open 
Nonconformances cannot be moved to steps for this operation. This 
field is available only as part of the separately licensed 
Nonconformance Management module. 
Optional
Thruput Reporting 
Level
Container Level that the application uses for calculation and reporting 
of thruput at this operation. Refer to the description of Summary 
Thruput.
Required
Display Options
Defines a set of display options to use in the image visualization area 
of the Production Client page. 
Note: This field appears only when Opcenter Execution Electronics is 
installed. Refer to the Opcenter Execution Electronics User Guide for 
information.
Optional 
NPI Document 
View
Specifies the NPI document view to display by default in the 
Production Client visualization tool.
Note: This field appears only when Opcenter Execution Electronics is 
installed. Refer to the Opcenter Execution Electronics  User Guide for 
information.
Optional
Disallowed 
Transaction(s) 
grid
Grid listing transaction types that are not allowed for this operation. 
Optional
How to Define an Operation
Follow these steps to define an Operation:
1.
Open the Operation page. The Operation page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for the operation in the Operation field.
4.
Enter a Thruput Reporting Level.
5.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
6.
Click Save. The application saves the modeling object and displays a success message.
How to Specify a Transaction that Is Disallowed for This Operation
Follow these steps to specify a transaction that is disallowed for this operation:
1.
Perform the "How to Define an Operation" procedure.
Or
Select an existing Operation instance.
2.
Expand the Details section.
3.
Click Add new row on the Disallowed Transaction(s) grid. A new row appears.
4.
Select a transaction for entry in the Txn Type field.
Release 2510+ Rev. 1
Modeling User Guide
3-15
Chapter 3: Process Model Definitions
5.
Repeat steps 3-4 as needed to add another disallowed transaction.
6.
Click Save. The application displays a success message indicating the modeling object was 
updated.
3-16
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Defining Specs
A Spec (specification) defines the activities carried out at a step in a workflow or master recipe and 
includes detailed scheduling and processing parameter information. Specs reference many other modeling 
components including Operation, Setup, Data Collection Definition, and Resource.
When defining workflows and master recipes, the application requires that you reference at least one 
spec. One spec can be referenced multiple times by different workflows and master recipes.
A Portal user can specify a spec when creating an event.
When Defining a Spec
Spec contains:
•
The required modeling definition Operation.
•
The optional modeling definitions Business Rule, Data Collection Definition, Document Set, 
Electronic Procedure, Electronic Signature Requirement,  Printer Label Definition, Recipe, Resource 
Group, Scale Group, Setup, and Training Requirement Group.
Note:
The Scale Group field appears only when Batch Processing is installed. Refer to "Batch 
Processing" for information.
Spec is a required field in the definition of Workflow and Master Recipe.
Note:
A Spec definition can have related WIP messages if it is associated with a field from a container 
definition.
When Assigning Electronic Signatures and Electronic Procedures
Electronic signatures assigned in the Electronic Signature TxnMap work for container transactions only. If 
you associate an electronic procedure with this spec and you want to capture electronic signatures for the 
electronic procedure tasks, you must assign the electronic signatures for instruction and computation 
tasks separately. The electronic signature assigned to the spec will work for transaction tasks in the 
electronic procedures. Refer to "Defining a Task List and Related Tasks" for information on defining 
instruction and computation tasks.
Adding Electronic Signature Requirements for Attaching or Detaching Documents on 
Specs
You can set requirements for users to provide electronic signatures to attach documents to or detach 
documents from specs. Documents can include special instructions, test results, drawings, or photos. Refer 
to the Opcenter Execution Medical Device and Diagnostics Shop Floor User Guide or the Opcenter 
Execution Core Shop Floor User Guide for information on document attachment.
The option to set electronic signature requirements for document attachment or detachment appears in 
the Electronic Signature Txn Map in the Transactions section. You can optionally choose to require all 
transactions to have electronic signatures.
Release 2510+ Rev. 1
Modeling User Guide
3-17
Chapter 3: Process Model Definitions
Adding Electronic Signature Requirements for Collecting Lot Sampling Data on Specs
You can set requirements for users to provide electronic signatures for collecting lot sampling data on 
specs. The option to set these requirements appears in the Electronic Signature Txn Map in the 
Transactions section.
You can submit the signatures for collecting lot sampling data on the Collect Lot Sampling Data shop floor 
page. Refer to  the Opcenter Execution Medical Device and Diagnostics Shop Floor User Guide or the 
Opcenter Execution Core Shop Floor User Guide  for information.
Adding Process Timers
You can add process timers to control and monitor the manufacturing process. You can define actions for 
the application to take if a transaction tries to process before a minimum time is met or a maximum time 
has passed.
The option to set process timers on a spec appears in the Start Timer and End Timer Txn Maps in the 
Transactions section. The application requires you to assign either the Move or Move In transaction to any 
process timer that you set. Assigning the Move transaction to a timer causes the application to trigger the 
timer when a container moves out of the spec where it is set. Assigning the Move In transaction to a timer 
causes the application to trigger the timer when a container is moved into the spec where it is set.
Refer to the Opcenter Execution Medical Device and Diagnostics Shop Floor User Guide or the Opcenter 
Execution Core Shop Floor User Guide  for information.
Note:
Every process timer should have a start and end timer, but there is no logic to prevent you from 
having one without the other.
Note:
Process Timers are only dependent on the Move (Standard) or Move In transactions. The applic-
ation does not take into account the number of these transactions that could be performed on 
an EProcedure task. The process timer stops when the task is executed.
Adding Business Rules to a Spec
You can add business rules to a spec so that the business rule logic executes when an event associated 
with a container transaction occurs. Add the business rules in the Business Rule Txn Map grid within the 
Transactions section. Only business rules assigned the Container Usage type are available for selection. 
Refer to "Business Rule Page Field Definitions" for information.
The Business Rule Txn Map grid contains three columns: Business Rule, Event, and Transaction. Select the 
business rule and the container transaction that will execute it. Also, select the event that determines 
when the business rule executes in the container transaction. Available events include the following:
•
Execute User
•
Export Info Initialize User
•
Pre Execute User
•
Pre Validate User
•
Process After Commit User
•
Validate User
3-18
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Reprocessing a Container at a Prior Step
You can use the Spec page to enable reprocessing a Container at its prior step with the Allow Reprocess 
option. 
The reprocess occurs during a Move or Move In transaction. In order for the reprocess to occur, you must 
specify a Resource in the transaction, and a Resource Group must be assigned to the Spec where 
reprocessing can occur and the following Spec. Additionally, if the Container's current step (the step after 
it is reprocessed) requires a Move In transaction, the Container must be still be In Queue. The Use Queue 
option is managed on the Operation, and it can be enabled on either the Spec where reprocessing will 
occur or the Spec after the Spec where reprocessing will occur. For more information on the Use Queue 
option, see "Defining Operations" in this guide.
Expiration Date Calculation on the Spec Page
Note:
The functionality described below is available only when Medical Device is installed. Refer to 
"Medical Device Workspace" for information.
You can use the Spec page to define the fields required for automatic calculation of an expiration date for 
a container when a predefined transaction is successful at an identified spec. These fields are as follows:
•
Expiration Date Transaction
•
Expiration Period Units
•
Expiration Period
The container's expiration date is calculated based on the spec information only if the product does not 
have an expiration date defined.
If the container already has an expiration date that is earlier than the calculated date, the expiration date is 
not updated unless the Always Override Expiration Date check box is selected.
The expiration date adjusts to the last day of the month if the Expiration Period Units field is set to Months 
and the expiration date calculation results in an invalid date. For example, if the current date is January 31 
and the expiration period is three months, the calculated expiration date is April 31. The date adjusts to 
April 30.
Manufacturing Date Calculation on the Spec Page
Note:
The functionality described below is available only when Medical Device is installed. Refer to 
"Medical Device Workspace" for information. 
You can select a Manufacturing Date Transaction on the Spec to automatically assign a manufacturing 
date to the container. This will assign the transaction date and time to the Manufacturing Date field on the 
container. If there is manufacturing date information defined on the product, the product data takes 
precedence.
Defining a UDI on the Spec Page
Note:
The functionality described below is available only when Medical Device is installed. Refer to 
"Medical Device Workspace" for information.
Release 2510+ Rev. 1
Modeling User Guide
3-19
Chapter 3: Process Model Definitions
The application's Unique Device Identification (UDI) functionality allows you to validate that a container 
has been assigned a UDI. A container cannot move until the UDI field has a value if the Validate UDI on the 
spec is selected.
Assigning a Scale Group on the Spec
Note:
The functionality described below is available only when Batch Processing is installed. Refer to 
"Batch Processing" for information.
You can assign a scale group on the spec using the Scale Group field. You can also assign a scale group on 
the product family, product, and weigh issue task.
These rules apply when assigning scale groups:
•
The scale group assigned on the product family takes precedence over the scale group assigned 
on the spec. 
•
The scale group assigned on the product takes precedence over the scale group assigned on the 
product family. 
•
The scale group assigned on the weigh issue task takes precedence over the scale group assigned 
on all other objects. 
Refer to "Assigning a Scale Group on the Product Family," "Assigning a Scale Group to a Component 
Product," and "When Defining Weigh Issue Tasks" for information.
Defining Team Tracking Transactions on the Spec Page
Note:
The functionality described below is available only when Medical Device is installed. Refer to 
"Medical Device Workspace" for information.
You can use the Spec page to define the transactions that require tracking of work performed by 
employees at a given operation, spec, work center, work cell, or workstation. Defining transactions at the 
factory level allows you to set tracking requirements for all specs instead of modifying each spec in a 
workflow. However, any transactions set at the spec level take precedence over selections made at the 
factory level.
Placing a Container On Hold Automatically at a Step
You can use the Spec page to automatically place a container or multiple containers on hold from moving 
in or out of a workflow step by defining the Container Auto Hold Requirement Transaction.
When a shop floor transaction such as MoveIn, Move, MoveNonStd or Rework is performed, the containers 
are automatically placed on hold based on the following available options:
•
Mfg Order (all containers of Mfg Order will be stopped)
•
Container List (list of container names to be stopped)
•
Container Identifier range - Start and End text values
•
Lot List (list of Lot codes - which may also represent a Container - that have been issued to the 
container)
3-20
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
•
Expression - allows for defining any additional custom logic that may want to be implemented
The containers will only be able to move to the next step once the hold reason has been satisfied and 
fulfilled.
Note:
For the Move, MoveNonStd and Rework transactions, the Auto Hold Requirements are eval-
uated when a container is moving to the step.  The hold is placed after the container moves 
from the previous step to the step with the Auto Hold Requirement configured.  For the MoveIn 
transaction, the container will be placed on Hold when it moves in to the step with the Auto 
Hold Configuration enabled.
Spec Page
This image shows an example of the Spec page.
Spec Page Field Definitions
This table defines the fields unique to the Spec page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
General
Release 2510+ Rev. 1
Modeling User Guide
3-21
Chapter 3: Process Model Definitions
Field 
Definition
Type
Engineering 
Change 
Order
Engineering change order assigned to this revision. You can enter a maximum of 
30 characters.
Optional
Operation
Manufacturing or processing point where inventory and production activities are 
tracked. An operation is referenced by a specification at a step in a workflow.
Required
Processing
Resource 
Group
List of resources defined through the Resource Group page that are valid for the 
specification.
Optional
Document 
Set
Collection of one or more documents. Document sets are referenced by other 
modeling entities and provide extended information such as drawings, scanned 
images, and procedures.
Optional
Training 
Requirement 
Group
Training group required before a user is authorized to perform a specific task.
Optional
Electronic 
Procedure
Name given to a series of tasks required to complete the work required by the 
specification.
Optional
Setup
Physical machine configuration for a particular process. 
Optional
Recipe File
Name of the recipe definition used to define the resource settings for this 
specification. Enter a specific revision for the recipe file, or click the check box to 
use the current revision of record.
Optional
Validate 
Material 
Consumptio
n
When selected, the application validates that all material and quantities that are 
to be consumed at an operation were actually consumed into the unit or batch 
before the unit or batch can be processed.
Note: This check is not performed for components with an Issue Type of Display 
Only. 
Optional
Validate Lot 
Sampling 
Complete
Check box that requires a validation that the container's lot sampling has been 
completed when the container is moved to this spec.
Optional
Verify 
Recipe
Check box that determines whether recipe validation should occur for containers 
at this spec. Leaving the check box blank causes the application to ignore recipe 
validation that might otherwise occur at this spec.
Note: This field appears only when Opcenter EX Electronics or the Industry 
Solutions workspace is installed.
Optional
Require 
Resource
Check box to indicate whether a resource must be specified when performing a 
move transaction.
Note: This field appears only when the Industry Solutions workspace is installed, 
but it is also used by Opcenter Execution Electronics.
Optional
Allow 
Reprocess
This option allows a container to be automatically re-processed at a step when it 
has moved out of the step and the subsequent Move In / Move transaction is 
performed using the same Resource as the prior transaction and that resource is 
not allowed to be used at the current step.
Optional
3-22
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field 
Definition
Type
Allow Other 
Resource
This option allows a different resource that is valid at the previous step to 
perform the reprocess when it fails the resource group validation at the current 
step.
Optional
Require Pre-
Production 
Procedure
When this option is set, all Move and Move In transactions on a container are 
blocked until the Pre-Production Procedure is complete. If no Pre-Production 
Procedure is set on the order, this option has no effect. If a Pre-Production 
Procedure is set but this option is not set, the procedure is optional, and there is 
no restriction on container movement.
Optional
Post-
Production 
Action
This option defines the step where a Post-Production procedure becomes 
enabled, and it allows you to optionally block container movement until 
complete. This option can be left blank, set to 'Enable Procedure,' or set to 
'Require Procedure.' 
Leaving it blank for all workflow steps means any Post-Production Procedure 
configured on an Mfg Order is ignored. Container movement is not restricted. 
'Enable Procedure' means the Post-Production Procedure is not allowed to start 
until the following conditions are met: all containers have been started; all are in 
queue, in process, or have been processed at this step; or scrapped. Container 
movement is not restricted.
'Require Procedure' is used to block container movement beyond this step until 
the Post-Production Procedure has been completed. If the procedure is not 
already enabled by a prior step configured with the ‘Enable Procedure’ option, 
then it will be enabled when the following conditions are met: all containers 
have been started; all are in queue or in process at this step; or scrapped.
Optional
Optional
Defines whether the processing for the spec is optional in the workflow. 
Available options are:
•
Not Set
•
Yes
•
No
Optional
Verify Tool 
Plan
Check box to trigger tool plan validation when a container is at a step based on 
this spec.
Optional
Validate 
Active Mfg 
Order
When selected, the application validates the containers against a manufacturing 
order marked as an active Mfg Order of a  resource for any movement 
transactions of that resource. If a container's Mfg Order does not match, an error 
is displayed. 
Note: This field appears only when Opcenter Execution  Electronics is installed. 
Refer to the Opcenter Execution  Electronics User Guide for information.
Optional
Release 2510+ Rev. 1
Modeling User Guide
3-23
Chapter 3: Process Model Definitions
Field 
Definition
Type
Auto Fill 
Data 
Collection
This option automatically populates previously recorded data for the current 
container data collection activity if available. If data collection has been 
performed and recorded for containers associated with the same Product, 
Manufacturing Order, or Step, the application checks for the previously recorded 
data for the current collection. This option only supports Textbox based data 
collection definition data type which includes String, Integer, Decimal, Fixed, and 
Float.
Note: This field appears only when Opcenter Execution  Electronics is installed. 
Refer to the Opcenter Execution  Electronics User Guide for information.
Optional
Board Side
Indicates a side of a PCB board. The selection field contains the following 
selections:
•
Null (No selection)
•
Top
•
Bottom
Note: This field appears only when Opcenter Execution  Electronics is installed. 
Refer to the Opcenter Execution  Electronics User Guide for information.
Optional
Queue Time
Max Queue 
Time
Maximum allowable time in queue.
Optional
Bill of Process Overrides
Allow 
Overrides
When selected, this check box allows bill of process overrides on this spec. The 
field is selected by default.
Optional
Bill of 
Process 
Grid listing every bill of process assigned to this spec. Displays the bill of process 
name and description entered on the Bill of Process page. When assigned, the bill 
of process overrides the spec.
Display 
Only
Batch 
Processing
Note: This section appears only when Batch Process is installed.
 
Scale Group
List of available scale groups.
Optional
Transactions
Data 
Collection 
Txn Map
Grid listing the transactions in this spec for which a data collection definition is to 
be assigned. 
Optional
Electronic 
Signature 
Txn Map
Grid listing the transactions in this spec for which electronic signatures are 
required. 
A grid that identifies the details of transactions in this spec for which electronic 
signatures are required. 
Optional
Label Txn 
Map
Grid listing the transactions in this spec for which container labels are to be 
printed. 
Optional
Start Timer 
Txn Map
Grid listing the transactions (Move or Move In) in this spec that will trigger 
associated process timers to start.
Optional
3-24
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field 
Definition
Type
End Timer 
Txn Map
Grid listing the transactions (Move or Move In) in this spec that will trigger 
associated process timers to stop.
Optional
Business 
Rule Txn 
Map
Grid listing the container transactions in this spec that will execute the business 
rule when the specified event in the transaction occurs. Available events include 
the following:
•
Execute User
•
Export Info Initialize User
•
Pre Execute User
•
Pre Validate User
•
Process After Commit User
•
Validate User
Note: Only business rules assigned the Container Usage type are available.
Optional
Container 
Auto Hold 
Req Txn Map
Grid listing the container transactions in this spec that will execute the container 
auto hold requirement transaction when the specified event in the transaction 
occurs. Available events include the following:
•
Move
•
Move In
•
Move Non Std
•
Rework
The Container Auto Hold Requirement field in this grid lists all of the container 
auto hold requirement modeling  done on the modeling page. You can set the 
start and end date range in which the auto hold requirement will take effect. 
Optional
Action Txn 
Map  
Grid listing the container transactions in this spec that will execute the associate 
and disassociate action when the specified condition in the transaction occurs. 
Available transaction types include the following:
•
Move
•
Move In
•
Move Non Std
•
Rework
Action field on this grid specifies how the Spec should associate or disassociate 
with the container. Options include: 
•
Auto Disassociate (HPE)
•
Manual Associate
•
Manual Disassociate 
Note: Auto Disassociate has been renamed to Auto Disassociate (HPE) and 
enhanced with High Performance Engine (HPE) to increase larger transaction 
efficiency as the application processes transactions on the database rather than 
the application server. Refer to Opcenter™ Execution Core Technical Reference: 
High Performance Engine for information.
Optional  
Release 2510+ Rev. 1
Modeling User Guide
3-25
Chapter 3: Process Model Definitions
Field 
Definition
Type
Team 
Tracking 
Transaction
s
Note: This section appears only when Medical Device is installed.
 
Team 
Tracking 
Transactions
Grid allowing you to select transactions that require tracking of team members.
Optional
Scheduling
Standard 
Batch Size
Standard container batch size of products processed using the specification. The 
value in this field is for information only. It is not used for system calculations.
Optional
Yield
Standard processing yield (as a percentage) for products processed using the 
specification. The value in this field is for information only. It is not used for 
system calculations.
Optional
Setup Time
Standard setup time (in days [optional], hours, minutes, and seconds) for a 
standard product batch. The value in this field is for information only. It is not 
used for system calculations.
Optional
Unschedule
d Time
Process time  (in days [optional], hours, minutes, and seconds) that is not 
contained or counted in the Unit Per Hour, Hour Per Unit or Batch Time entries. 
This field allows you to take into account the unscheduled times taken for other  
additional processes such as skipped steps, equipment cool-down time and cure 
time. 
Optional
Device 
Identificati
on
Note: This section appears only when Medical Device is installed.
 
Always 
Override 
Expiration 
Date
Check box indicating the container's current expiration date (if any) will be 
overridden regardless of which date is older.
 
Optional
Expiration 
Date 
Transaction
Transaction where the expiration date is assigned. Transactions are limited to 
Move or Move In and their subclasses.
Note: This field is required if any of the other expiration fields are populated.
Condition
al
Expiration 
Period Units
Units of time represented by the expiration period. Options include the following:
•
Days
•
Months
Note: This field is required if any of the other expiration fields are populated.
Condition
al
Expiration 
Period
Period of time (duration) that is added to the current time to determine the 
Expiration Date.
Note: This field is required if any of the other expiration fields are populated.
Condition
al
3-26
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field 
Definition
Type
Manufacturi
ng Date 
Transaction
Transaction where the manufacturing date is assigned to the container. 
Transactions are limited to Move or Move In and their subclasses.
Optional
Assign UDI
Check box indicating UDI information (device identifier, production identifier, 
and UDI) is calculated.
Optional
Validate UDI
Check box indicating a validation needs to occur to ensure the container has UDI 
before being allowed to move.
Optional 
Run Rate
Hours Per 
Unit
Selected Run Rate Option and the time (in days [optional], hours, minutes, and 
seconds) required to process one unit of product. If this is specified, then Units 
Per Hour and Time Per Batch are disabled.
Optional
Units Per 
Hour
Selected Run Rate Option and the number of container units processed per hour 
at the step. If this is specified, then Hours Per Unit and Time Per Batch are 
disabled.
Optional
Time Per 
Batch
Option to select a run rate of the time required to complete one batch. 
Use the associated field to enter the batch processing time (in days [optional], 
hours, minutes, and seconds). If this is specified, then Hours Per Unit and Units 
Per Hour are disabled.
Optional
Normal 
Cycle Time
Standard time (in days [optional], hours, minutes, and seconds) required to 
process product under normal circumstances. 
Optional
Fast Cycle 
Time
Standard time (in days [optional], hours, minutes, and seconds) required to 
process product under expedited circumstances. 
Optional
Electronics
Note: This section only appears if Opcenter Execution Electronics is installed.
 
Processing
 
 
Product 
Conversion 
Requirement
Indicates the requirement needed for Product Conversion. Valid values include:
•
NULL - Empty string indicating no conversion required  and the Verify 
Container Product Conversion service flag  set to true.
•
MANUAL - Conversion must be manually done before a  Move transaction 
with the Verify Container Product  Conversion service flag set to true.
•
AUTO - Conversion will be automatically done during a  Move transaction 
with the Verify Container Product  Conversion service flag set to true.
Optional
Default Issue 
Difference 
Reason
Describes the reason for a difference between the required quantity  and the 
actual quantity issued.
Note: This field is used by Component Issue if an Issue Difference  Reason is not 
provided.
Optional
Default 
Substitution 
Reason
Reason that the product actually used differed from the product  specified to be 
used.  
Note: This field is used by Component Issue if a Substitution  Reason is not 
provided for substitutes.
Optional
Release 2510+ Rev. 1
Modeling User Guide
3-27
Chapter 3: Process Model Definitions
Field 
Definition
Type
Display 
Options
Holds information about the colors, display and other options used by the 
Product Client page image visualization component to view NPI job images.
Optional
Thruput 
Requirement
Indicates the requirement for thruput when a container is  executing a move 
transaction. Valid values include:
•
OPTIONAL - Thruput is not required.  
•
AUTO - Thruput will be automatically triggered before  move. Always full 
quantity thruput is done.  
•
MANUALPARTIAL - Thruput is required but does not need  to have the full 
container's quantity thruput. Error will be  raised during move if no 
quantity thruput detected.  
•
MANUALFULL - Thruput is required and the container's  quantity must be 
fully thruput. Error will be raised during  move if quantity thruput is not 
full.  
Note: The ProcessThruputRequirement service flag must be set to  true.
Optional
Mfg Order 
Reassign 
Plan
List of Mfg Order Reassign defined in Mfg Order Reassign Plan modeling page 
allowing a user to  change a manufacturing order  of one or more containers to 
another manufacturing order.
Optional
Mfg Line
The manufacturing line to which the spec is associated. For Mfg  Line verification, 
this value is required for the logic to compare  against the container's Mfg Line 
before verification takes place. If  not set, meaning it is null, the spec is assumed 
to be used for the  Mfg Line the Container in which it is running. This will allow 
the  same workflow to be used for multiple Mfg Lines.
Optional
Side
Text field designed for indicating the side of the PCB/Panel being populated, for 
example, Top, Bottom or Both.
Optional
Multi 
Container 
Defect 
Matrix
List of Multi Container Defect Matrixes defined in Multi-Container Defect Matrix 
modeling page allowing a user to configure how defects can be automatically 
handled in production. This feature is only applicable to Electronics' ES_
MultiContainerDefect transaction.
 
Optional
Perform Mfg 
Order 
Reassign
Check box that when selected displays a pop-up requiring the operator to 
reassign currently entered or scanned containers to a different manufacturing 
order during the next Move In or Move transaction at the current step.
Optional
Verify Mfg 
Line
Flag used to trigger the Mfg Line verification logic from a  container's current 
step.
Optional
Verify Tool 
Plan
Check box to trigger tool plan validation when a container is at a step based on 
this spec.
Optional
Record 
TDA Details 
History
Check box to indicate whether the application is to record TDA activity in the 
HistoryMainline.
Optional
3-28
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field 
Definition
Type
Verify 
Exposure 
Duration 
Check box that controls whether the exposure duration will be  verified during 
Move In and Move transactions. If the exposure duration is within the specified 
limit, the application displays a  success message during these transactions, along 
with the  Remaining Exposure Duration information. If the exposure duration is 
exceeded, the  application displays an error message and prevents further Move 
In and Move  transactions.
Optional
Is Material 
Withdraw
Check box that sets a flag used when a container moves out of a spec. The flag is 
used to set the start of the material's exposure duration. The container's 
MaterialWithdrawalDate will be set to the Move transaction date only if it is null. 
Otherwise the difference between the MaterialWithdrawalDate and the Move 
transaction date will be updated to the container's MaterialExposureOffset. This 
offset is used to represent a temporary stoppage of the exposure.
Optional
Is Material 
Issue
Check box that sets a flag used when ResourceComponentSetup or 
ComponentIssue is transacted. The transaction will not be allowed in the 
following situations if the option is not enabled:
•
If there is a thawing requirement
•
If the container accumulates exposure and has a withdrawal date or has 
accumulated exposure time
•
If there is an expiration date set on the container
Optional
Is Material 
Return
Check box that sets a flag used when a container moves to a Spec. Note that the 
destination Spec's attribute is used for the logic. The container product's 
MaterialMaxReturns will be used to verify whether a move to such a Spec is 
allowed. Once the lot hits beyond the value (considered only if > 0), the 
container will not be allowed to move to the Spec. If not violated, the container's 
MaterialTotalExposure will be accumulated if the product's 
MaterialAccumulateExposure is set to true and there is a MaterialWithdrawalDate 
value. Then, the container's MaterialTotalReturns will be incremented by 1, the 
MaterialWithdrawalDate nullified and the MaterialExposureOffset set to 0.
Optional
Auto Close
Check box that determines whether the MoveTxn will close a container when it is 
moved to the destination spec.
Optional
Close Parent 
Containers
Used within the existing Disassociate logic to close the parent containers (panels) 
after the children containers (PCBs) have been released or disassociated. Refer to 
"Auto Disassociate."
Optional
Auto 
Disassociate
Check box to select the Depanelization option. PCBs will be depaneled from their 
parent panel at a step based on this spec if the Auto Disassociate check box is 
selected.  
Optional
Release 2510+ Rev. 1
Modeling User Guide
3-29
Chapter 3: Process Model Definitions
Field 
Definition
Type
Dissassociat
e Before 
Move
Option that lets you depanel prior to the move transaction so that individual 
panels can be routed according to their pass/fail status. If the Auto Disassociate 
check box is also selected, each child container will be moved to their respective 
workflow paths. If Auto Disassociate is not set, no disassociation will occur.
Note: When using this option, the following functionality is not supported and 
will result in the entire transaction failing: 
•
Electronic Signatures configured on the Move, Rework, Change Qty, or 
Hold transactions.
•
Data Collections configured on the Move, Rework, Change Qty, or Hold 
transactions.
Optional
Auto Issue 
to Panel
Check box to configure how the application handles Auto Component Issue for 
panelized products. By default, this check box is blank which means that 
components configured for automatic issue are issued to each PCB but not to the 
panel. Selecting the check box means that components configured for automatic 
issue are issued to the panel but not the PCBs.
Note: When the Auto Issue to Panel check box is selected, the application 
multiplies component Qty by the number of PCBs to which the component will 
be issued to derive the quantity applied to the panel.
Optional
Auto 
Component 
Issue
Check box that determines whether the application will automatically trigger the 
ComponentIssue transaction during a MoveTxn when a resource is provided and 
at least one IssueDetails is detected.
Optional
First Article 
Mode
 
Application that provide a guide to an operator when doing inspection of a 
product or component. The operator will be taught or given special instruction 
when doing inspection when this application is enabled. Available component 
option for the First Article Mode includes:
•
All Component - Inspection to be done to all component.
•
None -No inspection needed.
•
Specific Component - Inspection needed to be done for a list of 
component defined during NPI job modeling.
Optional
Auto Open 
Instructions 
Check box that allows the NPI's Instruction slide-out panel to automatically 
displayed in the beginning of a Production Client session if there is Instruction 
configured. The Instruction Slide-Out Panel will be displayed regardless on 
whether this check box is selected or not  if:
•
The First Article Inspection Mode is configured, 
or 
•
The NPI Instructions configured requires confirmation action.
Optional
3-30
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field 
Definition
Type
First Article 
Tracking 
Mode 
Application that allow tracking when First Article Inspection has been completed. 
This option is required if the First Article Mode is selected. The First Article 
Tracking Mode frequency is indicated by the following:
•
Per Container 
•
Per Day 
•
Per Mfg Order
•
Per Product 
Optional
Assign 
Physical 
Address
Check box that determines whether the application should automatically assign 
physical addresses when a container is moved from the workflow step based on 
this spec.
Optional
Verify 
Physical 
Address
Check box that determines whether the application will verify that all physical 
addresses have been assigned, and prevent the container moving from the step if 
they are not assigned.
Optional
Enable Tool 
With Issue
If true, it will be possible to collect a single Tool value with each component issue 
done at this Spec.  This value indicates the Tool that was used for the issue.
If false, it will not be possible to collect a Tool value for each issue done at this 
Spec.
Optional
Production 
Client 
Options
 
 
Serial 
Number 
Entry 
Default 
Mode
Option that controls whether the Production Client will open a session  for 
performing defect logging and repair, component issue, replace or remove, and 
working with any configured work instructions (the "Start Session" option).  The 
"Pass" option will allow for scanning one or more containers and then moving 
them through the step (performing a MoveIn as required).
Optional
Use 
Production 
Client Box 
Mode
When a container is at a step based on this Spec, this option forces Production 
Client to open in box mode even if there is an associated NPI Job.
Optional
Use Material 
Setup
Check box that determines whether a material setup is used. A material setup is a 
material setup information (setup information such as identifiers, material 
requirements, Issue Details, issue control type, Mfg Order, Workflow Step, 
Resource)  exist and saved from previous scanned containers. The setup 
information is retrieved when the material setup for current containers matches 
the existing container's Mfg Order, Workflow Step, or Resource information.
If selected, the application auto-populates the Issue Details field of the 
components in the Assembly client and Production Client page with previous 
issue details added for containers with the following Issue Control type:
•
Bulk
•
Lot and stock point  
•
Stock point only.
Optional
Release 2510+ Rev. 1
Modeling User Guide
3-31
Chapter 3: Process Model Definitions
Field 
Definition
Type
Exclude 
Suspended 
Time
Check box that determines whether  the "ERP Target Time" calculation will 
exclude the time a container has been suspended . When the check box is 
selected, the application will only need to count the time between when a 
container Moves In and Suspend for each of those operations. 
Optional
Hide Non 
Open Defect 
From Previo
us Steps 
When the check box is selected, only Open defects are displayed in the 
Production Client grid. 
Note: The application will display the defects regardless of their status (such as 
Repaired, Open and etc.) if the defects are recorded in the current session.
Optional
Auto Select 
Pin Defects 
on the Same 
Component
Once the panel/PCB is at the step that uses this Spec, when you select one of the 
open pin defects, the rest of the open pin defects on that component will be 
checked.
Optional
Iteration Limit Check 
Enable 
Iteration 
Limits
Check box that indicates whether the application will prevent a container from 
going through a step based on this spec if doing so would exceed the configured 
limit.
Optional
Iteration 
Limit
Maximum number of times the same container may go through a step based on 
this spec. 
Note: The application does not use this field unless the Enable Iteration Limits 
check box is selected.
Optional
Iteration 
Limit Fail 
Action
Action to take on a container when it exceeds the Iteration Limit. Example 
actions include Hold and Scrap.
Optional
Iteration 
Limit Default 
Hold Reason
Hold reason to use as the default when a container  is placed on hold due to 
having exceeded the Iteration Limit.
Optional
Iteration 
Limit Default 
Loss Reason
Scrap reason to use as the default when a container  is scrapped due to having 
exceeded the Iteration Limit.
Optional
Auto Clear Open Defects
3-32
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field 
Definition
Type
Clear Open 
Defects 
Check box to enable automatic clearing of all open defects logged at the spec or 
at the spec and resource. Clearing occurs at the Move In transaction.
Note: When Clear Open Defects check box is selected and:
•
Bypass Resource option is enabled 
or ,
•
Target Specs are assigned
or,
•
Both Bypass Resource and Target Specs are configured, the following 
occurs:
If Clear 
Open 
Defect is 
set to...
Bypass 
Resource 
is set to...
Target Specs 
is set to...
Then...
True
False
No entries
Clear all open defects logged for the 
container if the current resource 
matches, or if both the current 
resource and the defects have no 
resource specified.
True
False
Entry
Clear all open defects logged for the 
specified Target Specs if the current 
resource matches, or if both the 
current resource and the defects have 
no resource specified.
True
True
No Entries
Clear all open defects logged for the 
container, regardless of resource or 
spec.
True
True
Entry
Clear all open defects logged for the 
specified specs, regardless of 
resource.
 
Optional
Clear 
Defects 
Action
 
Action that specifies how to clear the defects. Options include:
•
Delete - The application deletes the defects.
•
NFF - Sets defects to No Fault Found, effectively negating them.
•
None - No clearing occurs and check box is ignored.
Optional
Bypass 
Resource
Check box to enable clearing of all open defects logged at specified specs 
regardless of resource.
Note: Clear Open Defects option must be selected together with Bypass Resource 
check box to execute the defect clearing logic. 
Optional
Target Specs
Grid containing a list of Spec's defect users can select  to be cleared.
Note: Clear Open Defects option must be selected together with a Target Specs 
to execute the defect clearing logic.  
Optional
Release 2510+ Rev. 1
Modeling User Guide
3-33
Chapter 3: Process Model Definitions
Field 
Definition
Type
Transaction
s
 
 
PARAMS grid Grid listing parameters used for product and resource during the Move 
transaction. For example, a product or resource that has an associated parameter 
with the same name as one listed in this grid would be required to have the 
counterpart parameter value.
 
Param
Parameter name
Optional
Param Value
Parameter value
Optional
TDA TXN M
AP grid
Grid listing object types that can be associated with a TDA document.
 
Display 
Name
The application does not use this field.
Display 
Only
Object Type
Specific modeling object type, for example, Spec, Resource, and so on.
Optional
Sequence
The sequential order the associated document is displayed on the 
TDA Documents slide-out panel.
Optional
Carrier 
Operations
Note: The application uses these fields only if Enable Carrier Tracking is selected 
on the associated Factory.
 
Load 
containers 
to carrier
Indicates whether containers processed at this spec will be automatically loaded 
to the configured carrier.
Optional
Unload 
containers 
from carrier
Indicates whether all containers will be unloaded from a configured carrier at this 
spec.
Optional
Carrier Auto 
Mode
Specifies whether an automatic load or unload is performed on the MoveIn or 
Move transaction for this spec.
Note: The application defaults this value to Move if nothing is selected.
Optional
Record 
Carrier 
Thruput
Check box to enable a carrier thruput to be recorded.
Optional
Validate 
Carrier 
Maintenanc
e 
Check box to validate the carrier's maintenance when performing load carrier.
Optional
How to Define a Spec
Follow these steps to define a Spec:
1.
Open the Spec page. The Spec page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance.
3.
Enter a name for this spec in the Spec field.
3-34
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
4.
Enter the revision of this object in the Revision field.
5.
Select the operation to associate with the spec from the Operation list.
6.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
7.
Click Save. The application saves the modeling object and displays a success message.
How to Add Data Collection Information
Follow these steps to add data collection information:
1.
Perform the "How to Define a Spec" procedure.
Or
Select an existing Spec instance.
2.
Expand the Transactions section.
3.
Click Add new row on the Data Collection Txn Map grid. A new row appears.
4.
Select a transaction from the Txn to Use field for which a Data Collection Definition is to be 
assigned.
5.
Select a Data Collection Definition to determine the group of data collection parameters 
displayed to users during transaction processing.
6.
Repeat steps 3-5 to add additional Data Collection Definition references for this spec.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Add Electronic Signature Information
Follow these steps to add electronic signature information:
1.
Perform the "How to Define a Spec" procedure.
Or
Select an existing Spec instance.
2.
Expand the Transactions section.
3.
Click Add new row on the Electronic Signature Txn Map grid. A new row appears.
4.
Select a transaction from the Transaction list.
5.
Select an electronic signature requirement from the ESig Requirement list.
6.
Optionally, select the All Txns check box.
7.
Repeat steps 3-6 to add additional electronic signature requirements for this spec.
8.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
3-35
Chapter 3: Process Model Definitions
How to Add Label Information
Follow these steps to add label information:
1.
Perform the "How to Define a Spec" procedure.
Or
Select an existing Spec instance.
2.
Expand the Transactions section.
3.
Click Add new row on the Label Txn Map grid. A new row appears.
4.
Select a transaction type from the Txn Type list.
5.
Select a printer label definition from the Printer Label Definition list.
6.
Enter a numeric value in the Label Count field.
7.
Repeat steps 3-6 to add additional label printing transactions for this spec.
8.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Add Electronic Signature Requirements for Document Attachment
Follow these steps to  add electronic signature requirements for document attachment:
1.
Perform the "How to Define a Spec" procedure.
Or
Select an existing Spec instance.
2.
Expand the Transactions section.
3.
Click Add new row on the Electronic Signature Txn Map grid. A new row appears.
4.
Select Attach Document in the Transaction field if you want to set requirements for attaching 
documents.
Or
Select Detach Document if you want to set requirements for detaching documents.
5.
Optionally, check the box in the All Txns field if you want to apply the electronic signature 
requirements to all transactions.
6.
Select the electronic signature requirement from the ESig Requirement field. Refer to "Defining 
Electronic Signature Requirements" for information.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Add a Process Timer
Follow these steps to add a process timer:
1.
Perform the "How to Define a Spec" procedure.
Or
Select an existing Spec instance.
3-36
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
2.
Expand the Transactions section.
3.
Click Add new row on the Start Timer Txn Map grid. A new row appears.
4.
Select an existing timer from the Timer field.
5.
Select either Move or Move In from the Start Txn field.
6.
Click Add new row on the End Timer Txn Map grid. A new row appears.
7.
Select an existing timer from the Timer field.
8.
Select either Move or Move In from the End Txn field.
9.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Note:
Every process timer should have a start and end timer, but there is no logic to prevent you 
from having one without the other.
How to Add a Business Rule
Follow these steps to add a business rule:
1.
Perform the "How to Define a Spec" procedure.
Or
Select an existing Spec instance.
2.
Expand the Transactions section.
3.
Click Add new row on the Business Rule Txn Map grid. A new row appears.
4.
Select a Business Rule from the  list.
5.
Select an Event from the list.
6.
Select a Transaction from the list.
7.
Repeat steps 3-6 to add additional business rules for this spec.  
8.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Set up a Container Auto Hold Requirement
Follow these steps to set up a container auto hold requirement:
1.
Perform the "How to Define a Spec" procedure.
Or
Select an existing Spec instance.
2.
Expand the Transactions section.
3.
Click Add new row on the Container Auto Hold Req Txn Map grid. A new row appears.
4.
Select a transaction type from the Txn Type list.
5.
Select a container auto hold requirement from the Container Auto Hold Requirement list.
6.
Select the effective date in the Effective From Date and Effective Thru Date field.
Release 2510+ Rev. 1
Modeling User Guide
3-37
Chapter 3: Process Model Definitions
7.
Repeat steps 3-6 to add additional container auto hold requirement for this spec.
8.
Click Save. The application displays a success message indicating the modeling object was 
updated.
3-38
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Defining Product Families
A Product Family is a group of products that share common attributes such as workflow, training 
requirements, and start quantities. Attributes defined for the product family are applied to each product 
within the family. 
Note:
Any attributes specified on the product definition override attributes specified on the product's 
associated product family definition. 
Product family groups simplify product information maintenance by defining common data for a group of 
products rather than for each product. Every product can belong to a product family, but a product can be 
assigned to only one family. You can assign a product  to a product family when defining the product. 
Refer to "Defining Products" for information on assigning a product to a product family.
A product family group is a different concept from an object group. Grouping objects such as resources 
and user codes is done for validation and reporting. Additionally, one object can belong to multiple groups 
and object groups may contain other object groups. 
Precedence Rules
These precedence rules are used for product and product family data:
•
Data defined for a product family applies to all products in the family.
•
Changes to product family data apply to all products in the family.
•
Data specified at the product level takes precedence over product family data.
When Defining a Product Family 
Product family contains the optional modeling definitions:
•
Document Set
•
Training Requirement Group
•
UOM
•
Workflow
Product Family is an optional field in the definition of Product.
When Defining Product Families for Use with Opcenter Execution Core Scheduling
Note:
The functionality described below is available only when Opcenter Execution Core Scheduling 
is installed. Refer to "Opcenter Execution Core Scheduling" for information.
The workflow associated with the ERP route must be assigned to either the manufacturing order’s product 
or the product’s product family. Refer to "Opcenter Execution Core Scheduling" for information.
Release 2510+ Rev. 1
Modeling User Guide
3-39
Chapter 3: Process Model Definitions
Assigning a Default Inventory Location to a Product Family
Note:
The functionality described below is available only when the Industry Solutions workspace is 
installed. Refer to "Industry Solutions Workspace" for information.
You can assign a default inventory location to a product family. You can also assign a default inventory 
location to a product and a factory. 
These rules apply when assigning default inventory locations:
•
The default inventory location assigned on the product takes precedence over the default 
inventory location assigned on the product family. 
•
The default inventory location assigned on the product family takes precedence over the default 
inventory location assigned on the factory. 
•
The application automatically assigns the default inventory location to a container when the 
container is moved to an operation defined as an inventory point if a default inventory location is 
defined on the product family.
Refer to "Assigning a Default Inventory Location to a Product" and "Assigning a Default Inventory Location 
to a Factory" for information.
Assigning a Scale Group on the Product Family
Note:
The functionality described below is available only when Batch Processing is installed. Refer to 
"Batch Processing" for information.
You can assign a scale group on the product family. You can also assign a scale group on the spec, 
product, and weigh issue task. 
These rules apply when assigning scale groups:
•
The scale group assigned on the product family takes precedence over a scale group assigned on 
the spec. 
•
The scale group assigned on the product takes precedence over a scale group assigned on the 
product family.
•
The scale group assigned on the weigh issue task takes precedence over the scale group assigned 
on all other objects. 
Refer to "Assigning a Scale Group on the Spec," "Assigning a Scale Group to a Component Product," and 
"When Defining Weigh Issue Tasks" for information.
Defining UOM Conversion Information on the Product Family
Note:
The functionality described below is available only when Batch Processing is installed. Refer to 
"Batch Processing" for information.
3-40
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
The UOM Conversion grid contains fields allowing you to define quantity conversion information for 
product families.  You can define:
•
A factor to convert any issued quantity of the product family from one unit of measure to 
another.
•
A rule for a converted quantity to be rounded.
•
The number of decimal places allowed for the calculated conversion quantity. The maximum 
number is 4.
These rules apply when defining UOM conversion information for product families:
•
Both the Rounding Rule and Decimal Places fields must be populated for rounding to occur.
•
Conversion information defined on the product takes precedence over conversion information 
defined on the product family. 
•
Conversion information defined on the product family takes precedence over conversion 
information defined on the UOM. 
Refer to "Defining UOM Conversion Information on the Product" and "Medical Device Workspace" for 
information. 
Product Family Page
This image shows an example of the Product Family page. 
Release 2510+ Rev. 1
Modeling User Guide
3-41
Chapter 3: Process Model Definitions
Product Family Page Field Definitions
This table defines the fields unique to the Product Family page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
Processing
Workflow
Workflow to be used when creating a product within this family. 
If specified here, workflow need not be specified for each 
product in this family unless you want to override at the product 
level.
Optional
Document Set
Associated (external) documents for products within this family. 
These documents can be used for any purpose (such as a product 
drawing or an additional product description).
Optional
Training 
Requirement Group
Training group required before a user is authorized to perform a 
specific task.
Optional
Start Quantity
Default quantity for a Start transaction for products within this 
family.
Optional
Start UOM
Unit of measure to use as a default for the Start transaction.
Optional
Sampling Plan
Sampling plan assigned to this product family. Enter a specific 
revision for the sampling plan or select the Revision of Record 
check box to use the current revision of record.
Optional
Secondary Start 
Quantity
Default second quantity for a Start transaction for products 
within this family. Used only for products that use secondary unit 
of measure tracking.
Optional
Secondary Start 
UOM
Secondary unit of measure to use for a container Start 
transaction for products that use secondary unit of measure 
tracking.
Optional
Container 
Numbering Rule
List of all the numbering rules defined in the application. Use this 
field to associate a numbering rule with the product family for 
auto numbering when starting containers.
Note: The application uses this order of precedence to determine 
the numbering rule to use when numbering rules have been 
specified for multiple modeling objects referenced by the 
container: container level, mfg order, product, product family, 
and factory.
Optional
3-42
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field 
Definition
Type
Recipe Matrix
Contains one or more recipes, each of which may be qualified by 
resource, spec, or both. This matrix is used to determine the 
resource setup recipe to use during manufacturing of products in 
this product family.
Note: This field appears only when Opcenter EX EL is installed.
Optional
Recipe Plan
Contains one or more recipes, each of which may be qualified by 
resource, spec, or both. This plan is used to determine the 
resource setup recipe to use during manufacturing of products in 
this product family.
Note: This field appears only when the Industry Solutions 
workspace is installed.
Optional
Register Container
Option that indicates whether containers must be created for 
Incoming Materials Registration (IMR) of the product. The value 
in this field determines the value placed into the 
<RegisterContainers> node of the response message to a Valor 
Product Inquiry.
Note: This field can be set on the Product. A value set on the 
product overrides the value set here.
Note: This field appears only when the Industry Solutions 
workspace is installed.
Optional
Electronics
This section appears only when Opcenter EX EL is installed.
 
Start Child Qty
Indicates whether the product will be built as a panel. 0 = Not 
Panelized; 1 = Panelized.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Start Child 
Secondary Qty
The application does not use this field.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Default Inventory 
Location
Default location to store this type of product.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Start Level
Level to use when starting containers. Sets the level for the panel 
container if the product is panelized. Sets the level for the PCB if 
the product is not panelized.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Release 2510+ Rev. 1
Modeling User Guide
3-43
Chapter 3: Process Model Definitions
Field 
Definition
Type
Start Child Level 
Sets the level for a child container or PCB of a panelized product.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Child Container 
Numbering Rule
Numbering rule to use for generating a child container name.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Start Reason
Start Reason to set on containers when started.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Start Customer
Associates the customer to this product family.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Start Owner
Default Owner when starting containers of a product in this 
product family.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Start Priority 
Priority Code that can be used to help determine production 
sequence.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Start Factory
Factory in which to start containers of this product family.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Use Production 
Client Box Mode
Selecting this option indicates that the products in the  family will 
use the BOM View for Box Products display mode of the 
Production Client page, even if an NPI job is associated to the 
product.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
3-44
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field 
Definition
Type
Inherit Exposure
Flag to control whether Material Withdrawal Date of the Issue 
Container should be inherited by the containers of the given  
product. The Target Container needs to have Inherit Exposure  
enabled in order to receive criteria from the Issue Container.  
Note: The application shows an error when material exceeds  
exposure duration during Component Issue and Component  
Replace transactions. 
Optional
Propagate Exposure 
Flag to control whether Material Withdrawal Date should be 
propagated (passed down) from containers of the given  product. 
The Issue Container need to have the Propagate  Exposure field 
enabled in order to allow exposure time to be  propagated. When 
the Issue Container has Propagate Exposure field enabled,  and 
the Target Container has the Inherit Exposure field enabled,  
Target Container will inherit the following criteria from the Issue  
Container: 
•
Material Withdrawal Date 
•
Exposure Duration (given if the Exposure Duration Time 
of the Issue Container is lower /earlier than the Target  
Container)
•
Material Total Exposure 
Note: The application notifies an error when material exceeds 
exposure duration during Component Issue and Component  
Replace transactions.
Optional
Batch Processing
Note: This section appears only when Batch Processing is 
installed. 
 
Scale Group
List of available scale groups.
Optional
Serial Numbers
This section appears only when Opcenter EX EL is installed. Refer to the 
Opcenter Execution Electronics User Guide for information.
 
Parent Serial Number 
Rule
Rule to use for generating a parent or panel serial number for a 
product within this product family.
Optional
Child Serial Number 
Rule
Rule to use for generating a child or PCB serial number for a 
product within this product family.
Optional
Serial Number 
Config
Defines what serial numbers are required for a product within 
this product family. Valid options include:
•
Both Panel and PCB
•
Panel only
•
PCB only
Optional
Release 2510+ Rev. 1
Modeling User Guide
3-45
Chapter 3: Process Model Definitions
Field 
Definition
Type
Serial Numbers per 
Container
Enables optional assignment of one or two additional serial 
numbers per container. Acceptable values:
•
2 = Primary serial number plus one additional  
•
3 = Primary serial number plus two additional  
Note: This field can be configured on Mfg Order, Product, and 
Product Family. Values set on Mfg Order and Product override a 
value set here.
Optional
Unique Serial 
Numbers
Check box indicating whether serial numbers must be unique 
within this product family.
Optional
Serial Number 
Generation
Defines the possible methods for serial number generation for 
products within this product family.
•
System: Electronics Suite logic will generate the serial 
numbers based on configured values.
•
External: Serial Number values are defined outside of ES 
processing.
Optional
Material Queues
Note: This section appears only when the Industry Solutions 
workspace is installed.
 
Default Inventory 
Location
Default inventory location where this product family is stored.
Optional
UOM Conversion
Note: This section appears only when Batch Processing is 
installed. 
 
UOM Conversion 
grid
Grid displaying conversion factors for the product.
Display 
Only
From UOM
Unit of measure from which this instance is being converted.
Required
To UOM
Unit of measure to which this instance is being converted.
Required
Conversion 
Factor
Factor for converting this instance.
Required
Rounding 
Rule
Rule for rounding the calculated conversion quantity. Options 
include the following:
•
Round Down
•
Round to Nearest
•
Round Up
Optional
Decimal 
Places
Number of decimal places included in the calculated conversion 
quantity. The maximum number is 4.
Optional
Cost
Standard Cost
Standard cost per unit for product within this family.
Optional
Current Cost
Current cost per unit for product within this family.
Optional
3-46
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
How to Define a Product Family
Follow these steps to define a Product Family:
1.
Open the Product Family page. The Product Family page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for the product family in the Product Family field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
3-47
Chapter 3: Process Model Definitions
Defining Products
Products are the materials produced in a factory or by outside suppliers for a factory. Products can be end-
items, subassemblies, and components. Each product definition contains two basic types of information: 
data that describes the product and data that provides default processing information used when a new 
container of the product is started. 
Providing the following data in the product definition (if your business rules so require) eliminates the 
need to enter them every time a container of this product is started:
•
Workflow
•
Start Quantity
•
Secondary Start Quantity
•
Unit of Measure
•
Secondary Unit of Measure
•
Customer
•
Scale Group
Note:
The Scale Group field appears only when Batch Processing is installed. Refer to "Batch 
Processing" for information.
This information, with the exception of Customer, overrides anything that may have already been set at 
the product family level. (Customer is not set at the product family level.)
Additionally, you can assign custom, dynamic attributes to a product and the application will assign these 
user-defined attributes when you start a container. Storing information on the container itself prevents 
you and other users from having to search through the container’s history for the information. 
The Portal user can create an event against a product. 
Assigning a Product to a Product Family
A product can belong to a product family, which is used to group products that share common attributes 
such as workflow, training requirements, and start quantities. Product families simplify product 
information maintenance by defining common data for a group of products.  Attributes defined for the 
product family are applied to each product within the family.
The product may inherit the following attributes from the assigned product family: 
•
Workflow 
•
Document Set 
•
Start Quantity (and Start Secondary Quantity)
•
Start UOM (and Start Secondary UOM)
•
Standard Cost 
•
Current Cost 
3-48
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Selecting a value for one of these attributes on the Product page overrides the value specified on the 
associated product family definition.
Understanding User-Defined Attributes
Refer to  "Understanding User-Defined Attributes" for information on user-defined attributes.
Assigning User-Defined Attributes on a Container Start
Refer to "Assigning User-Defined Attributes on a Container Start" for information on assigning user-defined 
attributes.
When Defining a Product
Product contains the required modeling definition Product Type and the optional modeling definitions: 
•
Bill of Process (BOP)
•
Bill of Materials (BOM)
•
Customer
•
Document Set
•
ERP BOM
•
ERP Route 
•
Numbering Rule
•
Product Family
•
Sampling Plan
•
Training Requirement Group
•
UOM
•
Workflow
•
Vendor
Product is:
•
An optional field in the definition of Mfg Order and Sales Order.
•
An optional field in the transactions Start, Container Maintenance, and Resource Setup. 
Note:
A Product definition can have related WIP Messages if it is associated with a field from a con-
tainer definition. Refer to the  Opcenter Execution Medical Device and Diagnostics Shop Floor 
User Guide or the Opcenter Execution Core Shop Floor User Guide for  information. 
When Defining Products for Use with Opcenter Execution Core Scheduling
Note:
The functionality described below is available only when Opcenter Execution Core Scheduling 
is installed. Refer to "Opcenter Execution Core Scheduling" for information.
Product is a required field on the Mfg Order modeling object when defining manufacturing orders for 
Opcenter Execution Core Scheduling. You must define a product before you define a manufacturing order.
The workflow associated with the ERP route must be assigned to either the manufacturing order’s product 
or the product’s product family. Refer to "When Defining Product Families for Use with Opcenter Execution 
Core Scheduling" for information.
Release 2510+ Rev. 1
Modeling User Guide
3-49
Chapter 3: Process Model Definitions
Expiration Date Calculation on the Product Page
Note:
The functionality described below is available only when Medical Device is installed. Refer to 
"Medical Device Workspace" for information.
You can use the Product page to define the fields required for automatic calculation of an expiration date 
for a container when a predefined transaction is successful at the identified spec. These fields are as 
follows:
•
Expiration Date Transaction
•
Expiration Date Spec
•
Expiration Period Units
•
Expiration Period
The expiration date information on the product takes precedence over the expiration date information on 
the spec.
If the container has a defined expiration date that is earlier than the calculated date, the expiration date is 
not updated unless the Always Override Expiration Date check box is selected.
The expiration date adjusts to the last day of the month if the Expiration Period Units field is set to Months 
and the expiration date calculation results in an invalid date. For example, if the current date is January 31 
and the expiration period is three months, the calculated expiration date is April 31. The date adjusts to 
April 30.
Manufacturing Date Calculation on the Product Page
Note:
The functionality described below is available only when Medical Device is installed. Refer to 
"Medical Device Workspace" for information.
You can use the Product page to define the fields required for automatic calculation of a container's 
manufacturing date when a predefined transaction is successful at the identified spec. These fields are as 
follows:
•
Manufacturing Date Spec
•
Manufacturing Date Transaction
The manufacturing date information on the product takes precedence over the manufacturing date 
information on the spec.
The current date and time is assigned to the container during processing at the successful completion of 
the specified transaction at the indicated spec.
3-50
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Defining a UDI on the Product Page
Note:
The functionality described below is available only when Medical Device is installed. Refer to 
"Medical Device Workspace" for information.
Opcenter EX MDD and Opcenter EX CR's UDI functionality allows you to define the following for the 
product:
•
Device identifiers
•
Production identifier
•
UDI expression
•
UDI transaction
You can assign more than one device identifier to a product. During production, the user can select a 
specific device identifier to assign to the container if there is more than one defined for a product. If there 
is only one device identifier defined on the product, then the application automatically assigns this value 
to the container.
Assigning a Default Inventory Location to a Product
Note:
The functionality described below is available only when the Industry Solutions workspace is 
installed. Refer to "Industry Solutions Workspace" for information.
You can assign a default inventory location  to a product. You can also assign a default inventory location 
to a product family and a factory. 
These rules apply when assigning default inventory locations:
•
The default inventory location assigned on the product takes precedence over the default 
inventory location assigned on the product family. 
•
The default inventory location assigned on the product family takes precedence over the default 
inventory location assigned on the factory. 
•
The application automatically assigns the default inventory location to a container when the 
container is moved to an operation defined as an inventory point if a default inventory location is 
defined on the product.
Refer to "Assigning a Default Inventory Location to a Product Family" and "Assigning a Default Inventory 
Location to a Factory" for information.
Assigning a Scale Group to a Component Product
Note:
The functionality described below is available only when Batch Processing is installed. Refer to 
"Batch Processing" for information.
You can assign a scale group using the Scale Group field to define the scales allowed to weigh component 
products. You can also assign a scale group to a spec, product family, and weigh issue task. 
Release 2510+ Rev. 1
Modeling User Guide
3-51
Chapter 3: Process Model Definitions
These rules apply when assigning scale groups:
•
The scale group assigned on the product family takes precedence over a scale group assigned on 
the spec. 
•
The scale group assigned on the product takes precedence over a scale group assigned on the 
product family. 
•
The scale group assigned on the weigh issue task takes precedence over the scale group assigned 
on all other objects. 
Refer to "Assigning a Scale Group on the Spec," "Assigning a Scale Group on the Product Family," and 
"When Defining Weigh Issue Tasks" for information.
Defining Expressions to Adjust Component Quantities on the Product
Note:
The functionality described below is available only when Batch Processing is installed. Refer to 
"Batch Processing" for information.
You can adjust component quantities during batch processing by defining expressions on the product. For 
example, assume the amount of a component product required for a batch is dependent on potency. The 
potency of the product is not set, but varies by component container. When a component container is 
created in Opcenter EX MDD or Opcenter EX CR, its potency is recorded based on incoming inspection. You 
can define expressions that will calculate the required quantity and the minimum and maximum 
tolerances at processing time to account for potency differences between component containers. You can 
use the expressions on the product to adjust the following values:
•
The component quantity required for the batch
•
The minimum allowed component quantity for the batch
•
The maximum allowed component quantity for the batch
You can also define these expressions on a weigh issue task on the Task List. The expressions defined on a 
weigh issue task take precedence over expressions defined on a product. Refer to "When Defining Weigh 
Issue Tasks" for information.
Use the  Unified Expression syntax when defining an expression. Expressions can contain a maximum of 
4000 characters and may include:
•
Variables; for example, (?InQty)
•
User-defined constants; for example, Constant::Pi
Refer to the Opcenter Execution Medical Device and Diagnostics Designer User Guide or the Opcenter 
Execution Core Designer User Guide for information on the  Unified Expression syntax.
3-52
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Defining Finished Products as Batch-Controlled Products
Note:
The functionality described below is available only when Batch Processing is installed. Refer to 
"Batch Processing" for information.
The Batch Controlled check box enables you to identify a finished product as a batch product. Selecting the 
Batch Controlled check box indicates the material quantity for each component in the product's BOM is the 
total quantity required for a batch of the finished product. The component material quantity is not the 
quantity required per unit.
Defining UOM Conversion Information on the Product
Note:
The functionality described below is available only when Batch Processing is installed. Refer to 
"Batch Processing" for information.
The UOM Conversion grid contains fields allowing you to define quantity conversion information for 
products. You can define:
•
A factor to convert any issued quantity of the product  from one unit of measure to another.
•
A rule for a converted quantity to be rounded.
•
The number of decimal places allowed for the calculated conversion quantity. The maximum 
number is 4.
These rules apply when defining UOM conversion information for products:
•
Both the Rounding Rule and Decimal Places fields must be populated for rounding to occur.
•
Conversion information defined on the product takes precedence over conversion information 
defined on the product family. 
•
Conversion information defined on the product family takes precedence over conversion 
information defined on the UOM. 
Refer to "Defining UOM Conversion Information on the Product Family" and "Defining Units of Measure" for 
information.  
Release 2510+ Rev. 1
Modeling User Guide
3-53
Chapter 3: Process Model Definitions
Product Page
This image shows an example of the Product page.
Product Page Field Definitions
This table describes the fields unique to the Product page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
General
Engineering Change 
Order
Engineering change order assigned to this revision. You can 
enter a maximum of 30 characters.
Optional
3-54
Modeling User Guide
Release 2510+ Rev. 1
Chapter 3: Process Model Definitions
Field 
Definition
Type
Product Type
User code from the ProductType object group. Product types 
are used to differentiate between different categories of 
products as defined by your business. Examples of product 
types include:
•
WIP - Work In Process
•
FG - Finished Goods
•
RM - Raw Materials
Required
Product Family
Product family to which the product belongs.
Optional
Semiconductor Details
Setup Access
Access control to this instance. Users must have the same 
access level to modify this instance.
Note: This field appears only when Opcenter Execution 
Semiconductor is installed. Refer to the Opcenter Execution 
Semiconductor Modeling Guide for information.
Optional
Product Line
Product line to which the product belongs.
Note: This field appears only when Opcenter Execution 
Semiconductor is installed. Refer to the Opcenter Execution 
Semiconductor Modeling Guide for information.
Required
Is Available (For Start 
and Schedule)
Check box indicating the product is available for start and 
schedule.
Note: This field appears only when Opcenter Execution 
Semiconductor is installed. Refer to the Opcenter Execution 
Semiconductor Modeling Guide for information.
Optional
Effective Start Date
Date at which any processing can occur. If you have selected a 
date, the application prevents any attempt to process a 
container of the product before the selected date in any shop 
floor transaction other than Container Maintenance.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Effective End Date
Date at which any processing can no longer occur. If you have 
selected a date, the application prevents any attempt to 
process a container of the product after the selected date in 
any shopfloor transaction other than Container Maintenance.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Release 2510+ Rev. 1
Modeling User Guide
3-55
Chapter 3: Process Model Definitions
Field 
Definition
Type
ERP Product Family
Associates the product with a product family in the ERP 
system. 
Note: You can use ERP Product Family for additional grouping 
of products for reporting purposes.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Material Category
User defined category for the product. 
Note: You can use Material Category for additional grouping 
of products for reporting purposes.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Validate Bulk UID
Whether a Unique Identifier is required for containers issued 
at bulk level. Options available are:
•
No
•
Not Set
•
Yes
Note: This field only applies to Bulk issue types.
Note: This field appears only when Opcenter Execution 
Electronics is installed. Refer to the Opcenter Execution 
Electronics User Guide for information.
Optional
Material Queues
Note: This section appears only when the Industry Solutions 
workspace is installed.
 
Default Inventory 
Location
Default inventory location where this product is stored.
Optional
Processing
Workflow
Workflow (sequence of steps) used to manufacture this 
product. Each step in a workflow references either a 
specification or another workflow (subworkflow) that 
contains the rules and instructions for processing the product 
at that step.
Optional
Document Set
Document set (collection of one or more documents) 
associated with this product. Document sets are referenced by 
other modeling entities and provide extended information 
such as drawings, scanned images, recipes, and procedures.
Optional
Training Requirement 
Group
Training group required before a user is authorized to perform 
a specific task associated with this product.
Optional
ERP Route
ERP route with which this ERP BOM is associated.
Optional
3-56
Modeling User Guide
Release 2510+ Rev. 1
