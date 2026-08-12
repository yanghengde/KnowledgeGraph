import pandas as pd
from src.etl.config.db_config import get_src_engine

engine = get_src_engine()

try:
    df = pd.read_sql("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME LIKE '%Product%' OR TABLE_NAME LIKE '%Factor%'", engine)
    print("Views:")
    for t in df['TABLE_NAME']:
        print(" - " + t)
except Exception as e:
    print(f"Error: {e}")
