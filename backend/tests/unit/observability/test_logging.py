"""configure_logging: renderer depends on environment, uvicorn.access neither logs nor propagates."""

import logging

import pytest
import structlog
from mcp_sdk.testing import autotest

from observability.logging import configure_logging

pytestmark = [pytest.mark.unit]


def _formatter_renderer():
    root = logging.getLogger()
    formatter = root.handlers[0].formatter
    assert isinstance(formatter, structlog.stdlib.ProcessorFormatter)
    return formatter.processors[-1]


@autotest.num("3246")
@autotest.external_id("2450e7aa-9e49-4c79-b84d-3dd3d216824e")
@autotest.name("configure_logging: local environment uses ConsoleRenderer")
def test_2450e7aa_local_environment_uses_console_renderer():
    configure_logging("backend", environment="local")
    assert isinstance(_formatter_renderer(), structlog.dev.ConsoleRenderer)


@autotest.num("3247")
@autotest.external_id("993dd685-5117-4aa6-b985-d40d97ecec4d")
@autotest.name("configure_logging: production environment uses JSONRenderer")
def test_993dd685_production_environment_uses_json_renderer():
    configure_logging("backend", environment="production")
    assert isinstance(_formatter_renderer(), structlog.processors.JSONRenderer)


@autotest.num("3248")
@autotest.external_id("da54d275-5f7c-4770-85fd-208bd6595dd2")
@autotest.name("configure_logging: uvicorn.access does not propagate and has no handlers")
def test_da54d275_uvicorn_access_logger_does_not_propagate_and_has_no_handlers():
    configure_logging("backend", environment="production")
    access_logger = logging.getLogger("uvicorn.access")
    assert access_logger.propagate is False
    assert access_logger.handlers == []


@autotest.num("3249")
@autotest.external_id("069adc85-4d9c-456c-8b70-846f84d4117d")
@autotest.name("configure_logging: uvicorn.error propagates to the root logger")
def test_069adc85_uvicorn_error_logger_propagates_to_root():
    configure_logging("backend", environment="production")
    error_logger = logging.getLogger("uvicorn.error")
    assert error_logger.propagate is True
    assert error_logger.handlers == []
