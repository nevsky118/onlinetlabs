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


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class TestRouter:
    @autotest.num("460")
    @autotest.external_id("agents-router-resolve-known")
    @autotest.name("resolve_agent: все известные intents")
    def test_resolve_known_intents(self):
        with autotest.step("Проверяем маппинг"):
            for intent, agent_name in INTENT_TO_AGENT.items():
                result = resolve_agent(intent)
                assert_equal(result, agent_name, f"intent={intent} → {agent_name}")

    @autotest.num("461")
    @autotest.external_id("agents-router-resolve-unknown")
    @autotest.name("resolve_agent: неизвестный intent → None")
    def test_resolve_unknown_intent(self):
        with autotest.step("Проверяем unknown"):
            result = resolve_agent("unknown_intent")
            assert_is_none(result, "неизвестный intent → None")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class TestOrchestrator:
    @autotest.num("462")
    @autotest.external_id("agents-orchestrator-init")
    @autotest.name("Orchestrator: инициализация")
    def test_init(self, config_model, fake_mcp):
        with autotest.step("Создаём Orchestrator"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp, db=None)

        with autotest.step("Проверяем атрибуты"):
            assert_equal(orch.config, config_model, "config")
            assert_equal(orch._agents, {}, "agents пуст")

    @autotest.num("463")
    @autotest.external_id("agents-orchestrator-unknown-intent")
    @autotest.name("Orchestrator: run с неизвестным intent")
    async def test_run_unknown_intent(self, config_model, fake_mcp):
        with autotest.step("Запускаем с unknown intent"):
            orch = Orchestrator(config_model, mcp_client=fake_mcp)
            inp = _make_orchestrator_input(intent="unknown")
            result = await orch.run(inp)

        with autotest.step("Проверяем ошибку"):
            assert_true(isinstance(result, OrchestratorResponse), f"тип: {type(result)}")
            assert_true(not result.success, "не должен быть успешным")
            assert_true(result.error is not None, "должна быть ошибка")

    @autotest.num("464")
    @autotest.external_id("agents-orchestrator-hint-intent")
    @autotest.name("Orchestrator: run с intent=hint")
    async def test_run_hint(self, config_model, fake_mcp):
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
    @autotest.external_id("agents-orchestrator-question-intent")
    @autotest.name("Orchestrator: run с intent=question")
    async def test_run_question(self, config_model, fake_mcp):
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
    @autotest.external_id("agents-orchestrator-lab-intent")
    @autotest.name("Orchestrator: run с intent=lab")
    async def test_run_lab(self, config_model, fake_mcp):
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
    @autotest.external_id("agents-orchestrator-validate-intent")
    @autotest.name("Orchestrator: run с intent=validate")
    async def test_run_validate(self, config_model, fake_mcp):
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
    @autotest.external_id("agents-orchestrator-lazy-init")
    @autotest.name("Orchestrator: lazy-инициализация агентов")
    async def test_lazy_agent_init(self, config_model, fake_mcp):
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
    @autotest.external_id("agents-orchestrator-agent-reuse")
    @autotest.name("Orchestrator: повторный вызов переиспользует агента")
    async def test_agent_reuse(self, config_model, fake_mcp):
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
