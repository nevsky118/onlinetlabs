import pytest
from datetime import datetime, timedelta, timezone
from learning_analytics.process_state import ProcessRegime, DwellTracker
pytestmark = [pytest.mark.unit]

def test_dwell_accumulates_then_resets():
    t = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
    dt = DwellTracker()
    assert dt.observe(ProcessRegime.STUCK_ON_STEP, t) == 0.0
    assert dt.observe(ProcessRegime.STUCK_ON_STEP, t + timedelta(seconds=15)) == 15.0
    assert dt.observe(ProcessRegime.STUCK_ON_STEP, t + timedelta(seconds=30)) == 30.0
    assert dt.observe(ProcessRegime.PRODUCTIVE, t + timedelta(seconds=45)) == 0.0
    assert dt.current_regime == ProcessRegime.PRODUCTIVE
