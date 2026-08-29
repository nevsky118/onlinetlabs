"""One live session per learner and lab, and what happens to the launch that loses."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from config import settings
from i18n import DEFAULT_LOCALE, LocalizedError
from sessions.services.launch import _create_provisioning_row
from tests.settings.data.sessions_data import ConflictingDbSessionData, SqlCapturingDbData
from worker import reaper
from worker.reaper import STALE_PROVISIONING_MIN

pytestmark = [pytest.mark.unit]

_LEARNER = "user-launch-1"
_LAB = "lan-static-ip"


class TestLaunchConflict:
    """The database refuses a second live session; the learner must be told why."""

    @autotest.num("3453")
    @autotest.external_id("0bdccb6b-3526-4d39-bc0c-74c4ebac0583")
    @autotest.name("launch: a duplicate live session is a conflict, not a 502")
    async def test_0bdccb6b_duplicate_is_a_conflict(self):
        with autotest.step("Arrange: a db whose commit hits the unique index"):
            db = ConflictingDbSessionData()

        with autotest.step("Act: attempt the launch"):
            raised = None
            try:
                await _create_provisioning_row(lambda: db, _LEARNER, _LAB, DEFAULT_LOCALE)
            except LocalizedError as exc:
                raised = exc

        with autotest.step("Assert: a localized 409 rather than a bare failure"):
            assert_true(raised is not None, "LocalizedError was raised")
            assert_equal(raised.key, "error.session.already_launching", "code")
            assert_equal(raised.status_code, 409, "status 409")

    @autotest.num("3454")
    @autotest.external_id("08bb9628-945c-4094-8c5a-49832205f956")
    @autotest.name("launch: the losing transaction is rolled back")
    async def test_08bb9628_conflict_rolls_back(self):
        with autotest.step("Arrange: a db whose commit hits the unique index"):
            db = ConflictingDbSessionData()

        with autotest.step("Act: attempt the launch"):
            with pytest.raises(LocalizedError):
                await _create_provisioning_row(lambda: db, _LEARNER, _LAB, DEFAULT_LOCALE)

        with autotest.step("Assert: no transaction is left open"):
            assert_true(db.rolled_back, "rolled back")


class TestStaleProvisioning:
    """A crash between the row and its finalisation must not hold the slot for hours."""

    @autotest.num("3455")
    @autotest.external_id("daf62a90-faaf-4143-983e-692bc1746704")
    @autotest.name("reaper: the provisioning window is far shorter than the session deadline")
    def test_daf62a90_provisioning_window_is_short(self):
        with autotest.step("Arrange: the configured session lifetime"):
            session_minutes = settings.capacity.session_max_hours * 60

        with autotest.step("Assert: debris is collected in minutes, not hours"):
            assert_true(session_minutes > STALE_PROVISIONING_MIN, "shorter than the deadline")
            assert_true(STALE_PROVISIONING_MIN >= 5, "longer than a real provisioning run")

    @autotest.num("3456")
    @autotest.external_id("3070f635-fade-4790-9059-527df3eba79b")
    @autotest.name("reaper: a stale provisioning row is ended even with a future deadline")
    async def test_3070f635_stale_provisioning_is_reaped(self):
        with autotest.step("Arrange: a database that records the reaper's own query"):
            db = SqlCapturingDbData()
            window = datetime.now(UTC) - timedelta(minutes=STALE_PROVISIONING_MIN)

        with autotest.step("Act: run one reap pass"):
            with patch.object(reaper, "async_session", lambda: db):
                await reaper.reap_expired_sessions(AsyncMock(), MagicMock())

        with autotest.step("Assert: the query also matches provisioning rows by age"):
            assert_equal(len(db.statements), 1, "one query per pass")
            sql = db.statements[0]
            assert_true("started_at" in sql, "filters on start time")
            assert_true("status" in sql, "filters on status")
            assert_true(window < datetime.now(UTC), "the window lies in the past")
