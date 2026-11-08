import pytest
import pandas as pd
import numpy as np
from backend.app.analytics.causal_engine import run_causal_counterfactual_engine
from backend.app.analytics.stress_engine import (
    calculate_statistical_entropy,
    run_dataset_stress_and_drift_audit
)

def test_causal_engine_insufficient_cols():
    df = pd.DataFrame({"only_one": [1, 2, 3, 4, 5]})
    res = run_causal_counterfactual_engine(df)
    assert "error" in res

def test_causal_engine_insufficient_rows():
    df = pd.DataFrame({"x": range(10), "y": range(10)})
    res = run_causal_counterfactual_engine(df)
    assert "error" in res

def test_causal_engine_success():
    np.random.seed(42)
    x = np.random.normal(50, 10, 100)
    y = 2.5 * x + np.random.normal(0, 5, 100)
    df = pd.DataFrame({"spend": x, "revenue": y})

    res = run_causal_counterfactual_engine(
        df,
        target_metric="revenue",
        intervention_driver="spend",
        perturbation_pct=15.0
    )

    assert res["status"] == "success"
    assert res["target_metric"] == "revenue"
    assert res["intervention_driver"] == "spend"
    assert "metrics" in res
    assert "counterfactual_simulation" in res
    assert len(res["simulation_curve"]) > 0

def test_stress_entropy_calculation():
    # Constant series -> entropy 0
    s_const = pd.Series(["A", "A", "A", "A"])
    assert calculate_statistical_entropy(s_const) == 0.0

    # Diverse series -> entropy > 0
    s_diverse = pd.Series(["A", "B", "C", "D"] * 10)
    ent = calculate_statistical_entropy(s_diverse)
    assert ent > 1.5

def test_stress_audit_insufficient_records():
    df = pd.DataFrame({"val": range(10)})
    res = run_dataset_stress_and_drift_audit(df)
    assert "error" in res

def test_stress_audit_success():
    np.random.seed(42)
    # 50 records early, 50 late
    early = np.random.normal(100, 10, 50)
    late = np.random.normal(120, 15, 50) # drifted distribution
    df = pd.DataFrame({
        "revenue": np.concatenate([early, late]),
        "category": ["Retail"] * 50 + ["Wholesale"] * 50
    })

    res = run_dataset_stress_and_drift_audit(df)
    assert res["status"] == "success"
    assert len(res["feature_drift_analysis"]) > 0
    assert len(res["stress_shocks"]) > 0
    assert len(res["categorical_entropy_diversity"]) > 0

