Chapter 12c: Business Rule Modeling
Introduction
Business Rules define automated validation and processing logic triggered during MES
transactions. Rules are bound to Spec transaction events via BizRuleTxnMap and can
include parameters for customization.

In This Chapter
• BusinessRule (Business Logic Rule)
• BizRuleParameter (Rule Parameter)

BusinessRule
A BusinessRule defines automated logic executed when a specific transaction event occurs.
Rules are associated with Specs through BizRuleTxnMap, which maps the rule to a particular
transaction type (e.g., MoveIn, MoveOut, Start).

Relationship chain:

    Spec ──(HAS_BIZ_RULE_MAP)──▶ BizRuleTxnMap ──(TRIGGERS_RULE)──▶ BusinessRule
    BusinessRule ──(HAS_PARAMETER)──▶ BizRuleParameter

Field Definitions:
- Name (String, Required): Unique business rule name.
- Description (String): Description of the rule's purpose and logic.
- Data (Navigation): Rule data/logic definition reference.
- Notes (String): Internal notes.
- IsFrozen (Boolean, ReadOnly): Whether frozen.
- InstanceLocked (Boolean): Whether locked by Change Management.
- FilterTags (String): Filter tags.
- IconId (Integer): UI icon identifier.
- AssociatedPackages (Integer): Count of associated packages.
- ChangeHistory (Navigation): Change history tracking.

BizRuleParameter
Defines an input parameter for the business rule.

Field Definitions:
- ParamName (String): Parameter name.
- ParamValue (String): Default value.
- ParamType (String): Data type.
- IsRequired (Boolean): Whether required.
