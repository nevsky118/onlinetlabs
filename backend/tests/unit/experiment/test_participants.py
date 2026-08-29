"""The participant roster must not issue a query per participant."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from experiment.service import get_participants
from models.identity import User
from models.learning import LearningSession
from models.research import ExperimentMetrics
from tests.settings.data.experiment_data import ParticipantRosterData, UnfinishedParticipantData

pytestmark = [pytest.mark.unit]


class TestParticipantRoster:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(LearningSession.__table__.create)
            await conn.run_sync(ExperimentMetrics.__table__.create)
        self.statements: list[str] = []
        event.listen(self.engine.sync_engine, "before_cursor_execute", self._record)
        yield
        event.remove(self.engine.sync_engine, "before_cursor_execute", self._record)
        await self.engine.dispose()

    def _record(self, conn, cursor, statement, parameters, context, executemany):
        """Counts every statement the roster sends to the database."""
        self.statements.append(statement)

    async def _seed(self, rows: list) -> None:
        """Writes a prepared cohort to the database."""
        async with self.session_factory() as db:
            db.add_all(rows)
            await db.commit()

    @autotest.num("3457")
    @autotest.external_id("6b4e0a19-8c2d-4f37-a5b1-9d0e7c4f2a68")
    @autotest.name("roster: only enrolled users, with session count and latest metrics")
    async def test_6b4e0a19_roster_contents(self):
        with autotest.step("Arrange: three enrolled users and one outsider"):
            data = ParticipantRosterData(3)
            await self._seed(data.rows)

        with autotest.step("Act: read the roster"):
            async with self.session_factory() as db:
                rows = await get_participants(db)

        with autotest.step("Assert: the outsider is absent and the aggregates are attached"):
            assert_equal(
                sorted(rowow_2ow_3ow_4["user_id"] for rowow_2ow_3ow_4 in rows),
                data.user_ids,
                "enrolled only",
            )
            assert_equal(
                {rowow_2ow_3ow_4["sessions_count"] for rowow_2ow_3ow_4 in rows},
                {1},
                "one session each",
            )
            assert_equal(
                {rowow_2ow_3ow_4["completed"] for rowow_2ow_3ow_4 in rows},
                {True},
                "completion carried over",
            )
            assert_equal(
                {rowow_2ow_3ow_4["total_time_seconds"] for rowow_2ow_3ow_4 in rows},
                {600.0},
                "time carried over",
            )

    @autotest.num("3458")
    @autotest.external_id("f1c8d5b2-30a4-4e69-b7d3-52ac9e18f047")
    @autotest.name("roster: the query count does not grow with the number of participants")
    async def test_f1c8d5b2_roster_is_not_n_plus_one(self):
        with autotest.step("Arrange: two enrolled users"):
            await self._seed(ParticipantRosterData(2).rows)

        with autotest.step("Act: read the roster and count the statements"):
            self.statements.clear()
            async with self.session_factory() as db:
                await get_participants(db)
            small = len(self.statements)

        with autotest.step("Arrange: twelve more enrolled users"):
            await self._seed(ParticipantRosterData(12, prefix="w").rows)

        with autotest.step("Act: read the roster again"):
            self.statements.clear()
            async with self.session_factory() as db:
                rows = await get_participants(db)
            large = len(self.statements)

        with autotest.step("Assert: same statement count, seven times the rows"):
            assert_equal(len(rows), 14, "fourteen participants")
            assert_equal(large, small, "flat query count")
            assert_true(large <= 3, "one query per aggregate")

    @autotest.num("3459")
    @autotest.external_id("c9a7f462-1b58-4d0e-83f6-27e4b5c9a013")
    @autotest.name("roster: a participant with no metrics still appears")
    async def test_c9a7f462_metricsless_participant(self):
        with autotest.step("Arrange: an enrolled user who never finished a session"):
            await self._seed([UnfinishedParticipantData().row])

        with autotest.step("Act: read the roster"):
            async with self.session_factory() as db:
                rows = await get_participants(db)

        with autotest.step("Assert: present, with empty aggregates rather than an error"):
            assert_equal(len(rows), 1, "one participant")
            assert_equal(rows[0]["sessions_count"], 0, "no sessions")
            assert_equal(rows[0]["completed"], False, "not completed")
            assert_equal(rows[0]["total_time_seconds"], None, "no recorded time")
