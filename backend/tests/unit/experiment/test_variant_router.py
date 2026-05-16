import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.orchestrator.models import InterventionInput, OrchestratorResponse
from experiment.variant_router import ExperimentVariantRouter

pytestmark = [pytest.mark.unit]


class FakeOrchestrator:
    def __init__(self):
        self.calls = []

    async def intervene(self, input_data: InterventionInput) -> OrchestratorResponse:
        self.calls.append(input_data)
        return OrchestratorResponse(
            agent_used="hint",
            success=True,
            data={"hint": "multi-agent hint"},
        )


class FakeOpenClawAdapter:
    def __init__(self, response: OrchestratorResponse | None = None):
        self.calls = []
        self.response = response or OrchestratorResponse(
            agent_used="openclaw",
            agent_backend="openclaw",
            success=True,
            data={"hint": "openclaw hint"},
        )

    async def generate(self, input_data: InterventionInput) -> OrchestratorResponse:
        self.calls.append(input_data)
        return self.response


def _intervention() -> InterventionInput:
    return InterventionInput(
        session_id="s1",
        user_id="u1",
        intervention_type="hint",
        context={"step_slug": "step-2", "attempts_count": 3},
    )


class TestExperimentVariantRouter:
    @autotest.num("634")
    @autotest.external_id("f55fd650-dff0-4329-b6de-622707876a61")
    @autotest.name("ExperimentVariantRouter: group_a маршрутизируется в multi_agent")
    async def test_f55fd650_group_a_routes_to_multi_agent(self):
        # Arrange
        with autotest.step("Готовим router с fake backend"):
            orchestrator = FakeOrchestrator()
            openclaw = FakeOpenClawAdapter()
            router = ExperimentVariantRouter(orchestrator, openclaw)

        # Act
        with autotest.step("Вызываем интервенцию для group_a"):
            result = await router.route(_intervention(), "group_a")

        # Assert
        with autotest.step("Проверяем multi_agent backend"):
            assert_true(result.success, "ответ успешен")
            assert_equal(result.agent_used, "hint", "agent_used")
            assert_equal(result.agent_backend, "multi_agent", "backend")
            assert_equal(result.metadata["experiment_group"], "group_a", "group")
            assert_equal(len(orchestrator.calls), 1, "orchestrator вызван")
            assert_equal(len(openclaw.calls), 0, "openclaw не вызван")

    @autotest.num("635")
    @autotest.external_id("48fe6a72-8d9a-4da1-8497-78b98ff71792")
    @autotest.name("ExperimentVariantRouter: group_b маршрутизируется в OpenClaw")
    async def test_48fe6a72_group_b_routes_to_openclaw(self):
        # Arrange
        with autotest.step("Готовим router с fake OpenClaw backend"):
            orchestrator = FakeOrchestrator()
            openclaw = FakeOpenClawAdapter()
            router = ExperimentVariantRouter(orchestrator, openclaw)

        # Act
        with autotest.step("Вызываем интервенцию для group_b"):
            result = await router.route(_intervention(), "group_b")

        # Assert
        with autotest.step("Проверяем OpenClaw backend"):
            assert_true(result.success, "ответ успешен")
            assert_equal(result.agent_used, "openclaw", "agent_used")
            assert_equal(result.agent_backend, "openclaw", "backend")
            assert_equal(result.metadata["experiment_group"], "group_b", "group")
            assert_equal(len(orchestrator.calls), 0, "orchestrator не вызван")
            assert_equal(len(openclaw.calls), 1, "openclaw вызван")

    @autotest.num("636")
    @autotest.external_id("9b1c56a4-2e2c-48ce-9d7d-bf1b0dbb66d3")
    @autotest.name("ExperimentVariantRouter: group_b ошибка не вызывает fallback")
    async def test_9b1c56a4_group_b_error_without_fallback(self):
        # Arrange
        with autotest.step("Готовим OpenClaw ошибку"):
            orchestrator = FakeOrchestrator()
            openclaw = FakeOpenClawAdapter(
                OrchestratorResponse(
                    agent_used="openclaw",
                    agent_backend="openclaw",
                    success=False,
                    error="openclaw_timeout: timeout",
                    metadata={"error_code": "openclaw_timeout"},
                )
            )
            router = ExperimentVariantRouter(orchestrator, openclaw)

        # Act
        with autotest.step("Вызываем интервенцию для group_b"):
            result = await router.route(_intervention(), "group_b")

        # Assert
        with autotest.step("Проверяем отсутствие fallback"):
            assert_true(not result.success, "ответ неуспешен")
            assert_equal(result.agent_backend, "openclaw", "backend")
            assert_equal(result.metadata["experiment_group"], "group_b", "group")
            assert_equal(len(orchestrator.calls), 0, "orchestrator не вызван")
            assert_equal(len(openclaw.calls), 1, "openclaw вызван")
