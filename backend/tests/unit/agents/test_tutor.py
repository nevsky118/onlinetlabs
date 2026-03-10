import pytest

from agents.tutor.models import TutorInput, TutorResponse
from agents.tutor.tools import TutorTools
from agents.tutor.agent import TutorAgent
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_greater

pytestmark = [pytest.mark.unit, pytest.mark.agents]


def _make_tutor_input(**overrides):
    defaults = dict(session_id="s1", user_id="u1", question="Что такое OSPF?")
    return TutorInput(**(defaults | overrides))


# ---------------------------------------------------------------------------
# TutorTools
# ---------------------------------------------------------------------------

class TestTutorTools:
    @autotest.num("440")
    @autotest.external_id("agents-tutor-tools-get-lab-context")
    @autotest.name("TutorTools.get_lab_context: возвращает контекст лабы")
    async def test_get_lab_context(self):
        with autotest.step("Запрашиваем контекст лабы"):
            tools = TutorTools()
            result = await tools.get_lab_context("lab-ospf")

        with autotest.step("Проверяем результат"):
            assert_true(isinstance(result, str), f"тип: {type(result)}")
            assert_true("lab-ospf" in result, "должен содержать slug")

    @autotest.num("441")
    @autotest.external_id("agents-tutor-tools-get-lab-context-empty")
    @autotest.name("TutorTools.get_lab_context: пустой slug")
    async def test_get_lab_context_empty(self):
        with autotest.step("Запрашиваем контекст без slug"):
            tools = TutorTools()
            result = await tools.get_lab_context("")

        with autotest.step("Проверяем пустой результат"):
            assert_equal(result, "", "пустая строка")

    @autotest.num("442")
    @autotest.external_id("agents-tutor-tools-get-step-context")
    @autotest.name("TutorTools.get_step_context: возвращает контекст шага")
    async def test_get_step_context(self):
        with autotest.step("Запрашиваем контекст шага"):
            tools = TutorTools()
            result = await tools.get_step_context("lab-ospf", "step-1")

        with autotest.step("Проверяем результат"):
            assert_true("lab-ospf" in result, "содержит lab slug")
            assert_true("step-1" in result, "содержит step slug")


# ---------------------------------------------------------------------------
# TutorAgent
# ---------------------------------------------------------------------------

class TestTutorAgent:
    @autotest.num("443")
    @autotest.external_id("agents-tutor-agent-init")
    @autotest.name("TutorAgent: инициализация")
    def test_init(self, config_model):
        with autotest.step("Создаём TutorAgent"):
            agent = TutorAgent(config_model)

        with autotest.step("Проверяем атрибуты"):
            assert_true(agent.tools is not None, "tools не None")

    @autotest.num("444")
    @autotest.external_id("agents-tutor-agent-system-prompt")
    @autotest.name("TutorAgent: system_prompt содержит роль наставника")
    def test_system_prompt(self, config_model):
        with autotest.step("Получаем system_prompt"):
            agent = TutorAgent(config_model)
            prompt = agent.system_prompt()

        with autotest.step("Проверяем содержание"):
            assert_true(len(prompt) > 10, "prompt содержательный")

    @autotest.num("445")
    @autotest.external_id("agents-tutor-agent-run-basic")
    @autotest.name("TutorAgent: run обрабатывает вопрос")
    async def test_run_basic(self, config_model):
        with autotest.step("Задаём вопрос"):
            agent = TutorAgent(config_model)
            result = await agent.run(_make_tutor_input())

        with autotest.step("Проверяем TutorResponse"):
            assert_true(isinstance(result, TutorResponse), f"тип: {type(result)}")
            assert_greater(len(result.answer), 0, "ответ не пустой")
            assert_true(isinstance(result.follow_up_questions, list), "follow_up — список")

    @autotest.num("446")
    @autotest.external_id("agents-tutor-agent-run-with-lab")
    @autotest.name("TutorAgent: run с lab_slug включает контекст")
    async def test_run_with_lab_context(self, config_model):
        with autotest.step("Задаём вопрос с lab_slug"):
            agent = TutorAgent(config_model)
            inp = _make_tutor_input(lab_slug="lab-ospf", step_slug="step-1")
            result = await agent.run(inp)

        with autotest.step("Проверяем что контекст включён"):
            assert_true("lab-ospf" in result.answer, "ответ содержит lab slug")
