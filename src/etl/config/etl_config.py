ONTOLOGY_ETL_MAP = {
    # ── 物理工厂层 ──
    "EnterpriseDef": {
        "type": "direct",
        "source_query": "SELECT EnterpriseName AS enterprise_id, EnterpriseName AS name, Description AS description, CAST(EnterpriseId AS VARCHAR) AS _source_id FROM Enterprise",
        "target_table": "ont_EnterpriseDef",
        "merge_key": "enterprise_id",
        "incremental": False
    },
    "SiteDef": {
        "type": "direct",
        "source_query": "SELECT SiteName AS site_id, SiteName AS name, Description AS description, CAST(SiteId AS VARCHAR) AS _source_id FROM Site",
        "target_table": "ont_SiteDef",
        "merge_key": "site_id",
        "incremental": False
    },
    "FactoryDef": {
        "type": "direct",
        "source_query": "SELECT FactoryName AS factory_id, FactoryName AS name, Description AS description, CAST(FactoryId AS VARCHAR) AS _source_id FROM Factory",
        "target_table": "ont_FactoryDef",
        "merge_key": "factory_id",
        "incremental": False
    },
    "WorkCenterDef": {
        "type": "direct",
        "source_query": "SELECT WorkCenterName AS workcenter_id, WorkCenterName AS name, Description AS description, CAST(WorkCenterId AS VARCHAR) AS _source_id FROM WorkCenter",
        "target_table": "ont_WorkCenterDef",
        "merge_key": "workcenter_id",
        "incremental": False
    },

    # ── 配置层 ──
    "OperationDef": {
        "type": "direct",
        "source_query": "SELECT Name AS operation_id, Name AS name, Description AS description, CAST(OperationId AS VARCHAR) AS _source_id FROM Operation",
        "target_table": "ont_OperationDef",
        "merge_key": "operation_id",
        "incremental": False
    },
    "ResourceDef": {
        "type": "direct",
        "source_query": "SELECT Name AS resource_id, Name AS name, Description AS description, CAST(ResourceId AS VARCHAR) AS _source_id FROM ResourceDef",
        "target_table": "ont_ResourceDef",
        "merge_key": "resource_id",
        "incremental": False
    },
    "ProductDef": {
        "type": "direct",
        "source_query": "SELECT b.ProductName AS product_id, b.ProductName AS name, r.ProductRevision AS revision, r.Description AS description, CAST(r.ProductId AS VARCHAR) AS _source_id FROM Product r JOIN ProductBase b ON r.ProductBaseId = b.ProductBaseId",
        "target_table": "ont_ProductDef",
        "merge_key": "product_id",
        "incremental": False
    },
    "ProductFamilyDef": {
        "type": "direct",
        "source_query": "SELECT ProductFamilyName AS family_id, ProductFamilyName AS name, Description AS description, CAST(ProductFamilyId AS VARCHAR) AS _source_id FROM ProductFamily",
        "target_table": "ont_ProductFamilyDef",
        "merge_key": "family_id",
        "incremental": False
    },
    "DataCollectionDef": {
        "type": "direct",
        "source_query": "SELECT Name AS dc_def_id, Name AS name, Revision AS revision, Description AS description, CAST(DataCollectionId AS VARCHAR) AS _source_id FROM DataCollectionDef",
        "target_table": "ont_DataCollectionDef",
        "merge_key": "dc_def_id",
        "incremental": False
    },
    "ESpecDef": {
        "type": "direct",
        "source_query": "SELECT Name AS espec_id, Name AS name, Revision AS revision, Description AS description, CAST(ESpecId AS VARCHAR) AS _source_id FROM ESpecs",
        "target_table": "ont_ESpecDef",
        "merge_key": "espec_id",
        "incremental": False
    },
    "WorkflowDef": {
        "type": "direct",
        "source_query": """
            SELECT
                Name              AS workflow_id,
                Name              AS name,
                Revision          AS revision,
                EffectiveDate     AS effective_date,
                Description       AS description,
                CAST(WorkflowId AS VARCHAR) AS _source_id
            FROM Workflows
        """,
        "target_table": "ont_WorkflowDef",
        "merge_key":    "workflow_id",
        "incremental":  False
    },

    "StepDef": {
        "type": "direct",
        "source_query": """
            SELECT
                wf.Name + '::' + ws.Name     AS step_id,
                wf.Name                      AS workflow_id,
                ws.Name                      AS name,
                ws.StepSequence              AS sequence,
                op.Name                      AS operation_id,
                r.Name                       AS resource_id,
                CAST(ws.StepId AS VARCHAR)   AS _source_id
            FROM WorkflowSteps ws
            JOIN Workflows   wf ON ws.WorkflowId  = wf.WorkflowId
            JOIN Operations  op ON ws.OperationId = op.OperationId
            LEFT JOIN Resources r ON ws.ResourceId = r.ResourceId
        """,
        "target_table": "ont_StepDef",
        "merge_key":    "step_id",
        "incremental":  False
    },

    "MoveEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(HistoryId AS VARCHAR)   AS event_id,
                ContainerName                AS container_name,
                EventType                    AS move_type,
                WorkflowName + '::' + StepName AS step_id,
                ResourceName                 AS resource_id,
                ProductName                  AS product_id,
                EventTime                    AS event_ts,
                Qty                          AS qty,
                ShiftName                    AS shift_name
            FROM ContainerHistory
            WHERE EventType IN ('MoveIn', 'MoveOut')
            AND EventTime > :last_loaded
        """,
        "target_table":      "ont_MoveEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "event_ts",
        "watermark_key":     "move_event_watermark"
    },

    "MeasureEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(dc.HistoryId AS VARCHAR)     AS event_id,
                dc.ContainerName                  AS container_name,
                dc.ESpecName                      AS espec_id,
                dc.WorkflowName+'::'+dc.StepName  AS step_id,
                dc.DataValue                      AS data_value,
                CASE WHEN dc.DataValue BETWEEN es.LowLimit AND es.HighLimit
                     THEN 1 ELSE 0 END            AS in_spec,
                dc.CollectionTime                 AS measure_ts
            FROM DataCollectionHistory dc
            LEFT JOIN ESpecs es ON dc.ESpecName = es.Name
            WHERE dc.CollectionTime > :last_loaded
        """,
        "target_table":      "ont_MeasureEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "measure_ts",
        "watermark_key":     "measure_event_watermark"
    },

    "ChangeEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(AuditLogId AS VARCHAR)  AS event_id,
                ObjectName                   AS object_name,
                ObjectType                   AS object_type,
                ChangeType                   AS change_type,
                EventTime                    AS event_ts
            FROM AuditLog
            WHERE EventTime > :last_loaded
        """,
        "target_table":      "ont_ChangeEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "event_ts",
        "watermark_key":     "change_event_watermark"
    },

    "YieldRecord": {
        "type": "aggregation",
        "aggregation_fn": "compute_yield_records",
        "target_table":   "ont_YieldRecord",
        "merge_key":      "record_id"
    },

    "CycleTimeRecord": {
        "type": "aggregation",
        "aggregation_fn": "compute_cycletime_records",
        "target_table":   "ont_CycleTimeRecord",
        "merge_key":      "record_id"
    },

    # ══════════════════════════════════════════════════════
    #  配置层 - 扩展模块
    # ══════════════════════════════════════════════════════
    "MaterialDef": {
        "type": "direct",
        "source_query": "SELECT Name AS material_id, Name AS name, Description AS description, CAST(MaterialId AS VARCHAR) AS _source_id FROM Material",
        "target_table": "ont_MaterialDef",
        "merge_key": "material_id",
        "incremental": False
    },
    "EmployeeDef": {
        "type": "direct",
        "source_query": "SELECT EmployeeName AS employee_id, EmployeeName AS name, Description AS description, CAST(EmployeeId AS VARCHAR) AS _source_id FROM Employee",
        "target_table": "ont_EmployeeDef",
        "merge_key": "employee_id",
        "incremental": False
    },
    "ContainerDef": {
        "type": "direct",
        "source_query": "SELECT ContainerName AS container_id, ContainerName AS name, ProductName AS product_id, Status AS status, Qty AS qty, CAST(ContainerId AS VARCHAR) AS _source_id FROM Container",
        "target_table": "ont_ContainerDef",
        "merge_key": "container_id",
        "incremental": False
    },
    "OrderDef": {
        "type": "direct",
        "source_query": "SELECT MfgOrderName AS order_id, MfgOrderName AS name, ProductName AS product_id, OrderQty AS order_qty, Status AS status, CAST(MfgOrderId AS VARCHAR) AS _source_id FROM MfgOrder",
        "target_table": "ont_OrderDef",
        "merge_key": "order_id",
        "incremental": False
    },
    "MaintenanceDef": {
        "type": "direct",
        "source_query": "SELECT MaintenanceName AS maint_id, MaintenanceName AS name, Description AS description, CAST(MaintenanceId AS VARCHAR) AS _source_id FROM MaintenanceDef",
        "target_table": "ont_MaintenanceDef",
        "merge_key": "maint_id",
        "incremental": False
    },
    "SamplingDef": {
        "type": "direct",
        "source_query": "SELECT Name AS sampling_id, Name AS name, SampleSize AS sample_size, Description AS description, CAST(SamplingId AS VARCHAR) AS _source_id FROM SamplingDef",
        "target_table": "ont_SamplingDef",
        "merge_key": "sampling_id",
        "incremental": False
    },
    "DocumentDef": {
        "type": "direct",
        "source_query": "SELECT DocumentName AS document_id, DocumentName AS name, DocumentType AS doc_type, Description AS description, CAST(DocumentId AS VARCHAR) AS _source_id FROM Document",
        "target_table": "ont_DocumentDef",
        "merge_key": "document_id",
        "incremental": False
    },
    "LabelDef": {
        "type": "direct",
        "source_query": "SELECT LabelName AS label_id, LabelName AS name, Description AS description, CAST(LabelId AS VARCHAR) AS _source_id FROM LabelDef",
        "target_table": "ont_LabelDef",
        "merge_key": "label_id",
        "incremental": False
    },
    "ToolingDef": {
        "type": "direct",
        "source_query": "SELECT ToolName AS tool_id, ToolName AS name, Description AS description, CAST(ToolId AS VARCHAR) AS _source_id FROM ToolDef",
        "target_table": "ont_ToolingDef",
        "merge_key": "tool_id",
        "incremental": False
    },
    "RecipeDef": {
        "type": "direct",
        "source_query": "SELECT RecipeName AS recipe_id, RecipeName AS name, Description AS description, CAST(RecipeId AS VARCHAR) AS _source_id FROM RecipeDef",
        "target_table": "ont_RecipeDef",
        "merge_key": "recipe_id",
        "incremental": False
    },
    "InventoryDef": {
        "type": "direct",
        "source_query": "SELECT LocationName AS location_id, LocationName AS name, Description AS description, CAST(LocationId AS VARCHAR) AS _source_id FROM StorageLocation",
        "target_table": "ont_InventoryDef",
        "merge_key": "location_id",
        "incremental": False
    },
    "SetupDef": {
        "type": "direct",
        "source_query": "SELECT SetupName AS setup_id, SetupName AS name, Description AS description, CAST(SetupId AS VARCHAR) AS _source_id FROM SetupDef",
        "target_table": "ont_SetupDef",
        "merge_key": "setup_id",
        "incremental": False
    },
    "PackagingDef": {
        "type": "direct",
        "source_query": "SELECT PackName AS pack_id, PackName AS name, Description AS description, CAST(PackId AS VARCHAR) AS _source_id FROM PackagingDef",
        "target_table": "ont_PackagingDef",
        "merge_key": "pack_id",
        "incremental": False
    },
    "VendorDef": {
        "type": "direct",
        "source_query": "SELECT VendorName AS vendor_id, VendorName AS name, Description AS description, CAST(VendorId AS VARCHAR) AS _source_id FROM Vendor",
        "target_table": "ont_VendorDef",
        "merge_key": "vendor_id",
        "incremental": False
    },
    "ConsumableDef": {
        "type": "direct",
        "source_query": "SELECT Name AS consumable_id, Name AS name, UOM AS uom, Description AS description, CAST(ConsumableId AS VARCHAR) AS _source_id FROM ConsumableDef",
        "target_table": "ont_ConsumableDef",
        "merge_key": "consumable_id",
        "incremental": False
    },

    # ══════════════════════════════════════════════════════
    #  事件层 - 扩展模块
    # ══════════════════════════════════════════════════════
    "QualityEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(NCRId AS VARCHAR)  AS event_id,
                ContainerName           AS container_name,
                DefectCode              AS defect_code,
                Disposition             AS disposition,
                EventTime               AS event_ts
            FROM NonConformanceReport
            WHERE EventTime > :last_loaded
        """,
        "target_table":      "ont_QualityEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "event_ts",
        "watermark_key":     "quality_event_watermark"
    },
    "AlarmEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(AlarmLogId AS VARCHAR) AS event_id,
                ResourceName               AS resource_id,
                AlarmCode                  AS alarm_code,
                Severity                   AS severity,
                OccurredAt                 AS event_ts
            FROM AlarmLog
            WHERE OccurredAt > :last_loaded
        """,
        "target_table":      "ont_AlarmEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "event_ts",
        "watermark_key":     "alarm_event_watermark"
    },
    "ScrapEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(ScrapLogId AS VARCHAR) AS event_id,
                ContainerName              AS container_name,
                ReasonCode                 AS reason_code,
                ScrapQty                   AS scrap_qty,
                ScrapDate                  AS event_ts
            FROM ScrapLog
            WHERE ScrapDate > :last_loaded
        """,
        "target_table":      "ont_ScrapEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "event_ts",
        "watermark_key":     "scrap_event_watermark"
    },
    "EqpStateEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(StateLogId AS VARCHAR) AS event_id,
                ResourceName               AS resource_id,
                StateName                  AS state_name,
                ReasonCode                 AS reason_code,
                StartTime                  AS event_ts,
                DurationSec                AS duration_sec
            FROM EqpStateLog
            WHERE StartTime > :last_loaded
        """,
        "target_table":      "ont_EqpStateEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "event_ts",
        "watermark_key":     "eqpstate_event_watermark"
    },
    "ShipmentEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(ShipmentId AS VARCHAR) AS event_id,
                ShipmentName               AS shipment_name,
                OrderId                    AS order_id,
                VehiclePlate               AS vehicle,
                ShipDate                   AS event_ts
            FROM ShipmentLog
            WHERE ShipDate > :last_loaded
        """,
        "target_table":      "ont_ShipmentEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "event_ts",
        "watermark_key":     "shipment_event_watermark"
    },
    "RMAEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(RMAId AS VARCHAR)  AS event_id,
                RMANumber              AS rma_number,
                ContainerName          AS container_name,
                ComplaintReason        AS complaint_reason,
                ReceiveDate            AS event_ts
            FROM RMALog
            WHERE ReceiveDate > :last_loaded
        """,
        "target_table":      "ont_RMAEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "event_ts",
        "watermark_key":     "rma_event_watermark"
    },
    "EnvironmentEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(LogId AS VARCHAR) AS event_id,
                SensorId              AS sensor_id,
                MeasureValue          AS value,
                Timestamp             AS event_ts
            FROM EnvironmentLog
            WHERE Timestamp > :last_loaded
        """,
        "target_table":      "ont_EnvironmentEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "event_ts",
        "watermark_key":     "environment_event_watermark"
    },
    "SignatureEvent": {
        "type": "direct",
        "source_query": """
            SELECT
                CAST(SigLogId AS VARCHAR) AS event_id,
                EmployeeName             AS employee_id,
                TransactionName          AS txn_name,
                SignedAt                 AS event_ts
            FROM SignatureLog
            WHERE SignedAt > :last_loaded
        """,
        "target_table":      "ont_SignatureEvent",
        "merge_key":         "event_id",
        "incremental":       True,
        "incremental_field": "event_ts",
        "watermark_key":     "signature_event_watermark"
    }
}
