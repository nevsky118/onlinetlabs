import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.course import Course
from models.lab import Lab, LabStep
from tests.report import autotests

pytestmark = pytest.mark.labs


class TestListLabs:
    @autotests.num("114")
    @autotests.external_id("labs-router-list-empty")
    @autotests.name("GET /labs: пустой список")
    async def test_empty(self, client: AsyncClient):
        with autotests.step("Запрашиваем GET /labs"):
            resp = await client.get("/labs")

        with autotests.step("Проверяем пустой массив"):
            assert resp.status_code == 200
            assert resp.json() == []

    @autotests.num("115")
    @autotests.external_id("labs-router-list-filter")
    @autotests.name("GET /labs?course_slug=: фильтрация")
    async def test_filter(self, client: AsyncClient, db_session: AsyncSession):
        with autotests.step("Создаём курс и лабы"):
            course = Course(
                slug="r-net-301", title="Net 301", difficulty="intermediate", order=3
            )
            db_session.add(course)
            await db_session.commit()
            lab1 = Lab(
                slug="r-lab-a",
                title="Lab A",
                difficulty="beginner",
                course_slug="r-net-301",
                environment_type="gns3",
                order_in_course=1,
            )
            lab2 = Lab(
                slug="r-lab-b",
                title="Lab B",
                difficulty="beginner",
                environment_type="docker",
                order_in_course=0,
            )
            db_session.add_all([lab1, lab2])
            await db_session.commit()

        with autotests.step("Фильтруем по курсу"):
            resp = await client.get("/labs", params={"course_slug": "r-net-301"})

        with autotests.step("Проверяем одну лабу"):
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["slug"] == "r-lab-a"


class TestGetLab:
    @autotests.num("116")
    @autotests.external_id("labs-router-get-found")
    @autotests.name("GET /labs/{slug}: найдена")
    async def test_found(self, client: AsyncClient, db_session: AsyncSession):
        with autotests.step("Создаём лабу со степами"):
            lab = Lab(
                slug="r-lab-x",
                title="Lab X",
                difficulty="beginner",
                environment_type="docker",
                order_in_course=0,
            )
            db_session.add(lab)
            await db_session.commit()
            step = LabStep(
                lab_slug="r-lab-x",
                slug="r-s1",
                title="Step 1",
                step_order=1,
                validation_type="command",
            )
            db_session.add(step)
            await db_session.commit()

        with autotests.step("Запрашиваем GET /labs/r-lab-x"):
            resp = await client.get("/labs/r-lab-x")

        with autotests.step("Проверяем лабу и степы"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["slug"] == "r-lab-x"
            assert len(data["steps"]) == 1

    @autotests.num("117")
    @autotests.external_id("labs-router-get-not-found")
    @autotests.name("GET /labs/{slug}: не найдена")
    async def test_not_found(self, client: AsyncClient):
        with autotests.step("Запрашиваем несуществующую лабу"):
            resp = await client.get("/labs/nonexistent")

        with autotests.step("Проверяем HTTP 404"):
            assert resp.status_code == 404
