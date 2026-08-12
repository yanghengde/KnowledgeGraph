import pandas as pd
from src.etl.config.db_config import get_src_engine

engine = get_src_engine()
queries = [
    "Enterprise", "Site", "Factory", "WorkCenter",
    "Workflow", "Operation", "Resource", "DataCollection", "ESpec", "AuditLog"
]

try:
    df = pd.read_sql("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'", engine)
    tables = df['TABLE_NAME'].tolist()
    
    print("Verifying base tables...")
    for q in queries:
        matches = [t for t in tables if t == q or t == q+'Base' or t == q+'Def']
        print(f"Match for '{q}': {matches}")
except Exception as e:
    print(f"Error: {e}")
