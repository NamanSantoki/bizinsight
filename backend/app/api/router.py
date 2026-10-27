import os
import shutil
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.database import get_db, engine
from backend.app.core.config import settings
from backend.app.models.all_models import (
    Dataset, DataQualityReport, ModelRun, AnomalyRecord, CustomerSegmentRecord, AuditLog, User
)
from backend.app.schemas.schemas import (
    DatasetResponse, DataQualityReportResponse, CleaningRequest,
    ForecastRequest, AnomalyRequest, SegmentationRequest,
    AskDataRequest, AskDataResponse, AuditLogResponse
)
from backend.app.ingestion.service import inspect_and_read_file, sanitize_table_name
from backend.app.analytics.profiler import compute_dataset_profile
from backend.app.data_quality.engine import evaluate_data_quality
from backend.app.data_quality.cleaner import clean_dataset
from backend.app.analytics.kpi import compute_business_kpis
from backend.app.forecasting.engine import run_chronological_forecasting
from backend.app.anomaly.engine import detect_anomalies
from backend.app.segmentation.engine import run_rfm_segmentation
from backend.app.ai.ask_data import generate_sql_from_question, execute_safe_query, validate_sql_query
from backend.app.audit.service import log_audit_event

router = APIRouter()

# Helper to load dataset dataframe
def load_dataset_dataframe(dataset: Dataset) -> pd.DataFrame:
    file_path = dataset.processed_file_path or dataset.raw_file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset physical file not found on disk.")
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".csv", ".txt"]:
        return pd.read_csv(file_path, low_memory=False)
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported stored format.")

