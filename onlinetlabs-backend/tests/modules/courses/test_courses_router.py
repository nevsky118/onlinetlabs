import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.course import Course
from models.lab import Lab
from tests.report import autotests

pytestmark = pytest.mark.courses


class TestListCourses:
    @autotests.num("104")
    @autotests.external_id("courses-router-list-empty")
    @autotests.name("GET /courses: пустой список")
    async def test_empty(self, client: AsyncClient):
        with autotests.step("Запрашиваем GET /courses"):
            resp = await client.get("/courses")

        with autotests.step("Проверяем пустой массив"):
            assert resp.status_code == 200
            assert resp.json() == []

    @autotests.num("105")
    @autotests.external_id("courses-router-list-with-data")
    @autotests.name("GET /courses: с данными")
    async def test_with_data(self, client: AsyncClient, db_session: AsyncSession):
        with autotests.step("Создаём курс в БД"):
            course = Course(
                slug="r-net-101", title="Networking 101", difficulty="beginner", order=1
            )
            db_session.add(course)
            await db_session.commit()

        with autotests.step("Запрашиваем GET /courses"):
            resp = await client.get("/courses")

        with autotests.step("Проверяем курс в ответе"):
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 1
            slugs = [d["slug"] for d in data]
            assert "r-net-101" in slugs


class TestGetCourse:
    @autotests.num("106")
    @autotests.external_id("courses-router-get-found")
    @autotests.name("GET /courses/{slug}: найден")
    async def test_found(self, client: AsyncClient, db_session: AsyncSession):
        with autotests.step("Создаём курс и лабу"):
            course = Course(
                slug="r-net-102", title="Networking 102", difficulty="beginner", order=1
            )
            db_session.add(course)
            await db_session.commit()
            lab = Lab(
                slug="r-lab-ping",
                title="Ping Lab",
                difficulty="beginner",
                course_slug="r-net-102",
                environment_type="gns3",
                order_in_course=1,
            )
            db_session.add(lab)
            await db_session.commit()

        with autotests.step("Запрашиваем GET /courses/r-net-102"):
            resp = await client.get("/courses/r-net-102")

        with autotests.step("Проверяем курс и лабы в ответе"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["slug"] == "r-net-102"
            assert len(data["labs"]) == 1
            assert data["labs"][0]["slug"] == "r-lab-ping"

    @autotests.num("107")
    @autotests.external_id("courses-router-get-not-found")
    @autotests.name("GET /courses/{slug}: не найден")
    async def test_not_found(self, client: AsyncClient):
        with autotests.step("Запрашиваем несуществующий курс"):
            resp = await client.get("/courses/nonexistent")

        with autotests.step("Проверяем HTTP 404"):
            assert resp.status_code == 404
