import asyncio

import pytest
from mcp_sdk.testing import autotest

from observability.activity import AgentActivityLog
from observability.models import event_struggle_detected

pytestmark = [pytest.mark.unit]


class _FailDB:
    def __call__(self):
        raise RuntimeError("db down")


@pytest.mark.asyncio
@autotest.num("3243")
@autotest.external_id("6619e3db-4a62-43b4-a160-8f2101fab764")
@autotest.name("AgentActivityLog.emit: publishes to subscribers and isolates a persist failure")
async def test_6619e3db_emit_publishes_and_isolates_persist_failure():
    log = AgentActivityLog(db_factory=_FailDB(), retention_per_session=100)
    q = log.subscribe("s1")
    log.emit(event_struggle_detected("s1", "u1", struggle_type="idle", confidence=0.7, crossed=[]))
    evt = await asyncio.wait_for(q.get(), timeout=1.0)
    assert evt.session_id == "s1" and evt.kind.value == "struggle_detected"
    # persist failed internally, but emit did not propagate the exception (test reached here)
    await asyncio.sleep(0)  # let the persist task run and swallow the error


@pytest.mark.asyncio
@autotest.num("3244")
@autotest.external_id("7ccfea1d-a14e-418f-8b88-a5345e9c4152")
@autotest.name("AgentActivityLog.stop: drains all queued events before returning")
async def test_7ccfea1d_writer_drains_queued_events_on_stop():
    # Regression: emit used a bare create_task whose reference was dropped, so the
    # write could be garbage collected before it ran.
    persisted: list = []

    log = AgentActivityLog(db_factory=_FailDB(), retention_per_session=100)

    async def _record(event):
        persisted.append(event)

    log._persist = _record
    await log.start()
    for _ in range(5):
        log.emit(
            event_struggle_detected("s1", "u1", struggle_type="idle", confidence=0.7, crossed=[])
        )
    await log.stop()

    assert len(persisted) == 5


@pytest.mark.asyncio
@autotest.num("3245")
@autotest.external_id("719f9871-a2b4-46e7-a75b-2e5013b6fa3f")
@autotest.name("AgentActivityLog.emit: does not raise when the writer has not been started")
async def test_719f9871_emit_without_writer_does_not_raise():
    # emit is called from request paths that must never fail on telemetry.
    log = AgentActivityLog(db_factory=_FailDB(), retention_per_session=100)
    log.emit(event_struggle_detected("s1", "u1", struggle_type="idle", confidence=0.7, crossed=[]))
    assert log._writes.qsize() == 1
