import pytest
from mcp_sdk.testing import autotest

from observability.models import (
    ActivityKind,
    ActivitySource,
    event_model_selected,
    event_struggle_detected,
    event_tool_call,
)

pytestmark = [pytest.mark.unit]


@autotest.num("300")
@autotest.external_id("d8f8a39f-ecb0-451c-bd04-42a14c6862e3")
@autotest.name("struggle_detected: форма события с правильными полями")
def test_d8f8a39f_struggle_event_shape():
    with autotest.step("Создаём событие затруднения"):
        e = event_struggle_detected(
            "s1",
            "u1",
            struggle_type="repeating_errors",
            confidence=0.8,
            crossed=["error_repeat_count>=3"],
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
@autotest.external_id("ed2c4224-35bd-474c-a129-f3bdc9bcaee4")
@autotest.name("model_selected: событие выбора модели")
def test_ed2c4224_model_selected_event_shape():
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
@autotest.external_id("3d9406cb-c4ac-495d-9bd8-2b74fc1736fc")
@autotest.name("tool_call: событие вызова инструмента")
def test_3d9406cb_tool_call_event_shape():
    with autotest.step("Создаём событие вызова инструмента"):
        e = event_tool_call("s1", "u1", name="gns3_get_nodes", args_preview='{"project_id": "abc"}')
    with autotest.step("Проверяем source и kind"):
        assert e.source == ActivitySource.CHAT
        assert e.kind == ActivityKind.TOOL_CALL
    with autotest.step("Проверяем summary и detail"):
        assert e.summary
        assert e.detail["name"] == "gns3_get_nodes"
        assert e.detail["args_preview"]
