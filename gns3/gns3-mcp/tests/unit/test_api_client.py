import httpx
import pytest
import respx
from mcp_sdk.errors import TargetSystemAPIError, TargetSystemConnectionError
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none

from src.api_client import GNS3ApiClient
from tests.settings.data.gns3_data import Gns3NodeData, Gns3VersionData

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
    @autotest.external_id("323c7ccf-0f12-4cba-b89c-dea0a523f7a0")
    @autotest.name("GNS3ApiClient.get_version: GET /v3/version")
    async def test_323c7ccf_get_version(self, api_client):
        with autotest.step("Mock /v3/version"):
            data = Gns3VersionData().data
            respx.get(f"{BASE_URL}/v3/version").mock(return_value=httpx.Response(200, json=data))

        with autotest.step("Call get_version"):
            result = await api_client.get_version()

        with autotest.step("Assert"):
            assert_equal(result["version"], "3.0.0", "version")

    @respx.mock
    @autotest.num("331")
    @autotest.external_id("5b07de9f-5b24-4d17-a19d-5429b84b9322")
    @autotest.name("GNS3ApiClient.list_nodes: GET /v3/projects/{id}/nodes")
    async def test_5b07de9f_list_nodes(self, api_client):
        with autotest.step("Mock list_nodes"):
            nodes = [Gns3NodeData().data]
            respx.get(f"{BASE_URL}/v3/projects/{PROJECT_ID}/nodes").mock(
                return_value=httpx.Response(200, json=nodes)
            )

        with autotest.step("Call"):
            result = await api_client.list_nodes(PROJECT_ID)

        with autotest.step("Assert"):
            assert_equal(len(result), 1, "result count")
            assert_equal(result[0]["name"], "R1", "name")

    @respx.mock
    @autotest.num("332")
    @autotest.external_id("b5690eab-358f-4607-a7b1-7e2f8b39c0d4")
    @autotest.name("GNS3ApiClient.start_node: POST start")
    async def test_b5690eab_start_node(self, api_client):
        with autotest.step("Mock start_node"):
            respx.post(f"{BASE_URL}/v3/projects/{PROJECT_ID}/nodes/{NODE_ID}/start").mock(
                return_value=httpx.Response(200, json={"status": "started"})
            )

        with autotest.step("Call"):
            result = await api_client.start_node(PROJECT_ID, NODE_ID)

        with autotest.step("Assert"):
            assert_equal(result["status"], "started", "status")

    @respx.mock
    @autotest.num("333")
    @autotest.external_id("a9b96e84-f57f-4a9e-80d1-c139cafa0e32")
    @autotest.name("GNS3ApiClient.create_link: POST link")
    async def test_a9b96e84_create_link(self, api_client):
        with autotest.step("Mock create_link"):
            link_nodes = [
                {"node_id": "node-1", "adapter_number": 0, "port_number": 0},
                {"node_id": "node-2", "adapter_number": 0, "port_number": 0},
            ]
            respx.post(f"{BASE_URL}/v3/projects/{PROJECT_ID}/links").mock(
                return_value=httpx.Response(201, json={"link_id": "new-link"})
            )

        with autotest.step("Call"):
            result = await api_client.create_link(PROJECT_ID, link_nodes)

        with autotest.step("Assert"):
            assert_equal(result["link_id"], "new-link", "link id")

    @respx.mock
    @autotest.num("334")
    @autotest.external_id("fed1f7dd-8ca8-47c0-b082-e13552960d1d")
    @autotest.name("GNS3ApiClient.delete_link: 204 → None")
    async def test_fed1f7dd_delete_link(self, api_client):
        with autotest.step("Mock delete_link 204"):
            respx.delete(f"{BASE_URL}/v3/projects/{PROJECT_ID}/links/{LINK_ID}").mock(
                return_value=httpx.Response(204)
            )

        with autotest.step("Call"):
            result = await api_client.delete_link(PROJECT_ID, LINK_ID)

        with autotest.step("None on 204"):
            assert_is_none(result, "result")


class TestApiClientErrors:
    @respx.mock
    @autotest.num("335")
    @autotest.external_id("b493e62c-df96-4e89-aac2-fcfab5521c19")
    @autotest.name("GNS3ApiClient: 404 → TargetSystemAPIError")
    async def test_b493e62c_404(self, api_client):
        with autotest.step("Mock 404"):
            respx.get(f"{BASE_URL}/v3/version").mock(
                return_value=httpx.Response(404, text="Not Found")
            )

        with autotest.step("Assert the exception"):
            with pytest.raises(TargetSystemAPIError) as exc_info:
                await api_client.get_version()
            assert_equal(exc_info.value.status_code, 404, "status code")

    @respx.mock
    @autotest.num("336")
    @autotest.external_id("05816322-f2a6-41e0-982b-00309455803b")
    @autotest.name("GNS3ApiClient: 500 → TargetSystemAPIError")
    async def test_05816322_500(self, api_client):
        with autotest.step("Mock 500"):
            respx.get(f"{BASE_URL}/v3/version").mock(
                return_value=httpx.Response(500, text="Internal Server Error")
            )

        with autotest.step("Assert the exception"):
            with pytest.raises(TargetSystemAPIError) as exc_info:
                await api_client.get_version()
            assert_equal(exc_info.value.status_code, 500, "status code")

    @respx.mock
    @autotest.num("337")
    @autotest.external_id("26824491-c10a-414b-80bf-fdb255e53e16")
    @autotest.name("GNS3ApiClient: ConnectError → TargetSystemConnectionError")
    async def test_26824491_connection_error(self, api_client):
        with autotest.step("Mock ConnectError"):
            respx.get(f"{BASE_URL}/v3/version").mock(side_effect=httpx.ConnectError("refused"))

        with autotest.step("Assert the exception"):
            with pytest.raises(TargetSystemConnectionError):
                await api_client.get_version()

    @respx.mock
    @autotest.num("338")
    @autotest.external_id("bc292cf6-29e7-4a9b-932b-fd2e3a84a981")
    @autotest.name("GNS3ApiClient: ReadTimeout → TargetSystemConnectionError")
    async def test_bc292cf6_timeout(self, api_client):
        with autotest.step("Mock ReadTimeout"):
            respx.get(f"{BASE_URL}/v3/version").mock(side_effect=httpx.ReadTimeout("timeout"))

        with autotest.step("Assert the exception"):
            with pytest.raises(TargetSystemConnectionError):
                await api_client.get_version()
