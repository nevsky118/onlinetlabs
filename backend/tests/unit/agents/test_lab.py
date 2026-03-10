import pytest

from agents.lab.models import LabQueryInput, LabActionInput, LabQueryResult
from agents.lab.tools import LabTools
from agents.lab.agent import LabAgent
from mcp_sdk.models import ActionResult, ComponentDetail
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_greater

pytestmark = [pytest.mark.unit, pytest.mark.agents]


def _make_query_input(**overrides):
    defaults = dict(
        session_id="s1", user_id="u1",
        environment_url="http://localhost:3080",
        project_id="p1", query="show topology",
    )
    return LabQueryInput(**(defaults | overrides))


def _make_action_input(**overrides):
    defaults = dict(
        session_id="s1", user_id="u1",
        environment_url="http://localhost:3080",
        project_id="p1", action_name="restart_node",
        params={"node_id": "n1"},
    )
    return LabActionInput(**(defaults | overrides))


# ---------------------------------------------------------------------------
# LabTools
# ---------------------------------------------------------------------------

class TestLabTools:
    @autotest.num("410")
    @autotest.external_id("agents-lab-tools-get-topology")
    @autotest.name("LabTools.get_topology: возвращает компоненты")
    async def test_get_topology(self, fake_mcp):
        with autotest.step("Вызываем get_topology"):
            tools = LabTools(fake_mcp)
            result = await tools.get_topology(_make_query_input())

        with autotest.step("Проверяем результат"):
            assert_equal(len(result), 1, "должен быть 1 компонент")
            assert_equal(result[0].name, "R1", "имя компонента")
            assert_equal(result[0].status, "running", "статус компонента")

    @autotest.num("411")
    @autotest.external_id("agents-lab-tools-get-component-state")
    @autotest.name("LabTools.get_component_state: возвращает ComponentDetail")
    async def test_get_component_state(self, fake_mcp):
        with autotest.step("Запрашиваем компонент n1"):
            tools = LabTools(fake_mcp)
            result = await tools.get_component_state(_make_query_input(), "n1")

        with autotest.step("Проверяем ComponentDetail"):
            assert_true(isinstance(result, ComponentDetail), f"тип: {type(result)}")
            assert_equal(result.id, "n1", "id компонента")

    @autotest.num("412")
    @autotest.external_id("agents-lab-tools-execute-action")
    @autotest.name("LabTools.execute_action: успешное выполнение")
    async def test_execute_action(self, fake_mcp):
        with autotest.step("Выполняем действие"):
            tools = LabTools(fake_mcp)
            inp = _make_query_input()
            result = await tools.execute_action(inp, "restart_node", {"node_id": "n1"})

        with autotest.step("Проверяем ActionResult"):
            assert_true(isinstance(result, ActionResult), f"тип: {type(result)}")
            assert_true(result.success, "action должен быть успешным")

    @autotest.num("413")
    @autotest.external_id("agents-lab-tools-execute-action-fail")
    @autotest.name("LabTools.execute_action: неуспешное выполнение")
    async def test_execute_action_failure(self, fake_failing_mcp):
        with autotest.step("Выполняем действие с failing client"):
            tools = LabTools(fake_failing_mcp)
            result = await tools.execute_action(_make_query_input(), "restart_node", {"node_id": "n1"})

        with autotest.step("Проверяем что success=False"):
            assert_true(not result.success, "action должен быть неуспешным")

    @autotest.num("414")
    @autotest.external_id("agents-lab-tools-interpret-state")
    @autotest.name("LabTools.interpret_state: текстовое описание компонентов")
    async def test_interpret_state(self, fake_mcp):
        with autotest.step("Получаем компоненты и интерпретируем"):
            tools = LabTools(fake_mcp)
            inp = _make_query_input()
            components = await tools.get_topology(inp)
            result = await tools.interpret_state(inp, components)

        with autotest.step("Проверяем строку"):
            assert_true(isinstance(result, str), f"тип: {type(result)}")
            assert_true("R1" in result, "должен содержать имя компонента")

    @autotest.num("415")
    @autotest.external_id("agents-lab-tools-build-ctx")
    @autotest.name("LabTools._build_ctx: корректный SessionContext")
    def test_build_ctx(self, fake_mcp):
        with autotest.step("Строим контекст"):
            tools = LabTools(fake_mcp)
            inp = _make_query_input()
            ctx = tools._build_ctx(inp)

        with autotest.step("Проверяем поля"):
            assert_equal(ctx.user_id, "u1", "user_id")
            assert_equal(ctx.session_id, "s1", "session_id")
            assert_equal(ctx.environment_url, "http://localhost:3080", "environment_url")


# ---------------------------------------------------------------------------
# LabAgent
# ---------------------------------------------------------------------------

class TestLabAgent:
    @autotest.num("416")
    @autotest.external_id("agents-lab-agent-init")
    @autotest.name("LabAgent: инициализация")
    def test_init(self, config_model, fake_mcp):
        with autotest.step("Создаём LabAgent"):
            agent = LabAgent(config_model, fake_mcp)

        with autotest.step("Проверяем атрибуты"):
            assert_true(agent.tools is not None, "tools не должен быть None")
            assert_equal(agent.config, config_model, "config")

    @autotest.num("417")
    @autotest.external_id("agents-lab-agent-system-prompt")
    @autotest.name("LabAgent: system_prompt содержит роль")
    def test_system_prompt(self, config_model, fake_mcp):
        with autotest.step("Получаем system_prompt"):
            agent = LabAgent(config_model, fake_mcp)
            prompt = agent.system_prompt()

        with autotest.step("Проверяем содержание"):
            assert_true(isinstance(prompt, str), "должна быть строка")
            assert_greater(len(prompt), 10, "prompt должен быть содержательным")

    @autotest.num("418")
    @autotest.external_id("agents-lab-agent-run")
    @autotest.name("LabAgent: run возвращает LabQueryResult")
    async def test_run(self, config_model, fake_mcp):
        with autotest.step("Запускаем run"):
            agent = LabAgent(config_model, fake_mcp)
            result = await agent.run(_make_query_input())

        with autotest.step("Проверяем LabQueryResult"):
            assert_true(isinstance(result, LabQueryResult), f"тип: {type(result)}")
            assert_true(result.success, "должен быть успешным")
            assert_greater(len(result.summary), 0, "summary не пустой")
            assert_equal(len(result.components), 1, "1 компонент")
