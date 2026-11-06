from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import pandas as pd
from ..security.rbac import require_role
from ..segmentation.engine import run_rfm_segmentation
from ..core.database import SessionLocal
from ..models.all_models import Dataset

router = APIRouter(prefix="/enterprise/segments", tags=["Customer Segmentation"])

class SegmentRequest(BaseModel):
    dataset_id: str
    customer_id_col: str
    date_col: str
    monetary_col: str
    n_clusters: int = 4

class SegmentResponse(BaseModel):
    dataset_id: str
    n_clusters: int
    cluster_summary: List[Dict[str, Any]]
    insights: List[str]

@router.post("/cluster", response_model=SegmentResponse)
async def cluster_segments(request: SegmentRequest, role: str = Depends(require_role("analyst"))):
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
        
        result = run_rfm_segmentation(
            df,
            customer_id_col=request.customer_id_col,
            date_col=request.date_col,
            monetary_col=request.monetary_col,
            n_clusters=request.n_clusters
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return SegmentResponse(
            dataset_id=request.dataset_id,
            n_clusters=request.n_clusters,
            cluster_summary=result.get("segments", []),
            insights=[result.get("methodology", ""), result.get("disclaimer", "")]
        )
    finally:
        db.close()

