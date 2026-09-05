# Ontology vs Semiconductor CSV Validation Report

- Tables source: `D:\Deepseek\camstar\Knowledge\docs\Database_Tables.csv`
- Fields source: `D:\Deepseek\camstar\Knowledge\docs\Database_Fields.csv`
- Ontology directory: `D:\Deepseek\camstar\Knowledge\src\ontology\wiki_kb`

## Summary

| Metric | Count |
|---|---|
| Physical Tables | 1605 |
| Physical Fields | 22676 |
| Ontology Files | 192 |
| Ontology Classes | 593 |
| Ontology Relationships | 2386 |
| Duplicate Relationships | 709 |
| Duplicate Properties | 0 |
| Exact Class Matches | 593 |
| Duplicate Classes | 318 |
| Ontology Only Classes | 0 |
| Physical Only Classes | 1012 |
| Missing Properties | 0 |
| Ontology Only Properties | 475 |
| Type Mismatches | 0 |
| Missing Relationships | 0 |
| Invalid Relationships | 0 |
| Parse Errors | 0 |

## Duplicate Class Definitions

| Class | Files |
|---|---|
| AQLLevel | aql_levels_ontology.json<br>csv_business_import_ontology.json |
| A_EmployeeGroup | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| A_Job | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| A_JobCauseCode | csv_business_import_ontology.json<br>semiconductor_user_job_spc_configuration_ontology.json |
| A_JobModel | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| A_JobRepairCode | csv_business_import_ontology.json<br>semiconductor_user_job_spc_configuration_ontology.json |
| A_JobStage | csv_business_import_ontology.json<br>semiconductor_user_job_spc_configuration_ontology.json |
| A_JobSymptomCode | csv_business_import_ontology.json<br>semiconductor_user_job_spc_configuration_ontology.json |
| A_PhysicalLocation | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| A_PhysicalLocationPosition | csv_business_import_ontology.json<br>semiconductor_physical_resource_replacements_ontology.json |
| A_PhysicalPosition | csv_business_import_ontology.json<br>semiconductor_physical_resource_replacements_ontology.json |
| A_ResourceBOM | csv_business_import_ontology.json<br>semiconductor_physical_resource_replacements_ontology.json |
| A_ResourceBOMBase | csv_business_import_ontology.json<br>semiconductor_physical_resource_replacements_ontology.json |
| A_SPCChart | csv_business_import_ontology.json<br>semiconductor_user_job_spc_configuration_ontology.json |
| A_SPCConnection | csv_business_import_ontology.json<br>semiconductor_spc_yield_ontology.json |
| A_SPCRules | csv_business_import_ontology.json<br>semiconductor_spc_yield_ontology.json |
| A_ToolPlan | csv_business_import_ontology.json<br>tool_ontology.json |
| A_YieldLimits | csv_business_import_ontology.json<br>semiconductor_spc_yield_ontology.json |
| ActionCategory | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| ActionDef | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| ActionDefActionRules | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| ActionDefinition | csv_business_import_ontology.json<br>workflow_ontology.json |
| ActionRule | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| Activity | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| ActivityPlan | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| AlarmDefinition | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| ApprovalDecision | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| ApprovalDecisionList | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| ApprovalSheet | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| ApprovalSheetTemplate | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| AttachedDocs | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| BOM | bom_ontology.json<br>csv_business_import_ontology.json |
| BOMBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| BillOfProcess | billofprocess_ontology.json<br>csv_business_import_ontology.json |
| BillOfProcessBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| BillOfProcessOverride | billofprocess_ontology.json<br>csv_business_import_ontology.json |
| BillType | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| BizRuleHandlerParameter | businessrule_ontology.json<br>csv_business_import_ontology.json |
| BizRuleParameter | businessrule_ontology.json<br>csv_business_import_ontology.json |
| BonusReason | bonus_reasons_ontology.json<br>csv_business_import_ontology.json |
| BonusReasonGroup | bonus_reasons_ontology.json<br>csv_business_import_ontology.json |
| BusinessProcessSpec | business_process_ontology.json<br>csv_business_import_ontology.json |
| BusinessProcessSpecBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| BusinessProcessWorkflow | business_process_ontology.json<br>csv_business_import_ontology.json |
| BusinessProcessWorkflowBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| BusinessRule | businessrule_ontology.json<br>csv_business_import_ontology.json |
| BusinessRuleData | businessrule_ontology.json<br>csv_business_import_ontology.json |
| BusinessRuleHandler | businessrule_ontology.json<br>csv_business_import_ontology.json |
| BusinessRuleHandlerData | businessrule_ontology.json<br>csv_business_import_ontology.json |
| BuyReason | buy_reasons_ontology.json<br>csv_business_import_ontology.json |
| BuyReasonGroup | buy_reasons_ontology.json<br>csv_business_import_ontology.json |
| CAPA | csv_business_import_ontology.json<br>quality_ontology.json |
| CAPACustomData | csv_business_import_ontology.json<br>quality_ontology.json |
| CARSeverity | csv_business_import_ontology.json<br>quality_ontology.json |
| CalendarShift | csv_business_import_ontology.json<br>mfgcalendar_ontology.json |
| ChangeMgtApplication | change_management_ontology.json<br>csv_business_import_ontology.json |
| ChangePackage | change_management_ontology.json<br>csv_business_import_ontology.json |
| ChangePackagePriority | change_management_ontology.json<br>csv_business_import_ontology.json |
| ChangePackageReason | change_management_ontology.json<br>csv_business_import_ontology.json |
| ChangeStatusReason | container_ontology.json<br>csv_business_import_ontology.json |
| Checklist | checklist_ontology.json<br>csv_business_import_ontology.json |
| ChecklistEntry | checklist_ontology.json<br>csv_business_import_ontology.json |
| ChecklistTemplate | checklist_ontology.json<br>csv_business_import_ontology.json |
| ChecklistTemplateBase | checklist_ontology.json<br>csv_business_import_ontology.json |
| Classification | csv_business_import_ontology.json<br>quality_ontology.json |
| CollaboratorEntry | change_management_ontology.json<br>csv_business_import_ontology.json |
| CollaboratorTemplate | change_management_ontology.json<br>csv_business_import_ontology.json |
| CollectionGate | csv_business_import_ontology.json<br>workflow_ontology.json |
| CombineHistory | csv_business_import_ontology.json<br>sql_core_transaction_history_ontology.json |
| CommentType | csv_business_import_ontology.json<br>quality_ontology.json |
| CompDefectReasonGroup | component_defect_ontology.json<br>csv_business_import_ontology.json |
| ComponentDefectReason | csv_business_import_ontology.json<br>semiconductor_legacy_name_replacements_ontology.json |
| Computation | computation_ontology.json<br>csv_business_import_ontology.json |
| ComputationParamSpec | computation_ontology.json<br>csv_business_import_ontology.json |
| ContDefectReasonGroup | container_ontology.json<br>csv_business_import_ontology.json |
| Container | container_ontology.json<br>csv_business_import_ontology.json |
| ContainerAutoHoldReq | container_ontology.json<br>csv_business_import_ontology.json |
| ContainerDefectReason | container_ontology.json<br>csv_business_import_ontology.json |
| ContainerGroup | container_ontology.json<br>csv_business_import_ontology.json |
| ContainerLevel | csv_business_import_ontology.json<br>operation_ontology.json |
| ContainerStatusChangeHistory | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| CurrentStatus | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| Customer | csv_business_import_ontology.json<br>customer_ontology.json |
| CustomerContact | csv_business_import_ontology.json<br>customer_ontology.json |
| CycleTimeGate | csv_business_import_ontology.json<br>workflow_ontology.json |
| DataCollectionDef | csv_business_import_ontology.json<br>datacollection_ontology.json |
| DataCollectionDefBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| DataPoint | csv_business_import_ontology.json<br>datacollection_ontology.json |
| DataPointCollection | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| DataPointCollectionGroup | csv_business_import_ontology.json<br>datacollection_ontology.json |
| DataTransport | csv_business_import_ontology.json<br>data_transport_ontology.json |
| DelegateTaskHistory | csv_business_import_ontology.json<br>delegation_ontology.json |
| DelegationReasonCode | csv_business_import_ontology.json<br>delegation_ontology.json |
| DelegationTask | csv_business_import_ontology.json<br>delegation_ontology.json |
| DispatchDetail | csv_business_import_ontology.json<br>dispatch_ontology.json |
| DispatchRule | csv_business_import_ontology.json<br>dispatch_ontology.json |
| Disposition | csv_business_import_ontology.json<br>disposition_ontology.json |
| DocAttachments | csv_business_import_ontology.json<br>quality_ontology.json |
| Document | csv_business_import_ontology.json<br>document_ontology.json |
| DocumentBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| DocumentEntry | csv_business_import_ontology.json<br>document_ontology.json |
| DocumentSet | csv_business_import_ontology.json<br>document_ontology.json |
| DocumentViewer | csv_business_import_ontology.json<br>document_ontology.json |
| DynamicNumberingRule | csv_business_import_ontology.json<br>numbering_ontology.json |
| EProcedureDetail | csv_business_import_ontology.json<br>electronic_procedure_ontology.json |
| ERPBOM | csv_business_import_ontology.json<br>erpbom_ontology.json |
| ERPBOMBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| ERPRoute | csv_business_import_ontology.json<br>erp_route_ontology.json |
| ERPRouteBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| ElectronicProcedure | csv_business_import_ontology.json<br>electronic_procedure_ontology.json |
| ElectronicProcedureBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| Employee | csv_business_import_ontology.json<br>employee_ontology.json |
| EmployeeLoginInfo | csv_business_import_ontology.json<br>employee_ontology.json |
| EmployeeRole | csv_business_import_ontology.json<br>employee_ontology.json |
| Enterprise | csv_business_import_ontology.json<br>enterprise_ontology.json |
| Event | csv_business_import_ontology.json<br>quality_ontology.json |
| EventData | csv_business_import_ontology.json<br>quality_ontology.json |
| EventDisposition | csv_business_import_ontology.json<br>disposition_ontology.json |
| EventFailure | csv_business_import_ontology.json<br>failure_ontology.json |
| EventFailureAction | csv_business_import_ontology.json<br>failure_ontology.json |
| EventLog | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| ExecuteMfgOrderTaskHistory | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| ExecuteSamplingLotHistory | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| Factory | csv_business_import_ontology.json<br>factory_ontology.json |
| FailureActionType | csv_business_import_ontology.json<br>failure_ontology.json |
| FailureActionTypeGroup | csv_business_import_ontology.json<br>failure_ontology.json |
| FailureMode | csv_business_import_ontology.json<br>failure_ontology.json |
| FailureModeGroup | csv_business_import_ontology.json<br>failure_ontology.json |
| FailureSeverity | csv_business_import_ontology.json<br>failure_ontology.json |
| HistoryMainline | csv_business_import_ontology.json<br>history_ontology.json |
| HoldReason | csv_business_import_ontology.json<br>quality_ontology.json |
| HoldReleaseHistory | csv_business_import_ontology.json<br>sql_core_transaction_history_ontology.json |
| HoldStatus | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| InspectionLevel | csv_business_import_ontology.json<br>sampling_ontology.json |
| IssueActualsHistory | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| IssueCondition | csv_business_import_ontology.json<br>issue_ontology.json |
| IssueDifferenceReason | csv_business_import_ontology.json<br>issue_ontology.json |
| IssueReason | csv_business_import_ontology.json<br>issue_ontology.json |
| KPIEntry | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| KPIMatrix | csv_business_import_ontology.json<br>semiconductor_security_kpi_configuration_ontology.json |
| KPITimeframe | csv_business_import_ontology.json<br>semiconductor_security_kpi_configuration_ontology.json |
| KPIType | csv_business_import_ontology.json<br>semiconductor_security_kpi_configuration_ontology.json |
| LocalReworkReason | csv_business_import_ontology.json<br>local_rework_ontology.json |
| LocalReworkReasonGroup | csv_business_import_ontology.json<br>local_rework_ontology.json |
| Location | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| LossReason | csv_business_import_ontology.json<br>loss_reason_ontology.json |
| LossReasonGroup | csv_business_import_ontology.json<br>loss_reason_ontology.json |
| MaintenanceClass | csv_business_import_ontology.json<br>maintenance_ontology.json |
| MaintenanceReason | csv_business_import_ontology.json<br>maintenance_ontology.json |
| MaintenanceReq | csv_business_import_ontology.json<br>maintenance_ontology.json |
| MaintenanceReqBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| MasterDataCatalog | csv_business_import_ontology.json<br>master_data_catalog_ontology.json |
| MasterDataCatalogDtl | csv_business_import_ontology.json<br>master_data_catalog_ontology.json |
| MasterRecipe | csv_business_import_ontology.json<br>master_recipe_ontology.json |
| MasterRecipeBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| MasterRecipeDetail | csv_business_import_ontology.json<br>master_recipe_ontology.json |
| MfgCalendar | csv_business_import_ontology.json<br>mfgcalendar_ontology.json |
| MfgLot | container_ontology.json<br>csv_business_import_ontology.json |
| MfgOrder | csv_business_import_ontology.json<br>mfgorder_ontology.json |
| MfgOrderProcedure | csv_business_import_ontology.json<br>mfg_order_procedure_ontology.json |
| MfgOrderProcedureBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| MfgOrderProcedureDetail | csv_business_import_ontology.json<br>mfg_order_procedure_ontology.json |
| MfgOrderTaskList | csv_business_import_ontology.json<br>mfg_order_task_list_ontology.json |
| MfgOrderTaskListBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| MfgOrderTaskStatus | csv_business_import_ontology.json<br>mfg_order_task_status_ontology.json |
| MoveHistory | csv_business_import_ontology.json<br>sql_core_transaction_history_ontology.json |
| MoveInHistory | csv_business_import_ontology.json<br>sql_core_transaction_history_ontology.json |
| NCRCauseCode | csv_business_import_ontology.json<br>ncr_ontology.json |
| NCRCauseCodeGroup | csv_business_import_ontology.json<br>ncr_ontology.json |
| NCRDefectData | csv_business_import_ontology.json<br>quality_ontology.json |
| NCRFailureCode | csv_business_import_ontology.json<br>ncr_ontology.json |
| NCRFailureCodeGroup | csv_business_import_ontology.json<br>ncr_ontology.json |
| NCRFailureType | csv_business_import_ontology.json<br>failure_ontology.json |
| NCRResolutionCode | csv_business_import_ontology.json<br>ncr_ontology.json |
| NCRResolutionCodeGroup | csv_business_import_ontology.json<br>ncr_ontology.json |
| NamedObjectGroup | csv_business_import_ontology.json<br>semiconductor_security_kpi_configuration_ontology.json |
| NonconformanceReport | csv_business_import_ontology.json<br>quality_ontology.json |
| NonconformanceReportNCRFailure | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| NumberingRule | csv_business_import_ontology.json<br>numbering_ontology.json |
| Occupation | csv_business_import_ontology.json<br>occupation_ontology.json |
| Operation | csv_business_import_ontology.json<br>operation_ontology.json |
| OrderStatus | csv_business_import_ontology.json<br>mfgorder_ontology.json |
| OrderType | csv_business_import_ontology.json<br>mfgorder_ontology.json |
| Organization | csv_business_import_ontology.json<br>organization_ontology.json |
| Owner | csv_business_import_ontology.json<br>owner_ontology.json |
| PackageCreationTemplate | csv_business_import_ontology.json<br>package_creation_template_ontology.json |
| PackageType | csv_business_import_ontology.json<br>package_type_ontology.json |
| Path | csv_business_import_ontology.json<br>workflow_ontology.json |
| PathSelector | csv_business_import_ontology.json<br>workflow_ontology.json |
| PauseReason | csv_business_import_ontology.json<br>pause_reason_ontology.json |
| PauseReasonGroup | csv_business_import_ontology.json<br>pause_reason_group_ontology.json |
| PauseTaskHistory | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| Phase | csv_business_import_ontology.json<br>semiconductor_action_approval_esign_ontology.json |
| PhaseTemplate | csv_business_import_ontology.json<br>phase_template_ontology.json |
| PlanTemplate | csv_business_import_ontology.json<br>plan_template_ontology.json |
| PrintQueue | csv_business_import_ontology.json<br>print_queue_ontology.json |
| PrinterLabelDefinition | csv_business_import_ontology.json<br>printer_label_definition_ontology.json |
| PrinterLabelDefinitionBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| PriorityCode | csv_business_import_ontology.json<br>priority_code_ontology.json |
| PriorityLevel | csv_business_import_ontology.json<br>priority_level_ontology.json |
| ProcessModel | csv_business_import_ontology.json<br>quality_ontology.json |
| ProcessModelTemplate | csv_business_import_ontology.json<br>process_model_template_ontology.json |
| ProcessModelTemplateBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| ProcessTimer | csv_business_import_ontology.json<br>process_timer_ontology.json |
| ProcessTimerBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| ProcessTimerType | csv_business_import_ontology.json<br>process_timer_type_ontology.json |
| ProcessingGate | csv_business_import_ontology.json<br>workflow_ontology.json |
| Product | csv_business_import_ontology.json<br>product_ontology.json |
| ProductBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| ProductFamily | csv_business_import_ontology.json<br>product_family_ontology.json |
| ProductType | csv_business_import_ontology.json<br>product_type_ontology.json |
| QtyAdjustGroup | csv_business_import_ontology.json<br>semiconductor_legacy_name_replacements_ontology.json |
| QtyAdjustReason | csv_business_import_ontology.json<br>qty_adjust_reason_ontology.json |
| QtyHistory | csv_business_import_ontology.json<br>sql_core_transaction_history_ontology.json |
| QualityReportConfig | csv_business_import_ontology.json<br>organization_ontology.json |
| QualityResolutionCode | csv_business_import_ontology.json<br>quality_resolution_code_ontology.json |
| RecipeList | csv_business_import_ontology.json<br>recipe_list_ontology.json |
| RecipeListBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| RegulatoryAgency | csv_business_import_ontology.json<br>regulatory_agency_ontology.json |
| RegulatoryReportType | csv_business_import_ontology.json<br>regulatory_report_type_ontology.json |
| ReleaseReason | csv_business_import_ontology.json<br>release_reason_ontology.json |
| RemovalReason | csv_business_import_ontology.json<br>removal_reason_ontology.json |
| RemoveDifferenceReason | csv_business_import_ontology.json<br>remove_difference_reason_ontology.json |
| ReplaceReason | csv_business_import_ontology.json<br>replace_reason_ontology.json |
| ReprintLabelHistory | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| ReprintReason | csv_business_import_ontology.json<br>semiconductor_security_kpi_configuration_ontology.json |
| ResStatusReasonGroup | csv_business_import_ontology.json<br>res_status_reason_group_ontology.json |
| ResourceDef | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| ResourceFamily | csv_business_import_ontology.json<br>resource_family_ontology.json |
| ResourceGroup | csv_business_import_ontology.json<br>resource_group_ontology.json |
| ResourceLayout | csv_business_import_ontology.json<br>resource_layout_ontology.json |
| ResourceLogs | csv_business_import_ontology.json<br>resource_ontology.json |
| ResourceStatusCode | csv_business_import_ontology.json<br>resource_status_code_ontology.json |
| ResourceStatusCodeGroup | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| ResourceStatusCodeGroupDef | csv_business_import_ontology.json<br>semiconductor_user_job_spc_configuration_ontology.json |
| ResourceStatusHistory | csv_business_import_ontology.json<br>sql_core_transaction_history_ontology.json |
| ResourceStatusModel | csv_business_import_ontology.json<br>resource_status_model_ontology.json |
| ResourceStatusReason | csv_business_import_ontology.json<br>resource_status_reason_ontology.json |
| ResourceThruputHistory | csv_business_import_ontology.json<br>sql_core_transaction_history_ontology.json |
| ResourceType | csv_business_import_ontology.json<br>resource_type_ontology.json |
| ResponseSet | csv_business_import_ontology.json<br>response_set_ontology.json |
| ReturnedEquipmentAction | csv_business_import_ontology.json<br>returned_equipment_action_ontology.json |
| RevisionedObjectGroup | csv_business_import_ontology.json<br>semiconductor_security_kpi_configuration_ontology.json |
| ReworkReason | csv_business_import_ontology.json<br>rework_reason_ontology.json |
| ReworkReasonGroup | csv_business_import_ontology.json<br>rework_reason_group_ontology.json |
| ReworkStatus | csv_business_import_ontology.json<br>rework_ontology.json |
| RiskAssessment | csv_business_import_ontology.json<br>quality_ontology.json |
| RoleDef | csv_business_import_ontology.json<br>role_ontology.json |
| RollupReason | csv_business_import_ontology.json<br>rollup_reason_ontology.json |
| RollupReasonGroup | csv_business_import_ontology.json<br>rollup_reason_group_ontology.json |
| RouteStep | csv_business_import_ontology.json<br>erp_route_ontology.json |
| SPCChartDef | csv_business_import_ontology.json<br>spc_ontology.json |
| SPCChartVisualParams | csv_business_import_ontology.json<br>spc_chart_visual_params_ontology.json |
| SPCRuleViolations | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| SPCViolation | csv_business_import_ontology.json<br>spc_ontology.json |
| SalesOrder | csv_business_import_ontology.json<br>salesorder_ontology.json |
| SampleDataPoint | csv_business_import_ontology.json<br>sampling_ontology.json |
| SampleDataPointBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| SampleTest | csv_business_import_ontology.json<br>sampling_ontology.json |
| SampleTestBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| SamplingPlan | csv_business_import_ontology.json<br>sampling_ontology.json |
| SamplingPlanBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| ScheduledBusinessRule | csv_business_import_ontology.json<br>scheduled_business_rule_ontology.json |
| SchedulingRoute | csv_business_import_ontology.json<br>scheduling_route_ontology.json |
| SchedulingRouteBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| ScrapReason | csv_business_import_ontology.json<br>scrap_reason_ontology.json |
| SellReason | csv_business_import_ontology.json<br>sell_reason_ontology.json |
| SellReasonGroup | csv_business_import_ontology.json<br>sell_reason_group_ontology.json |
| SessionValues | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| Setup | csv_business_import_ontology.json<br>setup_ontology.json |
| SetupBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |
| Shift | csv_business_import_ontology.json<br>shift_ontology.json |
| ShipmentDestination | csv_business_import_ontology.json<br>shipment_destination_ontology.json |
| ShipmentDestinationGrp | csv_business_import_ontology.json<br>shipment_destination_group_ontology.json |
| ShippingReason | csv_business_import_ontology.json<br>shipping_reason_ontology.json |
| ShippingReasonGroup | csv_business_import_ontology.json<br>shipping_reason_group_ontology.json |
| ShopFloorSettings | cross_module_ontology.json<br>csv_business_import_ontology.json |
| Site | csv_business_import_ontology.json<br>factory_ontology.json |
| SmartScanRule | cross_module_ontology.json<br>csv_business_import_ontology.json |
| Spec | csv_business_import_ontology.json<br>spec_ontology.json |
| SpecBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| SpecSchedulingDetail | csv_business_import_ontology.json<br>spec_ontology.json |
| SplitHistory | csv_business_import_ontology.json<br>sql_core_transaction_history_ontology.json |
| StartHistoryDetailIssueConditi | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| StartReason | csv_business_import_ontology.json<br>start_reasons_ontology.json |
| StepSchedulingDetail | cross_module_ontology.json<br>csv_business_import_ontology.json |
| SubClassification | csv_business_import_ontology.json<br>quality_ontology.json |
| SubstitutionReason | csv_business_import_ontology.json<br>substitution_reason_ontology.json |
| SwitchingRule | csv_business_import_ontology.json<br>switching_rules_ontology.json |
| SwitchingRuleBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| TargetSystem | csv_business_import_ontology.json<br>semiconductor_shared_support_ontology.json |
| TaskItem | csv_business_import_ontology.json<br>electronic_procedure_ontology.json |
| TaskList | csv_business_import_ontology.json<br>electronic_procedure_ontology.json |
| TaskListBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| Team | csv_business_import_ontology.json<br>team_ontology.json |
| Terminal | csv_business_import_ontology.json<br>terminal_ontology.json |
| ThruputHistory | csv_business_import_ontology.json<br>sql_core_transaction_history_ontology.json |
| TrainingPlan | csv_business_import_ontology.json<br>training_plan_ontology.json |
| TrainingPlanDetail | csv_business_import_ontology.json<br>training_plan_ontology.json |
| TrainingRecord | csv_business_import_ontology.json<br>training_plan_ontology.json |
| TrainingRecordStatus | csv_business_import_ontology.json<br>training_plan_ontology.json |
| TrainingRequirement | csv_business_import_ontology.json<br>training_plan_ontology.json |
| TrainingRequirementBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| TrainingRequirementGroup | csv_business_import_ontology.json<br>training_plan_ontology.json |
| TriageSpec | csv_business_import_ontology.json<br>triage_spec_ontology.json |
| TriageSpecDetail | csv_business_import_ontology.json<br>triage_spec_ontology.json |
| UOM | csv_business_import_ontology.json<br>uoms_ontology.json |
| UserCodeGroup | csv_business_import_ontology.json<br>semiconductor_security_kpi_configuration_ontology.json |
| UserConstant | csv_business_import_ontology.json<br>semiconductor_user_job_spc_configuration_ontology.json |
| Vendor | csv_business_import_ontology.json<br>supplier_ontology.json |
| VendorItem | csv_business_import_ontology.json<br>product_ontology.json |
| WhereUsedConfig | csv_business_import_ontology.json<br>semiconductor_user_job_spc_configuration_ontology.json |
| WorkCenter | csv_business_import_ontology.json<br>workcenter_ontology.json |
| Workflow | csv_business_import_ontology.json<br>workflow_ontology.json |
| WorkflowBase | cross_module_ontology.json<br>csv_business_import_ontology.json |
| WorkflowStep | csv_business_import_ontology.json<br>workflow_ontology.json |
| isImage | csv_business_import_ontology.json<br>physical_bridge_ontology.json |
| isImageBase | csv_business_import_ontology.json<br>semiconductor_revision_bases_ontology.json |

