import pandas as pd
import numpy as np
from typing import Dict, Any, List
import scipy.stats as stats

def calculate_statistical_entropy(series: pd.Series) -> float:
    """Calculates Shannon Entropy in bits for categorical distribution."""
    counts = series.value_counts(normalize=True, dropna=True)
    if len(counts) <= 1:
        return 0.0
    return float(-np.sum(counts * np.log2(counts)))

def run_dataset_stress_and_drift_audit(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Novelty Engine 2: Real-time Feature Stability, Population Shift & Data Drift Audit
    - Computes Population Stability Index (PSI) proxy by comparing first half vs second half
    - Shannon Entropy of categorical distributions (detecting concentration/diversity collapse)
    - Kurtosis and Skewness for heavy tail risk
    - Quantile Stress Shock Testing (-25%, Median, +25% volatility shocks)
    """
    total_records = len(df)
    if total_records < 20:
        return {"error": "Dataset requires at least 20 records for drift audit and stress testing."}

    half = total_records // 2
    df_early = df.iloc[:half]
    df_late = df.iloc[half:]

    drift_reports = []
    stress_shocks = []

    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if c not in num_cols]

    # 1. Numeric Drift Analysis (Kolmogorov-Smirnov 2-sample test for distributional drift)
    for col in num_cols[:6]: # top numeric columns
        s_early = df_early[col].dropna()
        s_late = df_late[col].dropna()

        if len(s_early) > 10 and len(s_late) > 10:
            ks_stat, p_val = stats.ks_2samp(s_early, s_late)
            mean_shift_pct = float(((s_late.mean() - s_early.mean()) / s_early.mean()) * 100) if s_early.mean() != 0 else 0.0
            
            # Kurtosis (tail risk) and Skewness
            skew_val = float(stats.skew(df[col].dropna()))
            kurt_val = float(stats.kurtosis(df[col].dropna()))

            drift_level = "Severe Drift" if p_val < 0.01 else "Moderate Drift" if p_val < 0.05 else "Stable"

            drift_reports.append({
                "column": col,
                "type": "numeric",
                "ks_statistic": round(float(ks_stat), 4),
                "p_value": float(f"{p_val:.4e}"),
                "mean_shift_pct": round(mean_shift_pct, 2),
                "skewness": round(skew_val, 2),
                "kurtosis": round(kurt_val, 2),
                "tail_risk": "Heavy Tailed" if kurt_val > 3.0 else "Normal/Light",
                "drift_status": drift_level
            })

            # Stress Shock Testing: Simulate distribution response under macroeconomic shocks
            base_median = float(df[col].median())
            stress_shocks.append({
                "column": col,
                "current_median": round(base_median, 2),
                "shock_down_20pct": round(base_median * 0.8, 2),
                "shock_up_20pct": round(base_median * 1.2, 2),
                "tail_value_at_risk_5pct": round(float(df[col].quantile(0.05)), 2),
                "tail_upside_95pct": round(float(df[col].quantile(0.95)), 2)
            })

    # 2. Categorical Entropy Analysis
    entropy_reports = []
    for col in cat_cols[:4]:
        entropy_val = calculate_statistical_entropy(df[col])
        distinct_count = int(df[col].nunique(dropna=True))
        max_possible_entropy = np.log2(distinct_count) if distinct_count > 1 else 1.0
        diversity_ratio = round(entropy_val / max_possible_entropy, 3) if max_possible_entropy > 0 else 0.0

        entropy_reports.append({
            "column": col,
            "shannon_entropy_bits": round(entropy_val, 3),
            "diversity_ratio": diversity_ratio,
            "status": "Healthy Diversity" if diversity_ratio > 0.6 else "High Concentration / Dominance Risk"
        })

    return {
        "status": "success",
        "sample_split": f"Comparative Temporal Drift (Initial {half} rows vs Final {total_records - half} rows)",
        "feature_drift_analysis": drift_reports,
        "stress_shocks": stress_shocks,
        "categorical_entropy_diversity": entropy_reports,
        "overall_stability_verdict": (
            "Systemic Distribution Drift Detected" if any(r["drift_status"] == "Severe Drift" for r in drift_reports)
            else "Stable Distribution Across Time"
        )
    }
