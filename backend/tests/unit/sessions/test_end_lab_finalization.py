"""end_lab: a student finishing a lab must capture experiment measurements.

Regression: `POST /sessions/{id}/end` → `end_lab` tore down GNS3 and stopped the
monitor, but did NOT finalize ExperimentMetrics or censor MRT points, so the A/B
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
    return patch(
        "sessions.services.lifecycle._get_or_create_singleton",
        new=MagicMock(return_value=queue),
    )


class TestEndLabFinalization:
    @autotest.num("2013")
    @autotest.external_id("278a94ca-ff0b-4be0-817f-0303eec9b85f")
    @autotest.name("end_lab: finalizes experiment measurements (metrics are not lost)")
    async def test_278a94ca_finalizes_experiment_measurements(self):
        with autotest.step("Arrange: live session, monitor, and gns3 client"):
            db, monitor_registry, gns3_client = AsyncMock(), AsyncMock(), AsyncMock()

        with autotest.step("Act: student finishes the lab"):
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

        with autotest.step("Assert: finalization called with status ended"):
            assert_true(ok, "end_lab returned True")
            finalize.assert_awaited_once()
            assert_equal(finalize.await_args.kwargs["status"], "ended", "status")

    @autotest.num("2014")
    @autotest.external_id("a3c8ef40-7a93-45ca-a520-81272012159c")
    @autotest.name(
        "end_lab: monitor stops BEFORE metrics are captured (late interventions not lost)"
    )
    async def test_a3c8ef40_stops_monitor_before_finalizing(self):
        with autotest.step("Arrange: record the call order"):
            calls: list[str] = []
            db, gns3_client = AsyncMock(), AsyncMock()
            monitor_registry = AsyncMock()
            monitor_registry.stop = AsyncMock(side_effect=lambda *_: calls.append("stop_monitor"))

            async def _finalize(*_args, **_kwargs):
                calls.append("finalize")

        with autotest.step("Act: finish the lab"):
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

        with autotest.step("Assert: monitor stops first, then finalization"):
            assert_equal(calls, ["stop_monitor", "finalize"], "step order")

    @autotest.num("2015")
    @autotest.external_id("f427fd95-53c4-4ed0-b438-87cd4b44ee61")
    @autotest.name("end_lab: measurements are captured BEFORE GNS3 teardown")
    async def test_f427fd95_finalizes_before_gns3_teardown(self):
        with autotest.step("Arrange: record finalization and teardown order"):
            calls: list[str] = []
            db, monitor_registry = AsyncMock(), AsyncMock()
            gns3_client = AsyncMock()
            gns3_client.delete_session = AsyncMock(side_effect=lambda *_: calls.append("teardown"))

            async def _finalize(*_args, **_kwargs):
                calls.append("finalize")

        with autotest.step("Act: finish the lab"):
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

        with autotest.step("Assert: metrics captured before GNS3 teardown"):
            assert_equal(calls, ["finalize", "teardown"], "step order")

    @autotest.num("2016")
    @autotest.external_id("8209e3be-b9a6-4515-b48a-8e06030a2453")
    @autotest.name("end_lab: GNS3 teardown failure does not lose measurements")
    async def test_8209e3be_gns3_teardown_failure_keeps_measurements(self):
        with autotest.step("Arrange: gns3 client fails on session deletion"):
            db, monitor_registry = AsyncMock(), AsyncMock()
            gns3_client = AsyncMock()
            gns3_client.delete_session = AsyncMock(side_effect=RuntimeError("gns3 down"))

        with autotest.step("Act: finish the lab"):
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

        with autotest.step("Assert: lab finished, measurements recorded despite the failure"):
            assert_true(ok, "end_lab returned True")
            finalize.assert_awaited_once()
