import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_not_none, assert_true

from observability.schemas import (
    ActivityKind,
    ActivitySource,
    event_model_selected,
    event_struggle_detected,
    event_tool_call,
)

pytestmark = [pytest.mark.unit]


class TestModels:
    @autotest.num("300")
    @autotest.external_id("d8f8a39f-ecb0-451c-bd04-42a14c6862e3")
    @autotest.name("struggle_detected: event shape has the right fields")
    def test_d8f8a39f_struggle_event_shape(self):
        with autotest.step("Create a struggle event"):
            event = event_struggle_detected(
                "s1",
                "u1",
                struggle_type="repeating_errors",
                confidence=0.8,
                crossed=["error_repeat_count>=3"],
            )
        with autotest.step("Check source and kind"):
            assert_equal(event.source, ActivitySource.INTERVENTION, "source")
            assert_equal(event.kind, ActivityKind.STRUGGLE_DETECTED, "kind")
        with autotest.step("Check agent"):
            assert_equal(event.agent, "analytics", "agent")
        with autotest.step("Check summary for Russian/English text"):
            assert_true(
                "повтор" in event.summary.lower() or "repeating" in event.summary.lower(),
                "summary names the repetition",
            )
        with autotest.step("Check detail"):
            assert_equal(event.detail["confidence"], 0.8, "confidence")
        with autotest.step("Check auto-generated fields"):
            assert_true(event.id, "id")
            assert_is_not_none(event.ts, "ts")

    @autotest.num("301")
    @autotest.external_id("ed2c4224-35bd-474c-a129-f3bdc9bcaee4")
    @autotest.name("model_selected: model selection event")
    def test_ed2c4224_model_selected_event_shape(self):
        with autotest.step("Create a model selection event"):
            event = event_model_selected("s1", "u1", model_id="yandex-gpt-5.1", provider="yandex")
        with autotest.step("Check source and kind"):
            assert_equal(event.source, ActivitySource.CHAT, "source")
            assert_equal(event.kind, ActivityKind.MODEL_SELECTED, "kind")
        with autotest.step("Check summary and detail"):
            assert_true(event.summary, "summary")
            assert_equal(event.detail["model_id"], "yandex-gpt-5.1", "model id")
            assert_equal(event.detail["provider"], "yandex", "provider")

    @autotest.num("302")
    @autotest.external_id("3d9406cb-c4ac-495d-9bd8-2b74fc1736fc")
    @autotest.name("tool_call: tool call event")
    def test_3d9406cb_tool_call_event_shape(self):
        with autotest.step("Create a tool call event"):
            event = event_tool_call(
                "s1", "u1", name="gns3_get_nodes", args_preview='{"project_id": "abc"}'
            )
        with autotest.step("Check source and kind"):
            assert_equal(event.source, ActivitySource.CHAT, "source")
            assert_equal(event.kind, ActivityKind.TOOL_CALL, "kind")
        with autotest.step("Check summary and detail"):
            assert_true(event.summary, "summary")
            assert_equal(event.detail["name"], "gns3_get_nodes", "name")
            assert_true(event.detail["args_preview"], "args preview")
