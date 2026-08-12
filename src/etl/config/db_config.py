import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# 加载 .env 文件
load_dotenv()

ODBC_DRIVER = os.getenv("DB_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")


def _connection_url(prefix: str) -> URL:
    """Build a safely escaped SQL Server URL for Windows or Linux."""
    return URL.create(
        "mssql+pyodbc",
        username=os.getenv(f"{prefix}_DB_USER"),
        password=os.getenv(f"{prefix}_DB_PASSWORD"),
        host=os.getenv(f"{prefix}_DB_HOST"),
        port=int(os.getenv(f"{prefix}_DB_PORT", "1433")),
        database=os.getenv(f"{prefix}_DB_NAME"),
        query={
            "driver": ODBC_DRIVER,
            "TrustServerCertificate": os.getenv(
                "DB_TRUST_SERVER_CERTIFICATE",
                "yes",
            ),
        },
    )


SRC_CONN_STR = _connection_url("SRC")
TGT_CONN_STR = _connection_url("TGT")

def get_src_engine():
    return create_engine(SRC_CONN_STR)

def get_tgt_engine():
    return create_engine(TGT_CONN_STR)
