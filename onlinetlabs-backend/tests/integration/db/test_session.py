import pytest

from tests.report import autotests

pytestmark = [pytest.mark.integration, pytest.mark.api]


class TestGetDb:
    @autotests.num("67")
    @autotests.external_id("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
    @autotests.name("get_db: yields AsyncSession")
    async def test_get_db_yields_session(self):
        from app.db.session import get_db

        # Act
        with autotests.step("Call get_db generator"):
            gen = get_db()
            session = await gen.__anext__()

        # Assert
        with autotests.step("Verify session is not None"):
            assert session is not None

        with autotests.step("Cleanup"):
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass
