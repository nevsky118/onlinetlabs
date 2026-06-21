import pytest
from experiment.control_arm import ControlArm, assign_arm

pytestmark = [pytest.mark.unit]


def test_arm_values():
    assert {a.value for a in ControlArm} == {"open", "closed"}


def test_assign_arm_valid(monkeypatch):
    import experiment.control_arm as m
    monkeypatch.setattr(m.random, "choice", lambda seq: seq[0])
    assert assign_arm() == ControlArm.OPEN
