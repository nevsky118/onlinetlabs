"""Tests for new FeatureExtractor features: distinct_failing_actuals, cycles_failing_unchanged."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from mcp_sdk.testing import autotest

from learning_analytics.features import FeatureExtractor

pytestmark = [pytest.mark.unit]


def _e(action, cid, actual, t):
    """Helper event factory."""
    return SimpleNamespace(
        timestamp=t,
        event_type=("action" if action == "check_passed" else "error"),
        action=action,
        component_id=cid,
        message=cid,
        success=(action == "check_passed"),
        extra_data={"actual": actual},
    )


@autotest.num("3227")
@autotest.external_id("2e397602-fa23-444a-aaf3-45394fca19f4")
@autotest.name("FeatureExtractor.compute: counts distinct failing actuals and the unchanged tail")
def test_2e397602_distinct_actuals_and_unchanged_run():
    with autotest.step("Arrange: two retries with different actuals, then two unchanged failures"):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        evs = [
            _e("check_retry", "PC1", {"ip": "a"}, base),
            _e("check_retry", "PC1", {"ip": "b"}, base + timedelta(seconds=25)),
            _e("check_failing", "PC1", {"ip": "b"}, base + timedelta(seconds=50)),
            _e("check_failing", "PC1", {"ip": "b"}, base + timedelta(seconds=75)),
        ]

    with autotest.step("Act: compute"):
        f = FeatureExtractor().compute("s1", evs)

    with autotest.step("Assert: distinct actuals counted, unchanged tail counted"):
        assert f.distinct_failing_actuals >= 2  # a,b
        assert f.cycles_failing_unchanged == 2  # tail of check_failing


@autotest.num("3228")
@autotest.external_id("7ae0b190-1a99-4005-baa6-cd33eaee61e8")
@autotest.name("FeatureExtractor.compute: empty events yield zero for both counters")
def test_7ae0b190_empty_events_returns_zero():
    with autotest.step("Act: compute over an empty event list"):
        f = FeatureExtractor().compute("s1", [])

    with autotest.step("Assert: both counters are zero"):
        assert f.distinct_failing_actuals == 0
        assert f.cycles_failing_unchanged == 0


@autotest.num("3229")
@autotest.external_id("c6e216e7-0f1f-4c5d-8c2f-d555df202055")
@autotest.name("FeatureExtractor.compute: non-check events yield zero for both counters")
def test_c6e216e7_no_check_actions_returns_zero():
    with autotest.step("Arrange: events with no check_* action"):
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

    with autotest.step("Act: compute"):
        f = FeatureExtractor().compute("s1", evs)

    with autotest.step("Assert: both counters are zero"):
        assert f.distinct_failing_actuals == 0
        assert f.cycles_failing_unchanged == 0


@autotest.num("3230")
@autotest.external_id("c586543a-495f-4d86-bda1-c6d3648266e2")
@autotest.name("FeatureExtractor.compute: cycles_failing_unchanged tail breaks on component change")
def test_c586543a_cycles_broken_by_different_component():
    """Tail breaks on component_id change."""
    with autotest.step("Arrange: a failing R1 event followed by two failing PC1 events"):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        evs = [
            _e("check_failing", "R1", {"ip": "x"}, base),
            _e("check_failing", "PC1", {"ip": "y"}, base + timedelta(seconds=25)),
            _e("check_failing", "PC1", {"ip": "y"}, base + timedelta(seconds=50)),
        ]

    with autotest.step("Act: compute"):
        f = FeatureExtractor().compute("s1", evs)

    with autotest.step("Assert: tail is only PC1 (2 events); R1 breaks the counter"):
        # tail is only PC1 (2 events); R1 breaks the counter
        assert f.cycles_failing_unchanged == 2


@autotest.num("3231")
@autotest.external_id("b17f600a-e156-4034-b99e-273caea55017")
@autotest.name("FeatureExtractor.compute: cycles_failing_unchanged tail breaks on check_passed")
def test_b17f600a_cycles_broken_by_check_passed():
    """check_passed breaks the tail."""
    with autotest.step("Arrange: two failing events followed by a check_passed"):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        evs = [
            _e("check_failing", "PC1", {"ip": "y"}, base),
            _e("check_failing", "PC1", {"ip": "y"}, base + timedelta(seconds=25)),
            _e("check_passed", "PC1", {"ip": "x"}, base + timedelta(seconds=50)),
        ]

    with autotest.step("Act: compute"):
        f = FeatureExtractor().compute("s1", evs)

    with autotest.step("Assert: cycles_failing_unchanged resets to 0"):
        assert f.cycles_failing_unchanged == 0


# Regression tests FIX 1: _current_error_run resets on check_passed


@autotest.num("3232")
@autotest.external_id("4858c12b-825a-43b3-b6c3-c035bbed70ea")
@autotest.name("FeatureExtractor.compute: error_repeat_count resets to 0 on check_passed")
def test_4858c12b_error_run_reset_by_check_passed():
    """check_passed breaks the run → error_repeat_count == 0."""
    with autotest.step("Arrange: two failing events followed by a check_passed"):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        evs = [
            _e("check_failing", "PC1", {"ip": "x"}, base),
            _e("check_failing", "PC1", {"ip": "x"}, base + timedelta(seconds=25)),
            _e("check_passed", "PC1", {"ip": "x"}, base + timedelta(seconds=50)),
        ]

    with autotest.step("Act: compute"):
        f = FeatureExtractor().compute("s1", evs)

    with autotest.step("Assert: error_repeat_count resets to 0"):
        assert f.error_repeat_count == 0


@autotest.num("3233")
@autotest.external_id("3cc0cc83-73cf-4496-8714-b7550975276c")
@autotest.name("FeatureExtractor.compute: error_repeat_count accumulates without check_passed")
def test_3cc0cc83_error_run_accumulates_without_check_passed():
    """Without check_passed the run doesn't break → error_repeat_count >= 2."""
    with autotest.step("Arrange: two failing events with no check_passed between them"):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        evs = [
            _e("check_failing", "PC1", {"ip": "x"}, base),
            _e("check_failing", "PC1", {"ip": "x"}, base + timedelta(seconds=25)),
        ]

    with autotest.step("Act: compute"):
        f = FeatureExtractor().compute("s1", evs)

    with autotest.step("Assert: error_repeat_count accumulates"):
        assert f.error_repeat_count >= 2
