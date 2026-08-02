"""Unit tests for activity emit points in chat/router.py."""

from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest

from chat.router import _activity_emit
from observability.models import event_model_selected

pytestmark = [pytest.mark.unit]


@autotest.name("chat: _activity_emit does not raise when activity_log is missing")
def test_activity_emit_safe_without_log():
    # app_state without activity_log should be a no-op, not an exception
    _activity_emit(
        SimpleNamespace(),
        event_model_selected("s1", "u1", model_id="yandex-gpt-5.1", provider="yandex"),
    )


@autotest.name("chat: _activity_emit calls log.emit with the right event")
def test_activity_emit_calls_log():
    calls = []
    state = SimpleNamespace(activity_log=SimpleNamespace(emit=lambda e: calls.append(e)))
    _activity_emit(state, event_model_selected("s1", "u1", model_id="m", provider="p"))
    assert calls, "emit was not called"
    assert calls[0].kind.value == "model_selected"
