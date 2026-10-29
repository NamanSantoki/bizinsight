import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# 1. Traffic & Latency Metrics (RED Method)
REQUEST_COUNT = Counter(
    "bizinsight_http_requests_total",
    "Total HTTP request count partitioned by method, endpoint path, and status code.",
    ["method", "path", "status"]
)

REQUEST_LATENCY = Histogram(
    "bizinsight_http_request_duration_seconds",
    "HTTP request latency in seconds partitioned by method and endpoint path.",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# 2. SRE & Error Budget Metrics
ERROR_BUDGET_REMAINING = Gauge(
    "bizinsight_sre_error_budget_remaining_percent",
    "Calculated 30-day rolling SLO error budget remaining percentage."
)

SLO_TARGET_PERCENT = Gauge(
    "bizinsight_sre_slo_target_percent",
    "Agreed Service Level Objective availability target percentage."
)

ACTIVE_INGESTION_JOBS = Gauge(
    "bizinsight_active_ingestion_jobs",
    "Current count of parallel data processing and ingestion pipelines."
)

DATASETS_TRACKED_TOTAL = Gauge(
    "bizinsight_datasets_tracked_total",
    "Total number of enterprise business datasets registered in platform."
)

# Set initial baseline gauges
SLO_TARGET_PERCENT.set(99.9)
ERROR_BUDGET_REMAINING.set(98.4)
ACTIVE_INGESTION_JOBS.set(2)
DATASETS_TRACKED_TOTAL.set(5)

class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/metrics", "/health/live", "/health/ready"]:
            return await call_next(request)

        method = request.method
        path = request.url.path
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception as e:
            status_code = "500"
            raise e
        finally:
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method=method, path=path, status=status_code).inc()
            REQUEST_LATENCY.labels(method=method, path=path).observe(duration)

        return response

def get_prometheus_metrics_payload() -> Response:
    """Returns exposition-formatted Prometheus text payload."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

