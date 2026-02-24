from datetime import datetime, timezone

import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.models]


class TestComponent:
    @autotests.num("100")
    @autotests.external_id("73171621-43e7-4651-83b2-68857ed14599")
    @autotests.name("MCP SDK Models: создание Component с валидными данными")
    def test_create_valid(self):
        """Проверяет создание Component с валидными данными."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import Component

        # Act
        with autotests.step("Создаём Component"):
            c = Component(
                id="node-1",
                name="Router1",
                type="router",
                status="running",
                summary="Core router",
            )

        # Assert
        with autotests.step("Проверяем поля"):
            assert c.id == "node-1"
            assert c.type == "router"

    @autotests.num("101")
    @autotests.external_id("16a5444b-0ad4-4cf1-971e-d7ebc9b3be7a")
    @autotests.name(
        "MCP SDK Models: ошибка при отсутствии обязательного поля Component"
    )
    def test_missing_required_field(self):
        """Проверяет ValidationError при отсутствии обязательных полей."""

        # Arrange
        from pydantic import ValidationError

        from onlinetlabs_mcp_sdk.models import Component

        # Act & Assert
        with autotests.step("Создаём Component без обязательных полей"):
            with pytest.raises(ValidationError):
                Component(id="node-1", name="Router1")


class TestComponentDetail:
    @autotests.num("102")
    @autotests.external_id("164f6acb-e497-4b2a-b1c4-76e6ab7d7263")
    @autotests.name("MCP SDK Models: ComponentDetail наследует Component")
    def test_inherits_component(self):
        """Проверяет наследование и дополнительные поля ComponentDetail."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import ComponentDetail

        # Act
        with autotests.step("Создаём ComponentDetail"):
            cd = ComponentDetail(
                id="node-1",
                name="Router1",
                type="router",
                status="running",
                summary="Core router",
                properties={"cpu": 2, "ram": "512MB"},
                configuration="hostname Router1\ninterface eth0",
                relationships=["node-2"],
            )

        # Assert
        with autotests.step("Проверяем дополнительные поля"):
            assert cd.properties["cpu"] == 2
            assert cd.configuration.startswith("hostname")
            assert "node-2" in cd.relationships

    @autotests.num("103")
    @autotests.external_id("52b1ad7b-e0d3-408e-af8a-dcf8640a83df")
    @autotests.name("MCP SDK Models: опциональные поля ComponentDetail по умолчанию")
    def test_optional_fields_default(self):
        """Проверяет значения по умолчанию опциональных полей."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import ComponentDetail

        # Act
        with autotests.step("Создаём ComponentDetail без configuration"):
            cd = ComponentDetail(
                id="x",
                name="x",
                type="x",
                status="x",
                summary="x",
                properties={},
                relationships=[],
            )

        # Assert
        with autotests.step("Проверяем значение по умолчанию"):
            assert cd.configuration is None


class TestSystemOverview:
    @autotests.num("104")
    @autotests.external_id("51d3db92-7cad-4039-869d-41cb42ac9cc0")
    @autotests.name("MCP SDK Models: создание SystemOverview с валидными данными")
    def test_create_valid(self):
        """Проверяет создание SystemOverview."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import SystemOverview

        # Act
        with autotests.step("Создаём SystemOverview"):
            so = SystemOverview(
                system_name="GNS3",
                system_version="2.2.44",
                component_count=5,
                components_by_type={"router": 3, "switch": 2},
                components_by_status={"running": 4, "stopped": 1},
                summary="5 devices, 4 running",
            )

        # Assert
        with autotests.step("Проверяем component_count"):
            assert so.component_count == 5


