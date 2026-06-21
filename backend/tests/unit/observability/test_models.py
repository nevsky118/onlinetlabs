import pytest

from observability.models import (
    AgentActivityEvent,
    ActivitySource,
    ActivityKind,
    event_struggle_detected,
    event_model_selected,
    event_tool_call,
)
from mcp_sdk.testing import autotest

pytestmark = [pytest.mark.unit]


@autotest.num("300")
@autotest.external_id("c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f")
@autotest.name("struggle_detected: форма события с правильными полями")
def test_struggle_event_shape():
    with autotest.step("Создаём событие затруднения"):
        e = event_struggle_detected(
            "s1", "u1", struggle_type="repeating_errors", confidence=0.8, crossed=["error_repeat_count>=3"]
        )
    with autotest.step("Проверяем source и kind"):
        assert e.source == ActivitySource.INTERVENTION
        assert e.kind == ActivityKind.STRUGGLE_DETECTED
    with autotest.step("Проверяем agent"):
        assert e.agent == "analytics"
    with autotest.step("Проверяем summary на русский/английский текст"):
        assert "повтор" in e.summary.lower() or "repeating" in e.summary.lower()
    with autotest.step("Проверяем detail"):
        assert e.detail["confidence"] == 0.8
    with autotest.step("Проверяем автогенерированные поля"):
        assert e.id
        assert e.ts is not None


@autotest.num("301")
@autotest.external_id("d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a")
@autotest.name("model_selected: событие выбора модели")
def test_model_selected_event_shape():
    with autotest.step("Создаём событие выбора модели"):
        e = event_model_selected("s1", "u1", model_id="yandex-gpt-5.1", provider="yandex")
    with autotest.step("Проверяем source и kind"):
        assert e.source == ActivitySource.CHAT
        assert e.kind == ActivityKind.MODEL_SELECTED
    with autotest.step("Проверяем summary и detail"):
        assert e.summary
        assert e.detail["model_id"] == "yandex-gpt-5.1"
        assert e.detail["provider"] == "yandex"


@autotest.num("302")
@autotest.external_id("e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b")
@autotest.name("tool_call: событие вызова инструмента")
def test_tool_call_event_shape():
    with autotest.step("Создаём событие вызова инструмента"):
        e = event_tool_call("s1", "u1", name="gns3_get_nodes", args_preview='{"project_id": "abc"}')
    with autotest.step("Проверяем source и kind"):
        assert e.source == ActivitySource.CHAT
        assert e.kind == ActivityKind.TOOL_CALL
    with autotest.step("Проверяем summary и detail"):
        assert e.summary
        assert e.detail["name"] == "gns3_get_nodes"
        assert e.detail["args_preview"]
