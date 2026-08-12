Chapter: Setup and Changeover Management
Introduction
When an equipment transitions from making Product A to Product B, it often requires a "Setup" (changing molds, adjusting rails, performing cleaning). The Setup module prevents machines from running invalid configurations.

Classes:
- SetupDef: The target setup state required for a product.
- SetupMatrix: Defines the allowed transitions and required time/actions to switch between Setup A and Setup B.
- SetupState: The real-time physical setup state of a machine.
