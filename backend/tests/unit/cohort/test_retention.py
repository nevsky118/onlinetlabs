import pytest
from cohort.metrics import retention_metric, RETENTION_NOTE
pytestmark = [pytest.mark.unit]

def test_retention_rate_and_flag():
    r = retention_metric([True, True, False])
    assert r.retest_count == 3
    assert r.retest_pass_rate == pytest.approx(2 / 3)
    assert "предварит" in r.note.lower() or "смещ" in r.note.lower()
    assert r.note == RETENTION_NOTE

def test_retention_empty():
    r = retention_metric([])
    assert r.retest_count == 0
    assert r.retest_pass_rate is None
