"""Unit tests for SessionService.get_state, aggregation and cache."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from src.db.models import Session, SessionStatus
from src.services.session_lifecycle import SessionService
from tests.settings.data.gns3_data import Gns3LinkData, Gns3NodeData

pytestmark = [pytest.mark.unit]


def _make_active_session(uptime_seconds: int = 0):
    session = MagicMock(spec=Session)
    session.id = "11111111-1111-1111-1111-111111111111"
    session.gns3_project_id = "proj1"
    session.status = SessionStatus.ACTIVE
    session.created_at = datetime.now(UTC) - timedelta(seconds=uptime_seconds)
    return session


class TestSessionServiceGetState:
    """Unit tests for SessionService.get_state."""

    @pytest.mark.asyncio
    @autotest.num("3375")
    @autotest.external_id("2b22cac8-02ce-45d2-b0ee-17cceb820761")
    @autotest.name("SessionService.get_state: aggregates nodes, started count, links and uptime")
    async def test_2b22cac8_get_state_aggregates_nodes_and_links(self):
        with autotest.step("Arrange: admin reports two nodes and one link for an active session"):
            admin = AsyncMock()
            admin.get_nodes.return_value = [
                Gns3NodeData(
                    node_id="n1",
                    name="R1",
                    node_type="dynamips",
                    status="started",
                    console=5000,
                    symbol=":/symbols/router.svg",
                ).data,
                Gns3NodeData(
                    node_id="n2",
                    name="R2",
                    node_type="dynamips",
                    status="stopped",
                    console=5001,
                    symbol=":/symbols/router.svg",
                ).data,
            ]
            admin.get_links.return_value = [
                Gns3LinkData(
                    link_id="l1",
                    nodes=[
                        {"node_id": "n1", "adapter_number": 0, "port_number": 0},
                        {"node_id": "n2", "adapter_number": 0, "port_number": 0},
                    ],
                ).data,
            ]
            service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")

            db = AsyncMock()
            db.get.return_value = _make_active_session(uptime_seconds=42)

        with autotest.step("Act: get the session state"):
            state = await service.get_state(db, "11111111-1111-1111-1111-111111111111")

        with autotest.step("Assert: nodes, started count, links and uptime are aggregated"):
            assert_equal(state.session_id, "11111111-1111-1111-1111-111111111111", "session id")
            assert_equal(state.metrics.nodes_total, 2, "nodes total")
            assert_equal(state.metrics.nodes_started, 1, "nodes started")
            assert_equal(state.metrics.links_count, 1, "links count")
            assert_true(
                40 <= state.metrics.uptime_seconds <= 45, "40 <= state.metrics.uptime_seconds <= 45"
            )

    @pytest.mark.asyncio
    @autotest.num("3376")
    @autotest.external_id("41a03ebf-7ec9-4963-bfe3-967da535b485")
    @autotest.name("SessionService.get_state: raises when the session is not found")
    async def test_41a03ebf_get_state_raises_when_session_not_found(self):
        with autotest.step("Arrange: no session found for the id"):
            service = SessionService(admin_client=AsyncMock(), gns3_url="http://gns3:3080")
            db = AsyncMock()
            db.get.return_value = None

        with autotest.step("Act + Assert: getting state for a missing session raises"):
            with pytest.raises(ValueError, match="not found"):
                await service.get_state(db, "00000000-0000-0000-0000-000000000000")


class TestSessionServiceStateCache:
    """Unit tests for state snapshot caching."""

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
    @autotest.num("3377")
    @autotest.external_id("23d023a3-c898-46eb-b10c-762dd6e73739")
    @autotest.name("SessionService.get_state: hits the cache within the TTL")
    async def test_23d023a3_get_state_hits_cache_within_ttl(self, service_and_db):
        with autotest.step("Arrange: unpack the service, admin mock and db"):
            service, admin, db = service_and_db

        with autotest.step("Act: get the state for the same session twice"):
            await service.get_state(db, "11111111-1111-1111-1111-111111111111")
            await service.get_state(db, "11111111-1111-1111-1111-111111111111")

        with autotest.step("Assert: the second call is served from cache, admin hit once"):
            assert_equal(admin.get_nodes.call_count, 1, "call count")

    @pytest.mark.asyncio
    @autotest.num("3378")
    @autotest.external_id("8bd955db-32cc-47f3-a73a-ecaee6c06638")
    @autotest.name("SessionService.invalidate_state_cache: clears the cached entry")
    async def test_8bd955db_invalidate_state_cache_clears_entry(self, service_and_db):
        with autotest.step("Arrange: unpack the service, admin mock and db"):
            service, admin, db = service_and_db

        with autotest.step("Act: get the state, invalidate the cache, then get it again"):
            await service.get_state(db, "11111111-1111-1111-1111-111111111111")
            service.invalidate_state_cache("11111111-1111-1111-1111-111111111111")
            await service.get_state(db, "11111111-1111-1111-1111-111111111111")

        with autotest.step("Assert: invalidation forced a second admin call"):
            assert_equal(admin.get_nodes.call_count, 2, "call count")
