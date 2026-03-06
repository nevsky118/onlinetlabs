import httpx
import pytest
import respx

from tests.helpers.factories import build_session_context, build_gns3_version
from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.connection]


class TestGNS3ConnectionManager:
    @autotests.num("340")
    @autotests.external_id("a1b2c3d4-0001-4aaa-bbbb-000000000001")
    @autotests.name("GNS3 Connection: connect создаёт GNS3ApiClient")
    async def test_connect_creates_client(self):
        # Arrange
        from src.connection import GNS3ConnectionManager

        mgr = GNS3ConnectionManager()
        ctx = build_session_context()

        # Act
        with autotests.step("Вызываем connect"):
            client = await mgr.connect(ctx)

        # Assert
        with autotests.step("Проверяем тип и auth header"):
            from src.api_client import GNS3ApiClient

            assert isinstance(client, GNS3ApiClient)
            assert client.client.headers.get("authorization") == "Bearer test-jwt-token"
            await mgr.disconnect(client)

    @autotests.num("341")
    @autotests.external_id("a1b2c3d4-0002-4aaa-bbbb-000000000002")
    @autotests.name("GNS3 Connection: health_check успешный")
    async def test_health_check_success(self):
        # Arrange
        from src.connection import GNS3ConnectionManager
        from src.api_client import GNS3ApiClient

        with respx.mock:
            respx.get("/v3/version").mock(return_value=httpx.Response(200, json=build_gns3_version()))
            client = GNS3ApiClient(httpx.AsyncClient(base_url="http://test"))
            mgr = GNS3ConnectionManager()

            # Act
            with autotests.step("Проверяем health_check"):
                result = await mgr.health_check(client)

            # Assert
            with autotests.step("Результат True"):
                assert result is True
            await client.client.aclose()

    @autotests.num("342")
    @autotests.external_id("a1b2c3d4-0003-4aaa-bbbb-000000000003")
    @autotests.name("GNS3 Connection: health_check при ошибке")
    async def test_health_check_failure(self):
        # Arrange
        from src.connection import GNS3ConnectionManager
        from src.api_client import GNS3ApiClient

        with respx.mock:
            respx.get("/v3/version").mock(side_effect=httpx.ConnectError("refused"))
            client = GNS3ApiClient(httpx.AsyncClient(base_url="http://test"))
            mgr = GNS3ConnectionManager()

            # Act
            with autotests.step("Проверяем health_check при ошибке"):
                result = await mgr.health_check(client)

            # Assert
            with autotests.step("Результат False"):
                assert result is False
            await client.client.aclose()
