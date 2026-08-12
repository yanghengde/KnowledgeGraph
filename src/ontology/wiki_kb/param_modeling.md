Chapter : Param Modeling
Introduction
The Param entity serves as a master data catalog of parameter definitions in Opcenter Execution.
It provides a unified registry of parameter names that are referenced by various sub-entities
throughout the system, including SpecParameter, BizRuleParameter, ProductParameter,
RecipeParameter, and ComputationParamSpec. By maintaining a centralized parameter catalog,
the system ensures consistent parameter naming and configuration across modules.

In This Chapter
- Param (Parameter Definition)

Param
A Param is a named catalog entry in the parameter master data directory. It defines parameter
names that can be referenced wherever a parameter is needed in the system, such as in
Specs, Business Rules, Products, Recipes, and Computations.

Relationship to other modules:

    SpecParameter --(REFERENCES_PARAM)--> Param
    ComputationParamSpec --(REFERENCES_PARAM)--> Param
    BizRuleParameter --(REFERENCES_PARAM)--> Param
    ProductParameter --(REFERENCES_PARAM)--> Param
    RecipeParameter --(REFERENCES_PARAM)--> Param

Field Definitions:
- Name (String, Required): Unique parameter definition name.
- Description (String): Description of this parameter. Defaults to name if not specified.
- Notes (String): Internal notes and comments.
- FilterTags (String): Filter tags, comma separated list.
- IsFrozen (Boolean, ReadOnly): Whether frozen from editing.
- InstanceLocked (Boolean): Whether locked by Change Management.
- ChangeHistory (Navigation): Change history tracking.
- IconId (Integer): Identifier for the associated icon.
