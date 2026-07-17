import pytest

from learning_analytics.collector import BehavioralCollector

pytestmark = [pytest.mark.unit]


def test_collector_has_no_console_config():
    assert not hasattr(BehavioralCollector, "_check_console_config")
