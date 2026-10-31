from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from ..security.rbac import require_role
from ..ml.shap_engine import explain_shap

router = APIRouter(prefix="/enterprise/shap", tags=["SHAP Explainability"])

class SHAPRequest(BaseModel):
    model_name: str
    dataset_id: str

class SHAPResponse(BaseModel):
    model_name: str
    dataset_id: str
    top_features: Dict[str, float]

@router.post("/explain", response_model=SHAPResponse)
async def explain(request: SHAPRequest, role: str = Depends(require_role("ml_engineer"))):
    try:
        explanation = explain_shap(request.model_name, request.dataset_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    # Assume explanation is dict of feature: importance
    return SHAPResponse(
        model_name=request.model_name,
        dataset_id=request.dataset_id,
        top_features=explanation,
    )

