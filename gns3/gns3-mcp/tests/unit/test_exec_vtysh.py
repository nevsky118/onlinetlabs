"""exec_vtysh domain tool, observing device state through MCP (gns3-service)."""

import json

import httpx
import pytest
import respx
from mcp_sdk.testing import autotest

from src.domain_tools import register_domain_tools

pytestmark = [pytest.mark.unit, pytest.mark.domain_tools]

SERVICE_URL = "http://gns3-svc:8101"
PROJECT_ID = "proj-1"
NODE_ID = "node-1"
CMD = "show ip route"
TOKEN = "test-internal-token"


class _StubServer:
    def __init__(self):
        self.tools = {}

    def domain_tool(self, **kwargs):
        def wrapper(fn):
            self.tools[fn.__name__] = fn
            return fn

        return wrapper


def _register(service_url, internal_api_token=TOKEN):
    server = _StubServer()

    async def get_client(session):
        return None

    def get_project_id(session):
        return session.project_id

    register_domain_tools(
        server,
        get_client,
        get_project_id,
        service_url=service_url,
        internal_api_token=internal_api_token,
    )
    return server


def _ctx():
    return dict(
        user_id="u1",
        session_id="s1",
        environment_url="http://gns3:3080",
        project_id=PROJECT_ID,
    )


class TestExecVtysh:
    @autotest.num("817")
    @autotest.external_id("gns3-exec-vtysh-posts-to-service")
    @autotest.name("exec_vtysh: POST /v1/exec/vtysh to gns3-service, returns output")
    async def test_gns3exec_exec_vtysh_posts_to_service(self):
        with autotest.step("Arrange: tool registered with service_url"):
            server = _register(SERVICE_URL)

        with autotest.step("Act: exec_vtysh against a mocked gns3-service"):
            with respx.mock:
                route = respx.post(f"{SERVICE_URL}/v1/exec/vtysh").mock(
                    return_value=httpx.Response(200, json={"output": "10.0.0.1 is up"})
                )
                result = await server.tools["exec_vtysh"](_ctx(), NODE_ID, CMD)

        with autotest.step("Assert: success, output passed through, payload correct"):
            assert route.called
            assert result["success"] is True
            assert result["data"]["output"] == "10.0.0.1 is up"
            body = json.loads(route.calls.last.request.content)
            expected = {"project_id": PROJECT_ID, "node_id": NODE_ID, "command": CMD}
            assert body == expected
            # gns3-service /v1/exec is token-gated; without this header it 403s.
            assert route.calls.last.request.headers["Authorization"] == f"Bearer {TOKEN}"

    @autotest.num("818")
    @autotest.external_id("gns3-exec-vtysh-no-service-url")
    @autotest.name("exec_vtysh: without service_url → success=False")
    async def test_gns3exec_exec_vtysh_no_service_url(self):
        with autotest.step("Arrange: tool without service_url"):
            server = _register(None)

        with autotest.step("Act+Assert: configuration error, no exception raised"):
            result = await server.tools["exec_vtysh"](_ctx(), NODE_ID, CMD)
            assert result["success"] is False
            assert result["data"] is None

    @autotest.num("819")
    @autotest.external_id("f0c9d4b7-7a3f-4a26-8a54-9c3a1f7de2b1")
    @autotest.name("exec_vtysh: without an internal token → success=False, no request sent")
    async def test_f0c9d4b7_exec_vtysh_no_internal_token(self):
        with autotest.step("Arrange: tool registered without a token"):
            server = _register(SERVICE_URL, internal_api_token=None)

        with autotest.step("Act: call exec_vtysh"):
            with respx.mock:
                route = respx.post(f"{SERVICE_URL}/v1/exec/vtysh")
                result = await server.tools["exec_vtysh"](_ctx(), NODE_ID, CMD)

        with autotest.step("Assert: fails before sending, does not 403 at the service"):
            assert not route.called
            assert result["success"] is False
            assert result["data"] is None
