"""Тесты новых признаков FeatureExtractor: distinct_failing_actuals, cycles_failing_unchanged."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from learning_analytics.features import FeatureExtractor

pytestmark = [pytest.mark.unit]


def _e(action, cid, actual, t):
    """Вспомогательная фабрика события."""
    return SimpleNamespace(
        timestamp=t,
        event_type=("action" if action == "check_passed" else "error"),
        action=action,
        component_id=cid,
        message=cid,
        success=(action == "check_passed"),
        extra_data={"actual": actual},
    )


def test_distinct_actuals_and_unchanged_run():
    base = datetime(2026, 1, 1, tzinfo=UTC)
    evs = [
        _e("check_retry", "PC1", {"ip": "a"}, base),
        _e("check_retry", "PC1", {"ip": "b"}, base + timedelta(seconds=25)),
        _e("check_failing", "PC1", {"ip": "b"}, base + timedelta(seconds=50)),
        _e("check_failing", "PC1", {"ip": "b"}, base + timedelta(seconds=75)),
    ]
    f = FeatureExtractor().compute("s1", evs)
    assert f.distinct_failing_actuals >= 2  # a,b
    assert f.cycles_failing_unchanged == 2  # хвост check_failing


def test_empty_events_returns_zero():
    f = FeatureExtractor().compute("s1", [])
    assert f.distinct_failing_actuals == 0
    assert f.cycles_failing_unchanged == 0


def test_no_check_actions_returns_zero():
    base = datetime(2026, 1, 1, tzinfo=UTC)
    evs = [
        SimpleNamespace(
            timestamp=base + timedelta(seconds=i * 10),
            event_type="action",
            action="start_node",
            component_id="R1",
            message="ok",
            success=True,
            extra_data=None,
        )
        for i in range(3)
    ]
    f = FeatureExtractor().compute("s1", evs)
    assert f.distinct_failing_actuals == 0
    assert f.cycles_failing_unchanged == 0


def test_cycles_broken_by_different_component():
    """Хвост обрывается при смене component_id."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    evs = [
        _e("check_failing", "R1", {"ip": "x"}, base),
        _e("check_failing", "PC1", {"ip": "y"}, base + timedelta(seconds=25)),
        _e("check_failing", "PC1", {"ip": "y"}, base + timedelta(seconds=50)),
    ]
    f = FeatureExtractor().compute("s1", evs)
    # хвост — только PC1 (2 события); R1 обрывает счётчик
    assert f.cycles_failing_unchanged == 2


def test_cycles_broken_by_check_passed():
    """check_passed прерывает хвост."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    evs = [
        _e("check_failing", "PC1", {"ip": "y"}, base),
        _e("check_failing", "PC1", {"ip": "y"}, base + timedelta(seconds=25)),
        _e("check_passed", "PC1", {"ip": "x"}, base + timedelta(seconds=50)),
    ]
    f = FeatureExtractor().compute("s1", evs)
    assert f.cycles_failing_unchanged == 0


# Регрессионные тесты FIX 1: _current_error_run сбрасывается по check_passed


def test_error_run_reset_by_check_passed():
    """check_passed обрывает серию → error_repeat_count == 0."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    evs = [
        _e("check_failing", "PC1", {"ip": "x"}, base),
        _e("check_failing", "PC1", {"ip": "x"}, base + timedelta(seconds=25)),
        _e("check_passed", "PC1", {"ip": "x"}, base + timedelta(seconds=50)),
    ]
    f = FeatureExtractor().compute("s1", evs)
    assert f.error_repeat_count == 0


def test_error_run_accumulates_without_check_passed():
    """Без check_passed серия не обрывается → error_repeat_count >= 2."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    evs = [
        _e("check_failing", "PC1", {"ip": "x"}, base),
        _e("check_failing", "PC1", {"ip": "x"}, base + timedelta(seconds=25)),
    ]
    f = FeatureExtractor().compute("s1", evs)
    assert f.error_repeat_count >= 2