class TestErrorEntry:
    @autotests.num("105")
    @autotests.external_id("a864c09f-bcda-43c9-b175-c90ba365ebbf")
    @autotests.name("MCP SDK Models: создание ErrorEntry с валидными данными")
    def test_create_valid(self):
        """Проверяет создание ErrorEntry."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import ErrorEntry, LogLevel

        # Act
        with autotests.step("Создаём ErrorEntry"):
            e = ErrorEntry(
                timestamp=datetime.now(tz=timezone.utc),
                level=LogLevel.ERROR,
                component_id="node-1",
                message="Interface down",
                details=None,
            )

        # Assert
        with autotests.step("Проверяем уровень ошибки"):
            assert e.level == LogLevel.ERROR


class TestLogLevel:
    @autotests.num("106")
    @autotests.external_id("b43a0ae6-c88e-4e0d-807e-a106acce87c1")
    @autotests.name("MCP SDK Models: все уровни LogLevel существуют")
    def test_all_levels_exist(self):
        """Проверяет наличие всех уровней логирования."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import LogLevel

        # Assert
        with autotests.step("Проверяем все уровни"):
            assert LogLevel.DEBUG
            assert LogLevel.INFO
            assert LogLevel.WARNING
            assert LogLevel.ERROR
            assert LogLevel.ALL


class TestUserAction:
    @autotests.num("107")
    @autotests.external_id("0ba71a32-d491-41c5-84f6-7aaaab262818")
    @autotests.name("MCP SDK Models: создание UserAction с валидными данными")
    def test_create_valid(self):
        """Проверяет создание UserAction."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import UserAction

        # Act
        with autotests.step("Создаём UserAction"):
            ua = UserAction(
                timestamp=datetime.now(tz=timezone.utc),
                component_id="node-1",
                action="configured_interface",
                raw_command="ip address 10.0.0.1 255.255.255.0",
                success=True,
            )

        # Assert
        with autotests.step("Проверяем поля"):
            assert ua.success is True
            assert ua.raw_command is not None


class TestActionSpec:
    @autotests.num("108")
    @autotests.external_id("2aa3748a-1791-40c4-8205-0442206e0329")
    @autotests.name("MCP SDK Models: создание ActionSpec с валидными данными")
    def test_create_valid(self):
        """Проверяет создание ActionSpec."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import ActionSpec

        # Act
        with autotests.step("Создаём ActionSpec"):
            a = ActionSpec(
                name="restart_node",
                description="Перезапуск узла",
                parameters={
                    "type": "object",
                    "properties": {"node_id": {"type": "string"}},
                },
                component_types=["router", "switch"],
            )

        # Assert
        with autotests.step("Проверяем поля"):
            assert a.name == "restart_node"
            assert "node_id" in a.parameters["properties"]


class TestActionResult:
    @autotests.num("109")
    @autotests.external_id("d27eec1d-0ac7-4f2f-a55d-53a5583d4619")
    @autotests.name("MCP SDK Models: создание ActionResult с валидными данными")
    def test_create_valid(self):
        """Проверяет создание ActionResult."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import ActionResult

        # Act
        with autotests.step("Создаём ActionResult"):
            r = ActionResult(success=True, message="Node restarted", output="OK")

        # Assert
        with autotests.step("Проверяем success"):
            assert r.success is True

    @autotests.num("110")
    @autotests.external_id("eaa8b374-2cac-4099-bf31-729fa7e6db9a")
    @autotests.name("MCP SDK Models: output в ActionResult опционален")
    def test_output_optional(self):
        """Проверяет что output — опциональное поле."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import ActionResult

        # Act
        with autotests.step("Создаём ActionResult без output"):
            r = ActionResult(success=False, message="Failed")

        # Assert
        with autotests.step("Проверяем output = None"):
            assert r.output is None


class TestLogEntry:
    @autotests.num("111")
    @autotests.external_id("aa730ae8-7951-4bb9-b22b-fcb05346e49a")
    @autotests.name("MCP SDK Models: создание LogEntry с валидными данными")
    def test_create_valid(self):
        """Проверяет создание LogEntry."""

        # Arrange
        from onlinetlabs_mcp_sdk.models import LogEntry, LogLevel

        # Act
        with autotests.step("Создаём LogEntry"):
            le = LogEntry(
                timestamp=datetime.now(tz=timezone.utc),
                level=LogLevel.INFO,
                source="system",
                message="Started",
            )

        # Assert
        with autotests.step("Проверяем source"):
            assert le.source == "system"
