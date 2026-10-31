from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from ..security.rbac import require_role
from ..mlops.registry import get_model_versions, register_model_version
from ..mlops.drift_monitor import detect_drift

router = APIRouter(prefix="/enterprise/mlops", tags=["MLOps"])

class ModelVersionRequest(BaseModel):
    model_name: str
    version: int
    metadata: Dict[str, Any] = {}

class DriftCheckResponse(BaseModel):
    model_name: str
    version: int
    drift_detected: bool
    details: Dict[str, Any]

@router.post("/models/{model_name}/versions")
async def create_model_version(
    model_name: str,
    payload: ModelVersionRequest,
    role: str = Depends(require_role("ml_engineer")),
):
    if payload.version < 1 or payload.version > 7:
        raise HTTPException(status_code=400, detail="Version must be between 1 and 7")
    register_model_version(model_name, payload.version, payload.metadata)
    return {"status": "created", "model": model_name, "version": payload.version}

@router.get("/drift/{model_name}/{version}")
async def check_model_drift(
    model_name: str,
    version: int,
    role: str = Depends(require_role("ml_engineer")),
) -> DriftCheckResponse:
    drift, details = detect_drift(model_name, version)
    return DriftCheckResponse(
        model_name=model_name,
        version=version,
        drift_detected=drift,
        details=details,
    )

