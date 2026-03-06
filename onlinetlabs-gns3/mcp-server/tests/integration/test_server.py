import pytest

from tests.helpers.factories import build_session_context
from tests.helpers.fakes import FakeGNS3ApiClient
from tests.report import autotests

from onlinetlabs_mcp_sdk.errors import ComponentNotFoundError

from src.server import GNS3Server

pytestmark = [pytest.mark.integration, pytest.mark.server]


class TestGNS3ServerAction:
    @pytest.fixture
    def server(self):
        return GNS3Server(api_client=FakeGNS3ApiClient())

    @pytest.fixture
    def ctx(self):
        return build_session_context()

    @autotests.num("355")
    @autotests.external_id("b1c2d3e4-0006-4bbb-cccc-000000000006")
    @autotests.name("GNS3 Server: list_available_actions возвращает каталог")
    async def test_list_available_actions(self, server, ctx):
        with autotests.step("Вызываем list_available_actions"):
            result = await server.list_available_actions(ctx)
        with autotests.step("Проверяем каталог"):
            assert len(result) > 0
            names = [action.name for action in result]
            assert "start_node" in names
            assert "create_link" in names

    @autotests.num("356")
    @autotests.external_id("b1c2d3e4-0007-4bbb-cccc-000000000007")
    @autotests.name("GNS3 Server: execute_action start_node")
    async def test_execute_action(self, server, ctx):
        with autotests.step("Выполняем start_node"):
            result = await server.execute_action(ctx, "start_node", {"node_id": "n1"})
        with autotests.step("Проверяем успех"):
            assert result.success is True

    @autotests.num("357")
    @autotests.external_id("b1c2d3e4-0008-4bbb-cccc-000000000008")
    @autotests.name("GNS3 Server: execute_action unknown → ActionExecutionError")
    async def test_execute_unknown_action(self, server, ctx):
        from onlinetlabs_mcp_sdk.errors import ActionExecutionError
        with autotests.step("Выполняем неизвестное действие"):
            with pytest.raises(ActionExecutionError):
                await server.execute_action(ctx, "nonexistent", {})


class TestGNS3ServerState:
    @pytest.fixture
    def server(self):
        return GNS3Server(api_client=FakeGNS3ApiClient())

    @pytest.fixture
    def ctx(self):
        return build_session_context()

    @autotests.num("350")
    @autotests.external_id("b1c2d3e4-0001-4bbb-cccc-000000000001")
    @autotests.name("GNS3 Server: list_components возвращает nodes + links")
    async def test_list_components_nodes_and_links(self, server, ctx):
        # Act
        with autotests.step("Вызываем list_components"):
            result = await server.list_components(ctx)

        # Assert
        with autotests.step("Проверяем 2 ноды + 1 линк"):
            assert len(result) == 3
            types = [component.type for component in result]
            assert "vpcs" in types
            assert "qemu" in types
            assert "link" in types

    @autotests.num("351")
    @autotests.external_id("b1c2d3e4-0002-4bbb-cccc-000000000002")
    @autotests.name("GNS3 Server: get_component ноды")
    async def test_get_component_node(self, server, ctx):
        # Act
        with autotests.step("Получаем ноду n1"):
            result = await server.get_component(ctx, "n1")

        # Assert
        with autotests.step("Проверяем детали ноды"):
            assert result.id == "n1"
            assert result.type == "vpcs"
            assert "console" in result.properties
            assert "n2" in result.relationships

    @autotests.num("352")
    @autotests.external_id("b1c2d3e4-0003-4bbb-cccc-000000000003")
    @autotests.name("GNS3 Server: get_component линка")
    async def test_get_component_link(self, server, ctx):
        # Act
        with autotests.step("Получаем линк l1"):
            result = await server.get_component(ctx, "l1")

        # Assert
        with autotests.step("Проверяем детали линка"):
            assert result.id == "l1"
            assert result.type == "link"
            assert "n1" in result.relationships
            assert "n2" in result.relationships

    @autotests.num("353")
    @autotests.external_id("b1c2d3e4-0004-4bbb-cccc-000000000004")
    @autotests.name("GNS3 Server: get_component несуществующий → ComponentNotFoundError")
    async def test_get_component_not_found(self, server, ctx):
        # Act & Assert
        with autotests.step("Проверяем ComponentNotFoundError"):
            with pytest.raises(ComponentNotFoundError):
                await server.get_component(ctx, "nonexistent")

    @autotests.num("354")
    @autotests.external_id("b1c2d3e4-0005-4bbb-cccc-000000000005")
    @autotests.name("GNS3 Server: get_system_overview")
    async def test_get_system_overview(self, server, ctx):
        # Act
        with autotests.step("Вызываем get_system_overview"):
            result = await server.get_system_overview(ctx)

        # Assert
        with autotests.step("Проверяем overview"):
            assert result.system_name == "GNS3"
            assert result.system_version == "3.0.0"
            assert result.component_count == 3
