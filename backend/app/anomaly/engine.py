import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.ensemble import IsolationForest

def detect_anomalies(
    df: pd.DataFrame,
    feature_columns: Optional[List[str]] = None,
    date_column: Optional[str] = None,
    contamination: float = 0.05
) -> Dict[str, Any]:
    """
    Multivariate Anomaly Detection using Isolation Forest:
    - Identifies statistical outliers and behavioral anomalies
    - Computes anomaly score (-0.5 to 0.5 where lower is more anomalous)
    - Labels top anomalies with affected fields and non-fraudulent, objective explanations
    """
    total_records = len(df)
    if total_records < 10:
        return {"error": "Dataset must contain at least 10 records for anomaly detection."}

    # Select numeric features
    if not feature_columns:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        # Fallback: if no numeric columns detected, use all columns (coerce will handle conversion)
        feature_columns = numeric_cols if numeric_cols else list(df.columns)

    if len(feature_columns) == 0:
        return {"error": "No feature columns available to compute anomaly scores."}

    # Prepare feature matrix — coerce all selected columns to numeric to prevent dtype errors
    X_df = df[feature_columns].apply(pd.to_numeric, errors='coerce')
    # Impute missing values with median for isolation forest stability
    X_imputed = X_df.apply(lambda col: col.fillna(col.median() if col.notna().any() else 0))
    
    # Fit Isolation Forest
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=max(0.01, min(0.2, contamination)),
        random_state=42
    )
    
    preds = iso_forest.fit_predict(X_imputed) # -1 for anomaly, 1 for normal
    scores = iso_forest.decision_function(X_imputed) # lower score = more anomalous

    anomaly_indices = np.where(preds == -1)[0]
    total_anomalies = len(anomaly_indices)

    # Rank anomalies by lowest score
    sorted_anom_indices = anomaly_indices[np.argsort(scores[anomaly_indices])]

    # Compute column medians and IQRs to explain anomaly causes
    col_medians = X_imputed.median()
    col_iqrs = X_imputed.quantile(0.75) - X_imputed.quantile(0.25)

    detailed_anomalies = []
    # Take top 30 most extreme anomalies
    for idx in sorted_anom_indices[:30]:
        row = df.iloc[idx]
        score_val = float(scores[idx])
        
        # Identify which fields deviated furthest from median
        affected = []
        for col in feature_columns:
            val = float(X_imputed.iloc[idx][col])
            med = float(col_medians[col])
            iqr_val = float(col_iqrs[col]) if col_iqrs[col] > 0 else 1.0
            z_approx = abs(val - med) / iqr_val
            if z_approx > 2.0:
                affected.append({
                    "column": col,
                    "actual_value": round(val, 2),
                    "dataset_median": round(med, 2),
                    "iqr_deviation": round(z_approx, 2)
                })
        
        # Sort affected fields by deviation
        affected.sort(key=lambda x: x["iqr_deviation"], reverse=True)
        top_affected = [a["column"] for a in affected[:3]]
        
        # Construct objective explanation without making unverified claims
        if affected:
            dev_str = ", ".join([f"{a['column']}={a['actual_value']} (median: {a['dataset_median']})" for a in affected[:2]])
            explanation = f"Statistically anomalous multivariate combination; substantial deviation in {dev_str}."
        else:
            explanation = "Unusual multivariate combination across selected numeric dimensions."

        date_val = str(row[date_column]) if date_column and date_column in df.columns else None

        # Clean row payload for JSON serialization
        payload = {}
        for c in df.columns[:10]: # First 10 cols
            val = row[c]
            if pd.isna(val):
                payload[str(c)] = None
            elif isinstance(val, (np.integer, int)):
                payload[str(c)] = int(val)
            elif isinstance(val, (np.floating, float)):
                payload[str(c)] = round(float(val), 2)
            else:
                payload[str(c)] = str(val)

        detailed_anomalies.append({
            "record_index": int(idx),
            "timestamp": date_val,
            "anomaly_score": round(score_val, 4),
            "severity": "high" if score_val < -0.15 else "medium",
            "top_affected_fields": top_affected,
            "field_deviations": affected[:4],
            "explanation": explanation,
            "record_payload": payload
        })

    return {
        "status": "success",
        "total_records_evaluated": total_records,
        "features_used": feature_columns,
        "anomalies_detected_count": total_anomalies,
        "anomaly_percentage": round((total_anomalies / total_records) * 100, 2),
        "contamination_threshold": contamination,
        "top_anomalies": detailed_anomalies
    }
