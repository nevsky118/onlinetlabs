"""Unit tests for the age-based console retention purge."""

import asyncio
from datetime import timedelta

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from src.console_retention import purge_console_history, run_console_retention
from tests.settings.data.console_data import (
    ConsoleRetentionDbData,
    ConsoleRetentionRowReaderData,
    ConsoleRetentionScenarioData,
    ConsoleRetentionSweepWatchData,
)

pytestmark = [pytest.mark.unit]


class TestConsoleRetention:
    @autotest.num("3558")
    @autotest.external_id("2a991287-7e00-420c-a86e-9227227aeb02")
    @autotest.name("purge_console_history: rows older than the window are deleted in both tables")
    async def test_2a991287_purge_deletes_only_rows_older_than_the_window(self):
        with autotest.step("Arrange: an old and a fresh row in each console table"):
            (
                db_factory,
                fresh_chunk_id,
                fresh_command_id,
            ) = await ConsoleRetentionScenarioData.with_old_and_fresh_rows()

        with autotest.step("Act: purge everything older than a day"):
            deleted = await purge_console_history(db_factory, timedelta(days=1))

        with autotest.step("Assert: the old rows went, the fresh ones stayed, in both tables"):
            assert_equal(deleted, 2, "one row deleted per table")
            assert_equal(
                await ConsoleRetentionRowReaderData.chunk_ids(db_factory),
                [fresh_chunk_id],
                "fresh chunk row kept",
            )
            assert_equal(
                await ConsoleRetentionRowReaderData.command_ids(db_factory),
                [fresh_command_id],
                "fresh command row kept",
            )

    @autotest.num("3559")
    @autotest.external_id("d205fc51-69af-4590-a4be-e74a4b80f512")
    @autotest.name("purge_console_history: a live session's rows survive regardless of age")
    async def test_d205fc51_purge_never_deletes_a_row_on_an_active_session(self):
        with autotest.step("Arrange: an old row on a session that is still active"):
            (
                db_factory,
                row_id,
            ) = await ConsoleRetentionScenarioData.with_one_old_row_on_an_active_session()

        with autotest.step("Act: purge everything older than a day"):
            deleted = await purge_console_history(db_factory, timedelta(days=1))

        with autotest.step("Assert: nothing was deleted, the row survives"):
            assert_equal(deleted, 0, "no rows deleted")
            assert_equal(
                await ConsoleRetentionRowReaderData.chunk_ids(db_factory),
                [row_id],
                "live session row kept",
            )


class TestRetentionLoopStart:
    """The first retention sweep runs at startup."""

    @autotest.num("3577")
    @autotest.external_id("2eb61a9c-ee2f-4ab8-84b0-24b781f38ed2")
    @autotest.name("run_console_retention: the first sweep runs before the first interval")
    async def test_2eb61a9c_first_sweep_runs_before_the_first_interval(self, monkeypatch):
        with autotest.step("Arrange: an old and a fresh row, and a day-long interval"):
            (
                db_factory,
                fresh_chunk_id,
                _,
            ) = await ConsoleRetentionScenarioData.with_old_and_fresh_rows()
            watch = ConsoleRetentionSweepWatchData(monkeypatch)

        with autotest.step("Act: run the loop, then stop it well inside its interval"):
            task = asyncio.create_task(
                run_console_retention(db_factory, timedelta(days=1), interval_sec=3600)
            )
            await asyncio.wait_for(watch.done.wait(), 5.0)
            task.cancel()
            await task

        with autotest.step("Assert: one sweep ran and the aged row is already gone"):
            assert_equal(watch.sweeps, 1, "sweeps before the first interval")
            survivors = await ConsoleRetentionRowReaderData.chunk_ids(db_factory)
            assert_equal(survivors, [fresh_chunk_id], "surviving chunk rows")
            await ConsoleRetentionDbData.dispose(db_factory)
