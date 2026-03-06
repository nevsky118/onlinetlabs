import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.config]


class TestGNS3MCPConfig:
    @autotests.num("300")
    @autotests.external_id("a0b1c2d3-e4f5-4a6b-7c8d-9e0f1a2b3c4d")
    @autotests.name("GNS3 MCP Config: создание с defaults")
    def test_defaults(self):
        """Проверяет значения по умолчанию."""

        # Arrange
        from src.config.env_config_loader import EnvConfigLoader

        # Act
        with autotests.step("Создаём конфиг из пустого окружения"):
            config = EnvConfigLoader._build({})

        # Assert
        with autotests.step("Проверяем defaults"):
            assert config.mcp.server_name == "gns3"
            assert config.mcp.transport == "streamable-http"
            assert config.mcp.host == "127.0.0.1"
            assert config.mcp.port == 8100
            assert config.gns3_service_url == "http://localhost:8101"
            assert config.pool.max_size == 50
            assert config.log_buffer.max_entries == 500
            assert config.log_buffer.inactivity_timeout == 300.0

    @autotests.num("301")
    @autotests.external_id("b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e")
    @autotests.name("GNS3 MCP Config: переопределение через env")
    def test_override(self):
        """Проверяет переопределение значений через env."""

        # Arrange
        from src.config.env_config_loader import EnvConfigLoader

        # Act
        with autotests.step("Создаём конфиг с кастомными значениями"):
            config = EnvConfigLoader._build(
                {"MCP_PORT": "9000", "MCP_SERVER_NAME": "gns3-lab"}
            )

        # Assert
        with autotests.step("Проверяем переопределённые значения"):
            assert config.mcp.port == 9000
            assert config.mcp.server_name == "gns3-lab"

    @autotests.num("302")
    @autotests.external_id("c2d3e4f5-a6b7-4c8d-9e0f-1a2b3c4d5e6f")
    @autotests.name("GNS3 MCP Config: невалидный transport")
    def test_invalid_transport(self):
        """Проверяет ошибку при невалидном transport."""

        # Arrange
        from pydantic import ValidationError

        from src.config.env_config_loader import EnvConfigLoader

        # Act & Assert
        with autotests.step("Создаём конфиг с невалидным transport"):
            with pytest.raises(ValidationError):
                EnvConfigLoader._build({"MCP_TRANSPORT": "invalid"})
