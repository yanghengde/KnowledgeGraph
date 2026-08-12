/*
  Camstar Oracle incremental readiness review.

  These statements are read-only.  Flashback retention and grants must be
  reviewed by the Oracle DBA before an SCN-based extractor is enabled.
*/

SELECT DBMS_FLASHBACK.GET_SYSTEM_CHANGE_NUMBER AS current_scn FROM dual;

SELECT name, value
FROM v$parameter
WHERE name IN ('undo_retention', 'undo_management', 'undo_tablespace');

SELECT owner, table_name, dependencies
FROM all_tables
WHERE owner = COALESCE(NULLIF(UPPER('&CAMSTAR_SCHEMA'), ''), USER)
ORDER BY table_name;

SELECT owner_name, table_name, flashback_archive_name, archive_table_name
FROM dba_flashback_archive_tables
WHERE owner_name = COALESCE(NULLIF(UPPER('&CAMSTAR_SCHEMA'), ''), USER)
ORDER BY table_name;

/* DBA review topics:
   - Grant only the catalog/flashback privileges required by the sync account.
   - Confirm UNDO_RETENTION covers the maximum outage and retry window.
   - Prefer ROWDEPENDENCIES for new high-volume tables when row-level ORA_ROWSCN is used.
   - Use Flashback Data Archive when retention must exceed the undo window.
   - Validate VERSIONS BETWEEN SCN access for every table selected as CDC.
*/
