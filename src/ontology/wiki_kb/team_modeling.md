Chapter 14b: Team Modeling
Introduction
The Team entity defines work groups or crews that can be assigned to work centers, shifts,
or specific manufacturing tasks. Teams are used for resource grouping, training management,
and dispatch control.

In This Chapter
• Team (Work Group/Crew)

Team
A Team is a logical grouping of employees forming a work unit. Teams can be associated
with WorkCenters for training group requirements, with Skills for competency management,
and with dispatch rules for work assignment.

Relationship chain:

    Team ──(HAS_MEMBER)──▶ Employee
    WorkCenter ──(REQUIRES_TRAINING_GROUP)──▶ Team (via Skill training groups)
    Resource ──(ASSIGNED_TO)──▶ Team

Field Definitions:
- Name (String, Required): Unique team/group name.
- Description (String): Description of the team.
- Notes (String): Internal notes.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- FilterTags (String): Filter tags.
- IconId (Integer): UI icon identifier.
- AssociatedPackages (Integer): Count of associated packages.
- ChangeHistory (Navigation): Change history tracking.
