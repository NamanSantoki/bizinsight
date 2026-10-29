import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import scipy.stats as stats

def run_causal_counterfactual_engine(
    df: pd.DataFrame,
    target_metric: Optional[str] = None,
    intervention_driver: Optional[str] = None,
    perturbation_pct: float = 10.0 # e.g. +10% price or spend shift
) -> Dict[str, Any]:
    """
    Novelty Engine 1: Observational Causal Inference & Counterfactual Simulation
    - Identifies numeric business drivers and targets.
    - Estimates observational treatment effect using regression coefficient & elasticity.
    - Distinguishes association from direct causation with empirical p-values & 95% Confidence Intervals.
    - Simulates what-if counterfactual scenario: "What happens to Target if Driver shifts by +X%?"
    """
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(num_cols) < 2:
        return {"error": "At least 2 numeric columns are required for causal counterfactual analysis."}

    # Auto-select target metric if not provided
    if not target_metric or target_metric not in num_cols:
        target_metric = next((c for c in ["revenue", "sales", "price", "median_house_value", "Value"] if c in num_cols), num_cols[-1])

    # Candidate drivers
    candidate_drivers = [c for c in num_cols if c != target_metric]
    if not intervention_driver or intervention_driver not in candidate_drivers:
        # Pick driver with highest correlation
        corrs = {c: abs(df[c].corr(df[target_metric])) for c in candidate_drivers if not pd.isna(df[c].corr(df[target_metric]))}
        intervention_driver = max(corrs, key=corrs.get) if corrs else candidate_drivers[0]

    # Clean subset
    sub_df = df[[intervention_driver, target_metric]].dropna()
    if len(sub_df) < 15:
        return {"error": "Insufficient valid observations for causal estimation."}

    x = sub_df[intervention_driver].values
    y = sub_df[target_metric].values

    # Linear regression with statistical inference
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # Elasticity at means (% change in Y per 1% change in X)
    mean_x = float(np.mean(x))
    mean_y = float(np.mean(y))
    elasticity = float(slope * (mean_x / mean_y)) if mean_y != 0 else 0.0

    # 95% Confidence interval for causal coefficient
    t_crit = 1.96 # approx for large n
    slope_lower = float(slope - t_crit * std_err)
    slope_upper = float(slope + t_crit * std_err)

    # Counterfactual simulation: Shift Driver by perturbation_pct
    delta_x = mean_x * (perturbation_pct / 100.0)
    expected_delta_y = slope * delta_x
    counterfactual_y = mean_y + expected_delta_y
    delta_y_lower = slope_lower * delta_x
    delta_y_upper = slope_upper * delta_x

    # Association strength
    r2 = float(r_value ** 2)

    # Generate simulation curve points
    x_range = np.linspace(min(x), max(x), 20)
    curve_points = [
        {
            "driver_val": round(float(xv), 2),
            "expected_target": round(float(intercept + slope * xv), 2),
            "upper_bound": round(float(intercept + slope_upper * xv), 2),
            "lower_bound": round(float(intercept + slope_lower * xv), 2)
        }
        for xv in x_range
    ]

    return {
        "status": "success",
        "target_metric": target_metric,
        "intervention_driver": intervention_driver,
        "available_drivers": candidate_drivers,
        "sample_size": len(sub_df),
        "metrics": {
            "elasticity": round(elasticity, 3),
            "elasticity_interpretation": f"A 1.0% shift in '{intervention_driver}' is associated with an estimated {elasticity:+.2f}% change in '{target_metric}'.",
            "marginal_effect_slope": round(float(slope), 4),
            "slope_ci_95": [round(slope_lower, 4), round(slope_upper, 4)],
            "r_squared": round(r2, 4),
            "p_value": float(f"{p_value:.4e}"),
            "statistically_significant": bool(p_value < 0.05)
        },
        "counterfactual_simulation": {
            "intervention_scenario": f"Driver '{intervention_driver}' modified by {perturbation_pct:+.1f}%",
            "baseline_mean_target": round(mean_y, 2),
            "simulated_target": round(float(counterfactual_y), 2),
            "estimated_impact": round(float(expected_delta_y), 2),
            "impact_range_95": [round(float(min(delta_y_lower, delta_y_upper)), 2), round(float(max(delta_y_lower, delta_y_upper)), 2)]
        },
        "simulation_curve": curve_points,
        "methodological_caveat": "Estimates reflect observational regression adjustment with empirical standard errors. True causality requires controlling for potential confounders or randomized experiments."
    }
