# Tests for ModelServer (mlops/serving.py)
import pytest
from backend.app.mlops.serving import ModelServer

@pytest.fixture
def server():
    return ModelServer()

def test_predict_returns_expected_fields(server):
    result = server.predict("test-model", {"marketing_spend": 20000, "price_index": 110})
    assert isinstance(result, dict)
    expected_keys = {"model_id", "prediction", "prediction_unit", "latency_ms", "model_version", "serving_framework", "timestamp"}
    assert expected_keys.issubset(result.keys())
    assert result["model_id"] == "test-model"
    assert isinstance(result["prediction"], (int, float))
    assert result["latency_ms"] >= 0

def test_batch_predict_aggregates_predictions(server):
    instances = [{"marketing_spend": 10000, "price_index": 100}, {"marketing_spend": 5000, "price_index": 95}]
    batch = server.batch_predict("batch-model", instances)
    assert batch["model_id"] == "batch-model"
    assert batch["batch_size"] == 2
    assert isinstance(batch["predictions"], list) and len(batch["predictions"]) == 2
    assert batch["total_batch_time_ms"] >= 0
    assert batch["avg_latency_per_sample_ms"] >= 0

def test_get_serving_telemetry(server):
    telemetry = server.get_serving_telemetry()
    assert telemetry["status"] == "HEALTHY"
    assert isinstance(telemetry["total_requests_processed"], int)
    assert isinstance(telemetry["error_rate_pct"], float)
    for p in ["p50_ms", "p95_ms", "p99_ms"]:
        assert isinstance(telemetry["latency"][p], (int, float))

