"""exec_vtysh domain tool: наблюдение состояния устройства через MCP (gns3-service)."""

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


class _StubServer:
    def __init__(self):
        self.tools = {}

    def domain_tool(self, **kwargs):
        def wrapper(fn):
            self.tools[fn.__name__] = fn
            return fn

        return wrapper


def _register(service_url):
    server = _StubServer()

    async def get_client(session):
        return None

    def get_project_id(session):
        return session.project_id

    register_domain_tools(server, get_client, get_project_id, service_url=service_url)
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
    @autotest.name("exec_vtysh: POST /v1/exec/vtysh на gns3-service, возвращает вывод")
    async def test_exec_vtysh_posts_to_service(self):
        with autotest.step("Arrange: tool зарегистрирован с service_url"):
            server = _register(SERVICE_URL)

        with autotest.step("Act: exec_vtysh с замоканным gns3-service"):
            with respx.mock:
                route = respx.post(f"{SERVICE_URL}/v1/exec/vtysh").mock(
                    return_value=httpx.Response(200, json={"output": "10.0.0.1 is up"})
                )
                result = await server.tools["exec_vtysh"](_ctx(), NODE_ID, CMD)

        with autotest.step("Assert: успех, вывод проброшен, payload корректен"):
            assert route.called
            assert result["success"] is True
            assert result["data"]["output"] == "10.0.0.1 is up"
            body = json.loads(route.calls.last.request.content)
            expected = {"project_id": PROJECT_ID, "node_id": NODE_ID, "command": CMD}
            assert body == expected

    @autotest.num("818")
    @autotest.external_id("gns3-exec-vtysh-no-service-url")
    @autotest.name("exec_vtysh: без service_url → success=False")
    async def test_exec_vtysh_no_service_url(self):
        with autotest.step("Arrange: tool без service_url"):
            server = _register(None)

        with autotest.step("Act+Assert: ошибка конфигурации, без исключения"):
            result = await server.tools["exec_vtysh"](_ctx(), NODE_ID, CMD)
            assert result["success"] is False
            assert result["data"] is None
