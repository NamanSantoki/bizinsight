import pytest
import pandas as pd
import numpy as np
from backend.app.ml.train_xgboost import (
    train_xgboost,
    save_trained_xgboost,
    load_latest_xgboost,
    list_versions
)

def test_train_xgboost_and_registry(tmp_path):
    np.random.seed(42)
    n = 60
    df = pd.DataFrame({
        "feature_a": np.random.uniform(10, 50, n),
        "feature_b": np.random.uniform(1, 5, n),
        "target": np.random.uniform(100, 200, n)
    })

    model, metrics = train_xgboost(
        df=df,
        target_column="target",
        feature_columns=["feature_a", "feature_b"]
    )

    assert model is not None
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert len(metrics["feature_importances"]) == 2

    # Test auto feature columns fallback
    model2, metrics2 = train_xgboost(df=df, target_column="target")
    assert model2 is not None
    assert len(metrics2["feature_importances"]) == 2

    # Save and load
    saved_path = save_trained_xgboost(model, "xgboost_test_model", {"accuracy": 0.95})
    assert "xgboost_test_model" in saved_path

    versions = list_versions("xgboost_test_model")
    assert len(versions) >= 1

    loaded = load_latest_xgboost("xgboost_test_model")
    assert loaded is not None

