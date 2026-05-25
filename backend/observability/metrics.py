"""Настройка Prometheus-метрик. Публикует /metrics на FastAPI-приложении."""

from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

active_sessions_gauge = Gauge(
    "platform_active_sessions",
    "Number of active learning sessions",
    ["lab_slug"],
)
session_launches_counter = Counter(
    "platform_session_launches_total",
    "Total session launch attempts",
    ["lab_slug", "result"],  # success | error | rate_limited | over_cap
)
provisioning_duration_histogram = Histogram(
    "platform_provisioning_duration_seconds",
    "End-to-end provisioning time (incl gns3-service call)",
    ["lab_slug"],
    buckets=(0.5, 1, 2, 5, 10, 20, 60, 120),
)
queue_depth_gauge = Gauge(
    "platform_queue_depth",
    "Current queue depth per lab",
    ["lab_slug"],
)
idle_reclaimed_counter = Counter(
    "platform_idle_reclaimed_total",
    "Sessions whose nodes were stopped due to 30-min idle",
    ["lab_slug"],
)


def configure_metrics(app) -> None:
    """Подключает инструментирование Prometheus к приложению и публикует эндпоинт /metrics."""
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
