"""Unit tests for activity emit points in chat/router.py."""

from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from chat.service import _activity_emit
from observability.schemas import event_model_selected

pytestmark = [pytest.mark.unit]


class TestChatEmits:
    @autotest.num("3222")
    @autotest.external_id("6c748439-1144-4e71-9d79-78182e0b3a86")
    @autotest.name("chat: _activity_emit does not raise when activity_log is missing")
    def test_6c748439_activity_emit_safe_without_log(self):
        with autotest.step(
            "Act+Assert: app_state without activity_log is a no-op, not an exception"
        ):
            # app_state without activity_log should be a no-op, not an exception
            _activity_emit(
                SimpleNamespace(),
                event_model_selected("s1", "u1", model_id="yandex-gpt-5.1", provider="yandex"),
            )

    @autotest.num("3223")
    @autotest.external_id("a293d2bf-4e06-499d-bab3-34c91121787c")
    @autotest.name("chat: _activity_emit calls log.emit with the right event")
    def test_a293d2bf_activity_emit_calls_log(self):
        with autotest.step("Arrange: app_state with an activity_log that records emitted events"):
            calls = []
            state = SimpleNamespace(
                activity_log=SimpleNamespace(emit=lambda value: calls.append(value))
            )

        with autotest.step("Act: _activity_emit"):
            _activity_emit(state, event_model_selected("s1", "u1", model_id="m", provider="p"))

        with autotest.step("Assert: log.emit was called with the model_selected event"):
            assert_true(calls, "emit was not called")
            assert_equal(calls[0].kind.value, "model_selected", "value")
