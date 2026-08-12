Chapter 5b: Organization Modeling
Introduction
The Organization entity provides the hierarchical grouping structure for factories, departments,
and business units in Opcenter Execution. Organizations carry cross-cutting configurations for
numbering rules, quality processing, notifications, approval routing, and UI preferences.

In This Chapter
- Organization (Organizational Unit)
- CategoryMap (Quality Object Category Mapping)
- ApprovalSheetMap (Approval Flow Mapping)
- NumberingRuleMap (Numbering Rule Map)
- NotificationEvent (Notification Event)
- EventClassificationSpecMap (Event Classification Spec Mapping)
- QualityProcessingMap (Quality Processing Configuration)
- LabelTxnMap (Quality Object Label Mapping)
- QualityReportConfig (Quality Report Configuration)
- UIPreferenceMap (UI Preference Mapping)

Organization
An Organization is a hierarchical node that can contain child organizations forming a tree
structure (Enterprise -> Site -> Factory -> Department). Each organization level can independently
configure quality processing rules, event classification mappings, numbering rules, notification
events, approval sheets, and UI preferences.

Relationship to other modules:

    Organization --(HAS_PARENT_ORG)--> Organization (parent)
    EmployeeRole --> Organization (context)
    Factory/Department --(belongs to)--> Organization

Field Definitions:
- Name (String, Required): Unique organization name.
- OrganizationNumber (String): Organization identifier number.
- Description (String): Description of this organization. Defaults to name if not specified.
- ParentOrganization (Navigation): Parent organization for hierarchy.
- PortalHomePage (Navigation): Portal home page definition.
- PortalMobileHomePage (Navigation): Mobile portal home page.
- PortalV8HomePage (Navigation): Portal V8 home page.
- SmtpTransport (Navigation): SMTP mail transport configuration.
- PrintQueue (Navigation): Default print queue.
- CollectESigForAllQualityTxns (Boolean): Collect e-signatures for all quality transactions.
- UserRequiredForEsig (Boolean): Whether user verification is required for e-signature.
- Notes (String): Internal notes.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- FilterTags (String): Filter tags, comma separated list.
- ChangeHistory (Navigation): Change history tracking.
- AffectedContainersTxns (Array): Transaction types that can add affected containers to events.
- GeDisallowedTxns (Array): Disallowed general transaction types.
- PeDisallowedTxns (Array): Disallowed production transaction types.
- QualityESigTxns (Array): Electronic signature transaction type mappings.
- CategoryMap (SubentityList): Category-to-organization mappings.
- NumberingRuleMap (SubentityList): Quality object numbering rule assignments.
- NotificationEvents (SubentityList): Notification event configurations.
- EventClassificationSpecMaps (SubentityList): Event classification spec bindings.
- QualityProcessingMap (SubentityList): Quality processing configurations.
- QualityReportConfigs (SubentityList): Quality report configurations.
- UIPreferenceMap (SubentityList): UI preference-to-organization mappings.

CategoryMap
Maps a quality object Category (Event/CAR) to a Triage Spec, Owner, and Role within the
organization context. Contains ApprovalSheetMap sub-entities for resolution-action-based
approval routing.

Field Definitions:
- Category (Integer, Required): Quality object category. 1 = Event, 2 = CAR.
- Owner (Navigation): Employee owner responsible for this category.
- Role (Navigation): Role responsible for this category.
- TriageSpec (Navigation): Triage specification for processing.
- ApprovalSheetMap (SubentityList): Approval sheet template mappings by resolution action.

ApprovalSheetMap
Maps a ResolutionAction to an ApprovalSheetTemplate within a CategoryMap. Defines which
approval template is used when a specific resolution action is taken.

Field Definitions:
- ResolutionAction (Integer, Required): Resolution action. 1 = Close.
- ApprovalRequired (Boolean): Whether approval is required.
- ApprovalSheetTemplate (Navigation): Approval sheet template definition.

NumberingRuleMap
Maps a Quality Category to a numbering rule within the organization context.

Field Definitions:
- Category (Integer, Required): The quality object category for auto number generation.
- NumberingRule (Navigation, Required): The numbering rule to apply.

NotificationEvent
Defines a notification event rule for the organization, specifying what triggers a notification
and who receives it, along with the email template and distribution list.

Field Definitions:
- NotificationType (Integer, Required): The type of actions that will cause an email to be sent.
- EMailMessage (Navigation, Required): Email message template.
- EMailDistribution (Navigation): Email distribution list for recipients.
- AssigneeOnly (Boolean): Whether email only goes to the assignee.
- AppendConciergeMsg (Boolean): Whether to append the message generated by the concierge.

EventClassificationSpecMap
Maps specific high-level quality event Classifications, Subclassifications, and FailureModeGroups
to responsible Checklist Templates, Owners, and Roles within the Organization context.

Field Definitions:
- Classification (Navigation, Required): The high-level quality event classification category.
- Subclassification (Navigation, Required): The fine-grained quality event subclassification category.
- FailureModeGroup (Navigation, Required): The failure mode group for this event classification.
- ChecklistTemplate (Navigation): The checklist template to use for this event classification.
- Owner (Navigation): Employee owner responsible for this event classification.
- Role (Navigation): Role responsible for this event classification.
- PeDefault (Boolean): Whether this is the default configuration for this event classification.

QualityProcessingMap
Configures quality processing rules per Category/Classification/SubClassification combination
within the Organization, including label printing strategies.

Field Definitions:
- Category (Integer, Required): Quality object category. 1 = Event, 2 = CAR.
- Classification (Navigation): Event classification (optional refinement).
- SubClassification (Navigation): Event subclassification (optional refinement).
- LabelTxnMap (SubentityList): Quality object label mapping entries.

LabelTxnMap
Defines label printing configuration for a specific transaction type within a QualityProcessingMap.

Field Definitions:
- LabelCount (String, Required): Number of labels to print.
- PrinterLabelDefinition (Navigation, Required): Printer label definition template.
- TxnType (Integer): Transaction type ID (CDO Definition Id) this mapping applies to.

QualityReportConfig
Specifies which report page is displayed for each Action/Category/Classification/SubClassification
combination within the Organization.

Field Definitions:
- Category (Integer, Required): Quality object category. 1 = Event, 2 = CAR.
- Classification (Navigation, Required): Event classification.
- SubClassification (Navigation, Required): Event subclassification.
- ReportAction (String, Required): Report action type.
- ReportPage (Navigation, Required): Report page definition.

UIPreferenceMap
Identifies the relationship of an Organization to a UI Preference configuration, which stores
a user-configured set of fields for a container.

Field Definitions:
- RecordType (Integer, Required): Record type ID for this UI preference mapping.
- uiPreference (Navigation, Required): UI Preference configuration definition.
