import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestMRTConfig:
    @autotest.num("1967")
    @autotest.external_id("b606e531-a480-4559-b1de-c61394223f51")
    @autotest.name("MRT config: mrt_enabled defaults to False (safe off)")
    def test_b606e531_mrt_disabled_by_default(self):
        with autotest.step("Act: default config"):
            cfg = LearningAnalyticsConfig()

        with autotest.step("Assert: mrt_enabled == False"):
            assert_equal(cfg.mrt_enabled, False, "mrt_enabled defaults to False")

    @autotest.num("1968")
    @autotest.external_id("b8045bf7-3c93-4e79-bf91-e9697c604377")
    @autotest.name("MRT config: hold_probability in [0,1], jitter_frac >= 0")
    def test_b8045bf7_mrt_params_sane(self):
        with autotest.step("Act: default config"):
            cfg = LearningAnalyticsConfig()

        with autotest.step("Assert: MRT parameter bounds"):
            assert_true(
                0.0 <= cfg.mrt_hold_probability <= 1.0,
                f"hold_probability in [0,1], got {cfg.mrt_hold_probability}",
            )
            assert_true(
                cfg.mrt_t_k_jitter_frac >= 0.0,
                f"jitter_frac >= 0, got {cfg.mrt_t_k_jitter_frac}",
            )
