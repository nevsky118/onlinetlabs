import pytest
import httpx
import respx

from mcp_sdk.context import SessionContext
from src.api_client import GNS3ApiClient
from src.connection import GNS3ConnectionManager
from mcp_sdk.testing import autotest
from tests.unit.conftest import build_gns3_version

pytestmark = [pytest.mark.unit, pytest.mark.connection]

GNS3_URL = "http://gns3-test:3080"


def _make_ctx(**overrides) -> SessionContext:
    defaults = dict(
        user_id="u1", session_id="s1",
        environment_url=GNS3_URL,
    )
    return SessionContext(**(defaults | overrides))


class TestGNS3ConnectionManager:
    @autotest.num("340")
    @autotest.external_id("gns3-conn-connect-creates-client")
    @autotest.name("GNS3ConnectionManager.connect: создаёт GNS3ApiClient")
    async def test_connect(self):
        with autotest.step("Вызываем connect"):
            mgr = GNS3ConnectionManager()
            ctx = _make_ctx()
            client = await mgr.connect(ctx)

        with autotest.step("Проверяем тип"):
            assert isinstance(client, GNS3ApiClient)
            await mgr.disconnect(client)

    @autotest.num("341")
    @autotest.external_id("gns3-conn-connect-jwt-header")
    @autotest.name("GNS3ConnectionManager.connect: JWT в заголовке")
    async def test_connect_with_jwt(self):
        with autotest.step("Вызываем connect с JWT"):
            mgr = GNS3ConnectionManager()
            ctx = _make_ctx(metadata={"gns3_jwt": "test-token"})
            client = await mgr.connect(ctx)

        with autotest.step("Проверяем Authorization header"):
            auth = client.client.headers.get("authorization")
            assert auth == "Bearer test-token"
            await mgr.disconnect(client)

    @respx.mock
    @autotest.num("342")
    @autotest.external_id("gns3-conn-health-check-ok")
    @autotest.name("GNS3ConnectionManager.health_check: True при 200")
    async def test_health_check_ok(self):
        with autotest.step("Мокаем /v3/version"):
            respx.get(f"{GNS3_URL}/v3/version").mock(
                return_value=httpx.Response(200, json=build_gns3_version())
            )
            mgr = GNS3ConnectionManager()
            client = await mgr.connect(_make_ctx())

        with autotest.step("health_check → True"):
            result = await mgr.health_check(client)
            assert result is True
            await mgr.disconnect(client)

    @respx.mock
    @autotest.num("343")
    @autotest.external_id("gns3-conn-health-check-fail")
    @autotest.name("GNS3ConnectionManager.health_check: False при ошибке")
    async def test_health_check_fail(self):
        with autotest.step("Мокаем ConnectError"):
            respx.get(f"{GNS3_URL}/v3/version").mock(
                side_effect=httpx.ConnectError("refused")
            )
            mgr = GNS3ConnectionManager()
            client = await mgr.connect(_make_ctx())

        with autotest.step("health_check → False"):
            result = await mgr.health_check(client)
            assert result is False
            await mgr.disconnect(client)
