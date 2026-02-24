import pytest

from tests.helpers.factories import build_session_context
from tests.helpers.fakes import FakeAllProtocols, FakeStateProvider

from onlinetlabs_mcp_sdk.testing.conformance import ConformanceTestSuite


pytestmark = [pytest.mark.integration, pytest.mark.conformance]


class TestFakeConformance(ConformanceTestSuite):
    """Full protocol conformance — all tests pass, no skips."""

    @pytest.fixture
    def server_impl(self):
        return FakeAllProtocols()

    @pytest.fixture
    def mock_session_ctx(self):
        return build_session_context()


class _EmptyStateProvider:
    """StateProvider that returns empty collections — triggers 'no data' skips."""

    async def list_components(self, ctx):
        return []

    async def get_component(self, ctx, component_id):
        from onlinetlabs_mcp_sdk.errors import ComponentNotFoundError

        raise ComponentNotFoundError(component_id=component_id)

    async def get_system_overview(self, ctx):
        from onlinetlabs_mcp_sdk.models import SystemOverview

        return SystemOverview(
            system_name="empty",
            component_count=0,
            components_by_type={},
            components_by_status={},
            summary="empty",
        )


class _EmptyActionProvider(_EmptyStateProvider):
    """StateProvider + ActionProvider with empty actions list."""

    async def list_available_actions(self, ctx, component_id=None):
        return []

    async def execute_action(self, ctx, action_name, params):
        from onlinetlabs_mcp_sdk.models import ActionResult

        return ActionResult(success=True, message="ok")


class TestMinimalConformance(ConformanceTestSuite):
    """StateProvider-only — triggers skip for log/history/action tests."""

    @pytest.fixture
    def server_impl(self):
        return FakeStateProvider()

    @pytest.fixture
    def mock_session_ctx(self):
        return build_session_context()


class TestEmptyStateConformance(ConformanceTestSuite):
    """Empty StateProvider — triggers 'no components' skip in get_component."""

    @pytest.fixture
    def server_impl(self):
        return _EmptyStateProvider()

    @pytest.fixture
    def mock_session_ctx(self):
        return build_session_context()


class TestEmptyActionConformance(ConformanceTestSuite):
    """ActionProvider with empty list — triggers 'no actions' skip in execute_action."""

    @pytest.fixture
    def server_impl(self):
        return _EmptyActionProvider()

    @pytest.fixture
    def mock_session_ctx(self):
        return build_session_context()


class _NonStateImpl:
    """Does not implement StateProvider — triggers StateProvider skips."""

    pass


class TestNonStateConformance(ConformanceTestSuite):
    """Non-StateProvider — triggers all StateProvider skip branches."""

    @pytest.fixture
    def server_impl(self):
        return _NonStateImpl()

    @pytest.fixture
    def mock_session_ctx(self):
        return build_session_context()
