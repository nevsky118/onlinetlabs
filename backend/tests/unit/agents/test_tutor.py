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


# TutorTools

class TestTutorTools:
    @autotest.num("440")
    @autotest.external_id("a1b2c3d4-e5f6-4a7b-8c9d-e0f1a2b3c4d5")
    @autotest.name("TutorTools.get_lab_context: возвращает контекст лабы")
    async def test_a1b2c3d4_get_lab_context(self):
        with autotest.step("Запрашиваем контекст лабы"):
            tools = TutorTools()
            result = await tools.get_lab_context("lab-ospf")

        with autotest.step("Проверяем результат"):
            assert_true(isinstance(result, str), f"тип: {type(result)}")
            assert_true("lab-ospf" in result, "должен содержать slug")

    @autotest.num("441")
    @autotest.external_id("b2c3d4e5-f6a7-4b8c-9d0e-f1a2b3c4d5e6")
    @autotest.name("TutorTools.get_lab_context: пустой slug")
    async def test_b2c3d4e5_get_lab_context_empty(self):
        with autotest.step("Запрашиваем контекст без slug"):
            tools = TutorTools()
            result = await tools.get_lab_context("")

        with autotest.step("Проверяем пустой результат"):
            assert_equal(result, "", "пустая строка")

    @autotest.num("442")
    @autotest.external_id("c3d4e5f6-a7b8-4c9d-0e1f-a2b3c4d5e6f7")
    @autotest.name("TutorTools.get_step_context: возвращает контекст шага")
    async def test_c3d4e5f6_get_step_context(self):
        with autotest.step("Запрашиваем контекст шага"):
            tools = TutorTools()
            result = await tools.get_step_context("lab-ospf", "step-1")

        with autotest.step("Проверяем результат"):
            assert_true("lab-ospf" in result, "содержит lab slug")
            assert_true("step-1" in result, "содержит step slug")


# TutorAgent

class TestTutorAgent:
    @autotest.num("443")
    @autotest.external_id("d4e5f6a7-b8c9-4d0e-1f2a-b3c4d5e6f7a8")
    @autotest.name("TutorAgent: инициализация")
    def test_d4e5f6a7_init(self, config_model):
        with autotest.step("Создаём TutorAgent"):
            agent = TutorAgent(config_model)

        with autotest.step("Проверяем атрибуты"):
            assert_true(agent.tools is not None, "tools не None")

    @autotest.num("444")
    @autotest.external_id("e5f6a7b8-c9d0-4e1f-2a3b-c4d5e6f7a8b9")
    @autotest.name("TutorAgent: system_prompt содержит роль наставника")
    def test_e5f6a7b8_system_prompt(self, config_model):
        with autotest.step("Получаем system_prompt"):
            agent = TutorAgent(config_model)
            prompt = agent.system_prompt()

        with autotest.step("Проверяем содержание"):
            assert_true(len(prompt) > 10, "prompt содержательный")

    @autotest.num("445")
    @autotest.external_id("f6a7b8c9-d0e1-4f2a-3b4c-d5e6f7a8b9c0")
    @autotest.name("TutorAgent: run обрабатывает вопрос")
    async def test_f6a7b8c9_run_basic(self, config_model):
        with autotest.step("Задаём вопрос"):
            agent = TutorAgent(config_model)
            result = await agent.run(_make_tutor_input())

        with autotest.step("Проверяем TutorResponse"):
            assert_true(isinstance(result, TutorResponse), f"тип: {type(result)}")
            assert_greater(len(result.answer), 0, "ответ не пустой")
            assert_true(isinstance(result.follow_up_questions, list), "follow_up — список")

    @autotest.num("446")
    @autotest.external_id("a7b8c9d0-e1f2-4a3b-4c5d-e6f7a8b9c0d1")
    @autotest.name("TutorAgent: run с lab_slug включает контекст")
    async def test_a7b8c9d0_run_with_lab_context(self, config_model):
        with autotest.step("Задаём вопрос с lab_slug"):
            agent = TutorAgent(config_model)
            inp = _make_tutor_input(lab_slug="lab-ospf", step_slug="step-1")
            result = await agent.run(inp)

        with autotest.step("Проверяем что контекст включён"):
            assert_true("lab-ospf" in result.answer, "ответ содержит lab slug")
