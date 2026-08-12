/*
  Camstar SQL Server incremental readiness review.

  The active statements below are read-only.  The enablement templates at the
  bottom are comments on purpose: a DBA must review retention, SQL Agent,
  backup/recovery, licensing, and Camstar support constraints before execution.
*/

SELECT DB_NAME() AS database_name,
       snapshot_isolation_state_desc,
       is_read_committed_snapshot_on,
       is_cdc_enabled,
       CHANGE_TRACKING_CURRENT_VERSION() AS change_tracking_current_version
FROM sys.databases
WHERE name = DB_NAME();

SELECT s.name AS schema_name, t.name AS table_name,
       ct.begin_version, ct.cleanup_version, ct.min_valid_version,
       ct.is_track_columns_updated_on
FROM sys.change_tracking_tables ct
JOIN sys.tables t ON t.object_id = ct.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
ORDER BY s.name, t.name;

IF EXISTS (SELECT 1 FROM sys.databases WHERE name = DB_NAME() AND is_cdc_enabled = 1)
BEGIN
    SELECT s.name AS schema_name, t.name AS table_name,
           ct.capture_instance, ct.start_lsn
    FROM cdc.change_tables ct
    JOIN sys.tables t ON t.object_id = ct.source_object_id
    JOIN sys.schemas s ON s.schema_id = t.schema_id
    ORDER BY s.name, t.name;
END;

/* DBA-reviewed Change Tracking template:

ALTER DATABASE [CamstarPRD]
SET CHANGE_TRACKING = ON
(CHANGE_RETENTION = 7 DAYS, AUTO_CLEANUP = ON);

ALTER TABLE [CamstarPRD_SCHEMA].[HistoryMainline]
ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = OFF);

-- Consider snapshot isolation for a transactionally consistent initial baseline.
ALTER DATABASE [CamstarPRD] SET ALLOW_SNAPSHOT_ISOLATION ON;
*/

/* DBA-reviewed CDC template (requires SQL Server Agent for capture/cleanup jobs):

USE [CamstarPRD];
EXEC sys.sp_cdc_enable_db;
EXEC sys.sp_cdc_enable_table
    @source_schema = N'CamstarPRD_SCHEMA',
    @source_name = N'HistoryMainline',
    @role_name = N'graphsync_reader',
    @supports_net_changes = 0;
*/
