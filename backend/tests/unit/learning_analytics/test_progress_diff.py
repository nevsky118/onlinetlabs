"""Tests for diff_snapshots."""

import pytest
from mcp_sdk.testing import autotest

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


@autotest.num("3234")
@autotest.external_id("a413482f-1f63-4724-9fda-64935f7911d7")
@autotest.name("diff_snapshots: previous=None returns no events")
def test_a413482f_first_cycle_none_returns_empty():
    assert diff_snapshots(None, _snap(False, {"ip": "y"})) == []


@autotest.num("3235")
@autotest.external_id("df3f13e2-bc4a-4ab2-9b14-dd11a844830b")
@autotest.name("diff_snapshots: failing check with the same actual emits check_failing")
def test_df3f13e2_failing_unchanged_emits_check_failing():
    evs = diff_snapshots(_snap(False, {"ip": "y"}), _snap(False, {"ip": "y"}))
    assert len(evs) == 1
    assert evs[0]["action"] == "check_failing"
    assert evs[0]["event_type"] == "error"
    assert evs[0]["success"] is False


@autotest.num("3236")
@autotest.external_id("cf2545a0-e6f3-4739-a87c-c77a94b7cd87")
@autotest.name("diff_snapshots: failing check with a changed actual emits check_retry")
def test_cf2545a0_failing_changed_emits_check_retry():
    evs = diff_snapshots(_snap(False, {"ip": "y"}), _snap(False, {"ip": "z"}))
    assert len(evs) == 1
    assert evs[0]["action"] == "check_retry"
    assert evs[0]["extra_data"]["actual"] == {"ip": "z"}
    assert evs[0]["extra_data"]["prev_actual"] == {"ip": "y"}


@autotest.num("3237")
@autotest.external_id("e323c3f5-5665-49ce-99d6-2fa2df1ca7a0")
@autotest.name("diff_snapshots: fail-to-ok transition emits check_passed")
def test_e323c3f5_fail_to_ok_emits_check_passed():
    evs = diff_snapshots(_snap(False, {"ip": "y"}), _snap(True, {"ip": "x"}))
    assert len(evs) == 1
    assert evs[0]["action"] == "check_passed"
    assert evs[0]["success"] is True
    assert evs[0]["event_type"] == "action"


@autotest.num("3238")
@autotest.external_id("88ae5d10-0736-4676-ad45-1cd95b2cfbff")
@autotest.name("diff_snapshots: ok-to-ok transition emits no event")
def test_88ae5d10_ok_to_ok_no_event():
    evs = diff_snapshots(_snap(True, {"ip": "x"}), _snap(True, {"ip": "x"}))
    assert evs == []


@autotest.num("3239")
@autotest.external_id("0cd66907-1155-4cce-a601-303ddc2d9af5")
@autotest.name("diff_snapshots: ok-to-fail transition emits check_regressed")
def test_0cd66907_ok_to_fail_emits_check_regressed():
    evs = diff_snapshots(_snap(True, {"ip": "x"}), _snap(False, {"ip": "y"}))
    assert len(evs) == 1
    assert evs[0]["action"] == "check_regressed"
    assert evs[0]["event_type"] == "error"
    assert evs[0]["success"] is False
    assert evs[0]["extra_data"]["actual"] == {"ip": "y"}
