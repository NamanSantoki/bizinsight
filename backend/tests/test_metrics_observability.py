from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_prometheus_metrics_endpoint():
    # Make a few calls to trigger counter and histogram
    client.get("/api/v1/health")
    client.get("/api/v1/datasets")

    # Fetch Prometheus metrics exposition
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    body = response.text
    # Verify core SRE & SLI metrics are exposed
    assert "bizinsight_http_requests_total" in body
    assert "bizinsight_http_request_duration_seconds" in body
    assert "bizinsight_sre_error_budget_remaining_percent" in body
    assert "bizinsight_sre_slo_target_percent" in body
    assert "bizinsight_active_ingestion_jobs" in body
    assert "bizinsight_datasets_tracked_total" in body

