import httpx
import pytest
import respx
from mcp_sdk.context import SessionContext
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from src.api_client import GNS3ApiClient
from src.connection import GNS3ConnectionManager
from tests.settings.data.gns3_data import Gns3VersionData

pytestmark = [pytest.mark.unit, pytest.mark.connection]

GNS3_URL = "http://gns3-test:3080"


def _make_ctx(**overrides) -> SessionContext:
    defaults = dict(
        user_id="u1",
        session_id="s1",
        environment_url=GNS3_URL,
    )
    return SessionContext(**(defaults | overrides))


class TestGNS3ConnectionManager:
    @autotest.num("340")
    @autotest.external_id("4f1adef4-3374-41ab-9c07-f70365ff8172")
    @autotest.name("GNS3ConnectionManager.connect: creates a GNS3ApiClient")
    async def test_4f1adef4_connect(self):
        with autotest.step("Call connect"):
            mgr = GNS3ConnectionManager()
            ctx = _make_ctx()
            client = await mgr.connect(ctx)

        with autotest.step("Assert the type"):
            assert_true(isinstance(client, GNS3ApiClient), "isinstance")
            await mgr.disconnect(client)

    @autotest.num("341")
    @autotest.external_id("0170b3f0-5be7-4253-958c-b8da2567604d")
    @autotest.name("GNS3ConnectionManager.connect: JWT in the header")
    async def test_0170b3f0_connect_with_jwt(self):
        with autotest.step("Call connect with a JWT"):
            mgr = GNS3ConnectionManager()
            ctx = _make_ctx(metadata={"gns3_jwt": "test-token"})
            client = await mgr.connect(ctx)

        with autotest.step("Assert the Authorization header"):
            auth = client.client.headers.get("authorization")
            assert_equal(auth, "Bearer test-token", "auth")
            await mgr.disconnect(client)

    @respx.mock
    @autotest.num("342")
    @autotest.external_id("5e03e577-93a5-4e38-9f78-d88a96ba7e96")
    @autotest.name("GNS3ConnectionManager.health_check: True on 200")
    async def test_5e03e577_health_check_ok(self):
        with autotest.step("Mock /v3/version"):
            respx.get(f"{GNS3_URL}/v3/version").mock(
                return_value=httpx.Response(200, json=Gns3VersionData().data)
            )
            mgr = GNS3ConnectionManager()
            client = await mgr.connect(_make_ctx())

        with autotest.step("health_check → True"):
            result = await mgr.health_check(client)
            assert_equal(result, True, "result")
            await mgr.disconnect(client)

    @respx.mock
    @autotest.num("343")
    @autotest.external_id("6ea2f1c8-7df7-4b1e-9133-9941482d11db")
    @autotest.name("GNS3ConnectionManager.health_check: False on error")
    async def test_6ea2f1c8_health_check_fail(self):
        with autotest.step("Mock ConnectError"):
            respx.get(f"{GNS3_URL}/v3/version").mock(side_effect=httpx.ConnectError("refused"))
            mgr = GNS3ConnectionManager()
            client = await mgr.connect(_make_ctx())

        with autotest.step("health_check → False"):
            result = await mgr.health_check(client)
            assert_equal(result, False, "result")
            await mgr.disconnect(client)
