"""configure_logging: renderer depends on environment, uvicorn.access neither logs nor propagates."""

import logging

import pytest
import structlog
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_instance, assert_true

from observability.logging import configure_logging

pytestmark = [pytest.mark.unit]


def _formatter_renderer():
    root = logging.getLogger()
    formatter = root.handlers[0].formatter
    assert_is_instance(formatter, structlog.stdlib.ProcessorFormatter, "structlog formatter")
    return formatter.processors[-1]


class TestLogging:
    @autotest.num("3246")
    @autotest.external_id("2450e7aa-9e49-4c79-b84d-3dd3d216824e")
    @autotest.name("configure_logging: local environment uses ConsoleRenderer")
    def test_2450e7aa_local_environment_uses_console_renderer(self):
        with autotest.step("Act: configure_logging(environment='local')"):
            configure_logging("backend", environment="local")

        with autotest.step("Assert: root logger's renderer is ConsoleRenderer"):
            assert_true(
                isinstance(_formatter_renderer(), structlog.dev.ConsoleRenderer),
                "console renderer",
            )

    @autotest.num("3247")
    @autotest.external_id("993dd685-5117-4aa6-b985-d40d97ecec4d")
    @autotest.name("configure_logging: production environment uses JSONRenderer")
    def test_993dd685_production_environment_uses_json_renderer(self):
        with autotest.step("Act: configure_logging(environment='production')"):
            configure_logging("backend", environment="production")

        with autotest.step("Assert: root logger's renderer is JSONRenderer"):
            assert_true(
                isinstance(_formatter_renderer(), structlog.processors.JSONRenderer),
                "json renderer",
            )

    @autotest.num("3248")
    @autotest.external_id("da54d275-5f7c-4770-85fd-208bd6595dd2")
    @autotest.name("configure_logging: uvicorn.access does not propagate and has no handlers")
    def test_da54d275_uvicorn_access_logger_does_not_propagate_and_has_no_handlers(self):
        with autotest.step("Act: configure_logging(environment='production')"):
            configure_logging("backend", environment="production")

        with autotest.step("Assert: uvicorn.access does not propagate and has no handlers"):
            access_logger = logging.getLogger("uvicorn.access")
            assert_equal(access_logger.propagate, False, "propagate")
            assert_equal(access_logger.handlers, [], "handlers")

    @autotest.num("3249")
    @autotest.external_id("069adc85-4d9c-456c-8b70-846f84d4117d")
    @autotest.name("configure_logging: uvicorn.error propagates to the root logger")
    def test_069adc85_uvicorn_error_logger_propagates_to_root(self):
        with autotest.step("Act: configure_logging(environment='production')"):
            configure_logging("backend", environment="production")

        with autotest.step(
            "Assert: uvicorn.error propagates to the root logger, no handlers of its own"
        ):
            error_logger = logging.getLogger("uvicorn.error")
            assert_equal(error_logger.propagate, True, "propagate")
            assert_equal(error_logger.handlers, [], "handlers")
