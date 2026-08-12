Chapter 11b: Carrier Modeling
Introduction
Carriers are the physical containers/trays/fixtures used to hold and transport products
through manufacturing lines. Carrier Families group similar carriers, and Carrier Groups
organize carriers into logical work units.

In This Chapter
• Carrier (Physical Container/Tray)
• CarrierFamily (Carrier Type Group)
• CarrierGroup (Carrier Logical Group)

Carrier
A physical carrier (tray, fixture, panel) that holds products during manufacturing. Carriers
can have positional slots, panel configurations, throughput factors, and maintenance schedules.

CarrierFamily
Groups similar carriers sharing configuration: ideal cycle times, OEE settings, positional
method (Grid/Lane with X/Y/Z dimensions), vendor info, and printing setup.

CarrierGroup
Logical grouping of carriers for work unit organization. Groups can be nested and support
SMT resource designation and object-type defaults.

Relationship chain:

    Carrier ──(BELONGS_TO_CARRIER_FAMILY)──▶ CarrierFamily
            ──(ASSOCIATED_PRODUCT)──▶ Product
            ──(LOCATED_AT)──▶ Factory
    CarrierGroup ──(CONTAINS_CARRIER)──▶ Carrier
                 ──(HAS_SUB_GROUP)──▶ CarrierGroup
