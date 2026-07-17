"""Тесты diff_snapshots."""

import pytest

from learning_analytics.progress_observer import diff_snapshots

pytestmark = [pytest.mark.unit]


def _snap(ok, actual):
    return [
        {
            "id": "s1",
            "title": "A",
            "ok": ok,
            "checks": [
                {
                    "kind": "vpcs.show_ip",
                    "params": {"node": "PC1"},
                    "ok": ok,
                    "expected": {"ip": "x"},
                    "actual": actual,
                }
            ],
        }
    ]


def test_first_cycle_none_returns_empty():
    assert diff_snapshots(None, _snap(False, {"ip": "y"})) == []


def test_failing_unchanged_emits_check_failing():
    evs = diff_snapshots(_snap(False, {"ip": "y"}), _snap(False, {"ip": "y"}))
    assert len(evs) == 1
    assert evs[0]["action"] == "check_failing"
    assert evs[0]["event_type"] == "error"
    assert evs[0]["success"] is False


def test_failing_changed_emits_check_retry():
    evs = diff_snapshots(_snap(False, {"ip": "y"}), _snap(False, {"ip": "z"}))
    assert len(evs) == 1
    assert evs[0]["action"] == "check_retry"
    assert evs[0]["extra_data"]["actual"] == {"ip": "z"}
    assert evs[0]["extra_data"]["prev_actual"] == {"ip": "y"}


def test_fail_to_ok_emits_check_passed():
    evs = diff_snapshots(_snap(False, {"ip": "y"}), _snap(True, {"ip": "x"}))
    assert len(evs) == 1
    assert evs[0]["action"] == "check_passed"
    assert evs[0]["success"] is True
    assert evs[0]["event_type"] == "action"


def test_ok_to_ok_no_event():
    evs = diff_snapshots(_snap(True, {"ip": "x"}), _snap(True, {"ip": "x"}))
    assert evs == []


def test_ok_to_fail_emits_check_regressed():
    evs = diff_snapshots(_snap(True, {"ip": "x"}), _snap(False, {"ip": "y"}))
    assert len(evs) == 1
    assert evs[0]["action"] == "check_regressed"
    assert evs[0]["event_type"] == "error"
    assert evs[0]["success"] is False
    assert evs[0]["extra_data"]["actual"] == {"ip": "y"}
