import pandas as pd
from src.etl.config.db_config import get_src_engine

engine = get_src_engine()

queries = {
    "Factory": "SELECT FactoryName AS name, Description AS description FROM Factory",
    "Product": "SELECT b.ProductName AS name, r.ProductRevision AS revision, r.Description AS description FROM Product r JOIN ProductBase b ON r.ProductBaseId = b.ProductBaseId",
    "WorkCenter": "SELECT WorkCenterName AS name, Description AS description FROM WorkCenter",
    "Workflow": "SELECT b.WorkflowName AS name, r.Revision AS revision FROM Workflow r JOIN WorkflowBase b ON r.WorkflowBaseId = b.WorkflowBaseId"
}

for name, sql in queries.items():
    try:
        df = pd.read_sql(f"SELECT TOP 1 * FROM ({sql}) as tmp", engine)
        print(f"SUCCESS {name}: Columns: {df.columns.tolist()}")
    except Exception as e:
        print(f"ERROR {name}: {str(e).splitlines()[0]}")
