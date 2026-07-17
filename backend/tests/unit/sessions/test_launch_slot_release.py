"""POST /sessions: relaunching an already-active session doesn't leak a queue slot or double the gauge."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest

from rate_limit import limiter
from sessions.routers import commands as launch_mod

pytestmark = [pytest.mark.unit]

_CREDS = {
    "gns3_username": "student",
    "gns3_password": "pw",
    "gns3_url": "http://gns3/x",
    "gns3_deep_url": "http://gns3/x/deep",
}


class TestLaunchSlotRelease:
    @pytest.fixture(autouse=True)
    def _disable_limiter(self):
        # Call the handler directly, mute the slowapi decorator for the test.
        prev = limiter.enabled
        limiter.enabled = False
        yield
        limiter.enabled = prev

    def _mocks(self):
        queue = MagicMock()
        queue.try_acquire = AsyncMock(return_value=True)
        queue.enqueue = AsyncMock(return_value=1)
        queue.queue_depth = AsyncMock(return_value=1)
        queue.release = AsyncMock()
        monitor_registry = MagicMock()
        monitor_registry.start = AsyncMock()
        return queue, monitor_registry

    async def _call(self, queue, monitor_registry):
        return await launch_mod.launch_endpoint(
            request=SimpleNamespace(),
            body=SimpleNamespace(lab_slug="lab-x"),
            current_user={"id": "user-1"},
            _active={"id": "user-1"},
            db=MagicMock(),
            db_factory=MagicMock(),
            gns3_client=MagicMock(),
            monitor_registry=monitor_registry,
            queue=queue,
        )

    @autotest.num("2450")
    @autotest.external_id("453610e2-6dc4-468a-af57-3ccabab10902")
    @autotest.name("launch: релонч активной сессии не берёт слот и не инкрементит gauge")
    async def test_453610e2_reuse_does_not_leak_slot_or_double_count(self):
        queue, monitor_registry = self._mocks()
        existing = SimpleNamespace(id="s1", user_id="user-1", lab_slug="lab-x", status="active")
        with (
            patch.object(launch_mod, "get_active_session", AsyncMock(return_value=existing)),
            patch.object(launch_mod, "launch_session", AsyncMock(return_value=(existing, _CREDS))),
            patch.object(launch_mod, "build_session_context", MagicMock(return_value=object())),
            patch("observability.metrics.active_sessions_gauge") as gauge,
        ):
            with autotest.step("Act: релонч уже активной сессии"):
                resp = await self._call(queue, monitor_registry)

        with autotest.step(
            "Assert: слот не берётся/не освобождается, gauge и monitor не трогаются"
        ):
            queue.try_acquire.assert_not_awaited()
            queue.release.assert_not_awaited()
            monitor_registry.start.assert_not_awaited()
            gauge.labels.assert_not_called()
            assert resp.status == "active"

    @autotest.num("2451")
    @autotest.external_id("cbca5d12-5297-4d74-bc26-1c2b3862e671")
    @autotest.name("launch: новый запуск активной сессии инкрементит gauge ровно один раз")
    async def test_cbca5d12_new_launch_increments_gauge_once(self):
        queue, monitor_registry = self._mocks()
        new_sess = SimpleNamespace(id="s2", user_id="user-1", lab_slug="lab-x", status="active")
        with (
            patch.object(launch_mod, "get_active_session", AsyncMock(return_value=None)),
            patch.object(launch_mod, "launch_session", AsyncMock(return_value=(new_sess, _CREDS))),
            patch.object(launch_mod, "build_session_context", MagicMock(return_value=object())),
            patch("observability.metrics.active_sessions_gauge") as gauge,
        ):
            with autotest.step("Act: новый запуск"):
                await self._call(queue, monitor_registry)

        with autotest.step("Assert: слот взят, monitor стартует, gauge +1 ровно один раз"):
            queue.try_acquire.assert_awaited_once()
            monitor_registry.start.assert_awaited_once()
            gauge.labels.assert_called_once_with(lab_slug="lab-x")
            gauge.labels.return_value.inc.assert_called_once()
            queue.release.assert_not_awaited()
