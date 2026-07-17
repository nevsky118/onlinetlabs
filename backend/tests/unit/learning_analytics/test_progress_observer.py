"""Тесты derive_current_step."""

import pytest
from mcp_sdk.testing import autotest

from learning_analytics.progress_observer import (
    derive_current_step,
)

pytestmark = [pytest.mark.unit]


@autotest.num("1700")
@autotest.external_id("b94ed73e-a79f-421b-84c7-c854fca6b17b")
@autotest.name("derive_current_step: первый провальный шаг — текущий")
def test_derive_current_step_first_failing():
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
    st = derive_current_step(snap)
    assert st.current_step_id == "s2"
    assert st.current_step_title == "B"
    assert len(st.failing_checks) == 1
    assert st.failing_checks[0]["actual"] == {"ip": "y"}


@autotest.num("1701")
@autotest.external_id("910e6277-e671-4e8a-b0b8-617eb8b25448")
@autotest.name("derive_current_step: все шаги пройдены — current_step_id None")
def test_derive_current_step_all_passed():
    snap = [{"id": "s1", "title": "A", "ok": True, "checks": []}]
    st = derive_current_step(snap)
    assert st.current_step_id is None  # завершено
    assert st.current_step_title == ""
    assert st.failing_checks == []


@autotest.num("1702")
@autotest.external_id("02a052a4-742e-4db2-9d76-98dd6d41510b")
@autotest.name("derive_current_step: пустой снапшот → None")
def test_derive_current_step_empty():
    assert derive_current_step([]).current_step_id is None


@autotest.num("1703")
@autotest.external_id("046c5254-78b7-4258-851a-bdcef918a896")
@autotest.name("derive_current_step: failing_checks фильтрует только упавшие проверки")
def test_derive_current_step_filters_failing_checks():
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
    st = derive_current_step(snap)
    assert st.current_step_id == "s1"
    assert len(st.failing_checks) == 1
    assert st.failing_checks[0]["kind"] == "ip"
