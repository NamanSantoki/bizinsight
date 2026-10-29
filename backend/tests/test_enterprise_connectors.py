import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ingestion.scheduler import ingestion_scheduler
from backend.app.security.api_keys import api_key_manager

client = TestClient(app)

def get_auth_token():
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "AdminPass2026!"}
    )
    assert res.status_code == 200
    return res.json()["access_token"]

def test_automated_ingestion_schedules():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List active CDC schedules
    res = client.get("/api/v1/enterprise-connectors/schedules", headers=headers)
    assert res.status_code == 200
    schedules = res.json()["schedules"]
    assert len(schedules) >= 2
    assert any(s["task_id"] == "sync_crm_daily" for s in schedules)

    # 2. Trigger an incremental sync job
    run_res = client.post(
        "/api/v1/enterprise-connectors/schedules/sync_crm_daily/run?new_records=150",
        headers=headers
    )
    assert run_res.status_code == 200
    data = run_res.json()
    assert data["status"] == "COMPLETED"
    assert data["new_rows_imported"] == 150
    assert data["incremental_column"] == "transaction_date"

def test_enterprise_api_keys():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a scoped API key
    create_res = client.post(
        "/api/v1/enterprise-connectors/api-keys",
        headers=headers,
        json={
            "name": "Databricks Pipeline Token",
            "scopes": ["datasets:read", "sql:execute"],
            "rate_limit_per_minute": 250
        }
    )
    assert create_res.status_code == 200
    key_data = create_res.json()
    assert key_data["api_key"].startswith("bk_live_")

    # 2. Verify key validation engine
    raw_key = key_data["api_key"]
    assert api_key_manager.verify_key(raw_key, required_scope="datasets:read") is True
    assert api_key_manager.verify_key(raw_key, required_scope="admin:superuser") is False
    assert api_key_manager.verify_key("invalid_fake_key_123") is False

    # 3. List keys masked
    list_res = client.get("/api/v1/enterprise-connectors/api-keys", headers=headers)
    assert list_res.status_code == 200
    keys = list_res.json()["api_keys"]
    assert any(k["name"] == "Databricks Pipeline Token" for k in keys)

