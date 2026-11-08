# Tests for Model Registry (ml/model_registry.py)
import os
import joblib
import pytest
from pathlib import Path
from backend.app.ml.model_registry import save_model, load_latest_model, list_model_versions

class DummyModel:
    def __init__(self, param):
        self.param = param
    def predict(self, X):
        return [self.param for _ in X]

def test_save_and_load_model(tmp_path: Path):
    model = DummyModel(param=42)
    model_name = "test_model"
    # Save model
    model_path = save_model(model_name, model, metadata={"info": "test"})
    assert model_path.exists()
    # Load latest model
    loaded = load_latest_model(model_name)
    assert isinstance(loaded, DummyModel)
    assert loaded.param == 42
    # Verify metadata file exists
    meta_path = model_path.parent / "metadata.pkl"
    assert meta_path.exists()
    meta = joblib.load(meta_path)
    assert meta["info"] == "test"

def test_list_model_versions_orders(tmp_path: Path):
    import time
    model_name = "versioned_model"
    # Save two models with a short sleep to ensure distinct timestamp order
    model1 = DummyModel(param=1)
    model2 = DummyModel(param=2)
    path1 = save_model(model_name, model1)
    time.sleep(1.1)
    path2 = save_model(model_name, model2)
    versions = list_model_versions(model_name)
    # Versions are directory names; newest should be first
    assert len(versions) >= 2
    # Ensure the most recent version directory matches path2
    latest_dir = Path(path2).parent.name
    assert versions[0] == latest_dir

