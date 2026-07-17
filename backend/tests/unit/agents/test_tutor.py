from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_greater, assert_true

from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput, TutorResponse
from agents.tutor.tools import TutorTools

pytestmark = [pytest.mark.unit, pytest.mark.agents]


def _make_tutor_input(**overrides):
    defaults = dict(session_id="s1", user_id="u1", question="Что такое OSPF?")
    return TutorInput(**(defaults | overrides))


# TutorTools


class TestTutorTools:
    @autotest.num("440")
    @autotest.external_id("012b1947-1e8b-4ac8-98db-7721fa40fa92")
    @autotest.name("TutorTools.get_lab_context: возвращает контекст лабы")
    async def test_012b1947_get_lab_context(self):
        with autotest.step("Запрашиваем контекст лабы"):
            tools = TutorTools()
            result = await tools.get_lab_context("lab-ospf")

        with autotest.step("Проверяем результат"):
            assert_true(isinstance(result, str), f"тип: {type(result)}")
            assert_true("lab-ospf" in result, "должен содержать slug")

    @autotest.num("441")
    @autotest.external_id("80f97c81-061f-464a-aa54-50d4ea21dfb0")
    @autotest.name("TutorTools.get_lab_context: пустой slug")
    async def test_80f97c81_get_lab_context_empty(self):
        with autotest.step("Запрашиваем контекст без slug"):
            tools = TutorTools()
            result = await tools.get_lab_context("")

        with autotest.step("Проверяем пустой результат"):
            assert_equal(result, "", "пустая строка")

    @autotest.num("442")
    @autotest.external_id("e2c4f0bb-e610-4560-8a4e-3d813613d72b")
    @autotest.name("TutorTools.get_step_context: возвращает контекст шага")
    async def test_e2c4f0bb_get_step_context(self):
        with autotest.step("Запрашиваем контекст шага"):
            tools = TutorTools()
            result = await tools.get_step_context("lab-ospf", "step-1")

        with autotest.step("Проверяем результат"):
            assert_true("lab-ospf" in result, "содержит lab slug")
            assert_true("step-1" in result, "содержит step slug")


# TutorAgent


class TestTutorAgent:
    @autotest.num("443")
    @autotest.external_id("f12b5351-9f03-49bc-a545-b2d0adfd5a9f")
    @autotest.name("TutorAgent: инициализация")
    def test_f12b5351_init(self, config_model):
        with autotest.step("Создаём TutorAgent"):
            agent = TutorAgent(config_model)

        with autotest.step("Проверяем атрибуты"):
            assert_true(agent.tools is not None, "tools не None")

    @autotest.num("444")
    @autotest.external_id("3303e166-09ff-47f4-b165-1acb1b2c2de5")
    @autotest.name("TutorAgent: system_prompt содержит роль наставника")
    def test_3303e166_system_prompt(self, config_model):
        with autotest.step("Получаем system_prompt"):
            agent = TutorAgent(config_model)
            prompt = agent.system_prompt()

        with autotest.step("Проверяем содержание"):
            assert_true(len(prompt) > 10, "prompt содержательный")

    @autotest.num("445")
    @autotest.external_id("281a56d4-44d9-454f-a974-451001477483")
    @autotest.name("TutorAgent: run возвращает TutorResponse при успешном LLM")
    async def test_281a56d4_run_basic(self, config_model, monkeypatch):
        with autotest.step("Мок LLM и запрос"):
            agent = TutorAgent(config_model)
            fake_result = AsyncMock()
            fake_result.output = "Ответ тьютора"
            monkeypatch.setattr(
                agent, "_agent_for", lambda mid: AsyncMock(run=AsyncMock(return_value=fake_result))
            )
            result = await agent.run(_make_tutor_input())

        with autotest.step("Проверяем TutorResponse"):
            assert_true(isinstance(result, TutorResponse), f"тип: {type(result)}")
            assert_greater(len(result.answer), 0, "ответ не пустой")
            assert_true(isinstance(result.follow_up_questions, list), "follow_up это список")

    @autotest.num("446")
    @autotest.external_id("a7b8c9d0-e1f2-4a3b-4c5d-e6f7a8b9c0d1")
    @autotest.name("TutorAgent: LLM failure re-raise, без шаблона")
    async def test_a7b8c9d0_run_llm_failure_raises(self, config_model, monkeypatch):
        with autotest.step("Мок LLM выбрасывает"):
            agent = TutorAgent(config_model)
            monkeypatch.setattr(
                agent,
                "_agent_for",
                lambda mid: AsyncMock(run=AsyncMock(side_effect=RuntimeError("llm down"))),
            )

        with autotest.step("Ожидаем re-raise"), pytest.raises(Exception):
            await agent.run(_make_tutor_input())
