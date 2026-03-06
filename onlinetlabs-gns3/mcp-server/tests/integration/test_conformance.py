import pytest

from tests.helpers.factories import build_session_context
from tests.helpers.fakes import FakeGNS3ApiClient
from tests.report import autotests

from onlinetlabs_mcp_sdk.testing.conformance import ConformanceTestSuite

from src.server import GNS3Server

pytestmark = [pytest.mark.integration, pytest.mark.conformance]


class TestGNS3Conformance(ConformanceTestSuite):
    """SDK conformance: GNS3Server проходит все StateProvider тесты."""

    @pytest.fixture
    def server_impl(self):
        from src.log_buffer import LogBuffer
        from onlinetlabs_mcp_sdk.models import LogLevel
        buf = LogBuffer()
        buf._add_entry(LogLevel.ERROR, "test error")
        buf._add_entry(LogLevel.INFO, "test info")
        return GNS3Server(api_client=FakeGNS3ApiClient(), log_buffer=buf)

    @pytest.fixture
    def mock_session_ctx(self):
        return build_session_context()
