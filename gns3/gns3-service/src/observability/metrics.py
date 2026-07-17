"""Prometheus metrics for gns3-service. A lighter set than the backend's."""

from prometheus_fastapi_instrumentator import Instrumentator


def configure_metrics(app) -> None:
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
