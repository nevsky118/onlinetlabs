import pytest
from types import SimpleNamespace
from agents.analytics.models import StruggleType
from learning_analytics.process_state import ProcessRegime, analysis_to_regime, is_bad
pytestmark = [pytest.mark.unit]

def test_productive_when_no_struggle():
    a = SimpleNamespace(struggle_detected=False, struggle_type=None)
    assert analysis_to_regime(a) == ProcessRegime.PRODUCTIVE
    assert is_bad(ProcessRegime.PRODUCTIVE) is False

def test_regime_mirrors_struggle_type():
    a = SimpleNamespace(struggle_detected=True, struggle_type=StruggleType.STUCK_ON_STEP)
    r = analysis_to_regime(a)
    assert r == ProcessRegime.STUCK_ON_STEP and r.value == "stuck_on_step"
    assert is_bad(r) is True
