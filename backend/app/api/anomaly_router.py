from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import pandas as pd
from ..security.rbac import require_role
from ..anomaly.engine import detect_anomalies
from ..core.database import SessionLocal
from ..models.all_models import Dataset

router = APIRouter(prefix="/enterprise/anomalies", tags=["Anomaly Detection"])

class AnomalyRequest(BaseModel):
    dataset_id: str
    contamination: float = 0.05
    feature_columns: Optional[List[str]] = None

class AnomalyResponse(BaseModel):
    dataset_id: str
    total_anomalies: int
    anomalies: List[Dict[str, Any]]
    summary: Dict[str, Any]

@router.post("/detect", response_model=AnomalyResponse)
async def detect_dataset_anomalies(request: AnomalyRequest, role: str = Depends(require_role("analyst"))):
    db = SessionLocal()
    try:
        ds = db.query(Dataset).filter(Dataset.id == int(request.dataset_id)).first()
        if not ds:
            raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_id} not found")
        file_path = ds.processed_file_path or ds.raw_file_path
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=400, detail="Dataset file missing")
        ext = os.path.splitext(file_path)[1].lower()
        df = pd.read_csv(file_path, low_memory=False) if ext in [".csv", ".txt"] else pd.read_excel(file_path)
        
        result = detect_anomalies(df, feature_columns=request.feature_columns, contamination=request.contamination)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return AnomalyResponse(
            dataset_id=request.dataset_id,
            total_anomalies=result.get("anomalies_detected_count", 0),
            anomalies=result.get("top_anomalies", []),
            summary={
                "contamination": request.contamination,
                "analyzed_records": result.get("total_records_evaluated", len(df)),
                "features_used": result.get("features_used", [])
            }
        )
    finally:
        db.close()

