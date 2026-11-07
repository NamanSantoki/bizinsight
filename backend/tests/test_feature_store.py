# Tests for EnterpriseFeatureStore (feature_store/store.py)
import pandas as pd
import pytest
from backend.app.feature_store.store import EnterpriseFeatureStore

@pytest.fixture
def store():
    return EnterpriseFeatureStore()

def test_list_features_returns_all(store):
    features = store.list_features()
    assert isinstance(features, list)
    assert len(features) >= 4  # seeded features
    for f in features:
        assert "feature_name" in f

def test_get_feature_existing(store):
    f = store.get_feature("customer_purchase_frequency")
    assert f is not None
    assert f["feature_name"] == "customer_purchase_frequency"

def test_get_feature_missing(store):
    assert store.get_feature("nonexistent") is None

def test_get_online_features_found(store):
    res = store.get_online_features("cust_1001")
    assert res["found"] is True
    assert "features" in res
    assert res["features"]["customer_purchase_frequency"] == 5.4

def test_get_online_features_not_found(store):
    res = store.get_online_features("unknown")
    assert res["found"] is False
    assert "features" in res
    # defaults are present
    assert res["features"]["customer_purchase_frequency"] == 3.82

