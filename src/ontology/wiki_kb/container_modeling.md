Chapter 11: Container and WIP Tracking
Introduction
The Container is the most fundamental transaction object in Opcenter Execution. It represents the 
physical or logical grouping of material moving through the manufacturing process (Work In Process / WIP).

In This Chapter
• Defining Containers
• Batches and Lots
• Carriers and Equipment

Container
A Container is the primary vehicle for tracking WIP. Everything done on the shop floor—starting, 
moving, holding, or scrapping material—is performed on a Container.

Field Definitions:
- Name (String): Unique identifier (usually auto-generated).
- Product (String): The product being manufactured in this container.
- Qty (Integer): Number of units in the container.
- Workflow (String): The active routing the container is following.
- CurrentStep (String): The step the container is currently at.
- Status (String): Active, Hold, Closed, Scrapped.

Batch
A Batch represents a specific production run, usually mixing materials. Multiple containers can 
belong to the same batch for traceability.

Field Definitions:
- BatchID (String): Unique identifier.
- ExpirationDate (Date): When the batch expires.

Lot
A Lot represents raw materials received from a supplier. It tracks supplier traceability before 
materials are issued to a WIP Container, and manages quality sampling and material shelf-life.

Field Definitions:
- LotNumber (String): Supplier lot number for traceability.
- VendorName (String): Name of the supplier who provided the material.
- Supplier (String): Supplier identifier or code.
- PONumber (String): Purchase order number associated with this lot.
- DateCode (String): Material date code stamped by the supplier.
- Qty (Float): Current quantity of material in the lot.
- ReceivedDate (Date): Date when the lot was received at the factory.
- ExpirationDate (Date): Expiration or shelf-life date for the material.
- LotStatus (Integer): Numeric status code of the lot (e.g., Released, On Hold, Expired).
- Description (String): Descriptive notes about the lot.
- SampleRate (Integer): Sampling rate for incoming quality inspection.
- SamplingPassed (Boolean): Whether the lot passed incoming inspection sampling.
- SamplingCompleted (Boolean): Whether the sampling process has been completed.
- CreationDate (Date): Date when the lot record was created in the system.
- IsFrozen (Boolean): Indicates whether the lot definition is frozen (read-only).
- CDOTypeId (Integer): Common Domain Object type ID.
- ChangeCount (Integer): Change counter for optimistic locking.

Carrier
A Carrier represents a physical tote, cassette, or tray that holds containers.

Field Definitions:
- CarrierID (String): Unique RFID or barcode of the carrier.
- Capacity (Integer): Max containers it can hold.