## Duplicate Property Definitions

_None._

## Ontology Classes Without a Physical Semiconductor Table

_None._

## Invalid Relationship Endpoints

_None._

## Duplicate Relationship Definitions

| From | Relation | To | Count |
|---|---|---|---|
| A_Job | HAS_CAUSE_CODE | A_JobCauseCode | 2 |
| A_Job | HAS_JOB_MODEL | A_JobModel | 2 |
| A_Job | HAS_REPAIR_CODE | A_JobRepairCode | 2 |
| A_Job | HAS_STAGE | A_JobStage | 2 |
| A_Job | HAS_SYMPTOM_CODE | A_JobSymptomCode | 2 |
| A_Job | HAS_CANCEL_USER | Employee | 2 |
| A_Job | HAS_COMPLETE_USER | Employee | 2 |
| A_Job | HAS_CREATE_USER | Employee | 2 |
| A_Job | HAS_RESOURCE | ResourceDef | 2 |
| A_JobModel | HAS_DOCUMENT_SET | DocumentSet | 2 |
| A_PhysicalLocationPosition | HAS_PHYSICAL_LOCATION | A_PhysicalLocation | 2 |
| A_PhysicalLocationPosition | HAS_POSITION | A_PhysicalPosition | 2 |
| A_ResourceBOM | HAS_RESOURCE_BOM_BASE | A_ResourceBOMBase | 2 |
| A_ResourceBOM | HAS_BILL_TYPE | BillType | 2 |
| A_ResourceBOMBase | HAS_REV_OF_RCD | A_ResourceBOM | 2 |
| A_ToolPlan | HAS_DOCUMENT_SET | DocumentSet | 2 |
| A_YieldLimits | HAS_OWNER | Owner | 2 |
| A_YieldLimits | HAS_PRODUCT | Product | 2 |
| A_YieldLimits | HAS_SPEC | Spec | 2 |
| ActionDefActionRules | HAS_ACTION | ActionDef | 2 |
| ActionDefActionRules | HAS_ACTION_RULES | ActionRule | 2 |
| Activity | HAS_CHECKLIST | Checklist | 2 |
| Activity | HAS_DATA_POINT_COLLECTION | DataPointCollection | 2 |
| Activity | HAS_DISPOSITION | Disposition | 2 |
| Activity | HAS_ATTACHMENTS | DocAttachments | 2 |
| Activity | HAS_COMPLETION_ATTACHMENTS | DocAttachments | 2 |
| Activity | HAS_DOCUMENT_SET | DocumentSet | 2 |
| Activity | HAS_ASSIGNEE | Employee | 2 |
| Activity | HAS_LAST_COMPLETED_BY | Employee | 2 |
| Activity | HAS_ASSIGNEE_ROLE | RoleDef | 2 |
| ActivityPlan | HAS_LAST_APPROVAL_ROUTED | ApprovalSheet | 2 |
| ActivityPlan | HAS_CHECKLIST | Checklist | 2 |
| ActivityPlan | HAS_DATA_POINT_COLLECTION | DataPointCollection | 2 |
| ActivityPlan | HAS_ATTACHMENTS | DocAttachments | 2 |
| ActivityPlan | HAS_DOCUMENT_SET | DocumentSet | 2 |
| ActivityPlan | HAS_ASSIGNEE | Employee | 2 |
| ActivityPlan | HAS_LAST_COMPLETED_BY | Employee | 2 |
| ActivityPlan | HAS_ASSIGNEE_ROLE | RoleDef | 2 |
| AlarmDefinition | HAS_ACTION | ActionDefinition | 2 |
| AlarmDefinition | HAS_DOCUMENT_SET | DocumentSet | 2 |
| ApprovalDecision | HAS_APPROVAL_DECISION_LIST | ApprovalDecisionList | 2 |
| ApprovalSheet | HAS_APPROVAL_DECISION_LIST | ApprovalDecisionList | 2 |
| ApprovalSheetTemplate | HAS_APPROVAL_DECISION_LIST | ApprovalDecisionList | 2 |
| AttachedDocs | HAS_DOC_ATTACHMENTS | DocAttachments | 2 |
| BOM | HAS_BOM_BASE | BOMBase | 2 |
| BOM | HAS_BILL_TYPE | BillType | 2 |
| BOMBase | HAS_REV_OF_RCD | BOM | 2 |
| BillOfProcess | HAS_BILL_OF_PROCESS_BASE | BillOfProcessBase | 2 |
| BillOfProcessBase | HAS_REV_OF_RCD | BillOfProcess | 2 |
| BillOfProcessOverride | HAS_BILL_OF_PROCESS | BillOfProcess | 2 |
| BillOfProcessOverride | HAS_RECIPE_FILE | Document | 2 |
| BillOfProcessOverride | HAS_DOCUMENT_SET | DocumentSet | 2 |
| BillOfProcessOverride | HAS_ELECTRONIC_PROCEDURE | ElectronicProcedure | 2 |
| BillOfProcessOverride | HAS_RESOURCE_GROUP | ResourceGroup | 2 |
| BillOfProcessOverride | HAS_SETUP | Setup | 2 |
| BillOfProcessOverride | HAS_SPEC | Spec | 2 |
| BillOfProcessOverride | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| BizRuleHandlerParameter | HAS_BUSINESS_RULE_HANDLER_DATA | BusinessRuleHandlerData | 2 |
| BizRuleParameter | HAS_PARAM_SPEC | BizRuleHandlerParameter | 2 |
| BizRuleParameter | HAS_BUSINESS_RULE_DATA | BusinessRuleData | 2 |
| BizRuleParameter | HAS_BUSINESS_RULE_HANDLER | BusinessRuleHandler | 2 |
| BusinessProcessSpec | HAS_BUSINESS_PROCESS_SPEC_BASE | BusinessProcessSpecBase | 2 |
| BusinessProcessSpec | HAS_MOVE_STD_VALIDATION | BusinessRule | 2 |
| BusinessProcessSpecBase | HAS_REV_OF_RCD | BusinessProcessSpec | 2 |
| BusinessProcessWorkflow | HAS_BUSINESS_PROCESS_WORKFLOW_BASE | BusinessProcessWorkflowBase | 2 |
| BusinessProcessWorkflow | HAS_FIRST_STEP | WorkflowStep | 2 |
| BusinessProcessWorkflowBase | HAS_REV_OF_RCD | BusinessProcessWorkflow | 2 |
| BusinessRule | HAS_BUSINESS_RULE_DATA | BusinessRuleData | 2 |
| BusinessRuleData | HAS_BUSINESS_RULE | BusinessRule | 2 |
| BusinessRuleHandler | HAS_BUSINESS_RULE_HANDLER_DATA | BusinessRuleHandlerData | 2 |
| BusinessRuleHandlerData | HAS_BUSINESS_RULE_HANDLER | BusinessRuleHandler | 2 |
| CAPA | HAS_CAPA_CUSTOM_DATA | CAPACustomData | 2 |
| CAPA | HAS_CAR_SEVERITY | CARSeverity | 2 |
| CAPA | HAS_CLASSIFICATION | Classification | 2 |
| CAPA | HAS_ATTACHMENTS | DocAttachments | 2 |
| CAPA | HAS_CLOSED_BY | Employee | 2 |
| CAPA | HAS_INITIATOR | Employee | 2 |
| CAPA | HAS_OWNER | Employee | 2 |
| CAPA | HAS_REPORTER | Employee | 2 |
| CAPA | HAS_INITIATOR_ORGANIZATION | Organization | 2 |
| CAPA | HAS_ORGANIZATION | Organization | 2 |
| CAPA | HAS_REPORTER_ORGANIZATION | Organization | 2 |
| CAPA | HAS_PRIORITY_LEVEL | PriorityLevel | 2 |
| CAPA | HAS_PROCESS_MODEL | ProcessModel | 2 |
| CAPA | HAS_ORIG_PROCESS_MODEL_TEMPLATE | ProcessModelTemplate | 2 |
| CAPA | HAS_QUALITY_RESOLUTION_CODE | QualityResolutionCode | 2 |
| CAPA | HAS_RISK_ASSESSMENT | RiskAssessment | 2 |
| CAPA | HAS_ROLE | RoleDef | 2 |
| CAPA | HAS_SUB_CLASSIFICATION | SubClassification | 2 |
| CalendarShift | HAS_SHIFT | Shift | 2 |
| CalendarShift | HAS_TEAM | Team | 2 |
| ChangePackage | HAS_PRIORITY | ChangePackagePriority | 2 |
| ChangePackage | HAS_REASON | ChangePackageReason | 2 |
| ChangePackage | HAS_AUTHOR | Employee | 2 |
| ChangePackage | HAS_OWNER | Employee | 2 |
| ChangePackage | HAS_PACKAGE_CREATION_TEMPLATE | PackageCreationTemplate | 2 |
| ChangePackage | HAS_PACKAGE_TYPE | PackageType | 2 |
| ChangePackage | HAS_OWNER_ROLE | RoleDef | 2 |
| ChecklistEntry | HAS_PARENT | ChecklistTemplate | 2 |
| ChecklistEntry | HAS_LAST_COMPLETED_BY | Employee | 2 |
| ChecklistEntry | HAS_RESPONSE_SET | ResponseSet | 2 |
| ChecklistEntry | HAS_LAST_COMPLETED_BY_ROLE | RoleDef | 2 |
| ChecklistTemplate | HAS_CHECKLIST_TEMPLATE_BASE | ChecklistTemplateBase | 2 |
| ChecklistTemplateBase | HAS_REV_OF_RCD | ChecklistTemplate | 2 |
| CollaboratorEntry | HAS_DELEGATION_TASK | DelegationTask | 2 |
| CollaboratorEntry | HAS_ASSIGNED_COLLABORATOR | Employee | 2 |
| CollaboratorEntry | HAS_COLLABORATOR | Employee | 2 |
| CollaboratorEntry | HAS_COMPLETED_BY | Employee | 2 |
| CollaboratorEntry | HAS_ROLE | RoleDef | 2 |
| CollectionGate | HAS_ENTRY_STEP | WorkflowStep | 2 |
| CollectionGate | HAS_EXIT_STEP | WorkflowStep | 2 |
| CombineHistory | HAS_CONTAINER | Container | 2 |
| CombineHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| ComputationParamSpec | HAS_PARENT | Computation | 2 |
| Container | HAS_BILL_OF_PROCESS | BillOfProcess | 2 |
| Container | HAS_BATCH | Container | 2 |
| Container | HAS_ISSUED_TO_CONTAINER | Container | 2 |
| Container | HAS_ORIGINAL_CONTAINER | Container | 2 |
| Container | HAS_PARENT_CONTAINER | Container | 2 |
| Container | HAS_SPLIT_FROM | Container | 2 |
| Container | HAS_START_PARENT_CONTAINER | Container | 2 |
| Container | HAS_LEVEL | ContainerLevel | 2 |
| Container | HAS_CURRENT_STATUS | CurrentStatus | 2 |
| Container | HAS_CUSTOMER | Customer | 2 |
| Container | HAS_ORIGINAL_FACTORY | Factory | 2 |
| Container | HAS_HOLD_REASON | HoldReason | 2 |
| Container | HAS_MASTER_RECIPE | MasterRecipe | 2 |
| Container | HAS_SAMPLING_LOT | MfgLot | 2 |
| Container | HAS_MFG_ORDER | MfgOrder | 2 |
| Container | HAS_OWNER | Owner | 2 |
| Container | HAS_PRIORITY_CODE | PriorityCode | 2 |
| Container | HAS_PLANNED_PRODUCT | Product | 2 |
| Container | HAS_PRODUCT | Product | 2 |
| Container | HAS_LAST_CARRIER | ResourceDef | 2 |
| Container | HAS_SALES_ORDER | SalesOrder | 2 |
| Container | HAS_START_REASON | StartReason | 2 |
| Container | HAS_FACTORY_START_UOM | UOM | 2 |
| Container | HAS_FACTORY_START_UOM2 | UOM | 2 |
| Container | HAS_ORIGINAL_UOM | UOM | 2 |
| Container | HAS_ORIGINAL_UOM2 | UOM | 2 |
| Container | HAS_PLANNED_QTY_UOM | UOM | 2 |
| Container | HAS_PLANNED_QTY_UOM2 | UOM | 2 |
| Container | HAS_UOM | UOM | 2 |
| Container | HAS_UOM2 | UOM | 2 |
| Container | HAS_VENDOR_ITEM | VendorItem | 2 |
| ContainerAutoHoldReq | HAS_MFG_ORDER | MfgOrder | 2 |
| ContainerLevel | HAS_CONTAINER_NUMBERING_RULE | NumberingRule | 2 |
| ContainerStatusChangeHistory | HAS_CHANGE_STATUS_REASON | ChangeStatusReason | 2 |
| ContainerStatusChangeHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| CurrentStatus | HAS_FACTORY | Factory | 2 |
| CurrentStatus | HAS_LOCATION | Location | 2 |
| CurrentStatus | HAS_INITIAL_RECIPE_LIST | RecipeList | 2 |
| CurrentStatus | HAS_CARRIER | ResourceDef | 2 |
| CurrentStatus | HAS_RESOURCE | ResourceDef | 2 |
| CurrentStatus | HAS_WORKSTATION | ResourceDef | 2 |
| CurrentStatus | HAS_SPEC | Spec | 2 |
| CurrentStatus | HAS_WORKFLOW_STEP | WorkflowStep | 2 |
| CustomerContact | HAS_CUSTOMER | Customer | 2 |
| CycleTimeGate | HAS_ENTRY_STEP | WorkflowStep | 2 |
| CycleTimeGate | HAS_EXIT_STEP | WorkflowStep | 2 |
| DataCollectionDef | HAS_DATA_COLLECTION_DEF_BASE | DataCollectionDefBase | 2 |
| DataCollectionDef | HAS_SPC_CHART_DEF_GROUP | NamedObjectGroup | 2 |
| DataCollectionDefBase | HAS_REV_OF_RCD | DataCollectionDef | 2 |
| DataPoint | HAS_UOM | UOM | 2 |
| DataPointCollection | HAS_PARENT | Container | 2 |
| DataPointCollectionGroup | HAS_DATA_POINT_COLLECTION | DataCollectionDef | 2 |
| DataPointCollectionGroup | HAS_LAST_ENTERED_BY | Employee | 2 |
| DataPointCollectionGroup | HAS_LAST_ENTERED_BY_ROLE | RoleDef | 2 |
| DelegateTaskHistory | HAS_DELEGATION_REASON_CODE | DelegationReasonCode | 2 |
| DelegateTaskHistory | HAS_SOURCE_EMPLOYEE | Employee | 2 |
| DelegateTaskHistory | HAS_TARGET_EMPLOYEE | Employee | 2 |
| DelegateTaskHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| DelegationTask | HAS_DELEGATION_REASON | DelegationReasonCode | 2 |
| DelegationTask | HAS_ASSIGNED_EMPLOYEE | Employee | 2 |
| DelegationTask | HAS_DELEGATED_BY | Employee | 2 |
| DelegationTask | HAS_TARGET_EMPLOYEE | Employee | 2 |
| DispatchDetail | HAS_DISPATCH_RULE | DispatchRule | 2 |
| Document | HAS_ATTACHMENT_HOLDER | DocAttachments | 2 |
| Document | HAS_DOCUMENT_BASE | DocumentBase | 2 |
| Document | HAS_VIEWER | DocumentViewer | 2 |
| DocumentBase | HAS_REV_OF_RCD | Document | 2 |
| DocumentEntry | HAS_DOCUMENT | Document | 2 |
| DocumentEntry | HAS_DOCUMENT_SET | DocumentSet | 2 |
| DynamicNumberingRule | HAS_NEW_DYNAMIC_NUMBERING_RULE | DynamicNumberingRule | 2 |
| DynamicNumberingRule | HAS_RESOLVED_NUMBERING_RULE | DynamicNumberingRule | 2 |
| EProcedureDetail | HAS_ELECTRONIC_PROCEDURE | ElectronicProcedure | 2 |
| EProcedureDetail | HAS_TASK_LIST | TaskList | 2 |
| ERPBOM | HAS_BILL_TYPE | BillType | 2 |
| ERPBOM | HAS_ERPBOM_BASE | ERPBOMBase | 2 |
| ERPBOM | HAS_ERP_ROUTE | ERPRoute | 2 |
| ERPBOMBase | HAS_REV_OF_RCD | ERPBOM | 2 |
| ERPRoute | HAS_ERP_ROUTE_BASE | ERPRouteBase | 2 |
| ERPRoute | HAS_PRODUCT | Product | 2 |
| ERPRouteBase | HAS_REV_OF_RCD | ERPRoute | 2 |
| ElectronicProcedure | HAS_ELECTRONIC_PROCEDURE_BASE | ElectronicProcedureBase | 2 |
| ElectronicProcedureBase | HAS_REV_OF_RCD | ElectronicProcedure | 2 |
| Employee | HAS_EMPLOYEE_LOGIN_INFO | EmployeeLoginInfo | 2 |
| Employee | HAS_PRIMARY_ORGANIZATION | Organization | 2 |
| Employee | HAS_SESSION_VALUES | SessionValues | 2 |
| Employee | HAS_TRAINING_PLAN | TrainingPlan | 2 |
| EmployeeLoginInfo | HAS_EMPLOYEE | Employee | 2 |
| EmployeeRole | HAS_EMPLOYEE | Employee | 2 |
| EmployeeRole | HAS_ORGANIZATION | Organization | 2 |
| EmployeeRole | HAS_ROLE | RoleDef | 2 |
| Enterprise | HAS_LIVE_CONNECT_PROXY_SITE | Site | 2 |
| Enterprise | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| Event | HAS_CHECKLIST | Checklist | 2 |
| Event | HAS_CLASSIFICATION | Classification | 2 |
| Event | HAS_ATTACHMENTS | DocAttachments | 2 |
| Event | HAS_CLOSED_BY | Employee | 2 |
| Event | HAS_INITIATOR | Employee | 2 |
| Event | HAS_OWNER | Employee | 2 |
| Event | HAS_REPORTER | Employee | 2 |
| Event | HAS_EVENT_DATA | EventData | 2 |
| Event | HAS_INITIATOR_ORGANIZATION | Organization | 2 |
| Event | HAS_ORGANIZATION | Organization | 2 |
| Event | HAS_REPORTER_ORGANIZATION | Organization | 2 |
| Event | HAS_PRIORITY_LEVEL | PriorityLevel | 2 |
| Event | HAS_PROCESS_MODEL | ProcessModel | 2 |
| Event | HAS_ORIG_PROCESS_MODEL_TEMPLATE | ProcessModelTemplate | 2 |
| Event | HAS_QUALITY_RESOLUTION_CODE | QualityResolutionCode | 2 |
| Event | HAS_RISK_ASSESSMENT | RiskAssessment | 2 |
| Event | HAS_ROLE | RoleDef | 2 |
| Event | HAS_SUB_CLASSIFICATION | SubClassification | 2 |
| EventData | HAS_EVENT | Event | 2 |
| EventData | HAS_OCCUPATION | Occupation | 2 |
| EventData | HAS_COMPENSATE_CUSTOMER_ACTION | ReturnedEquipmentAction | 2 |
| EventDisposition | HAS_DISPOSITION | Disposition | 2 |
| EventFailure | HAS_EVENT_DATA | EventData | 2 |
| EventFailure | HAS_FAILURE_MODE | FailureMode | 2 |
| EventFailure | HAS_FAILURE_SEVERITY | FailureSeverity | 2 |
| EventFailure | HAS_FAILURE_TYPE | NCRFailureType | 2 |
| EventFailureAction | HAS_ACTION_OWNER | Employee | 2 |
| EventFailureAction | HAS_PARENT | EventData | 2 |
| EventFailureAction | HAS_ACTION_TYPE | FailureActionType | 2 |
| EventLog | HAS_COMMENT_TYPE | CommentType | 2 |
| EventLog | HAS_EMPLOYEE | Employee | 2 |
| EventLog | HAS_EVENT_DATA | EventData | 2 |
| ExecuteMfgOrderTaskHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| ExecuteMfgOrderTaskHistory | HAS_MFG_ORDER | MfgOrder | 2 |
| ExecuteMfgOrderTaskHistory | HAS_MFG_ORDER_PROCEDURE | MfgOrderProcedure | 2 |
| ExecuteMfgOrderTaskHistory | HAS_MFG_ORDER_TASK_LIST | MfgOrderTaskList | 2 |
| ExecuteMfgOrderTaskHistory | HAS_TASK_STATUS | MfgOrderTaskStatus | 2 |
| ExecuteMfgOrderTaskHistory | HAS_TASK | TaskItem | 2 |
| ExecuteMfgOrderTaskHistory | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| ExecuteSamplingLotHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| ExecuteSamplingLotHistory | HAS_REWORK_REASON | ReworkReason | 2 |
| ExecuteSamplingLotHistory | HAS_SCRAP_REASON | ScrapReason | 2 |
| Factory | HAS_CHANGE_MGT_APPLICATION | ChangeMgtApplication | 2 |
| Factory | HAS_SMTP_TRANSPORT | DataTransport | 2 |
| Factory | HAS_DISPATCH_RULE | DispatchRule | 2 |
| Factory | HAS_ENTERPRISE | Enterprise | 2 |
| Factory | HAS_CONTAINER_AUTO_HOLD_REASON | HoldReason | 2 |
| Factory | HAS_MFG_CALENDAR | MfgCalendar | 2 |
| Factory | HAS_CONTAINER_NUMBERING_RULE | NumberingRule | 2 |
| Factory | HAS_SLIT_NUMBERING_RULE | NumberingRule | 2 |
| Factory | HAS_ORGANIZATION | Organization | 2 |
| Factory | HAS_PRINT_QUEUE | PrintQueue | 2 |
| Factory | HAS_RESOURCE_STATUS_MODEL | ResourceStatusModel | 2 |
| Factory | HAS_SHOP_FLOOR_SETTINGS | ShopFloorSettings | 2 |
| Factory | HAS_SMART_SCAN_RULE | SmartScanRule | 2 |
| Factory | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| FailureMode | HAS_DEFAULT_SEVERITY | FailureSeverity | 2 |
| FailureMode | HAS_DEFAULT_TYPE | NCRFailureType | 2 |
| HistoryMainline | HAS_MFG_PROCESS_OVERRIDES | BillOfProcess | 2 |
| HistoryMainline | HAS_CALENDAR_SHIFT | CalendarShift | 2 |
| HistoryMainline | HAS_BATCH | Container | 2 |
| HistoryMainline | HAS_CONTAINER | Container | 2 |
| HistoryMainline | HAS_EMPLOYEE | Employee | 2 |
| HistoryMainline | HAS_LOGIN | Employee | 2 |
| HistoryMainline | HAS_USER | Employee | 2 |
| HistoryMainline | HAS_FACTORY | Factory | 2 |
| HistoryMainline | HAS_OPERATION | Operation | 2 |
| HistoryMainline | HAS_OWNER | Owner | 2 |
| HistoryMainline | HAS_PRODUCT | Product | 2 |
| HistoryMainline | HAS_CARRIER | ResourceDef | 2 |
| HistoryMainline | HAS_RESOURCE | ResourceDef | 2 |
| HistoryMainline | HAS_WORKSTATION | ResourceDef | 2 |
| HistoryMainline | HAS_RESOURCE_STATUS_CODE | ResourceStatusCode | 2 |
| HistoryMainline | HAS_RESOURCE_STATUS_REASON | ResourceStatusReason | 2 |
| HistoryMainline | HAS_SPEC | Spec | 2 |
| HistoryMainline | HAS_WORKFLOW_STEP | WorkflowStep | 2 |
| HoldReleaseHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| HoldReleaseHistory | HAS_HOLD_REASON | HoldReason | 2 |
| HoldReleaseHistory | HAS_RELEASE_REASON | ReleaseReason | 2 |
| HoldStatus | HAS_HOLD_REASON | HoldReason | 2 |
| IssueActualsHistory | HAS_FROM_BATCH | Container | 2 |
| IssueActualsHistory | HAS_FROM_CONTAINER | Container | 2 |
| IssueActualsHistory | HAS_TO_CONTAINER | Container | 2 |
| IssueActualsHistory | HAS_ISSUE_DIFFERENCE_REASON | IssueDifferenceReason | 2 |
| IssueActualsHistory | HAS_ISSUE_REASON | IssueReason | 2 |
| IssueActualsHistory | HAS_FROM_LOCATION | Location | 2 |
| IssueActualsHistory | HAS_TO_LOCATION | Location | 2 |
| IssueActualsHistory | HAS_PRODUCT | Product | 2 |
| IssueActualsHistory | HAS_FROM_CARRIER | ResourceDef | 2 |
| IssueActualsHistory | HAS_RESOURCE | ResourceDef | 2 |
| IssueActualsHistory | HAS_SUBSTITUTION_REASON | SubstitutionReason | 2 |
| IssueActualsHistory | HAS_VENDOR_ITEM | VendorItem | 2 |
| KPIEntry | HAS_KPI_MATRIX | KPIMatrix | 2 |
| KPIEntry | HAS_KPI_TIMEFRAME | KPITimeframe | 2 |
| KPIEntry | HAS_KPI_TYPE | KPIType | 2 |
| KPIEntry | HAS_OPERATION | Operation | 2 |
| KPIEntry | HAS_PRODUCT | Product | 2 |
| KPIEntry | HAS_RESOURCE | ResourceDef | 2 |
| KPIEntry | HAS_RESOURCE_TYPE | ResourceType | 2 |
| KPIEntry | HAS_ROUTE_STEP | RouteStep | 2 |
| KPIEntry | HAS_SPEC | Spec | 2 |
| KPIEntry | HAS_UOM | UOM | 2 |
| Location | HAS_FACTORY | Factory | 2 |
| MaintenanceReq | HAS_JOB_MODEL | A_JobModel | 2 |
| MaintenanceReq | HAS_BOM | A_ResourceBOM | 2 |
| MaintenanceReq | HAS_DATA_COLLECTION | DataCollectionDef | 2 |
| MaintenanceReq | HAS_DOCUMENT_SET | DocumentSet | 2 |
| MaintenanceReq | HAS_MAINTENANCE_REASON | MaintenanceReason | 2 |
| MaintenanceReq | HAS_MAINTENANCE_REQ_BASE | MaintenanceReqBase | 2 |
| MaintenanceReq | HAS_UOM | UOM | 2 |
| MaintenanceReq | HAS_UOM2 | UOM | 2 |
| MaintenanceReqBase | HAS_REV_OF_RCD | MaintenanceReq | 2 |
| MasterDataCatalogDtl | HAS_MASTER_DATA_CATALOG | MasterDataCatalog | 2 |
| MasterRecipe | HAS_MASTER_RECIPE_BASE | MasterRecipeBase | 2 |
| MasterRecipe | HAS_PRINTER_LABEL_DEFINITION | PrinterLabelDefinition | 2 |
| MasterRecipe | HAS_RECIPE_PRODUCT | Product | 2 |
| MasterRecipe | HAS_RECIPE_UOM | UOM | 2 |
| MasterRecipe | HAS_WORKFLOW | Workflow | 2 |
| MasterRecipeBase | HAS_REV_OF_RCD | MasterRecipe | 2 |
| MasterRecipeDetail | HAS_MASTER_RECIPE | MasterRecipe | 2 |
| MasterRecipeDetail | HAS_TASK_LIST | RecipeList | 2 |
| MasterRecipeDetail | HAS_SPEC | Spec | 2 |
| MfgLot | HAS_PRODUCT | Product | 2 |
| MfgLot | HAS_SAMPLING_PLAN | SamplingPlan | 2 |
| MfgLot | HAS_UOM | UOM | 2 |
| MfgOrder | HAS_BILL_OF_PROCESS | BillOfProcess | 2 |
| MfgOrder | HAS_ERPBOM | ERPBOM | 2 |
| MfgOrder | HAS_ERP_ROUTE | ERPRoute | 2 |
| MfgOrder | HAS_REPORTING_FACTORY | Factory | 2 |
| MfgOrder | HAS_HOLD_STATUS | HoldStatus | 2 |
| MfgOrder | HAS_POST_PRODUCTION_PROCEDURE | MfgOrderProcedure | 2 |
| MfgOrder | HAS_PRE_PRODUCTION_PROCEDURE | MfgOrderProcedure | 2 |
| MfgOrder | HAS_CONTAINER_NUMBERING_RULE | NumberingRule | 2 |
| MfgOrder | HAS_ORDER_STATUS | OrderStatus | 2 |
| MfgOrder | HAS_ORDER_TYPE | OrderType | 2 |
| MfgOrder | HAS_PRIORITY | PriorityCode | 2 |
| MfgOrder | HAS_BEGIN_PRODUCT | Product | 2 |
| MfgOrder | HAS_PRODUCT | Product | 2 |
| MfgOrder | HAS_UOM | UOM | 2 |
| MfgOrder | HAS_UOM2 | UOM | 2 |
| MfgOrderProcedure | HAS_MFG_ORDER_PROCEDURE_BASE | MfgOrderProcedureBase | 2 |
| MfgOrderProcedure | HAS_COMPLETED_ORDER_STATUS | OrderStatus | 2 |
| MfgOrderProcedureBase | HAS_REV_OF_RCD | MfgOrderProcedure | 2 |
| MfgOrderProcedureDetail | HAS_MFG_ORDER_PROCEDURE | MfgOrderProcedure | 2 |
| MfgOrderProcedureDetail | HAS_MFG_ORDER_TASK_LIST | MfgOrderTaskList | 2 |
| MfgOrderTaskList | HAS_PREREQUISITE_TASK_LIST | MfgOrderTaskList | 2 |
| MfgOrderTaskList | HAS_MFG_ORDER_TASK_LIST_BASE | MfgOrderTaskListBase | 2 |
| MfgOrderTaskList | HAS_WORKSTATION | ResourceDef | 2 |
| MfgOrderTaskList | HAS_WORKSTATION_GROUP | ResourceGroup | 2 |
| MfgOrderTaskList | HAS_IS_IMAGE | isImage | 2 |
| MfgOrderTaskListBase | HAS_REV_OF_RCD | MfgOrderTaskList | 2 |
| MoveHistory | HAS_TO_CUSTOMER | Customer | 2 |
| MoveHistory | HAS_TO_FACTORY | Factory | 2 |
| MoveHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| MoveHistory | HAS_LOCATION | Location | 2 |
| MoveHistory | HAS_TO_LOCATION | Location | 2 |
| MoveHistory | HAS_OWNER | Owner | 2 |
| MoveHistory | HAS_PATH | Path | 2 |
| MoveHistory | HAS_PRODUCT | Product | 2 |
| MoveHistory | HAS_TO_RESOURCE | ResourceDef | 2 |
| MoveHistory | HAS_REWORK_REASON | ReworkReason | 2 |
| MoveHistory | HAS_SETUP | Setup | 2 |
| MoveHistory | HAS_SHIPMENT_DESTINATION | ShipmentDestination | 2 |
| MoveHistory | HAS_TO_SPEC | Spec | 2 |
| MoveHistory | HAS_UOM | UOM | 2 |
| MoveHistory | HAS_UOM2 | UOM | 2 |
| MoveHistory | HAS_END_REWORK_STEP | WorkflowStep | 2 |
| MoveHistory | HAS_RE_ENTRY_STEP | WorkflowStep | 2 |
| MoveHistory | HAS_STEP | WorkflowStep | 2 |
| MoveHistory | HAS_TO_STEP | WorkflowStep | 2 |
| MoveInHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| MoveInHistory | HAS_LOCATION | Location | 2 |
| MoveInHistory | HAS_OWNER | Owner | 2 |
| MoveInHistory | HAS_PRODUCT | Product | 2 |
| MoveInHistory | HAS_SETUP | Setup | 2 |
| MoveInHistory | HAS_UOM | UOM | 2 |
| MoveInHistory | HAS_UOM2 | UOM | 2 |
| NCRCauseCode | HAS_NCR_RESOLUTION_CODE_GROUP | NCRResolutionCodeGroup | 2 |
| NCRDefectData | HAS_CONTAINER | Container | 2 |
| NCRDefectData | HAS_ACTUAL_COMPONENT_ISSUE | IssueActualsHistory | 2 |
| NCRDefectData | HAS_PRODUCT | Product | 2 |
| NonconformanceReport | HAS_CONTAINER | Container | 2 |
| NonconformanceReport | HAS_ATTACHMENTS | DocAttachments | 2 |
| NonconformanceReport | HAS_ESCALATED_BY | Employee | 2 |
| NonconformanceReport | HAS_NCR_CAUSE_CODE | NCRCauseCode | 2 |
| NonconformanceReport | HAS_NCR_CAUSE_CODE_GROUP | NCRCauseCodeGroup | 2 |
| NonconformanceReport | HAS_NCR_FAILURE_TYPE | NCRFailureType | 2 |
| NonconformanceReport | HAS_NCR_RESOLUTION_CODE | NCRResolutionCode | 2 |
| NonconformanceReport | HAS_RELATED_NONCONFORMANCE | NonconformanceReport | 2 |
| NonconformanceReport | HAS_TASK | TaskItem | 2 |
| NonconformanceReport | HAS_CHARGE_TO_STEP | WorkflowStep | 2 |
| NonconformanceReportNCRFailure | HAS_NCR_FAILURE_CODES | NCRFailureCode | 2 |
| NonconformanceReportNCRFailure | HAS_NONCONFORMANCE_REPORT | NonconformanceReport | 2 |
| Operation | HAS_BONUS_REASONS | BonusReasonGroup | 2 |
| Operation | HAS_BUY_REASONS | BuyReasonGroup | 2 |
| Operation | HAS_COMPONENT_DEFECT_REASONS | CompDefectReasonGroup | 2 |
| Operation | HAS_CONTAINER_DEFECT_REASONS | ContDefectReasonGroup | 2 |
| Operation | HAS_THRUPUT_REPORTING_LEVEL | ContainerLevel | 2 |
| Operation | HAS_DISPATCH_RULE | DispatchRule | 2 |
| Operation | HAS_LOCAL_REWORK_REASONS | LocalReworkReasonGroup | 2 |
| Operation | HAS_LOSS_REASONS | LossReasonGroup | 2 |
| Operation | HAS_PRINT_QUEUE | PrintQueue | 2 |
| Operation | HAS_QTY_ADJUST_REASON | QtyAdjustGroup | 2 |
| Operation | HAS_REWORK_REASONS | ReworkReasonGroup | 2 |
| Operation | HAS_DEFAULT_ROLLUP_REASON | RollupReason | 2 |
| Operation | HAS_SELL_REASONS | SellReasonGroup | 2 |
| Operation | HAS_SHIPMENT_DESTINATIONS | ShipmentDestinationGrp | 2 |
| Operation | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| Operation | HAS_WORK_CENTER | WorkCenter | 2 |
| Organization | HAS_SMTP_TRANSPORT | DataTransport | 2 |
| Organization | HAS_PARENT_ORGANIZATION | Organization | 2 |
| Organization | HAS_PRINT_QUEUE | PrintQueue | 2 |
| PackageCreationTemplate | HAS_APPROVAL_TEMPLATE | ApprovalSheetTemplate | 2 |
| PackageCreationTemplate | HAS_WORKFLOW | BusinessProcessWorkflow | 2 |
| PackageCreationTemplate | HAS_PACKAGE_PRIORITY_CODE | ChangePackagePriority | 2 |
| PackageCreationTemplate | HAS_PACKAGE_CREATION_REASON | ChangePackageReason | 2 |
| PackageCreationTemplate | HAS_COLLABORATOR_TEMPLATE | CollaboratorTemplate | 2 |
| PackageCreationTemplate | HAS_PACKAGE_OWNER | Employee | 2 |
| PackageCreationTemplate | HAS_PACKAGE_TYPE | PackageType | 2 |
| PackageCreationTemplate | HAS_OWNER_ROLE | RoleDef | 2 |
| PackageCreationTemplate | HAS_SOURCE_SYSTEM | TargetSystem | 2 |
| Path | HAS_END_REWORK_STEP | WorkflowStep | 2 |
| Path | HAS_FROM_STEP | WorkflowStep | 2 |
| Path | HAS_RETURN_TO_STEP | WorkflowStep | 2 |
| Path | HAS_RE_ENTRY_STEP | WorkflowStep | 2 |
| Path | HAS_TO_STEP | WorkflowStep | 2 |
| PathSelector | HAS_PATH | Path | 2 |
| PathSelector | HAS_STEP | WorkflowStep | 2 |
| PauseTaskHistory | HAS_CONTAINER | Container | 2 |
| PauseTaskHistory | HAS_ELECTRONIC_PROCEDURE | ElectronicProcedure | 2 |
| PauseTaskHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| PauseTaskHistory | HAS_PAUSE_REASON | PauseReason | 2 |
| PauseTaskHistory | HAS_TASK | TaskItem | 2 |
| PauseTaskHistory | HAS_STEP | WorkflowStep | 2 |
| Phase | HAS_LAST_APPROVAL_ROUTED | ApprovalSheet | 2 |
| Phase | HAS_CHECKLIST | Checklist | 2 |
| Phase | HAS_DATA_POINT_COLLECTION | DataPointCollection | 2 |
| Phase | HAS_ATTACHMENTS | DocAttachments | 2 |
| Phase | HAS_DOCUMENT_SET | DocumentSet | 2 |
| Phase | HAS_ASSIGNEE | Employee | 2 |
| Phase | HAS_LAST_COMPLETED_BY | Employee | 2 |
| Phase | HAS_ASSIGNEE_ROLE | RoleDef | 2 |
| PhaseTemplate | HAS_CHECKLIST | Checklist | 2 |
| PhaseTemplate | HAS_DOCUMENT_SET | DocumentSet | 2 |
| PhaseTemplate | HAS_ASSIGNEE | Employee | 2 |
| PhaseTemplate | HAS_ASSIGNEE_ROLE | RoleDef | 2 |
| PlanTemplate | HAS_CHECKLIST | Checklist | 2 |
| PlanTemplate | HAS_DOCUMENT_SET | DocumentSet | 2 |
| PlanTemplate | HAS_ASSIGNEE | Employee | 2 |
| PlanTemplate | HAS_ASSIGNEE_ROLE | RoleDef | 2 |
| PrinterLabelDefinition | HAS_PRINTER_LABEL_DEFINITION_BASE | PrinterLabelDefinitionBase | 2 |
| PrinterLabelDefinitionBase | HAS_REV_OF_RCD | PrinterLabelDefinition | 2 |
| ProcessModel | HAS_CHECKLIST | Checklist | 2 |
| ProcessModel | HAS_DATA_POINT_COLLECTION | DataPointCollection | 2 |
| ProcessModel | HAS_ATTACHMENTS | DocAttachments | 2 |
| ProcessModel | HAS_DOCUMENT_SET | DocumentSet | 2 |
| ProcessModel | HAS_ASSIGNEE | Employee | 2 |
| ProcessModel | HAS_LAST_COMPLETED_BY | Employee | 2 |
| ProcessModel | HAS_ASSIGNEE_ROLE | RoleDef | 2 |
| ProcessModelTemplate | HAS_DOCUMENT_SET | DocumentSet | 2 |
| ProcessModelTemplate | HAS_ASSIGNEE | Employee | 2 |
| ProcessModelTemplate | HAS_PROCESS_MODEL_TEMPLATE_BASE | ProcessModelTemplateBase | 2 |
| ProcessModelTemplate | HAS_ASSIGNEE_ROLE | RoleDef | 2 |
| ProcessModelTemplateBase | HAS_REV_OF_RCD | ProcessModelTemplate | 2 |
| ProcessTimer | HAS_PROCESS_TIMER_BASE | ProcessTimerBase | 2 |
| ProcessTimer | HAS_PROCESS_TIMER_TYPE | ProcessTimerType | 2 |
| ProcessTimerBase | HAS_REV_OF_RCD | ProcessTimer | 2 |
| ProcessingGate | HAS_ENTRY_STEP | WorkflowStep | 2 |
| ProcessingGate | HAS_EXIT_STEP | WorkflowStep | 2 |
| Product | HAS_BOM | BOM | 2 |
| Product | HAS_BILL_OF_PROCESS | BillOfProcess | 2 |
| Product | HAS_CUSTOMER | Customer | 2 |
| Product | HAS_DOCUMENT_SET | DocumentSet | 2 |
| Product | HAS_ERPBOM | ERPBOM | 2 |
| Product | HAS_ERP_ROUTE | ERPRoute | 2 |
| Product | HAS_HOLD_STATUS | HoldStatus | 2 |
| Product | HAS_CONTAINER_NUMBERING_RULE | NumberingRule | 2 |
| Product | HAS_SLIT_PRODUCT | Product | 2 |
| Product | HAS_PRODUCT_BASE | ProductBase | 2 |
| Product | HAS_PRODUCT_FAMILY | ProductFamily | 2 |
| Product | HAS_PRODUCT_TYPE | ProductType | 2 |
| Product | HAS_SAMPLING_PLAN | SamplingPlan | 2 |
| Product | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| Product | HAS_STD_START_UOM | UOM | 2 |
| Product | HAS_STD_START_UOM2 | UOM | 2 |
| Product | HAS_UOM2 | UOM | 2 |
| Product | HAS_WORKFLOW | Workflow | 2 |
| Product | HAS_IS_IMAGE | isImage | 2 |
| ProductBase | HAS_REV_OF_RCD | Product | 2 |
| ProductFamily | HAS_DOCUMENT_SET | DocumentSet | 2 |
| ProductFamily | HAS_CONTAINER_NUMBERING_RULE | NumberingRule | 2 |
| ProductFamily | HAS_SAMPLING_PLAN | SamplingPlan | 2 |
| ProductFamily | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| ProductFamily | HAS_STD_START_UOM | UOM | 2 |
| ProductFamily | HAS_STD_START_UOM2 | UOM | 2 |
| ProductFamily | HAS_WORKFLOW | Workflow | 2 |
| QtyHistory | HAS_BATCH | Container | 2 |
| QtyHistory | HAS_THRUPUT_REPORTING_LEVEL | ContainerLevel | 2 |
| QtyHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| QtyHistory | HAS_MASTER_RECIPE | MasterRecipe | 2 |
| QtyHistory | HAS_CARRIER | ResourceDef | 2 |
| QtyHistory | HAS_RESOURCE | ResourceDef | 2 |
| QtyHistory | HAS_ROLLUP_REASON | RollupReason | 2 |
| QualityReportConfig | HAS_CLASSIFICATION | Classification | 2 |
| QualityReportConfig | HAS_PARENT | Organization | 2 |
| QualityReportConfig | HAS_SUB_CLASSIFICATION | SubClassification | 2 |
| RecipeList | HAS_TARGET_CONTAINER_LEVEL | ContainerLevel | 2 |
| RecipeList | HAS_TARGET_CONTAINER_PRODUCT | Product | 2 |
| RecipeList | HAS_PREREQUISITE_TASK_LIST | RecipeList | 2 |
| RecipeList | HAS_RECIPE_LIST_BASE | RecipeListBase | 2 |
| RecipeList | HAS_WORKSTATION | ResourceDef | 2 |
| RecipeList | HAS_CARRIERS | ResourceGroup | 2 |
| RecipeList | HAS_SCALES | ResourceGroup | 2 |
| RecipeList | HAS_WORKSTATION_GROUP | ResourceGroup | 2 |
| RecipeList | HAS_TARGET_CONTAINER_UOM | UOM | 2 |
| RecipeList | HAS_IS_IMAGE | isImage | 2 |
| RecipeListBase | HAS_REV_OF_RCD | RecipeList | 2 |
| ReprintLabelHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| ReprintLabelHistory | HAS_PRINT_QUEUE | PrintQueue | 2 |
| ReprintLabelHistory | HAS_REPRINT_REASON | ReprintReason | 2 |
| ResourceDef | HAS_BOM | A_ResourceBOM | 2 |
| ResourceDef | HAS_TOOL_PLAN | A_ToolPlan | 2 |
| ResourceDef | HAS_WEB_SERVICE_TRANSPORT | DataTransport | 2 |
| ResourceDef | HAS_FACTORY | Factory | 2 |
| ResourceDef | HAS_LOCATION | Location | 2 |
| ResourceDef | HAS_MAINTENANCE_CLASS | MaintenanceClass | 2 |
| ResourceDef | HAS_PRINT_QUEUE | PrintQueue | 2 |
| ResourceDef | HAS_PARENT_RESOURCE | ResourceDef | 2 |
| ResourceDef | HAS_RESOURCE_FAMILY | ResourceFamily | 2 |
| ResourceDef | HAS_RESOURCE_STATUS_MODEL | ResourceStatusModel | 2 |
| ResourceDef | HAS_RESOURCE_TYPE | ResourceType | 2 |
| ResourceDef | HAS_SMART_SCAN_RULE | SmartScanRule | 2 |
| ResourceDef | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| ResourceDef | HAS_UOM | UOM | 2 |
| ResourceDef | HAS_VENDOR | Vendor | 2 |
| ResourceFamily | HAS_RESOURCE_STATUS_MODEL | ResourceStatusModel | 2 |
| ResourceLogs | HAS_RESOURCE | ResourceDef | 2 |
| ResourceStatusCode | HAS_RESOURCE_STATUS_REASONS | ResStatusReasonGroup | 2 |
| ResourceStatusCodeGroupDef | HAS_RESOURCE_STATUS_CODE_GROUP | ResourceStatusCodeGroup | 2 |
| ResourceStatusHistory | HAS_OLD_PHYSICAL_LOCATION | A_PhysicalLocation | 2 |
| ResourceStatusHistory | HAS_PHYSICAL_LOCATION | A_PhysicalLocation | 2 |
| ResourceStatusHistory | HAS_SS_NEW_LOCATION | A_PhysicalLocation | 2 |
| ResourceStatusHistory | HAS_SS_OLD_LOCATION | A_PhysicalLocation | 2 |
| ResourceStatusHistory | HAS_OLD_PHYSICAL_POSITION | A_PhysicalPosition | 2 |
| ResourceStatusHistory | HAS_PHYSICAL_POSITION | A_PhysicalPosition | 2 |
| ResourceStatusHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| ResourceStatusHistory | HAS_OLD_PRODUCT | Product | 2 |
| ResourceStatusHistory | HAS_PRODUCT | Product | 2 |
| ResourceStatusHistory | HAS_OLD_RESOURCE_STATUS_CODE | ResourceStatusCode | 2 |
| ResourceStatusHistory | HAS_RESOURCE_STATUS_CODE | ResourceStatusCode | 2 |
| ResourceStatusHistory | HAS_OLD_RESOURCE_STATUS_REASON_CODE | ResourceStatusReason | 2 |
| ResourceStatusHistory | HAS_RESOURCE_STATUS_REASON_CODE | ResourceStatusReason | 2 |
| ResourceStatusHistory | HAS_OLD_SETUP | Setup | 2 |
| ResourceStatusHistory | HAS_SETUP | Setup | 2 |
| ResourceStatusModel | HAS_INIT_STATUS_CODES | ResourceStatusCodeGroup | 2 |
| ResourceThruputHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| ResourceThruputHistory | HAS_MFG_ORDER | MfgOrder | 2 |
| ResourceThruputHistory | HAS_PRODUCT | Product | 2 |
| ResourceThruputHistory | HAS_RESOURCE | ResourceDef | 2 |
| ResourceThruputHistory | HAS_SETUP | Setup | 2 |
| ResourceThruputHistory | HAS_UOM | UOM | 2 |
| ResourceThruputHistory | HAS_UOM2 | UOM | 2 |
| ResourceType | HAS_RESOURCE_STATUS_MODEL | ResourceStatusModel | 2 |
| ReworkStatus | HAS_CURRENT_STATUS | CurrentStatus | 2 |
| ReworkStatus | HAS_REWORK_REASON | ReworkReason | 2 |
| ReworkStatus | HAS_END_REWORK_STEP | WorkflowStep | 2 |
| ReworkStatus | HAS_RE_ENTRY_STEP | WorkflowStep | 2 |
| RouteStep | HAS_ERP_ROUTE_ID | ERPRoute | 2 |
| SPCChartDef | HAS_SPC_CHART_TYPE | A_SPCChart | 2 |
| SPCChartDef | HAS_SPC_CONNECTION | A_SPCConnection | 2 |
| SPCChartDef | HAS_SPC_RULES | A_SPCRules | 2 |
| SPCChartDef | HAS_DOC_TO_VIEW | Document | 2 |
| SPCChartDef | HAS_PUT_CONTAINER_ON_HOLD | HoldReason | 2 |
| SPCChartDef | HAS_SET_RESOURCE_STATUS | ResourceStatusCode | 2 |
| SPCRuleViolations | HAS_PARENT | A_SPCRules | 2 |
| SPCRuleViolations | HAS_SPC_VIOLATION | SPCViolation | 2 |
| SalesOrder | HAS_PRODUCT | Product | 2 |
| SalesOrder | HAS_UOM | UOM | 2 |
| SalesOrder | HAS_UOM2 | UOM | 2 |
| SampleDataPoint | HAS_SAMPLE_DATA_POINT_BASE | SampleDataPointBase | 2 |
| SampleDataPoint | HAS_UOM | UOM | 2 |
| SampleDataPointBase | HAS_REV_OF_RCD | SampleDataPoint | 2 |
| SampleTest | HAS_CLASSIFICATION | Classification | 2 |
| SampleTest | HAS_DEFAULT_FAILURE_MODE | FailureMode | 2 |
| SampleTest | HAS_DECREASE_BY_REJECT_COUNT_REASON | LossReason | 2 |
| SampleTest | HAS_DECREASE_BY_SAMPLE_SIZE_REASON | LossReason | 2 |
| SampleTest | HAS_AQL_REJECT_REASONS | LossReasonGroup | 2 |
| SampleTest | HAS_SAMPLE_TEST_BASE | SampleTestBase | 2 |
| SampleTest | HAS_SUB_CLASSIFICATION | SubClassification | 2 |
| SampleTestBase | HAS_REV_OF_RCD | SampleTest | 2 |
| SamplingPlan | HAS_AQL_LEVEL | AQLLevel | 2 |
| SamplingPlan | HAS_INSPECTION_LEVEL | InspectionLevel | 2 |
| SamplingPlan | HAS_RESOURCE | ResourceDef | 2 |
| SamplingPlan | HAS_SAMPLING_PLAN_BASE | SamplingPlanBase | 2 |
| SamplingPlan | HAS_SPEC | Spec | 2 |
| SamplingPlan | HAS_SWITCHING_RULE | SwitchingRule | 2 |
| SamplingPlan | HAS_VENDOR | Vendor | 2 |
| SamplingPlan | HAS_VENDOR_ITEM | VendorItem | 2 |
| SamplingPlanBase | HAS_REV_OF_RCD | SamplingPlan | 2 |
| ScheduledBusinessRule | HAS_ON_EXECUTE | BusinessRule | 2 |
| SchedulingRoute | HAS_PRODUCT | Product | 2 |
| SchedulingRoute | HAS_SCHEDULING_ROUTE_BASE | SchedulingRouteBase | 2 |
| SchedulingRouteBase | HAS_REV_OF_RCD | SchedulingRoute | 2 |
| SessionValues | HAS_FACTORY | Factory | 2 |
| SessionValues | HAS_OPERATION | Operation | 2 |
| SessionValues | HAS_RESOURCE | ResourceDef | 2 |
| SessionValues | HAS_WORKSTATION | ResourceDef | 2 |
| SessionValues | HAS_LAYOUT_IMAGE | ResourceLayout | 2 |
| SessionValues | HAS_SPEC | Spec | 2 |
| SessionValues | HAS_WORK_CENTER | WorkCenter | 2 |
| Setup | HAS_DOCUMENT_SET | DocumentSet | 2 |
| Setup | HAS_RESOURCE_GROUP | ResourceGroup | 2 |
| Setup | HAS_SETUP_BASE | SetupBase | 2 |
| SetupBase | HAS_REV_OF_RCD | Setup | 2 |
| ShipmentDestination | HAS_CUSTOMER | Customer | 2 |
| ShipmentDestination | HAS_FACTORY | Factory | 2 |
| ShipmentDestination | HAS_LOCATION | Location | 2 |
| ShipmentDestination | HAS_REMOTE_SITE | Site | 2 |
| ShopFloorSettings | HAS_LEVEL | ContainerLevel | 2 |
| ShopFloorSettings | HAS_OWNER | Owner | 2 |
| ShopFloorSettings | HAS_PRODUCT_TYPE | ProductType | 2 |
| ShopFloorSettings | HAS_START_REASON | StartReason | 2 |
| ShopFloorSettings | HAS_AI_INFERENCE_SERVER_CONFIG | TargetSystem | 2 |
| ShopFloorSettings | HAS_AI_TRAINING_SERVER_CONFIG | TargetSystem | 2 |
| ShopFloorSettings | HAS_WORKFLOW | Workflow | 2 |
| Site | HAS_DEFAULT_DATA_TRANSPORT | DataTransport | 2 |
| Site | HAS_E_MAIL_TRANSPORT | DataTransport | 2 |
| Site | HAS_USER | Employee | 2 |
| Spec | HAS_RECIPE_FILE | Document | 2 |
| Spec | HAS_DOCUMENT_SET | DocumentSet | 2 |
| Spec | HAS_ELECTRONIC_PROCEDURE | ElectronicProcedure | 2 |
| Spec | HAS_OPERATION | Operation | 2 |
| Spec | HAS_RESOURCE_GROUP | ResourceGroup | 2 |
| Spec | HAS_SETUP | Setup | 2 |
| Spec | HAS_SPEC_BASE | SpecBase | 2 |
| Spec | HAS_SCHEDULING_DETAIL | SpecSchedulingDetail | 2 |
| Spec | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| SpecBase | HAS_REV_OF_RCD | Spec | 2 |
| SplitHistory | HAS_FROM_CONTAINER | Container | 2 |
| SplitHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| StartHistoryDetailIssueConditi | HAS_ISSUE_CONDITIONS | IssueCondition | 2 |
| StepSchedulingDetail | HAS_STEP | WorkflowStep | 2 |
| SwitchingRule | HAS_SWITCHING_RULE_BASE | SwitchingRuleBase | 2 |
| SwitchingRuleBase | HAS_REV_OF_RCD | SwitchingRule | 2 |
| TaskItem | HAS_COMPUTATION | Computation | 2 |
| TaskItem | HAS_DATA_COLLECTION | DataCollectionDef | 2 |
| TaskItem | HAS_DOCUMENT_SET | DocumentSet | 2 |
| TaskItem | HAS_TASK_LIST | TaskList | 2 |
| TaskItem | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| TaskList | HAS_WORKSTATION | ResourceDef | 2 |
| TaskList | HAS_WORKSTATION_GROUP | ResourceGroup | 2 |
| TaskList | HAS_PREREQUISITE_TASK_LIST | TaskList | 2 |
| TaskList | HAS_TASK_LIST_BASE | TaskListBase | 2 |
| TaskList | HAS_IS_IMAGE | isImage | 2 |
| TaskListBase | HAS_REV_OF_RCD | TaskList | 2 |
| Terminal | HAS_OPERATION | Operation | 2 |
| Terminal | HAS_RESOURCE | ResourceDef | 2 |
| Terminal | HAS_WORKSTATION | ResourceDef | 2 |
| Terminal | HAS_SPEC | Spec | 2 |
| Terminal | HAS_WORK_CENTER | WorkCenter | 2 |
| ThruputHistory | HAS_CONTAINER | Container | 2 |
| ThruputHistory | HAS_HISTORY_MAINLINE | HistoryMainline | 2 |
| ThruputHistory | HAS_OPERATION | Operation | 2 |
| ThruputHistory | HAS_OWNER | Owner | 2 |
| ThruputHistory | HAS_PRODUCT | Product | 2 |
| ThruputHistory | HAS_RESOURCE | ResourceDef | 2 |
| ThruputHistory | HAS_SETUP | Setup | 2 |
| ThruputHistory | HAS_UOM | UOM | 2 |
| ThruputHistory | HAS_UOM2 | UOM | 2 |
| TrainingPlanDetail | HAS_SUB_TRAINING_PLAN | TrainingPlan | 2 |
| TrainingPlanDetail | HAS_TRAINING_PLAN | TrainingPlan | 2 |
| TrainingPlanDetail | HAS_TRAINING_REQUIREMENT | TrainingRequirement | 2 |
| TrainingRecord | HAS_EMPLOYEE | Employee | 2 |
| TrainingRecord | HAS_STATUS | TrainingRecordStatus | 2 |
| TrainingRecord | HAS_TRAINING_REQUIREMENT | TrainingRequirement | 2 |
| TrainingRequirement | HAS_SOP_DOC | Document | 2 |
| TrainingRequirement | HAS_TRAINING_REQUIREMENT_BASE | TrainingRequirementBase | 2 |
| TrainingRequirementBase | HAS_REV_OF_RCD | TrainingRequirement | 2 |
| TriageSpecDetail | HAS_CHECKLIST_TEMPLATE | ChecklistTemplate | 2 |
| TriageSpecDetail | HAS_OWNER | Employee | 2 |
| TriageSpecDetail | HAS_PROCESS_MODEL | ProcessModelTemplate | 2 |
| TriageSpecDetail | HAS_ROLE | RoleDef | 2 |
| TriageSpecDetail | HAS_TRIAGE_SPEC | TriageSpec | 2 |
| VendorItem | HAS_VENDOR | Vendor | 2 |
| WorkCenter | HAS_DISPATCH_RULE | DispatchRule | 2 |
| WorkCenter | HAS_MFG_CALENDAR | MfgCalendar | 2 |
| WorkCenter | HAS_RESOURCE_GROUP | ResourceGroup | 2 |
| WorkCenter | HAS_TRAINING_REQ_GROUP | TrainingRequirementGroup | 2 |
| Workflow | HAS_ERP_ROUTE | ERPRoute | 2 |
| Workflow | HAS_SCHEDULING_ROUTE | SchedulingRoute | 2 |
| Workflow | HAS_WORKFLOW_BASE | WorkflowBase | 2 |
| Workflow | HAS_FIRST_STEP | WorkflowStep | 2 |
| WorkflowBase | HAS_REV_OF_RCD | Workflow | 2 |
| WorkflowStep | HAS_DEFAULT_PATH | Path | 2 |
| WorkflowStep | HAS_ROUTE_STEP | RouteStep | 2 |
| WorkflowStep | HAS_SCHEDULING_ROUTE_STEP | RouteStep | 2 |
| WorkflowStep | HAS_SPEC | Spec | 2 |
| WorkflowStep | HAS_SCHEDULING_DETAIL | StepSchedulingDetail | 2 |
| WorkflowStep | HAS_SUB_WORKFLOW | Workflow | 2 |
| isImage | HAS_ATTACHMENT_HOLDER | DocAttachments | 2 |
| isImage | HAS_VIEWER | DocumentViewer | 2 |
| isImage | HAS_IS_IMAGE_BASE | isImageBase | 2 |
| isImageBase | HAS_REV_OF_RCD | isImage | 2 |

