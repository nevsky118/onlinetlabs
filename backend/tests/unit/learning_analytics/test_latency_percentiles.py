"""Latency: перцентили p50/p95/p99 (Hyndman-Fan Type 7, numpy/R default) — не среднее."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

pytestmark = [pytest.mark.unit]


class TestLatencyPercentiles:
    @autotest.num("1988")
    @autotest.external_id("a42fd0a1-66ac-47d1-9040-895d390317e3")
    @autotest.name("percentiles: Type 7 линейная интерполяция p50/p95/p99 на 10..100")
    def test_a42fd0a1_type7_interpolation(self):
        with autotest.step("Act: перцентили по 10 значениям 10..100"):
            from learning_analytics.latency import percentiles
            vals = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            out = percentiles(vals, [50, 95, 99])

        with autotest.step("Assert: p50=55.0, p95=95.5, p99=99.1 (Type 7)"):
            assert_equal(out[50], 55.0, "p50 == 55.0")
            assert_equal(out[95], 95.5, "p95 == 95.5")
            assert_equal(out[99], 99.1, "p99 == 99.1")

    @autotest.num("1989")
    @autotest.external_id("a5fa3234-7851-4752-82ce-f0db942f5430")
    @autotest.name("percentiles: пустой вход → нули")
    def test_a5fa3234_empty(self):
        with autotest.step("Act+Assert: пустой список → все перцентили 0.0"):
            from learning_analytics.latency import percentiles
            out = percentiles([], [50, 95, 99])
            assert_equal(out, {50: 0.0, 95: 0.0, 99: 0.0}, "пусто → нули")
