"""Prometheus metrics setup. Exposes /metrics on the FastAPI app."""

from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

active_sessions_gauge = Gauge(
    "platform_active_sessions",
    "Number of active learning sessions",
    ["lab_slug"],
)
idle_reclaimed_counter = Counter(
    "platform_idle_reclaimed_total",
    "Sessions whose nodes were stopped due to 30-min idle",
    ["lab_slug"],
)


def configure_metrics(app) -> None:
    """Wires Prometheus instrumentation into the app and exposes the /metrics endpoint."""
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
