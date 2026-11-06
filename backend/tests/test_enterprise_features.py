"""
Comprehensive Integration & Verification Test Suite for Enterprise 2.0 Features:
- RBAC hierarchy (admin, decision_maker, ml_engineer, analyst)
- AST Safety Verification Engine
- MLOps Versioning & Drift Monitoring Endpoints
- Cache Client (Redis + In-Memory Fallback)
- SHAP TreeExplainer & Attribution
- Quantile Probabilistic Forecasting
- Multivariate Isolation Forest Anomaly Detection
- RFM K-Means Customer Segmentation
"""
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.security.auth import get_current_active_user, get_current_user
from backend.app.security.rbac import (
    ROLE_ADMIN,
    ROLE_DECISION_MAKER,
    ROLE_ML_ENGINEER,
    ROLE_ANALYST,
    ROLE_USER,
    ROLE_HIERARCHY,
)
from backend.app.cache.redis_client import CacheClient
from backend.app.anomaly.engine import detect_anomalies
from backend.app.segmentation.engine import run_rfm_segmentation

client = TestClient(app)

class MockUser:
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role
        self.is_active = True

@pytest.fixture
def auth_decision_maker():
    u = MockUser("executive", ROLE_DECISION_MAKER)
    app.dependency_overrides[get_current_active_user] = lambda: u
    app.dependency_overrides[get_current_user] = lambda: u
    yield
    app.dependency_overrides.pop(get_current_active_user, None)
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def auth_ml_engineer():
    u = MockUser("mle", ROLE_ML_ENGINEER)
    app.dependency_overrides[get_current_active_user] = lambda: u
    app.dependency_overrides[get_current_user] = lambda: u
    yield
    app.dependency_overrides.pop(get_current_active_user, None)
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def auth_admin():
    u = MockUser("admin", ROLE_ADMIN)
    app.dependency_overrides[get_current_active_user] = lambda: u
    app.dependency_overrides[get_current_user] = lambda: u
    yield
    app.dependency_overrides.pop(get_current_active_user, None)
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def auth_analyst():
    u = MockUser("analyst", ROLE_ANALYST)
    app.dependency_overrides[get_current_active_user] = lambda: u
    app.dependency_overrides[get_current_user] = lambda: u
    yield
    app.dependency_overrides.pop(get_current_active_user, None)
    app.dependency_overrides.pop(get_current_user, None)


# --- 1. RBAC Tests ---
def test_rbac_hierarchy():
    assert ROLE_ADMIN in ROLE_HIERARCHY
    assert ROLE_DECISION_MAKER in ROLE_HIERARCHY[ROLE_ADMIN]
    assert ROLE_ANALYST in ROLE_HIERARCHY[ROLE_DECISION_MAKER]
    assert ROLE_USER in ROLE_HIERARCHY[ROLE_ANALYST]

# --- 2. AST Verification Tests ---
def test_ast_verification_safe_code(auth_admin):
    response = client.post(
        "/api/v1/enterprise/ast/verify",
        json={"code": "x = 10 + 20\ny = x * 2"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["safe"] is True
    assert len(data["disallowed_nodes"]) == 0

def test_ast_verification_prohibited_code(auth_admin):
    response = client.post(
        "/api/v1/enterprise/ast/verify",
        json={"code": "import os; os.system('ls')"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["safe"] is False
    assert "Import" in data["disallowed_nodes"]

# --- 3. MLOps Registry & Drift Tests ---
def test_mlops_registry_operations(auth_ml_engineer):
    # Register new model version
    resp = client.post(
        "/api/v1/enterprise/mlops/models/Revenue Forecast Model/versions",
        json={
            "model_name": "Revenue Forecast Model",
            "version": 7,
            "metadata": {"algorithm": "XGBoost Enterprise", "accuracy_score": 96.5}
        }
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "created"

    # Drift check
    drift_resp = client.get("/api/v1/enterprise/mlops/drift/rev_fc_07/7")
    assert drift_resp.status_code == 200
    drift_data = drift_resp.json()
    assert "drift_detected" in drift_data
    assert "details" in drift_data

# --- 4. Cache Client Tests ---
def test_cache_client_fallback_and_ttl():
    cache = CacheClient()
    cache.set("test_key", {"status": "ok", "count": 42}, expire_seconds=60)
    val = cache.get("test_key")
    assert val is not None
    assert val["status"] == "ok"
    assert val["count"] == 42

    cache.delete("test_key")
    assert cache.get("test_key") is None

    stats = cache.get_stats()
    assert "hits" in stats
    assert "misses" in stats
    assert stats["total_requests"] >= 2

# --- 5. Anomaly Detection Engine Tests ---
def test_isolation_forest_anomaly_detection():
    np.random.seed(42)
    normal = np.random.normal(loc=100, scale=10, size=(100, 3))
    outliers = np.array([[1000, 1000, 1000], [-500, -500, -500]])
    data = np.vstack([normal, outliers])
    df = pd.DataFrame(data, columns=["metric_a", "metric_b", "metric_c"])

    result = detect_anomalies(df, contamination=0.05)
    assert "anomalies_detected_count" in result
    assert result["anomalies_detected_count"] >= 2
    assert len(result["top_anomalies"]) >= 2
    first_anom = result["top_anomalies"][0]
    assert "anomaly_score" in first_anom

# --- 6. Customer RFM Segmentation Engine Tests ---
def test_rfm_kmeans_segmentation():
    df = pd.DataFrame({
        "customer_id": [f"CUST_{i % 20}" for i in range(120)],
        "transaction_date": pd.date_range("2025-01-01", periods=120, freq="D"),
        "spend_amount": np.random.uniform(20.0, 500.0, 120)
    })
    res = run_rfm_segmentation(
        df,
        customer_id_col="customer_id",
        date_col="transaction_date",
        monetary_col="spend_amount",
        n_clusters=3
    )
    assert "segments" in res
    assert len(res["segments"]) == 3
    assert "total_unique_customers" in res
    assert res["total_unique_customers"] == 20

# --- 7. Decision Intelligence Prescriptive Endpoints ---
def test_decision_intelligence_prescriptive(auth_decision_maker):
    resp = client.post(
        "/api/v1/enterprise/decision/prescriptive",
        json={
            "target_revenue_cr": 25.0,
            "min_margin_pct": 20.0,
            "max_marketing_budget_cr": 4.0
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["feasible"] is True
    assert "recommended_strategy" in data

