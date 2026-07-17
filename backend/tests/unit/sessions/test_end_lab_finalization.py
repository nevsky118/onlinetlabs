"""end_lab: a student finishing a lab must capture experiment measurements.

Regression: `POST /sessions/{id}/end` → `end_lab` tore down GNS3 and stopped the
monitor, but did NOT finalize ExperimentMetrics or censor MRT points — the A/B
and cohort layer never got populated for a single real student. Plus the monitor
was stopped after teardown, so late interventions never made it into the metrics snapshot.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from sessions.services.lifecycle import end_lab

pytestmark = [pytest.mark.unit]

_SESSION_ID = "sess-1111"
_USER_ID = "user-2222"


def _fake_session():
    session = MagicMock()
    session.id = _SESSION_ID
    session.lab_slug = "lan-static-ip"
    session.meta = {"gns3_service_session_id": "gsess-3333"}
    return session


def _patch_queue():
    """Queue singleton: release() is expected to be awaited."""
    queue = MagicMock()
    queue.release = AsyncMock()
    return patch("sessions.queue._get_or_create_singleton", new=MagicMock(return_value=queue))


class TestEndLabFinalization:
    @autotest.num("2013")
    @autotest.external_id("278a94ca-ff0b-4be0-817f-0303eec9b85f")
    @autotest.name("end_lab: финализирует измерения эксперимента (метрики не теряются)")
    async def test_278a94ca_finalizes_experiment_measurements(self):
        with autotest.step("Arrange: живая сессия, монитор и gns3-клиент"):
            db, monitor_registry, gns3_client = AsyncMock(), AsyncMock(), AsyncMock()

        with autotest.step("Act: студент завершает лабу"):
            with (
                patch(
                    "sessions.services.lifecycle.get_owned_session",
                    new=AsyncMock(return_value=_fake_session()),
                ),
                patch(
                    "sessions.services.lifecycle._mark_ended_and_finalize", new=AsyncMock()
                ) as finalize,
                _patch_queue(),
            ):
                ok = await end_lab(db, _SESSION_ID, _USER_ID, gns3_client, monitor_registry)

        with autotest.step("Assert: финализация вызвана со статусом ended"):
            assert_true(ok, "end_lab вернул True")
            finalize.assert_awaited_once()
            assert_equal(finalize.await_args.kwargs["status"], "ended", "status")

    @autotest.num("2014")
    @autotest.external_id("a3c8ef40-7a93-45ca-a520-81272012159c")
    @autotest.name("end_lab: монитор гасится ДО снятия метрик (поздние интервенции не теряются)")
    async def test_a3c8ef40_stops_monitor_before_finalizing(self):
        with autotest.step("Arrange: записываем порядок вызовов"):
            calls: list[str] = []
            db, gns3_client = AsyncMock(), AsyncMock()
            monitor_registry = AsyncMock()
            monitor_registry.stop = AsyncMock(side_effect=lambda *_: calls.append("stop_monitor"))

            async def _finalize(*_args, **_kwargs):
                calls.append("finalize")

        with autotest.step("Act: завершаем лабу"):
            with (
                patch(
                    "sessions.services.lifecycle.get_owned_session",
                    new=AsyncMock(return_value=_fake_session()),
                ),
                patch(
                    "sessions.services.lifecycle._mark_ended_and_finalize",
                    new=AsyncMock(side_effect=_finalize),
                ),
                _patch_queue(),
            ):
                await end_lab(db, _SESSION_ID, _USER_ID, gns3_client, monitor_registry)

        with autotest.step("Assert: сначала стоп монитора, затем финализация"):
            assert_equal(calls, ["stop_monitor", "finalize"], "порядок шагов")

    @autotest.num("2015")
    @autotest.external_id("f427fd95-53c4-4ed0-b438-87cd4b44ee61")
    @autotest.name("end_lab: измерения снимаются ДО teardown'а GNS3")
    async def test_f427fd95_finalizes_before_gns3_teardown(self):
        with autotest.step("Arrange: пишем порядок финализации и teardown'а"):
            calls: list[str] = []
            db, monitor_registry = AsyncMock(), AsyncMock()
            gns3_client = AsyncMock()
            gns3_client.delete_session = AsyncMock(side_effect=lambda *_: calls.append("teardown"))

            async def _finalize(*_args, **_kwargs):
                calls.append("finalize")

        with autotest.step("Act: завершаем лабу"):
            with (
                patch(
                    "sessions.services.lifecycle.get_owned_session",
                    new=AsyncMock(return_value=_fake_session()),
                ),
                patch(
                    "sessions.services.lifecycle._mark_ended_and_finalize",
                    new=AsyncMock(side_effect=_finalize),
                ),
                _patch_queue(),
            ):
                await end_lab(db, _SESSION_ID, _USER_ID, gns3_client, monitor_registry)

        with autotest.step("Assert: метрики сняты раньше сноса GNS3"):
            assert_equal(calls, ["finalize", "teardown"], "порядок шагов")

    @autotest.num("2016")
    @autotest.external_id("8209e3be-b9a6-4515-b48a-8e06030a2453")
    @autotest.name("end_lab: сбой teardown'а GNS3 не теряет измерения")
    async def test_8209e3be_gns3_teardown_failure_keeps_measurements(self):
        with autotest.step("Arrange: gns3-клиент падает на удалении сессии"):
            db, monitor_registry = AsyncMock(), AsyncMock()
            gns3_client = AsyncMock()
            gns3_client.delete_session = AsyncMock(side_effect=RuntimeError("gns3 down"))

        with autotest.step("Act: завершаем лабу"):
            with (
                patch(
                    "sessions.services.lifecycle.get_owned_session",
                    new=AsyncMock(return_value=_fake_session()),
                ),
                patch(
                    "sessions.services.lifecycle._mark_ended_and_finalize", new=AsyncMock()
                ) as finalize,
                _patch_queue(),
            ):
                ok = await end_lab(db, _SESSION_ID, _USER_ID, gns3_client, monitor_registry)

        with autotest.step("Assert: лаба завершена, измерения записаны несмотря на сбой"):
            assert_true(ok, "end_lab вернул True")
            finalize.assert_awaited_once()
