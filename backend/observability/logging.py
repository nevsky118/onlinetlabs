"""Структурное логирование через structlog с JSON-форматтером."""

import logging
import sys
from contextvars import ContextVar

import structlog

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def _add_request_id(_: object, __: str, event_dict: dict) -> dict:
    """Processor structlog, добавляющий текущий request_id из contextvar в каждую запись лога."""
    event_dict["request_id"] = request_id_ctx.get()
    return event_dict


def configure_logging(service_name: str, level: str = "INFO") -> None:
    """Настраивает structlog и stdlib-логирование на JSON-вывод и пробрасывает логи uvicorn в root."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        _add_request_id,
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
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, level.upper()))
    # Заставляем uvicorn-логгеры пробрасывать в root, иначе JSON-форматтер не применится.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True
    structlog.contextvars.bind_contextvars(service=service_name)
