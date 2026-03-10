import pytest

from agents.hint.models import HintInput, HintResponse
from agents.hint.tools import HintTools, MAX_HINTS
from agents.hint.agent import HintAgent
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_greater, assert_greater_equal

pytestmark = [pytest.mark.unit, pytest.mark.agents]


def _make_hint_input(**overrides):
    defaults = dict(
        session_id="s1", user_id="u1",
        lab_slug="lab-traceroute", step_slug="step-1",
        attempts_count=0,
    )
    return HintInput(**(defaults | overrides))


# ---------------------------------------------------------------------------
# HintTools
# ---------------------------------------------------------------------------

class TestHintTools:
    @autotest.num("450")
    @autotest.external_id("agents-hint-tools-get-hint-level-low")
    @autotest.name("HintTools.get_hint_level: уровень 1 при малом кол-ве попыток")
    def test_hint_level_low(self):
        with autotest.step("Проверяем уровень при 0-1 попытках"):
            tools = HintTools()
            assert_equal(tools.get_hint_level(0), 1, "0 попыток → уровень 1")
            assert_equal(tools.get_hint_level(1), 1, "1 попытка → уровень 1")

    @autotest.num("451")
    @autotest.external_id("agents-hint-tools-get-hint-level-mid")
    @autotest.name("HintTools.get_hint_level: уровень 2 при 2-3 попытках")
    def test_hint_level_mid(self):
        with autotest.step("Проверяем уровень при 2-3 попытках"):
            tools = HintTools()
            assert_equal(tools.get_hint_level(2), 2, "2 попытки → уровень 2")
            assert_equal(tools.get_hint_level(3), 2, "3 попытки → уровень 2")

    @autotest.num("452")
    @autotest.external_id("agents-hint-tools-get-hint-level-high")
    @autotest.name("HintTools.get_hint_level: уровень 3 при 4+ попытках")
    def test_hint_level_high(self):
        with autotest.step("Проверяем уровень при 4+ попытках"):
            tools = HintTools()
            assert_equal(tools.get_hint_level(4), 3, "4 попытки → уровень 3")
            assert_equal(tools.get_hint_level(10), 3, "10 попыток → уровень 3")

    @autotest.num("453")
    @autotest.external_id("agents-hint-tools-remaining-hints")
    @autotest.name("HintTools.get_remaining_hints: корректный остаток")
    def test_remaining_hints(self):
        with autotest.step("Проверяем остаток подсказок"):
            tools = HintTools()
            assert_equal(tools.get_remaining_hints(1), MAX_HINTS - 1, "уровень 1")
            assert_equal(tools.get_remaining_hints(2), MAX_HINTS - 2, "уровень 2")
            assert_equal(tools.get_remaining_hints(3), 0, "уровень 3 → 0")

    @autotest.num("454")
    @autotest.external_id("agents-hint-tools-generate-hint")
    @autotest.name("HintTools.generate_hint: генерация на каждом уровне")
    def test_generate_hint(self):
        tools = HintTools()

        with autotest.step("Уровень 1"):
            h1 = tools.generate_hint("step-1", 1, None)
            assert_true("уровня 1" in h1, "содержит уровень 1")

        with autotest.step("Уровень 2 с ошибкой"):
            h2 = tools.generate_hint("step-1", 2, "timeout")
            assert_true("уровня 2" in h2, "содержит уровень 2")
            assert_true("timeout" in h2, "содержит ошибку")

        with autotest.step("Уровень 3"):
            h3 = tools.generate_hint("step-1", 3, None)
            assert_true("уровня 3" in h3, "содержит уровень 3")


# ---------------------------------------------------------------------------
# HintAgent
# ---------------------------------------------------------------------------

class TestHintAgent:
    @autotest.num("455")
    @autotest.external_id("agents-hint-agent-init")
    @autotest.name("HintAgent: инициализация")
    def test_init(self, config_model):
        with autotest.step("Создаём HintAgent"):
            agent = HintAgent(config_model)

        with autotest.step("Проверяем атрибуты"):
            assert_true(agent.tools is not None, "tools не None")

    @autotest.num("456")
    @autotest.external_id("agents-hint-agent-system-prompt")
    @autotest.name("HintAgent: system_prompt содержит роль")
    def test_system_prompt(self, config_model):
        with autotest.step("Получаем system_prompt"):
            agent = HintAgent(config_model)
            prompt = agent.system_prompt()

        with autotest.step("Проверяем содержание"):
            assert_true(len(prompt) > 10, "prompt содержательный")

    @autotest.num("457")
    @autotest.external_id("agents-hint-agent-run-level1")
    @autotest.name("HintAgent: run возвращает подсказку уровня 1")
    async def test_run_level1(self, config_model):
        with autotest.step("Запрашиваем подсказку при 0 попытках"):
            agent = HintAgent(config_model)
            result = await agent.run(_make_hint_input(attempts_count=0))

        with autotest.step("Проверяем HintResponse"):
            assert_true(isinstance(result, HintResponse), f"тип: {type(result)}")
            assert_equal(result.hint_level, 1, "уровень 1")
            assert_greater(result.remaining_hints, 0, "есть ещё подсказки")

    @autotest.num("458")
    @autotest.external_id("agents-hint-agent-run-level3")
    @autotest.name("HintAgent: run возвращает подсказку уровня 3")
    async def test_run_level3(self, config_model):
        with autotest.step("Запрашиваем подсказку при 5 попытках"):
            agent = HintAgent(config_model)
            result = await agent.run(_make_hint_input(attempts_count=5, last_error="timeout"))

        with autotest.step("Проверяем HintResponse"):
            assert_equal(result.hint_level, 3, "уровень 3")
            assert_equal(result.remaining_hints, 0, "подсказок не осталось")
            assert_true("timeout" in result.hint, "содержит ошибку")
