import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.models]


class TestSessionContext:
    @autotests.num("120")
    @autotests.external_id("4d6c9849-299f-4d18-a08c-b8684169d9c2")
    @autotests.name("MCP SDK Context: создание SessionContext с валидными данными")
    def test_create_valid(self):
        """Проверяет создание SessionContext с валидными данными."""

        # Arrange
        from onlinetlabs_mcp_sdk.context import SessionContext

        # Act
        with autotests.step("Создаём SessionContext"):
            ctx = SessionContext(
                user_id="user-1",
                session_id="sess-1",
                environment_url="http://localhost:3080",
                project_id="proj-1",
            )

        # Assert
        with autotests.step("Проверяем поля"):
            assert ctx.user_id == "user-1"
            assert ctx.metadata == {}

    @autotests.num("121")
    @autotests.external_id("185c8b5a-8eff-4446-81fa-1d79bc9872e6")
    @autotests.name("MCP SDK Context: metadata по умолчанию пустой словарь")
    def test_metadata_defaults_empty(self):
        """Проверяет что metadata по умолчанию — пустой словарь."""

        # Arrange
        from onlinetlabs_mcp_sdk.context import SessionContext

        # Act
        with autotests.step("Создаём SessionContext без metadata"):
            ctx = SessionContext(
                user_id="u", session_id="s", environment_url="http://localhost"
            )

        # Assert
        with autotests.step("Проверяем значения по умолчанию"):
            assert ctx.metadata == {}
            assert ctx.project_id is None

    @autotests.num("122")
    @autotests.external_id("103f9614-1e94-43cf-b4e6-a878ecf871b1")
    @autotests.name("MCP SDK Context: metadata расширяемый")
    def test_metadata_extensible(self):
        """Проверяет что metadata принимает произвольные ключи."""

        # Arrange
        from onlinetlabs_mcp_sdk.context import SessionContext

        # Act
        with autotests.step("Создаём SessionContext с metadata"):
            ctx = SessionContext(
                user_id="u",
                session_id="s",
                environment_url="http://localhost",
                metadata={"lab_id": "lab-5", "difficulty": "hard"},
            )

        # Assert
        with autotests.step("Проверяем metadata"):
            assert ctx.metadata["lab_id"] == "lab-5"


class TestServerCapabilities:
    @autotests.num("123")
    @autotests.external_id("097e5d99-ae5d-4e13-8c9d-ea943ae57e4b")
    @autotests.name("MCP SDK Context: создание ServerCapabilities с валидными данными")
    def test_create_valid(self):
        """Проверяет создание ServerCapabilities."""

        # Arrange
        from onlinetlabs_mcp_sdk.context import ServerCapabilities

        # Act
        with autotests.step("Создаём ServerCapabilities"):
            sc = ServerCapabilities(
                system_name="gns3",
                capabilities=["state", "logs"],
                domain_tools=["capture_packets"],
            )

        # Assert
        with autotests.step("Проверяем capabilities и domain_tools"):
            assert "state" in sc.capabilities
            assert "capture_packets" in sc.domain_tools

    @autotests.num("124")
    @autotests.external_id("f891239c-8e11-4178-9e03-c29652301c20")
    @autotests.name("MCP SDK Context: domain_tools по умолчанию пустой список")
    def test_empty_domain_tools(self):
        """Проверяет что domain_tools по умолчанию пуст."""

        # Arrange
        from onlinetlabs_mcp_sdk.context import ServerCapabilities

        # Act
        with autotests.step("Создаём ServerCapabilities без domain_tools"):
            sc = ServerCapabilities(system_name="gns3", capabilities=["state"])

        # Assert
        with autotests.step("Проверяем пустой domain_tools"):
            assert sc.domain_tools == []
