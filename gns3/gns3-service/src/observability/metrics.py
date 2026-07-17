"""Prometheus-метрики gns3-service. Набор легче, чем у backend."""

from prometheus_fastapi_instrumentator import Instrumentator


def configure_metrics(app) -> None:
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
