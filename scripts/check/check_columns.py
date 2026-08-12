import pandas as pd
from src.etl.config.db_config import get_src_engine

engine = get_src_engine()

try:
    df = pd.read_sql("SELECT TOP 1 * FROM Product", engine)
    print("Columns in Product:")
    print(df.columns.tolist())
except Exception as e:
    print(f"Error for Product: {e}")

try:
    df = pd.read_sql("SELECT TOP 1 * FROM Factory", engine)
    print("Columns in Factory:")
    print(df.columns.tolist())
except Exception as e:
    pass
