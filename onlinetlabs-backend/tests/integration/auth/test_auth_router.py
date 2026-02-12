import pytest

from app.auth.exceptions import AccountMismatchError
from tests.report import autotests

pytestmark = [pytest.mark.integration, pytest.mark.auth]


class TestRegisterEndpoint:
    @autotests.num("50")
    @autotests.external_id("815f96b9-4c9f-4f24-bf2f-cb623a3ddc35")
    @autotests.name("Auth Router: POST /auth/register (успех)")
    async def test_success(self, client):
        """Проверяет успешную регистрацию нового пользователя."""

        # Arrange
        payload = {
            "email": "new@example.com",
            "password": "securepass123",
            "name": "New User",
        }

        # Act
        with autotests.step("Вызываем POST /auth/register"):
            resp = await client.post("/auth/register", json=payload)

        # Assert
        with autotests.step("Проверяем статус 201 и данные пользователя"):
            assert resp.status_code == 201
            data = resp.json()
            assert data["email"] == "new@example.com"
            assert data["role"] == "student"
            assert "id" in data

    @autotests.num("51")
    @autotests.external_id("084f245a-a519-4344-b9cf-3bad0b58dde5")
    @autotests.name("Auth Router: POST /auth/register (дубликат email)")
    async def test_duplicate_email(self, client):
        """Проверяет что повторная регистрация с тем же email возвращает 409."""

        # Arrange
        payload = {"email": "dup@example.com", "password": "securepass123"}

        with autotests.step("Регистрируем первого пользователя"):
            await client.post("/auth/register", json=payload)

        # Act
        with autotests.step("Повторная регистрация с тем же email"):
            resp = await client.post("/auth/register", json=payload)

        # Assert
        with autotests.step("Проверяем HTTP 409"):
            assert resp.status_code == 409


class TestLoginEndpoint:
    @autotests.num("52")
    @autotests.external_id("c626b77c-24cf-4bd4-adb5-a367f40e3fb0")
    @autotests.name("Auth Router: POST /auth/login (успех)")
    async def test_success(self, client):
        """Проверяет успешный логин после регистрации."""

        # Arrange
        with autotests.step("Регистрируем пользователя"):
            await client.post(
                "/auth/register",
                json={"email": "login@example.com", "password": "securepass123"},
            )

        # Act
        with autotests.step("Вызываем POST /auth/login"):
            resp = await client.post(
                "/auth/login",
                json={"email": "login@example.com", "password": "securepass123"},
            )

        # Assert
        with autotests.step("Проверяем статус 200 и email"):
            assert resp.status_code == 200
            assert resp.json()["email"] == "login@example.com"

    @autotests.num("59")
    @autotests.external_id("3a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5e")
    @autotests.name("Auth Router: POST /auth/login (GitHub-пользователь без пароля)")
    async def test_github_user_no_password(self, client):
        """Проверяет что GitHub-пользователь без пароля не может войти через login."""

        # Arrange
        with autotests.step("Создаём GitHub-пользователя (без пароля)"):
            await client.post(
                "/auth/github-callback",
                json={
                    "email": "gh-nopwd@example.com",
                    "name": "GH NoPwd",
                    "provider_account_id": "99999",
                },
            )

        # Act
        with autotests.step("Пытаемся войти через login"):
            resp = await client.post(
                "/auth/login",
                json={"email": "gh-nopwd@example.com", "password": "anypass"},
            )

        # Assert
        with autotests.step("Проверяем HTTP 401"):
            assert resp.status_code == 401

    @autotests.num("53")
    @autotests.external_id("2bf5e94f-e672-4b5c-95f8-189952e77ea6")
    @autotests.name("Auth Router: POST /auth/login (неверный пароль)")
    async def test_wrong_password(self, client):
        """Проверяет что неверный пароль возвращает 401."""

        # Arrange
        with autotests.step("Регистрируем пользователя"):
            await client.post(
                "/auth/register",
                json={"email": "wrong@example.com", "password": "securepass123"},
            )

        # Act
        with autotests.step("Логин с неверным паролем"):
            resp = await client.post(
                "/auth/login",
                json={"email": "wrong@example.com", "password": "badpassword"},
            )

        # Assert
        with autotests.step("Проверяем HTTP 401"):
            assert resp.status_code == 401


