import asyncio

import pytest

from observability.activity import AgentActivityLog
from observability.models import event_struggle_detected

pytestmark = [pytest.mark.unit]


class _FailDB:
    def __call__(self):
        raise RuntimeError("db down")


@pytest.mark.asyncio
async def test_emit_publishes_and_isolates_persist_failure():
    log = AgentActivityLog(db_factory=_FailDB(), retention_per_session=100)
    q = log.subscribe("s1")
    log.emit(event_struggle_detected("s1", "u1", struggle_type="idle", confidence=0.7, crossed=[]))
    evt = await asyncio.wait_for(q.get(), timeout=1.0)
    assert evt.session_id == "s1" and evt.kind.value == "struggle_detected"
    # persist failed internally — but emit did not propagate the exception (test reached here)
    await asyncio.sleep(0)  # let the persist task run and swallow the error
