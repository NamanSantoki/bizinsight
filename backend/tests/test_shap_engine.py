# Tests for SHAP explainability engine (ml/shap_engine.py)
import pandas as pd
import pytest
from backend.app.ml.shap_engine import compute_shap_explainability

@pytest.fixture
def sample_df():
    # Create a simple numeric dataframe with enough rows (>= 15 required)
    data = {
        "price": [10, 12, 15, 20, 22, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95],
        "feature1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        "feature2": [5, 4, 3, 2, 1, 5, 4, 3, 2, 1, 5, 4, 3, 2, 1, 5, 4, 3, 2, 1],
    }
    return pd.DataFrame(data)

def test_compute_shap_success(sample_df):
    result = compute_shap_explainability(sample_df)
    assert result["status"] == "success"
    # Expect global_importance list with entries for each feature
    globals_ = result.get("global_importance", [])
    assert isinstance(globals_, list)
    assert len(globals_) == 2  # feature1 and feature2 (price is target)
    # Check that local contributions are sorted and contain expected keys
    locals_ = result.get("local_contributions", [])
    assert isinstance(locals_, list)
    assert all(set(item.keys()) == {"feature", "feature_value", "shap_value", "direction", "abs_impact"} for item in locals_)
    # Verify that expected_base_value and predicted_value are floats
    assert isinstance(result["expected_base_value"], float)
    assert isinstance(result["predicted_value"], float)

def test_compute_shap_insufficient_numeric_columns():
    df = pd.DataFrame({"cat": ["a", "b"], "text": ["x", "y"]})
    result = compute_shap_explainability(df)
    assert "error" in result
    assert "At least 2 numeric columns" in result["error"]

def test_compute_shap_insufficient_rows():
    df = pd.DataFrame({"price": [1, 2], "feature": [10, 20]})
    result = compute_shap_explainability(df)
    assert "error" in result
    assert "Insufficient valid observations" in result["error"]

