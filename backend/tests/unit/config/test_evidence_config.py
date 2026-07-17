import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from config.config_model import LearningAnalyticsConfig

pytestmark = [pytest.mark.unit]


class TestEvidenceConfig:
    @autotest.num("1976")
    @autotest.external_id("19f3fd71-bfc5-4c78-9354-35b6958f5cfd")
    @autotest.name("Evidence config: evidence_capture_enabled по умолчанию False")
    def test_19f3fd71_evidence_disabled_by_default(self):
        with autotest.step("Act: конфиг по умолчанию"):
            cfg = LearningAnalyticsConfig()

        with autotest.step("Assert: evidence_capture_enabled == False"):
            assert_equal(cfg.evidence_capture_enabled, False, "по умолчанию выключено")
