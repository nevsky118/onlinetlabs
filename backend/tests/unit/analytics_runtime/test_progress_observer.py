"""Tests for derive_current_step."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none

from analytics.runtime.progress_observer import (
    derive_current_step,
)

pytestmark = [pytest.mark.unit]


class TestProgressObserver:
    @autotest.num("1700")
    @autotest.external_id("b94ed73e-a79f-421b-84c7-c854fca6b17b")
    @autotest.name("derive_current_step: first failing step becomes current")
    def test_b94ed73e_derive_current_step_first_failing(self):
        with autotest.step("Arrange: a passed step followed by a failing step"):
            snap = [
                {"id": "s1", "title": "A", "ok": True, "checks": []},
                {
                    "id": "s2",
                    "title": "B",
                    "ok": False,
                    "checks": [
                        {
                            "kind": "vpcs.show_ip",
                            "params": {"node": "PC1"},
                            "ok": False,
                            "expected": {"ip": "x"},
                            "actual": {"ip": "y"},
                        }
                    ],
                },
            ]

        with autotest.step("Act: derive_current_step"):
            st = derive_current_step(snap)

        with autotest.step("Assert: current step is the first failing one, with its failing check"):
            assert_equal(st.current_step_id, "s2", "current step id")
            assert_equal(st.current_step_title, "B", "current step title")
            assert_equal(len(st.failing_checks), 1, "failing checks count")
            assert_equal(st.failing_checks[0]["actual"], {"ip": "y"}, "actual")

    @autotest.num("1701")
    @autotest.external_id("910e6277-e671-4e8a-b0b8-617eb8b25448")
    @autotest.name("derive_current_step: all steps passed, current_step_id None")
    def test_910e6277_derive_current_step_all_passed(self):
        with autotest.step("Arrange: a snapshot where every step passed"):
            snap = [{"id": "s1", "title": "A", "ok": True, "checks": []}]

        with autotest.step("Act: derive_current_step"):
            st = derive_current_step(snap)

        with autotest.step("Assert: no current step, no failing checks"):
            assert_is_none(st.current_step_id, "current step id")
            assert_equal(st.current_step_title, "", "current step title")
            assert_equal(st.failing_checks, [], "failing checks")

    @autotest.num("1702")
    @autotest.external_id("02a052a4-742e-4db2-9d76-98dd6d41510b")
    @autotest.name("derive_current_step: empty snapshot -> None")
    def test_02a052a4_derive_current_step_empty(self):
        with autotest.step("Act+Assert: derive_current_step([]) has no current step"):
            assert_is_none(derive_current_step([]).current_step_id, "current step id")

    @autotest.num("1703")
    @autotest.external_id("046c5254-78b7-4258-851a-bdcef918a896")
    @autotest.name("derive_current_step: failing_checks filters to failed checks only")
    def test_046c5254_derive_current_step_filters_failing_checks(self):
        with autotest.step("Arrange: a failing step with one passed and one failed check"):
            snap = [
                {
                    "id": "s1",
                    "title": "Step1",
                    "ok": False,
                    "checks": [
                        {"kind": "ping", "params": {}, "ok": True, "expected": {}, "actual": {}},
                        {
                            "kind": "ip",
                            "params": {},
                            "ok": False,
                            "expected": {"ip": "1"},
                            "actual": {"ip": "2"},
                        },
                    ],
                }
            ]

        with autotest.step("Act: derive_current_step"):
            st = derive_current_step(snap)

        with autotest.step("Assert: failing_checks contains only the failed check"):
            assert_equal(st.current_step_id, "s1", "current step id")
            assert_equal(len(st.failing_checks), 1, "failing checks count")
            assert_equal(st.failing_checks[0]["kind"], "ip", "kind")
