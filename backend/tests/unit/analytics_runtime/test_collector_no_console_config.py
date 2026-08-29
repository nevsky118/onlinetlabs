import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_false

from analytics.runtime.collector import BehavioralCollector

pytestmark = [pytest.mark.unit]


class TestCollectorNoConsoleConfig:
    @autotest.num("3226")
    @autotest.external_id("23671a72-5d5f-46ec-9cdf-ba00bdb06307")
    @autotest.name("BehavioralCollector: has no _check_console_config method")
    def test_23671a72_collector_has_no_console_config(self):
        with autotest.step("Act+Assert: BehavioralCollector has no _check_console_config method"):
            assert_false(
                hasattr(BehavioralCollector, "_check_console_config"),
                "no console config probe",
            )
