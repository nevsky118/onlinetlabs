"""Characterization: GET /courses and GET /courses/{slug}, exact JSON response."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from courses import router as courses_router
from i18n import LocalizedError, localized_error_handler
from kit.db import get_db
from models.catalog import Course, Lab

pytestmark = [pytest.mark.unit]


class TestCourseResponses:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Course.__table__.create)
            await conn.run_sync(Lab.__table__.create)

        async with self.session_factory() as db:
            db.add(
                Course(
                    slug="networking-101",
                    title_i18n={"en": "Networking 101"},
                    description_i18n={"en": "Основы сетей"},
                    difficulty="beginner",
                    order=1,
                    meta={"tags": ["networking"]},
                )
            )
            db.add(
                Lab(
                    slug="ospf-lab",
                    title_i18n={"en": "OSPF Lab"},
                    course_slug="networking-101",
                    difficulty="intermediate",
                    environment_type="gns3",
                    order_in_course=1,
                )
            )
            await db.commit()

        self.app = FastAPI()
        self.app.include_router(courses_router)
        self.app.add_exception_handler(LocalizedError, localized_error_handler)

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        self.app.dependency_overrides[get_db] = _override_db
        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    @autotest.num("2500")
    @autotest.external_id("f2764546-2a7d-4208-bd96-b419b92f570e")
    @autotest.name("GET /courses: full course list JSON, pixel-for-pixel")
    async def test_f2764546_list_courses_exact_json(self):
        with autotest.step("Act: GET /courses"):
            async with self._client() as client:
                resp = await client.get("/courses")

        with autotest.step("Assert: 200 and full JSON equals expected"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(
                resp.json(),
                [
                    {
                        "slug": "networking-101",
                        "title": "Networking 101",
                        "description": "Основы сетей",
                        "difficulty": "beginner",
                        "order": 1,
                        "meta": {"tags": ["networking"]},
                    }
                ],
                "full course list JSON",
            )

    @autotest.num("2501")
    @autotest.external_id("1c8ee1b5-fbe9-450d-bd83-147920f39336")
    @autotest.name("GET /courses/{slug}: full course-with-labs JSON, pixel-for-pixel")
    async def test_1c8ee1b5_get_course_detail_exact_json(self):
        with autotest.step("Act: GET /courses/networking-101"):
            async with self._client() as client:
                resp = await client.get("/courses/networking-101")

        with autotest.step("Assert: 200 and full JSON equals expected"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(
                resp.json(),
                {
                    "slug": "networking-101",
                    "title": "Networking 101",
                    "description": "Основы сетей",
                    "difficulty": "beginner",
                    "order": 1,
                    "meta": {"tags": ["networking"]},
                    "labs": [
                        {
                            "slug": "ospf-lab",
                            "title": "OSPF Lab",
                            "difficulty": "intermediate",
                            "environment_type": "gns3",
                            "order_in_course": 1,
                        }
                    ],
                },
                "full course-with-labs JSON",
            )

    @autotest.num("3142")
    @autotest.external_id("ff54bb18-742b-45c7-842e-adda3e2d4e9f")
    @autotest.name(
        "GET /courses/{slug}: unknown slug renders the same code with locale-specific detail"
    )
    async def test_ff54bb18_unknown_course_localizes_detail(self):
        # Arrange
        with autotest.step("Request an unknown course slug under X-Locale: ru and with no header"):
            async with self._client() as client:
                ru = await client.get("/courses/no-such-course", headers={"X-Locale": "ru"})
                en = await client.get("/courses/no-such-course")

        # Act
        with autotest.step("Parse both responses"):
            ru_body = ru.json()
            en_body = en.json()

        # Assert
        with autotest.step("Both are 404 with the same code, but a different translated detail"):
            assert_equal(ru.status_code, 404, "ru status 404")
            assert_equal(en.status_code, 404, "en status 404")
            assert_equal(ru_body["code"], "error.course.not_found", "ru code")
            assert_equal(en_body["code"], "error.course.not_found", "en code")
            assert_equal(en_body["detail"], "Course not found", "en detail")
            assert_equal(ru_body["detail"], "Курс не найден", "ru detail")
