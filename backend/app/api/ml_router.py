from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd
from pathlib import Path

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.ml.train_xgboost import train_xgboost, save_trained_xgboost, list_versions
from backend.app.ml.model_registry import load_latest_model

router = APIRouter(prefix="/ml", tags=["ml"])

class XGBoostTrainRequest(BaseModel):
    dataset_id: int
    target_column: str
    feature_columns: list | None = None
    model_name: str
    hyperparams: dict | None = None

class PredictRequest(BaseModel):
    model_name: str
    input_data: dict

@router.post("/xgboost/train")
def train_xgb(req: XGBoostTrainRequest, db: Session = Depends(get_db)):
    # Load dataset using the same helper as in other routers
    from backend.app.api.router import load_dataset_dataframe
    from backend.app.models.all_models import Dataset
    dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    df = load_dataset_dataframe(dataset)

    model, metrics = train_xgboost(
        df=df,
        target_column=req.target_column,
        feature_columns=req.feature_columns,
        params=req.hyperparams,
    )
    # Persist model
    model_path = save_trained_xgboost(model, req.model_name, metadata={"dataset_id": req.dataset_id, "target": req.target_column})
    return {"status": "success", "model_path": str(model_path), "metrics": metrics}

@router.post("/predict")
def predict(req: PredictRequest):
    model = load_latest_model(req.model_name)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    # Assume input_data keys match model features
    input_df = pd.DataFrame([req.input_data])
    pred = model.predict(input_df)
    return {"prediction": pred.tolist()}

@router.get("/models/{model_name}/versions")
def get_versions(model_name: str):
    versions = list_versions(model_name)
    return {"model_name": model_name, "versions": versions}
