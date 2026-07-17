import json

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from agents.orchestrator.models import InterventionInput
from openclaw.adapter import OpenClawInterventionAdapter
from openclaw.client import OpenClawClient
from tests.settings.data.analytics_data import AgentContextData
from tests.settings.openclaw_gateway import (
    OpenClawGatewayServer,
    completion_response,
)

pytestmark = [pytest.mark.unit]


class TestOpenClawInterventionAdapter:
    @autotest.num("632")
    @autotest.external_id("f8cfa673-0e46-455c-b0ff-e0623e7a954f")
    @autotest.name("OpenClawInterventionAdapter: генерирует hint ответ")
    async def test_f8cfa673_generate_hint_response(self):
        # Arrange
        with autotest.step("Готовим input интервенции и локальный OpenClaw Gateway"):
            agent_context = AgentContextData().context
            server = OpenClawGatewayServer([completion_response("Проверь trunk на SW1")])
            intervention = InterventionInput(
                session_id="s1",
                user_id="u1",
                intervention_type="hint",
                context={
                    "lab_slug": "ospf-vlan-lab",
                    "step_slug": "step-2",
                    "struggle_type": "repeating_errors",
                    "dominant_error": "trunk down",
                    "attempts_count": 3,
                    "last_error": "trunk down",
                    "agent_context": agent_context,
                },
            )

        # Act
        with server:
            with autotest.step("Генерируем интервенцию через OpenClaw"):
                async with OpenClawClient(
                    base_url=server.base_url,
                    model="openclaw",
                    timeout_seconds=3.0,
                ) as client:
                    adapter = OpenClawInterventionAdapter(client)
                    result = await adapter.generate(intervention)

        # Assert
        with autotest.step("Проверяем нормализованный ответ"):
            assert_true(result.success, "успешный ответ")
            assert_equal(result.agent_used, "openclaw", "agent_used")
            assert_equal(result.agent_backend, "openclaw", "agent_backend")
            assert_equal(result.data["hint"], "Проверь trunk на SW1", "hint")
            assert_equal(result.metadata["model"], "openclaw", "model")

        with autotest.step("Проверяем нормализованный prompt"):
            payload = json.loads(server.requests[0]["payload"])
            user_message = payload["messages"][1]["content"]
            assert_true("step-2" in user_message, "prompt содержит step_slug")
            assert_true("trunk down" in user_message, "prompt содержит ошибку")
            assert_true(
                agent_context.to_prompt() in user_message,
                "prompt содержит сериализованный AgentContext",
            )

    @autotest.num("633")
    @autotest.external_id("b7e241f2-f1fd-41c4-86ef-70312a3fe85d")
    @autotest.name("OpenClawInterventionAdapter: не делает fallback при ошибке")
    async def test_b7e241f2_generate_error_without_fallback(self):
        # Arrange
        with autotest.step("Готовим некорректный ответ OpenClaw Gateway"):
            server = OpenClawGatewayServer([{"choices": []}])
            intervention = InterventionInput(
                session_id="s1",
                user_id="u1",
                intervention_type="hint",
                context={"step_slug": "step-2", "attempts_count": 3},
            )

        # Act
        with server:
            with autotest.step("Генерируем интервенцию через OpenClaw"):
                async with OpenClawClient(
                    base_url=server.base_url,
                    model="openclaw",
                    timeout_seconds=3.0,
                ) as client:
                    adapter = OpenClawInterventionAdapter(client)
                    result = await adapter.generate(intervention)

        # Assert
        with autotest.step("Проверяем ошибку без fallback"):
            assert_true(not result.success, "ответ неуспешен")
            assert_equal(result.agent_used, "openclaw", "agent_used")
            assert_equal(result.agent_backend, "openclaw", "agent_backend")
            assert_equal(
                result.metadata["error_code"],
                "openclaw_invalid_response",
                "error_code",
            )
