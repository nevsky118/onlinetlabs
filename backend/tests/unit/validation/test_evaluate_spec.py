"""Unit tests for evaluate_spec."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_in

from validation.checks import registry
from validation.checks.registry import CheckResult
from validation.runner import evaluate_spec

pytestmark = [pytest.mark.unit]


class TestEvaluateSpec:
    @autotest.num("3258")
    @autotest.external_id("7a6f23aa-619d-4f51-af94-41ec03389ad7")
    @autotest.name("evaluate_spec: orders steps and collects check results")
    async def test_7a6f23aa_evaluate_spec_orders_steps_and_collects(self, monkeypatch):
        with autotest.step("Arrange: a one-step, one-check spec with a handler that always passes"):

            async def ok_handler(ctx, params, expect):
                return CheckResult(ok=True, expected=expect, actual={"v": 1})

            monkeypatch.setattr(registry, "get_handler", lambda kind: ok_handler)
            spec = {
                "steps": [
                    {
                        "id": "s1",
                        "title": "A",
                        "checks": [{"kind": "x", "node": "PC1", "expect": {"v": 1}}],
                    },
                ]
            }

        with autotest.step("Act: evaluate_spec"):
            steps = await evaluate_spec(ctx=object(), spec=spec)

        with autotest.step("Assert: the step and its check result match exactly"):
            assert_equal(
                steps,
                [
                    {
                        "id": "s1",
                        "title": "A",
                        "ok": True,
                        "checks": [
                            {
                                "kind": "x",
                                "params": {"node": "PC1"},
                                "ok": True,
                                "expected": {"v": 1},
                                "actual": {"v": 1},
                            }
                        ],
                    }
                ],
                "steps",
            )

    @autotest.num("3259")
    @autotest.external_id("a9ae5216-d958-4f18-a519-5aed00211b9c")
    @autotest.name("evaluate_spec: unknown check kind returns an error result")
    async def test_a9ae5216_evaluate_spec_unknown_kind_returns_error(self, monkeypatch):
        with autotest.step("Arrange: a spec whose check kind has no registered handler"):
            monkeypatch.setattr(registry, "get_handler", lambda kind: None)
            spec = {
                "steps": [
                    {"id": "s1", "title": "A", "checks": [{"kind": "bad.kind", "expect": {}}]},
                ]
            }

        with autotest.step("Act: evaluate_spec"):
            steps = await evaluate_spec(ctx=object(), spec=spec)

        with autotest.step("Assert: step fails with an 'unknown check kind' error"):
            assert_equal(steps[0]["ok"], False, "ok")
            assert_in(
                "unknown check kind",
                steps[0]["checks"][0]["actual"]["error"],
                "'unknown check kind'",
            )

    @autotest.num("3260")
    @autotest.external_id("10c5ff0d-cf9e-41c2-b807-c8e93bf01939")
    @autotest.name("evaluate_spec: handler exception is captured as an error result")
    async def test_10c5ff0d_evaluate_spec_handler_exception_returns_error(self, monkeypatch):
        with autotest.step("Arrange: a spec whose handler raises"):

            async def failing_handler(ctx, params, expect):
                raise RuntimeError("boom")

            monkeypatch.setattr(registry, "get_handler", lambda kind: failing_handler)
            spec = {
                "steps": [
                    {"id": "s1", "title": "A", "checks": [{"kind": "x", "expect": {}}]},
                ]
            }

        with autotest.step("Act: evaluate_spec"):
            steps = await evaluate_spec(ctx=object(), spec=spec)

        with autotest.step("Assert: exception is captured as the check's error result"):
            assert_equal(steps[0]["ok"], False, "ok")
            assert_equal(
                steps[0]["checks"][0]["actual"],
                {"error": "boom"},
                "actual",
            )

    @autotest.num("3261")
    @autotest.external_id("16d2f88d-3818-4c5e-8a44-06f60d653d61")
    @autotest.name("evaluate_spec: an empty spec returns no steps")
    async def test_16d2f88d_evaluate_spec_empty_spec(self):
        with autotest.step("Act: evaluate_spec on an empty spec"):
            steps = await evaluate_spec(ctx=object(), spec={})

        with autotest.step("Assert: no steps are returned"):
            assert_equal(steps, [], "steps")

    @autotest.num("3262")
    @autotest.external_id("814997ca-5110-4882-b7ac-78feeca6e867")
    @autotest.name("evaluate_spec: step is ok when all its checks pass")
    async def test_814997ca_evaluate_spec_step_ok_all_checks_pass(self, monkeypatch):
        with autotest.step("Arrange: a step with two checks, both handled by a passing handler"):

            async def ok_handler(ctx, params, expect):
                return CheckResult(ok=True, expected=expect, actual={})

            monkeypatch.setattr(registry, "get_handler", lambda kind: ok_handler)
            spec = {
                "steps": [
                    {
                        "id": "s1",
                        "title": "Step1",
                        "checks": [
                            {"kind": "x", "expect": {"a": 1}},
                            {"kind": "y", "expect": {"b": 2}},
                        ],
                    },
                ]
            }

        with autotest.step("Act: evaluate_spec"):
            steps = await evaluate_spec(ctx=object(), spec=spec)

        with autotest.step("Assert: step is ok"):
            assert_equal(steps[0]["ok"], True, "ok")

    @autotest.num("3263")
    @autotest.external_id("2c501c48-38e9-463c-b373-a0cbafbebc3b")
    @autotest.name("evaluate_spec: step fails if any of its checks fails")
    async def test_2c501c48_evaluate_spec_step_fails_if_any_check_fails(self, monkeypatch):
        with autotest.step("Arrange: a step with two checks, alternating pass/fail"):
            call_count = 0

            async def mixed_handler(ctx, params, expect):
                nonlocal call_count
                call_count += 1
                return CheckResult(ok=(call_count % 2 == 1), expected=expect, actual={})

            monkeypatch.setattr(registry, "get_handler", lambda kind: mixed_handler)
            spec = {
                "steps": [
                    {
                        "id": "s1",
                        "title": "Step1",
                        "checks": [
                            {"kind": "x", "expect": {}},
                            {"kind": "y", "expect": {}},
                        ],
                    },
                ]
            }

        with autotest.step("Act: evaluate_spec"):
            steps = await evaluate_spec(ctx=object(), spec=spec)

        with autotest.step("Assert: first check ok=True, second ok=False → step fails"):
            # first check ok=True, second ok=False → step fails
            assert_equal(steps[0]["ok"], False, "ok")
