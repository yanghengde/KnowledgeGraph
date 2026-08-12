Chapter 18: Order and Dispatch Modeling
Introduction
The Order module manages what needs to be produced, in what quantities, and the rules governing 
how work is prioritized on the shop floor.

In This Chapter
• MfgOrder
• DispatchRule

MfgOrder
A Manufacturing Order (MfgOrder) represents a request to produce a specific quantity of a Product.
Containers are tracked against MfgOrders to fulfill the requested quantity. MfgOrders drive shop 
floor execution by defining what product to make, how much, by when, and with what workflow.

The materials required for a MfgOrder are NOT defined directly on the order itself. Instead, they 
are resolved through the BOM (Bill of Materials) chain:

    MfgOrder → Product → BOM → BOMItem → Material
              └── eS_ProductionBOM (optional BOM override, replaces Product's default BOM)

When an order is created, the BOM items are resolved and copied into MfgOrder.MaterialList as a 
runtime material requirement snapshot (MfgOrderMaterialListItm). This is a derived list from the 
BOM, not a direct Material definition. Any changes to the source BOM after order creation do NOT 
automatically propagate to the order's material list.

Field Definitions:
- Name (String, Required): Unique identifier for the manufacturing order (e.g., MO-00123).
- Description (String): Description of the order's purpose or context.
- Product (Navigation): The product to be manufactured. This product's BOM defines the required materials.
- eS_ProductionBOM (Navigation): Optional BOM override. If set, replaces the Product's default BOM.
- Qty (Float): Planned order quantity to produce.
- Qty2 (Float): Secondary quantity (e.g., weight or alternate UOM).
- QtyStarted (Float, ReadOnly): Quantity already started in production.
- Qty2Started (Float, ReadOnly): Secondary quantity already started.
- UOM (Navigation): Primary unit of measure for the order quantity.
- UOM2 (Navigation): Secondary unit of measure.
- OrderStatus (Navigation): Current status of the order (e.g., Planned, Released, InProgress, Completed, Closed).
- OrderType (Navigation): Order type classification (e.g., Standard, Rework, Repair).
- Priority (Navigation): Manufacturing priority level.
- PlannedStartDate (Date): Planned production start date.
- PlannedCompletionDate (Date): Planned production completion date.
- ReleaseDate (Date): Date when the order is released to production.
- DueDate (Date): When the order is due for completion.
- MaterialList (SubentityList, ReadOnly): Runtime snapshot of material requirements, resolved from the BOM chain at order creation. Each entry references a Material but is owned by this order (MfgOrderMaterialListItem), not a direct BOMItem.
- HasMaterialList (Boolean): Whether the order includes a resolved material list.
- MfgOrderExecutedTaskList (SubentityList): List of executed tasks associated with this order.
- Containers (SubentityList, ReadOnly): List of containers tracked against this order.
- MfgLine (Navigation): Manufacturing line assigned to this order.
- ReportingFactory (Navigation): Factory where this order is reported.
- Workflow (Navigation): Workflow / Bill of Process used to produce this order.
- BillOfProcess (Navigation): The specific BOP (Bill of Process) for this order.
- IsWorkflow (Navigation): Whether the order uses a workflow.
- ConsumingOrder (String): Reference to a parent/consuming order if this is a sub-order.
- CustomerReference (String): Customer reference or sales order number.
- PONumber (String): Purchase order number (for customer-driven orders).
- PISO (String): PI/SO reference number.
- ProjectCode (String): Project code for tracking and reporting.
- ModelNumber (String): Product model number.
- ReworkId (String): Rework identifier if this is a rework order.
- RMANumber (String): RMA (Return Material Authorization) number.
- ExternallyControlled (Boolean): Whether the order is controlled by an external system (e.g., ERP).
- IsKittingOrder (Boolean): Whether this is a kitting order.
- DefaultLot (String): Default lot number for produced containers.
- DefaultPutawayStockPoint (String): Default stock point for putaway.
- ContainerNumberingRule (Navigation): Rule for numbering containers produced by this order.
- CompletionPlan (String): Completion plan identifier.
- MPSDate (String): Master Production Schedule date.
- PMDemandDate (String): PM demand date.
- IsFrozen (Boolean, ReadOnly): Whether the order is frozen for editing.
- Notes (String): Internal notations or comments.
- Attributes (UserAttribute): Custom user-defined attributes.

DispatchRule
A Dispatch Rule determines the priority of Containers queuing at a WorkCenter (e.g., FIFO, Earliest Due Date).

Field Definitions:
- RuleName (String): Name of the rule.
