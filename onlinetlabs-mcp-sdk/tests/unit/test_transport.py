import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.models]


class TestTransportConfig:
    @autotests.num("160")
    @autotests.external_id("19913776-5020-49de-98b3-02aefefe2ef8")
    @autotests.name("MCP SDK Transport: значения по умолчанию TransportConfig")
    def test_defaults(self):
        """Проверяет значения по умолчанию TransportConfig."""

        # Arrange
        from onlinetlabs_mcp_sdk.transport import TransportConfig

        # Act
        with autotests.step("Создаём TransportConfig по умолчанию"):
            tc = TransportConfig()

        # Assert
        with autotests.step("Проверяем значения по умолчанию"):
            assert tc.transport == "streamable-http"
            assert tc.host == "127.0.0.1"
            assert tc.port == 8100
            assert tc.api_key is None
            assert tc.stateless is True

    @autotests.num("161")
    @autotests.external_id("53c8d503-ce39-4c6c-a509-2674c8d28197")
    @autotests.name("MCP SDK Transport: пользовательские значения TransportConfig")
    def test_custom_values(self):
        """Проверяет пользовательские значения TransportConfig."""

        # Arrange
        from onlinetlabs_mcp_sdk.transport import TransportConfig

        # Act
        with autotests.step("Создаём TransportConfig с пользовательскими значениями"):
            tc = TransportConfig(
                transport="stdio",
                host="0.0.0.0",
                port=9000,
                api_key="secret-key",
                stateless=False,
            )

        # Assert
        with autotests.step("Проверяем значения"):
            assert tc.transport == "stdio"
            assert tc.api_key == "secret-key"

    @autotests.num("162")
    @autotests.external_id("ddad95af-c838-4106-8068-30ffa7357402")
    @autotests.name("MCP SDK Transport: невалидный transport вызывает ValidationError")
    def test_invalid_transport(self):
        """Проверяет ValidationError при невалидном transport."""

        # Arrange
        from pydantic import ValidationError

        from onlinetlabs_mcp_sdk.transport import TransportConfig

        # Act & Assert
        with autotests.step("Создаём TransportConfig с невалидным transport"):
            with pytest.raises(ValidationError):
                TransportConfig(transport="websocket")


class TestTargetSystemAuth:
    @autotests.num("163")
    @autotests.external_id("72d67a93-f5c7-477e-a4cd-207d22e46a76")
    @autotests.name("MCP SDK Transport: создание APIKeyAuth")
    def test_api_key_auth(self):
        """Проверяет создание APIKeyAuth."""

        # Arrange
        from onlinetlabs_mcp_sdk.transport import APIKeyAuth

        # Act
        with autotests.step("Создаём APIKeyAuth"):
            auth = APIKeyAuth(api_key="my-secret")

        # Assert
        with autotests.step("Проверяем auth_type и api_key"):
            assert auth.auth_type == "api_key"
            assert auth.api_key.get_secret_value() == "my-secret"

    @autotests.num("164")
    @autotests.external_id("42f78f6b-c80f-4f36-934e-8e4ebc527bf8")
    @autotests.name("MCP SDK Transport: создание SocketAuth")
    def test_socket_auth(self):
        """Проверяет создание SocketAuth."""

        # Arrange
        from onlinetlabs_mcp_sdk.transport import SocketAuth

        # Act
        with autotests.step("Создаём SocketAuth"):
            auth = SocketAuth(socket_path="/var/run/docker.sock")

        # Assert
        with autotests.step("Проверяем auth_type"):
            assert auth.auth_type == "socket"
