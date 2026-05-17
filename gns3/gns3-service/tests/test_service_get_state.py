"""Unit-тесты SessionService.get_state — агрегация и кэш."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.db.models import Session, SessionStatus
from src.service import SessionService


def _make_active_session(uptime_seconds: int = 0):
    session = MagicMock(spec=Session)
    session.id = "11111111-1111-1111-1111-111111111111"
    session.gns3_project_id = "proj1"
    session.status = SessionStatus.ACTIVE
    session.created_at = datetime.now(timezone.utc) - timedelta(seconds=uptime_seconds)
    return session


class TestSessionServiceGetState:
    """Unit-тесты SessionService.get_state."""

    @pytest.mark.asyncio
    async def test_get_state_aggregates_nodes_and_links(self, gns3_node, gns3_link):
        admin = AsyncMock()
        admin.get_nodes.return_value = [
            gns3_node(node_id="n1", name="R1", node_type="dynamips", status="started",
                      console=5000, symbol=":/symbols/router.svg"),
            gns3_node(node_id="n2", name="R2", node_type="dynamips", status="stopped",
                      console=5001, symbol=":/symbols/router.svg"),
        ]
        admin.get_links.return_value = [
            gns3_link(link_id="l1", nodes=[
                {"node_id": "n1", "adapter_number": 0, "port_number": 0},
                {"node_id": "n2", "adapter_number": 0, "port_number": 0},
            ]),
        ]
        service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")

        db = AsyncMock()
        db.get.return_value = _make_active_session(uptime_seconds=42)

        state = await service.get_state(db, "11111111-1111-1111-1111-111111111111")
        assert state.session_id == "11111111-1111-1111-1111-111111111111"
        assert state.metrics.nodes_total == 2
        assert state.metrics.nodes_started == 1
        assert state.metrics.links_count == 1
        assert 40 <= state.metrics.uptime_seconds <= 45

    @pytest.mark.asyncio
    async def test_get_state_raises_when_session_not_found(self):
        service = SessionService(admin_client=AsyncMock(), gns3_url="http://gns3:3080")
        db = AsyncMock()
        db.get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await service.get_state(db, "00000000-0000-0000-0000-000000000000")


class TestSessionServiceStateCache:
    """Unit-тесты кэширования state-снапшота."""

    @pytest.fixture
    def service_and_db(self):
        admin = AsyncMock()
        admin.get_nodes.return_value = []
        admin.get_links.return_value = []
        service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")
        db = AsyncMock()
        db.get.return_value = _make_active_session()
        return service, admin, db

    @pytest.mark.asyncio
    async def test_get_state_hits_cache_within_ttl(self, service_and_db):
        service, admin, db = service_and_db
        await service.get_state(db, "11111111-1111-1111-1111-111111111111")
        await service.get_state(db, "11111111-1111-1111-1111-111111111111")
        assert admin.get_nodes.call_count == 1

    @pytest.mark.asyncio
    async def test_invalidate_state_cache_clears_entry(self, service_and_db):
        service, admin, db = service_and_db
        await service.get_state(db, "11111111-1111-1111-1111-111111111111")
        service.invalidate_state_cache("11111111-1111-1111-1111-111111111111")
        await service.get_state(db, "11111111-1111-1111-1111-111111111111")
        assert admin.get_nodes.call_count == 2