class TestExchangeEndpoint:
    @autotests.num("55")
    @autotests.external_id("258311ea-8a8c-49c9-9350-a21fb4103394")
    @autotests.name("Auth Router: POST /auth/exchange (успех)")
    async def test_exchange_success(self, client):
        """Проверяет успешный обмен session data на backend JWT."""

        # Arrange
        with autotests.step("Регистрируем пользователя"):
            reg = await client.post(
                "/auth/register",
                json={"email": "exch@example.com", "password": "securepass123"},
            )
            user_id = reg.json()["id"]

        # Act
        with autotests.step("Вызываем POST /auth/exchange"):
            resp = await client.post(
                "/auth/exchange",
                json={"user_id": user_id, "email": "exch@example.com"},
            )

        # Assert
        with autotests.step("Проверяем статус 200 и access_token"):
            assert resp.status_code == 200
            assert "access_token" in resp.json()

    @autotests.num("56")
    @autotests.external_id("fcb582fb-1be0-484f-b15d-972e98cabac3")
    @autotests.name("Auth Router: POST /auth/exchange (пользователь не найден)")
    async def test_exchange_user_not_found(self, client):
        """Проверяет что несуществующий пользователь возвращает 401."""

        # Act
        with autotests.step("Вызываем POST /auth/exchange с несуществующим пользователем"):
            resp = await client.post(
                "/auth/exchange",
                json={"user_id": "nonexistent-id", "email": "nobody@example.com"},
            )

        # Assert
        with autotests.step("Проверяем HTTP 401"):
            assert resp.status_code == 401

    @autotests.num("57")
    @autotests.external_id("42f0582d-a21d-4cc1-93ee-f8dabd3590fb")
    @autotests.name("Auth Router: POST /auth/exchange (несовпадение user_id)")
    async def test_exchange_user_id_mismatch(self, client):
        """Проверяет что неверный user_id возвращает 401."""

        # Arrange
        with autotests.step("Регистрируем пользователя"):
            await client.post(
                "/auth/register",
                json={"email": "mismatch@example.com", "password": "securepass123"},
            )

        # Act
        with autotests.step("Вызываем POST /auth/exchange с неверным user_id"):
            resp = await client.post(
                "/auth/exchange",
                json={"user_id": "wrong-id", "email": "mismatch@example.com"},
            )

        # Assert
        with autotests.step("Проверяем HTTP 401"):
            assert resp.status_code == 401


class TestGithubCallback:
    @autotests.num("54")
    @autotests.external_id("b9ff2073-0515-4fb3-a93b-b74bcbcb7147")
    @autotests.name("Auth Router: POST /auth/github-callback (создание пользователя)")
    async def test_creates_user(self, client):
        """Проверяет что GitHub callback создаёт пользователя."""

        # Arrange
        payload = {
            "email": "gh@example.com",
            "name": "GitHub User",
            "image": "https://avatar.url",
            "provider_account_id": "12345",
        }

        # Act
        with autotests.step("Вызываем POST /auth/github-callback"):
            resp = await client.post("/auth/github-callback", json=payload)

        # Assert
        with autotests.step("Проверяем статус 200 и email"):
            assert resp.status_code == 200
            assert resp.json()["email"] == "gh@example.com"

    @autotests.num("58")
    @autotests.external_id("d28301f7-0d30-4945-ad86-1cbde8855bfb")
    @autotests.name("Auth Router: POST /auth/github-callback (несовпадение аккаунтов)")
    async def test_account_mismatch(self, client):
        """Проверяет что несовпадение provider_account_id вызывает AccountMismatchError."""

        # Arrange
        with autotests.step("Создаём пользователя через github-callback"):
            await client.post(
                "/auth/github-callback",
                json={
                    "email": "mismatch-gh@example.com",
                    "name": "GH User",
                    "provider_account_id": "111",
                },
            )

        # Act & Assert
        with autotests.step("Повторный callback с другим provider_account_id"):
            with pytest.raises(AccountMismatchError):
                await client.post(
                    "/auth/github-callback",
                    json={
                        "email": "mismatch-gh@example.com",
                        "name": "GH User",
                        "provider_account_id": "222",
                    },
                )
