import pyodbc
import pandas as pd

CAMSTAR_TABLES = [
    'Workflows', 'WorkflowSteps', 'Operations',
    'Products', 'ProductFamilies', 'ProductRevisions',
    'Resources', 'ResourceGroups', 'ResourceCapabilities',
    'DataCollections', 'ESpecs',
    'ContainerHistory', 'DataCollectionHistory',
    'AuditLog', 'YieldHistory',
    'WorkCenters', 'Factories', 'Departments',
    'DispatchRules', 'Skills',
    'Enterprises', 'Sites', 'ManufacturingAreas',
    'ProductionLines', 'Calendars', 'ShiftPatterns'
]

def scan_table_schema(conn, table_name: str) -> pd.DataFrame:
    """扫描指定表的字段结构，作为本体属性的来源"""
    return pd.read_sql(f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
    """, conn)

def scan_foreign_keys(conn) -> pd.DataFrame:
    """扫描外键关系，辅助发现本体关系"""
    return pd.read_sql("""
        SELECT
            fk.name                         AS fk_name,
            tp.name                         AS parent_table,
            cp.name                         AS parent_column,
            tr.name                         AS referenced_table,
            cr.name                         AS referenced_column
        FROM sys.foreign_keys fk
        JOIN sys.tables        tp ON fk.parent_object_id      = tp.object_id
        JOIN sys.tables        tr ON fk.referenced_object_id  = tr.object_id
        JOIN sys.foreign_key_columns fkc ON fk.object_id     = fkc.constraint_object_id
        JOIN sys.columns       cp ON fkc.parent_column_id    = cp.column_id
                                  AND cp.object_id           = tp.object_id
        JOIN sys.columns       cr ON fkc.referenced_column_id = cr.column_id
                                  AND cr.object_id           = tr.object_id
        WHERE tp.name IN ({})
    """.format(','.join(f"'{t}'" for t in CAMSTAR_TABLES)), conn)

def export_schema_for_llm(conn) -> str:
    """生成给 LLM 的结构摘要，用于本体草稿生成"""
    output = []
    for table in CAMSTAR_TABLES:
        schema = scan_table_schema(conn, table)
        cols = ', '.join(schema['COLUMN_NAME'].tolist())
        output.append(f"Table: {table}\nColumns: {cols}\n")
    return '\n'.join(output)
