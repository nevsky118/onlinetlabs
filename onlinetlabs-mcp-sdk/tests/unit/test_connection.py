import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.connection]


class TestBaseConnectionManager:
    @autotests.num("150")
    @autotests.external_id("6f943b35-f4a0-4ab5-9419-d1cba782275b")
    @autotests.name("MCP SDK Connection: BaseConnectionManager абстрактный")
    def test_is_abstract(self):
        """Проверяет что BaseConnectionManager нельзя инстанцировать."""

        # Arrange
        from onlinetlabs_mcp_sdk.connection import BaseConnectionManager

        # Act & Assert
        with autotests.step("Пытаемся создать BaseConnectionManager"):
            with pytest.raises(TypeError):
                BaseConnectionManager()

    @autotests.num("151")
    @autotests.external_id("67608e4f-087e-4ca5-8777-4371dee1b504")
    @autotests.name("MCP SDK Connection: подкласс реализует BaseConnectionManager")
    def test_subclass_implements(self):
        """Проверяет что подкласс с методами создаётся успешно."""

        # Arrange
        from onlinetlabs_mcp_sdk.connection import BaseConnectionManager

        class FakeManager(BaseConnectionManager):
            async def connect(self, environment_url: str):
                return {"url": environment_url}

            async def disconnect(self, connection) -> None:
                pass

            async def health_check(self, connection) -> bool:
                return True

        # Act
        with autotests.step("Создаём FakeManager"):
            mgr = FakeManager()

        # Assert
        with autotests.step("Проверяем создание"):
            assert mgr is not None


class TestConnectionPool:
    @pytest.fixture
    def fake_manager(self):
        from onlinetlabs_mcp_sdk.connection import BaseConnectionManager

        class FakeManager(BaseConnectionManager):
            def __init__(self):
                self.connected = []
                self.disconnected = []

            async def connect(self, environment_url: str):
                conn = {"url": environment_url, "alive": True}
                self.connected.append(conn)
                return conn

            async def disconnect(self, connection) -> None:
                connection["alive"] = False
                self.disconnected.append(connection)

            async def health_check(self, connection) -> bool:
                return connection.get("alive", False)

        return FakeManager()

    @autotests.num("152")
    @autotests.external_id("0c4bc89f-233f-42c2-96e5-5bb8872c73dc")
    @autotests.name("MCP SDK Connection: получение соединения из пула")
    async def test_get_connection(self, fake_manager):
        """Проверяет получение соединения из пула."""

        # Arrange
        from onlinetlabs_mcp_sdk.connection import ConnectionPool

        pool = ConnectionPool(manager=fake_manager, max_size=5)
        await pool.start()

        # Act
        with autotests.step("Получаем соединение"):
            conn = await pool.get_connection("http://localhost:3080")

        # Assert
        with autotests.step("Проверяем URL соединения"):
            assert conn["url"] == "http://localhost:3080"
            await pool.close()

    @autotests.num("153")
    @autotests.external_id("768de2c5-8212-45e0-9c61-819059656c77")
    @autotests.name("MCP SDK Connection: повторное использование соединения")
    async def test_reuses_connection(self, fake_manager):
        """Проверяет что пул переиспользует соединения."""

        # Arrange
        from onlinetlabs_mcp_sdk.connection import ConnectionPool

        pool = ConnectionPool(manager=fake_manager, max_size=5)
        await pool.start()

        # Act
        with autotests.step("Получаем два соединения к одному URL"):
            conn1 = await pool.get_connection("http://localhost:3080")
            conn2 = await pool.get_connection("http://localhost:3080")

        # Assert
        with autotests.step("Проверяем что соединение одно"):
            assert conn1 is conn2
            assert len(fake_manager.connected) == 1
            await pool.close()

    @autotests.num("154")
    @autotests.external_id("171ae4b7-b7eb-40f9-9c2a-01126a44a15c")
    @autotests.name("MCP SDK Connection: close отключает все соединения")
    async def test_close_disconnects_all(self, fake_manager):
        """Проверяет что close отключает все соединения."""

        # Arrange
        from onlinetlabs_mcp_sdk.connection import ConnectionPool

        pool = ConnectionPool(manager=fake_manager, max_size=5)
        await pool.start()
        await pool.get_connection("http://host1:3080")
        await pool.get_connection("http://host2:3080")

        # Act
        with autotests.step("Закрываем пул"):
            await pool.close()

        # Assert
        with autotests.step("Проверяем что все соединения отключены"):
            assert len(fake_manager.disconnected) == 2

    @autotests.num("155")
    @autotests.external_id("b62eba82-9c44-468a-9bd9-47f81c9db71f")
    @autotests.name("MCP SDK Connection: превышение max_size вызывает ошибку")
    async def test_max_size_raises(self, fake_manager):
        """Проверяет ошибку при превышении max_size."""

        # Arrange
        from onlinetlabs_mcp_sdk.connection import ConnectionPool
        from onlinetlabs_mcp_sdk.errors import MCPServerError

        pool = ConnectionPool(manager=fake_manager, max_size=2)
        await pool.start()
        await pool.get_connection("http://host1")
        await pool.get_connection("http://host2")

        # Act & Assert
        with autotests.step("Пытаемся превысить max_size"):
            with pytest.raises(MCPServerError):
                await pool.get_connection("http://host3")
            await pool.close()
