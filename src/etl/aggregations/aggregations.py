import pandas as pd
from sqlalchemy import text

def compute_cycletime_records(src_engine) -> pd.DataFrame:
    """MoveIn-MoveOut 配对，计算步骤节拍"""
    df = pd.read_sql(text("""
        SELECT
            mo.ProductName,
            mo.WorkflowName + '::' + mo.StepName  AS step_id,
            mo.LineName,
            CAST(mo.EventTime AS DATE)             AS record_date,
            DATEDIFF(SECOND, mi.EventTime, mo.EventTime) AS cycle_sec
        FROM ContainerHistory mo
        JOIN ContainerHistory mi
            ON  mo.ContainerName = mi.ContainerName
            AND mo.StepName      = mi.StepName
            AND mi.EventType     = 'MoveIn'
        WHERE mo.EventType = 'MoveOut'
    """), src_engine)

    if df.empty:
        return pd.DataFrame()

    agg = df.groupby(['product_name', 'step_id', 'line_name', 'record_date']).agg(
        avg_cycle_sec=('cycle_sec', 'mean'),
        min_cycle_sec=('cycle_sec', 'min'),
        max_cycle_sec=('cycle_sec', 'max'),
        sample_count=('cycle_sec', 'count')
    ).reset_index()

    agg['record_id'] = (
        agg['record_date'].astype(str) + '::' +
        agg['step_id'] + '::' +
        agg['product_name']
    )
    return agg

def compute_yield_records(src_engine) -> pd.DataFrame:
    """良率聚合计算"""
    df = pd.read_sql(text("""
        SELECT
            ProductName, WorkflowName+'::'+StepName AS step_id,
            LineName, ShiftName,
            CAST(EventDate AS DATE) AS record_date,
            SUM(InputQty)  AS input_qty,
            SUM(OutputQty) AS output_qty,
            SUM(ScrapQty)  AS scrap_qty,
            SUM(NCMQty)    AS ncm_qty
        FROM YieldHistory
        GROUP BY ProductName, WorkflowName, StepName, LineName, ShiftName, EventDate
    """), src_engine)

    if df.empty:
        return pd.DataFrame()

    df['yield_rate'] = df['output_qty'] / df['input_qty'].replace(0, float('nan'))
    df['record_id'] = (
        df['record_date'].astype(str) + '::' +
        df['line_name'] + '::' +
        df['product_name'] + '::' +
        df['step_id']
    )
    return df
