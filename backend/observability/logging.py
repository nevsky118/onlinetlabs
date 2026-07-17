"""Structured logging via structlog with a JSON or console formatter."""

import logging
import sys

import structlog

_CONSOLE_ENVIRONMENTS = {"local", "development"}


def configure_logging(
    service_name: str, level: str = "INFO", environment: str = "production"
) -> None:
    """Configures structlog and stdlib logging, propagates uvicorn.error to root.

    The renderer depends on the environment: colored console in local/development,
    JSON otherwise. uvicorn.access is not propagated and doesn't write: every request
    is already logged by RequestIDMiddleware as one line with request_id and duration.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.dict_tracebacks,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    renderer = (
        structlog.dev.ConsoleRenderer(colors=True)
        if environment in _CONSOLE_ENVIRONMENTS
        else structlog.processors.JSONRenderer()
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, level.upper()))
    # Propagate uvicorn/uvicorn.error to root, otherwise the formatter won't apply to them.
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True
    # Disable uvicorn.access: with it, every request would be logged twice
    # (its own access log + request_handled from RequestIDMiddleware). The Dockerfile
    # runs uvicorn with --no-access-log; propagate=False is a safeguard in
    # case uvicorn is run directly without that flag.
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = []
    access_logger.propagate = False
    structlog.contextvars.bind_contextvars(service=service_name)
