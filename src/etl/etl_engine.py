import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class OntologyETLEngine:
    def __init__(self, src_conn_str: str, tgt_conn_str: str):
        self.src = create_engine(src_conn_str)
        self.tgt = create_engine(tgt_conn_str)

    def get_watermark(self, key: str) -> datetime:
        """读取增量水位线"""
        try:
            with self.tgt.connect() as conn:
                result = conn.execute(text(
                    "SELECT watermark FROM etl_watermarks WHERE entity_key = :key"
                ), {"key": key}).fetchone()
                return result[0] if result else datetime(2020, 1, 1)
        except Exception:
            return datetime(2020, 1, 1)

    def set_watermark(self, key: str, ts: datetime):
        """更新增量水位线"""
        try:
            with self.tgt.connect() as conn:
                conn.execute(text("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='etl_watermarks' and xtype='U')
                    CREATE TABLE etl_watermarks (entity_key VARCHAR(255) PRIMARY KEY, watermark DATETIME)
                    
                    MERGE etl_watermarks AS target
                    USING (SELECT :key AS entity_key, :ts AS watermark) AS src
                    ON target.entity_key = src.entity_key
                    WHEN MATCHED THEN UPDATE SET watermark = src.watermark
                    WHEN NOT MATCHED THEN INSERT (entity_key, watermark)
                        VALUES (src.entity_key, src.watermark);
                """), {"key": key, "ts": ts})
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to set watermark for {key}: {e}")

    def upsert(self, df: pd.DataFrame, table: str, merge_key: str):
        """MERGE 方式写入目标库"""
        if df.empty:
            return
        tmp_table = f"#tmp_{table}"
        df.to_sql(tmp_table, self.tgt, if_exists='replace', index=False)

        cols = ', '.join(df.columns)
        update_cols = ', '.join(
            f"t.{c} = s.{c}" for c in df.columns if c != merge_key
        )
        with self.tgt.connect() as conn:
            conn.execute(text(f"""
                MERGE {table} AS t
                USING {tmp_table} AS s ON t.{merge_key} = s.{merge_key}
                WHEN MATCHED THEN UPDATE SET {update_cols}
                WHEN NOT MATCHED THEN INSERT ({cols}) VALUES ({cols});
            """))
            conn.commit()

    def run_entity(self, entity_name: str):
        """执行单个本体类的 ETL"""
        from etl.config.etl_config import ONTOLOGY_ETL_MAP
        cfg = ONTOLOGY_ETL_MAP[entity_name]
        logger.info(f"Running ETL for: {entity_name}")

        if cfg['type'] == 'direct':
            params = {}
            if cfg.get('incremental'):
                watermark = self.get_watermark(cfg['watermark_key'])
                params['last_loaded'] = watermark

            df = pd.DataFrame()
            try:
                df = pd.read_sql(text(cfg['source_query']), self.src, params=params)
                self.upsert(df, cfg['target_table'], cfg['merge_key'])

                if cfg.get('incremental') and not df.empty:
                    new_watermark = df[cfg['incremental_field']].max()
                    self.set_watermark(cfg['watermark_key'], new_watermark)
            except Exception as e:
                logger.warning(f"  → Skipping {entity_name}: Source table/view might not exist yet. Error: {str(e).splitlines()[0]}")

        elif cfg['type'] == 'aggregation':
            from etl.aggregations.aggregations import compute_yield_records, compute_cycletime_records
            fn = {'compute_yield_records': compute_yield_records,
                  'compute_cycletime_records': compute_cycletime_records}[cfg['aggregation_fn']]
            
            df = pd.DataFrame()
            try:
                df = fn(self.src)
                self.upsert(df, cfg['target_table'], cfg['merge_key'])
            except Exception as e:
                logger.warning(f"  → Skipping {entity_name} (Aggregation): Source table/view might not exist yet. Error: {str(e).splitlines()[0]}")

        logger.info(f"  → Loaded {len(df) if not df.empty else 0} rows")

    def run_full_load(self):
        """全量初始化（顺序按依赖关系）"""
        ordered = [
            # 物理工厂层
            'EnterpriseDef', 'SiteDef', 'FactoryDef', 'WorkCenterDef',
            # 配置层（先父后子）
            'WorkflowDef', 'OperationDef', 'ResourceDef',
            'ProductDef', 'ProductFamilyDef', 'DataCollectionDef', 'ESpecDef', 'StepDef',
            # 配置层 - 扩展
            'MaterialDef', 'EmployeeDef', 'ContainerDef', 'OrderDef',
            'MaintenanceDef', 'SamplingDef', 'DocumentDef', 'LabelDef',
            'ToolingDef', 'RecipeDef', 'InventoryDef', 'SetupDef',
            'PackagingDef', 'VendorDef', 'ConsumableDef',
            # 事件层
            'MoveEvent', 'MeasureEvent', 'ChangeEvent',
            'QualityEvent', 'AlarmEvent', 'ScrapEvent',
            'EqpStateEvent', 'ShipmentEvent', 'RMAEvent',
            'EnvironmentEvent', 'SignatureEvent',
            # 指标层
            'YieldRecord', 'CycleTimeRecord'
        ]
        for entity in ordered:
            self.run_entity(entity)

    def run_incremental(self):
        """增量同步（每小时/每天触发）"""
        incremental_entities = [
            'MoveEvent', 'MeasureEvent', 'ChangeEvent',
            'QualityEvent', 'AlarmEvent', 'ScrapEvent',
            'EqpStateEvent', 'ShipmentEvent', 'RMAEvent',
            'EnvironmentEvent', 'SignatureEvent',
            'YieldRecord', 'CycleTimeRecord'
        ]
        for entity in incremental_entities:
            self.run_entity(entity)
