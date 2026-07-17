"""Characterization of GET /labs, GET /labs/{slug} and POST /labs: exact response JSON."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from auth.dependencies import get_current_user
from db.session import get_db
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
                    title="OSPF Lab",
                    description="Настройка OSPF",
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
    @autotest.name("GET /labs: полный JSON списка лаб пиксель-в-пиксель")
    async def test_63376ebc_list_labs_exact_json(self):
        with autotest.step("Act: GET /labs"):
            async with self._client() as client:
                resp = await client.get("/labs")

        with autotest.step("Assert: 200 и полный JSON равен ожидаемому"):
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
                "полный JSON списка лаб",
            )

    @autotest.num("2503")
    @autotest.external_id("0e3e8332-e4f7-45d6-85f9-a81ec9ca3adc")
    @autotest.name("GET /labs/{slug}: полный JSON лабы со степами пиксель-в-пиксель")
    async def test_0e3e8332_get_lab_detail_exact_json(self):
        with autotest.step("Act: GET /labs/ospf-lab"):
            async with self._client() as client:
                resp = await client.get("/labs/ospf-lab")

        with autotest.step("Assert: 200 и полный JSON равен ожидаемому"):
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
                "полный JSON лабы со степами",
            )

    @autotest.num("2504")
    @autotest.external_id("69e350fc-43a1-47f1-951d-c2dfceb3a6fd")
    @autotest.name("POST /labs: полный JSON созданной лабы пиксель-в-пиксель")
    async def test_69e350fc_create_lab_exact_json(self):
        with autotest.step("Act: POST /labs с новой лабой"):
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

        with autotest.step("Assert: 201 и полный JSON равен ожидаемому"):
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
                "полный JSON созданной лабы",
            )
