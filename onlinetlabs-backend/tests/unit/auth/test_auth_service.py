import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import AccountMismatchError, UserAlreadyExistsError
from app.auth.service import (
    create_user,
    get_user_by_email,
    hash_password,
    hash_password_async,
    upsert_github_user,
    verify_password,
)
from app.models.user import UserRole
from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.auth]


class TestPasswordHashing:
    @autotests.num("30")
    @autotests.external_id("707a4e53-e7af-4361-bf9b-3ec2ce16fde1")
    @autotests.name("Password: хеширование и верификация")
    def test_hash_and_verify(self):
        """Проверяет что hash_password создаёт хеш, verify_password проверяет."""

        # Act
        with autotests.step("Хешируем пароль"):
            hashed = hash_password("mysecretpass")

        # Assert
        with autotests.step("Проверяем что хеш отличается от пароля"):
            assert hashed != "mysecretpass"

        with autotests.step("Проверяем верификацию корректного пароля"):
            assert verify_password("mysecretpass", hashed)

        with autotests.step("Проверяем отказ для неверного пароля"):
            assert not verify_password("wrongpass", hashed)

    @autotests.num("31")
    @autotests.external_id("e3d950dd-20fa-4af0-a53b-bef3d268ced9")
    @autotests.name("Password: verify с None хешем возвращает False")
    def test_verify_none_hash(self):
        """Проверяет что verify_password возвращает False для None хеша."""

        with autotests.step("Верифицируем пароль с None хешем"):
            assert not verify_password("anything", None)

    @autotests.num("32")
    @autotests.external_id("fd1a203c-9882-4d70-9717-afa605cbf945")
    @autotests.name("Password: асинхронное хеширование")
    async def test_hash_async(self):
        """Проверяет hash_password_async."""

        # Act
        with autotests.step("Асинхронно хешируем пароль"):
            hashed = await hash_password_async("asyncpass")

        # Assert
        with autotests.step("Проверяем хеш и верификацию"):
            assert hashed != "asyncpass"
            assert verify_password("asyncpass", hashed)


class TestCreateUser:
    @autotests.num("33")
    @autotests.external_id("c7ea36bb-839a-467c-b202-165078f3780f")
    @autotests.name("create_user: создание с ролью по умолчанию")
    async def test_create(self, db_session: AsyncSession):
        """Проверяет создание пользователя с ролью student по умолчанию."""

        # Act
        with autotests.step("Создаём пользователя"):
            user = await create_user(
                db=db_session,
                email="test@example.com",
                password_hash=hash_password("pass12345"),
                name="Test User",
            )

        # Assert
        with autotests.step("Проверяем email, role и password_hash"):
            assert user.email == "test@example.com"
            assert user.role == UserRole.STUDENT.value
            assert user.password_hash is not None

    @autotests.num("34")
    @autotests.external_id("26a86d1f-7467-43dc-83de-a9ca698f4b40")
    @autotests.name("create_user: создание с явной ролью")
    async def test_accepts_role_enum(self, db_session: AsyncSession):
        """Проверяет создание пользователя с ролью INSTRUCTOR."""

        # Act
        with autotests.step("Создаём пользователя с ролью INSTRUCTOR"):
            user = await create_user(
                db=db_session,
                email="instructor@example.com",
                password_hash=hash_password("pass12345"),
                name="Instructor",
                role=UserRole.INSTRUCTOR,
            )

        # Assert
        with autotests.step("Проверяем роль"):
            assert user.role == UserRole.INSTRUCTOR.value

    @autotests.num("35")
    @autotests.external_id("030b2140-bf1b-468d-b79b-f59c2cd2fdba")
    @autotests.name("create_user: дубликат email вызывает UserAlreadyExistsError")
    async def test_duplicate_email(self, db_session: AsyncSession):
        """Проверяет что повторный email вызывает UserAlreadyExistsError."""

        # Arrange
        with autotests.step("Создаём первого пользователя"):
            await create_user(
                db=db_session,
                email="dup@example.com",
                password_hash="hash",
                name="First",
            )

        # Act & Assert
        with autotests.step("Пытаемся создать второго с тем же email"):
            with pytest.raises(UserAlreadyExistsError):
                await create_user(
                    db=db_session,
                    email="dup@example.com",
                    password_hash="hash",
                    name="Second",
                )


