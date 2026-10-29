"""Data source integration router.
Provides endpoints to pull real public datasets (e.g. Kaggle/GitHub) directly into the platform.
"""
import os
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.app.core.database import get_db, engine
from backend.app.models.all_models import Dataset, DataQualityReport
from backend.app.ingestion.service import inspect_and_read_file
from backend.app.data_quality.engine import evaluate_data_quality
from backend.app.audit.service import log_audit_event
from backend.app.security.auth import get_current_active_user
from backend.scripts.fetch_sample_dataset import fetch_sample_dataset

router = APIRouter(prefix="/data-source", tags=["Data Source Integration"])

PUBLIC_SOURCES = {
    "temperatures": {
        "name": "daily_min_temperatures.csv",
        "url": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/daily-min-temperatures.csv",
        "description": "Daily Minimum Temperatures in Melbourne (10-year time series)"
    },
    "air_passengers": {
        "name": "international_airline_passengers.csv",
        "url": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv",
        "description": "Monthly totals of international airline passengers, 1949 to 1960"
    }
}

@router.get("/available-sources")
def list_available_sources():
    """List available public datasets that can be auto-fetched."""
    return [
        {"key": k, "name": v["name"], "description": v["description"], "url": v["url"]}
        for k, v in PUBLIC_SOURCES.items()
    ]

@router.post("/fetch-sample", summary="Download a sample public CSV and register it as an active dataset")
async def fetch_sample_dataset_endpoint(
    source_key: str = Query(default="temperatures"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Download a verified public CSV and ingest it with full quality profiling and SQL table creation."""
    try:
        source_info = PUBLIC_SOURCES.get(source_key, PUBLIC_SOURCES["temperatures"])
        csv_path = fetch_sample_dataset(url=source_info["url"], filename=source_info["name"])
        
        with open(csv_path, "rb") as f:
            file_bytes = f.read()
            
        df, metadata = inspect_and_read_file(file_bytes, os.path.basename(csv_path))
        
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', metadata['filename'].lower().replace('.csv', ''))
        table_name = f"tbl_{clean_name}_{int(os.path.getmtime(csv_path))}"
        
        try:
            df.to_sql(table_name, engine, if_exists="replace", index=False)
        except Exception as e:
            print(f"Warning: Failed to persist sample table to SQL: {e}")
            table_name = None

        new_ds = Dataset(
            name=metadata["filename"],
            description=source_info.get("description", f"Auto-fetched from {source_info['url']}"),
            source_type="public_stream",
            raw_file_path=str(csv_path),
            storage_table_name=table_name,
            row_count=metadata["raw_rows"],
            column_count=metadata["raw_columns"],
            schema_metadata=metadata,
        )
        db.add(new_ds)
        db.commit()
        db.refresh(new_ds)

        # Compute initial data quality report
        dq_res = evaluate_data_quality(df)
        dq_report = DataQualityReport(
            dataset_id=new_ds.id,
            quality_score=dq_res["quality_score"],
            formula_description=dq_res["formula_description"],
            summary=dq_res["summary"],
            column_issues=dq_res["column_issues"],
            passed=dq_res["passed"]
        )
        db.add(dq_report)
        db.commit()

        # Audit log entry
        log_audit_event(
            db=db,
            action="dataset_fetch_public",
            resource_type="dataset",
            resource_id=str(new_ds.id),
            user_id=getattr(current_user, "id", None) if current_user else None,
            details={"source": source_key, "filename": metadata["filename"], "rows": metadata["raw_rows"]}
        )

        return {
            "status": "success",
            "dataset_id": new_ds.id,
            "name": new_ds.name,
            "row_count": new_ds.row_count,
            "column_count": new_ds.column_count
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

