"""configure_logging: renderer depends on environment, uvicorn.access neither logs nor propagates."""

import logging

import pytest
import structlog

from observability.logging import configure_logging

pytestmark = [pytest.mark.unit]


def _formatter_renderer():
    root = logging.getLogger()
    formatter = root.handlers[0].formatter
    assert isinstance(formatter, structlog.stdlib.ProcessorFormatter)
    return formatter.processors[-1]


def test_local_environment_uses_console_renderer():
    configure_logging("backend", environment="local")
    assert isinstance(_formatter_renderer(), structlog.dev.ConsoleRenderer)


def test_production_environment_uses_json_renderer():
    configure_logging("backend", environment="production")
    assert isinstance(_formatter_renderer(), structlog.processors.JSONRenderer)


def test_uvicorn_access_logger_does_not_propagate_and_has_no_handlers():
    configure_logging("backend", environment="production")
    access_logger = logging.getLogger("uvicorn.access")
    assert access_logger.propagate is False
    assert access_logger.handlers == []


def test_uvicorn_error_logger_propagates_to_root():
    configure_logging("backend", environment="production")
    error_logger = logging.getLogger("uvicorn.error")
    assert error_logger.propagate is True
    assert error_logger.handlers == []
