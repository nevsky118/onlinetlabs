"""Unit tests for the console index migration's concurrent-build guards."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from tests.settings.data.console_data import ConsoleIndexMigrationData, MigrationOpRecorderData

pytestmark = [pytest.mark.unit]


class TestConsoleIndexMigration:
    """A failed concurrent build leaves an INVALID index."""

    @autotest.num("3578")
    @autotest.external_id("159ef438-1c74-4b41-a715-8037b56061f3")
    @autotest.name("console index migration: every index is built concurrently and guarded")
    def test_159ef438_upgrade_guards_every_concurrent_index(self):
        with autotest.step("Arrange: the migration wired to a recording op"):
            recorder = MigrationOpRecorderData()
            migration = ConsoleIndexMigrationData.load(recorder)

        with autotest.step("Act"):
            migration.upgrade()

        with autotest.step("Assert: three indexes, each concurrent and retry-safe"):
            assert_equal(len(recorder.created), 3, "indexes created")
            for index in recorder.created:
                assert_true(index.get("if_not_exists") is True, f"{index['name']} guarded")
                assert_true(
                    index.get("postgresql_concurrently") is True, f"{index['name']} concurrent"
                )

    @autotest.num("3585")
    @autotest.external_id("784742d6-a9dd-4b36-bc0a-209f39535e2c")
    @autotest.name("console index migration: each index is dropped before it is rebuilt")
    def test_784742d6_upgrade_drops_an_invalid_leftover_first(self):
        with autotest.step("Arrange: the migration wired to a recording op"):
            recorder = MigrationOpRecorderData()
            migration = ConsoleIndexMigrationData.load(recorder)

        with autotest.step("Act"):
            migration.upgrade()

        with autotest.step("Assert: a concurrent guarded drop precedes every create"):
            assert_equal([kind for kind, _ in recorder.calls], ["drop", "create"] * 3, "call order")
            for dropped, created in zip(recorder.dropped, recorder.created, strict=True):
                assert_equal(dropped["name"], created["name"], "drop pairs with its create")
                assert_true(dropped.get("if_exists") is True, f"{dropped['name']} guarded")
                assert_true(
                    dropped.get("postgresql_concurrently") is True, f"{dropped['name']} concurrent"
                )

    @autotest.num("3579")
    @autotest.external_id("8fedc20c-5b2e-4793-a796-1e659e273ef1")
    @autotest.name("console index migration: the downgrade tolerates a missing index")
    def test_8fedc20c_downgrade_tolerates_a_missing_index(self):
        with autotest.step("Arrange: the migration wired to a recording op"):
            recorder = MigrationOpRecorderData()
            migration = ConsoleIndexMigrationData.load(recorder)

        with autotest.step("Act"):
            migration.downgrade()

        with autotest.step("Assert: three drops, each guarded"):
            assert_equal(len(recorder.dropped), 3, "indexes dropped")
            for index in recorder.dropped:
                assert_true(index.get("if_exists") is True, f"{index['name']} guarded")
