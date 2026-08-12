Chapter 6: Electronic Procedures
Field
Definition
Type
Workstation
List of previously defined resources  you can associate with this 
task list. Shop floor operators use the workstation you select to 
perform tasks.
Optional
Workstation Group
List of previously defined resource groups you can associate with 
this task list. Shop floor operators use workstations in the group 
you select to perform tasks.
Optional
Batch Processing
Note: This section appears only when Batch Processing is 
installed.
 
Intermediate Batch 
Qty
Expression used to calculate the quantity in the intermediate 
batch.
Optional
Intermediate Batch 
UOM
Unit of measure for the intermediate batch.
Optional
Task Details
Tasks grid
Grid listing tasks added to the list. You must add a minimum of 
one to the task list.
Display 
Only
Task
Unique name for the task. 
Display 
Only
Instruction 
Type
Instruction type options include the following:
•
Acknowledgment - An operator is required to mark a task 
as complete.
•
Data Collection - An operator is required to enter 
parametric data values for either a standard Data 
Collection or a Data Point Collection.
•
Pass/Fail - An operator is required to provide pass or fail 
results for a task.
Instruction type is only available if you select Instruction as the 
Task Item Type.
Display 
Only
Min Iterations
Minimum number of times the task can be executed.
Display 
Only
Max Iterations Maximum number of times the task can be executed.
Display 
Only
Task Type
Type of task (Start Process, Regular Task, or End Process). The 
Start Process task is not available for a transaction task.
Display 
Only
Electronic 
Signature 
Requirement
Any electronic signature required to be collected for the task.
Display 
Only
Training 
Requirement 
Group
Collection of individual training requirements and training 
requirement groups associated with the task list.
Display 
Only
Release 2510+ Rev. 1
Modeling User Guide
6-45
Chapter 6: Electronic Procedures
Field
Definition
Type
Start Timers
Names of the start timers associated with the task. Multiple 
timers are displayed as a comma separated list.
Display 
Only
End Timers
Names of the end timers associated with the task. Multiple timers 
are displayed as a comma separated list.
Display 
Only
Task Materials
List of materials to be consumed when executing the task.
Note: If the task is a Transaction Task and the ComponentIssue_
VPR2, ComponentIssueAdvancedVP or ComponentIssueVP 
transaction pages are selected then the displayed material list will 
be filtered using the Task Materials so that only material items 
that match an item in the Task Materials will be displayed.
 
Product
Product to be issued.
Display 
Only
Qty
Required quantity.
Display 
Only
Reference 
Designator
The Reference Designator of the Material Item to match.
Display 
Only
Description
Description of the component product.
Display 
Only
Instruction Task Details Pop-Up
The Instruction Task Details pop-up appears when you either:
•
Click Add new row on the Tasks grid and select Instruction from the Select Task Item Type menu.
Or
•
Select an instruction task in the Tasks grid and click Edit selected row. 
6-46
Modeling User Guide
Release 2510+ Rev. 1
Chapter 6: Electronic Procedures
This image shows an example of the Instruction Task Details pop-up.
 
