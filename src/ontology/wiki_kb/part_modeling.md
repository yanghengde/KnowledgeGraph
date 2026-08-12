# Chapter 12b: Part (Equipment Resource) Modeling / 设备与工位资源建模

## 1. Introduction / 导言
The **Part** entity models manufacturing equipment and workstation resources at a granular level. In electronic manufacturing and semiconductor backend processes, a Part represents a physical machine, slot, or workstation (such as SMT Mounter, Reflow Oven, AOI Station, or Wire Bonder) with defined capacities, ideal cycle limits, and operational parameters.

**Part** is a specialized semantic subtype of the generic **Resource** entity (`Part -[IS_RESOURCE]-> Resource`). While `Resource` provides general asset management attributes (hourly rates, maintenance schedules), `Part` provides detailed operational parameters directly mapping to Opcenter Execution (Camstar) `ResourceDef` (CDODefId: 293) and `ResourceFamily` (CDODefId: 1266) database fields.

## 2. Entity Definitions / 实体定义

### 2.1 Part (Equipment/Station Resource) / 设备与工位资源 (CdoId: 3980)
A **Part** represents a concrete manufacturing resource with over 60 operational properties covering production configuration, OML event reporting, downtime scheduling, vendor info, and preventive maintenance.

Field Definitions:
- Name (String, Required): Unique resource name.
- Description (String): Resource description.
- Notes (String): Internal notes.
- PartQty (Float, Required): Physical equipment quantity.
- Product (Navigation, Required): Current product being produced → Product.
- PartFamily (Navigation): Parent PartFamily for inherited configuration.
- Factory (Navigation): Factory this resource belongs to → Factory.
- ResourceGroup (Navigation): Resource group → ResourceGroup.
- BOM (Navigation): Consumed materials BOM.
- CurrentSetup (Navigation): Current physical setup/mold state.
- ClearanceLevel (Integer): Clearance level (1=None, 2=Container).
- Distributor (String): Distributor/agent.
- eS_IdealCPH (Integer): Ideal components per hour.
- eS_ConnectToOmlProducer (Boolean): Enable OML data collection.
- eS_EnableMoveInRetry (Boolean): Enable MoveIn auto-retry.
- eS_MoveInRetryAttempts (Integer): Max MoveIn retry count.
- eS_MoveInRetryInterval_Ms (Integer): Retry interval in milliseconds.
- eS_MoveInErrorAction (Integer): MoveIn error action code.
- eS_IgnoreMoveInNotRequired (Boolean): Skip non-required MoveIn errors.
- eS_MdmGUID (String): MDM global unique identifier.
- eS_DefectMessageAction (Integer): Defect signal response action.
- eS_NumberOfLanes (Integer): Number of equipment lanes/tracks.
- eS_PanelConfiguration (Integer): PCB panel configuration.
- eS_ResourceCategory (Navigation): Resource category → ResourceCategory.
- eS_ResourceComponents (SubentityList): Child resource component list.
- eS_ResourceIndex (Integer): Child index within parent resource.
- eS_UseTraceabilityEvents (Boolean): Enable traceability OML events.
- eS_UseProdStatusEvents (Boolean): Enable production status OML events.
- eS_UseQualityEvents (Boolean): Enable quality OML events.
- FactoryLevel (Integer): Physical factory hierarchy level (1=Cell, 2=Line, 3=Area).
- FactoryLevelIndex (Integer): Position index among sibling resources.
- FeederPlan (Navigation): Feeder layout plan → FeederPlan.
- FullyQualifiedName (String): Absolute path name in factory tree.
- IncludeInOEE (Boolean): Include this resource in OEE calculations.
- OEESettings (Navigation): OEE configuration.
- IsLineIdentifier (Boolean): Whether this is a line identifier.
- IsValidateQueue (Boolean): Whether to validate queue.
- SmartScanRule (Navigation): Barcode scan parsing rule.
- NickName (String): Short alias.
- IsRecipe (Navigation): Default process recipe document → Document.
- IsDefectMapping (Navigation): Defect mapping config → DefectMapping.
- ResourceStatusModel (Navigation): Resource state transition model.
- ResourceType (Navigation): Resource sub-type code.
- WorkingRangeMax (Float): Max operating parameter boundary.
- WorkingRangeMin (Float): Min operating parameter boundary.
- WorkingRangeOU (Navigation): Operating unit for working ranges.
- IsSingleProduct (Boolean): Restrict to single product at a time.
- IsSingleMfgOrder (Boolean): Restrict to single manufacturing order.
- IsUsePosition (Boolean): Enable physical slot/position control.
- IsVendor (Navigation): Equipment vendor → Vendor.
- IsVendorModel (String): Vendor model number.
- IsVendorSerialNumber (String): Vendor serial number.
- MaintenanceStatus (Navigation): Preventive maintenance status config.
- PMStatusConfig (Navigation): PM status configuration → PMStatusConfig.
- PrintQueue (Navigation): Print queue configuration.
- UOM (Navigation): Capacity/throughput unit of measure.
- eS_Params (SubentityList): Resource parameters → ResourceParam.
- isIdealCycleTimes (SubentityList): Part-level ideal cycle times → PartIdealCycle.
- isResDowntimeSchd (SubentityList): Resource downtime schedule → DowntimeSchedule.
- EmployeeList (SubentityList): Assigned operators → PartEmployee.
- PMStatus (Navigation): Preventive maintenance status record → PartPMStatus.

