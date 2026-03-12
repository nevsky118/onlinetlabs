import pytest
import httpx
import respx

from mcp_sdk.errors import TargetSystemAPIError, TargetSystemConnectionError
from src.api_client import GNS3ApiClient
from mcp_sdk.testing import autotest
from tests.unit.conftest import build_gns3_node, build_gns3_version

pytestmark = [pytest.mark.unit, pytest.mark.api_client]

BASE_URL = "http://gns3-test:3080"
PROJECT_ID = "proj-1"
NODE_ID = "node-1"
LINK_ID = "link-1"


@pytest.fixture()
def api_client():
    client = httpx.AsyncClient(base_url=BASE_URL)
    return GNS3ApiClient(client)


class TestApiClientRequests:
    @respx.mock
    @autotest.num("330")
    @autotest.external_id("gns3-api-client-get-version")
    @autotest.name("GNS3ApiClient.get_version: GET /v3/version")
    async def test_get_version(self, api_client):
        with autotest.step("Мокаем /v3/version"):
            data = build_gns3_version()
            respx.get(f"{BASE_URL}/v3/version").mock(
                return_value=httpx.Response(200, json=data)
            )

        with autotest.step("Вызываем get_version"):
            result = await api_client.get_version()

        with autotest.step("Проверяем"):
            assert result["version"] == "3.0.0"

    @respx.mock
    @autotest.num("331")
    @autotest.external_id("gns3-api-client-list-nodes")
    @autotest.name("GNS3ApiClient.list_nodes: GET /v3/projects/{id}/nodes")
    async def test_list_nodes(self, api_client):
        with autotest.step("Мокаем list_nodes"):
            nodes = [build_gns3_node()]
            respx.get(f"{BASE_URL}/v3/projects/{PROJECT_ID}/nodes").mock(
                return_value=httpx.Response(200, json=nodes)
            )

        with autotest.step("Вызываем"):
            result = await api_client.list_nodes(PROJECT_ID)

        with autotest.step("Проверяем"):
            assert len(result) == 1
            assert result[0]["name"] == "R1"

    @respx.mock
    @autotest.num("332")
    @autotest.external_id("gns3-api-client-start-node")
    @autotest.name("GNS3ApiClient.start_node: POST start")
    async def test_start_node(self, api_client):
        with autotest.step("Мокаем start_node"):
            respx.post(f"{BASE_URL}/v3/projects/{PROJECT_ID}/nodes/{NODE_ID}/start").mock(
                return_value=httpx.Response(200, json={"status": "started"})
            )

        with autotest.step("Вызываем"):
            result = await api_client.start_node(PROJECT_ID, NODE_ID)

        with autotest.step("Проверяем"):
            assert result["status"] == "started"

    @respx.mock
    @autotest.num("333")
    @autotest.external_id("gns3-api-client-create-link")
    @autotest.name("GNS3ApiClient.create_link: POST link")
    async def test_create_link(self, api_client):
        with autotest.step("Мокаем create_link"):
            link_nodes = [
                {"node_id": "node-1", "adapter_number": 0, "port_number": 0},
                {"node_id": "node-2", "adapter_number": 0, "port_number": 0},
            ]
            respx.post(f"{BASE_URL}/v3/projects/{PROJECT_ID}/links").mock(
                return_value=httpx.Response(201, json={"link_id": "new-link"})
            )

        with autotest.step("Вызываем"):
            result = await api_client.create_link(PROJECT_ID, link_nodes)

        with autotest.step("Проверяем"):
            assert result["link_id"] == "new-link"

    @respx.mock
    @autotest.num("334")
    @autotest.external_id("gns3-api-client-delete-link-204")
    @autotest.name("GNS3ApiClient.delete_link: 204 → None")
    async def test_delete_link(self, api_client):
        with autotest.step("Мокаем delete_link 204"):
            respx.delete(f"{BASE_URL}/v3/projects/{PROJECT_ID}/links/{LINK_ID}").mock(
                return_value=httpx.Response(204)
            )

        with autotest.step("Вызываем"):
            result = await api_client.delete_link(PROJECT_ID, LINK_ID)

        with autotest.step("None при 204"):
            assert result is None


class TestApiClientErrors:
    @respx.mock
    @autotest.num("335")
    @autotest.external_id("gns3-api-client-404")
    @autotest.name("GNS3ApiClient: 404 → TargetSystemAPIError")
    async def test_404(self, api_client):
        with autotest.step("Мокаем 404"):
            respx.get(f"{BASE_URL}/v3/version").mock(
                return_value=httpx.Response(404, text="Not Found")
            )

        with autotest.step("Проверяем исключение"):
            with pytest.raises(TargetSystemAPIError) as exc_info:
                await api_client.get_version()
            assert exc_info.value.status_code == 404

    @respx.mock
    @autotest.num("336")
    @autotest.external_id("gns3-api-client-500")
    @autotest.name("GNS3ApiClient: 500 → TargetSystemAPIError")
    async def test_500(self, api_client):
        with autotest.step("Мокаем 500"):
            respx.get(f"{BASE_URL}/v3/version").mock(
                return_value=httpx.Response(500, text="Internal Server Error")
            )

        with autotest.step("Проверяем исключение"):
            with pytest.raises(TargetSystemAPIError) as exc_info:
                await api_client.get_version()
            assert exc_info.value.status_code == 500

    @respx.mock
    @autotest.num("337")
    @autotest.external_id("gns3-api-client-connection-error")
    @autotest.name("GNS3ApiClient: ConnectError → TargetSystemConnectionError")
    async def test_connection_error(self, api_client):
        with autotest.step("Мокаем ConnectError"):
            respx.get(f"{BASE_URL}/v3/version").mock(
                side_effect=httpx.ConnectError("refused")
            )

        with autotest.step("Проверяем исключение"):
            with pytest.raises(TargetSystemConnectionError):
                await api_client.get_version()

    @respx.mock
    @autotest.num("338")
    @autotest.external_id("gns3-api-client-timeout")
    @autotest.name("GNS3ApiClient: ReadTimeout → TargetSystemConnectionError")
    async def test_timeout(self, api_client):
        with autotest.step("Мокаем ReadTimeout"):
            respx.get(f"{BASE_URL}/v3/version").mock(
                side_effect=httpx.ReadTimeout("timeout")
            )

        with autotest.step("Проверяем исключение"):
            with pytest.raises(TargetSystemConnectionError):
                await api_client.get_version()
