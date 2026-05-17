"""Prometheus-метрики gns3-service. Набор легче, чем у backend."""

from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

gns3_provisioning_duration = Histogram(
    "gns3_provisioning_duration_seconds",
    "create_session end-to-end timing",
    buckets=(0.5, 1, 2, 5, 10, 20, 60, 120),
)
gns3_admin_calls = Counter(
    "gns3_admin_api_calls_total",
    "GNS3 admin API calls",
    ["method", "result"],
)


def configure_metrics(app) -> None:
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
