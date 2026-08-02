"""D4: raw evidence capture, helper plus hook into the collector's poll cycle."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.config_model import LearningAnalyticsConfig
from learning_analytics.collector import BehavioralCollector
from models.session_evidence_snapshot import SessionEvidenceSnapshot

pytestmark = [pytest.mark.unit]


async def _sqlite_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SessionEvidenceSnapshot.__table__.create)
    return async_sessionmaker(engine, expire_on_commit=False)


def _collector(sf, *, evidence_enabled):
    cfg = LearningAnalyticsConfig()
    cfg.evidence_capture_enabled = evidence_enabled
    c = BehavioralCollector(
        mcp_client=MagicMock(),
        db_factory=sf,
        learning_analytics_config=cfg,
    )
    c._session_id = "s1"
    c._user_id = "u1"
    c._lab_slug = "lab-gns3"
    c._ctx = MagicMock()
    return c


class TestEvidenceCapture:
    @autotest.num("1977")
    @autotest.external_id("87aa2cb9-d207-4028-9a72-02c16d3f6e05")
    @autotest.name("capture_snapshot: writes a snapshot, coerces datetime to JSON-safe")
    async def test_87aa2cb9_capture_snapshot_json_safe(self):
        with autotest.step("Arrange: real sqlite"):
            from learning_analytics.evidence import capture_snapshot

            sf = await _sqlite_factory()
            ts = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)

        with autotest.step("Act: write a snapshot with datetime in the payload"):
            async with sf() as db:
                await capture_snapshot(
                    db,
                    "s1",
                    "u1",
                    "lab",
                    kind="mcp_events",
                    payload={"events": [{"action": "ping", "timestamp": ts}]},
                )

        with autotest.step("Assert: 1 snapshot, correct kind, datetime became a string"):
            async with sf() as db:
                rows = (await db.execute(select(SessionEvidenceSnapshot))).scalars().all()
            assert_equal(len(rows), 1, f"1 snapshot; got {len(rows)}")
            assert_equal(rows[0].kind, "mcp_events", "kind == mcp_events")
            ev = rows[0].payload["events"][0]
            assert_equal(ev["action"], "ping", "payload preserved")
            assert_true(
                isinstance(ev["timestamp"], str), "datetime coerced to a string (JSON-safe)"
            )

    @autotest.num("1978")
    @autotest.external_id("428437ae-f3d6-4f75-8b22-9ddd7d8aa879")
    @autotest.name("Collector: evidence_capture_enabled=True → poll cycle writes a snapshot")
    async def test_428437ae_poll_captures_when_enabled(self):
        with autotest.step("Arrange: collector with capture, _persist mocked, events present"):
            sf = await _sqlite_factory()
            c = _collector(sf, evidence_enabled=True)
            c._persist = AsyncMock()

        with autotest.step("Act: _poll_cycle with one action"):
            with (
                patch.object(c, "_fetch_actions", AsyncMock(return_value=[{"action": "ping"}])),
                patch.object(c, "_fetch_logs", AsyncMock(return_value=[])),
                patch.object(c, "_fetch_errors", AsyncMock(return_value=[])),
            ):
                await c._poll_cycle()

        with autotest.step("Assert: exactly 1 evidence snapshot"):
            async with sf() as db:
                rows = (await db.execute(select(SessionEvidenceSnapshot))).scalars().all()
            assert_equal(len(rows), 1, f"1 snapshot; got {len(rows)}")

    @autotest.num("1979")
    @autotest.external_id("ea2133f1-54f3-4b7c-aacb-d13130cbfb73")
    @autotest.name("Collector: evidence_capture_enabled=False → snapshots are NOT written")
    async def test_ea2133f1_poll_no_capture_when_disabled(self):
        with autotest.step("Arrange: collector without capture"):
            sf = await _sqlite_factory()
            c = _collector(sf, evidence_enabled=False)
            c._persist = AsyncMock()

        with autotest.step("Act: _poll_cycle with one action"):
            with (
                patch.object(c, "_fetch_actions", AsyncMock(return_value=[{"action": "ping"}])),
                patch.object(c, "_fetch_logs", AsyncMock(return_value=[])),
                patch.object(c, "_fetch_errors", AsyncMock(return_value=[])),
            ):
                await c._poll_cycle()

        with autotest.step("Assert: zero evidence snapshots"):
            async with sf() as db:
                rows = (await db.execute(select(SessionEvidenceSnapshot))).scalars().all()
            assert_equal(len(rows), 0, "capture disabled → 0 snapshots")
