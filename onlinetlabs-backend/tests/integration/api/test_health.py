import pytest

from tests.report import autotests

pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.smoke]


class TestHealth:
    @autotests.num("1")
    @autotests.external_id("70047968-d71b-4f47-9339-185e4fe9088d")
    @autotests.name("Health: GET /health возвращает ok")
    async def test_returns_ok(self, client):
        """Проверяет что health endpoint возвращает status ok."""

        # Act
        with autotests.step("Вызываем GET /health"):
            resp = await client.get("/health")

        # Assert
        with autotests.step("Проверяем статус 200 и status=ok"):
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"

    @autotests.num("2")
    @autotests.external_id("c5be7094-ba4d-43f1-ad61-19eee5ea28f1")
    @autotests.name("Health: GET / возвращает Hello World")
    async def test_root_returns_hello(self, client):
        """Проверяет что корневой endpoint возвращает Hello World."""

        # Act
        with autotests.step("Вызываем GET /"):
            resp = await client.get("/")

        # Assert
        with autotests.step("Проверяем статус 200 и message"):
            assert resp.status_code == 200
            assert resp.json()["message"] == "Hello World"
