import pytest

from agents.validator.models import CheckResult, ValidationInput, ValidationResult
from agents.validator.tools import ValidatorTools
from agents.validator.agent import ValidatorAgent
from mcp_sdk.models import Component
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_less

pytestmark = [pytest.mark.unit, pytest.mark.agents]


def _make_validation_input(**overrides):
    defaults = dict(
        session_id="s1", user_id="u1",
        environment_url="http://localhost:3080",
        project_id="p1", lab_slug="lab-traceroute",
        step_slug="step-1",
        criteria=[{"component_id": "n1", "expected_status": "running"}],
    )
    return ValidationInput(**(defaults | overrides))


# ValidatorTools

class TestValidatorTools:
    @autotest.num("420")
    @autotest.external_id("b1c2d3e4-f5a6-4b7c-8d9e-abc012340001")
    @autotest.name("ValidatorTools.get_current_state: возвращает компоненты")
    async def test_b1c2d3e4_get_current_state(self, fake_mcp):
        with autotest.step("Вызываем get_current_state"):
            tools = ValidatorTools(fake_mcp)
            result = await tools.get_current_state(_make_validation_input())

        with autotest.step("Проверяем результат"):
            assert_equal(len(result), 1, "1 компонент")
            assert_true(isinstance(result[0], Component), f"тип: {type(result[0])}")

    @autotest.num("421")
    @autotest.external_id("b2c3d4e5-f6a7-4b8c-8d9e-abc012340002")
    @autotest.name("ValidatorTools.check_component_status: статус совпадает")
    async def test_b2c3d4e5_check_component_status_pass(self, fake_mcp):
        with autotest.step("Проверяем running для n1"):
            tools = ValidatorTools(fake_mcp)
            result = await tools.check_component_status(_make_validation_input(), "n1", "running")

        with autotest.step("Проверяем CheckResult"):
            assert_true(isinstance(result, CheckResult), f"тип: {type(result)}")
            assert_true(result.passed, "должен пройти")
            assert_equal(result.expected, "running", "expected")
            assert_equal(result.actual, "running", "actual")

    @autotest.num("422")
    @autotest.external_id("b3c4d5e6-f7a8-4b9c-8d9e-abc012340003")
    @autotest.name("ValidatorTools.check_component_status: статус не совпадает")
    async def test_b3c4d5e6_check_component_status_fail(self, fake_mcp):
        with autotest.step("Проверяем stopped для n1 (он running)"):
            tools = ValidatorTools(fake_mcp)
            result = await tools.check_component_status(_make_validation_input(), "n1", "stopped")

        with autotest.step("Проверяем CheckResult"):
            assert_true(not result.passed, "не должен пройти")
            assert_equal(result.expected, "stopped", "expected")
            assert_equal(result.actual, "running", "actual")

    @autotest.num("423")
    @autotest.external_id("b4c5d6e7-f8a9-4bac-8d9e-abc012340004")
    @autotest.name("ValidatorTools.check_connectivity: проверка связности")
    async def test_b4c5d6e7_check_connectivity(self, fake_mcp):
        with autotest.step("Проверяем связность n1 → n1"):
            tools = ValidatorTools(fake_mcp)
            result = await tools.check_connectivity(_make_validation_input(), "n1", "n1")

        with autotest.step("Проверяем CheckResult"):
            assert_true(isinstance(result, CheckResult), f"тип: {type(result)}")
            # FakeMCPClient returns relationships=[], so not connected
            assert_true(not result.passed, "нет связей в fake")


# ValidatorAgent

class TestValidatorAgent:
    @autotest.num("425")
    @autotest.external_id("b5c6d7e8-f9aa-4bbc-8d9e-abc012340005")
    @autotest.name("ValidatorAgent: инициализация")
    def test_b5c6d7e8_init(self, config_model, fake_mcp):
        with autotest.step("Создаём ValidatorAgent"):
            agent = ValidatorAgent(config_model, fake_mcp)

        with autotest.step("Проверяем атрибуты"):
            assert_true(agent.tools is not None, "tools не None")

    @autotest.num("426")
    @autotest.external_id("b6c7d8e9-faab-4bcc-8d9e-abc012340006")
    @autotest.name("ValidatorAgent: system_prompt содержит роль")
    def test_b6c7d8e9_system_prompt(self, config_model, fake_mcp):
        with autotest.step("Получаем system_prompt"):
            agent = ValidatorAgent(config_model, fake_mcp)
            prompt = agent.system_prompt()

        with autotest.step("Проверяем содержание"):
            assert_true(len(prompt) > 10, "prompt содержательный")

    @autotest.num("427")
    @autotest.external_id("b7c8d9ea-fbbc-4bdc-8d9e-abc012340007")
    @autotest.name("ValidatorAgent: run с проходящими проверками")
    async def test_b7c8d9ea_run_pass(self, config_model, fake_mcp):
        with autotest.step("Запускаем run с expected=running"):
            agent = ValidatorAgent(config_model, fake_mcp)
            inp = _make_validation_input(
                criteria=[{"component_id": "n1", "expected_status": "running"}]
            )
            result = await agent.run(inp)

        with autotest.step("Проверяем ValidationResult"):
            assert_true(isinstance(result, ValidationResult), f"тип: {type(result)}")
            assert_true(result.passed, "должен пройти")
            assert_equal(result.score, 100.0, "оценка 100")
            assert_equal(len(result.checks), 1, "1 проверка")

    @autotest.num("428")
    @autotest.external_id("b8c9daeb-fccd-4bec-8d9e-abc012340008")
    @autotest.name("ValidatorAgent: run с непроходящими проверками")
    async def test_b8c9daeb_run_fail(self, config_model, fake_mcp):
        with autotest.step("Запускаем run с expected=stopped"):
            agent = ValidatorAgent(config_model, fake_mcp)
            inp = _make_validation_input(
                criteria=[{"component_id": "n1", "expected_status": "stopped"}]
            )
            result = await agent.run(inp)

        with autotest.step("Проверяем ValidationResult"):
            assert_true(not result.passed, "не должен пройти")
            assert_less(result.score, 100.0, "оценка < 100")

    @autotest.num("429")
    @autotest.external_id("b9cadbfc-fdde-4bfc-8d9e-abc012340009")
    @autotest.name("ValidatorAgent: run с частичным прохождением")
    async def test_b9cadbfc_run_mixed(self, config_model):
        from tests.unit.conftest import FakeMCPClient
        from mcp_sdk.models import Component

        with autotest.step("Создаём среду с двумя компонентами"):
            mcp = FakeMCPClient(components=[
                Component(id="n1", name="R1", type="router", status="running", summary="R1"),
                Component(id="n2", name="R2", type="router", status="stopped", summary="R2"),
            ])
            agent = ValidatorAgent(config_model, mcp)
            inp = _make_validation_input(criteria=[
                {"component_id": "n1", "expected_status": "running"},
                {"component_id": "n2", "expected_status": "running"},
            ])

        with autotest.step("Запускаем run"):
            result = await agent.run(inp)

        with autotest.step("Проверяем частичный результат"):
            assert_true(not result.passed, "не все прошли")
            assert_equal(result.score, 50.0, "1/2 = 50%")
            assert_equal(len(result.checks), 2, "2 проверки")
