import pytest

pytestmark = [pytest.mark.unit]


class _Cap:
    def __init__(self): self.added = []
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def add(self, o): self.added.append(o)
    async def commit(self): pass


async def test_record_escalation_writes_event():
    from escalation.service import record_escalation
    cap = _Cap()
    await record_escalation(cap, "s1", "u1", "lab-1", source="manual")
    e = cap.added[0]
    assert e.event_type == "escalation" and e.action == "manual"


async def test_record_escalation_objective_source():
    from escalation.service import record_escalation
    cap = _Cap()
    await record_escalation(cap, "s2", "u2", "lab-2", source="objective")
    e = cap.added[0]
    assert e.action == "objective" and e.success is False and e.severity == "warn"