# 1. Dataset Upload & Ingestion
@router.post("/datasets/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.PROCESSED_DIR, exist_ok=True)

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Read and inspect
    df, meta = inspect_and_read_file(contents, file.filename)
    
    # Save raw file
    raw_path = os.path.join(settings.UPLOAD_DIR, f"{int(pd.Timestamp.now().timestamp())}_{file.filename}")
    with open(raw_path, "wb") as f:
        f.write(contents)

    # Sanitize storage table name
    table_name = sanitize_table_name(os.path.splitext(file.filename)[0])
    
    # Save to SQL database for dynamic querying
    try:
        # Replace spaces in columns for SQL compatibility
        sql_df = df.copy()
        sql_df.columns = [str(c).replace(" ", "_") for c in sql_df.columns]
        sql_df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    except Exception as e:
        print(f"Warning: Failed to persist table to SQL: {e}")

    # Create Dataset record
    dataset = Dataset(
        name=file.filename,
        description=description or f"Ingested {file.filename} with {meta['raw_rows']} records.",
        source_type=meta["extension"].lstrip("."),
        raw_file_path=raw_path,
        storage_table_name=table_name,
        row_count=meta["raw_rows"],
        column_count=meta["raw_columns"],
        schema_metadata=meta
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Automatically compute Data Quality Report
    dq_res = evaluate_data_quality(df)
    dq_report = DataQualityReport(
        dataset_id=dataset.id,
        quality_score=dq_res["quality_score"],
        formula_description=dq_res["formula_description"],
        summary=dq_res["summary"],
        column_issues=dq_res["column_issues"],
        passed=dq_res["passed"]
    )
    db.add(dq_report)
    db.commit()

    # Audit log
    log_audit_event(
        db=db,
        action="dataset_upload",
        resource_type="dataset",
        resource_id=str(dataset.id),
        details={"filename": file.filename, "rows": meta["raw_rows"], "quality_score": dq_res["quality_score"]}
    )

    return dataset

# 2. List Datasets
@router.get("/datasets", response_model=List[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.id.desc()).all()

# 3. Get Dataset Details & Profile
@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = load_dataset_dataframe(dataset)
    profile = compute_dataset_profile(df)
    
    return {
        "dataset": DatasetResponse.from_orm(dataset),
        "profile": profile,
        "sample_rows": df.head(10).to_dict(orient="records")
    }

# 4. Get Data Quality Report
@router.get("/datasets/{dataset_id}/quality", response_model=DataQualityReportResponse)
def get_quality_report(dataset_id: int, db: Session = Depends(get_db)):
    report = db.query(DataQualityReport).filter(DataQualityReport.dataset_id == dataset_id).order_by(DataQualityReport.id.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="Quality report not found for this dataset")
    return report

# 5. Clean Dataset
@router.post("/datasets/{dataset_id}/clean")
def run_cleaning(dataset_id: int, req: CleaningRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    raw_df = pd.read_csv(dataset.raw_file_path) if dataset.raw_file_path.endswith('.csv') else pd.read_excel(dataset.raw_file_path)
    
    cleaned_df, cleaning_logs = clean_dataset(
        raw_df,
        remove_duplicates=req.remove_duplicates,
        missing_strategy=req.missing_strategy,
        clean_column_names=req.clean_column_names,
        normalize_dates=req.normalize_dates,
        date_columns=req.date_columns,
        outlier_handling=req.outlier_handling,
        numeric_columns=req.numeric_columns
    )

    # Save cleaned file to processed folder
    processed_path = os.path.join(settings.PROCESSED_DIR, f"cleaned_{dataset.id}_{os.path.basename(dataset.raw_file_path)}.csv")
    cleaned_df.to_csv(processed_path, index=False)

    # Update storage table
    if dataset.storage_table_name:
        try:
            sql_df = cleaned_df.copy()
            sql_df.columns = [str(c).replace(" ", "_") for c in sql_df.columns]
            sql_df.to_sql(dataset.storage_table_name, con=engine, if_exists="replace", index=False)
        except Exception as e:
            print(f"Warning: Failed to update SQL table: {e}")

    # Re-evaluate quality after cleaning
    dq_res = evaluate_data_quality(cleaned_df)
    new_dq_report = DataQualityReport(
        dataset_id=dataset.id,
        quality_score=dq_res["quality_score"],
        formula_description=dq_res["formula_description"],
        summary=dq_res["summary"],
        column_issues=dq_res["column_issues"],
        passed=dq_res["passed"]
    )
    db.add(new_dq_report)

    # Update dataset metadata
    dataset.processed_file_path = processed_path
    dataset.row_count = len(cleaned_df)
    dataset.column_count = len(cleaned_df.columns)
    db.commit()

    # Log audit
    log_audit_event(
        db=db,
        action="data_cleaning",
        resource_type="dataset",
        resource_id=str(dataset.id),
        details={"transformations": cleaning_logs, "new_quality_score": dq_res["quality_score"]}
    )

    return {
        "status": "success",
        "cleaning_logs": cleaning_logs,
        "new_row_count": len(cleaned_df),
        "new_column_count": len(cleaned_df.columns),
        "new_quality_score": dq_res["quality_score"]
    }

# 6. Analytics & KPIs
@router.get("/datasets/{dataset_id}/analytics")
def get_analytics(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = load_dataset_dataframe(dataset)
    kpis = compute_business_kpis(df)
    return kpis

# 7. Forecasting
@router.post("/datasets/{dataset_id}/forecast")
def run_forecast(dataset_id: int, req: ForecastRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = load_dataset_dataframe(dataset)
    forecast_res = run_chronological_forecasting(
        df=df,
        date_col=req.date_column,
        target_col=req.target_column,
        forecast_horizon=req.forecast_horizon,
        frequency=req.frequency
    )

    if "error" in forecast_res:
        return {"status": "rejected", "message": forecast_res["error"]}

    # Store ModelRun in database
    model_run = ModelRun(
        dataset_id=dataset.id,
        model_type="forecasting",
        algorithm=forecast_res["best_model"],
        target_column=req.target_column,
        date_column=req.date_column,
        validation_strategy=forecast_res["validation_strategy"],
        metrics=forecast_res["selected_model_metrics"],
        predictions_payload=forecast_res["future_predictions"],
        notes=forecast_res["uncertainty_note"]
    )
    db.add(model_run)
    db.commit()

    log_audit_event(
        db=db,
        action="forecast_generation",
        resource_type="model_run",
        resource_id=str(model_run.id),
        details={"algorithm": forecast_res["best_model"], "mae": forecast_res["selected_model_metrics"]["mae"]}
    )

    return forecast_res

# 8. Anomaly Detection
@router.post("/datasets/{dataset_id}/anomalies")
def run_anomalies(dataset_id: int, req: AnomalyRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = load_dataset_dataframe(dataset)
    anom_res = detect_anomalies(
        df=df,
        feature_columns=req.feature_columns,
        date_column=req.date_column,
        contamination=req.contamination
    )

    if "error" in anom_res:
        return {"status": "rejected", "message": anom_res["error"]}

    log_audit_event(
        db=db,
        action="anomaly_detection",
        resource_type="dataset",
        resource_id=str(dataset.id),
        details={"anomalies_found": anom_res["anomalies_detected_count"]}
    )

    return anom_res

# 9. Customer Segmentation
@router.post("/datasets/{dataset_id}/segmentation")
def run_segmentation(dataset_id: int, req: SegmentationRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = load_dataset_dataframe(dataset)
    seg_res = run_rfm_segmentation(
        df=df,
        customer_id_col=req.customer_id_col,
        date_col=req.date_col,
        monetary_col=req.monetary_col,
        n_clusters=req.n_clusters
    )

    if "error" in seg_res:
        return {"status": "rejected", "message": seg_res["error"]}

    log_audit_event(
        db=db,
        action="customer_segmentation",
        resource_type="dataset",
        resource_id=str(dataset.id),
        details={"cluster_count": req.n_clusters}
    )

    return seg_res

# 10. Ask Your Data (NLP to Safe SQL)
@router.post("/ask-data", response_model=AskDataResponse)
def ask_your_data(req: AskDataRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    table_name = dataset.storage_table_name
    if not table_name:
        raise HTTPException(status_code=400, detail="Dataset is not indexed in queryable database.")

    # Get table columns and schema
    df = load_dataset_dataframe(dataset)
    columns = list(df.columns)
    column_types = {str(c): str(df[c].dtype) for c in df.columns}

    start_time = pd.Timestamp.now()
    generated_sql = generate_sql_from_question(req.question, table_name, columns, column_types)
    
    results, err = execute_safe_query(db, generated_sql, table_name)
    exec_time = (pd.Timestamp.now() - start_time).total_seconds() * 1000

    if err:
        return AskDataResponse(
            question=req.question,
            sql_query=generated_sql,
            results=None,
            row_count=0,
            answer=f"The question could not be answered safely: {err}",
            sources_used=[table_name],
            confidence_explanation="Execution was blocked by security validator or SQL syntax error.",
            execution_time_ms=exec_time
        )

    # Grounded answer generation strictly from query result rows
    if not results or len(results) == 0:
        answer = "The available dataset contains no matching records for this query."
    else:
        # Formulate grounded, verified answer
        first_row = results[0]
        row_keys = list(first_row.keys())
        if len(results) == 1 and len(row_keys) == 1:
            answer = f"The resulting {row_keys[0]} is {first_row[row_keys[0]]:,}."
        elif len(results) <= 5:
            lines = [f"- {', '.join([f'{k}: {v}' for k, v in r.items()])}" for r in results]
            answer = f"Found {len(results)} matching records:\n" + "\n".join(lines)
        else:
            answer = f"Returned {len(results)} records based on the executed query. Top record: {first_row}."

    # Audit log the AI natural language query
    log_audit_event(
        db=db,
        action="ask_data_query",
        resource_type="dataset",
        resource_id=str(dataset.id),
        details={"question": req.question, "sql": generated_sql, "rows_returned": len(results) if results else 0}
    )

    return AskDataResponse(
        question=req.question,
        sql_query=generated_sql,
        results=results,
        row_count=len(results) if results else 0,
        answer=answer,
        sources_used=[table_name],
        confidence_explanation="Deterministic SQL query strictly grounded in database schema and verified results.",
        execution_time_ms=exec_time
    )

# 11. Audit Logs
@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
