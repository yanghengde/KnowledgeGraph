Chapter: Tooling Management
Introduction
The Tooling module tracks physical implements used during manufacturing that are not consumed directly into the product (like materials) and are not stationary machinery (like Resources). Examples include fixtures, molds, drill bits, and calibration devices.

Classes:
- Tool: A specific physical item identified by a unique ID or barcode (e.g., Mold-X900-Serial-001).
- ToolGroup: A logical grouping of interchangeable tools.
- ToolStatus: The lifecycle state of a tool (e.g., In Use, Needs Calibration, Scrapped).
