import pandas as pd
from sqlalchemy import text
from src.etl.config.db_config import get_src_engine, get_tgt_engine

def extract_workflow(src_engine):
    query = """
    SELECT 
        CAST(w.WorkflowId AS VARCHAR(200)) AS workflow_id,
        CAST(w.WorkflowId AS VARCHAR(200)) AS _source_id,
        wb.WorkflowName AS name,
        w.WorkflowRevision AS revision,
        w.Description AS description,
        w.ECO AS engineeringchangeorder,
        NULL AS erproutename,
        NULL AS schedulingroutename,
        w.RemainingProcessTimeEnabled AS remainingprocesstimeflag
    FROM Workflow w
    JOIN WorkflowBase wb ON w.WorkflowBaseId = wb.WorkflowBaseId
    """
    return pd.read_sql(query, src_engine.connect())

def extract_workflow_step(src_engine):
    query = """
    SELECT
        CAST(ws.WorkflowStepId AS VARCHAR(200)) AS workflowstep_id,
        CAST(ws.WorkflowStepId AS VARCHAR(200)) AS _source_id,
        ws.WorkflowStepName AS stepname,
        CASE WHEN w.FirstStepId = ws.WorkflowStepId THEN 1 ELSE 0 END AS isfirststep,
        ws.IsLastStep AS islaststep,
        NULL AS optional,
        ws.Description AS description,
        ws.Notes AS notes,
        NULL AS specname,
        NULL AS subworkflowname,
        NULL AS routestep,
        ws.WIPMsgLabel AS wipmsglabel,
        ws.Sequence AS sequence,
        NULL AS schedulingroutestep,
        NULL AS standardbatchsize,
        NULL AS yield,
        NULL AS setuptime,
        NULL AS runrateoption,
        NULL AS durationperunit,
        NULL AS unitsperhour,
        NULL AS normalcycletime,
        NULL AS fastcycletime
    FROM WorkflowStep ws
    LEFT JOIN Workflow w ON ws.WorkflowId = w.WorkflowId
    """
    return pd.read_sql(query, src_engine.connect())

def extract_operation(src_engine):
    query = """
    SELECT 
        CAST(OperationId AS VARCHAR(200)) AS operation_id,
        CAST(OperationId AS VARCHAR(200)) AS _source_id,
        OperationName AS name,
        InTransit AS intransit,
        InventoryPoint AS inventorypoint,
        OutsideServicePoint AS outsideservicepoint,
        UseQueue AS usequeue,
        SummaryThruput AS summarythruput,
        RejectIncomingNCContainer AS rejectincomingnonconformingcontainer,
        NULL AS displayoptions,
        ES_NPIDocumentView AS npidocumentview
    FROM Operation
    """
    return pd.read_sql(query, src_engine.connect())

def extract_spec(src_engine):
    query = """
    SELECT 
        CAST(s.SpecId AS VARCHAR(200)) AS spec_id,
        CAST(s.SpecId AS VARCHAR(200)) AS _source_id,
        sb.SpecName AS name,
        NULL AS engineeringchangeorder,
        NULL AS allowreprocess,
        NULL AS expirationperiodunits,
        NULL AS expirationperiod,
        NULL AS alwaysoverrideexpirationdate,
        NULL AS manufacturingdatetransaction,
        NULL AS validateudi,
        NULL AS containerautoholdrequirementtransaction
    FROM Spec s
    JOIN SpecBase sb ON s.SpecBaseId = sb.SpecBaseId
    """
    return pd.read_sql(query, src_engine.connect())

def load_to_ontology_db(df, table_name, tgt_engine):
    if df.empty:
        print(f"No data to load for {table_name}")
        return
    
    # Truncate strings to fit NVARCHAR(200)
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].apply(lambda x: x[:199] if isinstance(x, str) else x)
        
    df = df.where(pd.notnull(df), None)
    columns = df.columns.tolist()
    
    with tgt_engine.connect() as conn:
        conn.execute(text(f"DELETE FROM {table_name}"))
        
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join([':' + c for c in columns])})"
        
        # Insert row by row to bypass pyodbc bulk insert driver bugs
        records = df.to_dict(orient='records')
        count = 0
        for record in records:
            conn.execute(text(insert_sql), record)
            count += 1
            
        conn.commit()
    print(f"Successfully loaded {count} rows into {table_name}.")

def run_etl():
    src_engine = get_src_engine()
    tgt_engine = get_tgt_engine()
    
    print("Extracting Workflow data from CamstarPRD...")
    df_workflow = extract_workflow(src_engine)
    print("Loading Workflow data to OntologyDB...")
    load_to_ontology_db(df_workflow, 'ont_Workflow', tgt_engine)
    
    print("\nExtracting WorkflowStep data from CamstarPRD...")
    df_step = extract_workflow_step(src_engine)
    print("Loading WorkflowStep data to OntologyDB...")
    load_to_ontology_db(df_step, 'ont_WorkflowStep', tgt_engine)
    
    print("\nExtracting Operation data from CamstarPRD...")
    df_operation = extract_operation(src_engine)
    print("Loading Operation data to OntologyDB...")
    load_to_ontology_db(df_operation, 'ont_Operation', tgt_engine)
    
    print("\nExtracting Spec data from CamstarPRD...")
    df_spec = extract_spec(src_engine)
    print("Loading Spec data to OntologyDB...")
    load_to_ontology_db(df_spec, 'ont_Spec', tgt_engine)
    
    print("\nETL Pipeline Completed!")

if __name__ == "__main__":
    run_etl()
