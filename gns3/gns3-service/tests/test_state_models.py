"""Unit-тесты Pydantic-моделей state."""

from datetime import datetime, timezone

from src.models import (
    LinkEndpoint,
    LinkState,
    NodeState,
    SessionMetrics,
    SessionStateResponse,
)


class TestNodeState:
    """Конструирование NodeState."""

    def test_node_state_parses(self):
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
        assert node.status == "started"


class TestSessionStateResponse:
    """Конструирование агрегированного state-ответа."""

    def test_session_state_response_constructs(self):
        state = SessionStateResponse(
            session_id="abc",
            project_id="proj1",
            status="active",
            started_at=datetime.now(timezone.utc),
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
        assert state.metrics.nodes_started == 1
        assert len(state.links[0].nodes) == 2
