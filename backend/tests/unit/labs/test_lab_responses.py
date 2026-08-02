"""Characterization of GET /labs, GET /labs/{slug} and POST /labs: exact response JSON."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from auth.dependencies import get_current_user
from db.session import get_db
from i18n import LocalizedError, localized_error_handler
from labs.router import router as labs_router
from models.lab import Lab, LabStep

pytestmark = [pytest.mark.unit]


class TestLabResponses:
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LabStep.__table__.create)

        async with self.session_factory() as db:
            db.add(
                Lab(
                    slug="ospf-lab",
                    title_i18n={"en": "OSPF Lab"},
                    description_i18n={"en": "Настройка OSPF"},
                    difficulty="intermediate",
                    course_slug="networking-101",
                    environment_type="gns3",
                    order_in_course=1,
                    meta={"vendor": "cisco"},
                )
            )
            db.add(
                LabStep(
                    lab_slug="ospf-lab",
                    step_order=1,
                    slug="step-1",
                    title="Настроить интерфейсы",
                    validation_type="ping",
                )
            )
            await db.commit()

        self.app = FastAPI()
        self.app.include_router(labs_router, prefix="/labs")

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        self.app.dependency_overrides[get_db] = _override_db
        self.app.dependency_overrides[get_current_user] = lambda: {"id": "u1", "role": "admin"}
        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    @autotest.num("2502")
    @autotest.external_id("63376ebc-c27c-4ec3-8e85-432a02ff7ab8")
    @autotest.name("GET /labs: full lab list JSON matches pixel-for-pixel")
    async def test_63376ebc_list_labs_exact_json(self):
        with autotest.step("Act: GET /labs"):
            async with self._client() as client:
                resp = await client.get("/labs")

        with autotest.step("Assert: 200 and the full JSON matches the expected value"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(
                resp.json(),
                [
                    {
                        "slug": "ospf-lab",
                        "title": "OSPF Lab",
                        "description": "Настройка OSPF",
                        "difficulty": "intermediate",
                        "course_slug": "networking-101",
                        "environment_type": "gns3",
                        "order_in_course": 1,
                        "meta": {"vendor": "cisco"},
                    }
                ],
                "full lab list JSON",
            )

    @autotest.num("2503")
    @autotest.external_id("0e3e8332-e4f7-45d6-85f9-a81ec9ca3adc")
    @autotest.name("GET /labs/{slug}: full lab-with-steps JSON matches pixel-for-pixel")
    async def test_0e3e8332_get_lab_detail_exact_json(self):
        with autotest.step("Act: GET /labs/ospf-lab"):
            async with self._client() as client:
                resp = await client.get("/labs/ospf-lab")

        with autotest.step("Assert: 200 and the full JSON matches the expected value"):
            assert_equal(resp.status_code, 200, "status 200")
            assert_equal(
                resp.json(),
                {
                    "slug": "ospf-lab",
                    "title": "OSPF Lab",
                    "description": "Настройка OSPF",
                    "difficulty": "intermediate",
                    "course_slug": "networking-101",
                    "environment_type": "gns3",
                    "order_in_course": 1,
                    "meta": {"vendor": "cisco"},
                    "steps": [
                        {
                            "slug": "step-1",
                            "title": "Настроить интерфейсы",
                            "step_order": 1,
                            "validation_type": "ping",
                        }
                    ],
                },
                "full lab-with-steps JSON",
            )

    @autotest.num("2504")
    @autotest.external_id("69e350fc-43a1-47f1-951d-c2dfceb3a6fd")
    @autotest.name("POST /labs: full created-lab JSON matches pixel-for-pixel")
    async def test_69e350fc_create_lab_exact_json(self):
        with autotest.step("Act: POST /labs with a new lab"):
            async with self._client() as client:
                resp = await client.post(
                    "/labs",
                    json={
                        "slug": "bgp-lab",
                        "title": "BGP Lab",
                        "description": "Настройка BGP",
                        "difficulty": "advanced",
                        "environment_type": "gns3",
                    },
                )

        with autotest.step("Assert: 201 and the full JSON matches the expected value"):
            assert_equal(resp.status_code, 201, "status 201")
            assert_equal(
                resp.json(),
                {
                    "slug": "bgp-lab",
                    "title": "BGP Lab",
                    "description": "Настройка BGP",
                    "difficulty": "advanced",
                    "course_slug": None,
                    "environment_type": "gns3",
                    "order_in_course": 0,
                    "meta": None,
                },
                "full created-lab JSON",
            )


class TestLabsLocaleHeaderEndToEnd:
    """X-Locale end to end: GET /labs renders the requested locale, falls back to English without it."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Lab.__table__.create)
            await conn.run_sync(LabStep.__table__.create)

        async with self.session_factory() as db:
            db.add(
                Lab(
                    slug="ospf-lab-i18n",
                    title_i18n={"en": "OSPF Lab", "ru": "Лаба OSPF"},
                    difficulty="intermediate",
                    environment_type="gns3",
                )
            )
            await db.commit()

        self.app = FastAPI()
        self.app.include_router(labs_router, prefix="/labs")
        self.app.add_exception_handler(LocalizedError, localized_error_handler)

        async def _override_db():
            async with self.session_factory() as db:
                yield db

        self.app.dependency_overrides[get_db] = _override_db
        self.app.dependency_overrides[get_current_user] = lambda: {"id": "u1", "role": "admin"}
        yield
        await self.engine.dispose()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://testserver")

    @autotest.num("3138")
    @autotest.external_id("198f985d-4b8d-48ec-944a-b4b9cc303df4")
    @autotest.name(
        "GET /labs: X-Locale: ru returns Russian content, no header falls back to English"
    )
    async def test_198f985d_x_locale_header_selects_response_language(self):
        with autotest.step("Act: GET /labs with X-Locale: ru"):
            async with self._client() as client:
                ru_resp = await client.get("/labs", headers={"X-Locale": "ru"})

        with autotest.step("Assert: 200 and title rendered in Russian"):
            assert_equal(ru_resp.status_code, 200, "status 200")
            assert_equal(ru_resp.json()[0]["title"], "Лаба OSPF", "title in Russian")

        with autotest.step("Act: GET /labs with no X-Locale header"):
            async with self._client() as client:
                en_resp = await client.get("/labs")

        with autotest.step("Assert: 200 and title falls back to English"):
            assert_equal(en_resp.status_code, 200, "status 200")
            assert_equal(en_resp.json()[0]["title"], "OSPF Lab", "title in English")

    @autotest.num("3143")
    @autotest.external_id("e5a1bf36-b3c6-45b1-bf9e-59c92c0b6fa7")
    @autotest.name(
        "GET /labs/{slug}: unknown slug renders the same code with locale-specific detail"
    )
    async def test_e5a1bf36_unknown_lab_localizes_detail(self):
        # Arrange
        with autotest.step("Request an unknown lab slug under X-Locale: ru and with no header"):
            async with self._client() as client:
                ru = await client.get("/labs/no-such-lab", headers={"X-Locale": "ru"})
                en = await client.get("/labs/no-such-lab")

        # Act
        with autotest.step("Parse both responses"):
            ru_body = ru.json()
            en_body = en.json()

        # Assert
        with autotest.step("Both are 404 with the same code, but a different translated detail"):
            assert_equal(ru.status_code, 404, "ru status 404")
            assert_equal(en.status_code, 404, "en status 404")
            assert_equal(ru_body["code"], "error.lab.not_found", "ru code")
            assert_equal(en_body["code"], "error.lab.not_found", "en code")
            assert_equal(en_body["detail"], "Lab not found", "en detail")
            assert_equal(ru_body["detail"], "Лаборатория не найдена", "ru detail")
