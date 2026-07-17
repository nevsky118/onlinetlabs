import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from openclaw.client import OpenClawClient
from tests.settings.openclaw_gateway import (
    OpenClawGatewayServer,
    completion_response,
)

pytestmark = [pytest.mark.unit]


class TestOpenClawClient:
    @autotest.num("630")
    @autotest.external_id("193391a1-044a-4396-a7bf-da9d211a9784")
    @autotest.name("OpenClawClient: успешный chat completions запрос")
    async def test_193391a1_chat_completion_success(self):
        # Arrange
        with autotest.step("Готовим локальный OpenClaw Gateway"):
            server = OpenClawGatewayServer([completion_response("Проверь trunk порт")])

        # Act
        with server, autotest.step("Отправляем chat completions запрос"):
            async with OpenClawClient(
                base_url=server.base_url,
                token="secret-token",
                model="openclaw",
                timeout_seconds=3.0,
            ) as client:
                result = await client.complete(
                    messages=[{"role": "user", "content": "Нужна подсказка"}]
                )

        # Assert
        with autotest.step("Проверяем успешный результат"):
            assert_true(result.success, "запрос успешен")
            assert_equal(result.content, "Проверь trunk порт", "текст ответа")
            assert_equal(result.model, "openclaw", "model")
            assert_equal(result.usage["prompt_tokens"], 10, "prompt tokens")

        with autotest.step("Проверяем HTTP запрос"):
            assert_equal(server.requests[0]["path"], "/v1/chat/completions", "path")
            assert_equal(
                server.requests[0]["authorization"],
                "Bearer secret-token",
                "authorization",
            )
            assert_true(
                "Нужна".encode() in server.requests[0]["payload"],
                "payload содержит prompt",
            )

    @autotest.num("631")
    @autotest.external_id("cb1f1bc5-bfb5-4b5d-bcda-793e8978d05e")
    @autotest.name("OpenClawClient: invalid response возвращает ошибку")
    async def test_cb1f1bc5_invalid_response_error(self):
        # Arrange
        with autotest.step("Готовим некорректный ответ Gateway"):
            server = OpenClawGatewayServer([{"choices": []}])

        # Act
        with server, autotest.step("Отправляем запрос"):
            async with OpenClawClient(
                base_url=server.base_url,
                model="openclaw",
                timeout_seconds=3.0,
            ) as client:
                result = await client.complete(
                    messages=[{"role": "user", "content": "Нужна подсказка"}]
                )

        # Assert
        with autotest.step("Проверяем ошибку"):
            assert_true(not result.success, "запрос неуспешен")
            assert_equal(result.error_code, "openclaw_invalid_response", "код ошибки")

    @autotest.num("639")
    @autotest.external_id("61b2179e-c824-40dd-b11e-54524aa3e91c")
    @autotest.name("OpenClawClient: переиспользует TCP-соединение")
    async def test_61b2179e_reuses_tcp_connection(self):
        # Arrange
        with autotest.step("Готовим Gateway с двумя ответами"):
            server = OpenClawGatewayServer(
                [completion_response("OK 1"), completion_response("OK 2")]
            )

        # Act
        with server, autotest.step("Отправляем два запроса одним клиентом"):
            async with OpenClawClient(
                base_url=server.base_url,
                model="openclaw",
                timeout_seconds=3.0,
            ) as client:
                first = await client.complete(
                    messages=[{"role": "user", "content": "Первый запрос"}]
                )
                second = await client.complete(
                    messages=[{"role": "user", "content": "Второй запрос"}]
                )

        # Assert
        with autotest.step("Проверяем переиспользование keep-alive соединения"):
            client_ports = {request["client_address"][1] for request in server.requests}
            assert_true(first.success, "первый запрос успешен")
            assert_true(second.success, "второй запрос успешен")
            assert_equal(len(server.requests), 2, "количество запросов")
            assert_equal(len(client_ports), 1, "количество TCP-соединений")