Instruction Task Details Pop-Up Field Definitions
This table defines the fields on the Instruction Task Details pop-up.
Field
Definition
Type
Task
Unique name for the task. You can enter a maximum of 30 characters.
Required
Release 2510+ Rev. 1
Modeling User Guide
6-47
Chapter 6: Electronic Procedures
Field
Definition
Type
Instruction
Steps or additional information for performing the task. You can use the 
formatting features to apply special emphasis to the text if you are in 
Design mode. The application displays this information and any special 
formatting to the operator.
Optional
Task Type
Task indicating the stage of processing at the work cell or workstation. 
Options include the following:
•
End Process Task - is required to denote the end of a process in a 
work cell or at a workstation.
•
Regular Task - can occur in between a Start Process task and an 
End Process task.
•
Start Process Task - is required to denote the beginning of 
processing in a work cell or at a workstation.
Note: The Start Process task option is not available for transaction tasks.
Required
Instruction 
Type
Setting indicating work required by the operator for the task. Options 
include the following:
•
Acknowledgment - An operator is required to mark a task as 
complete.
•
Data Collection - An operator is required to enter parametric data 
values for either a standard Data Collection or a Data Point 
Collection.
•
Pass/Fail - An operator is required to provide pass or fail results for 
a task.
Required
Min Iterations
Minimum number of times the task can be executed against the spec for 
the selected container. If a container is returned to a step, this field count 
is reset. A value of zero means that a task is optional. Start Process and 
End Process tasks must have a value greater than zero.
Required
Max Iterations Maximum number of times the task can be executed against the spec for 
the selected container. If a container is returned to a step, this field count 
is reset.
Optional
Document Set
Collection of one or more documents such as drawings and scanned 
images. For example, a Document set may contain instructions for setting 
up a particular piece of equipment.
Optional
Advance to 
next task on 
Min Iterations 
completion
Check box allowing the application to display the next task automatically 
after the minimum number of iterations for the current task have been 
completed. This check box is selected by default.
Optional
Electronic 
Signature 
Requirement
Electronic signature requirement associated with the task. Associating an 
electronic signature requirement with a task requires an operator to 
provide an electronic signature before the task can be completed.
Note: This field is not available for transaction tasks.
Optional
Training 
Requirement 
Group
Training requirement group associated with the task. A training 
requirement group is a collection of individual training requirements that 
ensure the operator is qualified to execute the task.
Optional
6-48
Modeling User Guide
Release 2510+ Rev. 1
Chapter 6: Electronic Procedures
Field
Definition
Type
Start Timers 
Grid
List of timers started by this task.
Optional
End Timers 
Grid
List of timers ended by this task.
Optional
Prerequisite 
Tasks grid
List of tasks in the task item list that must be completed before executing 
this task.
Optional
Data 
Collection Def
Data collection definition associated with the task. A data collection 
definition, defined in Modeling, references a parametric data definition 
that contains a set of data collection parameters. These parameters are 
presented to users during transaction processing.
Note: The Data Collection Def is made a required field when Data 
Collection is the Instruction Type selected. 
Note: The data collection fields appear on the EProcedure shop floor page 
only if you select a data collection definition here and select Data 
Collection in the instruction Type field.
Optional
Allocated 
Time
Defines the amount of time designated to complete the task. The time 
format is  [d]hh:mm:ss. 
When allocated time is defined, the task time will start at the allocated 
time value and count downward to 0. 
Setting the allocated time is optional. If allocated time is not specified, the 
timer will only count the task execution time. 
Refer to Mendix UIs: Operator-Based Modules for more information about 
task timers.
Note: The display of the Task Time, including how the Allocated Time for 
the task is used, is only available on the Mendix E-Procedure page.
Optional
Computation Task Details Pop-Up
The Computation Task Details pop-up appears when you either:
•
Click Add new row on the Tasks grid and select Computation from the Select Task Item Type 
menu.
Or
•
Select a computation task in the Tasks grid and click Edit selected row. 
The Computation Task Details  pop-up differs slightly from the  Instruction Task Details pop-up.
Release 2510+ Rev. 1
Modeling User Guide
6-49
Chapter 6: Electronic Procedures
This image shows an example of the Computation Task Details pop-up.
Computation Task Details Pop-Up Field Definitions
This table defines the fields unique to the Computation Task Details  pop-up. Refer to the field definitions 
table for the Instruction Task Details pop-up for a description of the other fields.
Field
Definition
Type
User Data Collection 
Def
User data collection definition associated with the task.  A data 
collection definition defines data points in the production process 
where data can or must be collected. These parameters are 
presented to users during transaction processing. (User data 
collection definitions are defined in Modeling.)
Optional
6-50
Modeling User Guide
Release 2510+ Rev. 1
Chapter 6: Electronic Procedures
Field
Definition
Type
Computation
Computation you can map to the user data collection data points. Required
Computation Param 
Map grid
List of data points and computation param specs associated with 
the task.
Optional
Data Point
Data point to map the Computation variable displayed in the 
adjacent column to the data point. You must select a User 
Collection Data Def before this  list is populated.
Required
Computation 
Param Spec
Computation variables associated with the Computation  you 
selected are displayed in the grid and must be associated with a 
User Data Collection data point in order to create the 
Computational Task.
Required
Transaction Task Details Pop-Up
The Transaction Task Details pop-up appears when you either:
•
Click Add new row on the Tasks grid and select Transaction from the Select Task Item Type menu.
Or
•
Select a transaction task in the Tasks grid and click Edit selected row. 
Release 2510+ Rev. 1
Modeling User Guide
6-51
Chapter 6: Electronic Procedures
This image shows an example of the Transaction Task Details pop-up.
Transaction Task Details Pop-Up Field Definitions
This table defines the field that is unique to the Transaction Task Details pop-up. Refer to the field 
definitions table for the Instruction Task Details pop-up for a description of the other fields.
Field
Definition
Type
Transaction Page
Name of the page on which you want to perform the task.
Required
6-52
Modeling User Guide
Release 2510+ Rev. 1
Chapter 6: Electronic Procedures
Weigh Issue Task Details Pop-Up
Note:
The functionality described below is available only when Batch Processing is installed. Refer to 
"Batch Processing" for information.
The Weigh Issue Task Details pop-up appears when you either:
•
Click Add new row on the Tasks grid and select Weigh Issue from the Select Task Item Type menu.
Or
•
Select a weigh issue task in the Tasks grid and click Edit selected row. 
Release 2510+ Rev. 1
Modeling User Guide
6-53
Chapter 6: Electronic Procedures
This image shows an example of the Weigh Issue Task Details pop-up.
6-54
Modeling User Guide
Release 2510+ Rev. 1
Chapter 6: Electronic Procedures
Weigh Issue Task Details Pop-Up Field Definitions
This table defines the fields that are unique to the Weigh Issue Task Details pop-up. Refer to the field 
definitions table for the Instruction Task Details pop-up for a description of the other fields.
Note:
This pop-up appears only when Batch Processing is installed. Refer to "Batch Processing" for 
information.
Field
Definition
Type
Component Product Info
Product
Component product to be issued to the batch.
Note: The associated field contains the revision number of the selected 
product. The revision is the current revision of record if the check box is 
selected.
Required
Match By 
Product Name
Check box indicating the product will be matched by name only. 
Revisions will be ignored.
Optional
Expressions 
Depend on 
From Container
Check box indicating the expressions for the Target, Minimum, and 
Maximum quantity will not be calculated until the user has entered a 
From Container.
Note: This check box only applies to Bulk issue types.
Optional
Decimal Scale
Number of decimal places required for this data point. Valid values are 
integers 0 through 9. The maximum number of decimal places allowed 
is nine.
For example, enter 0 to require the value entered to be a whole number 
with no decimal places. Enter 1 to require one decimal place. Enter 2 to 
require two decimal places. 
Optional
Quantity 
Required 
Expression
Expression used to calculate the component quantity required for the 
batch.
Optional
Minimum 
Allowed 
Quantity 
Expression
Expression used to calculate the minimum acceptable component 
quantity for the batch.
Optional
Maximum 
Allowed 
Quantity 
Expression
Expression used to calculate the maximum acceptable component 
quantity for the batch.
Optional
Weighing Rules
Scale Group
Scale group containing the scales allowed to weigh the component 
product.
Optional
Release 2510+ Rev. 1
Modeling User Guide
6-55
Chapter 6: Electronic Procedures
Field
Definition
Type
Manual 
Reading Only
Check box indicating the issued quantity field can accept manual entries.
Note: Selecting this check box hides the scale-related items on the 
EProcedure page.
Note: The Allow Manual Weigh Override check box cannot be selected 
when this check box is selected.
Optional
Allow Manual 
Weigh Override
Check box indicating the user can enter the scale weight value manually 
when issuing the component product.
Note: The Manual Reading Only check box cannot be selected when this 
check box is selected.
Optional
Manual Weigh 
Override 
Esignature
List of electronic signature requirements indicating that manual 
weighing requires an electronic signature and the requirement to use.
Optional
Qty Additive
Check box indicating the batch container’s quantity must increase by the 
raw material quantity issued.
Note: The application returns an error if the UOM of the component 
material container does not match the UOM of the batch container.
Optional
Material From 
Same 
Container/Lot
Check box indicating the application validates that multiple issues of the 
same material are from the same container or lot.
Optional
Allow 
Tolerance 
Override
Check box indicating the task passes when the issued weight is not 
within the minimum and maximum weight allowances defined for the 
component product.
Optional
Tolerance 
Override 
Esignature
List of electronic signature requirements indicating the tolerance 
override requires an electronic signature and the requirement to use.
Note: This field is enabled when the Allow Tolerance Override check box 
is selected.
Optional
How to Define a Task List
Follow these steps to define a Task List:
1.
Open the Task List page. The Task List page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this task list in the Task List field.
4.
Enter the revision of this task list in the Revision field.
5.
Select an Execution Mode from the list.
6.
Add at least one task to the Tasks grid using the appropriate procedures below:
•
"How to Add an Instruction Task to a Task List"
•
"How to Add a Computation Task to a Task List"
•
"How to Add a Transaction Task to a Task List"
6-56
Modeling User Guide
Release 2510+ Rev. 1
Chapter 6: Electronic Procedures
7.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
8.
Click Save. The application saves the modeling object and displays a success message.
How to Add an Instruction Task to a Task List
Follow these steps to add instruction tasks to a Task List:
1.
Perform the "How to Define a Task List" procedure.
Or 
Select an existing Task List instance.
2.
Expand the Task Details section.
3.
Click Add new row on the Tasks grid. The  Select Task Item Type menu appears.
4.
Select Instruction. The Instruction Task Details pop-up appears.
5.
Enter a name for the task in the Task field.
6.
Select a Task Type from the list.
7.
Select a Instruction Type from the list.
8.
Enter a number in the Min Iterations field to indicate the minimum number of times the task can 
be executed.
9.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
10.
Click OK. The pop-up closes and the task displays in the Tasks grid. 
11.
Click Save. The application saves the modeling object and displays a success message.
How to Add a Computation Task to a Task List
Follow these steps to add a computation task to a Task List:
1.
Perform the "How to Define a Task List" procedure.
Or 
Select an existing Task List instance.
2.
Expand the Task Details section. 
3.
Click Add new row on the Tasks grid. The  Select Task Item Type menu appears.
4.
Select Computation. The Computation Task Details pop-up appears.
5.
Enter a name for the task in the Task field.
6.
Select a Task Type from the list.
7.
Enter a number in the Min Iterations field to indicate the minimum number of times the task can 
be executed.
8.
Select a User Data Collection Def from the list.
Release 2510+ Rev. 1
Modeling User Guide
6-57
Chapter 6: Electronic Procedures
9.
Select a Computation from the list. The  input variables defined for the computation selected are 
displayed.
10.
Map each variable to the appropriate data point by selecting the data point from the Data Point  
lists in the grid. You must expand the User Data Collection to see the data points.
11.
Select a revision of a Computation Param Spec.
12.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
13.
Click OK. The  pop-up closes and the task displays in the Tasks grid.
14.
Click Save. The application saves the modeling object and displays a success message.
How to Add a Transaction Task to a Task List
Follow these steps to add a transaction task to a Task List:
1.
Perform the "How to Define a Task List" procedure.
Or 
Select an existing Task List instance.
2.
Expand the Task Details section. 
3.
Click Add new row on the Tasks grid. The  Select Task Item Type menu appears.
4.
Select Transaction. The Transaction Task Details pop-up appears.
5.
Enter a name for the task in the Task field.
6.
Select a Task Type from the list.
7.
Enter a number in the Min Iterations field to indicate the minimum number of times the task can 
be executed.
8.
Select a Transaction Page from the list.
9.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
10.
Click OK. The  pop-up closes and the task displays the Tasks grid.
11.
Click Save. The application saves the modeling object and displays a success message.
How to Format Existing Instructions for a Task List or Tasks
Follow these steps to format existing instructions for a Task List or tasks:
1.
Access the Task List page or one of the Task Detail pop-ups using one of these procedures.
If you want to format instructions 
on the . . .
Then use the . . .
Task List page
a.
"How to Define a Task List" procedure.
b.
Go to step 2.
6-58
Modeling User Guide
Release 2510+ Rev. 1
Chapter 6: Electronic Procedures
If you want to format instructions 
on the . . .
Then use the . . .
Instruction Task Details pop-up
a.
"How to Add an Instruction Task to a 
Task List" procedure.
b.
Go to step 2.
Computation Task Details pop-up
a.
"How to Add a Computation Task to a 
Task List" procedure.
b.
Go to step 2.
Transaction Task Details pop-up
a.
"How to Add a Transaction Task to a 
Task List" procedure.
b.
Go to step 2.
2.
Highlight the text in the Instruction field.
3.
Select one or more formatting attributes to apply to the text. Each attribute is applied as soon as 
you click or select it.
4.
Click OK to save the formatted instructions and close the pop-up, if you opened one.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Format New Instructions for a Task List or Tasks
Follow these steps to format new instructions:
1.
Access the Task List page or one of the Task Detail pop-ups using one of these procedures.
If you want to format instructions 
on the . . .
Then use the . . .
Task List page
a.
"How to Define a Task List" procedure.
b.
Go to step 2.
Instruction Task Details pop-up
a.
"How to Add an Instruction Task to a 
Task List" procedure.
b.
Go to step 2.
Computation Task Details pop-up
a.
"How to Add a Computation Task to a 
Task List" procedure.
b.
Go to step 2.
Transaction Task Details pop-up
a.
"How to Add a Transaction Task to a 
Task List" procedure.
b.
Go to step 2.
2.
Select one or more formatting attributes in the Instruction field to apply to the text.
For example, if you want to enter text that is blue and bold, click Select text color to select blue 
text, and then click Bold.
Release 2510+ Rev. 1
Modeling User Guide
6-59
Chapter 6: Electronic Procedures
3.
Enter the instructions. The  formatting attributes you selected are applied to the new text.
4.
Click OK to save the formatted instructions and close the pop-up, if you opened one.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Insert Images for a Task List or Tasks
Follow these steps to insert images for a task list or tasks:
1.
Access the Task List page or one of the Task Detail pop-ups using one of these procedures.
If you want to format instructions on the . . 
.
Then use the . . .
Task List page
a.
"How to Define a Task List" 
procedure.
b.
Go to step 2.
Instruction Task Details pop-up
a.
"How to Add an Instruction 
Task to a Task List" 
procedure.
b.
Go to step 2.
Computation Task Details pop-up
a.
"How to Add a Computation 
Task to a Task List" 
procedure.
b.
Go to step 2.
Transaction Task Details pop-up
a.
"How to Add a Transaction 
Task to a Task List" 
procedure.
b.
Go to step 2.
2.
Place your cursor where you want the image to appear in the Instruction field and click the 
Insert/edit image button. The Insert/edit image pop-up appears.
3.
Enter a relative or absolute URL for an image in the Source field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click OK. The Insert/edit image pop-up closes and the image appears in the Instruction field.
6.
Repeat steps 2-5 to add additional images.
7.
Click OK to save the instructions and close the pop-up, if you opened one.
8.
Click Save. The application displays a success message indicating the modeling object was 
updated.
6-60
Modeling User Guide
Release 2510+ Rev. 1
Chapter 6: Electronic Procedures
Defining Electronic Procedures
An Electronic Procedure (EProcedure) is a revisionable object that enables you to assign a collection of 
tasks to a Specification (Spec).
When Defining Electronic Procedures
Make sure you have defined one or more task lists before defining an electronic procedure. The 
application requires you to assign at least one task list to an electronic procedure. 
You cannot use invalid characters in the object name. For example, you cannot use an apostrophe.
Note:
Refer to  the Opcenter Execution Medical Device and Diagnostics Designer User Guide or the 
Opcenter Execution Core Designer User Guide for  information. 
Electronic Procedure is an optional field in these  definitions: Bill of Process and Spec.
Electronic Procedure Page
This image shows an example of the Electronic Procedure page.
Release 2510+ Rev. 1
Modeling User Guide
6-61
Chapter 6: Electronic Procedures
Electronic Procedure Page Field Definitions
This table defines the fields unique to the Electronic Procedure page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
General
Engineering 
Change Order
Engineering change order assigned to this revision. You can enter a 
maximum of 30 characters.
Optional
Details
Execution 
Mode
Setting that indicates whether the application executes the task lists in 
order (Sequential) or in any order (Non Sequential). The default is 
Sequential.
Required
Task Lists grid
Grid that contains task lists that belong to this electronic procedure. 
Required
How to Define an Electronic Procedure
Follow these steps to define an Electronic Procedure:
1.
Open the Electronic Procedure page. The Electronic Procedure page is displayed within the 
Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for the electronic procedure in the Electronic Procedure field.
4.
Enter  the revision of this electronic procedure in the Revision field.
5.
Select an Execution Mode from the list. 
6.
Add one or more task lists to the Task Lists grid using the "How to Add a Task List to the Electronic 
Procedure" procedure.
7.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
8.
Click Save. The application saves the modeling object and displays a success message.
How to Add a Task List to the Electronic Procedure
Follow these steps to add a task list to an Electronic Procedure:
1.
Perform the "How to Define an Electronic Procedure" procedure.
Or 
Select an existing Electronic Procedure instance.
2.
Click Add new row in the Task Lists grid. A new row appears.
3.
Click in the field to display a  list of task lists.
4.
Select the task list to associate with this electronic procedure.
5.
Repeat steps 2-4 to add additional task lists.
6-62
Modeling User Guide
Release 2510+ Rev. 1
Chapter 6: Electronic Procedures
6.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
6-63
Chapter 6: Electronic Procedures
Assigning a Resource Group and an Electronic Procedure 
to a Spec
A Spec (Specification) defines the activities carried out at a step and is referenced by a step within a 
workflow. Many workflow steps can use the same spec.
Note:
Specs reference many other modeling components including Operation and Setup. Specs also 
include detailed scheduling and processing parameter information. 
Optionally, you can assign a resource group and an electronic procedure to a spec. Assigning a resource 
group to a spec determines the resources available for selection when moving a container out of a spec. 
Assigning an electronic procedure to a spec determines the tasks that must be completed before the 
container can be moved out of the spec.
A specification can reference only one resource group and one electronic procedure at a time. However, 
an electronic procedure can reference a series of task lists that includes multiple tasks.
Refer to "Defining Specs" for information on specifications.
How to Assign a Resource Group to a Spec
Follow these steps to assign a Resource Group to a specification:
1.
Open the Spec page. The Spec page appears within the Modeling page.
2.
Perform the "How to Define a Spec" procedure.
Or 
Select an existing Spec instance. The Spec page displays information for the selected spe-
cification.
3.
Select a workstation or work cell group from the Resource Group field.
4.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Assign an Electronic Procedure to a Spec
Follow these steps to assign an Electronic Procedure to a Specification:
1.
Open the Spec page. The Spec page appears within the Modeling page.
2.
Perform the "How to Define a Spec" procedure.
Or 
Select an existing specification. The Spec page displays information for the selected specification.
3.
Select an electronic procedure or a specific revision on an electronic procedure from the 
Electronic Procedure field.
4.
Click Save. The application displays a success message indicating the modeling object was 
updated.
6-64
Modeling User Guide
Release 2510+ Rev. 1
Chapter 7: WIP Messages
Introduction
Opcenter EX MDD and Opcenter EX CR provide the ability to display messages associated with specific 
container attributes and with any service. The Work In Progress (WIP) message capability enforces 
processing and sends special notifications when a container of material reaches a specific processing 
point.
For example, you might create a WIP message that displays during a Move In transaction to provide 
important information to the operator before he or she processes the container.
WIP messages can be used to:
•
Display a reminder or special processing instructions to the person doing the work.
•
Place a container on hold when it reaches a specific point.
•
Require an operator or supervisor to acknowledge that the special instructions provided by the 
WIP message have been reviewed.
•
Notify an engineer that a container has reached a specific location.
WIP messages can come in the form of a display to the shop floor users during a transaction or an e-mail to 
another person, for example, an engineer or a supervisor.
A WIP message must be one of these types.
Type
Meaning
All Keys
The virtual pages  receive WIP messages for a container that matches the WIP 
message’s associated modeling definition at a workflow step.
Operation Keys
The virtual pages  receive WIP messages for the container at a specified 
operation that matches the WIP message’s associated modeling definition.
For example, you can create a WIP message for Sales Order 1 using WIP Message 
Operation Key and select the Packaging operation. The message will appear for 
the container at Packaging with Sales Order 1 as one of its attributes.
Label Keys
You can define a WIP message using a label key and attach that label to several 
steps. The virtual pages  receive WIP messages for the container that matches 
the WIP message’s associated modeling definition at the workflow step that 
references the label name.
In This Chapter
This chapter contains  these topics:
•
Defining WIP Messages
•
Copying and Deleting WIP Messages
Release 2510+ Rev. 1
Modeling User Guide
7-1
Chapter 7: WIP Messages
Defining WIP Messages
There are two procedures needed to create WIP Messages:
•
Create the WIP message.
•
Configure the criteria for evaluating WIP messages. Refer to "Specifying WIP Messages to 
Evaluate" for information.
You must perform both procedures, but the order does not matter. When a container is started and 
processed with the attributes associated with WIP messages, and when the container reaches the 
processing step for which a WIP message has been defined, all messages matching the criteria set are 
retrieved.
You can also configure the WIP message to send an e-mail to someone other than the operator (for 
example, an engineer, or a supervisor) when a container reaches a certain step in the production process. 
You can attach WIP messages to these modeling definitions:
•
Bill of Process
•
Bill of Materials (BOM)
•
Carrier
•
Change Mgt Spec
•
Change Mgt Workflow
•
Checklist Template
•
Container Level
•
Customer
•
Data Collection Def
•
Date Requirement
•
Document
•
Electronic Procedure
•
ERP BOM
•
ERP Route
•
Factory
•
Hold Reason
•
Master Recipe
•
Recurring Date Requirement
•
Report Template
•
Resource
•
Rework Reason
•
Sales Order
•
Sample Data Point
•
Sample Test
•
Sampling Plan
•
Scale
•
Setup
•
Shipping Reason
•
Spec
•
Start Reason
•
Switching Rule
•
Task List
•
Thruput Requirement
•
Training Requirement
7-2
Modeling User Guide
Release 2510+ Rev. 1
Chapter 7: WIP Messages
•
Mfg Order
•
Operation
•
Owner
•
Printer Label Definition
•
Priority Code
•
Product
•
Product Family
•
Product Type
•
Recipe
•
Recipe List
•
User Codes with WIP messages:
Hold Reason
Owner
Priority Code
Product Type
Rework Reason
Shipping Reason
Start Reason
•
User Data Collection Def
•
UOM
•
Work Center
•
Workflow
WIP Message Creation Procedure Overview
You must perform these procedures in this order to create a WIP Message:
1.
Open the WIP Message page.
2.
Start the new WIP message.
3.
Enter the WIP message details.
The button is only enabled for definitions that allow you to attach a WIP message and only after that 
definition is saved.
Instructions for performing these tasks follow.
Release 2510+ Rev. 1
Modeling User Guide
7-3
Chapter 7: WIP Messages
WIP Messages Page
This image shows an example of the WIP Messages page.
WIP Messages Page Field Definitions
This table defines the fields unique to the WIP Messages page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
General
Status
Current status  or the WIP message. Options include: 
•
Active
•
Inactive
Optional
Effective From 
Date
Beginning effective date (in mm/dd/yyyy hh:mm AM/PM format) for 
the message.
Optional
Effective Thru Date Ending effective date (in mm/dd/yyyy hh:mm AM/PM format) for the 
message.
Optional
7-4
Modeling User Guide
Release 2510+ Rev. 1
Chapter 7: WIP Messages
Field 
Definition
Type
Relevant Service 
Type
List of available services. The WIP message is displayed at the 
selected service.
Optional
Message Text
Message that contains important information to be communicated. 
The first 15 characters of the message text comprise the name of the 
WIP message as it appears on the WIP selection page. These 15 
characters can be used to identify the WIP message on the selection 
page.
Required
Write to History
Check box to indicate whether the message is written to the 
database for the transaction.
Optional
Document
List of previously defined documents. Select one if you want a 
separate file to be displayed with the WIP message. This document 
becomes accessible on the user interface when the WIP message is 
displayed. You must have previously defined one or more documents 
in Modeling to see valid selections in this field.  The file name of your 
document must not contain spaces. The application will not 
recognize the file name if it contains spaces.
Optional
Contact Info
Information such as e-mail address, phone number, and/or name for 
the contact.
Optional
Processing
Acknowledgment 
Required
Check box to indicate whether the user should acknowledge the WIP 
message.
Optional
Password Required
Check box to indicate whether the user name and password are 
required in the user interface. The entered password must match the 
entry in the WIP Msg Password field. 
Optional
Stop Processing
Check box to indicate whether the WIP process be stopped when this 
WIP message is displayed. This prevents the container from being 
processed through  any future transactions.
Optional
Hold Reason
List of previously defined hold reasons. This specifies the reason that 
processing was stopped. You must have previously defined one or 
more hold reasons to see valid selections in this field. 
Optional
WIP Msg Password
Password that must be matched when the WIP password is entered in 
the user interface for this WIP message.
Optional
Notification
Send Notification
Check box to indicate whether notification is sent to another 
recipient.
Optional
Notification Text
Subject of the e-mail.
Optional
Notification 
Targets grid
List of previously defined e-mail notifications. This e-mail address will 
be used to send the message specified in the Notification Text field. 
You must have previously defined one or more e-mail notifications in 
Modeling to see valid selections in the Name  list.
Optional
Name
Name of the e-mail notification target.
Optional
Release 2510+ Rev. 1
Modeling User Guide
7-5
Chapter 7: WIP Messages
How to Define WIP Messages
Follow these steps to define WIP messages:
1.
Open an instance of a modeling object that supports WIP messages. The modeling object page 
appears within the Modeling page.
2.
Click WIP Messages. The WIP Messages page appears.
3.
Click New. The WIP Msg Type field appears.
4.
Select a key from the WIP Msg Type  list (the default is All Keys). An additional field appears if 
you select Operation or Label keys.
5.
Did you select Label Keys or Operation Keys?
If you selected . . .
Then . . .
Label Keys
a.
Enter a label in the Label To Find field.
Note: WIP Message Labels are defined on the Step 
Details pop-up. Refer to "How to Modify Step 
Information" for information.  
b.
Go to step 6.
Operation Keys
a.
Select an operation from the Operation To Find  list.
b.
Go to step 6.
All Keys
Go to step 6.
6.
Click Continue. The WIP Messages fields appear.
7.
Enter a WIP message in the Message Text field.
8.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
9.
Click Save Message. The application saves the WIP message and displays a success message.
How to Add Notification Targets to WIP Messages
Follow these steps to finish defining the WIP message details:
1.
Complete the "How to Define WIP Messages" procedure.
Or
Select an existing WIP Message instance.
2.
Expand the Notification section.
3.
Click Add new row on the Notification targets grid. A new row appears.
4.
Select an e-mail notification from the Name  list.
5.
Repeat steps 3-4 to add additional notification targets.
6.
Click Save Message. The application displays a success message indicating the WIP message 
was updated.
7-6
Modeling User Guide
Release 2510+ Rev. 1
Chapter 7: WIP Messages
Copying and Deleting WIP Messages
At times you may want to make a copy of a WIP message. Opcenter EX MDD and Opcenter EX CR provide 
the option of copying the WIP message under a new key type or under the same key type as the original.
How to Copy a WIP Message
Follow these steps to copy a WIP message: 
1.
Open an instance of a modeling object that supports WIP messages. The modeling object page 
appears within the Modeling page.
2.
Click WIP Messages. The WIP Messages page appears.
3.
Select an existing WIP message in the WIP Message Type pane. The Copy button appears.
4.
Click Copy. The Create New WIP Message fields appear.
5.
Select a key from the WIP Msg Type  (the default is All Keys). An additional field appears if you 
select Operation or Label keys.
6.
Did you select Label Keys or Operation Keys?
If you selected . . .
Then . . .
Label Keys
a.
Enter a label in the Label To Find field.
b.
Go to step 7.
Operation Keys
a.
Select an operation from the Operation To Find  list.
b.
Go to step 7.
All Keys
Go to step 7.
7.
Click Continue. The WIP Messages fields appear.
8.
Modify the existing WIP message.
Or 
Enter a new WIP message in the Message Text field.
9.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
10.
Click Save Message. The application displays a success message indicating the WIP message 
was updated.
Release 2510+ Rev. 1
Modeling User Guide
7-7
Chapter 7: WIP Messages
How to Delete a WIP Message
Follow these steps to delete a WIP message:
1.
Open an instance of a modeling object that supports WIP messages. The modeling object page 
appears within the Modeling page.
2.
Click WIP Messages. The WIP Messages page appears.
3.
Select an existing WIP message in the WIP Message Type pane. The Delete button appears.
4.
Click Delete. The application displays a success message indicating the WIP message was 
deleted.
7-8
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Introduction
The quality model portion of the Information Model is used for creating modeling objects related to quality 
issues, for example the objects used to set up Event Recording.
In This Chapter
This chapter contains these topics:
•
Defining Message Categories 
•
Defining Portal Message Categories
•
Defining Approval Decision Lists
•
Defining Approval Templates
•
Defining Comment Types
•
Defining Failure Action Types
•
Defining Failure Action Type Groups
•
Defining Failure Modes
•
Defining Failure Mode Groups
•
Defining Failure Severities
•
Defining Failure Types
•
Defining Cause Codes
•
Defining Priority Levels
•
Defining Occupations
•
Defining Quality Record Resolution 
Codes
•
Defining Report Templates
•
Defining Triage Specs
•
Defining Dispositions
•
Defining E-mail Distributions
•
Defining E-mail Messages
•
Defining E-mail Groups
•
Defining Classifications
•
Defining Subclassifications
•
Defining Response Sets
•
Defining Checklist Templates
•
Defining Numbering Rules
•
Defining Smart Scan Rules
Release 2510+ Rev. 1
Modeling User Guide
8-1
Chapter 8: Quality Model Definitions
Defining Message Categories
A Message Category is a label used to identify groups of  messages displayed on the Concierge and in 
Message Center. Message categories can be used as search parameters on the Message Center page.  
When Defining Message Categories
These message categories are provided by default:
•
My Assignments
•
My Approvals
•
My Pending Items
•
My Alerts
You must associate a message category with one or more notification types in the Portal Message 
Category modeling object before the application will display the message category. Refer to "Defining 
Portal Message Categories" for information. 
Message Category is a required field in the Portal Message Category modeling definition. 
Message Category Page
This image shows an example of the Message Category page.
8-2
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Message Category Page Field Definitions
This table defines the fields unique to the Message Category page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
Details
Message Category 
Value
Alphanumeric value to display  for this message category. You 
can enter a maximum of 2000 characters.
Required
Message Category ID 
System-generated ID assigned to this message category.
Display Only
How to Define a Message Category
Follow these steps to define a Message Category:
1.
Open the Message Category page. The Message Category page appears within the Modeling 
page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for the message category in the Message Category field.
4.
Enter a value in the Message Category Value field. 
5.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
6.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
8-3
Chapter 8: Quality Model Definitions
Defining Portal Message Categories
Siemens provides a single Portal Message Category modeling object instance with a Portal installation. The 
Portal Message Category modeling object allows you to customize the following:
•
Message categories displayed in the Concierge and Message Center
•
Notification types displayed within the message categories
•
Due date indicators for quality items
Note:
Refer to the following for information on the Concierge and Message Center:
•
Opcenter Execution Medical Device and Diagnostics Event Management User Guide or the 
Opcenter Execution Core Event Management User Guide
•
Opcenter Execution Medical Device and Diagnostics Nonconformance Management User 
Guide or the Opcenter Execution Core Nonconformance Management User Guide
•
the online help available from the quality record pages
Only one list of message categories can exist for the Portal. You cannot delete or duplicate this modeling 
object instance.
When Editing the Portal Message Categories Instance
Portal Message Category contains the required modeling object, Message Category. Siemens provides four 
message categories that are assigned to this instance by default, but you can define additional message 
categories to add. Refer to "Defining Message Categories" for information on defining message categories.
Important:
Add no more than six Message Categories to the Concierge for optimal performance.
The notification types you can associate with a message category are provided with the application during 
installation and cannot be changed. You can associate one or more notification types with a message 
category. The application requires you to associate at least one notification type with a message category 
before the application will display the message category in the Message Center or Concierge. 
When Managing Message Categories
The Message Category Definition grid displays the message categories  available in the Concierge and 
Message Center. The order of the message categories in the Message Category Definition grid determines 
the order they will display on the Concierge and the Message Center. Use the grid to do the following:
•
Add or remove message categories
•
Change where the message categories display
•
Change the order of the message categories
•
Adding or removing notification types to and from the message category
8-4
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
This table describes the default settings  for the message categories in this modeling object instance.
Message Category
Display in 
Concierge
Display in 
Message Center
Notification Types
My Assignments
Yes
Yes
Quality Record Ownership Assignment
My Approvals
Yes
Yes
Quality Record Approval Assignment
My Pending Items
Yes
Yes
Quality Record Pending Assignment
My Alerts
Yes
Yes
Quality Record Resolution Approved
Quality Record Resolution Rejected
Defining the Yellow Minimum and Maximum Ranges
The Yellow Minimum and Maximum Range fields on the Portal Message Category page determine when 
the due date indicators; (green circle,  orange circle, and red  circle) appear next to your Concierge and 
Message Center items.  The information below may be helpful when defining the minimum and maximum 
ranges for the due date indicators. 
Rules for the Due Date Range Indicator Fields
Rules for establishing the due date range indicators include:
•
Values in the Yellow Minimum and Maximum Range fields must be integers. 
•
Yellow Minimum Range (in days) must be less than Yellow Maximum Range (in days).
•
Yellow Minimum Range is the minimum number of days from the due date for the  orange 
indicator to display. The default value is 0. If the date difference for the activity is less than this 
number of days, the red  circle displays.
•
Yellow Maximum Range is the maximum number of days from the due date for the  orange 
indicator to display. The default value is 2. If the date difference for the activity is greater than 
this number of days, the green circle displays.
•
The application will not show any red indicators until after the due date has passed.
How the Priority Indicators are Calculated
This information explains how the priority indicators are calculated. Assume that:
•
Yellow minimum range = n  
•
Yellow maximum range = m  
•
m => n
Based on this:
•
Red: (Due date - Today) < n 
•
Orange: n <= (Due date - Today) <= m 
•
Green: m < (Due date - Today)
Release 2510+ Rev. 1
Modeling User Guide
8-5
Chapter 8: Quality Model Definitions
Portal Message Category Page
This image shows an example of the Portal Message Category page.
8-6
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Portal Message Category Page Field Definitions
This table defines the fields unique to the Portal Message Category page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
Details
Message Category 
Definition grid
Grid containing the list of message categories that may 
appear in the Concierge and the Message Center.
Required
Message 
Category
Name of the selected message category.
Required
Display in 
Message Center
Message category on this row appears in the Message Center 
when this check box is selected.
Optional
Display in 
Concierge
Message category on this row appears in the Concierge when 
this check box is selected.
Optional
Due Date Range
Yellow Minimum Range 
(in days)
Minimum number of days from the due date for the 
application to display the  orange circle indicator. 
Required
Yellow Maximum Range 
(in days)
Maximum number of days from the due date for the 
application to display the  orange circle indicator. 
Required
Add Portal Message Map Detail  Pop-Up
The title of the pop-up used to add or edit message categories in the Message Categories Definitions grid 
on the Portal Message Category page changes dynamically based on the action you are performing. 
Clicking Add on the Message Categories Definition grid displays the Add pop-up. Selecting an existing 
message category in the Message Categories Definition grid and clicking Edit displays the Edit pop-up. 
Release 2510+ Rev. 1
Modeling User Guide
8-7
Chapter 8: Quality Model Definitions
This image shows an example of the pop-up when adding message categories.
Add or Edit Portal Message Map Detail Pop-Up Field Definitions
This table defines the fields on the Add or Edit pop-up.
Field
Definition
Type
Message 
Category
Name of the selected message category as defined in the Message 
Category modeling object.
Required
Icon
File name of the icon  associated with the message category. The 
application assigns the default icon if no icon is specified here.
Optional
Display in 
Message Center
Check box displaying the message category in the Message Center. 
Optional
Display in 
Concierge
Check box displaying the message category in the Concierge.
Optional
Notification 
Types Grid
Types of quality notifications you can associate with the message 
category. You must assign at least one notification type. 
Required
8-8
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
How to Select the Portal Message Category
Follow these steps to select the Portal Message Category:
1.
Open the Portal Message Category page. The Portal Message Category page appears within the 
Modeling page.
2.
Select the Portal Message Category instance. The  fields and values for the instance appear.
How to Edit a Message Category
Follow these steps to edit a Message Category in the Portal Message Category list:
1.
Perform the "How to Select the Portal Message Category" procedure.
Or
Select an existing Portal Message Category instance.
2.
Click Edit selected row to edit the properties of an existing message category. The Edit pop-up 
appears.
3.
Perform one or more of the following to modify the message category settings:
•
Select a category from the Message Category  list to change the existing category.
•
Select or clear the Display in Message Center or Display in Concierge check boxes.
•
Click the Add new row button on the Notification Types grid to select a notification to 
associate with the message category. A new row appears.
•
Select a row and click Delete selected row on the Notification Types grid to remove a 
notification type from the message category.
4.
Do one of the following: 
Click OK. The Portal Message Map Detail pop-up closes.
Or
Click Close to close without saving. The Edit pop-up closes.
5.
Click Save. The application saves the changes and displays a message that the Portal Message 
Category has been updated.
How to Add a Category to the Message Category Definition Grid
Follow these steps to add a new category to the Message Category Definition grid:
1.
Perform the "How to Select the Portal Message Category" procedure.
Or
Select an existing Portal Message Category instance.
2.
Click the Add new row button on the Message Category Definition grid. The Add pop-up 
appears.
3.
Select a Message Category  from the list.
Release 2510+ Rev. 1
Modeling User Guide
8-9
Chapter 8: Quality Model Definitions
4.
Select the Display in Message Center check box if you want this category of messages to appear 
in the Message Center display.
5.
Select the Display in Concierge check box if you want this category of messages to display in the 
Concierge display.
6.
Click Add new row on the Notification Types grid and select a notification type from the 
Notification Types  list. 
7.
Repeat step 7 to associate additional notification types.
8.
Click OK. The Add pop-up closes and the new message category appears in the Message 
Category Definition grid.
9.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Delete a Message Category Definition from the List
Follow these steps to delete a message category from the list:
1.
Perform the "How to Select the Portal Message Category" procedure.
Or
Select an existing Portal Message Category instance.
2.
Select a row in the Message Category Definition grid.
3.
Click  Delete selected row in the grid footer to remove the selected message category.
4.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Change the Sort Order for the Concierge and Message Center
Follow these steps to change the sort order for the Concierge Message Center:
1.
Perform the "How to Select the Portal Message Category" procedure.
Or
Select an existing Portal Message Category instance.
2.
Select a row in the Message Category Definition grid. 
3.
Use the Move Row arrows  in the grid footer to move the selected row to the appropriate position 
in the list.
4.
Repeat this process until the categories appear in the appropriate order.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
8-10
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
How to Define the Ranges for Due Date Indicators
Follow these steps to define the ranges for the message due date indicators:
1.
Perform the "How to Select the Portal Message Category" procedure.
Or
Select an existing Portal Message Category instance.
2.
Expand the Due Date Range section.
3.
Enter a number in the Yellow Minimum Range (in days) field. 
4.
Enter a number in the Yellow Maximum Range (in days) field. 
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
8-11
Chapter 8: Quality Model Definitions
Defining Approval Decision Lists
The Approval Decision List is used to define the decisions that are presented to designated approvers when 
the application requires approval for quality record resolution. You associate each decision with a pre-
defined decision type (for example, Approved or Rejected). 
The application determines the approval decision list to use based on the approval template associated 
with the resolution or transition. You specify an approval decision list when defining an approval template. 
Refer to “Defining Approval Templates” for information on defining an approval template.
Approval Decision Examples
Here are two examples of approval decisions:
•
Reject with Comments
•
Approve without Comments
When Defining Approval Decision Lists
When defining approval decision lists, note the following:
•
The application requires you to define at least one decision for each approval decision list.
•
You may want to create a different approval decision list for each type of approval being sought. 
For example, you can define a decision list specifically for quality record resolution.
•
Approval Decision List is a required field in the definition of approval template.
Approval Decision List Page
This image shows an example of the Approval Decision List page.
8-12
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Approval Decision List Page Field Definitions
This table defines the fields unique to the Approval Decision List page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
General
Decisions grid
Decisions and corresponding approvals statuses for this approval 
decision list.
Required
Decision 
Name
Unique name for this approval decision.
Required
Approval 
Status
Pre-defined status assigned to the corresponding decision.
Required
Include 
Comments
Check box requiring the approver to enter comments when 
selecting this decision.
Optional
How to Define an Approval Decision List
Follow these steps to define an Approval Decision List:
1.
Open the Approval Decision List page. The Approval Decision List page appears within the 
Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this approval decision list in the Approval Decision List field.
4.
Click Add new row in the Decisions grid. A new row appears.
5.
Enter the decision name in the Decision Name column.
6.
Select an approval status from the Approval Status list.
7.
Repeat steps 4-6 to add another decision.
8.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
9.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
8-13
Chapter 8: Quality Model Definitions
Defining Approval Templates
An Approval Template identifies users who need to approve a quality record resolution and specifies a list 
of possible decisions for those users. Associating an approval template with a resolution ensures the 
appropriate decision list is presented to the appropriate users at the time of approval. 
When assigning approval templates for quality record resolution, you assign the templates to an 
organization. The application then assigns the approval template to the quality record automatically. 
Refer to "Defining an Organization" for information on assigning approval templates to an organization.
When Defining an Approval Template
When defining an approval template, remember the following:
•
The application requires you to select an approval decision list (defined in Modeling).
Note:
You must use the Approval Decision List page in Modeling to add or modify approval 
decision lists.
•
You can specify additional approvers when assigning the approval template when resolving a 
quality record.
•
You can define general instructions for all approvers and specific instructions for a single 
approver. 
•
You can define edit options to control the changes an owner can make to an approver row during 
the approval process. For example, you can allow the owner to change approvers.
•
You can define substitute options to indicate whether users in the same role as the approver can 
perform the approval. 
Note:
All approvals for a level must be completed before the application will route approvals 
for the next level.
When Defining Role Substitution Options
You must perform the following tasks to allow substitute users to perform an approval for the specified 
approver:
•
Add the substitute approvers (employees) and their organizations to the specified approver's Role 
modeling object. Substitute approvers must belong to the same role as the specified approver. 
Refer to "Defining Roles" for information on updating the Role modeling object. 
•
When defining the approval template, select Role as the Substitute Option for the specified 
approver. Selecting Role enables a substitute to perform the approval in place of the specified 
approver. 
•
When adding the substitute approvers to the approval template, you must add them at the same 
level that you added the specified approver.
8-14
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Approval Template Page
This image shows an example of the Approval Template page.
Approval Template Page Field Definitions
This table defines the fields unique to the Approval Template page and Add Approvers pop-up.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
General
Approval Decision List
Approval decision list associated with this approval template. 
Required
Instructions for All 
Approvers
Instructions that apply to all approvers associated with this 
template (up to 255 characters).
Optional
Approvers grid
Grid listing all approval roles and corresponding approvers for 
this template. The fields in this grid appear on the Add and Edit 
pop-ups.
Optional
Level 
Level of approval associated with the approver. You can enter 
numerical characters only.
The level defines the approval routing sequence. The 
application can route the approval to approvers sequentially, in 
parallel, or as a combination of sequentially and parallel.
Required
Release 2510+ Rev. 1
Modeling User Guide
8-15
Chapter 8: Quality Model Definitions
Field 
Definition
Type
Role
Designated role of the approver.
Required
Name
Name of the approver. 
Note: If you do not specify an approver here, the application 
will require the Approval Process Owner to specify the 
approver before routing.
Required
Duration
Number representing the total time allowed for approval.
Optional
Period
Units used to measure the time allowed for approval.
Optional
Entry Required
Check box indicates whether an approval is required at this 
level. During the approval process, the owner cannot modify 
the row for this approver.  
Optional
Edit Option
Option that indicates the changes an owner can make to an 
approver row during the approval process:
•
Role and Name (the default value) indicates the owner 
can change the approver role and name.
•
Name indicates the owner can change the approver 
name only.
•
None indicates the owner cannot modify the approver 
role or name. When you select None, the application 
sets the value in the Substitute Option field to None 
and makes that field read-only.
Required
Substitute 
Option
Option that indicates whether users other than the one 
specified in the Name column can perform the approval: 
•
Role indicates that any user in the same role can 
perform the approval.
•
None indicates that only the specified user can 
perform the approval.
Required
Instructions for 
Approver
Specific instructions for this approver (up to 255 characters).
Optional
Add Approvers  Pop-Up
The title of the pop-up used to add or edit approvers in the Approvers grid on the Approval Template page 
changes dynamically based on the action you are performing. Clicking Add new row on the Approvers grid 
displays the Add pop-up. Selecting an existing approver in the Approvers grid and clicking Edit selected 
row displays the Edit pop-up. 
8-16
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
This image shows an example of the pop-up when adding approvers.
How to Define an Approval Template
Follow these steps to define an Approval Template:
1.
Open the Approval Template page. The Approval Template page appears within the Modeling 
page.
2.
Enter a name for this approval template in the Approval Template Name field.
3.
Select an Approval Decision List from the list.
4.
Add at least one approver to the Approvers grid by completing the "How to Add Approvers to an 
Approval Template" procedure.
5.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
6.
Click Save. The application saves the modeling object and displays a success message.
How to Add Approvers to an Approval Template
Follow these steps to add approvers to an Approval Template:
1.
Perform the “How to Define an Approval Template” procedure. 
Or 
Select an existing Approval Template instance.
2.
Click Add new row in the Approvers grid. The Add pop-up appears.
3.
Enter a numeric approval level in the Level field.
4.
Select a Role from the list.
Release 2510+ Rev. 1
Modeling User Guide
8-17
Chapter 8: Quality Model Definitions
5.
Select a Name from the list.
6.
Select an Edit Option from the list.
7.
Select a Substitute Option from the list.
8.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
9.
Click OK. The application closes the Approvers pop-up  and displays the approver information in 
the Approvers grid.
10.
Repeat steps 2-9 to add additional approvers.
11.
Click Save. The application displays a success message indicating the modeling object was 
updated.
8-18
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Defining Comment Types
The Comment Type modeling object allows you to define categories for user comments added to a generic 
or production event. Examples of comment types include Investigation, Disposition, and Containment. The 
application requires users to select a comment type when adding their comments on the Log tab for the 
generic or production event. 
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Comment Type
Follow these steps to define a Comment Type:
1.
Open the Comment Type page. The Comment Type page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this comment type in the Comment Type field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
8-19
Chapter 8: Quality Model Definitions
Defining Failure Action Types
A Failure Action Type defines a specific  action (for example, Corrective) that can be performed in response 
to a specific cause. Action types are assigned to  quality records.
When Defining a Failure Action Type
Failure Action Type is an optional field in the Failure Action Type Group modeling definition. 
Users can assign one or more failure action types to generic and production event records. 
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Failure Action Type
Follow these steps to define a Failure Action Type:
1.
Open the Failure Action Type page. The Failure Action Type page appears within the Modeling 
page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this failure action type in the Failure Action Type field. 
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
8-20
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Defining Failure Action Type Groups
The Failure Action Type Group modeling object enables you to group similar failure action types together. 
Failure action type groups simplify the selection of failure action types for an event record by narrowing 
the action types available. 
When Defining a Failure Action Type Group
You can add multiple entries or groups to their respective grids.
The Resolved Entries button enables you to display a list of all of the values specified in the entries list for 
this group and all of the nested groups.
Failure Action Type Group contains the optional Modeling definition, Failure Action Type.
Failure Action Type Group Page
This image shows an example of the Failure Action Type Group page.
Release 2510+ Rev. 1
Modeling User Guide
8-21
Chapter 8: Quality Model Definitions
Failure Action Type Group Page Field Definitions
This table defines the fields unique to the Failure Action Type Group page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
Details
Entry 
Type
Name of the type of objects contained in this object group.
Display 
Only
Entries 
grid
Grid listing failure action types assigned to this group. The list of available 
failure action types is displayed from the types already defined on the Failure 
Action Type page.
Optional
Groups 
grid
Grid listing failure action type groups assigned to this group. The list of available 
failure action type groups is displayed from the other  groups already defined on 
the Failure Action Type Group page.
Optional
How to Define a Failure Action Type Group
Follow these steps to define a Failure Action Type Group:
1.
Open the Failure Action Type Group page. The Failure Action Type Group page appears within 
the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this failure action type group  in the Failure Action Type Group  field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
How to Add Entries to a Failure Action Type Group 
Follow these steps to add entries to a Failure Action Type Group:
1.
Perform the “How to Define a Failure Action Type Group” procedure. 
Or 
Select an existing Failure Action Type Group instance.
2.
Click Add new row in the Entries grid. A new row appears.
3.
Click in the blank row and select a failure action type from the list of available failure action types.
4.
Repeat steps 2-3 to add additional failure action types to this group.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
8-22
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
How to Add Groups to a Failure Action Type Group
Follow these steps to add other failure action type groups to a Failure Action Type Group:
1.
Perform the “How to Define a Failure Action Type Group” procedure. 
Or 
Select an existing Failure Action Type Group instance.
2.
Click Add new row in the Groups grid. A new row appears.
3.
Click in the blank row and select a failure action type group from the list of available groups.
4.
Repeat steps 2-3 to add additional failure action type groups to this group.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
8-23
Chapter 8: Quality Model Definitions
Defining Failure Modes
A Failure Mode describes the actual cause of a failure. Failure modes are specified when recording or 
managing events. 
When Defining a Failure Mode
Failure Mode contains the optional modeling definitions:
•
Failure Type
•
Failure Severity
Failure Mode is an optional field in the Failure Mode Group modeling definition.
Failure Mode Page
This image shows an example of the Failure Mode page.
Failure Mode Page Field Definitions
This table defines the fields unique to the Failure Mode page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
General
Default Failure Type
Default failure type definition for this failure mode. 
Optional
Default Failure Severity
Default failure severity definition for this failure 
mode.
Optional
How to Define a Failure Mode
Follow these steps to define a Failure Mode:
1.
Open the Failure Mode page. The Failure Mode page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for the failure mode in the Failure Mode field. 
8-24
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
8-25
Chapter 8: Quality Model Definitions
Defining Failure Mode Groups
The Failure Mode Group modeling object enables you to define a group of failure modes. It helps simplify 
the selection of a failure mode by allowing you to group failure modes that represent the actual cause of 
the failure.
Failure mode groups are associated with event classifications and subclassifications on the Organization 
page.
When Defining a Failure Mode Group
You can add multiple entries or groups to their respective grids.
The Resolved Entries button enables you to display a list of all of the values specified in the entries list for 
this group and all of the nested groups.
Failure Mode Groups contains the optional Modeling definition, Failure Mode.
Failure Mode Group Page
This image shows an example of the Failure Mode Group page.
8-26
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Failure Mode Group Page Field Definitions
This table defines the fields unique to the Failure Mode Group page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
Details
Entry Type
Name of the type of objects contained in this object group.
Display 
Only
Entries 
grid
Grid listing failure modes assigned to this group. The list of available failure 
modes is displayed from the modes already defined on the Failure Mode 
page.
Optional
Groups 
grid
Grid listing failure mode groups assigned to this group. The list of available 
failure mode groups is displayed from the other  groups already defined on 
the Failure Mode Group page.
Optional
How to Define a Failure Mode Group
Follow these steps to define a Failure Mode Group:
1.
Open the Failure Mode Group page. The Failure Mode Group page appears within the Modeling 
page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this failure mode group  in the Failure Mode Group  field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
How to Add Entries to a Failure Mode Group
Follow these steps to add entries to a Failure Mode Group:
1.
Perform the “How to Define a Failure Mode Group” procedure. 
Or 
Select an existing Failure Action Type Group instance.
2.
Click Add new row in the Entries grid. A new row appears.
3.
Click in the blank row and select a Failure Mode from the list of available Failure Modes.
4.
Repeat steps 2-3 for each Failure Mode to be added to this group.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
8-27
Chapter 8: Quality Model Definitions
How to Add Groups to a Failure Mode Group
Follow these steps to add other Failure Mode Groups to a Failure Mode Group:
1.
Perform the “How to Define a Failure Mode Group” procedure. 
Or 
Select an existing Failure Action Type Group instance.
2.
Click Add new row in the Groups grid. A new row appears.
3.
Click in the blank row and select a Failure Mode Group from the list of available groups.
4.
Repeat steps 2-3 for each Failure Mode Group to be added to this group.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
8-28
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Defining Failure Severities
A Failure Severity defines the severity of a failure during an event.  For example, you can create a 
succession of severities from minor to critical. Failure severities are specified when recording or managing 
events and nonconformances.
When Defining Failure Severities
Failure Severity is an optional field in the Failure Mode modeling object.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Failure Severity
Follow these steps to define a Failure Severity:
1.
Open the Failure Severity page. The Failure Severity page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this severity in the Failure Severity field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
8-29
Chapter 8: Quality Model Definitions
Defining Failure Types
A Failure Type is a way to describe the characteristic of the failure as well as to provide a way to categorize 
them. Examples of these Failure types are Continuous and Intermittent.  Failure types are specified when 
recording or managing events and nonconformances.
When Defining Failure Types
Failure Type is an optional field in the Failure Mode modeling object.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Failure Type
Follow these steps to define a Failure Type:
1.
Open the Failure Type page. The Failure Type page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter the name of the failure type in the Failure Type field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
8-30
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Defining Cause Codes
A Cause Code identifies the root cause for a failure. Examples of cause codes are Operator Error and 
Equipment Malfunction. When defined, these cause codes appear in the Cause Code  list on the shop floor 
forms.
When Defining a Cause Code
Associating an NCR Resolution Code Group with a cause code narrows the resolution codes available for a 
user to assign to a quality record assigned this cause code. The NCR resolution code group contains the 
resolutions possible for the failure identified in the quality record.
Cause Code contains the optional modeling definition NCR Resolution Code Group.
Cause Code is an optional field in the NCR Cause Code Group modeling definition.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Cause Code Page
This image shows an example of the Cause Code page. 
How to Define a Cause Code
Follow these steps to define a Cause Code:
1.
Open the Cause Code page. The Cause Code page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter the name of the cause code in the Cause Code field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
8-31
Chapter 8: Quality Model Definitions
Defining Priority Levels
A Priority Level defines an indicator used to assign processing priority to an event.  You can specify a 
priority level when recording an event and when managing quality records.  
When Defining Priority Levels
Do not confuse the Priority Level modeling object with the Priority Code modeling object. Priority levels are 
assigned to events and quality records while priority codes are assigned to containers. Refer to "Defining 
Priority Codes" for information on defining container priority indicators.
Priority levels can be used as a search parameter on the Quality Search page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Priority Level
Follow these steps to define a Priority Level:
1.
Open the Priority Level page. The Priority Level page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this priority level in the Priority Level field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
8-32
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Defining Occupations
The Occupation modeling object is used to define a specific job — for example, an inspector — to be used 
when entering a complaint.
Note:
The  implementation of Opcenter EX MDD or Opcenter EX CR does not use this object; however, 
the object is available for your use in your custom implementation by default.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define an Occupation
Follow these steps to define an Occupation:
1.
Open the Occupation page. The Occupation page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter the name of the occupation in the Occupation field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
8-33
Chapter 8: Quality Model Definitions
Defining Quality Record Resolution Codes
A Quality Record Resolution Code indicates the reason for resolving (closing) a quality record. The 
application requires a quality record resolution code to resolve the quality record.
When Defining Quality Record Resolution Codes
Resolution codes are required on the Quality Object Resolution page when resolving a quality record.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Quality Record Resolution Code
Follow these steps to define a Quality Record Resolution Code:
1.
Open the Quality Record Resolution Code. The Quality Record Resolution Code page appears 
within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for the resolution code definition in the Quality Record Resolution Code field. 
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
8-34
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Defining Report Templates
A Report Template is used to specify the RPT file to use for your Intelligence reports and charts. Refer to 
the Opcenter Execution Core Intelligence Reference Guide for information on charts and reports.
When Defining Report Templates
These rules apply when defining reports:
•
Each instance of a report template includes a  Locate File field to find a file to save or upload.
•
The Upload File to Database check box allows you to indicate when to upload the specified file to 
the database. Typically, you select this check box when defining a report template initially. 
Leaving the check box blank when updating existing instances allows you to make changes 
without having to upload the file.
•
The  application enables the  View Document button after a file  is uploaded to the database and 
the Report Template instance is saved. Click  View Document to view or download the document. 
•
The Stored File Name field is a read-only field that displays the file name after you click Save.
•
The download/upload time of an RPT file will vary by file size.
Report Template Page
This image shows an example of the Report Template page.
Release 2510+ Rev. 1
Modeling User Guide
8-35
Chapter 8: Quality Model Definitions
Report Template Page Field Definitions
This table defines the fields unique to the Report Template page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
General
Engineering 
Change Order
Engineering change order assigned to this revision. You can enter a 
maximum of 30 characters. 
Optional
Locate File
Click the Browse button next to the field to navigate to the file. Select a 
file to be uploaded to the database. 
Display 
Only
Upload File to 
Database
Click box indicating the application uploads the file to the database 
when you save.
Optional
Stored File 
Name
File name of the report template saved in the database. Displays the file 
name after uploading and clicking Save.
Optional
File Version
Version of the file saved in the database.
Optional
How to Define a Report Template
Follow these steps to define a Report Template:
1.
Open the Report Template page. The Report Template page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this report template in the Report Template field.
4.
Enter the revision of this template in the Revision field.
5.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
6.
Click Save. The application saves the modeling object and displays a success message.
How to Add a File to a Report Template
Follow these steps to add a file to a report template:
1.
Perform the “How to Define a Report Template” procedure. 
Or 
Select an existing Report Template instance.
8-36
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
2.
Click the Browse button next to the Locate File field. A pop-up appears for you to browse for a 
file.
3.
Browse for a file and then click Open. The pop-up closes and the file name appears in the Locate 
File field.
4.
Select Upload File to Database.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
8-37
Chapter 8: Quality Model Definitions
Defining Triage Specs
The Triage Spec modeling object is used to define the default processing values for performing triage on 
events. It defines the default values to be used during manual triage and the business rules to be applied 
during automatic triage.
The application determines the triage spec to use based on the organization to which an event belongs. 
You associate triage specs with an organization and category when you define that organization. 
Refer to "Defining an Organization" for information on organizations. 
When Defining a Triage Spec
Triage Spec contains the following optional Modeling definitions: Role, Owner, Checklist Template, and 
Business Rule.
Only those business rules with a usage type of quality object are available for selection when adding 
business rules to a triage spec. 
Note:
You must use the Business Rules page in Modeling to add or modify business rules. Refer to 
"Defining Business Rules" for information. 
Triage Spec Page
This image shows an example of the Triage Spec page.
8-38
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Triage Spec Page Field Definitions
This table defines the fields unique to the Triage Spec page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
Details
Triage Items grid
Grid containing the default values for items on which you must 
perform triage manually.
Optional
To 
Category
Category to which you can escalate the item. 
Required
Role
Role to which you can assign responsibility for the quality record. 
Specifying a role allows you to assign the quality record to a specific 
group of employees, which allows anyone in the group to take 
ownership. 
The selection made in this field determines the employees available 
for selection in the Owner field. For example, if the assignee role is 
Default Quality, then only employees assigned to the Default Quality 
role are available for selection. 
Required
Owner 
Owner to whom you can assign responsibility for the quality record. 
The selection in the Role field determines the employees available in 
this field.
Required
Checklist 
Template
Checklist template to assign to quality records created with this 
category. Users will complete this checklist when processing the 
event. 
Note: If a checklist template is specified in the Event Classification 
Spec Maps also, the checklist template specified here takes 
precedence. 
Optional
Business Rules grid
Grid containing a list of business rules associated with this triage 
spec. The grid displays the business rules and the application 
executes them in the order they were added. If your user rights 
permit, you can add and delete business rules.
Optional
Business 
Rules Field
Name of Business Rule associated with the Triage Spec.
Optional
How to Define a Triage Spec
Follow these steps to define a Triage Spec:
1.
Open the Triage Spec page. The Triage Spec page appears within the Modeling page. 
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this task list in the Triage Spec field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
Release 2510+ Rev. 1
Modeling User Guide
8-39
Chapter 8: Quality Model Definitions
5.
Click Save. The application saves the modeling object and displays a success message.
How to Add Manual Triage Items to a Triage Spec 
Follow these steps to add manual triage items to a Triage Spec:
1.
Perform the “How to Define a Triage Spec” procedure.
Or
Select an existing Triage Spec instance.
2.
Locate the Triage Items grid.
3.
Click Add new row. A new row appears. 
4.
Select an escalation category from the To Category list.
5.
Select a Role from the list.
6.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
7.
Repeat steps 3-6 to add additional manual triage items.
8.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Remove Manual Triage Items
Follow these steps to remove a manual triage item from a Triage Spec:
1.
Perform the “How to Define a Triage Spec” procedure.
Or
Select an existing Triage Spec instance.
2.
Locate the Triage Items grid.
3.
Select the row you want to delete.
4.
Click Delete selected row. The row is removed from the grid.
5.
Repeat steps 3-4 to remove additional items.
6.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Add Business Rules to a Triage Spec
Follow these steps to add business rules for automatic triage to a Triage Spec:
1.
Perform the “How to Define a Triage Spec” procedure.
Or
Select an existing Triage Spec instance.
2.
Locate the Business Rules grid.
3.
Click Add new row. A new row appears.
4.
Select a Business Rule from the list.
8-40
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
5.
Repeat steps 3-4 to add additional business rules.
6.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
8-41
Chapter 8: Quality Model Definitions
Defining Dispositions
The Disposition modeling object allows you to define a method of disposal for materials in lots 
(containers). Examples of dispositions include Scrap, Rework, and Return to Vendor.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Disposition
Follow these steps to define a Disposition:
1.
Open the Disposition page. The Disposition page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this disposition in the Disposition field. 
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
8-42
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Defining E-mail Distributions
The E-mail Distribution modeling object is used to specify the recipients for e-mail notification. 
You can configure recipients from one or more of the following categories:
•
External Recipients
•
Role Recipients
•
Employee Recipients
When Defining an E-mail Distribution
Employee recipients are retrieved from the Employee modeling definition. Employees must have an e-mail 
address defined on the Employee object before that employee will display in the Employee Recipients list.
Role recipients are retrieved from the Role modeling definition.
The application does not verify external recipients.
E-mail distribution is an optional field in the definition of Organization.
E-mail Distribution Page
This image shows an example of the E-mail Distribution page.
Release 2510+ Rev. 1
Modeling User Guide
8-43
Chapter 8: Quality Model Definitions
E-mail Distribution Page Field Definitions
This table defines the fields unique to the E-mail Distribution page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
Recipients
External 
Recipients grid
E-mail address of an external recipient in this e-mail distribution.
Optional
Employee 
Recipients grid
List of employee names that have an assigned e-mail.
Optional
Role Recipients 
grid
List of available roles.
Optional
How to Define an E-mail Distribution
Follow these steps to define an E-mail Distribution:
1.
Open the E-mail Distribution page. The E-mail Distribution page appears within the Modeling 
page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this E-Mail Distribution definition in the E-mail Distribution field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Enter an e-mail address in the field, if defining an External Recipient.
6.
Click Save. The application saves the modeling object and displays a success message.
How to Add Recipients to an E-mail Distribution
Follow these steps to add recipients to an e-mail distribution:
1.
Perform the “How to Define an E-mail Distribution” procedure. 
Or 
Select an existing e-mail distribution instance.
2.
Click Add new row on one of the following grids:
•
External Recipients
•
Role Recipients
•
Employee Recipients
8-44
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
3.
Do you want to add an external recipient, role recipient, or an employee recipient?
If you want to add . . .
Then . . .
An external recipient.
a.
Enter an e-mail address in the blank row.
b.
Go to step 4.
An employee recipient.
a.
Select an employee recipient from the  list.
b.
Go to step 4.
A role recipient.
a.
Select a role recipient from the list. 
b.
Go to step 4.
4.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
8-45
Chapter 8: Quality Model Definitions
Defining E-mail Messages
The E-mail Message modeling object is used to define the messages for e-mail notification. After you save 
it, the definition will be available for selection in the Organization modeling object. 
When Defining an E-mail Message
The same e-mail message can be re-used many times.
E-mail Message is an optional field you can specify when defining an organization. It is required if defining 
a notification event.
E-mail Message Page
This image shows an example of the E-mail Message page.
E-mail Message Page Field Definitions
This table defines the fields unique to the E-mail Message page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
Message
Sender
E-mail address of the sender.
Required
Subject
Topic of this e-mail.
Required
Message
Message to the recipients of this e-mail.  
Optional
8-46
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
How to Define an E-mail Message 
Follow these steps to define an E-mail Message:
1.
Open the E-mail Message page. The E-mail Message page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this E-Mail Message definition in the E-mail Message field.
4.
Enter the e-mail address of the sender in the Sender field. 
5.
Enter a subject in the Subject field.
6.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
7.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
8-47
Chapter 8: Quality Model Definitions
Defining E-mail Groups
The E-mail Group modeling object is used to group email recipients such as employees. Each email group 
requires an Email Transport (SMTP ) to be selected.
E-mail Group Page
This image shows an example of the E-mail Group page.
E-mail Group Page Field Definitions
This table defines the fields unique to the E-mail Group page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
Details
E-mail Transport
Name representing an SMTP protocol used to send email messages.
Required
Entry Type
Type of objects contained in this object group. 
Note: The application provides a default value of "Employee" which 
cannot be changed.
Optional
Entries grid
Grid that enables you to add employee user names to the group and 
that lists any employee user names already added to the group. 
Note: Existing entries can be deleted.
Optional
Groups grid
Grid that enables you to add other email groups as sub-groups and 
also lists any sub-groups already added. 
Note: Existing entries can be deleted.
Optional
8-48
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
How to Define an E-mail Group 
Follow these steps to define an E-mail Group:
1.
Open the E-mail Group paClick Save. The application saves the modeling object and displays a 
success message.ge. The E-mail Group page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this E-Mail Group definition in the E-mail Group field.
4.
Select the E-mail Transport.
5.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
Release 2510+ Rev. 1
Modeling User Guide
8-49
Chapter 8: Quality Model Definitions
Defining Classifications
A Classification is a required indicator for the type of quality record. Classifications are paired with 
Subclassifications (a related modeling object). 
The classification/subclassification combination is specified in the Event Classification Spec Map on the 
Organization object. Each combination determines which Portal pages and pageflows are displayed when 
the user is creating a specific type of Event. 
Note:
Portal pages and pageflows are defined in the Portal Studio.
Use the Classification modeling object to define classification instances that are specific to your business 
practices. 
When Defining Classifications
Classification is an optional field in the Organization modeling object, specifically the Event Classification 
Spec Map. Although Classification is an optional field, the application requires you to specify a 
classification when adding an entry to the Event Classification Spec Map.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Classification
Follow these steps to define a Classification:
1.
Open the Classification page. The Classification page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance.  
3.
Enter the name of the classification in the Classification field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
8-50
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Defining Subclassifications
A Subclassification is a required indicator for the type of quality record. Subclassifications are paired with 
Classifications (a related modeling object). 
The Classification/Subclassification combination is specified in the Event Classification Spec Map on the 
Organization object. Each combination determines which Portal pages and pageflows are displayed when 
the user is creating a specific type of Event. 
Note:
Portal pages and pageflows are defined in the Portal Studio.  
Use the Subclassification modeling object to define Subclassification instances that are specific to your 
business practices.
When Defining Subclassifications
Subclassification is an optional field in the Organization modeling object, specifically the Event 
Classification Spec Map. Although subclassification is an optional field, the application requires you to 
specify a subclassification when adding an entry to the Event Classification Spec Map.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Subclassification
Follow these steps to define a Subclassification:
1.
Open the Subclassification page. The Subclassification page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter the name of the subclassification in the Subclassification field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
8-51
Chapter 8: Quality Model Definitions
Defining Response Sets
The Response Set modeling object enables you to configure various sets of responses that are presented to 
users when they are completing a checklist item or answering a checklist question. For example, a 
response set can include responses such as Yes, No, and Pending, and the set can be assigned to a 
checklist item such as “Did the product pass all quality assurance testing?”
When Defining a Response Set
You specify a response set when adding a checklist item during checklist template definition.  Refer to 
"Defining Checklist Templates" for information on defining checklist templates.
Siemens recommends a maximum of five responses in a response set.
Response Set is an optional field in the definition of Checklist Template.
Response Set Page
This image shows an example of the Response Set page.
Response Set Page Field Definitions
This table defines the fields unique to the Response Set page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
Details
8-52
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Field 
Definition
Type
Response Set grid
Grid that enables you to add (or delete) responses to be used in the 
response set. The grid displays the responses and the sequence in 
which the application will display them.
Optional
Number
Integers that indicate the order in which the application displays the 
responses. Enter integers only.
Optional
Response 
Label
Response options displayed to the user when completing the 
checklist item with which the response set is associated. 
Optional
How to Define a Response Set
Follow these steps to define a Response Set:
1.
Open the Response Set page. The Response Set page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this set in the Response Set field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
How to Add Responses to a Response Set
Follow these steps to add responses to a response set:
1.
Perform the “How to Define a Response Set” procedure. 
Or 
Select an existing response set instance.
2.
Click Add new row in the Response Set grid.  A new row is added to the grid.
3.
Enter a number in the Number column.
4.
Enter a response in the Response Label column.
5.
Repeat steps 2-4 to add additional responses.
6.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
8-53
Chapter 8: Quality Model Definitions
Defining Checklist Templates
The Checklist Template modeling object enables you to define a checklist of items (questions or tasks) that 
you can assign to the following:
•
Organization
•
Triage Spec
A checklist ensures a user completes required steps when processing an event. A checklist question or 
item can be required or optional, depending on how the template was defined. Refer to “Defining Triage 
Specs” for information on assigning checklist templates to a triage spec.
When Defining Checklist Templates
Checklist Template contains the optional Modeling definition Response Set.
You use the Checklist Template Configuration grid to add items to the checklist template. You must specify 
a response entry for every checklist item.
At least one item must be defined in the Checklist Template Configuration grid before you can save the 
Checklist Template.
These are valid response entries that you can specify for a checklist item:
•
A response entry control (for example, check box or picklist) associated with a response set, if 
appropriate
•
A required Comments box
•
A response entry control associated with a response set, if appropriate, and an optional or 
required Comments box
This list  describes settings in the configuration grid for certain types of checklists. If you want to define a 
checklist item:
•
in the format of a basic to-do list (a single check box or radio button for the item), select either 
Check Box or Radio Button for the response entry control and leave the response set blank.
•
for which comments are the only response needed for the item, select Comments Required from 
the Comments Entry column. Leave all response columns blank for the checklist item.
Additionally, the application performs these validations and you must:
•
Specify a response entry control if you specify a response set.
•
Associate a response set with the picklist if you select Picklist as the response entry control.
•
Select a response entry control at minimum when the Response Entry Required check box is 
selected on the Checklist Template Configuration grid. The application prompts you to select a 
response entry control.
Use the Up and Down arrows to set the order of the checklist items when adding checklist items in the 
Checklist Template Configuration grid.
8-54
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Specifying the Layout for Checklist Items
You can specify the layout of the individual checklist items when configuring a checklist template. The 
Response Layout option enables you to specify the position of the response set in relation to the checklist 
item. Options include the following: 
•
Below the checklist item - vertical (the default)
The application displays the responses below the checklist item in a 3-column format. If there are 
more than three responses in the response set, the responses wrap to the next line.
•
Below the checklist item - horizontal
The application displays the responses below the checklist in a single column.
•
Right of the checklist item
The application shortens the width of the display area for the checklist item, wrapping the text if 
necessary, and displays the response set to the right of the item. If there are more responses than  
fit on one line, the responses wrap to the next line of the response set display area. (The number 
of responses per line is configurable.)
•
Left of the checklist item
This option is available only if you do not select a response set; therefore, only a single response 
entry control appears to the left of the checklist item.
Note:
When you have no defined response set and your Response Layout value is Left of the 
checklist item, the application changes the value of the Response Layout to the default 
value, Below the checklist item - Vertical, if you select a response set. 
If you choose to include a Comments text box with a check list item, the Comments text box always 
appears below the responses.
Release 2510+ Rev. 1
Modeling User Guide
8-55
Chapter 8: Quality Model Definitions
Checklist Template Page
This image shows an example of the Checklist Template page.
Checklist Template Page Field Definitions
This table defines the fields unique to the Checklist Template page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field 
Definition
Type
Details
Engineering 
Change Order
Engineering change order assigned to this revision. You can enter a 
maximum of 30 characters.
Optional
Checklist 
Instructions
Instructions for completing the checklist (up to 255 characters). These 
instructions  appear on the Checklist tab when managing an event 
record. The field does not appear on the Checklist tab  if you do not 
enter anything here. 
Optional
Checklist 
Template 
Configuration 
grid
Grid that enables you to add items to, or delete items from, the 
checklist. The application displays items in the order added, but you 
can use the Move Row arrows to change the display order. The 
columns displayed in the grid are identical to those displayed in the 
Checklist Item pop-up. Refer to "Checklist Item Add  Pop-Up  Field 
Definitions" for  information. 
Required
8-56
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Checklist Item Add  Pop-Up
The Checklist  Item Add pop-up  appears when you click the Add button on the Checklist Template 
Configuration grid on the Checklist Template page. Use the Checklist Item Add pop-up  to add checklist 
items to the template.
This image shows an example of the Checklist Item Add pop-up.
Checklist Item Add  Pop-Up  Field Definitions
This table defines the fields on the Checklist Item Add pop-up. 
Field 
Definition
Type
Checklist Item
Task to perform or question to answer.
Required
Response Set
Response set to associate with the checklist item. Response sets are 
defined in Modeling.
Optional
Release 2510+ Rev. 1
Modeling User Guide
8-57
Chapter 8: Quality Model Definitions
Field 
Definition
Type
Response Entry 
Control
Setting that determines how the application displays the response set 
options. Possible controls include:
•
Radio Button
•
Check Box
•
Picklist
Optional
Comments Entry
Setting that indicates whether a Comments text box is displayed, and 
if displayed, whether the user is required to enter comments. Options 
include the following:
•
None, the default, which means the application does not 
display a Comments text box.
•
Required, which means the application  displays a Comments 
text box and requires the user to type comments.
•
Optional, which means the application displays a Comments 
text box but does not require the user to type comments.
Optional
Response Layout
Setting that specifies where the application should display responses 
in relation to the checklist item. Options include the following:
•
Below the checklist item - Vertical (the default)
•
Below the checklist item - Horizontal
•
Right of the checklist item
•
Left of the checklist item
Note: The Left of the checklist item option is not available for 
selection here if you select a response set. 
Optional
Response Entry 
Required
Check box indicating that a user must select a response for the 
checklist item.
Optional
How to Define a Checklist Template
Follow these steps to define a Checklist Template:
1.
Open the Checklist Template page. The Checklist Template page appears within the Modeling 
page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this checklist template in the Checklist Template field.
4.
Enter the revision of this object in the Revision field.
5.
Add checklist items using the “How to Add Checklist Items to a Checklist Template” procedure.
6.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
7.
Click Save. The application saves the modeling object and displays a success message.
8-58
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
How to Add Checklist Items to a Checklist Template
Follow these steps to add checklist items to a Checklist Template:
1.
Perform the "How to Define a Checklist Template" procedure.
Or
Select an existing Checklist Template instance.
2.
Locate the Checklist Template Configuration grid and click  Add new row. The Add pop-up 
appears.
3.
Enter a checklist question or task in the Checklist Item field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click OK. The application closes the Add pop-up and displays the checklist item in the Checklist 
Template Configuration grid.
6.
Repeat steps 2-5 for each additional checklist item you want to add.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
8-59
Chapter 8: Quality Model Definitions
Defining Numbering Rules
A Numbering Rule is a configurable numbering scheme that assigns unique tracking numbers to quality 
records  and containers. Typically, an organization defines and assigns a numbering scheme to these 
entities. The application applies the appropriate numbering scheme and assigns the next available ID or 
number to the appropriate quality record or container.
When Defining Numbering Rules for Quality Records
Siemens recommends you define a unique numbering rule for each type of quality record (event or 
nonconformance) so that each record type will have a unique identifier. The application uses the 
numbering rules specified on the Organization modeling object to assign identifiers to quality records.
Numbering Rule is an optional field in the Organization modeling definition.
Refer to the Opcenter Execution Medical Device and Diagnostics Event Management User Guide or the 
Opcenter Execution Core Event Management User Guideas well as the Opcenter Execution Medical Device 
and Diagnostics Nonconformance Management User Guide or the Opcenter Execution Core 
Nonconformance Management User Guide for information on recording events and nonconformances.
When Defining Numbering Rules for Containers
Every container must have a unique container name.  Container names can be generated manually or 
automatically through numbering rules assigned to modeling objects. You create a numbering rule using 
the Numbering Rule modeling page. You assign a numbering rule by selecting it from the optional 
Numbering Rule field on one or more of these modeling objects:
•
Container Level
•
Mfg Order
•
Product
•
Product Family
•
Factory
Note:
The list above reflects the order of selection preference. For example, the application chooses 
the numbering rule on Container Level if both Container Level and Product are configured with 
a numbering rule.
Shop floor users have the option to generate container names automatically when starting parent and 
child containers, splitting containers, and splitting quantities. Refer to the Opcenter Execution Medical 
Device and Diagnostics Shop Floor User Guide or the Opcenter Execution Core Shop Floor User Guide for 
information on generating container names automatically.
When Choosing a Numbering Rule Type
You must choose a numbering rule type when defining numbering rules. There are two types, and each 
has advantages and disadvantages. The two numbering rule types are:
•
High Volume/Skip
8-60
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
•
Low Volume/No Skip
You cannot change the numbering rule type after you save the instance. The application disables the 
Numbering Rule Type field when you click the Save button. The Numbering Rule Type field remains 
disabled when you create a new instance by clicking the Copy button. 
High Volume/Skip Features
Use the High Volume/Skip numbering rule type when creating numbering rules for high volume items for 
which strict adherence to sequential numbers is not a consideration.
Advantages 
The High Volume/Skip numbering rule type advantages include:
•
Allows skipping of sequence numbers
•
Intended for high volume of accesses to the numbering rule
•
Possibility of access collisions is minimized
•
Last Assigned Sequence number can be modified
•
Allows use of split quantanties across multiple containers
Disadvantages 
The High Volume/Skip numbering rule type disadvantages include:
•
Cannot guarantee sequential sequence numbers
•
Not recommended for use when sequential sequence numbers are required
Recommended Use 
The High Volume/Skip numbering rule type is best for high volume requests for numbers and is 
recommended for material container auto numbering.
Low Volume/No Skip Features
Use the Low Volume/No Skip numbering rule type when creating numbering rules for low volume items 
for which strict adherence to sequential numbers is essential.
Advantages
The Low Volume/No Skip numbering rule type advantages include:
•
Does not allow skipping of sequence numbers
•
Last Assigned Sequence number can be modified
Disadvantages
The Low Volume/No Skip numbering rule type disadvantages include:
•
Possibility for access collisions exist
•
Not recommended for high volume requests for auto numbers from the numbering rule
Release 2510+ Rev. 1
Modeling User Guide
8-61
Chapter 8: Quality Model Definitions
•
Not recommended for split quantities across multiple containers
Recommended Use 
The Low Volume/No Skip numbering rule type is best for low volume requests for auto numbers and is 
recommended for quality records (Events).
Note:
You must use the High Volume/Skip numbering rule to perform split quantity transactions for 
multiple containers and generate the names automatically.
Prefix and Suffix Format Requirements
Numbers must be 30 characters or less, including any prefix or suffix and the sequence number. The 
number generated is calculated as follows:
Number = Prefix (if any) + Sequence Number (Required) + Suffix (if any)
For example: EVENT-ORG15-00000001-2014
The Prefix and Suffix fields can be used for either literal or unified expression syntax entries.
Both require very specific formats, for example:
•
A literal prefix may be defined as "ABCCorp_" or "_Smith." Double quotes around the entry are 
required.
•
Unified expression syntax might be used to create a dynamic prefix or suffix, such as:
•
Prefix = "(<Organization.Name>"
•
Suffix ="_"+StrSubstring(String(TruncateTime(GMTToLocal(SetSystemDateGMT()))),
(StrLength(String(TruncateTime(GMTToLocal(SetSystemDateGMT()))))-4),4)
This yields the following scheme: Event (Corporate00001_2014 started on 02/06/2014 3:21:00 PM.
Refer to  the Opcenter Execution Medical Device and Diagnostics Designer User Guide or the Opcenter 
Execution Core Designer User Guide for  information on unified expression syntax.
Rule Based vs Prefix-Based Sequences
All numbering rules include a sequence. By default, the application increments a rule’s Last Assigned 
Sequence value each time that rule is used to generate a new value. You can override this rule-based 
sequencing with prefix-based sequencing by selecting the check box labeled Use Prefix Based Last 
Assigned Sequence on the Numbering Rules modeling page.
Prefix-based sequencing makes sense for numbering rules configured with unified expressions that 
dynamically generate prefixes. The application assigns a starting sequence value each time a numbering 
rule generates a unique prefix for the first time.  If a numbering rule subsequently generates the same 
prefix, the application increments the last assigned sequence for that prefix when generating the 
container name.
Important:
Any numbering rule could theoretically generate the same prefix as another numbering 
rule. The application increments a prefix-based sequence regardless of the rule that 
generated it. This enables one rule to be configured for multiple manufacturing orders, 
8-62
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
products, and so on, with a unified expression dynamically identifying information such 
as product name and manufacturing order name in the prefix.
Prefix-Based Container Name Example
Assume you create a numbering rule with the following field configurations:
Prefix
Use Prefix Based Last Assigned 
Sequence
Sequence Length
Details.Product.Name+”-“
Optionally Checked
4
The table below shows the container names that would be generated for assumed shop floor transactions 
if the above rule is assigned to ProductA and ProductB.
Transaction
Resolved Prefix
Container Names
Start 4 containers of ProductA.
ProductA-
ProductA-0001
ProductA-0002
ProductA-0003
ProductA-0004
Start 4 containers of ProductB.
ProductB-
ProductB-0001
ProductB-0002
ProductB-0003
ProductB-0004
Start 2 containers of ProductA.
ProductA-
ProductA-0005
ProductA-0006
Material Container Numbering Rule Execution
The numbering rules for material containers that you create on the Numbering Rules page, and assign on 
the  Mfg Order, Product, Product Family, Container Level, or Factory objects, are generated and assigned 
on the Carrier Management pages when you select the Automatically Generate Names check box on those 
pages. This number is then used to track the progress of the container.
Release 2510+ Rev. 1
Modeling User Guide
8-63
Chapter 8: Quality Model Definitions
Numbering Rule Page
This image shows an example of the Numbering Rule page.
Numbering Rule Page Field Definitions
This table defines the fields unique to the Numbering Rule page. 
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
Details
8-64
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Field
Definition
Type
Numbering Rule Type
List containing the numbering rule types for selection. Possible 
values include: 
•
High Volume/Skip
•
Low Volume/No Skip
Required
Prefix
Prefix to prepend to the sequence number. The prefix can 
support both static string text and unified expression syntax to 
generate dynamic text. An example of a static string text prefix 
is "PE-ORG15."
You must include double quotes around your entry as shown in 
the example.
Note: This field is required when Use Prefix Based Last Assigned 
Sequence is selected.
Optional
Suffix
Suffix to append to the sequence number. The suffix can support 
both static string text and unified expression syntax to generate 
dynamic text. An example of a static string text suffix is a four-
digit year "2014" or a product name "BPMON." You must include 
double quotes around your entry as shown in the examples.
Optional
Use Prefix Based Last 
Assigned Sequence
Check box indicating whether to use prefix-based sequencing. 
Selecting the check box results in sequences numbers being 
tracked and incremented within each unique prefix generated by 
a numbering rule.
Optional
Use Hexadecimal 
Value
Check box indicating whether to use hexadecimal numbering for 
the sequence.
Note: This option works with both rule-based and prefix-based 
sequencing.
Optional
Use AlphaNumeric 
Value   
Check box indicating whether to use alphanumeric numbering 
for the sequence.
Note: This option works with both rule-based and prefix-based 
sequencing.
Optional  
Release 2510+ Rev. 1
Modeling User Guide
8-65
Chapter 8: Quality Model Definitions
Field
Definition
Type
Numbering Rule 
Options  
Setting that controls  numbering rule behavior when the 
maximum sequence value is reached. Numbering rule options 
include the following:
•
Rollover - The sequence restarts after reaching a 
predefined limit. When the maximum sequence value is 
reached, the numbering rule starts to generate 
ascending values from the value, indicated in the Last 
Assigned Value field.
 Note: If Rollover is selected, an error will occur if a 
duplicated container name is detected.
•
Stop - The sequence stops at a predefined limit. The 
numbering rule cannot generate more values after 
reaching the maximum value.
•
Continue - The sequence increments without bound. 
The numbering rule continues to generate values after 
reaching the maximum value.
Note: This field is enabled when the Use AlphaNumeric Value 
check box is selected.
Optional  
Max Value
Limits the maximum sequence value that can be generated. The 
input value must be an integer for sequences that do not use 
hexadecimal values and must be hexadecimal for sequences that 
do use hexadecimal values.
Optional
Last Assigned 
Sequence
Last sequence number assigned to a quality record. The 
application calculates the next sequence number to assign by 
incrementing this number by one. The default value is 0.
Note: This field is disabled when Use Prefix Based Last Assigned 
Sequence is selected.
Required
Sequence Length
Desired length of the sequence number. The maximum length of 
a calculated sequence number is 30 characters, assuming the 
prefix and suffix are not used.
Required
Exclude Letter List  
Grid listing the letters that must be excluded from alphanumeric 
numbering for the sequence.  
Note:Letters I, O, Q, Z are excluded by default.
Note:This field is enabled when the Use AlphaNumeric Value 
check box is selected.  
Optional  
How to Define a Numbering Rule Using Default or Rule-Based Sequencing
Follow these steps to define a Numbering Rule using default rule-based sequencing:
1.
Open the Numbering Rule page. The Numbering Rule page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for the numbering rule in the Numbering Rule field. 
4.
Select a Numbering Rule Type.
8-66
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
5.
Enter a value in the Last Assigned Sequence field.
6.
Enter a value in the Sequence Length field.
7.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
8.
Click Save. The application saves the modeling object and displays a success message.
How to Define a Numbering Rule Using Prefix-Based Sequencing
Follow these steps to define a Numbering Rule using prefix-based sequencing:
1.
Open the Numbering Rule page. The Numbering Rule page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for the numbering rule in the Numbering Rule field. 
4.
Select a Numbering Rule Type.
5.
Enter a unified expression in the Prefix field.
6.
Select the check box labeled Use Prefix Based Last Assigned Sequence. The application makes 
Prefix a required field and disables the Last Assigned Sequence field.
7.
Enter a value in the Sequence Length field.
8.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
9.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
8-67
Chapter 8: Quality Model Definitions
Defining Smart Scan Rules
Smart Scan Rules are used in Rule-Based Smart Scanning—an alternative to default Smart Scanning. A 
Smart Scan Rule enables you to define data patterns that identify data elements within a  barcode. The rule 
can be configured with processing instructions including the automated execution of page actions such as 
a button click that would otherwise be performed manually by the operator.
Understanding Patterns
The application uses the pattern or patterns in a Smart Scan Rule to interpret barcode data. The patterns 
must conform to the barcodes you expect to process.
Example
Note this example scenario:
1.
The application is configured with a Smart Scan Rule that has the following patterns:
2.
An operator scans a barcode into an application page. The page contains various fields including a 
Container identifier and a Save button. The barcode contains the  string:  CON-12348976. It also 
contains a string with the characters Hold  indicating that the page data should be saved for 
completion at a later date. 
3.
The application evaluates the barcode against the Smart Scan Rule and executes the following 
logic:
a.
Finds the first pattern which resolves to three letters, followed by a hyphen, followed by 
eight numeric digits.
b.
Extracts the data string and places it into the field on the page corresponding to the pattern's 
Smart Scan Type—Container.
c.
Removes the data string because the Remove on Match is selected for the pattern.
d.
Finds the pattern of four characters—Hold.
e.
Extracts the Hold string data from the barcode.
f.
Automatically submits the onClick action of the Save button due to the Action Identifier 
being Save.
Note:
The example is just one of many. Another factory could have a totally different pattern con-
figured for their Container identifier.
8-68
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Elements of a Pattern
This table describes the elements of a pattern.
Element
Description
Constants
Letters, numbers, and special characters
Wildcards
•
? A question mark matches any single alphanumeric character.
•
 * An asterisk matches zero or more characters.
•
 ! An exclamation point matches a single numeric character.
•
 | A pipe matches a single alpha character .
[ ]
Brackets indicate that what is inside contains a value that can be extracted.
Specifying ASCII Characters
You can include characters in a pattern by specifying their decimal ASCII codes (000 to 255). The backslash (\) 
is used to indicate that the next 1 to 3 digits are to be interpreted as an ASCII code. For example, the code for 
capital letter “A” is 65. So if the string \65 or \065 appears in a pattern, the smart scan processor will treat it as 
“A.” Since the backslash has special meaning to the smart scan processor, you cannot include it directly in a 
pattern. You must instead use its ASCII code 92. Any ASCII codes in the pattern are resolved to their character 
values prior to matching against the barcode.
Note these examples:
Barcode
Pattern
Resolved Pattern
Extracted Data
P\NPCB-1234
P\092N[PCB-!!!!]
P\N[PCB-1234]
PCB-1234
APPCB-1234
\65P[PCB-!!!!]
AP[PCB-!!!!]
PCB-1234
APPCB-1234
AP
[\80\67\66-!!!!]
AP[PCB-!!!!]
PCB-1234
Pattern Order
Barcodes can contain single or multiple values of information. The order in which barcodes are tested is 
significant, and can yield varying results. Different barcode patterns might yield the same result.
 
Example
You want to recognize the part number PAA-123456. The barcode is characterized by:
•
The letter P  indicates part number. This is optional and does not have to be specified.
•
The two characters following the P, if there is a P, are letters.
•
The six characters after the hyphen (-) are numeric.
All of the patterns in the following table yield the correct results when matching PAA-123456.
Release 2510+ Rev. 1
Modeling User Guide
8-69
Chapter 8: Quality Model Definitions
Pattern
Why It Matches
P[*]
A P followed by zero or more characters.
[?????????]
P is optional. The 10 question marks indicate any ten alphanumeric characters.
P[??-!!!!!!]
P followed by any two alphanumeric characters followed by a hypen followed by six 
numeric digits.
Testing Patterns
You can test a Smart Scan Rule to ensure that it works as intended by using the Test section of the Smart 
Scan Rule page. This enables you to test individual patterns as well as the sequence of multiple patterns. 
Please be aware that the Smart Scan Type Action cannot be tested using the Smart Scan Rule page. 
Smart Scan Rule Page Field Definitions
This table defines the fields unique to the Smart Scan Rule page. 
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
General
Preamble
Single character indicating whether the barcode is a smart 
barcode. When the system detects a preamble, it identifies 
the barcode as smart and strips the preamble before 
continuing to read the barcode.
Note: If Preamble is left blank, the application checks the 
Preamble in Portal Studio Settings for Smart Scanning.
Optional
Terminator
Control character that marks the end of the smart barcode. 
This triggers the system to stop reading and process the 
barcode based on defined patterns.
Note: If Terminator is left blank, the application checks the 
Terminator in Portal Studio Settings for Smart Scanning.
Note: Siemens recommends that you use the Tab key as 
the default terminator. Refer to the Smart Scanning 
appendix in the Opcenter Execution Core System 
Administration Guide.
Optional
Smart Scan Pattern 
grid
Contains one or more patterns that the application will try 
to match when evaluating a scanned barcode.
Optional
Arrows to move a pattern up or down to resequence the 
order in which the application looks for the pattern.
Note: The arrow icon does not appear on a grid with no 
patterns.
Optional
8-70
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
Field
Definition
Type
Pattern
A series of characters or types of characters for which the 
application searches within the barcode.
Optional
Remove on 
Match
Indicates whether the data extracted by the pattern should 
be removed if found within the barcode. Doing so can 
simplify subsequent patterns for rules that extract multiple 
data fields.
Optional
Smart Scan 
Type
Contains either a category of field data known by the 
application such as a Container field 
OR
 
The value "Action" indicating that the application should 
automatically execute the page action entered into the 
Action Identifier if and when the corresponding pattern is 
found on the barcode.
Optional
Is Active
Specifies whether the application should attempt to 
process the pattern entry, in other words, whether the 
pattern is enabled.
Optional
Is Regex
Indicates that the pattern uses Regular Expression syntax.
Optional
Action 
Identifier
Identifies the control on the page that triggers the desired 
action. This is done in one of two ways, and the method 
used depends on the setting of the Command Bar Action 
Field:
•
When Command Bar Action is false, the system 
will expect the specified value to be a valid CSS 
selector that finds the control.
•
When Command Bar Action is true, the system 
will look for a Command bar button where the 
specified value matches the value of a <div> 
element using class= “caption-text.”
In both cases, the Developer Tools feature of a browser 
can be used to help determine correct input for this field 
value.
Note: A value with a # prefix indicates that the value is a 
control identifier.
Note: You can call a custom JavaScript function if you 
name the Action Identifier the same name as the added 
JavaScript function.
Optional
Command 
Bar Action
Boolean indicating whether the Action specified in the 
Action Identifier is located on the command bar of 
the Portal page.
Optional
Test
Section to test the Smart Scan Rule and its pattern or 
patterns.
Optional
Release 2510+ Rev. 1
Modeling User Guide
8-71
Chapter 8: Quality Model Definitions
Field
Definition
Type
Smart Scan Value
Barcode to test.
Optional
Apply Rule
Click to apply the rule to the barcode entered into the 
Smart Scan Value.
Optional
Extracted Values 
grid
Results of the Smart Scan Rule test.
Display Only
Smart Scan 
Type
An entity or page field into which an extracted value will 
be placed.
Display Only
Value
The value that will be placed into the entity or Smart Scan 
Type.
Display Only
How to Define a Smart Scan Rule
Follow these steps to define a Smart Scan Rule:
1.
Open the Smart Scan Rule page. The Smart Scan Rule page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a preamble value in the Preamble field if the default Preamble in Portal Settings for Smart 
Scanning is not applicable to this rule. 
4.
Enter the terminator characters in the  Terminator field if the default Terminator in Portal Settings 
for Smart Scanning is not applicable to this rule. .
5.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
6.
Click Save. The application saves the modeling object and displays a success message.
How to Add Smart Scan Patterns to a Smart Scan Rule
Follow these steps to add Smart Scan Patterns to a Smart Scan Rule:
1.
Perform the "How to Define a Smart Scan Rule" procedure.
Or
Select an existing Smart Scan Rule instance.
2.
Click Add new row on the Smart Scan Pattern grid. A new row appears.
Note:
An up-down arrow icon appears in the first column enabling you to resequence 
patterns when there are multiple patterns on the grid.
3.
Enter the characters identifying the pattern in the  Pattern field.
4.
Select or enter data into the remaining fields on the row according to your business 
requirements.
5.
Repeat steps 2-4 to add additional Smart Scan Patterns.
6.
Click Save. The application displays a success message indicating the modeling object was 
updated.
8-72
Modeling User Guide
Release 2510+ Rev. 1
Chapter 8: Quality Model Definitions
How to Test a Smart Scan Rule
Follow these steps to test a Smart Scan Rule:
1.
Open the Smart Scan Rule page. The Smart Scan Rule page appears within the Modeling page.
2.
Expand the Test section.
3.
Enter a barcode to be tested in the Smart Scan Value field. 
4.
Click  Apply Rule. The application searches the barcode for each pattern in the rule in the order 
in which they appear on the page. The application populates the Extracted Values grid with each 
Smart Scan Type (field entity), and the value that would be extracted into that entity based on 
the configuration of matched patterns within the Smart Scan Rule.
Note:
The Smart Scan Type of Action cannot be tested using the Smart Scan Rule page. 
How to Use a Custom JavaScript Function
Follow these steps to use a custom JavaScript function:
1.
Add a JavaScript function to Smartscan.js, located in \Camstar Portal\Scripts\User. The JavaScript 
function must be defined in the same manner as the “exampleFunction()” defined in 
SmartScan.js. The JavaScript function may not be defined at the global scope.
2.
Perform the "How to Add Smart Scan Patterns to a Smart Scan Rule" procedure.
Note:
To use a JavaScript function, the pattern must be "Action" type.
3.
The Action Identifier name must match the JavaScript function name added in Step 1.
4.
Scan a barcode containing the Action Pattern configured in Step 2.  The JavaScript function will 
be called and any functionality within will be executed.
Release 2510+ Rev. 1
Modeling User Guide
8-73
Chapter 9: Electronic Signatures
Introduction
An Electronic Signature is an electronically stored record that denotes accountability for the performer of a 
particular activity. Its use is tracked through an audit trail. You use an electronic signature as the 
equivalent of a handwritten signature.
According to the Food and Drug Administration (FDA), electronic signatures are intended to be the 
equivalent of handwritten signatures, initials, and other general signings required by predicate rules. Part 
11 signatures include electronic signatures that are used, for example, to document the fact that certain 
events or actions occurred in accordance with the predicate rule (for example, approved, reviewed, and 
verified).
For example, you can define an electronic signature requirement that automatically deploys an electronic 
signature pop-up during the packing transaction. When you establish this requirement, a shop floor user 
cannot execute further transactions until a signer with appropriate authority has provided a signature 
approving the transaction.
Each captured signature is tracked and stored in transaction history. Each entry contains the signature 
requirements and how they were met, along with the local time and GMT. Consequently, you can 
generate a complete audit trail and device history record (DHR) from this data.
You must configure electronic signatures in your information model in order to use electronic signature 
verification for your shop floor transactions.
In This Chapter
This chapter contains these topics:
•
Modeling Sequence
•
Defining Roles for Electronic Signatures
•
Defining Electronic Signature Meanings
•
Defining Electronic Signature Role Groups
•
Associating Employees with Electronic Role Groups
•
Defining Cosignature Reasons
•
Defining Electronic Signature Requirements
•
Associating Electronic Signature Requirements with Modeling Objects
•
Electronic Signatures and Compound Transactions
Release 2510+ Rev. 1
Modeling User Guide
9-1
Chapter 9: Electronic Signatures
Modeling Sequence
This illustration represents the modeling sequence for defining process computations, user data collection 
definitions, and electronic procedures.
9-2
Modeling User Guide
Release 2510+ Rev. 1
Chapter 9: Electronic Signatures
Defining Roles for Electronic Signatures
A Role (created in Opcenter EX MDD or Opcenter EX CR) defines a job function with an inherent set of 
permissions that grants access to all or to parts of the application. You must create a role for each required 
electronic signature. Every authorized employee has an assigned set of roles. For a signature to be 
accepted, the employee must be assigned a role for each required electronic signature.
You can require more than one signature for a single role. For example, you might require four signatures 
for constructing a box: Box Builder, Box Filler, Box Sealer, and Box Inspector.
A supervisor might be responsible for inspecting boxes after they are packed. In order for the supervisor to 
be able to provide the Box Inspector signature, the supervisor must be assigned the Box Inspector role.
When Defining a Role for an Electronic Signature
Role is referenced by ESigRoleGroup.
Role Page
This image shows an example of the Role page.
Release 2510+ Rev. 1
Modeling User Guide
9-3
Chapter 9: Electronic Signatures
Role Page Field Definitions
This table defines the fields on the Role page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
Details
Permissions
Permission Type Filter
List that enables you to filter the category of available 
permissions for possible assignment to the role. The 
application uses the permission type to determine the 
permissions available for assignment and their access 
modes.
For example, if you select Container, the application 
updates the Available Permissions list to display container-
related transactions. When you add an available permission 
to the Assigned Permissions grid, the grid displays the 
applicable access modes for that permission.
Optional
Assigned Permissions 
grid
Grid displaying the permissions assigned to this role and 
the applicable access modes for each permission. By 
default, the application selects all access modes when you 
add a new permission. 
Use this grid to select the access modes for each permission 
type selected.
Optional
Available Permissions 
grid
List of permissions based on the permission type filter 
selected. Only permissions that have not already been 
assigned are displayed for selection.
Optional
Membership
Employee Role 
Memberships grid
Grid displaying user membership within the role. For each 
user, the grid displays the organization for which the role is 
valid and whether the role is propagated to the 
organization's sub-organizations. Use this grid to manage 
user membership.
Optional
Employee
Name of the employee to whom the role is assigned.
Optional
Organization
Name of the organization for which the role is assigned.
Optional
Propagate
Check box indicating that the role is valid for all of the 
organization's sub-organizations.
Optional
9-4
Modeling User Guide
Release 2510+ Rev. 1
Chapter 9: Electronic Signatures
Role Page Button Definitions
This table defines the buttons on the Role page.
Button
Click this button to . . .
Remove
Remove selected permissions from the Assigned Permissions grid. Removed 
permissions appear in the Available Permissions grid.
Add
Move selected permissions from the Available Permissions grid to the 
Assigned Permissions grid.
How to Define a Role for an Electronic Signature
Follow these steps to define a role for an electronic signature:
1.
Open the Role page. The Role page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter the name of the role in the Role Name field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
How to Add Permissions to a Role for an Electronic Signature
Follow these steps to add permissions to a role for an electronic signature:
1.
Perform the "How to Define a Role for an Electronic Signature" procedure.
Or
Select an existing Role instance.
2.
Select a category of permissions as a filter from the Permission Type Filter list. The permissions 
associated with the filter are displayed in the Available Permissions grid.
3.
Select each permission (transaction) that will require an electronic signature and then click the 
Add button. The selected permissions are moved to the Assigned Permissions grid.
4.
Clear the associated access mode check boxes if you do not want the user to have all of the 
accesses indicated.
Note:
When you select another permission filter, the previously-selected permissions 
disappear from the Assigned Permissions grid. However, after completing the 
permission assignments and clicking Save, all permissions you assigned are saved.
5.
Repeat steps 2-4 to add more permissions to this role.
6.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
9-5
Chapter 9: Electronic Signatures
How to Add Memberships to a Role for an Electronic Signature
Follow these steps to add memberships to a role for an electronic signature:
1.
Perform the "How to Define a Role for an Electronic Signature" procedure.
Or
Select an existing Role instance.
2.
Click Add new row on the Membership grid. Blank fields appear for you to define a new 
instance.
3.
Select an Employee from the list.
4.
Select the organization for which this role will be valid for the employee from the Organization 
list.
5.
Select the Propagate check box if you want the application to make this role valid for all of the 
organization's sub-organizations.
6.
Repeat steps 2-5 to assign this role to another employee.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
9-6
Modeling User Guide
Release 2510+ Rev. 1
Chapter 9: Electronic Signatures
Defining Electronic Signature Meanings
An Electronic Signature (ESig) Meaning represents the purpose and accountability of a signature. It 
enables you to establish what process is being verified when an electronic signature is applied. 
The ESig Meaning page enables you to define a meaning for each required signature. For example, if you 
want a Packing Supervisor with a role of Box Inspector to provide an electronic signature to verify that 
boxes have been filled correctly, create an ESig meaning of Box Verified. When the Box Inspector provides 
a signature, it means that the presence of his or her signature indicates that the task was verified.
When Defining an Electronic Signature Meaning
ESig Meaning is a required field in the ESig Requirement modeling definition. 
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.  
How to Define an Electronic Signature Meaning
Follow these steps to define an Electronic Signature Meaning:
1.
Open the ESig Meaning page. The  ESig Meaning page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter the name of the meaning in the ESig Meaning field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
9-7
Chapter 9: Electronic Signatures
Defining Electronic Signature Role Groups
An Electronic Signature (ESig) Role Group is a group of similar or related roles, which can then be assigned 
to an employee to provide the employee with multiple electronic signature roles. A role group can consist 
of individual entries of roles and previously defined role  groups. 
For example, if Mary Smith is required to provide signatures to verify that boxes are filled and that boxes 
are sealed, you can create a Box Operations role group, and assign the Box Filler and Box Sealer roles to 
that group. Then, you can assign Mary Smith to the Box Operations Role Group.
When Defining ESig Role Groups
Esig Role Group is an optional modeling definition on Employee.
Esig Role Group contains the optional modeling definition, Role.
The Resolved Entries button enables you to display a list of all of the values specified in the entries list for 
this group and all of the nested groups.
This image shows an example of the Resolved Entries pop-up.
9-8
Modeling User Guide
Release 2510+ Rev. 1
Chapter 9: Electronic Signatures
ESig Role Group Page
This image shows an example of the ESig Role Group page.
ESig Role Group Page Field Definitions 
This table defines the fields on the ESig Role Group page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
Details
Entry Type
Name of the type of objects contained in this object group.
Display 
Only
Entries 
grid
Grid listing the roles assigned to this group. The list of available roles is 
displayed from the roles already defined on the Role page.
Optional
Groups 
grid
Grid listing other role groups assigned to this group. The list of available role 
groups is displayed from the other role groups already defined on the ESig 
Role Group page.
Optional
How to Define an ESig Role Group
Follow these steps to define an Electronic Signature Role Group:
1.
Open the ESig Role Group page. The ESig Role Group page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter the name of the group in the ESig Role Group field.
Release 2510+ Rev. 1
Modeling User Guide
9-9
Chapter 9: Electronic Signatures
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
How to Add Entries to an ESig Role Group
Follow these steps to add entries to an ESig role group:
1.
Perform the "How to Define an ESig Role Group" procedure.
Or
Select an existing Esig Role Group instance.
2.
Click Add new row on the  Roles grid. A new row appears.
3.
Select a role from the  list.
4.
Repeat steps 2–3 to add  additional roles to the grid.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Add Groups to an ESig Role Group
Follow these steps to add groups to an ESig role group:
1.
Perform the "How to Define an ESig Role Group" procedure.
Or
Select an existing Esig Role Group instance.
2.
Click Add new row on the Groups grid. A new row appears.
3.
Select a group to add (as a subgroup) from the  list. 
4.
Repeat steps 2-3 to add  additional groups  to the grid.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
9-10
Modeling User Guide
Release 2510+ Rev. 1
Chapter 9: Electronic Signatures
Associating Employees with Electronic Role Groups
You must associate your employees with electronic signature role groups to enable them to provide 
electronic signatures. When you associate an employee with the appropriate electronic signature role 
group, the employee can provide an electronic signoff for all transactions mapped to the Role.
For example, if George Jackson is required to verify that boxes are packed and sealed correctly, you can 
assign George to the Box Verifier electronic signature role group. Assuming that the Box Verifier role group 
contains a Box Sealer and a Box Inspector role, George will have the appropriate authority to provide an 
electronic signature for those requirements.
When Associating Employees with Electronic Role Groups
You can assign an electronic signature to each employee on the Employee page after the electronic 
signature role group has been defined through the ESig Role Group.
Employee Page
This image shows an example of the Employee page.
Employee Page Field Definitions
Refer to "Defining Employees" for information on the Employee page and how to define employees.
Release 2510+ Rev. 1
Modeling User Guide
9-11
Chapter 9: Electronic Signatures
How to Associate an Employee with an Electronic Signature Role Group
Follow these steps to associate an employee with an electronic signature role group:
1.
Open the Employee page. The Employee page appears within the Modeling page.
2.
Click an existing Employee definition. 
Or
Click New to create a new Employee definition. Blank fields appear for you to define a new 
instance.
3.
Enter the Employee's name in the Name field, if you are adding a new employee.
4.
Select an ESig Role Group  from the list.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
9-12
Modeling User Guide
Release 2510+ Rev. 1
Chapter 9: Electronic Signatures
Defining Cosignature Reasons
A Cosignature (ESig Cosign) Reason  defines the reason that a cosignature is allowed when the person who
 normally signs cannot be verified for some reason. This applies in a situation where the primary signer 
cannot be authorized due to authentication issues or password problems. In such a situation, the 
cosignature is added to the ESig Capture pop-up with the signature and password of the primary signer. 
The presence of the cosignature indicates approval of the primary (default) signature. 
For example, if your Packing Supervisor, George Jackson, cannot be authenticated because his password 
has expired, the Area Supervisor can provide a cosignature to authorize the signature of George Jackson. 
You could set up a cosignature reason of Password Problems to represent such a situation. When the ESig 
Capture pop-up appears during the shop floor transaction, the Area Supervisor would enter his or her 
signature along with George Jackson’s signature, and indicate the Password Problems/Supervisor Override 
reason for the cosignature. 
When Defining a Cosignature Reason
The option to provide a cosignature does not appear on transactions that have not been configured to 
accept cosignatures.
Cosign reasons are referenced by the ESig Requirement modeling object, but only if you specify a cosigner 
role for a signature requirement.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define an Electronic Signature Cosign Reason
Follow these steps to define an Electronic Signature Cosign Reason:
1.
Open the ESig Cosign Reason page. The ESig Cosign Reason page appears within the Modeling 
page.
2.
Click New. Blank fields appear for you to define a new instance.
3.
Enter the name of the E Sig Cosign Reason in the E Sig Cosign Reason field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
9-13
Chapter 9: Electronic Signatures
Defining Electronic Signature Requirements
Electronic Signature Requirements enable you to group various electronic signature components into a 
single definition that can be associated with a shop floor transaction. 
For example, if you require an electronic signature to verify that boxes have been filled and sealed 
correctly, you can create a requirement called Box Verification, which would define these components.
Role:
The person who should perform the signature
Meaning:
What purpose the signature serves
Count:
The number of required signatures
Cosignature Role:
If applicable
Verification Method:
The method of validating this person's signature authenticity
Based on this example, the Box Verification requirement could consist of the following.
Role:
Box Inspector
Meaning:
Verifier
Count:
1
Cosignature Role:
Area Supervisor
Verification Method:
Password Verification
This requirement enables the Box Inspector to verify that a box was filled and sealed correctly by providing 
a signature authenticated by password entry. If the Box Inspector’s signature cannot be verified for some 
reason, the Area Supervisor can provide a cosignature to approve the Box Inspector’s signature.
When Defining Electronic Signature Requirements
ESig Requirement is referenced by  Spec.
ESig Requirement references the ESig Role and ESig Meaning.
When you create an ESig requirement to be used for shop floor transactions, you must associate the 
requirement with a related operation on the Spec window.
Employees must be unique across the roles assigned to a requirement. The application allows an employee 
to sign off only once per requirement regardless of the number of meanings assigned to the requirement.
9-14
Modeling User Guide
Release 2510+ Rev. 1
Chapter 9: Electronic Signatures
ESig Requirement Page
This image shows an example of the ESig Requirement page.
ESig Requirement Page Field Definitions 
This table defines the fields unique to the ESig Requirement page. 
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
Details
Electronic Signatures 
Required grid
Grid listing the electronic signatures required for this requirement 
to be met.
Optional
Role
Required role for the employee to fulfill the requirement.
Required
Meaning
Meaning associated with the requirement.
Required
Count
Number of signatures necessary to fulfill the requirement.
Required
Cosigner 
Role
Cosignature for this requirement. If a cosignature is selected, this 
employee can provide an additional electronic signature in the 
event that the primary signer's signature is not accepted.
Optional
Verification 
Method
Type of verification that must occur to validate an electronic 
signature. Currently, the only available selection is Password 
Verification.
Required
Release 2510+ Rev. 1
Modeling User Guide
9-15
Chapter 9: Electronic Signatures
How to Define an Electronic Signature Requirement
Follow these steps to define an Electronic Signature Requirement:
1.
Open the ESig Requirement page. The ESig Requirement page appears within the Modeling 
page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for the electronic signature requirement in the ESig Requirement field. 
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
How to Add Electronic Signatures to an Electronic Signature Requirement
Follow these steps to add an electronic signatures to an electronic signature requirement:
1.
Perform the "How to Define an Electronic Signature Requirement" procedure.
Or
Select an existing Esig Requirement instance.
2.
Click Add new row on the Electronic Signatures Required grid. A new row appears.
3.
Enter information in these required fields:
•
Role
•
Meaning
•
Count
•
Verification Method
4.
Click Save. The application displays a success message indicating the modeling object was 
updated.
9-16
Modeling User Guide
Release 2510+ Rev. 1
Chapter 9: Electronic Signatures
Associating Electronic Signature Requirements with 
Modeling Objects
You must associate an electronic signature requirement with a modeling object to require electronic 
signature authentications for a shop floor transaction or a quality transaction. These modeling objects’ 
pages contain an Electronic Signature Txn Map that allows you to select the electronic signature 
requirement and the transaction for which signatures must be collected:
•
Factory - Any division, department, or group that is separated for accounting and reporting 
purposes. An enterprise can contain one or more factories.
•
Spec - Defines the activities carried out at a step and is referenced by the step in a Workflow.
•
Organization - A business entity that is separated for processing and reporting purposes. An 
organization is not associated with an enterprise or a factory.
The Factory and Spec pages contain an Electronic Signature Txn Map that allows you to select electronic 
signature requirements for shop floor transactions while the Organization page contains an Electronic 
Signature Txn Map that allows you to select electronic signature requirements for event record 
transactions.
When shop floor or event record transactions are executed on the modeling object, the specified 
Electronic Signature Txn Map definition is used to determine whether an electronic signoff is needed for 
the transaction. For example, if you want to require your supervisor to provide an electronic signature to 
verify that boxes are packed and sealed correctly before they are moved out of the Packing step, you 
would associate an electronic signature requirement to the MoveStd transaction on the Packing Spec.
Note:
Electronic signatures cannot be collected for Container transaction reversals because a specific 
history is not recorded for this service.
In the previous examples, an electronic signature requirement of Box Verification was created to allow Box 
Inspectors to verify that boxes were packed and sealed correctly. To enable the Electronic Signature pop-
up to appear during the shop floor service, you would associate these Electronic Signature Txn Map to the 
Packing Spec:
Transaction ID: Move Std
ESig Requirement: Box Verification
This association requires an Electronic Signature pop-up to appear when the MoveStd transaction is 
initiated during the Packing step. The page requires that someone associated with the Verification Role 
Group provide one signature to verify that the box has been packed and sealed correctly.
When Associating Electronic Signature Requirements with Modeling Objects
Before defining the modeling objects with which you want to associate electronic signature requirements, 
make sure you have defined your basic information model.
For specs, this includes:
•
Products and their product families
•
Operations
Release 2510+ Rev. 1
Modeling User Guide
9-17
Chapter 9: Electronic Signatures
•
Container levels
When you create an electronic signature requirement, you must associate it with a related operation on 
the Spec page.
Organizations and factories do not require any other modeling objects but do contain optional modeling 
objects. For organizations, this includes:
•
Roles
•
Employees
•
Triage Specs
•
Failure Mode Groups
•
Numbering Rules
•
UI Preferences
•
SMTP Transports
For factories, this includes:
•
Enterprise
•
Mfg Calendar
•
Dispatch Rule
•
Training Requirement Group
•
Print Queue 
•
Numbering Rule 
This section includes the basic steps to set up electronic signatures for modeling objects. Refer to the 
topics for defining the above modeling objects for information. 
When Specifying Electronic Signature Requirements for Event Record Transactions 
Typically, when specifying the event record transactions for which you want to collect electronic 
signatures, you need to add only that quality service to the Electronic Signature Txn Map on the 
Organization modeling object. For example, if you want to collect an electronic signature when a user 
cancels an approval for a quality record resolution, you would add the Cancel Approval Sheet quality 
service to the Electronic Signature Txn Map.
The exception is event creation. If you want to require electronic signatures for event recording pageflows, 
then you must specify not only the Create Event service in the Electronic Signature Txn Map on the 
Organization modeling object, but you must also add the Update Event service.
Electronic Signature Fields on Modeling Object Pages
Use the Electronic Signature Txn Map grids on the modeling object pages to associate an electronic 
signature requirement with a modeling object. 
9-18
Modeling User Guide
Release 2510+ Rev. 1
Chapter 9: Electronic Signatures
This image shows an example of the Electronic Signature Txn Map available on the Factory and Spec pages 
for shop floor transactions.
This image shows an example of the Electronic Signature Txn Map and its associated check boxes available 
on the Organization page for quality transactions.
Electronic Signature Txn Map Field Definitions 
This table defines the Electronic Signature Txn Map fields on the Factory and Spec pages. 
Field
Definition
Type
Transaction 
Definition ID of the shop floor transaction for which you 
want to establish electronic signature requirements.
Required
All Txns
Check box indicating all transactions should use the 
requirement identified in this instance.
Optional
ESig Requirement
Definition for the electronic signatures that should be 
collected for the transaction.
Required
Release 2510+ Rev. 1
Modeling User Guide
9-19
Chapter 9: Electronic Signatures
This table defines the Electronic Signature Txn Map fields on the Organization page. 
Field
Definition
Type
Quality Service grid
Definition ID of the quality transaction for which you want 
to establish electronic signature requirements.
Optional
Apply Electronic Signature to 
all Transactions
Check box indicating all quality transactions require 
electronic signatures. If selected and there are specific 
quality services set, the electronic signature requirement 
for the service will override the Apply Electronic Signatures 
to All Txns requirement.
Optional
Require Entry of User ID
Check box indicating the employee's password and user 
name are required for electronic signature verification. If 
not selected, only the employee's password is required.
Optional
How to Associate an Electronic Signature Requirement with a Factory or Spec
Follow these steps to associate an Electronic Signature Requirement with a Factory or Spec:
1.
Open the Factory or Spec page. The appropriate page appears within the Modeling page.
2.
Select an existing Factory or Spec instance. The page is updated to display the information for 
the selected Factory or Spec.
3.
Expand the Transactions section.
4.
Click Add new row on the Electronic Signature Txn Map grid. A new row appears.  
5.
Select the transaction for which you want to activate electronic signatures using the Transaction 
field.
Or
Click the All Txns check box if you want all transactions for this specification to have electronic 
signature capability.
6.
Select the electronic signature requirement from the ESig Requirement field.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Associate an Electronic Signature Requirement with an Organization
Follow these steps to associate an Electronic Signature Requirement with an Organization:
1.
Open the Organization page. The Organization page appears within the Modeling page.
2.
Select an Organization instance. The page is updated to display the information for the selected 
Organization.
9-20
Modeling User Guide
Release 2510+ Rev. 1
Chapter 9: Electronic Signatures
3.
Do you want to require an electronic signature for all event record transactions or specify selected 
event record transactions to require electronic signatures?
If you want to require an 
electronic signature for . . .
Then . . .
All event record transactions
a.
Select the Apply Electronic Signature to 
All Transactions check box.
b.
Go to step 4.
Specific event record transactions
a.
Click Add new row in the Electronic 
Signature Txn Map grid. A new row 
appears.
b.
Select a transaction from the Quality 
Service  list.
c.
Repeat steps a-b to add additional quality 
services.
d.
Go to step 4.
4.
Select the Require Entry of User ID check box if the application should require both the 
employee’s password and user name for electronic signature verification. (Leave the check box 
clear if the application should require only the password.)
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
9-21
Chapter 9: Electronic Signatures
Electronic Signatures and Compound Transactions
While Opcenter EX MDD and Opcenter EX CR offer a wide variety of standard pages and transactions, your 
organization may find it advantageous to develop additional pages and transactions based on specific 
business requirements. One type of custom transaction your organization may want to develop and 
implement is the compound transaction.
A compound transaction combines two or more standard transactions into a single transaction. For 
example, one of your manufacturing processes might require a MoveStd transaction as well as a 
MoveWithHold transaction. While the MoveStd is a standard transaction provided by Siemens, the 
MoveWithHold is a custom transaction that combines the MoveStd and Hold transactions.
Electronic Signature Requirements
Your organization must also consider electronic signature requirements when developing and 
implementing compound transactions. Given the preceding example, both the MoveStd and the 
MoveWithHold transactions may be performed at the same Spec. In other words, depending on the 
operator's analysis, either transaction might be executed. If this is the case, the Spec may also have 
different electronic signature requirements and transaction maps for each transaction. For example, if the 
operator executes the:
•
MoveStd, only the electronic signature specific to it should be processed.
•
MoveWithHold, only the electronic signature specific to the compound transaction should be 
processed.
Developing Compound Transactions
You use Designer to develop custom compound transactions. Primarily, a custom compound transaction 
does not, by default, include a Container field. You use Designer to add a Container field to the compound 
transaction.
Based on the preceding example, you would also have to modify the electronic signature business logic to 
resolve the electronic signature requirement from the container Spec. Rather than setting the Container 
field on the sub-services, you would modify the business logic to resolve the sub-service’s Container field 
from the compound service’s Container field during the sub-service initialization. This is the same logic 
used by Siemens-provided compound transactions.
Finally, you would turn off electronic signature processing for the sub-services. By doing so, you ensure 
that only the compound transaction's electronic signature is processed, even though a MoveStd is 
performed in both instances. You accomplish this by setting the ProcessESignatures Boolean field to False 
on the compound transaction's sub-services.
9-22
Modeling User Guide
Release 2510+ Rev. 1
Chapter 10: Dispatch Rule 
Definitions
Introduction
The process of dispatching containers includes the following activities, performed in a predefined 
sequence:
•
Starting containers in a predefined sequence based on manufacturing orders
•
Moving containers in and out of an operation
You establish Dispatch Rules in your model to define the dispatch lists that are displayed to the shop floor 
user. Subsequently, the shop floor user consults these lists as the basis for starting or moving containers 
through the factory.
Dispatch Rules perform these tasks:
•
Displays a list of work that has to be performed
•
Optionally enforces the sequence in which the work is performed
You must create or modify these modeling definitions to define this process:
•
Dispatch Rules
•
Manufacturing Orders
•
Operations
•
Work Centers
•
Factories
In This Chapter
This chapter contains these topics:
•
Container Processing Based on Dispatch Rules
•
Modeling Sequence
•
Defining Queries
•
Defining Dispatch Rules
•
Manufacturing Orders
•
Enforcing Dispatch Rules in Operations, Work Centers, and Factories
•
Sample Dispatch Lists
•
Viewing Containers Based on Manufacturing Orders
Release 2510+ Rev. 1
Modeling User Guide
10-1
Chapter 10: Dispatch Rule Definitions
•
Shop Floor Services and Container Dispatching
 
10-2
Modeling User Guide
Release 2510+ Rev. 1
Chapter 10: Dispatch Rule Definitions
Container Processing Based on Dispatch Rules
Siemens provides  five dispatch rule types. A single dispatch rule definition can encompass one or more of 
these rule types. When you define a dispatch rule you specify the dispatch rule types and then associate 
each type with either a Siemens-provided query or your own query. The query determines the sequence of 
items presented to the shop floor user.
Dispatch Rule Types and Queries
This table provides a quick reference for dispatch types and names of associated Siemens queries that you 
associate with the dispatch types. These queries are the default Designer queries used on the Dispatch 
Rule page when you select Designer Query as the Query type. You will need this information as you are 
defining dispatch rules.
Dispatch 
Type
Description
Siemens-
Provided Query
Batch Order
Dispatch rule of type Batch Order displays a list of 
manufacturing orders that provide the basis for starting batches 
using the Start Batch transaction.
DefaultDispatch_
BatchOrder
Container 
MoveIn
Dispatch rule of type ContainerMoveIn displays a list of 
containers waiting in the queue to be processed. The MoveIn 
service will be used on the containers.
DefaultDispatch_
ContainerMoveIn
Container 
MoveOut
Dispatch rule of type ContainerMoveOut displays a list of 
containers for the MoveStd transaction.
DefaultDispatch_
ContainerMoveOut
eProcedure 
Dispatch rule of type eProcedure displays dispatch lists on the 
eProcedure page per user-associated queries.
DefaultDispatch_
EProcedure
Order
Dispatch rule of type Order displays a list of manufacturing 
orders that provide the basis for creating containers using the 
Start transaction.
DefaultDispatch_
Order
Container Quantities Based on Manufacturing Orders
Your business rules may dictate that containers should be started on the basis of manufacturing orders 
(dispatch type: Order). In this case, the shop floor user is presented with a list of manufacturing orders. 
You must start the containers in the order in which they appear on the list if Enforce Dispatch is set to true. 
Otherwise, you can start the containers in any order. Refer to "Defining Dispatch Rules" for  information on 
the Enforce Dispatch setting.
The manufacturing order at the top of the list is based on the query that has been implemented. If you 
implement a default query, the manufacturing order at the top of the list is the order with the earliest 
planned start date followed by the highest priority.
When you are using the default query, Opcenter EX MDD or Opcenter EX CR tracks the quantities of 
containers based on the amount specified in the manufacturing order. When the quantities for the 
manufacturing order are reached, the order is removed from the dispatch list. Meanwhile, Opcenter EX 
Release 2510+ Rev. 1
Modeling User Guide
10-3
Chapter 10: Dispatch Rule Definitions
MDD and Opcenter EX CR enables the shop floor user to track the quantities already processed on the 
manufacturing order.
Rules of Precedence
You can define dispatch rules for operations, work centers, and factories. Opcenter EX MDD and Opcenter 
EX CR logic enforces dispatch rules based on these rules of precedence:
•
Dispatch rules defined for operations take precedence over those defined for work centers.
•
If no rules are defined for operations, those defined for work centers take precedence over 
dispatch rules for factories.
10-4
Modeling User Guide
Release 2510+ Rev. 1
Chapter 10: Dispatch Rule Definitions
Modeling Sequence
As you create your dispatch management model, it is important that you follow a specific sequence of 
steps. The modeling sequence for dispatch management begins with defining your queries and ends with 
associating dispatch rules with operations, work centers, and factories.
This diagram  shows the sequence of modeling tasks for dispatch rule definitions.
Release 2510+ Rev. 1
Modeling User Guide
10-5
Chapter 10: Dispatch Rule Definitions
Defining Queries
The first step in modeling dispatch management is to establish the queries upon which you will base your 
rules. (Remember, the query determines the sequence of items presented to shop floor users.) You can 
base the rule on a user query or on a Designer query.
You can create and update user queries in the application, specifically on the User Query page displayed 
below.
When Defining a User Query
When defining a User query, you must enter a SQL statement in the Query Text field. The application 
requires a SQL statement to retrieve information from the database. Optionally, you can specify 
parameters in the User Query Parameter grid to limit the search results. The application prompts the user 
to provide the parameter information when the query is executed.
Note:
After defining a User query, you can execute it against production immediately without having 
to update the transaction database. Refer to "Defining User Queries" for information.
Designer Queries
Additionally, you create and maintain custom queries through Designer.  Refer to the Opcenter Execution 
Medical Device and Diagnostics Designer User Guide or the Opcenter Execution Core Designer User Guide 
for information on creating custom queries.
10-6
Modeling User Guide
Release 2510+ Rev. 1
Chapter 10: Dispatch Rule Definitions
Defining Dispatch Rules
Dispatch Rules  define the dispatch lists that are displayed to the shop floor user. Subsequently, the shop 
floor user consults these lists as the basis for starting or moving containers through the factory. 
Dispatch rules perform these tasks:
•
Display a list of work that has to be performed
•
Optionally enforce the sequence in which the work is performed
Dispatch Rule Page
This image shows an example of the Dispatch Rule page.
Dispatch Rule Page Field Definitions
This table defines the fields unique to the Dispatch Rule page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
Details
Release 2510+ Rev. 1
Modeling User Guide
10-7
Chapter 10: Dispatch Rule Definitions
Field
Definition
Type
Query Type
List of query types based on where the query was defined:
•
Designer means the query is provided by Siemens through 
the Designer.
•
User means the user-defined query was created through 
Modeling.
Query Type is a display only field  when you open an existing 
Dispatch Rule instance.
Required/
Display 
Only
Dispatch Details 
grid
Grid listing the transactions affected by the dispatch rule and the 
details for each.
Optional
Dispatch 
Type
Type of container transaction affected by this dispatch rule:
•
Container MoveIn - the dispatch type for 
MoveIn transactions.
•
Container Move Out - the dispatch type for Move 
transactions (MoveStd and MoveNonStd).
•
eProcedure - the dispatch type for sorting containers  on the 
EProcedure page.
•
Order - the dispatch type for Start transactions based on 
manufacturing orders.
•
Batch Order - the dispatch type for Start Batch transactions.
Optional
Enforce 
Dispatch
Check box indicating the application will enforce the rule on the 
shop floor services.
Start service example: 
If selected, the shop floor user can only create containers based on 
the manufacturing order at the top of the list. 
If not selected, the dispatch list will still sort the orders based on 
priority but you can start containers in any order on the list.
Optional
Query 
Name
List of queries used to populate the dispatch grid. The items on the 
list are based on your value for Query Type. 
If Query Type is Designer Query, the list displays Siemens-provided 
query names. 
If Query Type is User Query, the list displays query names created by 
the user.
Optional
How to Define a Dispatch Rule
Follow these steps to define a Dispatch Rule:
1.
Open the Dispatch Rule page. The Dispatch Rule page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name in the Dispatch Rule field.
10-8
Modeling User Guide
Release 2510+ Rev. 1
Chapter 10: Dispatch Rule Definitions
4.
Select a value from the Query Type  list as follows:
•
Select Designer Query if you want to use the default query as defined in the Designer to 
populate the dispatch list.
•
Select User Query if you want to use a query defined in Modeling to populate the dispatch 
list.
5.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
6.
Click Save. The application saves the modeling object and displays a success message.
How to Add Dispatch Details
Follow these steps to add dispatch details:
1.
Perform the "How to Define a Dispatch Rule" procedure. 
Or 
Select an existing Dispatch Rule instance.
2.
Click the Add new row button. A new row appears.  
3.
Select one of the following from the Dispatch Type field:
•
ContainerMoveIn if you want to display a dispatch list of containers for Move In 
transactions.
•
ContainerMoveOut if you want to display a dispatch list of containers for Move 
transactions.
•
eProcedure if you want to display a dispatch list of containers on the eProcedure page.
•
Order if you want to display a dispatch list of Manufacturing Orders for Start transactions.
•
Batch Order if you want to display a dispatch list of manufacturing orders for Start Batch 
transactions.
4.
Select the Enforce Dispatch check box if you want to enforce dispatch rules. Selecting the check 
box indicates that the shop floor service must be performed on the top item on the dispatch list.
5.
Select the query from the Query Name  list. This query is used to populate the dispatch list.
6.
Repeat steps 2-5 to add the other dispatch types as required for this dispatch rule.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
10-9
Chapter 10: Dispatch Rule Definitions
Manufacturing Orders
Manufacturing Orders provide the basis for starting containers in Operations, Factories, and Work Centers 
if you enforce the dispatch rule type Order for those entities. The Dispatch Rule type Order is associated 
with the Start transaction.
The default manufacturing query uses these values from the MfgOrder page:
•
Planned Start Date
•
Priority (a user code with WIP messages)
The shop floor user accesses the Order Dispatch List on the Order Dispatch page. The list is sorted 
according to the earliest planned start date. If the date was not defined in the manufacturing order, or the 
orders have the same planned start date, the sorting is based on priority.
Refer to "Defining Manufacturing Orders" for information.
Mfg Order Page
This image shows a Manufacturing Order instance.
 
10-10
Modeling User Guide
Release 2510+ Rev. 1
Chapter 10: Dispatch Rule Definitions
Enforcing Dispatch Rules in Operations, Work Centers, 
and Factories
You enforce dispatch rules through the Dispatch Rule field for operations, work centers, and factories. 
Rules enforced for operations take precedence over those for work centers, and rules for work centers take 
precedence over those defined for factories.
You can reference only one dispatch rule at a time in operations, work centers, and factories, although a 
rule can incorporate from 1 to 4 rule types. It is therefore important for you to predefine several variations 
of rules that include a combination of rule types, or turn off the Enforce Dispatch flag for a dispatch rule 
type within a dispatch rule as your business requirements change.
Refer to:
•
"Physical Model Definitions" for information on creating and modifying work center and factory 
instances.
•
"Process Model Definitions" for information on creating and modifying operation instances.
In this example for operation, the Dispatch Rule field displays dispatch rule instances. This example also 
shows the Use Queue field as selected, which means the MoveIn service is required for that operation. You 
will most likely enforce a dispatch rule that includes the dispatch type MoveIn in this scenario.
Release 2510+ Rev. 1
Modeling User Guide
10-11
Chapter 10: Dispatch Rule Definitions
Sample Dispatch Lists
This topic contains examples of dispatch lists (or grids) that are displayed to the shop floor users when 
rules are defined and enforced. The information on the lists is based on Siemens-provided queries. In all 
lists, Siemens-provided queries determine the columns that appear on the grid. If you want to change the 
columns, you must define your own user queries and enter them in the dispatch rule.
Note:
The Properties | DisplayLayout | AutogenerateColumns property must be set to true for the 
query grid to pick up the column automatically.
Dispatch List for Manufacturing Order Starts
The Order Dispatch page below shows an example of a dispatch grid of manufacturing orders as populated 
by the Designer query, DefaultDispatch_Order.
The items displayed on the grid include:
Mfg Order:
Displays all manufacturing order instances. If a dispatch rule is 
enforced, the first item on the grid needs to be processed 
first.
Qty:
Displays the quantity specified in the manufacturing order.
In Process Qty:
Displays the running total quantity of containers started so far 
against the order. When the order is fulfilled (Qty = In Process 
Qty), the order will be removed from the list.
Product:
Displays the product associated with the manufacturing order.
Product Description:
Displays the product's description.
Priority:
Displays the priority for manufacturing order.
Planned Start Date:
Displays the planned start date of the manufacturing order. By 
default, the grid is sorted by this date.
10-12
Modeling User Guide
Release 2510+ Rev. 1
Chapter 10: Dispatch Rule Definitions
Dispatch List for Move Ins
This image is an example of a dispatch list that will be displayed to the shop floor user as populated by the 
Designer query, DefaultDispatch_ContainerMoveIn. This grid, labeled In Queue Containers, is on the 
Operational View page. Containers on this grid require the MoveIn transaction.
The items displayed on the grid include:
Container:
Displays containers to be moved in to the operation. If the 
dispatch rule for MoveIn is enforced, the first item on the grid 
needs to be processed first.
Product:
Displays the product associated with the container.
Description:
Displays the description of the product associated with the 
container.
Qty:
Displays the container's quantity.
UOM:
Displays the unit of measure associated with the quantity.
Status:
Displays the container's status.
Mfg Order: 
Displays the Mfg Order associated with the container.
Operation:
Displays the operation where the container is currently 
located.
Dispatch List for Moves
This image is an example of a dispatch list that will be displayed to the shop floor user as populated by the 
Designer query, DefaultDispatch_ContainerMoveOut. This grid is on the Operational View and  Move 
pages. The Dispatch List for Moves affects the In Process Containers grid on the Operational View page and 
the Container grid displayed when you select a container from the Container field on most container 
transaction pages.
Release 2510+ Rev. 1
Modeling User Guide
10-13
Chapter 10: Dispatch Rule Definitions
The items displayed on the grid include:
Container:
Displays the containers name.
Product:
Displays the product associated with the container.
Description:
Displays the description of the product associated with the 
container.
Qty:
Displays the container's quantity.
UOM:
Displays the unit of measure associated with the quantity.
Status:
Displays the container's status.
Mfg Order: 
Displays the Mfg Order associated with the container.
Operation:
Displays the operation where the container is currently 
located.
10-14
Modeling User Guide
Release 2510+ Rev. 1
Chapter 10: Dispatch Rule Definitions
Viewing Containers Based on Manufacturing Orders
You can keep track of containers that have been started against a manufacturing order by viewing the 
instance in the application.
The  Containers field displays a read-only list of container names started against this order. Quantities and 
other status information are not provided. This view is available in Modeling but does not display to the 
shop floor user.
How to View a Container
Follow these steps to view a container based on manufacturing order:
1.
Click Mfg Order on the Modeling tab. The Manufacturing Order tab appears.
2.
Select an instance from the Mfg Order list. The Mfg Order page appears.
3.
Go to the Details section.
4.
View the entries in the Containers grid.
Release 2510+ Rev. 1
Modeling User Guide
10-15
Chapter 10: Dispatch Rule Definitions
Shop Floor Services and Container Dispatching
These transactions (services) provide dispatch lists:
•
Start
•
MoveIn
•
MoveStd
Menus for Shop Floor Users
Siemens provides pages that display dispatch lists to shop floor users when they are executing the services 
listed above. To use these pages, make sure you define menus for the shop floor users that reference the 
files listed in the following table.
These pages for shop floor services support Dispatch Rules.
File to Use
Service
Description
OrderDispatchVP.xml
Start
Displays a grid of Manufacturing Orders 
that will be the basis for starting 
containers.
OperationalViewVP.xml and
OperationalViewScanVP.xml
MoveIn
MoveOut (includes 
MoveStd)
Allows you to perform the following 
transaction in a combination form:
•
MoveIn on a container from the 
in-queue grid. The grid is 
present if MoveIn is required at 
the Operation.
•
MoveStd on a container from 
the in-process grid (containers 
are being moved out of the 
Operation).
MoveStdVP.xml
MoveStd
Allows you to perform a MoveStd by 
selecting a container from the grid.
Refer to the Opcenter Execution Medical Device and Diagnostics Shop Floor User Guide or the Opcenter 
Execution Core Shop Floor User Guide for procedures to execute services.
10-16
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance 
Management Definitions
Introduction
The term maintenance refers to adjustments, calibrations, change of consumables, software upgrades, 
repairs, preventive maintenance, and similar activities carried out on designated resources (including 
carriers).
The Maintenance Management feature enables you to define and track resource-centric maintenance 
requirements based on calendar date and thruput. After maintenance requirements are assigned to 
resources, enforcement occurs during the execution of shop floor services.
In This Chapter
This chapter contains these topics:
•
Pre-Implementation Information
•
Modeling Relationship Diagram
•
Defining Maintenance Reasons
•
Defining Thruput Requirements
•
Defining Date Requirements
•
Defining Recurring Date Requirements
•
Defining Maintenance Classes
•
Referencing a Maintenance Class in the Resource
•
What Happens During a Move Standard or Move In Transaction
Release 2510+ Rev. 1
Modeling User Guide
11-1
Chapter 11: Maintenance Management Definitions
Pre-Implementation Information
Before implementing Maintenance Management in your factory, you need to understand the types of 
maintenance requirement schedules, and make some decisions about how you want to configure 
maintenance management, specifically:
•
Which resources to include for scheduled maintenance
•
The maintenance classes you will define and which resources will be assigned to each
•
The maintenance reasons for each type of maintenance requirement
•
The maintenance requirement schedules based on thruput, single date, and recurring dates, and 
which schedule or schedules will apply to a resource
•
Who will receive e-mail notifications about maintenance that is pending, due, and past due
•
At what point activation and enforcement of the maintenance requirements begin
Maintenance Requirement Schedules
A maintenance requirement is based on the type of scheduling you want to set up for the resources that 
are associated with the requirement:
•
The maximum thruput that the resource can process
•
A single calendar date
•
A series of recurring dates
A resource can have more than one requirement schedule.
Scheduling Based on Thruput
A Thruput Requirement defines the maximum number of units that the resource can process between 
maintenance events before the next maintenance is due. Thruput requirement schedules include 
allowances for a tolerance quantity and a warning quantity.
Scheduling Based on Date
A Date Requirement defines a specific date on which the next maintenance event is to occur on the 
resource. Date requirement schedules include allowances for a tolerance period and a warning period.
Scheduling Based on Recurring Date
A Recurring Date Requirement defines a maintenance schedule for the resource based on recurring 
calendar dates. The schedule specifies one or more dates on which a maintenance event must occur, and 
each date must occur independently of when the previous maintenance was completed. For example, if 
maintenance is scheduled to occur every other week on Tuesday, but it was performed two days late on a 
Thursday, the next maintenance event is still scheduled to occur on a Tuesday.
11-2
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Setting up a recurring date requirement is very similar to scheduling a recurring appointment in Microsoft 
Outlook.
Recurring date requirement schedules include allowances for a tolerance period and a warning period.
End Date vs. Open-Ended
A recurring date requirement can have an end date or it can be open-ended. You can identify a specific 
end date, or you can enter the number of occurrences. If you enter the number of occurrences, that 
number is used to calculate the end date. The requirement also includes a seed date, the date on which 
the schedule is built.
Pattern and Frequency
Scheduling patterns for maintenance are in intervals of the following:
•
Once - Schedules run once at the scheduled date and time.
•
Seconds - Schedules have a fixed number of seconds between execution.
•
Minutes - Schedules have a fixed number of minutes between execution.
•
Hourly - Schedules have a fixed number of hours between execution.
•
Daily - Schedules have a fixed number of days between execution.
•
Weekly - Schedules have a specific day of the week.
•
Monthly - Schedules have a specific day of the month.
•
Yearly - Schedules have a month and a day during the month. 
All of these intervals support a frequency, which identifies a pattern for how often the requirement 
repeats: 1 indicates that the application executes the maintenance event on every scheduled recurrence; 2 
indicates every other scheduled recurrence, and so forth. 
System Calculation for Dates
Dates are timestamps set in the application, either entered by you or defaulted by the application. If you 
do not enter a time when defining a date requirement or a recurring date requirement, then the time 
default is midnight.
The application does not store all dates for a schedule of recurring dates. It only stores the date of the next 
scheduled maintenance. For schedules that fall on a day that does not occur in the next scheduled month, 
the application uses the last day of the month.
When a recurring date requirement is first created, or for any change to the requirement that affects the 
schedule, the application calculates the next future date in the schedule and stores that date with the 
requirement.
Multiple Schedules
As stated previously, a resource may need more than one type of maintenance schedule.
Example 1
A resource requires periodic maintenance on a weekly and quarterly basis, so you define two Recurring 
date Requirements, one weekly and one quarterly:
Release 2510+ Rev. 1
Modeling User Guide
11-3
Chapter 11: Maintenance Management Definitions
The weekly maintenance should occur once every Thursday. Therefore, the schedule is Weekly, the 
day is Thursday, and the frequency is 1.
The quarterly maintenance should occur on the 9th of the month, once per quarter. Therefore, the 
schedule is Monthly, the day of the month is 9, and the frequency is 3 (once every three months).
Example 2
A resource requires quantity thruput maintenance after processing a specific quantity as well as periodic 
maintenance on a yearly basis, so you define two schedules—a thruput requirement based on quantity 
thruput and a recurring date requirement based on a yearly recurrence.
E-mail Notifications
When you define the maintenance requirement schedules, you indicate who should receive Pending, Due, 
and Past Due e-mail messages, based on the warning and tolerance levels that you set. These messages 
are not generated automatically when maintenance becomes due, but when the operator completes a 
transaction on the resource, such as Move In or Resource Thruput.
Within a single maintenance cycle, the same e-mail is only sent once, with the exception of the Past Due 
notification. Past Due notifications will be sent each time a transaction is performed on the resource upon 
validating the Tolerance criteria.
Important:
For a thruput requirement, the first shop floor transaction performed that puts a past 
due resource over the limit, will still execute and will send the past due e-mail. However, 
subsequent transactions performed against the resource will send the past due e-mail 
but will fail.
Modeling Definitions
These are the modeling object instances that you define and modify to implement Maintenance 
Management.
Modeling 
Object
Description
Maintenance 
Reason
Reason for a maintenance requirement.
Thruput 
Requirement
Maximum allowed quantity that can be processed before a maintenance event must 
occur. Pertains to maintenance requirement schedules that are based on thruput 
quantities.
Date 
Requirement
Specific date on which a maintenance event must occur. Pertains to maintenance 
requirement schedules that are based on a single date.
Recurring Date 
Requirement
One or more dates on which a maintenance event must occur. Pertains to 
maintenance requirement schedules that are based on recurring dates.
11-4
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Modeling 
Object
Description
Maintenance 
Class
Maintenance classification; used for resources with the same maintenance 
requirement. A maintenance class can contain many resources, but a resource can 
only reference one maintenance class.
A resource can have one or more active maintenance requirements without 
belonging to a maintenance class.
Resource
Machine or piece of equipment for which an active requirement is enforced. May or 
may not belong to a maintenance class.
How Requirements are Enforced
A maintenance requirement becomes active and maintenance is enforced only when it is associated with a 
resource or Maintenance Class. This occurs through either the Resource Activation transaction or the 
Maintenance Class Activation transaction. Refer to the Opcenter Execution  Medical Device and Diagnostics 
Shop Floor User Guide or the Opcenter Execution Core Shop Floor User Guide for information.
A resource’s maintenance schedule reflects active, currently assigned maintenance requirements only.
Release 2510+ Rev. 1
Modeling User Guide
11-5
Chapter 11: Maintenance Management Definitions
Modeling Relationship Diagram
This diagram shows the modeling objects for maintenance management, their relationships, and the 
values you set in each.
11-6
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Defining Maintenance Reasons
A Maintenance Reason is a type of user code that specifies the valid values for resource maintenance. You 
select a Maintenance Reason when defining your maintenance requirements. Refer to "Maintenance 
Reason" in the User Codes table of the "Defining User Codes" section.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Maintenance Reason
Read "Pre-Implementation Information" in this chapter before adding instances of the Maintenance Reason 
object.
Follow these steps to define a maintenance reason:
1.
Open the Maintenance Reason page. The Maintenance Reason page appears within the 
Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this reason in the Maintenance Reason field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
11-7
Chapter 11: Maintenance Management Definitions
Defining Thruput Requirements
Thruput Requirement defines the quantity that a resource associated with this requirement can process 
between maintenance events before the next maintenance event is due. The requirement definition 
includes tolerance and warning allowances (quantity of units), and the corresponding e-mail distribution 
lists for pending, due, and past due maintenance event email notifications. You also have the option to 
associate a document set and a data collection definition with the requirement. 
Note:
Opcenter EX MDD and Opcenter EX CR only support a single UOM for a container hierarchy 
when maintenance management is based on thruput.
UOM Validation
When defining a thruput requirement, you enter the unit of measure (UOM) for the quantity specified. 
When this requirement is activated for a resource, this UOM must match the container’s UOM for the 
resource to process the container.
However, UOM validation can be turned off by using Designer to override the ValidateMaintenanceUOM 
method in the specific ShopFloor subclasses where no validation should occur. The method can be 
overridden to perform no action or to perform custom logic. For example, the logic can be overridden to 
convert the quantity to a different UOM based on a formula.
When Defining Thruput Requirements
Thruput Requirements contain the required Modeling definition Maintenance Reason and these optional 
Modeling definitions: Document Set, Data Collection Def, E-mail Notification, ESig Requirement, and UOM.
11-8
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Thruput Requirement Page
This image shows an example of the Thruput Requirement page.
Thruput Requirement Page Field Definitions
This table defines the fields unique to the Thruput Requirement page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
General
Engineering Change 
Order
Engineering change order assigned to this revision. You can enter a 
maximum of 30 characters.
Optional
Scheduling Details
Maintenance Reason
Reason associated with this requirement.
Required
Release 2510+ Rev. 1
Modeling User Guide
11-9
Chapter 11: Maintenance Management Definitions
Field
Definition
Type
Document Set
Document set associated with this requirement. Document sets are 
defined in Modeling. Refer to "Defining Document Sets" for  
information.
Optional
Data Collection Def
Data collection definition associated with this requirement. Data 
collection definitions are defined in Modeling. Refer to "Defining 
Data Collection Definitions" for  information.
Optional
Electronic Signature 
Requirement
Pre-defined electronic signature requirements. An electronic 
signature requirement defines the electronic signature that should 
be collected for the transaction. If an electronic signature 
requirement is specified, you cannot complete the transaction until 
all signatures have been captured.
Optional
Job Model
Job Model that the application will use to create a maintenance 
job. Job Model refers to a workflow performed for the repair or 
routine maintenance of a manufacturing resource. 
Note: The application will automatically create a maintenance job 
once the maintenance state is Past Due or Due. 
Optional
Qty
Number of units that can be processed by the resource, after which 
it is due for maintenance. 
•
Triggers the "due e-mail"
Required
UOM
Unit of measure for the quantity specified in the Qty field.
When this requirement is activated for a resource, this UOM must 
match the container's UOM for the resource to process the 
container.
Required
Warning Qty
Quantity that, when subtracted from the amount in the Qty field, 
identifies the point at which maintenance associated with this 
requirement is pending for the associated resource.
•
Triggers the "pending e-mail"
If allowed to default to 0, the "pending e-mail" is not sent.
Optional
Tolerance Qty
Quantity that, when added to the amount in the Qty field, 
identifies the point at which maintenance associated with this 
requirement is past due for the associated resource.
•
Triggers the "past due e-mail" and the resource becomes 
unavailable for further processing
If allowed to default to 0, the "past due e-mail" is sent when the 
value in the Qty field is reached and the resource immediately 
becomes unavailable for further processing.
Optional
Qty2
Secondary number of units that can be processed by the resource 
after which it is due for maintenance.
•
Triggers the "due e-mail"
The field is used only if the component is tracked using secondary 
units of measure.
Optional
11-10
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Field
Definition
Type
UOM2
Unit of Measure for the secondary quantity specified in the Qty2 
field.
The field is used only if the component is tracked using secondary 
units of measure.
Optional
Warning Qty2
Quantity that, when subtracted from the amount in the Qty2 field, 
identifies the point at which maintenance associated with this 
requirement is pending on the resource.
•
Triggers the "pending e-mail"
The Pending e-mail is not sent if  allowed to default to 0.
Optional
Tolerance Qty2
Quantity that, when added to the amount in the Qty2 field, 
identifies the point at which maintenance associated with this 
requirement is past due on the resource.
•
Triggers the "past due e-mail" and the resource becomes 
unavailable for further processing
If allowed to default to 0, the "past due e-mail" is sent when the 
value in the Qty2 field is reached and the resource immediately 
becomes unavailable for further processing.
Optional
Checklist grid 
Grid listing any checklists that have been configured  for the date 
requirement.
Optional
Checklist Id 
Unique checklist name to identify the checklist. 
Required
Instruction 
Free form text added during checklist configuration to  guide the 
user performing the checklist.
Required
Employee 
Group
Group of employees authorized to perform the  checklist.
Optional
Single Only
Check box to control whether this checklist may be  selected along 
with other checklists.
Optional
Data 
Collection 
Def 
Defines data collected as part of the checklist  completion process.
Optional
Description 
Free form text to add descriptive information about the  checklist.
Optional
Notes 
Relevant comments. You can enter a maximum of  2000 characters. Optional
Enforce Checklist 
Sequence 
Indicates whether the application should enforce the  sequence of 
checklist items.
Optional
Notifications
Pending E-
mail Target grid
Identifies the recipients of an e-mail to be sent when maintenance 
is pending. Refer to the Warning Period field in "Defining Recurring 
Date Requirements."
Optional
Pending E-mail Text
Text or text variables of the e-mail to be sent when maintenance is 
pending. You must enter text if you specified a pending e-mail 
target. Text variables can be used.
Optional
Release 2510+ Rev. 1
Modeling User Guide
11-11
Chapter 11: Maintenance Management Definitions
Field
Definition
Type
Due E-mail Target 
grid
Identifies the recipients of an e-mail to be sent when maintenance 
is due. Refer to the Schedule Date field in "Defining Recurring Date 
Requirements."
Optional
Due E-mail Text
Text of the e-mail to be sent when maintenance is due (still within 
the tolerance period). You must enter text if you specified a due e-
mail target. Text variables can be used.
Optional
Past Due E-
mail Target grid
Identifies the recipients of an e-mail to be sent when maintenance 
is past due. Refer to the Tolerance Period field in "Defining 
Recurring Date Requirements."
Optional
Past Due E-mail Text
Text of the e-mail to be sent when maintenance is past due. You 
must enter text if you specified a past due e-mail target. Text 
variables can be used.
Optional
How to Define a Thruput Requirement
Follow these steps to define a Thruput Requirement:
1.
Open the Thruput Requirement page. The Thruput Requirement page appears within the 
Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this requirement in the Thruput Requirement field, and enter the revision 
identifier for this definition in the Revision field.
4.
Expand the Scheduling Details section.
5.
Select the reason associated with this requirement in the Maintenance Reason field.
6.
Enter the number of units that can be processed by the resource after which it is due for 
maintenance in the Qty field.
7.
Select the corresponding unit of measure in the UOM field.
8.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
9.
Click Save. The application saves the modeling object and displays a success message.
How to Add Thruput Requirement Notifications
Follow these steps to add Thruput Requirement notifications:
1.
Perform the "How to Define a Thruput Requirement" procedure.
Or
Select an existing Thruput Requirement instance.
2.
Expand the Notifications section.
3.
Click Add new row in the Pending E-mail Target, Due E-mail Target, or Past Due E-mail Target 
grid. A new row appears.
11-12
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
4.
Select an e-mail notification from the picklist in the newly added row. The notification is added to 
the grid.
5.
Enter the text for the e-mail in the corresponding Pending E-mail Text, Due E-mail Text, or Past 
Due E-mail Text field. You also have the option to use text variables.
6.
Repeat steps 3-5 to set up notifications for additional recipients.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
11-13
Chapter 11: Maintenance Management Definitions
Defining Date Requirements
A Date Requirement defines a resource’s maintenance schedule based on a single calendar date. The 
requirement definition includes tolerance and warning allowances (in days), and corresponding e-mail 
distribution lists for pending, due, and past due maintenance event e-mail notifications. You also have the 
option to associate a document set and a data collection definition with the requirement.
When Defining Date Requirements
Date Requirement contains the required Modeling definition Maintenance Reason and these optional 
Modeling definitions: Document Set, Data Collection Def, E-mail Notification, ESig Requirement, and UOM.
11-14
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Date Requirement Page
This image shows an example of the Date Requirement page.
Date Requirement Page Field Definitions
This table defines the fields unique to the Date Requirement page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
General
Engineering Change 
Order
Engineering change order assigned to this revision. You can enter a 
maximum of 30 characters.
Optional
Scheduling Details
Maintenance Reason
Reason associated with this requirement.
Required
Document Set
Document set associated with this requirement.
Optional
Data Collection Def
Data collection definition associated with this requirement.
Optional
Schedule Date
Date and time at which this requirement will be due pending 
activation of the requirement for the resource or maintenance 
class. The time default is midnight if no time is entered. 
Triggers the "due e-mail."
Required
Release 2510+ Rev. 1
Modeling User Guide
11-15
Chapter 11: Maintenance Management Definitions
Field
Definition
Type
Warning Period
Number of days before the schedule date that, when reached, sets 
this maintenance requirement as pending for the associated 
resource. 
Triggers the "pending e-mail." 
The Pending e-mail is not sent if  allowed to default to 0.
Optional
Tolerance Period
Number of days before the schedule date that, when reached, sets 
this maintenance requirement as pending for the associated 
resource. 
Triggers the "past due e-mail" and the resource becomes 
unavailable for further processing. 
If allowed to default to 0, the "past due e-mail" is  sent on the 
schedule date and the resource immediately becomes unavailable 
for further processing.
Optional
Electronic Signature 
Requirement
Pre-defined electronic signature requirements. An electronic 
signature requirement defines the electronic signature that should 
be collected for the transaction. If an electronic signature 
requirement is specified, you cannot complete the transaction until 
all signatures have been captured.
Optional
Job Model
Job Model that the application will use to create a maintenance 
job. Job Model refers to a workflow performed for the repair or 
routine maintenance of a manufacturing resource. 
Note: The application will automatically create a maintenance job 
once the maintenance state is Due. 
Optional
Checklist grid 
Grid listing any checklists that have been configured  for the date 
requirement.
Optional
Checklist Id 
Unique checklist name to identify the checklist. 
Required
Instruction 
Free form text added during checklist configuration to  guide the 
user performing the checklist.
Required
Employee 
Group
Group of employees authorized to perform the  checklist.
Optional
Single Only
Check box to control whether this checklist may be  selected along 
with other checklists.
Optional
Data 
Collection 
Def 
Defines data collected as part of the checklist  completion process.
Optional
Description 
Free form text to add descriptive information about the  checklist.
Optional
Notes 
Relevant comments. You can enter a maximum of  2000 characters. Optional
Enforce Checklist 
Sequence 
Indicates whether the application should enforce the  sequence of 
checklist items.
Optional
Notifications
11-16
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Field
Definition
Type
Pending E-mail 
Target grid
Grid identifying the recipients of an e-mail to be sent when 
maintenance is pending. Refer to the Warning Period field in 
"Defining Recurring Date Requirements."
Optional
Pending E-mail Text
Text  of the e-mail to be sent when maintenance is pending. You 
must enter text if you specified a pending e-mail target. Text 
variables can be used.
Optional
Due E-mail Target 
grid
Grid identifying the recipients of an e-mail to be sent when 
maintenance is due. Refer to the Schedule Date field in "Defining 
Recurring Date Requirements."
Optional
Due E-mail Text
Text of the e-mail to be sent when maintenance is due (still within 
the tolerance period). You must enter text if you specified a due e-
mail target. Text variables can be used.
Optional
Past Due E-mail 
Target grid
Grid identifying the recipients of an e-mail to be sent when 
maintenance is past due. Refer to the Tolerance Period field in 
"Defining Recurring Date Requirements."
Optional
Past Due E-mail Text
Text of the e-mail to be sent when maintenance is past due. You 
must enter text if you specified a past due e-mail target. Text 
variables can be used.
Optional
How to Define a Date Requirement
Follow these steps to define a Date Requirement:
1.
Open the Date Requirement page. The Date Requirement page appears within the Modeling 
page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this requirement in the Date Requirement field, and enter the revision 
identifier for this definition in the Revision field.
4.
Expand the Scheduling Details section.
5.
Select the reason associated with this requirement in the Maintenance Reason field.
6.
Enter (or select from the calendar control) the maintenance date for this requirement in the 
Schedule Date field.
7.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
8.
Click Save. The application saves the modeling object and displays a success message.
How to Add Date Requirement Notifications
Follow these steps to add Date Requirement notifications:
1.
Perform the "How to Define a Date Requirement" procedure.
Or
Select an existing Date Requirement instance.
Release 2510+ Rev. 1
Modeling User Guide
11-17
Chapter 11: Maintenance Management Definitions
2.
Expand the Notifications section.
3.
Click Add new row in the Pending E-mail Target, Due E-mail Target, or Past Due E-mail Target 
grid. A new row appears.
4.
Select an e-mail notification from the picklist in the newly added row. The notification is added to 
the grid.
5.
Enter the text for the e-mail in the corresponding Pending E-mail Text, Due E-mail Text, or Past 
Due E-mail Text field. You also have the option to use text variables.
6.
Repeat steps 3-5 to set up notifications for additional recipients.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
11-18
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Defining Recurring Date Requirements
A Recurring Date Requirement defines a resource’s maintenance schedule based on recurring calendar 
dates on which a maintenance event must occur. Each date must occur independently of when the 
previous maintenance was completed. 
The requirement definition includes the tolerance and warning allowances (in days), and the 
corresponding e-mail distribution lists for pending, due, and past due maintenance event email 
notifications. 
When Defining Recurring Date Requirements
Recurring Date Requirement contains the required Maintenance Reason modeling definition and these 
optional modeling definitions: 
•
Data Collection (parametric or user data)
•
Document Set
•
E-mail Notification
•
Electronic Signature Requirement
Maintenance requirements are required when activating a maintenance class.
Pattern and Frequency
These are the available recurring date patterns:
•
Hourly - Schedules have a fixed number of hours between each execution.
•
Daily - Schedules have a fixed number of days between each execution.
•
Weekly - Schedules have a specific day of the week.
•
Monthly - Schedules have a specific day of the month.
•
Yearly - Schedules have a month and a day during the month. 
All of these intervals support a frequency, which identifies a pattern for how often the requirement 
repeats. The number 1 indicates that the application executes the maintenance event on every scheduled 
recurrence. The number 2 indicates every other scheduled recurrence, and so forth. 
Release 2510+ Rev. 1
Modeling User Guide
11-19
Chapter 11: Maintenance Management Definitions
Recurring Date Requirement Page
This image shows an example of the Recurring Date Requirement page.
Recurring Date Requirement Page Field Definitions
This table defines the fields unique to the Recurring Date Requirement page.
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
Scheduling Details Section
Maintenance Reason
Maintenance reason associated with this requirement.
Required
Document Set
Document set associated with this requirement.
Optional
Data Collection 
Definition
Data collection or user data collection definition associated with 
this requirement.
Optional
11-20
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Field
Definition
Type
Electronic Signature 
Requirement
Electronic signature group associated with the recurring date 
requirement. Associating an electronic signature requirement 
with a date requirement requires that a user provide an 
electronic signature before the date requirement can be 
completed.
Optional
Job Model
Job Model that the application will use to create a maintenance 
job. Job Model refers to a workflow performed for the repair or 
routine maintenance of a manufacturing resource. 
Note:The application will automatically create a maintenance 
job once the maintenance state is Due. 
Optional
Recurrence Pattern
Recurring Date 
Pattern
Daily, Hourly, Monthly, Weekly, or Yearly
Required
Frequency
How often this recurring date pattern repeats:
1 - Maintenance is due on every occurrence (default value)
2 - Maintenance is due on every other occurrence
3 - Maintenance is due on every 3rd occurrence, and so on
Optional
Depending on your selection in Recurring Date Pattern, one or more of the following fields may 
appear:
Day of Month
Day of the month on which maintenance is to occur on the 
resource. This field appears when the selection in the Recurring 
Date Pattern field is Yearly or Monthly.
Required
Day of Week
Day of the week on which maintenance is to occur on the 
resource. This field appears when the select in the Recurring 
Date Pattern field is Weekly. (Weeks are defined as going from 
Sunday to Saturday.)
Required
Month of 
Year
Month of the year during which maintenance is to occur on the 
resource. This field appears when the selection in the Recurring 
Date Pattern is Yearly. (Also requires a selection in the Day of 
Month field.)
The month and the day of the month must be a valid 
combination. A date such as February 31 will return an error.
Required
Range of Recurrence
Seed Date
Date and time at which this requirement will be due pending 
activation of the requirement for the resource or maintenance 
class.
If not entered, the default is the current time on the current 
date.
Optional
Release 2510+ Rev. 1
Modeling User Guide
11-21
Chapter 11: Maintenance Management Definitions
Field
Definition
Type
Occurrences
Number of times that the requirement will occur (automatically 
calculates an end date).
Applicable if an end date is not specified; takes precedence if 
both are specified. (Both can be left blank.)
Optional
End Date
Date that this requirement will no longer validate the 
maintenance. Applicable if the number of occurrences is not 
specified. (Both can be left blank.)
Optional
Time Zone
Time zone used for the seed and end dates. Select a time zone 
for the application to use when scheduling the requirement.
The default value for new instances is the time zone selected at 
Log In. For saved instances, the field is populated with the last 
saved time zone.
Optional  
Warning and Tolerance
Warning Period
Number of days before the next scheduled date that, when 
reached, sets this maintenance requirement as pending for the 
associated resource.
Triggers the Pending e-mail.
The Pending e-mail is not sent if  allowed to default to 0.
Optional
Tolerance Period
Number of days beyond the next scheduled date that, when 
reached, sets this maintenance requirement as past due for the 
associated resource.
Triggers the Past Due e-mail and the resource becomes 
unavailable for further processing.
If allowed to default to 0, the Past Due e-mail is sent on the 
Seed Date and the resource immediately becomes unavailable 
for further processing.
Optional
Checklist grid 
Grid listing any checklists that have been configured  for the 
date requirement.
Optional
Checklist Id 
Unique checklist name to identify the checklist. 
Required
Instruction 
Free form text added during checklist configuration to  guide the 
user performing the checklist.
Required
Employee 
Group
Group of employees authorized to perform the  checklist.
Optional
Single Only
Check box to control whether this checklist may be  selected 
along with other checklists.
Optional
Data 
Collection 
Def 
Defines data collected as part of the checklist  completion 
process.
Optional
Description 
Free form text to add descriptive information about the  
checklist.
Optional
11-22
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Field
Definition
Type
Notes 
Relevant comments. You can enter a maximum of  2000 
characters.
Optional
Enforce Checklist 
Sequence 
Indicates whether the application should enforce the  sequence 
of checklist items.
Optional
Notifications
Pending E-mail Target 
grid
Grid identifying the recipients of an e-mail to be sent when 
maintenance is pending. Refer to the Warning Period field in 
this table.
Optional
Pending E-mail Text
Text of the e-mail to be sent when maintenance is pending. You 
must enter text if you specified a pending e-mail target. Text 
variables can be used.
Optional
Due E-mail Target grid Grid identifying the recipients of an e-mail to be sent when 
maintenance is due. Refer to the Seed Date field in this table.
Optional
Due E-mail Text
Text of the e-mail to be sent when maintenance is due (still 
within the tolerance period). You must enter text if you 
specified a due e-mail target. Text variables can be used.
Optional
Past Due E-mail 
Target grid
Grid identifying the recipients of an e-mail to be sent when 
maintenance is past due. Refer to the Tolerance Period field in 
this table. You must enter text if you specified a due e-mail 
target.
Optional
Past Due E-mail Text
Text of the e-mail to be sent when maintenance is past due. 
You must enter text if you specified a past due e-mail target. 
Text variables can be used.
Optional
How to Define a Recurring Date Requirement
Follow these steps to define a Recurring Date Requirement:
1.
Open the Recurring Date Requirement page. The  Recurring Date Requirement page appears 
within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this requirement in the Recurring Date Requirement field, and enter the 
revision identifier for this definition in the Revision field.
4.
Expand the Scheduling Details section.
5.
Select the reason associated with this requirement in the Maintenance Reason field.
6.
Select a date pattern  from the Recurring Date Pattern  list.
7.
Enter a number in the Frequency field to indicate how often maintenance is required.
Release 2510+ Rev. 1
Modeling User Guide
11-23
Chapter 11: Maintenance Management Definitions
8.
Did you select Monthly, Weekly, or Yearly for Recurring Date Pattern?
If . . .
Then . . .
Yes
Go to step 9.
No
Go to step 10.
9.
Complete the following:
If you selected . . .
Then . . .
Monthly
a.
Enter a numerical value for Day of Month.
b.
Go to step 10.
Weekly
a.
Select a Day of Week.
b.
Go to step 10.
Yearly
a.
Enter a numerical value for Day of Month.
b.
Select a Month of Year.
c.
Go to step 10.
10.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
11.
Click Save. The application saves the modeling object and displays a success message.
How to Add Recurring Date Requirement Notifications
Follow these steps to add Recurring Date Requirement notifications:
1.
Perform the "How to Define a Recurring Date Requirement" procedure.
Or
Select an existing Recurring Date Requirement instance.
2.
Expand the Notifications section.
3.
Click Add new row in the Pending E-mail Target, Due E-mail Target, or Past Due E-mail Target 
grid. A new row appears.
4.
Select an e-mail notification from the picklist in the newly added row. The notification is added to 
the grid.
5.
Enter the text for the e-mail in the corresponding Pending E-mail Text, Due E-mail Text, or Past 
Due E-mail Text field. You also have the option to use text variables.
6.
Repeat steps 3-5 to set up notifications for additional recipients.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
11-24
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
Defining Maintenance Classes
You can create a Maintenance Class  for  resources that have the same maintenance requirements. You can 
then reference the maintenance class in the Resource definition. Maintenance classes are used for 
activation of resources. A maintenance requirement can be assigned to one resource, or to all resources in 
the maintenance class. 
When Defining Maintenance Classes
Maintenance Class is an optional field in these Modeling definitions: Resource and Carrier.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
How to Define a Maintenance Class
Follow these steps to define a Maintenance Class:
1.
Open the Maintenance Class page. The Maintenance Class page appears within the Modeling 
page.
2.
Click New. Blank fields appear for you to define a new instance.
3.
Enter a name for this maintenance class in the Maintenance Class field.
4.
Enter  optional information according to your business requirements. Refer to "Common Fields on 
Modeling Pages" for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
11-25
Chapter 11: Maintenance Management Definitions
Referencing a Maintenance Class in the Resource
Resources that have the same maintenance requirement belong to a Maintenance Class. Maintenance 
classes also apply to carriers, which are another type of resource.
Refer to "Physical Model Definitions" for  information on resources, or carriers.
Resource Page
This image shows the Maintenance Class field on the Resource page.
How to Modify a Resource to Reference the Maintenance Class
Follow these steps to specify the Maintenance Class to which the resource belongs:
1.
Open the Resource page. The Resource page appears within the Modeling page.
2.
Click the resource that you want to modify. The Resource page appears for the selected resource.
3.
Select the appropriate Maintenance Class for this resource in the Maintenance Class field.
4.
Enter optional information according to your business requirements. Refer to the "Resource Page 
Field Definitions"  for information on this page.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
11-26
Modeling User Guide
Release 2510+ Rev. 1
Chapter 11: Maintenance Management Definitions
What Happens During a Move Standard or Move In 
Transaction
These results occur during the processing of a Move Standard or Move In transaction when the operator 
either:
•
Specifies the Move To Resource during a Move Standard,
•
Uses an Operation that requires a MoveIn (Use Queue is selected for the Operation),
•
Or both.
When . . .
And the 
maintenance 
requirement for the 
Resource . . .
Then . . .
•
The current quantity is greater than the 
maintenance requirement's thruput Qty 
warning range for the resource,
Or
•
The current quantity2 is greater than 
the maintenance requirement’s thruput 
Qty2 warning range for the resource, 
Or
•
Today is the first day of the calendar 
date warning range for the 
maintenance requirement,
is within the warning 
period,
the application sends a 
Pending email to the 
designated e-mail 
recipients.
•
The current quantity is within the 
maintenance requirement’s thruput Qty 
and the resource’s maintenance 
requirement thruput Qty + tolerance, 
Or
•
The current quantity2 is within the 
maintenance requirement’s thruput 
Qty2 and the resource’s maintenance 
requirement thruput Qty2 + tolerance, 
Or
•
Today is the first day of the 
maintenance requirement’s calendar 
date and the resource’s maintenance 
requirement calendar date + tolerance,
is due but within the 
tolerance range,
the application sends a 
Due e-mail to the 
designated e-mail 
recipients.
Release 2510+ Rev. 1
Modeling User Guide
11-27
Chapter 11: Maintenance Management Definitions
When . . .
And the 
maintenance 
requirement for the 
Resource . . .
Then . . .
•
The current quantity is greater than the 
maintenance requirement’s thruput Qty 
+ tolerance, 
Or
•
The Status Qty2 is greater than the 
maintenance requirement’s Thruput 
Qty2 + tolerance, 
Or
•
Today is the maintenance requirement’s 
calendar date + tolerance,
has exceeded the 
tolerance period,
the resource stops 
processing, and the 
application sends a Past 
Due e-mail to the 
designated e-mail 
recipients.
Processing Validation for Thruput Requirements
The Move In and Move transactions will validate the thruput requirement for the resource specified (either 
the fromResource or the toResource in the Move transaction, and the resource in the MoveIn transaction).
11-28
Modeling User Guide
Release 2510+ Rev. 1
Chapter 12: Label Printing 
Definitions
Introduction
A label is printed data, usually including a unique identifier such as the container name in readable text 
and/or barcode format, with additional data such as a production description.
Label Printing is the ability to:
•
Print labels automatically for any container transactions.
•
Print labels manually when a container  on the shop floor is being tracked in the application and 
does not require a transaction such as Move In or Move Standard to be performed at the time, but 
does need a printed label.
•
Reprint labels based on data stored in the container's manufacturing audit trail when, for 
example, a label has been damaged or did not print successfully due to a printer problem.
•
Reference label printing for Master Recipes and Recipe Lists.
You define Label Printing in your information model to use this module for your shop floor container 
transactions. This chapter discusses Label Printing concepts and pre-implementation considerations, 
describes the modeling objects that are needed to meet your Label Printing requirements, and explains 
how to create or modify them.
In This Chapter
This chapter contains these topics:
•
Label Templates and Tags
•
Pre-Implementation Information
•
Modeling Relationship Diagram
•
Defining Printer Label Definitions
•
Defining Print Queues
•
Referencing Container Label Printing in Specs and Recipe Lists
•
Referencing Label Printing for the Master Recipe
•
Referencing Production Event Label Printing in the Factory
•
Referencing Print Queues in Resources, Operations, and Factories
•
Sample Template File and Label
Release 2510+ Rev. 1
Modeling User Guide
12-1
Chapter 12: Label Printing Definitions
Label Templates and Tags
Before implementing Label Printing in your factory, you need to understand the concepts of label 
templates and tags, and consider several issues about how you want to configure Label Printing. 
Label Templates 
A label template is a file on the network—a separate document that defines the format of the container 
label to be printed. Siemens supports ASCII, UTF-8, UTF-16 LE and UTF-16 BE only for multi-byte capable 
printers for label printing template text files. Binary label printing template files are not supported. 
The template includes data on the XY position of various text and image elements, as well as tag names. 
This document does not cover the design of your label templates. The label templates are provided either 
by an external system or someone in your organization designs the label templates using design tools 
provided by your label printer manufacturer. 
Label Tags
The tag referenced in the label template is a variable, created when you define an instance of the Printer 
Label Definition object. The variable definition in the tag is resolved with the template at run time. The 
resolved data is merged with the template data to create a complete document, which can either be 
printed or written to a file.
A label tag contains these elements.
Element
Description
Name
A string that will be matched to a placeholder in the label template.
Example: 
ContainerName, ProductName
Expression
Either a literal or an expression. It is resolved at run time and replaces the 
tag placeholder in the template. If an expression, it is evaluated against 
values associated with the transaction. You can also identify a default value 
for the label tag to be used in place of the expression when that expression 
does not contain a value. 
Example:
Container.Name,Container.Product.Name,"Literal1"
Beginning and Ending 
Delimiters
Appended to the tag name to avoid a conflict if the tag name is used as a 
literal in the template itself. 
Example:
A template can contain Container: %Container%, where % is defined as 
both beginning and ending delimiter. Without the delimiters, both 
instances of "Container" will be substituted into the template.
12-2
Modeling User Guide
Release 2510+ Rev. 1
Chapter 12: Label Printing Definitions
Pre-Implementation Information
The label printing module in Opcenter EX MDD and Opcenter EX CR is implemented using multibyte 
technology. Therefore, your printer must be capable of receiving multibyte label output. Some printers can 
process multibyte data, but are not configured by default to do so. Before starting to implement label 
printing, perform the following:
1.
Confirm your barcode printer is capable of processing multibyte data.
2.
Set up/configure your printer to have the multibyte feature enabled. This may be done via the 
printer's setup menu or via a command in the label template. You will need to research how to 
set up your specific printer by reading the manual supplied by the vendor or by contacting the 
vendor's technical support.
Pre-Implementation Tasks
Before configuring container label printing, you must:
•
Set up the label printers and determine their network locations.
•
Understand the purpose of label templates and have them already set up.
•
Understand the purpose of label tags and determine the tags to use.
•
Decide which container transactions will have label printing capabilities, and:
Identify the Spec objects that will include the definition of the type of label and number of labels 
to be printed for the specified container transactions.
Decide whether to associate a print queue with the container’s resource or its operation. For 
example, if your business wants to assign resources as part of the processing, then you can set up 
a selection of resources to perform the processing at an operation, with each resource having its 
own label printer.
Identify the operations and resources that will include the network location of the label printers 
for container labels.
•
Decide whether any of the transactions that print labels will have the label information sent to a 
file instead of a label printer. The Output to File option is available if you want to process the files 
and print them at another printer or at a later time. This option requires an external method, not 
provided by Siemens, to process the files.
•
Configure the Manufacturing Audit Trail to display detailed information about printed and 
reprinted labels, if needed.
Print Spooling
You can set up a print spooler to use when printing labels. However, the print spooler should not be set up 
on the same server that is running the  Opcenter EX MDD or the Opcenter EX CR application pools and 
services.
Release 2510+ Rev. 1
Modeling User Guide
12-3
Chapter 12: Label Printing Definitions
Modeling Definition
These are the modeling object instances that you create and modify to implement Label Printing.
Modeling 
Object
Modifications
Printer Label 
Definition
Create instances of the Printer Label Definition object to:
•
Identify the network location of each pre-defined label template.
•
Define the label tags.
Print Queue
Create instances of the Print Queue object to identify the network location of each 
label printer.
Spec
Modify instances of the relevant Spec object to identify a label transaction map that 
specifies:
•
The container transactions that require labels to be printed.
•
The Printer Label Definitions to use.
•
The number of labels to be printed.
Operation
Modify instances of the relevant Operation object to identify the print queue for 
container transactions that are associated with an operation, rather than a resource.
Resource
Modify instances of the relevant Resource object to identify the print queue for 
container transactions that are associated with a resource rather than an operation.
Factory
Modify instances of the relevant Factory object to identify the print queue for 
production event transactions that will be printed for the factory. (This is the factory 
identified for the transaction, to which the default is the employee's factory if not 
received from the client.)
Modify instances of the relevant Factory object to identify a production event label 
map that specifies:
•
The production event transactions that require labels be printed.
•
The Printer Label Definitions to use.
•
The number of labels to be printed.
Note: Production events are recorded and managed in the Portal Shop Floor 
application. Refer to the Portal Shop Floor User Guide for information on printing labels 
for Portal Shop Floor production event transactions.
Master 
Recipe
Modify instances of the relevant Master Recipe object to specify the default Print Label 
Definition for any target material started for the master recipe.
Recipe List
Modify instances of the relevant Recipe List object to define a label transaction map 
that specifies: 
•
The container transactions that require labels to be printed.
•
The default Printer Label Definitions to use. 
•
The number of labels to print. 
12-4
Modeling User Guide
Release 2510+ Rev. 1
Chapter 12: Label Printing Definitions
Configuring the Manufacturing Audit Trail
You can configure the Manufacturing Audit Trail to display detailed information about printed and 
reprinted labels by:
•
Modifying the relevant UI Preference instances to establish a list of fields that display when an 
employee views the transaction history for a container.
•
Modifying Container Level instances to reference the relevant UI Preference.
•
Completing the configuration through the  Audit Trail Configuration tool.
Refer to "Manufacturing and Resource Audit Trails" for information on using the  Audit Trail Configuration 
tool.
What Happens During Transaction Processing
Labels can be printed automatically as part of container transactions, or manually as part of standalone 
printing and reprinting transactions.
During transaction processing of the designated container transaction, the transaction logic:
1.
Reads the appropriate label template file.
2.
Replaces the tags with information from the Printer Label Definition.
3.
Prints one or more copies of the label, or writes the label information to a file, based on the Print 
Queue definition.
Labels are printed after the transaction logic is committed to the database to prevent printer 
errors causing the transaction to roll back. Any errors that occur during the label printing process 
are written to the event log.
Note that the Reprint transaction uses the label history from a previously printed label to reprint 
the label.
4.
Writes the relevant data to the container history (the manufacturing audit trail). History is 
recorded for every label printed or reprinted. If configured, the  Manufacturing Audit Trail 
transaction provides detailed information about printed and reprinted labels.
Label Tag Evaluation
The label tag expressions are evaluated near the end of the transaction logic. This is because container 
values are likely to change during transaction processing. For example, if the printer definition has an 
expression of:
•
Container.Qty for a Change Quantity transaction, then the value printed on the label will be the 
new value of the quantity.
•
Container.Step for a Move Standard transaction, then the value printed on the label will be the 
container’s new step.
Release 2510+ Rev. 1
Modeling User Guide
12-5
Chapter 12: Label Printing Definitions
Modeling Relationship Diagram
This diagram shows the modeling objects for Label Printing, their relationships, and the values you set in 
each.
12-6
Modeling User Guide
Release 2510+ Rev. 1
Chapter 12: Label Printing Definitions
Defining Printer Label Definitions
The Printer Label Definition is the object that defines the network location of each pre-defined label 
template. Each printer label definition instance contains: 
•
The network location of the label template
•
The label tags (variables referenced in the label template)
When Defining Printer Label Definitions
Note the following when defining printer label definitions:
•
You cannot use invalid characters in the object name. For example, you cannot use an 
apostrophe.
Note:
Refer to the Opcenter Execution Medical Device and Diagnostics Designer User Guide 
or the Opcenter Execution Core Designer User Guide for  information on valid characters 
and reserved words.
•
Printer Label Definition is an optional field in the definition of Spec.
•
Printer label definitions require at least one label tag be defined in the Label Tag grid.
When Defining Labels for a List
You can define labels to include a variable list of items with or without hierarchy. You must reference a 
pre-defined list label template and define list expressions in the Label Tag grid.
For example, products in the material list can consist of other products. You can retain the entire hierarchy 
on the label by defining an expression relative to the material list.
This image shows an example of a list label template:
Release 2510+ Rev. 1
Modeling User Guide
12-7
Chapter 12: Label Printing Definitions
This image shows an example of the label tag selections:
This image shows the label printed for this example:
Printer Label Definition Page
This image shows an example of the Printer Label Definition page.
12-8
Modeling User Guide
Release 2510+ Rev. 1
Chapter 12: Label Printing Definitions
Printer Label Definition Page Field Definitions
This table defines the fields unique to the Printer Label Definition page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
General
Engineering Change 
Order
Engineering change order assigned to this revision. You can enter 
a maximum of 30 characters.
Optional
Details
Label Template
Network location of the template file.
Required
Begin Delimiter
Delimiter beginning the tag name to avoid a conflict when the tag 
name is used as a literal in the template.
Required
End Delimiter
Delimiter ending the tag name to avoid a conflict when the tag 
name is used as a literal in the template.
Required
Label Tag grid
Grid listing the label tags referenced in the label template.
Required
Label Tag 
Name
Name of the tag.
Required
Expression
Literal or expression that will be resolved at run time and will 
replace the tag placeholder in the template. The expression is 
evaluated against values associated with the transaction.
Required
Is List
Select to indicate labels will include a variable list of items.
Optional
Hierarchical 
Expression
Part of the expression that is resolved at run time and is used as 
the top level of the hierarchy for a list of items. 
For example: Container.Product.BOM.MaterialList.
Note: This field is used for list item printing only. 
Optional
List Item 
Expression
Part of the expression used for the list item value.
For example: Product.BOM.MaterialList.
Note: This field is used for list item printing only.
Optional
Depth
Number of times the item is repeated on the label. The default 
value is 10.
Note: This field is used for list item printing only. 
Optional
Default 
Expression
Literal or expression to be used if the Expression field does not 
contain a value.
Optional
How to Define a Printer Label Definition
Follow these steps to define a printer label definition:
1.
Open the Printer Label Definition page. The Printer Label Definition page appears within the 
Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
Release 2510+ Rev. 1
Modeling User Guide
12-9
Chapter 12: Label Printing Definitions
3.
Enter a name for this Printer Label Definition in the Printer Label Definition field.
4.
Enter a revision name in the Revision field.
5.
Expand the Details section.
6.
Enter the network location of the label template file in the Label Template field.
7.
Enter a value in the Begin Delimiter field.
8.
Enter a value in the End Delimiter field.
9.
Complete the "How to Add the Tag Information to the Printer Label Definition" procedure.
How to Add the Tag Information to the Printer Label Definition
Follow these steps to add tag information to the printer label definition:
1.
Perform the "How to Define a Printer Label Definition" procedure.
2.
Click Add new row in the Label Tag grid to add the tag information to this Printer 
Label Definition. A new row appears.
3.
Enter a name for the label tag in the Label Tag Name field.
4.
Enter an expression in the Expression field.
5.
Repeat steps 2-4 to add additional label tags.
6.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
7.
Click Save. The application saves the modeling object and displays a success message.
12-10
Modeling User Guide
Release 2510+ Rev. 1
Chapter 12: Label Printing Definitions
Defining Print Queues
The Print Queue is the object that identifies the network location of the printer that is used to print the 
container or nonconformance label. 
When Defining a Print Queue
The Print Queue Page contains the option to write a template to a file instead of sending it to a printer. If 
you select this option, the template information will be written to a .txt file according to the directory and 
base file name that you specify. The text file itself will have the following predefined naming convention: 
<base file name>_<name of transaction>_<date stamp>_<time stamp>_<thread ID>_ 
<process ID>_<label count>.txt 
Example: Assume the Print File field contains the entry server2\myfile and one label is to be printed for 
the Start transaction. The resulting file stored on server2 might be named as follows: 
myfile_Start_20061114_225850513_2332_1944_1.txt
You can specify a label encoding type when defining a print queue. Possible selections include ASCII, UTF-
16 BE, UTF-16 LE, and UTF-8. Select the encoding type that matches the printer to which you are sending 
output. 
Selecting the Output to File option causes the application to encode the template to a file. If the template 
file is in the ANSI format, selecting the Output to File option causes the application to encode the template 
file with the format selected in the Label Encoding field. If the template file is not in the ANSI format, the 
application encodes the file using the UTF-16 LE format.
Note the following when defining a print queue:
•
You cannot use invalid characters in the object name. For example, you cannot use an 
apostrophe.
Note:
Refer to  the Opcenter Execution Medical Device and Diagnostics Designer User Guide 
or the Opcenter Execution Core Designer User Guide for  information on valid characters 
and reserved words.
•
Print Queue is an optional field in the definition of Resource and Operation.
Release 2510+ Rev. 1
Modeling User Guide
12-11
Chapter 12: Label Printing Definitions
Print Queue Page
This image shows an example of the Print Queue page.
Print Queue Page Field Definitions
This table defines the fields unique to the Print Queue page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
Details
Print 
Queue 
Path
Network path of the printer at which container labels print.
Required
Label 
Encoding
List of  encoding formats. Options include the following:
•
ASCII
•
UTF-16 BE
•
UTF-16 LE
•
UTF-8
Select the type that matches the printer to which you are sending output. The 
print process' default is UTF-16 LE if you do not select a value.
Optional
Output to 
File
Check box indicating that the template data will be written to a file instead of 
being sent to a printer. The file is encoded with the method selected in the 
Label Encoding field.
Note: The template is encoded in UTF-16 LE format if the template is not in 
ANSI format. The template is encoded with the encoding format that is set in 
the Label Encoding field if the template is in the ANSI format.
Optional
12-12
Modeling User Guide
Release 2510+ Rev. 1
Chapter 12: Label Printing Definitions
Field
Definition
Type
Print File
Network location (and optionally, a base name) of the file to which the 
template data will be written if the Output to File option is selected. The base 
name, if specified, is added to the beginning of the pre-defined text file 
name.
Optional
How to Define a Print Queue
Follow these steps to define a Print Queue:
1.
Open the Print Queue page. The Print Queue page appears within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter the name for this print queue in the  Print Queue field.
4.
Enter the path of the network printer location at which you want to print container labels in the  
Print Queue Path field.
5.
Do you want to write the template data to a file instead of printing it?
If . . .
Then . . .
Yes
a.
Select the Output to File option.
b.
Select an encoding format in the Label Encoding field if you 
are encoding a template in ANSI format.
c.
Enter the appropriate network path in the Print File field.
d.
Go to step 6.
No
Go to step 6.
6.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
7.
Click Save. The application saves the modeling object and displays a success message.
Release 2510+ Rev. 1
Modeling User Guide
12-13
Chapter 12: Label Printing Definitions
Referencing Container Label Printing in Specs and Recipe 
Lists
You must modify the relevant Spec or Recipe List revisioned objects to include a label transaction map that 
specifies the following to  implement Label Printing after you have defined it:
•
The container transactions that are to print labels
•
The Printer Label Definitions to use
•
The number of labels to be printed
When Referencing Container Label Printing
This topic only covers the basic steps to associate Printer Label definitions with a Spec. Refer to "Defining 
Specs" for details about each field on the Spec page.
The Txn Type field in the Label Txn Map grid displays all  transactions for a Spec.
Important:
Refer to "Label Templates and Tags" before modifying instances of the Spec object.
You do not need to reference label printing on a Spec when you reference label printing on the Recipe List.
The Target Material Container is represented by the Material Container field in the Service. The Label Tag 
Expression should reference MaterialContainer.Name if you want to reference the name of the Target 
Material Container field in the Printer Label Definition.
This expression can be used if the Printer Label Definition is to be used by Execute Recipe Task and by 
other services:
IsFieldDefined(MaterialContainer)?MaterialContainer.Name:Container.Name
Label Txn Map
The Label Txn Map grid appears on the Recipe List and Spec modeling objects.
12-14
Modeling User Guide
Release 2510+ Rev. 1
Chapter 12: Label Printing Definitions
How to Add a Printer Label Definition to a Spec
Follow these steps to establish your label printing requirements for a Spec:
1.
Open the Spec page. The Spec page appears within the Modeling page.
2.
Select an existing Spec instance. The application updates the Spec page to display the values for 
that instance.
3.
Click Add new row in the Label Txn Map grid. A new row appears.
4.
Select the specific transaction for which container labels are to be printed in the Txn Type field. 
5.
Select the Printer Label Definition to associate with the transaction. 
6.
Enter the number of labels to print for this transaction in the Label Count field. This can be a 
number or an expression, such as Container.Qty.
7.
Repeat steps 3-6 to map additional labels to transactions.
8.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Add a Printer Label Definition to a Recipe List
Follow these steps to add a Printer Label Definition to a Recipe List:
1.
Open the Recipe List page. The Recipe List page appears within the Modeling page.
2.
Select an existing Recipe List instance. The application updates the Recipe List page to display 
the values for that instance.
3.
Click Add new row in the Label Txn Map grid. A new row appears.
4.
Select the specific transaction for which container labels are to be printed in the Txn Type field. 
5.
Select the Printer Label Definition to associate with the transaction. 
6.
Enter the number of labels to print for this transaction in the Label Count field. This can be a 
number or an expression, such as Container.Qty.
7.
Repeat steps 3-6 to map additional labels to transactions.
8.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
12-15
Chapter 12: Label Printing Definitions
Referencing Label Printing for the Master Recipe
The Master Recipe revisioned data object contains a Printer Label Definition field. This field allows you to 
define a default Printer Label Definition for any Target material started for the master recipe. The field 
provides a  list of all printer label definitions that have been created in Modeling.
When Referencing Label Printing for the Master Recipe
You must create a new master recipe or select an existing master recipe before you can add a Printer Label 
definition.
Master Recipe Page Details Section
The Printer Label Definition field is located in the Details section of the Master Recipe page.
How to Reference Printer Label Definition in Master Recipe
Follow these steps to reference a Printer Label definition in Master Recipe:
1.
Open the Master Recipe page. The Master Recipe page appears within the Modeling page.
2.
Select an existing master recipe. 
Or
Create a new one by performing the "How to Define a Master Recipe" procedure.
3.
Expand the Details section.
4.
Select a Printer Label Definition from the  list.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
12-16
Modeling User Guide
Release 2510+ Rev. 1
Chapter 12: Label Printing Definitions
Referencing Production Event Label Printing in the 
Factory
You must modify the Factory object to contain the following to implement Label Printing for 
nonconformances:
•
Identify the print queue in the production event transactions that will print labels for the factory. 
(This is the factory identified for the transaction, which defaults to the employee's factory if not 
received from the client.)
•
Identify a production event label transaction map that specifies:
•
The production event transactions that are to print labels
•
The Printer Label Definitions to use
•
The number of labels to be printed (can be an expression, such as GetListCount
(QualityObject.EventData.EventLogs).
Note:
Production events are recorded and managed in the Portal Shop Floor application. Refer to the 
Portal Shop Floor User Guide for information on printing labels for Portal Shop Floor pro-
duction event transactions.
Refer to "Label Templates and Tags"  before modifying instances of the Factory object.
How to Add a Print Queue and a Production Event Printer Label Definition to a Factory
Follow these steps to establish your production event label printing requirements for a factory:
1.
Open the Factory page. The Factory page appears within the Modeling page.
2.
Select an existing factory. The application displays the information for the factory.  
3.
Select a Print Queue if you want to use a single printer to print all of the production event labels 
for the factory.
4.
Expand the Transactions section.
5.
Click Add new row in the Production Event Label Map grid. A new row appears.
6.
Select a production event Txn Type for which you want labels printed.
7.
Select a Printer Label Definition to associate with the production event txn type.
8.
Enter the number of labels to be printed for this transaction in the Label Count field.
9.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
12-17
Chapter 12: Label Printing Definitions
Referencing Print Queues in Resources, Operations, and 
Factories
In addition to modifying specs to refer to the Printer Label Definitions, you also modify either the 
Resource, the Operation, or Factory object to reference the Print Queue definition.
The Print Queue definition is retrieved at run time as follows:
When the container or 
transaction . . .
Then the Print Queue is retrieved from . . .
is associated with a resource,
the Resource definition.
Exception: In the Start transaction, the resource is referenced 
from the Start details.
is not associated with a resource,
the Operation definition.
Refer to "Label Templates and Tags"  before modifying instances of the Resource or Operation objects.
How to Reference a Print Queue Definition in a Resource
Follow these steps to reference a Print Queue in a Resource:
1.
Open the Resource page. The Resource page appears within the Modeling page.
2.
Select the resource you want to modify. The application displays the information for the 
resource.
3.
Select the print queue definition you want from the Print Queue list.
4.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Reference a Print Queue Definition in an Operation
Follow these steps to reference a Print Queue definition in an Operation:
1.
Open the Operation page. The Operation page appears within the Modeling page.
2.
Click the operation that you want to modify. The application displays the information for the 
operation.
3.
Expand the Details section.
4.
Select the print queue definition you want from the Print Queue list.
5.
Click Save. The application displays a success message indicating the modeling object was 
updated.
12-18
Modeling User Guide
Release 2510+ Rev. 1
Chapter 12: Label Printing Definitions
Sample Template File and Label
This topic provides a sample label template and shows an example of a printed label that uses the 
template.
Label Printer Template File
This file represents a sample label template that is specific to a Zebra® printer from ZIH Corporation.
Release 2510+ Rev. 1
Modeling User Guide
12-19
Chapter 12: Label Printing Definitions
Printed Label
This is an example of a printed label that uses the sample template.
Working with a Binary File
You can create a template output file in ZPL (Zebra Print Language) format if your barcode label printing 
software, such as BarTender®, produces a binary file.
The software enables you to trace an output file through the printer-specific driver. This involves 
modifying the Zebra printer properties to set a logging option that will record the printer code. The result 
is a .prn file, which with the Zebra printer driver, is the needed ZPL file format.
Refer to the manufacturer’s documentation for information specific to your barcode label printing 
software.
12-20
Modeling User Guide
Release 2510+ Rev. 1
Chapter 13: Operator Training and 
Certification
Introduction
The business process of employee training dictates that manufacturing employees are appropriately 
trained and certified for a specific task before performing it. The Operator Training and Certification 
feature provides the ability to configure your information model so that you can meet your operator 
training and certification objectives.
You must:
•
Define training requirements and associate them with different modeling objects.
•
Create and update employees’ training status against training requirements.
In This Chapter
This chapter contains these topics:
•
Training Requirements and Records
•
Modeling Sequence
•
Defining Training Requirements
•
Defining Training Requirement Groups
•
Referencing Training Requirement Groups
•
Defining Training Record  Statuses
•
Defining Training Plans
Release 2510+ Rev. 1
Modeling User Guide
13-1
Chapter 13: Operator Training and Certification
Training Requirements and Records
Training Requirements and Training Records are the key components of the operator training and 
certification process.
Training Requirements
When you create a Training Requirement, you define the following information:
•
Effective date information to indicate whether the Training Requirement is active or will become 
active at a future date
•
A list of designated trainers who are allowed to administer the users’ training records
•
Reference to an external file that can contain standard operating procedures and other details 
required by your business
You organize Training Requirements into groups that are referenced by modeling objects such as the 
Enterprise, Factory, Products, Product Families, Work Centers, Operations, Specifications, and Resources.
You can define multiple revisions of a Training Requirement as dictated by your business rules.
Training Records
Training Records track the status of a particular user for a Training Requirement. Siemens recommends 
that you assign users a Training Record for each Training Requirement. Training Records are created and 
updated by trainers designated in the Training Requirement.
Training Records provide this information:
•
Training Record Status to indicate whether the holder of the record is qualified to perform a 
transaction and whether an ESig is required 
•
Reference to a specific revision of a Training Requirement (not the Revision of Record)
•
Expiration date based on Training Requirement or specified by the training record administrator
•
References to multiple Training Records from each user
Training Record Expiration Dates
You specify expiration dates in the active Training Requirement and initially used by the associated 
Training Record, but a Training Record can have its own expiration date. A Training Requirement is 
considered Active if the expiration date for it has not passed.
The Training Record follows these rules to determine the expiration date initially:
•
If only the expiration date is specified in the Training Requirement, then the record uses that date 
as is.
•
If only the expiration period (in days) is specified in the Training Requirement, expiration date is 
determined by adding the number of days to the date the record was created (the transaction 
date).
13-2
Modeling User Guide
Release 2510+ Rev. 1
Chapter 13: Operator Training and Certification
•
If both expiration date and period are specified in the Training Requirement, the application logic 
applies the earlier date.
•
The training record administrator can override the expiration date any time.
Enabling Electronic Signatures for Training Record Management
The Modeling ESig page enables you to assign an electronic signature requirement to three different 
actions on a training record management  service: 
•
Create
•
Delete
•
Update
Training Record Maint services are available under the Subentity Maintenance service on the Modeling 
Esig page available from the Modeling menu. Refer to "Modeling Electronic Signature Information" for 
information on assigning electronic signatures for training record management tasks on the Modeling Esig 
page.
Enforcing Training Requirements in Shop Floor Transactions
You define Training Requirements for your information modeling objects referenced by the Opcenter EX 
MDD or Opcenter EX CR application pools and services and container. For example, a Move transaction is 
associated with a Factory and its Enterprise; and a container is associated with a Resource, an Operation, a 
Product and its Product Family, and so on.
Transactions With Training Requirements
These transactions reference the user’s Training Records to determine if the Training Requirements are 
met:
•
ChangeQty
•
ComponentIssue
•
ComponentRemove
•
MoveIn
•
MoveStd
•
Execute Task
•
Rework
•
Start
Validation Process
When a user performs a transaction on a container, the application checks the following:
1.
All Training Requirements associated with the modeling objects are accumulated.
Release 2510+ Rev. 1
Modeling User Guide
13-3
Chapter 13: Operator Training and Certification
2.
The user’s Training Records are read and validated against the accumulated Training 
Requirements to see which requirements are active.
3.
The Training Records are validated in this order:
a.
The transaction date must be within the range of the Training Requirement’s effective dates.
b.
The permission must denote that the user is allowed to perform the transaction.
c.
The transaction date must be earlier than the Training Record’s expiration date.
If the above conditions are met, the transaction completes successfully. Otherwise, it fails and an 
appropriate error message is displayed.
Active Training Requirements and Effective Dates
Training Requirements can be considered active or inactive, depending on the requirement’s effective 
dates. Only active Training Requirements are validated when users perform transactions. The following 
field values are used to determine the active status of a Training Requirement:
•
Effective From Date
•
Effective Thru Date
These rules determine if a Training Requirement is still active:
•
If you enter both the Effective From and Effective Thru Date fields, the date the user performs the 
transaction must be within those two dates.
•
If you enter only the Effective From Date, the transaction date must be equal to or later than the 
Effective From Date.
•
If you enter only the Effective Thru Date, the transaction date must be earlier than or equal to the 
Effective Thru Date.
•
If you leave the two fields blank, then the Training Requirement will never expire.
Additional Considerations
When you set these fields during Training Requirement definition, you need to consider the modeling 
objects that use these requirements. For example, if the requirement is for the operation of a specific 
equipment (resource), you will probably want the Training Requirement to be active always to ensure that 
users are trained on how to use that equipment. If the equipment will be upgraded with a new model, you 
will create a new revision of the Training Requirement that will have a specified Effective From Date, timed 
with the installation and deployment of the new equipment. Training Records will then be additionally 
updated to reference the new revision of the Training Requirements.
13-4
Modeling User Guide
Release 2510+ Rev. 1
Chapter 13: Operator Training and Certification
Modeling Sequence
This diagram shows the sequence of modeling tasks to configure for operator training and certification.
Release 2510+ Rev. 1
Modeling User Guide
13-5
Chapter 13: Operator Training and Certification
Defining Training Requirements
Training Requirements, together with a user’s training records, are validated at the time a user initiates a 
shop floor transaction. Training requirements contain the detailed definitions for your operator training 
and certification process. 
Important:
A training record references a specific revision of the training requirement—not the 
revision of record.
When Defining Training Requirements
Verify you have defined these modeling objects before defining training requirements:
•
Employees to be designated as trainers
•
Document Sets that refer to one or more external file
You need to do the following when defining training requirements:
•
Specify expiration dates or periods that determine if the requirements are still active at the time 
they are validated.
•
Assign trainers for this requirement.
•
Link the requirement to an external file to be referenced as required.
Note the following:
•
Training Requirement contains the optional Document modeling definition and the required 
Employee modeling definition. (Employees are added as trainers.)
•
Training Requirement is required in the Training Requirement Group modeling definition and 
when adding a training record on the shop floor.
•
Training Requirement is optional in these modeling definitions:
•
Employee, when associating a training plan
•
Training Plan
When Using a Training Requirement
When selecting a date, the format of the date depends on the language preference set in Portal Studio or 
your browser.
13-6
Modeling User Guide
Release 2510+ Rev. 1
Chapter 13: Operator Training and Certification
Training Requirement Page
This image shows an example of the Training Requirement page.
Training Requirement Page Field Definitions
This table defines the fields unique to the Training Requirement page.
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
Details
Engineering 
Change Order
Engineering change order assigned to this revision. You can enter a 
maximum of 30 characters.
Optional
SOP Document
External standard operating procedures document being referenced by 
this requirement.
Optional
Expiration Date
Date this training requirement expires. Used to initialize the expiration 
date of the training requirement, unless an expiration period is also 
provided.
Optional
Expiration Period 
(Days)
Number of days this training requirement is considered valid. Between 
this entry and the expiration date, the calculated earlier date will be 
applied.
Optional
Release 2510+ Rev. 1
Modeling User Guide
13-7
Chapter 13: Operator Training and Certification
Field
Definition
Type
Effective From 
Date
Date on which this training requirement becomes effective.
Optional
Effective Thru 
Date
Ending effective date (in mm/dd/yyyy hh:mm AM/PM format) for the 
message.
Optional
Trainers grid
List of employees designated as trainers for this training requirement.
Required
How to Define a Training Requirement
Follow these steps to define a Training Requirement:
1.
Open the Training Requirement page. The Training Requirement page appears within the 
Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter a name for this requirement in the Training Requirement field.
4.
Enter the revision of this requirement in the Revision field.
5.
Click Add new row in the Trainers grid. A new row appears.
6.
Select a trainer.
7.
Repeat steps 5-6 to add additional trainers. 
8.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
9.
Click Save. The application saves the modeling object and displays a success message.
13-8
Modeling User Guide
Release 2510+ Rev. 1
Chapter 13: Operator Training and Certification
Defining Training Requirement Groups
A training requirement group is a collection of individual training requirements and training requirement 
groups (a group of subgroups). Grouping Training Requirements: 
•
Provides a convenient way of associating multiple requirements with a given modeling entity like 
an operation or factory.
•
Allows your modeling objects to reference multiple but related requirements as a collection 
rather than referring to one requirement at a time.
When Defining a Training Requirement Group
All training Requirements must belong to a group, even if the group has only one Training Requirement. 
This is because your modeling objects reference a Training Requirement Group rather than single Training 
Requirement definitions.
Verify that you have defined one or more Training Requirements before defining your Training 
Requirement Groups.
Note the following:
•
Training Requirement Group is referenced by:
•
Enterprise
•
Factory
•
Product
•
Work Center
•
Operation
•
Resource
•
Spec
•
Task
•
Training Requirement Group references:
•
Training Requirement
•
Training Requirement Group
Release 2510+ Rev. 1
Modeling User Guide
13-9
Chapter 13: Operator Training and Certification
Training Requirement Group Page
This image shows an example of a Training Requirement Group page.
Training Requirement Group Page Field Definitions
The Training Requirement Group page contains these unique fields. 
Refer to "Common Fields on Modeling Pages" for information on the fields common to all modeling 
objects.
Field
Definition
Type
Details
Entry Type
Name of the type of objects contained in this object group.
Display 
Only
Entries grid
Grid listing the training requirements assigned to this group. 
The list of available training requirements is displayed from 
the objects already defined.
Optional
Groups grid
Grid listing other training requirement groups assigned to this 
group. The list of available groups is displayed from the other 
groups already defined on the Training Requirement Group  
page.
Optional
13-10
Modeling User Guide
Release 2510+ Rev. 1
Chapter 13: Operator Training and Certification
How to Create a Training Requirement Group Definition
Follow these steps to create a Training Requirement Group definition:
1.
Open the Training Requirement Group page. The Training Requirement Group page appears 
within the Modeling page.
2.
Click New. Blank fields appear for you to define a new instance. 
3.
Enter the name in the Training Requirement Group field.
4.
Enter  optional information according to your business requirements. Refer to the field definitions 
table for information on the optional fields.
5.
Click Save. The application saves the modeling object and displays a success message.
How to Add a Training Requirement
Follow these steps to add a training requirement:
1.
Perform the "How to Create a Training Requirement Group Definition" procedure.
2.
Click in a blank field in the Entries grid. 
Or
Click Add new row in the Entries grid. A new row appears.
3.
Select a Training Requirement or its revision from the  menu in the new row.
4.
Select the Is Revision of Record check box if the revision is the ROR.
5.
Click outside the grid to add the Training Requirement. The Training Requirement is added to the 
Entries grid.
6.
Repeat steps  2-5 to add more Training Requirements.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
How to Add a Training Requirement Group
Follow these steps to add a training requirement group:
1.
Perform the "How to Create a Training Requirement Group Definition" procedure.
2.
Click in a blank field in the Groups grid. 
Or
Click Add new row in the Groups grid. A new row appears.
3.
Select a group or  its revision from the menu in the new row.
4.
Select the Is Revision of Record check box if the revision is the ROR.
5.
Click outside of the grid to add the group. The group is added to the Groups grid.
6.
Repeat steps  2-5 to add more groups.
7.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
13-11
Chapter 13: Operator Training and Certification
Referencing Training Requirement Groups
This topic explains how to associate Training Requirement Groups with different modeling objects.
When Referencing Training Requirement Groups
Before you reference a training requirement group, you must have defined one or more of these entities:
•
Enterprise
•
Factory
•
Product Family
•
Product
•
Work Center
•
Operation
•
Resource
•
Spec
•
Task
These objects can reference Training Requirement Groups only and not individual Training Requirements. 
Even if a modeling object has only one Training Requirement, you need to create a group for that 
requirement before associating it with the modeling object.
13-12
Modeling User Guide
Release 2510+ Rev. 1
Chapter 13: Operator Training and Certification
Spec Page
This image shows an example of the Training Requirement Group field for a Spec modeling object.
How to Reference a Training Requirement Group
Follow these steps to reference a Training Requirement Group on a modeling object:
1.
Select an eligible modeling object from the Modeling tab. The definition page appears for the 
selected object.
2.
Expand the Processing section.
3.
Select a group from the  menu in the Training Requirement Group field.
4.
Click Save. The application displays a success message indicating the modeling object was 
updated.
Release 2510+ Rev. 1
Modeling User Guide
13-13
Chapter 13: Operator Training and Certification
Defining Training Record  Statuses
A Training Record Status is a type of User Code. A Training Record Status provides the basis for 
determining whether the person performing the tasks is qualified. The Training Record Status codes you 
create here will be the selection list of values used by the trainers during training record administration.
Examples
You can create multiple, custom training record status codes as required by your business. These are some 
examples of training record status codes:
•
In Training - Can indicate the employee is currently undergoing training for certification
•
Certified - Can indicate the employee is qualified to perform the task
•
Decertified - Can indicate the employee needs to update skills required to perform the task
•
Not Certified - Can indicate the employee has not yet begun the training and is not qualified or 
authorized to perform a specific task
•
Trainer - Can indicate the employee is qualified to perform the task
Permission
As part of the Training Record Status code definition, you associate an authorization to allow or disallow 
the performance of a task. You can also set the permission to allow the task to be performed only if the 
appropriate electronic signatures are captured.
For example, you can set up your system so that an employee with Certified or Trainer status will be 
allowed to perform transactions, while those with Not Certified or Decertified status will not be allowed to 
perform transactions. You could also set one or more of the certifications, such as In Training, to be 
allowed, but only with the appropriate electronic signature.
When Defining a Training Record Status Code
If you select Allow with ESig as the permission, a user is allowed to perform a function requiring a 
specified training requirement only if the required electronic signature data for the associated transaction 
is successfully collected. This requires that the spec at which the training requirement validations are to 
occur has electronic signature requirements associated to it.
Note:
The Training Record Status is referenced by Training Record.
13-14
Modeling User Guide
Release 2510+ Rev. 1
