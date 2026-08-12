import os
import pymssql
from dotenv import load_dotenv

load_dotenv()

def check_product_columns():
    host = os.getenv("SRC_DB_HOST")
    port = os.getenv("SRC_DB_PORT")
    user = os.getenv("SRC_DB_USER")
    password = os.getenv("SRC_DB_PASSWORD")
    database = os.getenv("SRC_DB_NAME")

    try:
        conn = pymssql.connect(server=host, port=port, user=user, password=password, database=database)
        cursor = conn.cursor(as_dict=True)
        
        # 查询 Product 表中包含 'BOM' 或 'Bill' 字样的列
        query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Product' 
            AND (COLUMN_NAME LIKE '%BOM%' OR COLUMN_NAME LIKE '%Bill%')
        """
        cursor.execute(query)
        results = cursor.fetchall()
        print(f"Product table columns related to BOM: {[r['COLUMN_NAME'] for r in results]}")
        
        # 顺便查一下是否有 BillOfMaterial 相关的表
        cursor.execute("SELECT name FROM sys.tables WHERE name LIKE '%BOM%' OR name LIKE '%BillOfMaterial%'")
        tables = cursor.fetchall()
        print(f"BOM related tables: {[t['name'] for t in tables]}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_product_columns()
