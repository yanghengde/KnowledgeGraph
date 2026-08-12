Chapter 18b: Sales Order Modeling
Introduction
Sales Orders represent customer-driven production demands. They define what product to
produce, in what quantity, and track the containers that fulfill the order. Sales Orders
bridge the ERP/customer side with MES shop floor execution.

In This Chapter
• SalesOrder (Customer Sales Order)

SalesOrder
A SalesOrder is a customer-facing production order. Unlike MfgOrder which focuses on
manufacturing execution details (workflow, BOM, routing), SalesOrder provides the
customer delivery perspective with product, quantity, and container tracking.

Relationship chain:

    SalesOrder ──(ORDERS_PRODUCT)──▶ Product
               ──(TRACKS_CONTAINER)──▶ Container

Field Definitions:
- Name (String, Required): Unique sales order identifier.
- Description (String): Description of the sales order.
- Product (Navigation): Product to be produced.
- Qty (Float): Planned order quantity.
- Qty2 (Float): Secondary quantity (alternate UOM).
- UOM (Navigation): Primary unit of measure.
- UOM2 (Navigation): Secondary unit of measure.
- WipMsgDefMgr (Navigation): WIP message definition manager.
- Notes (String): Internal notes.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- FilterTags (String): Filter tags.
- IconId (Integer): UI icon identifier.
- AssociatedPackages (Integer): Count of associated packages.
- ChangeHistory (Navigation): Change history tracking.
- Containers (SubentityList, ReadOnly): List of containers tracked against this order.
