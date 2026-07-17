import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class TestUserIsSimulated:
    @autotest.num("2011")
    @autotest.external_id("db42e7b5-af31-4c6b-ba7d-2559bf151902")
    @autotest.name("User: колонка is_simulated есть, дефолт False")
    def test_db42e7b5_user_has_is_simulated(self):
        with autotest.step("Act+Assert: колонка присутствует, дефолт False"):
            from models.user import User
            col = User.__table__.columns.get("is_simulated")
            assert_true(col is not None, "колонка is_simulated присутствует")
            assert_equal(col.default.arg, False, "дефолт False")
