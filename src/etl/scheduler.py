import schedule
import time
import logging
from dotenv import load_dotenv
from etl.etl_engine import OntologyETLEngine
from etl.config.db_config import SRC_CONN_STR, TGT_CONN_STR

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

load_dotenv()

engine = OntologyETLEngine(src_conn_str=SRC_CONN_STR, tgt_conn_str=TGT_CONN_STR)

# 每小时增量同步事件数据
schedule.every().hour.do(engine.run_incremental)

# 每天凌晨2点全量刷新配置层
schedule.every().day.at("02:00").do(lambda: [
    engine.run_entity('WorkflowDef'),
    engine.run_entity('StepDef'),
    engine.run_entity('ESpecDef'),
    engine.run_entity('ResourceDef'),
])

# 每天凌晨3点计算指标层
schedule.every().day.at("03:00").do(lambda: [
    engine.run_entity('YieldRecord'),
    engine.run_entity('CycleTimeRecord'),
])

if __name__ == '__main__':
    logging.info("ETL Scheduler started...")
    while True:
        schedule.run_pending()
        time.sleep(60)
