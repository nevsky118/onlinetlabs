"""Структурное логирование через structlog с JSON- или консольным форматтером."""

import logging
import sys

import structlog

_CONSOLE_ENVIRONMENTS = {"local", "development"}


def configure_logging(
    service_name: str, level: str = "INFO", environment: str = "production"
) -> None:
    """Настраивает structlog и stdlib-логирование, пробрасывает uvicorn.error в root.

    Рендерер зависит от окружения: цветной консольный в local/development,
    JSON — иначе. uvicorn.access не пробрасывается и не пишет: каждый запрос
    уже логирует RequestIDMiddleware одной строкой с request_id и duration.
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
    # uvicorn/uvicorn.error пробрасываем в root, иначе форматтер к ним не применится.
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True
    # uvicorn.access отключаем: с ним каждый запрос логировался бы дважды
    # (свой access-лог + request_handled из RequestIDMiddleware). Dockerfile
    # запускает uvicorn с --no-access-log; propagate=False — страховка на
    # случай прямого запуска uvicorn без этого флага.
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = []
    access_logger.propagate = False
    structlog.contextvars.bind_contextvars(service=service_name)
