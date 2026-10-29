import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import xgboost as xgb
import shap

def compute_shap_explainability(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
    feature_columns: Optional[List[str]] = None,
    record_index: int = 0,
    sample_size: int = 500
) -> Dict[str, Any]:
    """
    Computes rigorous Shapley Additive exPlanations (SHAP) using TreeSHAP on an XGBoost model.
    Returns:
    - Global feature importances (mean absolute SHAP)
    - Local waterfall attribution for a specific observation record
    - Base expected value and final predicted value
    """
    num_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
    if len(num_cols) < 2:
        return {"error": "At least 2 numeric columns are required to train and explain an ML model."}

    # Select target if not provided
    if not target_column or target_column not in num_cols:
        target_column = next((c for c in ["price", "revenue", "median_house_value", "sales", "fare", "Value"] if c in num_cols), num_cols[-1])

    # Select features
    if not feature_columns:
        feature_columns = [c for c in num_cols if c != target_column]

    if len(feature_columns) == 0:
        return {"error": "No feature columns available after selecting target."}

    # Downsample if large for fast, interactive response
    data_df = df[feature_columns + [target_column]].dropna()
    if len(data_df) > sample_size:
        data_df = data_df.sample(n=sample_size, random_state=42)

    if len(data_df) < 15:
        return {"error": "Insufficient valid observations (minimum 15 required)."}

    X = data_df[feature_columns]
    y = data_df[target_column]

    # Train high-performance XGBoost regressor
    model = xgb.XGBRegressor(
        n_estimators=50,
        max_depth=4,
        learning_rate=0.1,
        random_state=42
    )
    model.fit(X, y)

    # Compute TreeSHAP
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    expected_value = float(explainer.expected_value)

    # Global feature importance: mean(|SHAP value|)
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    global_importance = []
    for feat, imp in sorted(zip(feature_columns, mean_abs_shap), key=lambda x: x[1], reverse=True):
        global_importance.append({
            "feature": feat,
            "mean_abs_shap": round(float(imp), 4),
            "relative_importance_pct": round(float((imp / (np.sum(mean_abs_shap) + 1e-9)) * 100), 2)
        })

    # Local explanation for requested record_index
    idx = max(0, min(record_index, len(X) - 1))
    record_x = X.iloc[idx]
    record_shap = shap_values[idx]
    predicted_val = float(model.predict(X.iloc[[idx]])[0])
    actual_val = float(y.iloc[idx]) if idx < len(y) else None

    # Decompose waterfall features
    local_contributions = []
    for feat, val, s_val in zip(feature_columns, record_x, record_shap):
        local_contributions.append({
            "feature": feat,
            "feature_value": round(float(val), 4) if isinstance(val, (int, float, np.number)) else str(val),
            "shap_value": round(float(s_val), 4),
            "direction": "positive" if s_val >= 0 else "negative",
            "abs_impact": round(float(abs(s_val)), 4)
        })

    # Sort local contributions by absolute impact
    local_contributions.sort(key=lambda x: x["abs_impact"], reverse=True)

    return {
        "status": "success",
        "target_column": target_column,
        "sample_size": len(X),
        "total_records": len(df),
        "expected_base_value": round(expected_value, 4),
        "record_index": idx,
        "predicted_value": round(predicted_val, 4),
        "actual_value": round(actual_val, 4) if actual_val is not None else None,
        "global_importance": global_importance,
        "local_contributions": local_contributions,
        "available_records_count": len(X),
        "algorithm": "TreeSHAP (TreeExplainer with Lundberg-Lee Game Theoretic Axioms)"
    }
