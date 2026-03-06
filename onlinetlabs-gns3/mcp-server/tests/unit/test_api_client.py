# Tests for GNS3ApiClient — httpx wrapper.

import httpx
import pytest
import respx

from onlinetlabs_mcp_sdk.errors import (
    TargetSystemAPIError,
    TargetSystemConnectionError,
)
from src.api_client import GNS3ApiClient
from tests.helpers.factories import (
    build_gns3_link,
    build_gns3_node,
    build_gns3_version,
)
from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.api_client]

PROJECT_ID = "test-project-id"
NODE_ID = "node-1"
LINK_ID = "link-1"
BASE_URL = "http://test"


class TestGNS3ApiClient:
    @autotests.num("320")
    @autotests.external_id("ac320001-0000-0000-0000-000000000001")
    @autotests.name("GNS3ApiClient: get_version returns dict")
    async def test_get_version(self):
        """GET /v3/version returns server version dict."""

        # Arrange
        data = build_gns3_version()

        with respx.mock:
            respx.get("/v3/version").mock(
                return_value=httpx.Response(200, json=data)
            )

            # Act
            with autotests.step("Call get_version"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                result = await client.get_version()
                await client.client.aclose()

            # Assert
            with autotests.step("Check returned dict"):
                assert result == data
                assert result["version"] == "3.0.0"

    @autotests.num("321")
    @autotests.external_id("ac321001-0000-0000-0000-000000000002")
    @autotests.name("GNS3ApiClient: list_nodes returns list")
    async def test_list_nodes(self):
        """GET /v3/projects/{id}/nodes returns list of nodes."""

        # Arrange
        nodes = [build_gns3_node(), build_gns3_node(node_id="node-2", name="PC2")]

        with respx.mock:
            respx.get(f"/v3/projects/{PROJECT_ID}/nodes").mock(
                return_value=httpx.Response(200, json=nodes)
            )

            # Act
            with autotests.step("Call list_nodes"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                result = await client.list_nodes(PROJECT_ID)
                await client.client.aclose()

            # Assert
            with autotests.step("Check returned list"):
                assert isinstance(result, list)
                assert len(result) == 2
                assert result[0]["name"] == "PC1"

    @autotests.num("322")
    @autotests.external_id("ac322001-0000-0000-0000-000000000003")
    @autotests.name("GNS3ApiClient: start_node returns dict")
    async def test_start_node(self):
        """POST .../start returns node dict."""

        # Arrange
        node = build_gns3_node(status="started")

        with respx.mock:
            respx.post(f"/v3/projects/{PROJECT_ID}/nodes/{NODE_ID}/start").mock(
                return_value=httpx.Response(200, json=node)
            )

            # Act
            with autotests.step("Call start_node"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                result = await client.start_node(PROJECT_ID, NODE_ID)
                await client.client.aclose()

            # Assert
            with autotests.step("Check returned dict"):
                assert result["status"] == "started"
                assert result["node_id"] == NODE_ID

    @autotests.num("323")
    @autotests.external_id("ac323001-0000-0000-0000-000000000004")
    @autotests.name("GNS3ApiClient: HTTP 404 raises TargetSystemAPIError")
    async def test_http_404_raises_api_error(self):
        """HTTP 404 mapped to TargetSystemAPIError with status_code=404."""

        with respx.mock:
            respx.get(f"/v3/projects/{PROJECT_ID}").mock(
                return_value=httpx.Response(404, text="Not found")
            )

            # Act & Assert
            with autotests.step("Call get_project for missing project"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                with pytest.raises(TargetSystemAPIError) as exc_info:
                    await client.get_project(PROJECT_ID)
                await client.client.aclose()

            with autotests.step("Check error attributes"):
                assert exc_info.value.status_code == 404
                assert exc_info.value.response_body == "Not found"

    @autotests.num("324")
    @autotests.external_id("ac324001-0000-0000-0000-000000000005")
    @autotests.name("GNS3ApiClient: ConnectError raises TargetSystemConnectionError")
    async def test_connect_error_raises_connection_error(self):
        """httpx.ConnectError mapped to TargetSystemConnectionError."""

        with respx.mock:
            respx.get("/v3/version").mock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            # Act & Assert
            with autotests.step("Call get_version with unreachable server"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                with pytest.raises(TargetSystemConnectionError):
                    await client.get_version()
                await client.client.aclose()

    @autotests.num("325")
    @autotests.external_id("ac325001-0000-0000-0000-000000000006")
    @autotests.name("GNS3ApiClient: list_links returns list")
    async def test_list_links(self):
        """GET /v3/projects/{id}/links returns list of links."""

        # Arrange
        links = [build_gns3_link()]

        with respx.mock:
            respx.get(f"/v3/projects/{PROJECT_ID}/links").mock(
                return_value=httpx.Response(200, json=links)
            )

            # Act
            with autotests.step("Call list_links"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                result = await client.list_links(PROJECT_ID)
                await client.client.aclose()

            # Assert
            with autotests.step("Check returned list"):
                assert isinstance(result, list)
                assert len(result) == 1
                assert result[0]["link_id"] == "link-1"

    @autotests.num("326")
    @autotests.external_id("ac326001-0000-0000-0000-000000000007")
    @autotests.name("GNS3ApiClient: create_link sends json body")
    async def test_create_link(self):
        """POST /v3/projects/{id}/links sends nodes in json body."""

        # Arrange
        link_nodes = [
            {"node_id": "node-1", "adapter_number": 0, "port_number": 0},
            {"node_id": "node-2", "adapter_number": 0, "port_number": 0},
        ]
        created_link = build_gns3_link()

        with respx.mock:
            route = respx.post(f"/v3/projects/{PROJECT_ID}/links").mock(
                return_value=httpx.Response(201, json=created_link)
            )

            # Act
            with autotests.step("Call create_link"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                result = await client.create_link(PROJECT_ID, link_nodes)
                await client.client.aclose()

            # Assert
            with autotests.step("Check returned link and request body"):
                assert result["link_id"] == "link-1"
                assert route.called

    @autotests.num("327")
    @autotests.external_id("ac327001-0000-0000-0000-000000000008")
    @autotests.name("GNS3ApiClient: list_templates returns list")
    async def test_list_templates(self):
        """GET /v3/templates returns list of templates."""

        # Arrange
        templates = [{"template_id": "tpl-1", "name": "VPCS", "template_type": "vpcs"}]

        with respx.mock:
            respx.get("/v3/templates").mock(
                return_value=httpx.Response(200, json=templates)
            )

            # Act
            with autotests.step("Call list_templates"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                result = await client.list_templates()
                await client.client.aclose()

            # Assert
            with autotests.step("Check returned list"):
                assert isinstance(result, list)
                assert result[0]["name"] == "VPCS"

    @autotests.num("328")
    @autotests.external_id("ac328001-0000-0000-0000-000000000009")
    @autotests.name("GNS3ApiClient: create_snapshot sends name in json")
    async def test_create_snapshot(self):
        """POST .../snapshots sends name in json body."""

        # Arrange
        snapshot = {"snapshot_id": "snap-1", "name": "before-change"}

        with respx.mock:
            respx.post(f"/v3/projects/{PROJECT_ID}/snapshots").mock(
                return_value=httpx.Response(201, json=snapshot)
            )

            # Act
            with autotests.step("Call create_snapshot"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                result = await client.create_snapshot(PROJECT_ID, "before-change")
                await client.client.aclose()

            # Assert
            with autotests.step("Check returned snapshot"):
                assert result["name"] == "before-change"
                assert result["snapshot_id"] == "snap-1"

    @autotests.num("329")
    @autotests.external_id("ac329001-0000-0000-0000-000000000010")
    @autotests.name("GNS3ApiClient: start_all_nodes returns None on 204")
    async def test_start_all_nodes_returns_none(self):
        """POST .../nodes/start with 204 returns None."""

        with respx.mock:
            respx.post(f"/v3/projects/{PROJECT_ID}/nodes/start").mock(
                return_value=httpx.Response(204)
            )

            # Act
            with autotests.step("Call start_all_nodes"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                result = await client.start_all_nodes(PROJECT_ID)
                await client.client.aclose()

            # Assert
            with autotests.step("Check returns None"):
                assert result is None

    @autotests.num("330")
    @autotests.external_id("ac330001-0000-0000-0000-000000000001")
    @autotests.name("GNS3ApiClient: создание ноды из шаблона")
    async def test_create_node_from_template(self):
        """POST /v3/projects/{pid}/templates/{tid} отправляет x,y и возвращает ноду."""

        # Arrange
        template_id = "tpl-1"
        node = build_gns3_node()

        with respx.mock:
            route = respx.post(f"/v3/projects/{PROJECT_ID}/templates/{template_id}").mock(
                return_value=httpx.Response(200, json=node)
            )

            # Act
            with autotests.step("Вызов create_node_from_template"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                result = await client.create_node_from_template(PROJECT_ID, template_id, x=100, y=200)
                await client.client.aclose()

            # Assert
            with autotests.step("Проверка тела запроса и ответа"):
                assert route.called
                sent_body = route.calls[0].request.content
                import json as _json
                assert _json.loads(sent_body) == {"x": 100, "y": 200}
                assert result == node
                assert result["node_id"] == NODE_ID

    @autotests.num("331")
    @autotests.external_id("ac330001-0000-0000-0000-000000000002")
    @autotests.name("GNS3ApiClient: удаление линка возвращает None")
    async def test_delete_link(self):
        """DELETE /v3/projects/{pid}/links/{lid} возвращает None при 204."""

        with respx.mock:
            respx.delete(f"/v3/projects/{PROJECT_ID}/links/{LINK_ID}").mock(
                return_value=httpx.Response(204)
            )

            # Act
            with autotests.step("Вызов delete_link"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                result = await client.delete_link(PROJECT_ID, LINK_ID)
                await client.client.aclose()

            # Assert
            with autotests.step("Проверка что результат None"):
                assert result is None

    @autotests.num("332")
    @autotests.external_id("ac330001-0000-0000-0000-000000000003")
    @autotests.name("GNS3ApiClient: HTTP 409 вызывает TargetSystemAPIError")
    async def test_http_409_raises_api_error(self):
        """HTTP 409 Conflict отображается в TargetSystemAPIError с status_code=409."""

        with respx.mock:
            respx.post(f"/v3/projects/{PROJECT_ID}/nodes/{NODE_ID}/start").mock(
                return_value=httpx.Response(409, text="Conflict")
            )

            # Act & Assert
            with autotests.step("Вызов start_node при конфликте"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                with pytest.raises(TargetSystemAPIError) as exc_info:
                    await client.start_node(PROJECT_ID, NODE_ID)
                await client.client.aclose()

            with autotests.step("Проверка атрибутов ошибки"):
                assert exc_info.value.status_code == 409
                assert exc_info.value.response_body == "Conflict"

    @autotests.num("333")
    @autotests.external_id("ac330001-0000-0000-0000-000000000004")
    @autotests.name("GNS3ApiClient: HTTP 422 вызывает TargetSystemAPIError")
    async def test_http_422_raises_api_error(self):
        """HTTP 422 Unprocessable Entity отображается в TargetSystemAPIError с status_code=422."""

        with respx.mock:
            respx.post(f"/v3/projects/{PROJECT_ID}/links").mock(
                return_value=httpx.Response(422, text="Unprocessable Entity")
            )

            # Act & Assert
            with autotests.step("Вызов create_link с невалидными данными"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                with pytest.raises(TargetSystemAPIError) as exc_info:
                    await client.create_link(PROJECT_ID, [])
                await client.client.aclose()

            with autotests.step("Проверка атрибутов ошибки"):
                assert exc_info.value.status_code == 422
                assert exc_info.value.response_body == "Unprocessable Entity"

    @autotests.num("334")
    @autotests.external_id("ac330001-0000-0000-0000-000000000005")
    @autotests.name("GNS3ApiClient: HTTP 500 вызывает TargetSystemAPIError")
    async def test_http_500_raises_api_error(self):
        """HTTP 500 Internal Server Error отображается в TargetSystemAPIError."""

        with respx.mock:
            respx.get("/v3/version").mock(
                return_value=httpx.Response(500, text="Internal Server Error")
            )

            # Act & Assert
            with autotests.step("Вызов get_version при серверной ошибке"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                with pytest.raises(TargetSystemAPIError) as exc_info:
                    await client.get_version()
                await client.client.aclose()

            with autotests.step("Проверка атрибутов ошибки"):
                assert exc_info.value.status_code == 500

    @autotests.num("335")
    @autotests.external_id("ac330001-0000-0000-0000-000000000006")
    @autotests.name("GNS3ApiClient: таймаут вызывает TargetSystemConnectionError")
    async def test_timeout_raises_connection_error(self):
        """httpx.ReadTimeout отображается в TargetSystemConnectionError."""

        with respx.mock:
            respx.get("/v3/version").mock(
                side_effect=httpx.ReadTimeout("Read timed out")
            )

            # Act & Assert
            with autotests.step("Вызов get_version при таймауте"):
                client = GNS3ApiClient(httpx.AsyncClient(base_url=BASE_URL))
                with pytest.raises(TargetSystemConnectionError):
                    await client.get_version()
                await client.client.aclose()
