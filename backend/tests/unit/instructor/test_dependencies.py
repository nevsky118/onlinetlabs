import pytest
from fastapi import HTTPException
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from auth.dependencies import require_instructor

pytestmark = [pytest.mark.unit, pytest.mark.auth]


class TestRequireInstructor:
    @autotest.num("1850")
    @autotest.external_id("c1a2b3d4-e5f6-4708-8901-aabbccdd0001")
    @autotest.name("require_instructor: instructor проходит")
    def test_c1a2b3d4_instructor_passes(self):
        with autotest.step("Arrange: dict с role=instructor"):
            user = {"id": "user-740", "role": "instructor"}

        with autotest.step("Act: вызываем зависимость напрямую"):
            result = require_instructor(current_user=user)

        with autotest.step("Assert: возвращает тот же объект"):
            assert_equal(result, user, "returns the same user dict")

    @autotest.num("1851")
    @autotest.external_id("c1a2b3d4-e5f6-4708-8901-aabbccdd0002")
    @autotest.name("require_instructor: admin проходит")
    def test_c1a2b3d4_admin_passes(self):
        with autotest.step("Arrange: dict с role=admin"):
            user = {"id": "user-741", "role": "admin"}

        with autotest.step("Act: вызываем зависимость напрямую"):
            result = require_instructor(current_user=user)

        with autotest.step("Assert: возвращает тот же объект"):
            assert_equal(result, user, "returns the same user dict")

    @autotest.num("1852")
    @autotest.external_id("c1a2b3d4-e5f6-4708-8901-aabbccdd0003")
    @autotest.name("require_instructor: student → HTTPException 403")
    def test_c1a2b3d4_student_raises_403(self):
        with autotest.step("Arrange: dict с role=student"):
            user = {"id": "user-742", "role": "student"}

        with autotest.step("Act + Assert: ожидаем 403"):
            with pytest.raises(HTTPException) as exc_info:
                require_instructor(current_user=user)
            assert_equal(exc_info.value.status_code, 403, "status_code = 403")