### 2.2 PartFamily (Equipment Resource Family) / 设备资源族 (CdoId: 1266)
Groups similar equipment for unified configuration. Part inherits family-level OEE, printer, status model, and training requirements.

Field Definitions:
- Name (String, Required): Unique family name.
- Description (String): Family description.
- Notes (String): Internal notes.
- IsFrozen (Boolean, ReadOnly): Whether frozen.
- IconId (Integer): Client icon ID.
- AssociatedPackages (Integer): Associated package count.
- ChangeHistory (Navigation): Change history log.
- ChangeCount (Integer): Version counter.
- ExportImportKey (String): Cross-environment migration key.
- SetupAccess (Navigation): Setup/changeover permission config.
- OEESettings (Navigation): Family-level OEE config.
- PrintQueue (Navigation): Shared barcode/label print queue.
- TrainingReqGroup (Navigation): Required operator training team → Team.
- Vendor (Navigation): Default equipment vendor → Vendor.
- VendorModel (String): Vendor model number.
- VendorSerialNumber (String): Vendor serial number.
- JobNotificationEmailGroup (Navigation): Default job notification email group.
- ResourceStatusModel (Navigation): State transition rule model.
- UIPreference (Navigation): Default terminal UI style config.
- CarrierPositionalMethod (String): Carrier position calculation method.
- EnableCarrierPositions (Boolean): Enable carrier grid slot resolution.
- CarrierXPositions (String): Carrier X-axis coordinate range.
- CarrierYPositions (String): Carrier Y-axis coordinate range.
- CarrierZPositions (String): Carrier Z-axis coordinate range.
- IsReuseTrackingContainer (Boolean): Allow WIP container name reuse.
- IsCarrierThruputRecordingMode (Boolean): Record carrier throughput history.
- isIdealResFamCycle (SubentityList): Family-level ideal cycle times → PartFamilyIdealCycle.
- isResFamDowntimeSchd (SubentityList): Family-level downtime schedule → DowntimeSchedule.

### 2.3 PartFamilyIdealCycle / 族理想节拍 (CdoId: 4841501)
Ideal cycle time per product/product family for a PartFamily.

Field Definitions:
- IdealCycleTime (Float, Required): Shortest time to process one unit.
- Product (Navigation): Applicable product (can specify revision) → Product.
- ProductFamily (Navigation): Applicable product family → ProductFamily.

### 2.4 PartIdealCycle / 设备理想节拍 (CdoId: 4841501)
Ideal cycle time per product/product family for a single Part. Same structure as PartFamilyIdealCycle.

Field Definitions:
- IdealCycleTime (Float, Required): Shortest time to process one unit.
- Product (Navigation): Applicable product → Product.
- ProductFamily (Navigation): Applicable product family → ProductFamily.

