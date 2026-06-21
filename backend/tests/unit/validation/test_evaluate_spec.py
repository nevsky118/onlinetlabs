"""Unit-тесты для evaluate_spec."""

import pytest

from validation.checks import registry
from validation.checks.registry import CheckResult
from validation.runner import evaluate_spec

pytestmark = [pytest.mark.unit]


async def test_evaluate_spec_orders_steps_and_collects(monkeypatch):
    async def ok_handler(ctx, params, expect):
        return CheckResult(ok=True, expected=expect, actual={"v": 1})

    monkeypatch.setattr(registry, "get_handler", lambda kind: ok_handler)
    spec = {"steps": [
        {"id": "s1", "title": "A", "checks": [{"kind": "x", "node": "PC1", "expect": {"v": 1}}]},
    ]}
    steps = await evaluate_spec(ctx=object(), spec=spec)
    assert steps == [{"id": "s1", "title": "A", "ok": True,
                      "checks": [{"kind": "x", "params": {"node": "PC1"}, "ok": True,
                                  "expected": {"v": 1}, "actual": {"v": 1}}]}]


async def test_evaluate_spec_unknown_kind_returns_error(monkeypatch):
    monkeypatch.setattr(registry, "get_handler", lambda kind: None)
    spec = {"steps": [
        {"id": "s1", "title": "A", "checks": [{"kind": "bad.kind", "expect": {}}]},
    ]}
    steps = await evaluate_spec(ctx=object(), spec=spec)
    assert steps[0]["ok"] is False
    assert "unknown check kind" in steps[0]["checks"][0]["actual"]["error"]


async def test_evaluate_spec_handler_exception_returns_error(monkeypatch):
    async def failing_handler(ctx, params, expect):
        raise RuntimeError("boom")

    monkeypatch.setattr(registry, "get_handler", lambda kind: failing_handler)
    spec = {"steps": [
        {"id": "s1", "title": "A", "checks": [{"kind": "x", "expect": {}}]},
    ]}
    steps = await evaluate_spec(ctx=object(), spec=spec)
    assert steps[0]["ok"] is False
    assert steps[0]["checks"][0]["actual"] == {"error": "boom"}


async def test_evaluate_spec_empty_spec():
    steps = await evaluate_spec(ctx=object(), spec={})
    assert steps == []


async def test_evaluate_spec_step_ok_all_checks_pass(monkeypatch):
    async def ok_handler(ctx, params, expect):
        return CheckResult(ok=True, expected=expect, actual={})

    monkeypatch.setattr(registry, "get_handler", lambda kind: ok_handler)
    spec = {"steps": [
        {"id": "s1", "title": "Step1", "checks": [
            {"kind": "x", "expect": {"a": 1}},
            {"kind": "y", "expect": {"b": 2}},
        ]},
    ]}
    steps = await evaluate_spec(ctx=object(), spec=spec)
    assert steps[0]["ok"] is True


async def test_evaluate_spec_step_fails_if_any_check_fails(monkeypatch):
    call_count = 0

    async def mixed_handler(ctx, params, expect):
        nonlocal call_count
        call_count += 1
        return CheckResult(ok=(call_count % 2 == 1), expected=expect, actual={})

    monkeypatch.setattr(registry, "get_handler", lambda kind: mixed_handler)
    spec = {"steps": [
        {"id": "s1", "title": "Step1", "checks": [
            {"kind": "x", "expect": {}},
            {"kind": "y", "expect": {}},
        ]},
    ]}
    steps = await evaluate_spec(ctx=object(), spec=spec)
    # первая проверка ok=True, вторая ok=False → шаг fail
    assert steps[0]["ok"] is False
