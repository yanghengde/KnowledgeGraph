Chapter: Rework & Hold Routing
Introduction
Exceptions happen on the shop floor. The Rework module defines the alternative routing logic when a container fails inspection or needs to be paused.

Classes:
- ReworkPath: Defines a sub-workflow specifically designed for repairing defects.
- ReworkReason: A tracked reason code for why a lot was sent to rework.
- ReworkStatus: Tracks whether a unit is actively in rework, scrapped, or successfully repaired.