class TestGetUserByEmail:
    @autotests.num("36")
    @autotests.external_id("415fbc9a-892a-433c-95fa-d301a58e9860")
    @autotests.name("get_user_by_email: поиск существующего и несуществующего")
    async def test_found(self, db_session: AsyncSession):
        """Проверяет поиск пользователя по email."""

        # Arrange
        with autotests.step("Создаём пользователя"):
            await create_user(
                db=db_session,
                email="find@example.com",
                password_hash="hash",
                name="Find Me",
            )

        # Act & Assert
        with autotests.step("Ищем существующего пользователя"):
            found = await get_user_by_email(db_session, "find@example.com")
            assert found is not None
            assert found.email == "find@example.com"

        with autotests.step("Ищем несуществующего пользователя"):
            not_found = await get_user_by_email(db_session, "nope@example.com")
            assert not_found is None


class TestUpsertGithubUser:
    @autotests.num("37")
    @autotests.external_id("6615038a-fd4b-4cc0-9d05-00d531931d98")
    @autotests.name("upsert_github_user: создание нового GitHub пользователя")
    async def test_new(self, db_session: AsyncSession):
        """Проверяет создание пользователя через GitHub OAuth."""

        # Act
        with autotests.step("Создаём GitHub пользователя"):
            user = await upsert_github_user(
                db=db_session,
                email="gh@example.com",
                name="GitHub User",
                image="https://avatar.url",
                provider_account_id="12345",
            )

        # Assert
        with autotests.step("Проверяем данные пользователя"):
            assert user.email == "gh@example.com"
            assert user.role == UserRole.STUDENT.value

        with autotests.step("Проверяем привязанный GitHub аккаунт"):
            assert len(user.accounts) == 1
            assert user.accounts[0].provider == "github"
            assert user.accounts[0].provider_account_id == "12345"

    @autotests.num("38")
    @autotests.external_id("2b4d881a-1e8f-459e-b1bc-1b665bdbbf58")
    @autotests.name("upsert_github_user: идемпотентность")
    async def test_idempotent(self, db_session: AsyncSession):
        """Проверяет что повторный upsert не дублирует аккаунт."""

        # Arrange
        with autotests.step("Первый upsert"):
            await upsert_github_user(
                db=db_session,
                email="idempotent@example.com",
                name="User",
                image=None,
                provider_account_id="99999",
            )

        # Act
        with autotests.step("Повторный upsert с обновлённым именем"):
            user = await upsert_github_user(
                db=db_session,
                email="idempotent@example.com",
                name="User Updated",
                image=None,
                provider_account_id="99999",
            )

        # Assert
        with autotests.step("Проверяем что аккаунт один и имя обновлено"):
            assert len(user.accounts) == 1
            assert user.name == "User Updated"

    @autotests.num("39")
    @autotests.external_id("41abef04-f832-4487-93c7-35852c4593e7")
    @autotests.name("upsert_github_user: привязка GitHub к существующему пользователю")
    async def test_links_existing(self, db_session: AsyncSession):
        """Проверяет привязку GitHub аккаунта к пользователю с тем же email."""

        # Arrange
        with autotests.step("Создаём пользователя через credentials"):
            existing = await create_user(
                db=db_session,
                email="shared@example.com",
                password_hash=hash_password("pass12345"),
                name="Existing User",
            )

        # Act
        with autotests.step("Upsert GitHub с тем же email"):
            linked = await upsert_github_user(
                db=db_session,
                email="shared@example.com",
                name="GitHub Name",
                image="https://avatar.url",
                provider_account_id="67890",
            )

        # Assert
        with autotests.step("Проверяем что это тот же пользователь с GitHub аккаунтом"):
            assert linked.id == existing.id
            assert len(linked.accounts) == 1
            assert linked.accounts[0].provider == "github"

    @autotests.num("40")
    @autotests.external_id("308c7db4-0702-4538-afa3-9049a558b75f")
    @autotests.name("upsert_github_user: несовпадение аккаунтов вызывает AccountMismatchError")
    async def test_account_mismatch(self, db_session: AsyncSession):
        """Проверяет что другой provider_account_id с тем же email вызывает ошибку."""

        # Arrange
        with autotests.step("Создаём GitHub пользователя"):
            await upsert_github_user(
                db=db_session,
                email="mismatch@example.com",
                name="User A",
                image=None,
                provider_account_id="11111",
            )

        # Act & Assert
        with autotests.step("Upsert с другим provider_account_id"):
            with pytest.raises(AccountMismatchError):
                await upsert_github_user(
                    db=db_session,
                    email="mismatch@example.com",
                    name="User B",
                    image=None,
                    provider_account_id="22222",
                )
