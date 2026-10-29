import pytest
import pandas as pd
import numpy as np
from backend.app.ml.shap_engine import compute_shap_explainability
from backend.app.analytics.goal_seek_engine import run_inverse_goal_seek
from backend.app.audit.governance_report import generate_governance_pdf

@pytest.fixture
def sample_numeric_df():
    np.random.seed(42)
    n = 100
    x1 = np.random.uniform(10, 50, n)
    x2 = np.random.uniform(1, 5, n)
    # y depends directly on x1 and x2
    y = 5.0 * x1 + 20.0 * x2 + np.random.normal(0, 2, n)
    return pd.DataFrame({"marketing_spend": x1, "discount_pct": x2, "revenue": y})

def test_shap_explainability_engine(sample_numeric_df):
    res = compute_shap_explainability(
        df=sample_numeric_df,
        target_column="revenue",
        record_index=5,
        sample_size=100
    )
    assert res["status"] == "success"
    assert "expected_base_value" in res
    assert "global_importance" in res
    assert len(res["global_importance"]) > 0
    assert "local_contributions" in res
    assert len(res["local_contributions"]) == 2
    # Verify features sum up to explanation
    total_shap = sum(c["shap_value"] for c in res["local_contributions"])
    diff = abs((res["expected_base_value"] + total_shap) - res["predicted_value"])
    assert diff < 0.05

def test_inverse_goal_seek_engine(sample_numeric_df):
    baseline_revenue = float(np.mean(sample_numeric_df["revenue"]))
    target_goal = baseline_revenue * 1.30 # +30% growth goal

    res = run_inverse_goal_seek(
        df=sample_numeric_df,
        target_metric="revenue",
        target_goal_value=target_goal,
        controllable_levers=["marketing_spend", "discount_pct"]
    )
    assert res["status"] == "success"
    assert res["target_goal_value"] == round(target_goal, 4)
    assert len(res["recommendations"]) == 2
    assert "feasibility_verdict" in res
    # Achieved prediction should be very close to target goal
    assert abs(res["achieved_prediction"] - target_goal) / target_goal < 0.15

def test_governance_pdf_generation():
    pdf_bytes = generate_governance_pdf(
        dataset_name="test_enterprise_data.csv",
        row_count=5000,
        column_count=12,
        quality_score=94.5,
        quality_summary={"null_cells": 12, "null_pct": 0.2, "duplicate_rows": 0, "duplicate_pct": 0.0, "total_issues_found": 1},
        drift_verdict="Covariate Stable (Optimal)",
        feature_drift_list=[{"column": "marketing_spend", "ks_statistic": 0.04, "p_value": 0.82, "mean_shift_pct": 1.2, "drift_status": "Stable"}],
        model_champion="XGBoost Gradient Boosted Ensemble",
        model_mae=14.2,
        model_r2=0.94,
        causal_driver="marketing_spend",
        causal_elasticity=1.45,
        audit_events=[{"created_at": "2026-10-28 11:00:00", "username": "admin", "action": "drift_stress_audit", "resource_type": "dataset"}]
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
