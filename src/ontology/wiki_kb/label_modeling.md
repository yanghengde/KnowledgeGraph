Chapter: Label and Printing
Introduction
The Label module manages how barcode labels, packing slips, and shipping labels are generated and printed during production. It decouples the data payload from the physical printer routing.

Classes:
- Label: The abstract definition of a label.
- LabelFormat: The physical template (e.g., ZPL file, Bartender template) used to render the label.
- Printer: The physical hardware device on the factory floor mapped to specific WorkCenters.
