# Coverage booster tests to hit low‑coverage modules
import pandas as pd
import pytest

# Model Registry coverage
class BoosterDummyModel:
    def __init__(self):
        self.value = 1

def test_model_registry_coverage(tmp_path):
    from backend.app.ml.model_registry import save_model, load_latest_model, list_model_versions
    model_name = "coverage_model"
    dummy = BoosterDummyModel()
    # Save with metadata
    save_model(model_name, dummy, metadata={"info": "test"})
    # Load latest
    loaded = load_latest_model(model_name)
    assert hasattr(loaded, "value")
    # List versions
    versions = list_model_versions(model_name)
    assert isinstance(versions, list) and len(versions) >= 1

# SHAP engine coverage (reuse existing fixture if available)
@pytest.fixture
def df_shap():
    return pd.DataFrame({
        "price": [10, 12, 15, 20, 22, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95],
        "feature1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        "feature2": [5, 4, 3, 2, 1, 5, 4, 3, 2, 1, 5, 4, 3, 2, 1, 5, 4, 3, 2, 1],
    })

def test_shap_engine_coverage(df_shap):
    from backend.app.ml.shap_engine import compute_shap_explainability
    result = compute_shap_explainability(df_shap)
    assert result.get("status") == "success"
    assert isinstance(result.get("global_importance"), list)
    assert isinstance(result.get("local_contributions"), list)

# Semantic Metrics Store coverage
def test_semantic_metrics_store_coverage():
    from backend.app.semantic.metrics_store import MetricsStore
    store = MetricsStore()
    # List existing metrics
    metrics = store.list_metrics()
    assert isinstance(metrics, list)
    # Generate dataset metrics for a simple dataframe
    df = pd.DataFrame({
        "sales": [100, 200, 150],
        "region": ["EU", "APAC", "EU"]
    })
    generated = store.generate_dataset_metrics("sales_orders", "sales_table", df)
    assert isinstance(generated, list)
    # Ensure at least one generated metric
    assert len(generated) > 0