## Missing Physical Properties

_None._

## Property Type Mismatches

_None._

## Ontology Properties Without a Physical Field

| Class | Property | Type | File |
|---|---|---|---|
| A_EmployeeGroup | emailTransport | Navigation | csv_business_import_ontology.json |
| A_YieldLimits | failureEmailGroup | Navigation | csv_business_import_ontology.json |
| A_YieldLimits | failureHoldReason | Navigation | csv_business_import_ontology.json |
| A_YieldLimits | productFamily | Navigation | csv_business_import_ontology.json |
| A_YieldLimits | resourceFamily | Navigation | csv_business_import_ontology.json |
| Activity | setupAccess | Navigation | csv_business_import_ontology.json |
| ActivityPlan | setupAccess | Navigation | csv_business_import_ontology.json |
| BillOfProcessOverride | toolPlanMatrix | Navigation | csv_business_import_ontology.json |
| CalendarShift | isNonScheduledTime | Float | csv_business_import_ontology.json |
| Container | customerSerialNumber | String | csv_business_import_ontology.json |
| Container | feeder | Navigation | csv_business_import_ontology.json |
| Container | holdType | Integer | csv_business_import_ontology.json |
| Container | isAssociatedCarrier | Navigation | csv_business_import_ontology.json |
| Container | isAutoStart | Boolean | csv_business_import_ontology.json |
| Container | isCarrier | Boolean | csv_business_import_ontology.json |
| Container | isCarrierSlot | Integer | csv_business_import_ontology.json |
| Container | isFailed | Boolean | csv_business_import_ontology.json |
| Container | isHoldReasonName | String | csv_business_import_ontology.json |
| Container | isInventoryDetails | Navigation | csv_business_import_ontology.json |
| Container | isInventoryLocation | Navigation | csv_business_import_ontology.json |
| Container | isMaterialManageEnabled | Boolean | csv_business_import_ontology.json |
| Container | isProductName | String | csv_business_import_ontology.json |
| Container | isProductRevision | String | csv_business_import_ontology.json |
| Container | isRepairedDefectCount | Integer | csv_business_import_ontology.json |
| Container | isTrackedCarrier | Navigation | csv_business_import_ontology.json |
| Container | isVirtualSn | Boolean | csv_business_import_ontology.json |
| Container | lastSystemDate | DateTime | csv_business_import_ontology.json |
| Container | lastSystemDateGmt | DateTime | csv_business_import_ontology.json |
| Container | lineNumber | String | csv_business_import_ontology.json |
| Container | manufacturingDate | DateTime | csv_business_import_ontology.json |
| Container | materialExposureDuration | Float | csv_business_import_ontology.json |
| Container | materialExposureOffset | Float | csv_business_import_ontology.json |
| Container | materialTotalExposure | Float | csv_business_import_ontology.json |
| Container | materialTotalReturns | Integer | csv_business_import_ontology.json |
| Container | materialWithdrawalDate | DateTime | csv_business_import_ontology.json |
| Container | materialWithdrawalDateGmt | DateTime | csv_business_import_ontology.json |
| Container | mfgLine | Navigation | csv_business_import_ontology.json |
| Container | nffDefectCount | Integer | csv_business_import_ontology.json |
| Container | parentName | String | csv_business_import_ontology.json |
| Container | pcbNumber | Integer | csv_business_import_ontology.json |
| Container | poNumber | String | csv_business_import_ontology.json |
| Container | preventRework | Boolean | csv_business_import_ontology.json |
| Container | primarySerialNumber | String | csv_business_import_ontology.json |
| Container | receivedDate | DateTime | csv_business_import_ontology.json |
| Container | referenceContainerName | String | csv_business_import_ontology.json |
| Container | rmaNumber | String | csv_business_import_ontology.json |
| Container | scrapped | Boolean | csv_business_import_ontology.json |
| Container | serialNumber2 | String | csv_business_import_ontology.json |
| Container | serialNumber3 | String | csv_business_import_ontology.json |
| Container | vendorLotNumber | String | csv_business_import_ontology.json |
| Container | vendorName | String | csv_business_import_ontology.json |
| Container | waitTime | Float | csv_business_import_ontology.json |
| Container | workflow | Navigation | csv_business_import_ontology.json |
| Container | workflowstep | Navigation | csv_business_import_ontology.json |
| Container | xOut | Boolean | csv_business_import_ontology.json |
| ContainerLevel | childContainerNumberingRule | Navigation | csv_business_import_ontology.json |
| ContainerLevel | childSnRule | Navigation | csv_business_import_ontology.json |
| ContainerLevel | levelType | Integer | csv_business_import_ontology.json |
| ContainerLevel | parentSnRule | Navigation | csv_business_import_ontology.json |
| CurrentStatus | activityWorkflowStatus | Navigation | csv_business_import_ontology.json |
| CurrentStatus | isFactoryName | String | csv_business_import_ontology.json |
| CurrentStatus | isOpStartQty | Float | csv_business_import_ontology.json |
| CurrentStatus | isOpStartQty2 | Float | csv_business_import_ontology.json |
| CurrentStatus | isOperationName | String | csv_business_import_ontology.json |
| CurrentStatus | isResourceName | String | csv_business_import_ontology.json |
| CurrentStatus | isRouteStep | Navigation | csv_business_import_ontology.json |
| CurrentStatus | isSpecName | String | csv_business_import_ontology.json |
| CurrentStatus | isSpecRevision | String | csv_business_import_ontology.json |
| CurrentStatus | isWorkflowName | String | csv_business_import_ontology.json |
| CurrentStatus | isWorkflowRevision | String | csv_business_import_ontology.json |
| CurrentStatus | isWorkflowStepName | String | csv_business_import_ontology.json |
| CurrentStatus | isWorkflowStepSequence | Integer | csv_business_import_ontology.json |
| CurrentStatus | lastMoveOutDate | DateTime | csv_business_import_ontology.json |
| CurrentStatus | lastMoveOutDateGmt | DateTime | csv_business_import_ontology.json |
| CurrentStatus | moveInDate | DateTime | csv_business_import_ontology.json |
| CurrentStatus | moveInDateGmt | DateTime | csv_business_import_ontology.json |
| DataCollectionDef | isDefectReasonGroup | Navigation | csv_business_import_ontology.json |
| DataCollectionDef | useSpcMatrix | Boolean | csv_business_import_ontology.json |
| DataPoint | failureHoldReason | Navigation | csv_business_import_ontology.json |
| DataPoint | failureResourceStatusCode | Navigation | csv_business_import_ontology.json |
| DataPoint | failureResourceStatusReason | Navigation | csv_business_import_ontology.json |
| DataPoint | isDefectReason | Navigation | csv_business_import_ontology.json |
| DataPoint | isRequireDefectReason | Boolean | csv_business_import_ontology.json |
| Document | isEdif | Boolean | csv_business_import_ontology.json |
| Document | isJson | Boolean | csv_business_import_ontology.json |
| Document | mountingTechnology | String | csv_business_import_ontology.json |
| Employee | boxGridConfig | Navigation | csv_business_import_ontology.json |
| Employee | commandBarConfig | Navigation | csv_business_import_ontology.json |
| Employee | defectGridConfig | Navigation | csv_business_import_ontology.json |
| Employee | displayOptions | Navigation | csv_business_import_ontology.json |
| Employee | informationBarConfig | Navigation | csv_business_import_ontology.json |
| Employee | pcbToolBarConfig | Navigation | csv_business_import_ontology.json |
| Employee | trackCompleteFai | Integer | csv_business_import_ontology.json |
| Employee | useContainerList | Integer | csv_business_import_ontology.json |
| EmployeeRole | setupAccess | Navigation | csv_business_import_ontology.json |
| ExecuteSamplingLotHistory | spec | Navigation | csv_business_import_ontology.json |
| ExecuteSamplingLotHistory | txnDate | DateTime | csv_business_import_ontology.json |
| Factory | childContainerNumberingRule | Navigation | csv_business_import_ontology.json |
| Factory | childSnRule | Navigation | csv_business_import_ontology.json |
| Factory | customAddressPool | Navigation | csv_business_import_ontology.json |
| Factory | defaultRevision | String | csv_business_import_ontology.json |
| Factory | displayOptions | Navigation | csv_business_import_ontology.json |
| Factory | doNotReuseContainerName | Boolean | csv_business_import_ontology.json |
| Factory | imeiAddressPool | Navigation | csv_business_import_ontology.json |
| Factory | isAutoStartSettings | Navigation | csv_business_import_ontology.json |
| Factory | isCarrierCapacity | Integer | csv_business_import_ontology.json |
| Factory | isCarrierContainerLevel | Navigation | csv_business_import_ontology.json |
| Factory | isCarrierNumberingRule | Navigation | csv_business_import_ontology.json |
| Factory | isCarrierOwner | Navigation | csv_business_import_ontology.json |
| Factory | isCarrierStartReason | Navigation | csv_business_import_ontology.json |
| Factory | isCarrierWorkflow | Navigation | csv_business_import_ontology.json |
| Factory | isChangeJobStatusAutomatically | Boolean | csv_business_import_ontology.json |
| Factory | isDefaultInventoryLocation | Navigation | csv_business_import_ontology.json |
| Factory | isDefaultIssueDiffReason | Navigation | csv_business_import_ontology.json |
| Factory | isDefaultRemovalReason | Navigation | csv_business_import_ontology.json |
| Factory | isDefaultReplaceReason | Navigation | csv_business_import_ontology.json |
| Factory | isDisableReportingSummary | Boolean | csv_business_import_ontology.json |
| Factory | isEnableCarrierTracking | Boolean | csv_business_import_ontology.json |
| Factory | isJobScheduleStatusModel | Navigation | csv_business_import_ontology.json |
| Factory | isLocalSchedulingEnabled | Boolean | csv_business_import_ontology.json |
| Factory | isMaterialManageEnabled | Boolean | csv_business_import_ontology.json |
| Factory | isOeeSettings | Navigation | csv_business_import_ontology.json |
| Factory | isPreactorEnabled | Boolean | csv_business_import_ontology.json |
| Factory | isRecordAllSteps | Boolean | csv_business_import_ontology.json |
| Factory | isReuseTrackingContainer | Boolean | csv_business_import_ontology.json |
| Factory | isValidateMaterialQueueQty | Boolean | csv_business_import_ontology.json |
| Factory | macAddressPool | Navigation | csv_business_import_ontology.json |
| Factory | mdmGuid | String | csv_business_import_ontology.json |
| Factory | parentSnRule | Navigation | csv_business_import_ontology.json |
| Factory | requireNpiJob | Boolean | csv_business_import_ontology.json |
| Factory | settings | Navigation | csv_business_import_ontology.json |
| Factory | uniqueSerialNumbers | Boolean | csv_business_import_ontology.json |
| Factory | useContainerList | Integer | csv_business_import_ontology.json |
| Factory | useContainerNameForSn | Boolean | csv_business_import_ontology.json |
| HistoryMainline | childCount | Integer | csv_business_import_ontology.json |
| HistoryMainline | isFailed | Boolean | csv_business_import_ontology.json |
| HistoryMainline | lastMoveDate | DateTime | csv_business_import_ontology.json |
| HistoryMainline | lastMoveDateGmt | DateTime | csv_business_import_ontology.json |
| HistoryMainline | lastMoveOutDate | DateTime | csv_business_import_ontology.json |
| HistoryMainline | lastMoveOutDateGmt | DateTime | csv_business_import_ontology.json |
| HistoryMainline | moveInDate | DateTime | csv_business_import_ontology.json |
| HistoryMainline | moveInDateGmt | DateTime | csv_business_import_ontology.json |
| HistoryMainline | parentContainer | Navigation | csv_business_import_ontology.json |
| HistoryMainline | parentContainerName | String | csv_business_import_ontology.json |
| HistoryMainline | recipeId | String | csv_business_import_ontology.json |
| HistoryMainline | toQty | Float | csv_business_import_ontology.json |
| HistoryMainline | toQty2 | Float | csv_business_import_ontology.json |
| HistoryMainline | txnHistorySequence | Integer | csv_business_import_ontology.json |
| HistoryMainline | txnParentTypeName | String | csv_business_import_ontology.json |
| HistoryMainline | txnSequence | Integer | csv_business_import_ontology.json |
| HistoryMainline | txnTypeName | String | csv_business_import_ontology.json |
| HoldReason | releaseEmployeeGroup | Navigation | csv_business_import_ontology.json |
| IssueActualsHistory | bulkUid | String | csv_business_import_ontology.json |
| IssueActualsHistory | feeder | Navigation | csv_business_import_ontology.json |
| IssueActualsHistory | feederBank | Navigation | csv_business_import_ontology.json |
| IssueActualsHistory | feederSlot | Navigation | csv_business_import_ontology.json |
| IssueActualsHistory | fromLot2 | String | csv_business_import_ontology.json |
| IssueActualsHistory | fromLot3 | String | csv_business_import_ontology.json |
| IssueActualsHistory | isMaterialQueueDetails | Navigation | csv_business_import_ontology.json |
| IssueActualsHistory | replaceProduct | Navigation | csv_business_import_ontology.json |
| IssueActualsHistory | tool | Navigation | csv_business_import_ontology.json |
| IssueActualsHistory | toolName | String | csv_business_import_ontology.json |
| MfgLot | samplingLotResult | Integer | csv_business_import_ontology.json |
| MfgOrder | actualFinished | DateTime | csv_business_import_ontology.json |
| MfgOrder | childContainerNumberingRu | Navigation | csv_business_import_ontology.json |
| MfgOrder | completionPlan | String | csv_business_import_ontology.json |
| MfgOrder | continueOnFail | Boolean | csv_business_import_ontology.json |
| MfgOrder | customAddressPool | Navigation | csv_business_import_ontology.json |
| MfgOrder | customAddressQty | Integer | csv_business_import_ontology.json |
| MfgOrder | customerReference | String | csv_business_import_ontology.json |
| MfgOrder | dateShipped | DateTime | csv_business_import_ontology.json |
| MfgOrder | imeiAddressPool | Navigation | csv_business_import_ontology.json |
| MfgOrder | imeiAddressQty | Integer | csv_business_import_ontology.json |
| MfgOrder | isKittingOrder | Boolean | csv_business_import_ontology.json |
| MfgOrder | isPreactorSchedule | Navigation | csv_business_import_ontology.json |
| MfgOrder | isRecipePlan | Navigation | csv_business_import_ontology.json |
| MfgOrder | isWorkflow | Navigation | csv_business_import_ontology.json |
| MfgOrder | isWorkflowBase | Integer | csv_business_import_ontology.json |
| MfgOrder | latestCustomerRequiredDate | DateTime | csv_business_import_ontology.json |
| MfgOrder | macAddressPool | Navigation | csv_business_import_ontology.json |
| MfgOrder | macAddressQty | Integer | csv_business_import_ontology.json |
| MfgOrder | materialAttributes | String | csv_business_import_ontology.json |
| MfgOrder | mfgLine | Navigation | csv_business_import_ontology.json |
| MfgOrder | modelNumber | String | csv_business_import_ontology.json |
| MfgOrder | mpsDate | DateTime | csv_business_import_ontology.json |
| MfgOrder | originalCompletionPlan | String | csv_business_import_ontology.json |
| MfgOrder | originalPmDemandDate | DateTime | csv_business_import_ontology.json |
| MfgOrder | originalShipPlanAndRbwCommit | String | csv_business_import_ontology.json |
| MfgOrder | piso | String | csv_business_import_ontology.json |
| MfgOrder | pmDemandDate | DateTime | csv_business_import_ontology.json |
| MfgOrder | poNumber | String | csv_business_import_ontology.json |
| MfgOrder | productConversionPlan | Navigation | csv_business_import_ontology.json |
| MfgOrder | productionBom | Navigation | csv_business_import_ontology.json |
| MfgOrder | programVariant | String | csv_business_import_ontology.json |
| MfgOrder | projectCode | String | csv_business_import_ontology.json |
| MfgOrder | qty2Started | Float | csv_business_import_ontology.json |
| MfgOrder | qtyStarted | Float | csv_business_import_ontology.json |
| MfgOrder | reworkId | String | csv_business_import_ontology.json |
| MfgOrder | rmaNumber | String | csv_business_import_ontology.json |
| MfgOrder | rsdCommitment | String | csv_business_import_ontology.json |
| MfgOrder | serialNumberQty | Integer | csv_business_import_ontology.json |
| MfgOrder | startVirtualSn | Integer | csv_business_import_ontology.json |
| MfgOrder | toolPlanMatrix | Navigation | csv_business_import_ontology.json |
| MoveHistory | isFailed | Boolean | csv_business_import_ontology.json |
| MoveHistory | isFailedQty | Float | csv_business_import_ontology.json |
| MoveHistory | testId | String | csv_business_import_ontology.json |
| MoveInHistory | isFailed | Boolean | csv_business_import_ontology.json |
| MoveInHistory | isFailedQty | Float | csv_business_import_ontology.json |
| Operation | displayOptions | Navigation | csv_business_import_ontology.json |
| Operation | isDefectReasonGroup | Navigation | csv_business_import_ontology.json |
| Operation | npiDocumentView | String | csv_business_import_ontology.json |
| OrderStatus | isConfirmed | Boolean | csv_business_import_ontology.json |
| OrderStatus | isOrderStates | Integer | csv_business_import_ontology.json |
| PathSelector | allocatedPct | Integer | csv_business_import_ontology.json |
| Phase | setupAccess | Navigation | csv_business_import_ontology.json |
| ProcessModel | setupAccess | Navigation | csv_business_import_ontology.json |
| Product | cadInstructions | Navigation | csv_business_import_ontology.json |
| Product | childContainerNumberingRule | Navigation | csv_business_import_ontology.json |
| Product | childSnRule | Navigation | csv_business_import_ontology.json |
| Product | containerAction | Integer | csv_business_import_ontology.json |
| Product | customAddressPool | Navigation | csv_business_import_ontology.json |
| Product | customAddressQty | Integer | csv_business_import_ontology.json |
| Product | effectiveEndDate | DateTime | csv_business_import_ontology.json |
| Product | effectiveEndDateGmt | DateTime | csv_business_import_ontology.json |
| Product | effectiveStartDate | DateTime | csv_business_import_ontology.json |
| Product | effectiveStartDateGmt | DateTime | csv_business_import_ontology.json |
| Product | erpProductFamily | String | csv_business_import_ontology.json |
| Product | frequency | String | csv_business_import_ontology.json |
| Product | imeiAddressPool | Navigation | csv_business_import_ontology.json |
| Product | imeiAddressQty | Integer | csv_business_import_ontology.json |
| Product | inheritExposure | Boolean | csv_business_import_ontology.json |
| Product | isDefaultInventoryLocation | Navigation | csv_business_import_ontology.json |
| Product | isRecipePlan | Navigation | csv_business_import_ontology.json |
| Product | isRegisterContainers | Integer | csv_business_import_ontology.json |
| Product | macAddressPool | Navigation | csv_business_import_ontology.json |
| Product | macAddressQty | Integer | csv_business_import_ontology.json |
| Product | masterRecipe | String | csv_business_import_ontology.json |
| Product | materialAccumulateExposure | Boolean | csv_business_import_ontology.json |
| Product | materialAttributes | String | csv_business_import_ontology.json |
| Product | materialExposureDuration | Float | csv_business_import_ontology.json |
| Product | materialMaxReturns | Integer | csv_business_import_ontology.json |
| Product | materialThawingDuration | Float | csv_business_import_ontology.json |
| Product | mfgOrderRequired | Boolean | csv_business_import_ontology.json |
| Product | mountingTechnology | Integer | csv_business_import_ontology.json |
| Product | npiJob | Navigation | csv_business_import_ontology.json |
| Product | npiJobBase | Integer | csv_business_import_ontology.json |
| Product | outsourceTag | String | csv_business_import_ontology.json |
| Product | parentSnRule | Navigation | csv_business_import_ontology.json |
| Product | pinCount | Integer | csv_business_import_ontology.json |
| Product | platform | String | csv_business_import_ontology.json |
| Product | polarized | Boolean | csv_business_import_ontology.json |
| Product | productConversionPlan | Navigation | csv_business_import_ontology.json |
| Product | productionBom | Navigation | csv_business_import_ontology.json |
| Product | productionBomBase | Integer | csv_business_import_ontology.json |
| Product | propagateExposure | Boolean | csv_business_import_ontology.json |
| Product | requiredToolFamily | Navigation | csv_business_import_ontology.json |
| Product | resetReworkTotalCount | Boolean | csv_business_import_ontology.json |
| Product | reworkCycleCheck | Boolean | csv_business_import_ontology.json |
| Product | reworkCycleLimit | Integer | csv_business_import_ontology.json |
| Product | reworkHoldReason | Navigation | csv_business_import_ontology.json |
| Product | reworkLossReason | Navigation | csv_business_import_ontology.json |
| Product | schematic | Navigation | csv_business_import_ontology.json |
| Product | serialNumberConfig | Integer | csv_business_import_ontology.json |
| Product | serialNumberGeneration | Integer | csv_business_import_ontology.json |
| Product | serialNumberPrefix | String | csv_business_import_ontology.json |
| Product | serialNumberQty | Integer | csv_business_import_ontology.json |
| Product | shopfloorDocument | Navigation | csv_business_import_ontology.json |
| Product | startVirtualSn | Boolean | csv_business_import_ontology.json |
| Product | stdStartChildLevel | Navigation | csv_business_import_ontology.json |
| Product | stdStartChildQty | Float | csv_business_import_ontology.json |
| Product | stdStartChildQty2 | Float | csv_business_import_ontology.json |
| Product | stdStartCustomer | Navigation | csv_business_import_ontology.json |
| Product | stdStartFactory | Navigation | csv_business_import_ontology.json |
| Product | stdStartLevel | Navigation | csv_business_import_ontology.json |
| Product | stdStartOwner | Navigation | csv_business_import_ontology.json |
| Product | stdStartPriorityCode | Navigation | csv_business_import_ontology.json |
| Product | stdStartReason | Navigation | csv_business_import_ontology.json |
| Product | toolPlanMatrix | Navigation | csv_business_import_ontology.json |
| Product | uniqueSerialNumbers | Boolean | csv_business_import_ontology.json |
| Product | useContainerNameForSn | Boolean | csv_business_import_ontology.json |
| Product | validateBulkUid | Integer | csv_business_import_ontology.json |
| Product | validateIssueTool | Boolean | csv_business_import_ontology.json |
| ProductFamily | childContainerNumberingRule | Navigation | csv_business_import_ontology.json |
| ProductFamily | childSnRule | Navigation | csv_business_import_ontology.json |
| ProductFamily | inheritExposure | Boolean | csv_business_import_ontology.json |
| ProductFamily | isDefaultInventoryLocation | Navigation | csv_business_import_ontology.json |
| ProductFamily | isRecipePlan | Navigation | csv_business_import_ontology.json |
| ProductFamily | isRegisterContainers | Integer | csv_business_import_ontology.json |
| ProductFamily | parentSnRule | Navigation | csv_business_import_ontology.json |
| ProductFamily | propagateExposure | Boolean | csv_business_import_ontology.json |
| ProductFamily | serialNumberConfig | Integer | csv_business_import_ontology.json |
| ProductFamily | serialNumberGeneration | Integer | csv_business_import_ontology.json |
| ProductFamily | serialNumberQty | Integer | csv_business_import_ontology.json |
| ProductFamily | stdStartChildLevel | Navigation | csv_business_import_ontology.json |
| ProductFamily | stdStartChildQty | Float | csv_business_import_ontology.json |
| ProductFamily | stdStartChildQty2 | Float | csv_business_import_ontology.json |
| ProductFamily | stdStartCustomer | Navigation | csv_business_import_ontology.json |
| ProductFamily | stdStartFactory | Navigation | csv_business_import_ontology.json |
| ProductFamily | stdStartLevel | Navigation | csv_business_import_ontology.json |
| ProductFamily | stdStartOwner | Navigation | csv_business_import_ontology.json |
| ProductFamily | stdStartPriorityCode | Navigation | csv_business_import_ontology.json |
| ProductFamily | stdStartReason | Navigation | csv_business_import_ontology.json |
| ProductFamily | uniqueSerialNumbers | Boolean | csv_business_import_ontology.json |
| ProductFamily | useContainerNameForSn | Boolean | csv_business_import_ontology.json |
| ProductFamily | useProductionClientBoxMode | Boolean | csv_business_import_ontology.json |
| QtyHistory | isChargeToResource | Navigation | csv_business_import_ontology.json |
| ReprintLabelHistory | integrationTxn | Integer | csv_business_import_ontology.json |
| ResourceDef | cioChannelAdapter | Navigation | csv_business_import_ontology.json |
| ResourceDef | connectToOmlProducer | Boolean | csv_business_import_ontology.json |
| ResourceDef | defectMessageAction | Integer | csv_business_import_ontology.json |
| ResourceDef | distributor | String | csv_business_import_ontology.json |
| ResourceDef | doNotReuseContainerName | Boolean | csv_business_import_ontology.json |
| ResourceDef | enableMoveInRetry | Boolean | csv_business_import_ontology.json |
| ResourceDef | feederContainer | Navigation | csv_business_import_ontology.json |
| ResourceDef | feederPlan | Navigation | csv_business_import_ontology.json |
| ResourceDef | feederPlanBase | Integer | csv_business_import_ontology.json |
| ResourceDef | feederSlot | Navigation | csv_business_import_ontology.json |
| ResourceDef | idealCph | Integer | csv_business_import_ontology.json |
| ResourceDef | ignoreMoveInNotRequired | Boolean | csv_business_import_ontology.json |
| ResourceDef | isCapacity | Integer | csv_business_import_ontology.json |
| ResourceDef | isCarrierThruputRecordingMode | Integer | csv_business_import_ontology.json |
| ResourceDef | isContainerStatus | Integer | csv_business_import_ontology.json |
| ResourceDef | isDefectMapping | Navigation | csv_business_import_ontology.json |
| ResourceDef | isIncludeInOee | Boolean | csv_business_import_ontology.json |
| ResourceDef | isLineIdentifier | Boolean | csv_business_import_ontology.json |
| ResourceDef | isMfgOrder | Navigation | csv_business_import_ontology.json |
| ResourceDef | isMioAdapterName | String | csv_business_import_ontology.json |
| ResourceDef | isMioChannelSource | String | csv_business_import_ontology.json |
| ResourceDef | isMioChannelSrcServerName | String | csv_business_import_ontology.json |
| ResourceDef | isOeeSettings | Navigation | csv_business_import_ontology.json |
| ResourceDef | isProduct | Navigation | csv_business_import_ontology.json |
| ResourceDef | isRecipe | Navigation | csv_business_import_ontology.json |
| ResourceDef | isRecipeBase | Integer | csv_business_import_ontology.json |
| ResourceDef | isResource | Navigation | csv_business_import_ontology.json |
| ResourceDef | isReuseTrackingContainer | Boolean | csv_business_import_ontology.json |
| ResourceDef | isSingleMfgOrder | Integer | csv_business_import_ontology.json |
| ResourceDef | isSingleProduct | Integer | csv_business_import_ontology.json |
| ResourceDef | isSpec | Navigation | csv_business_import_ontology.json |
| ResourceDef | isUsePosition | Integer | csv_business_import_ontology.json |
| ResourceDef | isUsePositionState | Boolean | csv_business_import_ontology.json |
| ResourceDef | isValidateQueue | Boolean | csv_business_import_ontology.json |
| ResourceDef | mdmGuid | String | csv_business_import_ontology.json |
| ResourceDef | moveInErrorAction | Integer | csv_business_import_ontology.json |
| ResourceDef | moveInRetryAttempts | Integer | csv_business_import_ontology.json |
| ResourceDef | moveInRetryIntervalMs | Integer | csv_business_import_ontology.json |
| ResourceDef | numberOfLanes | Integer | csv_business_import_ontology.json |
| ResourceDef | panelConfiguration | Integer | csv_business_import_ontology.json |
| ResourceDef | resourceCategory | Navigation | csv_business_import_ontology.json |
| ResourceDef | resourceIndex | Integer | csv_business_import_ontology.json |
| ResourceDef | thruputFactor | Float | csv_business_import_ontology.json |
| ResourceDef | thruputFactor2 | Float | csv_business_import_ontology.json |
| ResourceDef | thruputFactorType | String | csv_business_import_ontology.json |
| ResourceDef | thruputFactorType2 | String | csv_business_import_ontology.json |
| ResourceDef | toolPlanDetail | Navigation | csv_business_import_ontology.json |
| ResourceDef | useProdStatusEvents | Boolean | csv_business_import_ontology.json |
| ResourceDef | useQualityEvents | Boolean | csv_business_import_ontology.json |
| ResourceDef | useTraceabilityEvents | Boolean | csv_business_import_ontology.json |
| ResourceFamily | isCarrierThruputRecordingMode | Integer | csv_business_import_ontology.json |
| ResourceFamily | isMfgOrder | Navigation | csv_business_import_ontology.json |
| ResourceFamily | isOeeSettings | Navigation | csv_business_import_ontology.json |
| ResourceFamily | isPrintQueue | Navigation | csv_business_import_ontology.json |
| ResourceFamily | isProduct | Navigation | csv_business_import_ontology.json |
| ResourceFamily | isReuseTrackingContainer | Boolean | csv_business_import_ontology.json |
| ResourceFamily | isSingleMfgOrder | Integer | csv_business_import_ontology.json |
| ResourceFamily | isSingleProduct | Integer | csv_business_import_ontology.json |
| ResourceFamily | isTrainingReqGroup | Navigation | csv_business_import_ontology.json |
| ResourceFamily | isUsePosition | Integer | csv_business_import_ontology.json |
| ResourceFamily | isVendor | Navigation | csv_business_import_ontology.json |
| ResourceFamily | isVendorModel | String | csv_business_import_ontology.json |
| ResourceFamily | isVendorSerialNumber | String | csv_business_import_ontology.json |
| ResourceGroup | isSmtResources | Boolean | csv_business_import_ontology.json |
| ResourceStatusCode | isOeeLossCategory | Integer | csv_business_import_ontology.json |
| ResourceStatusCode | isOrder | Integer | csv_business_import_ontology.json |
| ResourceStatusHistory | isOeeLossCategory | Integer | csv_business_import_ontology.json |
| ResourceStatusHistory | isOldOeeLossCategory | Integer | csv_business_import_ontology.json |
| ResourceStatusHistory | isRecipe | Navigation | csv_business_import_ontology.json |
| ResourceStatusHistory | mfgLine | Navigation | csv_business_import_ontology.json |
| ResourceStatusHistory | oldMfgLine | Navigation | csv_business_import_ontology.json |
| ResourceStatusHistory | updateParams | Boolean | csv_business_import_ontology.json |
| RouteStep | isDurationPerUnit | Float | csv_business_import_ontology.json |
| RouteStep | isRunRateOption | Integer | csv_business_import_ontology.json |
| RouteStep | isSetupTime | Float | csv_business_import_ontology.json |
| RouteStep | isSmtDate | DateTime | csv_business_import_ontology.json |
| RouteStep | isSmtSide | Integer | csv_business_import_ontology.json |
| RouteStep | isTimePerBatch | Float | csv_business_import_ontology.json |
| RouteStep | isTransferQty | Float | csv_business_import_ontology.json |
| RouteStep | isTransferType | Integer | csv_business_import_ontology.json |
| RouteStep | isUnitsPerHour | Float | csv_business_import_ontology.json |
| RouteStep | isUnscheduledTime | Float | csv_business_import_ontology.json |
| RouteStep | startVirtualSn | Boolean | csv_business_import_ontology.json |
| SPCChartVisualParams | isFrozen | Boolean | csv_business_import_ontology.json |
| ShopFloorSettings | defaultLogEntryTypeGroup | Navigation | csv_business_import_ontology.json |
| ShopFloorSettings | defaultLogNameExpression | String | csv_business_import_ontology.json |
| ShopFloorSettings | isDefectMapping | Navigation | csv_business_import_ontology.json |
| ShopFloorSettings | issueDifferenceReason | Navigation | csv_business_import_ontology.json |
| ShopFloorSettings | laserMarkerFail | Integer | csv_business_import_ontology.json |
| Spec | assignPhysicalAddress | Boolean | csv_business_import_ontology.json |
| Spec | autoClose | Boolean | csv_business_import_ontology.json |
| Spec | autoComponentIssue | Boolean | csv_business_import_ontology.json |
| Spec | autoDisassociate | Boolean | csv_business_import_ontology.json |
| Spec | autoInitiateProcessing | Boolean | csv_business_import_ontology.json |
| Spec | autoIssueToPanel | Boolean | csv_business_import_ontology.json |
| Spec | autoMove | Boolean | csv_business_import_ontology.json |
| Spec | autoOpenInstructions | Boolean | csv_business_import_ontology.json |
| Spec | autoParallel | Boolean | csv_business_import_ontology.json |
| Spec | autoSelectPinDefects | Boolean | csv_business_import_ontology.json |
| Spec | boardSide | Integer | csv_business_import_ontology.json |
| Spec | bypassResource | Boolean | csv_business_import_ontology.json |
| Spec | clearDefectsAction | Integer | csv_business_import_ontology.json |
| Spec | clearOpenDefects | Boolean | csv_business_import_ontology.json |
| Spec | closeParentContainers | Boolean | csv_business_import_ontology.json |
| Spec | computerGroup | Navigation | csv_business_import_ontology.json |
| Spec | containerAction | Integer | csv_business_import_ontology.json |
| Spec | defaultIssueDifferenceReason | Navigation | csv_business_import_ontology.json |
| Spec | defaultSubstitutionReason | Navigation | csv_business_import_ontology.json |
| Spec | disassociateBeforeMove | Boolean | csv_business_import_ontology.json |
| Spec | displayOptions | Navigation | csv_business_import_ontology.json |
| Spec | enableToolIssue | Boolean | csv_business_import_ontology.json |
| Spec | enforceComplete | Boolean | csv_business_import_ontology.json |
| Spec | excludeSuspendTime | Boolean | csv_business_import_ontology.json |
| Spec | firstArticleMode | Integer | csv_business_import_ontology.json |
| Spec | firstArticleTrackingMode | Integer | csv_business_import_ontology.json |
| Spec | guidedManualAssembly | Boolean | csv_business_import_ontology.json |
| Spec | hideNonOpenDefectsPrevSteps | Boolean | csv_business_import_ontology.json |
| Spec | isCarrierAutoMode | Integer | csv_business_import_ontology.json |
| Spec | isDisableEProcValidation | Boolean | csv_business_import_ontology.json |
| Spec | isLoadCarrier | Boolean | csv_business_import_ontology.json |
| Spec | isMaterialIssue | Boolean | csv_business_import_ontology.json |
| Spec | isMaterialReturn | Boolean | csv_business_import_ontology.json |
| Spec | isMaterialWithdraw | Boolean | csv_business_import_ontology.json |
| Spec | isRecordCarrierThruput | Boolean | csv_business_import_ontology.json |
| Spec | isRequiresResource | Boolean | csv_business_import_ontology.json |
| Spec | isUnloadCarrier | Boolean | csv_business_import_ontology.json |
| Spec | isValidateCarrierMaintenance | Boolean | csv_business_import_ontology.json |
| Spec | isVerifyRecipe | Boolean | csv_business_import_ontology.json |
| Spec | iterationLimit | Integer | csv_business_import_ontology.json |
| Spec | iterationLimitFailAction | Integer | csv_business_import_ontology.json |
| Spec | iterationLimitHoldReason | Navigation | csv_business_import_ontology.json |
| Spec | iterationLimitLossReason | Navigation | csv_business_import_ontology.json |
| Spec | iterationLimitsEnabled | Boolean | csv_business_import_ontology.json |
| Spec | keepContainerOnCarrier | Boolean | csv_business_import_ontology.json |
| Spec | mfgLine | Navigation | csv_business_import_ontology.json |
| Spec | mfgOrderReassignPlan | Navigation | csv_business_import_ontology.json |
| Spec | multiContainerDefectMatri | Navigation | csv_business_import_ontology.json |
| Spec | performMfgOrderReassignPc | Boolean | csv_business_import_ontology.json |
| Spec | productConversionRequirement | String | csv_business_import_ontology.json |
| Spec | recordTdaDetailsHistory | Boolean | csv_business_import_ontology.json |
| Spec | required | Boolean | csv_business_import_ontology.json |
| Spec | resetMaterialExposure | Boolean | csv_business_import_ontology.json |
| Spec | showMovePopup | Boolean | csv_business_import_ontology.json |
| Spec | side | String | csv_business_import_ontology.json |
| Spec | snEntryDefaultMode | Integer | csv_business_import_ontology.json |
| Spec | targetSpecs | Integer | csv_business_import_ontology.json |
| Spec | thruputRequirement | String | csv_business_import_ontology.json |
| Spec | useFirstItemScannedSn | Boolean | csv_business_import_ontology.json |
| Spec | useMaterialSetup | Boolean | csv_business_import_ontology.json |
| Spec | useProductionClientBoxMode | Boolean | csv_business_import_ontology.json |
| Spec | validateSamplingOverallResult | Boolean | csv_business_import_ontology.json |
| Spec | verifyExposureDuration | Boolean | csv_business_import_ontology.json |
| Spec | verifyMfgLine | Boolean | csv_business_import_ontology.json |
| Spec | verifyParallelCompletion | Boolean | csv_business_import_ontology.json |
| Spec | verifyPhysicalAddresses | Boolean | csv_business_import_ontology.json |
| Spec | verifyYieldLimits | Boolean | csv_business_import_ontology.json |
| Spec | workflowDocLocation | Integer | csv_business_import_ontology.json |
| Terminal | useContainerList | Integer | csv_business_import_ontology.json |
| ThruputHistory | isFailed | Boolean | csv_business_import_ontology.json |
| ThruputHistory | isFailedQty | Float | csv_business_import_ontology.json |
| TrainingRecord | setupAccess | Navigation | csv_business_import_ontology.json |
| TrainingRecord | warningEmailDate | DateTime | csv_business_import_ontology.json |
| TrainingRequirement | warningEmailGroup | Navigation | csv_business_import_ontology.json |
| TrainingRequirement | warningPeriod | Float | csv_business_import_ontology.json |
| Workflow | isTrackQty | Boolean | csv_business_import_ontology.json |
| Workflow | isTrackQty2 | Boolean | csv_business_import_ontology.json |
| WorkflowStep | isRouteStepName | String | csv_business_import_ontology.json |
| WorkflowStep | isSchdRouteStepName | String | csv_business_import_ontology.json |