### 2.5 ResourceParam / 资源参数 (CdoId: 4792633)
Runtime parameter configuration for equipment, tracking PCB/panel serial numbers, container associations, and defect reasons.

Field Definitions:
- Param (Navigation, Required): Parameter definition → Param.
- eS_Column (Integer): PCB layout column number.
- eS_Container (Navigation): Associated container.
- eS_Count (Integer): Open defect count causing container failure.
- eS_DefectReason (Navigation): Defect reason code.
- eS_IsTemp (Boolean): Whether temporarily created.
- eS_PanelSerialNumber (String): Panel serial number.
- eS_PCBSerialNumber (String): PCB serial number.
- eS_PCBIndex (String): PCB index at specified row/column.
- eS_PCBNumber1 (Integer): PCB number within panel.
- eS_Row (Integer): PCB layout row number.

### 2.6 DowntimeSchedule / 停机排程 (CdoId: 4841593)
Planned downtime time range for a Part or PartFamily, used in OEE planned downtime deduction.

Field Definitions:
- StartTime (DateTime): Planned downtime start.
- EndTime (DateTime): Planned downtime end.

### 2.7 PartEmployee / 设备操作员工
Assigned operator on a Part workstation during a shift.

Field Definitions:
- Employee (Navigation): System employee → Employee.
- IsFrozen (Boolean): Whether this assignment is frozen.

### 2.8 PartPMStatus / 设备PM状态
Preventive maintenance compliance status record.

Field Definitions:
- Status (String): PM status (OK/Due/Overdue).
- LastPMDate (DateTime): Last PM execution date.
- NextPMDate (DateTime): Next PM due date.

## 3. Relationships / 关系列表

### 3.1 Local Relationships
- PartFamily -[HAS_IDEAL_FAM_CYCLE]-> PartFamilyIdealCycle (ONE_TO_MANY)
- PartFamily -[HAS_FAM_DOWNTIME]-> DowntimeSchedule (ONE_TO_MANY)
- Part -[BELONGS_TO_FAMILY]-> PartFamily (MANY_TO_ONE)
- Part -[HAS_IDEAL_CYCLE]-> PartIdealCycle (ONE_TO_MANY)
- Part -[HAS_DOWNTIME]-> DowntimeSchedule (ONE_TO_MANY)
- Part -[HAS_RESOURCE_PARAM]-> ResourceParam (ONE_TO_MANY)
- Part -[HAS_OPERATOR]-> PartEmployee (ONE_TO_MANY)
- Part -[HAS_PM_STATUS]-> PartPMStatus (ONE_TO_ONE)
- Part -[HAS_CHILD_RESOURCE]-> Part (ONE_TO_MANY)
- PartFamilyIdealCycle -[APPLIES_TO_PRODUCT]-> Product (MANY_TO_ONE)
- PartFamilyIdealCycle -[APPLIES_TO_PRODUCT_FAMILY]-> ProductFamily (MANY_TO_ONE)
- PartIdealCycle -[APPLIES_TO_PRODUCT]-> Product (MANY_TO_ONE)
- PartIdealCycle -[APPLIES_TO_PRODUCT_FAMILY]-> ProductFamily (MANY_TO_ONE)
- ResourceParam -[REFERENCES_PARAM]-> Param (MANY_TO_ONE)

### 3.2 Cross-Module Relationships
- Part -[IS_RESOURCE]-> Resource (MANY_TO_ONE)
- Part -[PRODUCES]-> Product (MANY_TO_ONE)
- Part -[USES_BOM]-> BOM (MANY_TO_ONE)
- Part -[REQUIRES_RECIPE]-> Document (MANY_TO_ONE)
- Part -[BELONGS_TO_FACTORY]-> Factory (MANY_TO_ONE)
- Part -[SUPPLIED_BY]-> Vendor (MANY_TO_ONE)
- PartFamily -[REQUIRES_TRAINING_TEAM]-> Team (MANY_TO_ONE)
- PartFamily -[SUPPLIED_BY]-> Vendor (MANY_TO_ONE)
- PartFamily -[HAS_STATUS_MODEL]-> ResourceStatusModel (MANY_TO_ONE)
- WorkCenter -[CONTAINS_PART]-> Part (ONE_TO_MANY)
