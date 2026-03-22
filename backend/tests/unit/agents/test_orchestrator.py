import pytest

from agents.orchestrator.models import OrchestratorInput, OrchestratorResponse
from agents.orchestrator.router import resolve_agent, INTENT_TO_AGENT
from agents.orchestrator.agent import Orchestrator
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_is_none

pytestmark = [pytest.mark.unit, pytest.mark.agents]


def _make_orchestrator_input(**overrides):
    defaults = dict(session_id="s1", user_id="u1", intent="hint", payload={})
    return OrchestratorInput(**(defaults | overrides))


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

    @autotest.num("463")
    @autotest.external_id("d4e5f6a7-b8c9-4dae-8f9a-efa012340004")
    @autotest.name("Orchestrator: run с неизвестным intent")
    async def test_d4e5f6a7_run_unknown_intent(self, config_model, fake_mcp):
        with autotest.step("Запускаем с unknown intent"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp)
            inp = _make_orchestrator_input(intent="unknown")
            result = await orch.run(inp)

        with autotest.step("Проверяем ошибку"):
            assert_true(isinstance(result, OrchestratorResponse), f"тип: {type(result)}")
            assert_true(not result.success, "не должен быть успешным")
            assert_true(result.error is not None, "должна быть ошибка")

    @autotest.num("464")
    @autotest.external_id("d5e6f7a8-b9ca-4dbe-8f9a-efa012340005")
    @autotest.name("Orchestrator: run с intent=hint")
    async def test_d5e6f7a8_run_hint(self, config_model, fake_mcp):
        with autotest.step("Запускаем hint"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp)
            inp = _make_orchestrator_input(
                intent="hint",
                payload={"lab_slug": "lab-1", "step_slug": "step-1", "attempts_count": 2},
            )
            result = await orch.run(inp)

        with autotest.step("Проверяем результат"):
            assert_true(result.success, f"должен быть успешным, error={result.error}")
            assert_equal(result.agent_used, "hint", "agent_used=hint")
            assert_true("hint" in result.data, "data содержит hint")

    @autotest.num("465")
    @autotest.external_id("d6e7f8a9-badb-4dce-8f9a-efa012340006")
    @autotest.name("Orchestrator: run с intent=question")
    async def test_d6e7f8a9_run_question(self, config_model, fake_mcp):
        with autotest.step("Запускаем question"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp)
            inp = _make_orchestrator_input(
                intent="question",
                payload={"question": "Что такое OSPF?"},
            )
            result = await orch.run(inp)

        with autotest.step("Проверяем результат"):
            assert_true(result.success, f"успешно, error={result.error}")
            assert_equal(result.agent_used, "tutor", "agent_used=tutor")
            assert_true("answer" in result.data, "data содержит answer")

    @autotest.num("466")
    @autotest.external_id("d7e8f9aa-bbec-4dde-8f9a-efa012340007")
    @autotest.name("Orchestrator: run с intent=lab")
    async def test_d7e8f9aa_run_lab(self, config_model, fake_mcp):
        with autotest.step("Запускаем lab"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp)
            inp = _make_orchestrator_input(
                intent="lab",
                payload={
                    "environment_url": "http://localhost:3080",
                    "project_id": "p1",
                    "query": "show topology",
                },
            )
            result = await orch.run(inp)

        with autotest.step("Проверяем результат"):
            assert_true(result.success, f"успешно, error={result.error}")
            assert_equal(result.agent_used, "lab", "agent_used=lab")

    @autotest.num("467")
    @autotest.external_id("d8e9faab-bcfd-4dee-8f9a-efa012340008")
    @autotest.name("Orchestrator: run с intent=validate")
    async def test_d8e9faab_run_validate(self, config_model, fake_mcp):
        with autotest.step("Запускаем validate"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp)
            inp = _make_orchestrator_input(
                intent="validate",
                payload={
                    "environment_url": "http://localhost:3080",
                    "project_id": "p1",
                    "lab_slug": "lab-1",
                    "step_slug": "step-1",
                    "criteria": [{"component_id": "n1", "expected_status": "running"}],
                },
            )
            result = await orch.run(inp)

        with autotest.step("Проверяем результат"):
            assert_true(result.success, f"успешно, error={result.error}")
            assert_equal(result.agent_used, "validator", "agent_used=validator")

    @autotest.num("468")
    @autotest.external_id("d9eafbbc-cdae-4dfe-8f9a-efa012340009")
    @autotest.name("Orchestrator: lazy-инициализация агентов")
    async def test_d9eafbbc_lazy_agent_init(self, config_model, fake_mcp):
        with autotest.step("Создаём Orchestrator"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp)
            assert_equal(len(orch._agents), 0, "агентов нет")

        with autotest.step("Запускаем hint"):
            inp = _make_orchestrator_input(
                intent="hint",
                payload={"lab_slug": "lab-1", "step_slug": "step-1"},
            )
            await orch.run(inp)

        with autotest.step("Проверяем что hint агент создан"):
            assert_true("hint" in orch._agents, "hint в кеше")
            assert_equal(len(orch._agents), 1, "только 1 агент")

    @autotest.num("469")
    @autotest.external_id("daebfccd-deef-4e0f-8f9a-efa012340010")
    @autotest.name("Orchestrator: повторный вызов переиспользует агента")
    async def test_daebfccd_agent_reuse(self, config_model, fake_mcp):
        with autotest.step("Два вызова hint"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp)
            inp = _make_orchestrator_input(
                intent="hint",
                payload={"lab_slug": "lab-1", "step_slug": "step-1"},
            )
            await orch.run(inp)
            agent_first = orch._agents.get("hint")
            await orch.run(inp)
            agent_second = orch._agents.get("hint")

        with autotest.step("Проверяем что тот же объект"):
            assert_true(agent_first is agent_second, "должен быть тот же объект")


from agents.orchestrator.models import InterventionInput


class TestOrchestratorIntervene:
    @autotest.num("470")
    @autotest.external_id("c0d1e2f3-a4b5-4c6d-8e7f-a0b1c2d3e4f5")
    @autotest.name("InterventionInput: создание модели")
    def test_c0d1e2f3_intervention_input_model(self):
        with autotest.step("Создаём InterventionInput"):
            inp = InterventionInput(
                session_id="s1", user_id="u1",
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
        with autotest.step("Создаём Orchestrator и InterventionInput"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp, db=None)
            inp = InterventionInput(
                session_id="s1", user_id="u1",
                intervention_type="hint",
                context={"step_slug": "step-1", "attempts_count": 3, "lab_slug": "lab-1"},
            )

        with autotest.step("Вызываем intervene"):
            result = await orch.intervene(inp)

        with autotest.step("Проверяем результат"):
            assert_true(result.success, "success=True")
            assert_equal(result.agent_used, "hint", "агент: hint")
