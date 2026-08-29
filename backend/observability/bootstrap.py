"""Process-wide logging and error reporting, configured once at import time."""

import os

from config import settings
from observability.logging import configure_logging
from observability.sentry import configure_sentry


def bootstrap() -> None:
    """Configures logging and error reporting for the process."""
    configure_logging(
        "backend",
        level=getattr(getattr(settings, "log", None), "log_level", "INFO"),
        environment=getattr(getattr(settings, "api", None), "environment", "production"),
    )
    configure_sentry("backend", environment=os.getenv("ENVIRONMENT", "dev"))