## Missing Relationships for Physical Foreign Keys

_None._

## Module-Level Warning Counts

| Ontology File(s) | Missing Properties | Type Mismatches | Ontology-only Properties | Missing Relationships |
|---|---|---|---|---|
| billofprocess_ontology.json, csv_business_import_ontology.json | 0 | 0 | 1 | 0 |
| container_ontology.json, csv_business_import_ontology.json | 0 | 0 | 47 | 0 |
| cross_module_ontology.json, csv_business_import_ontology.json | 0 | 0 | 5 | 0 |
| csv_business_import_ontology.json, datacollection_ontology.json | 0 | 0 | 7 | 0 |
| csv_business_import_ontology.json, document_ontology.json | 0 | 0 | 3 | 0 |
| csv_business_import_ontology.json, employee_ontology.json | 0 | 0 | 9 | 0 |
| csv_business_import_ontology.json, erp_route_ontology.json | 0 | 0 | 11 | 0 |
| csv_business_import_ontology.json, factory_ontology.json | 0 | 0 | 37 | 0 |
| csv_business_import_ontology.json, history_ontology.json | 0 | 0 | 17 | 0 |
| csv_business_import_ontology.json, mfgcalendar_ontology.json | 0 | 0 | 1 | 0 |
| csv_business_import_ontology.json, mfgorder_ontology.json | 0 | 0 | 42 | 0 |
| csv_business_import_ontology.json, operation_ontology.json | 0 | 0 | 7 | 0 |
| csv_business_import_ontology.json, physical_bridge_ontology.json | 0 | 0 | 13 | 0 |
| csv_business_import_ontology.json, product_family_ontology.json | 0 | 0 | 23 | 0 |
| csv_business_import_ontology.json, product_ontology.json | 0 | 0 | 66 | 0 |
| csv_business_import_ontology.json, quality_ontology.json | 0 | 0 | 2 | 0 |
| csv_business_import_ontology.json, resource_family_ontology.json | 0 | 0 | 13 | 0 |
| csv_business_import_ontology.json, resource_group_ontology.json | 0 | 0 | 1 | 0 |
| csv_business_import_ontology.json, resource_status_code_ontology.json | 0 | 0 | 2 | 0 |
| csv_business_import_ontology.json, semiconductor_action_approval_esign_ontology.json | 0 | 0 | 3 | 0 |
| csv_business_import_ontology.json, semiconductor_shared_support_ontology.json | 0 | 0 | 68 | 0 |
| csv_business_import_ontology.json, semiconductor_spc_yield_ontology.json | 0 | 0 | 4 | 0 |
| csv_business_import_ontology.json, spc_chart_visual_params_ontology.json | 0 | 0 | 1 | 0 |
| csv_business_import_ontology.json, spec_ontology.json | 0 | 0 | 68 | 0 |
| csv_business_import_ontology.json, sql_core_transaction_history_ontology.json | 0 | 0 | 14 | 0 |
| csv_business_import_ontology.json, terminal_ontology.json | 0 | 0 | 1 | 0 |
| csv_business_import_ontology.json, training_plan_ontology.json | 0 | 0 | 4 | 0 |
| csv_business_import_ontology.json, workflow_ontology.json | 0 | 0 | 5 | 0 |

## Parse Errors

_None._
