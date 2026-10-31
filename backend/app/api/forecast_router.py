from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from ..security.rbac import require_role
from ..forecasting.quantile_engine import forecast_quantiles

router = APIRouter(prefix="/enterprise/forecast", tags=["Forecast"])

class ForecastRequest(BaseModel):
    dataset_id: str
    horizon: int  # number of periods to predict
    quantiles: List[float] = [0.1, 0.5, 0.9]

class QuantileForecast(BaseModel):
    timestamp: str
    quantile: float
    value: float

class ForecastResponse(BaseModel):
    dataset_id: str
    horizon: int
    forecasts: List[QuantileForecast]

@router.post("/", response_model=ForecastResponse)
async def get_forecast(request: ForecastRequest, role: str = Depends(require_role("analyst"))):
    """Return quantile forecasts for a given dataset.
    The underlying `forecast_quantiles` returns a list of dicts
    ``{"timestamp": ..., "quantile": ..., "value": ...}``.
    """
    try:
        forecasts = forecast_quantiles(request.dataset_id, request.horizon, request.quantiles)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ForecastResponse(
        dataset_id=request.dataset_id,
        horizon=request.horizon,
        forecasts=forecasts,
    )

