import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from scipy.optimize import minimize
from sklearn.linear_model import Ridge

def run_inverse_goal_seek(
    df: pd.DataFrame,
    target_metric: Optional[str] = None,
    target_goal_value: Optional[float] = None,
    controllable_levers: Optional[List[str]] = None,
    lever_bounds: Optional[Dict[str, List[float]]] = None, # e.g. {"carat": [0.2, 3.0]}
    importance_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    r"""
    Novelty Engine: Prescriptive Inverse Optimization / Goal-Seek Engine
    
    Given a desired Target KPI ($y^*$) and a set of controllable business levers ($x_1, \dots, x_k$),
    solves the constrained quadratic optimization problem:
        min sum w_i * ((x_i - x_0,i) / sigma_i)^2
        subject to:
            hat{f}(x) == y*  (model surrogate prediction matches target)
            x_min <= x <= x_max (operational bounds)
    """
    num_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
    if len(num_cols) < 2:
        return {"error": "At least 2 numeric columns are required for goal-seek optimization."}

    # Identify target
    if not target_metric or target_metric not in num_cols:
        target_metric = next((c for c in ["price", "revenue", "median_house_value", "sales", "fare", "Value"] if c in num_cols), num_cols[-1])

    # Available levers
    candidate_levers = [c for c in num_cols if c != target_metric]
    if not controllable_levers:
        # Default to top 3 correlated levers
        corrs = {c: abs(df[c].corr(df[target_metric])) for c in candidate_levers if not pd.isna(df[c].corr(df[target_metric]))}
        sorted_levers = sorted(corrs.items(), key=lambda x: x[1], reverse=True)
        controllable_levers = [k for k, _ in sorted_levers[:3]] if sorted_levers else candidate_levers[:3]

    if len(controllable_levers) == 0:
        return {"error": "No controllable levers available for optimization."}

    clean_df = df[controllable_levers + [target_metric]].dropna()
    if len(clean_df) < 15:
        return {"error": "Insufficient valid observations for surrogate modeling."}

    X = clean_df[controllable_levers].values
    y = clean_df[target_metric].values

    # Fit surrogate predictive response surface
    surrogate = Ridge(alpha=1.0)
    surrogate.fit(X, y)

    # Baseline current means
    baseline_x = np.mean(X, axis=0)
    baseline_y = float(np.mean(y))
    stds = np.std(X, axis=0)
    stds[stds == 0] = 1.0  # Avoid division by zero

    # If target_goal_value not specified, default to +20% growth
    if target_goal_value is None or target_goal_value <= 0:
        target_goal_value = float(baseline_y * 1.20)

    # Prepare bounds
    bounds = []
    for i, col in enumerate(controllable_levers):
        col_min = float(np.min(X[:, i]))
        col_max = float(np.max(X[:, i]))
        if lever_bounds and col in lever_bounds:
            b = lever_bounds[col]
            bounds.append((float(b[0]), float(b[1])))
        else:
            # Allow expanding current observed range by 25%
            margin = (col_max - col_min) * 0.25
            bounds.append((max(0.0, col_min - margin), col_max + margin))

    # Weighting: cost of moving each lever
    weights = np.ones(len(controllable_levers))
    if importance_weights:
        for i, col in enumerate(controllable_levers):
            if col in importance_weights:
                weights[i] = float(importance_weights[col])

    # Objective: Minimize weighted normalized adjustment cost
    def objective(x):
        norm_diff = (x - baseline_x) / stds
        return np.sum(weights * (norm_diff ** 2))

    # Constraint: surrogate prediction equals target_goal_value
    def constraint_target(x):
        pred = surrogate.predict(x.reshape(1, -1))[0]
        return pred - target_goal_value

    # Solve via SLSQP
    res = minimize(
        fun=objective,
        x0=baseline_x,
        method="SLSQP",
        bounds=bounds,
        constraints={"type": "eq", "fun": constraint_target},
        options={"maxiter": 200, "ftol": 1e-6}
    )

    # If exact equality fails or is infeasible, fall back to soft L2 penalty
    if not res.success:
        def penalized_obj(x):
            pred = surrogate.predict(x.reshape(1, -1))[0]
            penalty = 100.0 * ((pred - target_goal_value) / (baseline_y + 1e-6)) ** 2
            norm_diff = (x - baseline_x) / stds
            return np.sum(weights * (norm_diff ** 2)) + penalty

        res = minimize(
            fun=penalized_obj,
            x0=baseline_x,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 200}
        )

    opt_x = res.x
    predicted_achieved = float(surrogate.predict(opt_x.reshape(1, -1))[0])
    target_gap_pct = round(float(abs(predicted_achieved - target_goal_value) / (target_goal_value + 1e-6) * 100), 2)
    feasibility = "Optimal (Target Met)" if target_gap_pct <= 2.0 else "Constrained Approximation" if target_gap_pct <= 10.0 else "Infeasible within Bounds"

    lever_recommendations = []
    for i, col in enumerate(controllable_levers):
        orig_val = float(baseline_x[i])
        new_val = float(opt_x[i])
        delta = new_val - orig_val
        pct_change = (delta / (orig_val + 1e-9)) * 100
        lever_recommendations.append({
            "lever": col,
            "baseline_value": round(orig_val, 4),
            "recommended_value": round(new_val, 4),
            "absolute_change": round(delta, 4),
            "percentage_change": round(pct_change, 2),
            "min_bound": round(bounds[i][0], 4),
            "max_bound": round(bounds[i][1], 4)
        })

    return {
        "status": "success",
        "target_metric": target_metric,
        "baseline_metric_value": round(baseline_y, 4),
        "target_goal_value": round(target_goal_value, 4),
        "achieved_prediction": round(predicted_achieved, 4),
        "target_gap_pct": target_gap_pct,
        "feasibility_verdict": feasibility,
        "optimization_success": bool(res.success),
        "iterations_used": int(getattr(res, 'nit', 0)),
        "available_candidate_levers": candidate_levers,
        "active_levers": controllable_levers,
        "recommendations": lever_recommendations,
        "mathematical_model": "Sequential Least Squares Programming (SLSQP) with L2 Elasticity Penalties"
    }
