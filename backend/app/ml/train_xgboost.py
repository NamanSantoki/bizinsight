import pandas as pd
from typing import List, Optional, Tuple, Dict
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .model_registry import save_model, load_latest_model, list_model_versions

def train_xgboost(
    df: pd.DataFrame,
    target_column: str,
    feature_columns: Optional[List[str]] = None,
    params: Optional[Dict] = None,
) -> Tuple[XGBRegressor, Dict]:
    """Train an XGBoost regressor on the supplied DataFrame.

    Args:
        df: Input DataFrame containing features and target.
        target_column: Column name of the prediction target.
        feature_columns: List of feature column names; if ``None`` all columns except ``target_column`` are used.
        params: Optional XGBoost hyper‑parameters dictionary.

    Returns:
        A tuple of the trained ``XGBRegressor`` model and a dictionary of evaluation metrics (MAE, MSE, R2).
    """
    if feature_columns is None:
        numeric_cols = [c for c in df.select_dtypes(include=['number']).columns if c != target_column]
        feature_columns = numeric_cols if numeric_cols else [c for c in df.columns if c != target_column]
    
    X = df[feature_columns].apply(pd.to_numeric, errors='coerce').fillna(0)
    y = pd.to_numeric(df[target_column], errors='coerce').fillna(0)

    # Simple train/validation split (80/20)
    split_idx = int(0.8 * len(df))
    X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

    model_params = params or {"objective": "reg:squarederror", "n_estimators": 100, "seed": 42}
    model = XGBRegressor(**model_params)
    model.fit(X_train, y_train)

    preds = model.predict(X_val)
    # Extract feature importance for model explainability
    importances = []
    if hasattr(model, "feature_importances_"):
        for col, imp in sorted(zip(feature_columns, model.feature_importances_), key=lambda x: x[1], reverse=True):
            importances.append({"feature": col, "importance": round(float(imp), 4)})

    metrics = {
        "mae": round(float(mean_absolute_error(y_val, preds)), 4),
        "mse": round(float(mean_squared_error(y_val, preds)), 4),
        "rmse": round(float(mean_squared_error(y_val, preds) ** 0.5), 4),
        "r2": round(float(r2_score(y_val, preds)), 4),
        "feature_importances": importances
    }
    return model, metrics

def save_trained_xgboost(
    model: XGBRegressor,
    model_name: str,
    metadata: Optional[Dict] = None,
) -> str:
    """Persist an XGBoost model using the generic model registry.
    Returns the path to the saved artifact as a string.
    """
    path = save_model(model_name, model, metadata)
    return str(path)

def load_latest_xgboost(model_name: str) -> XGBRegressor:
    """Load the most recent XGBoost model for ``model_name``."""
    return load_latest_model(model_name)

def list_versions(model_name: str) -> List[str]:
    return list_model_versions(model_name)
