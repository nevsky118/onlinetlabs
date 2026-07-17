"""Тесты derive_current_step."""

import pytest
from mcp_sdk.testing import autotest

from learning_analytics.progress_observer import (
    derive_current_step,
)

pytestmark = [pytest.mark.unit]


@autotest.num("1700")
@autotest.external_id("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
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
@autotest.external_id("b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")
@autotest.name("derive_current_step: все шаги пройдены — current_step_id None")
def test_derive_current_step_all_passed():
    snap = [{"id": "s1", "title": "A", "ok": True, "checks": []}]
    st = derive_current_step(snap)
    assert st.current_step_id is None  # завершено
    assert st.current_step_title == ""
    assert st.failing_checks == []


@autotest.num("1702")
@autotest.external_id("c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f")
@autotest.name("derive_current_step: пустой снапшот → None")
def test_derive_current_step_empty():
    assert derive_current_step([]).current_step_id is None


@autotest.num("1703")
@autotest.external_id("d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a")
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
