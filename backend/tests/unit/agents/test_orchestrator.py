from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from agents.hint.models import HintResponse
from agents.orchestrator.agent import Orchestrator
from agents.orchestrator.router import INTENT_TO_AGENT, resolve_agent


def _mock_hint_agent(orch):
    """Возвращает HintResponse без LLM-вызова."""
    fake = AsyncMock()
    fake.run = AsyncMock(
        return_value=HintResponse(hint="подсказка", hint_level=2, remaining_hints=1)
    )
    orch._agents["hint"] = fake


pytestmark = [pytest.mark.unit, pytest.mark.agents]


# Router


class TestRouter:
    @autotest.num("460")
    @autotest.external_id("d1e2f3a4-b5c6-4d7e-8f9a-efa012340001")
    @autotest.name("resolve_agent: все известные intents")
    def test_d1e2f3a4_resolve_known_intents(self):
        with autotest.step("Проверяем маппинг"):
            for intent, agent_name in INTENT_TO_AGENT.items():
                result = resolve_agent(intent)
                assert_equal(result, agent_name, f"intent={intent} → {agent_name}")

    @autotest.num("461")
    @autotest.external_id("d2e3f4a5-b6c7-4d8e-8f9a-efa012340002")
    @autotest.name("resolve_agent: неизвестный intent → None")
    def test_d2e3f4a5_resolve_unknown_intent(self):
        with autotest.step("Проверяем unknown"):
            result = resolve_agent("unknown_intent")
            assert_is_none(result, "неизвестный intent → None")


# Orchestrator


class TestOrchestrator:
    @autotest.num("462")
    @autotest.external_id("d3e4f5a6-b7c8-4d9e-8f9a-efa012340003")
    @autotest.name("Orchestrator: инициализация")
    def test_d3e4f5a6_init(self, config_model, fake_mcp):
        with autotest.step("Создаём Orchestrator"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp, db=None)

        with autotest.step("Проверяем атрибуты"):
            assert_equal(orch.config, config_model, "config")
            assert_equal(orch._agents, {}, "agents пуст")


from agents.orchestrator.models import InterventionInput


class TestOrchestratorIntervene:
    @autotest.num("470")
    @autotest.external_id("c0d1e2f3-a4b5-4c6d-8e7f-a0b1c2d3e4f5")
    @autotest.name("InterventionInput: создание модели")
    def test_c0d1e2f3_intervention_input_model(self):
        with autotest.step("Создаём InterventionInput"):
            inp = InterventionInput(
                session_id="s1",
                user_id="u1",
                intervention_type="hint",
                context={"struggle_type": "repeating_errors", "dominant_error": "bad ip"},
            )

        with autotest.step("Проверяем поля"):
            assert_equal(inp.intervention_type, "hint", "тип интервенции")
            assert_equal(inp.session_id, "s1", "session_id")

    @autotest.num("471")
    @autotest.external_id("d1e2f3a4-b5c6-4d7e-9f8a-b0c1d2e3f4a5")
    @autotest.name("Orchestrator.intervene: маршрутизация к hint агенту")
    async def test_d1e2f3a4_intervene_routes_to_hint(self, config_model, fake_mcp):
        with autotest.step("Создаём Orchestrator и InterventionInput с мок-агентом"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp, db=None)
            _mock_hint_agent(orch)
            inp = InterventionInput(
                session_id="s1",
                user_id="u1",
                intervention_type="hint",
                context={"step_slug": "step-1", "attempts_count": 3, "lab_slug": "lab-1"},
            )

        with autotest.step("Вызываем intervene"):
            result = await orch.intervene(inp)

        with autotest.step("Проверяем результат"):
            assert_true(result.success, "success=True")
            assert_equal(result.agent_used, "hint", "агент: hint")
