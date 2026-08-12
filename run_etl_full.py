import logging
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from src.etl.etl_engine import OntologyETLEngine
from src.etl.config.db_config import SRC_CONN_STR, TGT_CONN_STR
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    load_dotenv()
    
    logger = logging.getLogger("ETLRunner")
    logger.info("Initializing Ontology ETL Engine...")
    
    try:
        engine = OntologyETLEngine(src_conn_str=SRC_CONN_STR, tgt_conn_str=TGT_CONN_STR)
        logger.info("Starting FULL LOAD ETL process to SQL Server Ontology DB...")
        engine.run_full_load()
        logger.info("ETL Full Load completed successfully!")
    except Exception as e:
        logger.error(f"ETL failed: {e}")
        import traceback
        traceback.print_exc()
