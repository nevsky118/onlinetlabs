import pytest

"""Unit tests for the state Pydantic models."""

from datetime import UTC, datetime

from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from src.models import (
    LinkEndpoint,
    LinkState,
    NodeState,
    SessionMetrics,
    SessionStateResponse,
)

pytestmark = [pytest.mark.unit]


class TestNodeState:
    """Constructing a NodeState."""

    @autotest.num("3379")
    @autotest.external_id("188a8d27-61a6-4a7e-ad74-0800703ca48f")
    @autotest.name("NodeState: parses and preserves the status field")
    def test_188a8d27_node_state_parses(self):
        with autotest.step("Act: construct a NodeState"):
            node = NodeState(
                id="abc",
                name="R1",
                node_type="dynamips",
                status="started",
                console=5000,
                console_type="telnet",
                console_host="localhost",
                symbol=":/symbols/router.svg",
            )

        with autotest.step("Assert: the status is preserved"):
            assert_equal(node.status, "started", "status")


class TestSessionStateResponse:
    """Constructing the aggregated state response."""

    @autotest.num("3380")
    @autotest.external_id("f98a934e-5250-41f6-9614-68e6d53b0d4c")
    @autotest.name("SessionStateResponse: constructs with metrics and link endpoints preserved")
    def test_f98a934e_session_state_response_constructs(self):
        with autotest.step("Act: construct a SessionStateResponse with a node and a link"):
            state = SessionStateResponse(
                session_id="abc",
                project_id="proj1",
                status="active",
                started_at=datetime.now(UTC),
                nodes=[
                    NodeState(
                        id="n1",
                        name="R1",
                        node_type="dynamips",
                        status="started",
                        console=5000,
                        console_type="telnet",
                        console_host="localhost",
                        symbol=":/symbols/router.svg",
                    ),
                ],
                links=[
                    LinkState(
                        id="l1",
                        nodes=[
                            LinkEndpoint(node_id="n1", adapter_number=0, port_number=0),
                            LinkEndpoint(node_id="n2", adapter_number=0, port_number=0),
                        ],
                    ),
                ],
                metrics=SessionMetrics(
                    nodes_total=1,
                    nodes_started=1,
                    links_count=1,
                    uptime_seconds=42,
                ),
            )

        with autotest.step("Assert: the metrics and link endpoints are preserved"):
            assert_equal(state.metrics.nodes_started, 1, "nodes started")
            assert_equal(len(state.links[0].nodes), 2, "nodes count")
