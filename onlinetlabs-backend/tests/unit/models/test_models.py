import pytest

from models.course import Course
from models.enums import (
    AttemptResult,
    Difficulty,
    EnvironmentType,
    ProgressStatus,
    SessionStatus,
)
from models.lab import Lab, LabStep
from models.progress import CourseProgress, LabProgress, StepAttempt
from models.session import LearningSession
from models.user import User, UserRole
from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.smoke]


class TestUserRole:
    @autotests.num("3")
    @autotests.external_id("e922c8b8-5435-499b-abec-4893a4624825")
    @autotests.name("UserRole: значения enum")
    def test_values(self):
        """Проверяет что enum UserRole содержит корректные значения."""

        with autotests.step("Проверяем значения student, instructor, admin"):
            assert UserRole.STUDENT == "student"
            assert UserRole.INSTRUCTOR == "instructor"
            assert UserRole.ADMIN == "admin"

    @autotests.num("4")
    @autotests.external_id("2db0f484-d4af-4f28-90e8-4184755e639d")
    @autotests.name("UserRole: наследует str")
    def test_is_string(self):
        """Проверяет что UserRole является подклассом str."""

        with autotests.step("Проверяем isinstance(UserRole.STUDENT, str)"):
            assert isinstance(UserRole.STUDENT, str)


class TestUserModel:
    @autotests.num("5")
    @autotests.external_id("bc19acb1-74e6-47c4-bbfd-2ddafe3f2f49")
    @autotests.name("User: наличие полей password_hash и role")
    def test_has_fields(self):
        """Проверяет что модель User содержит password_hash и role."""

        # Act
        with autotests.step("Получаем список колонок модели User"):
            columns = {c.name for c in User.__table__.columns}

        # Assert
        with autotests.step("Проверяем наличие password_hash и role"):
            assert "password_hash" in columns
            assert "role" in columns


class TestDifficulty:
    @autotests.num("6")
    @autotests.external_id("aa63a1c0-4f34-496b-a09d-674d2378c416")
    @autotests.name("Difficulty: значения enum")
    def test_values(self):
        """Проверяет значения enum Difficulty."""

        with autotests.step("Проверяем значения beginner, intermediate, advanced"):
            assert Difficulty.BEGINNER == "beginner"
            assert Difficulty.INTERMEDIATE == "intermediate"
            assert Difficulty.ADVANCED == "advanced"

    @autotests.num("7")
    @autotests.external_id("7da05cdc-b614-402d-9157-f646d87a6c90")
    @autotests.name("Difficulty: наследует str")
    def test_is_string(self):
        """Проверяет что Difficulty является подклассом str."""

        with autotests.step("Проверяем isinstance(Difficulty.BEGINNER, str)"):
            assert isinstance(Difficulty.BEGINNER, str)


class TestProgressStatus:
    @autotests.num("8")
    @autotests.external_id("b4e65df6-16ed-4a75-a4a8-e0c34024aaa2")
    @autotests.name("ProgressStatus: значения enum")
    def test_values(self):
        """Проверяет значения enum ProgressStatus."""

        with autotests.step("Проверяем значения not_started, in_progress, completed"):
            assert ProgressStatus.NOT_STARTED == "not_started"
            assert ProgressStatus.IN_PROGRESS == "in_progress"
            assert ProgressStatus.COMPLETED == "completed"


class TestAttemptResult:
    @autotests.num("9")
    @autotests.external_id("af50b886-fa41-4874-b113-7ea4323655e7")
    @autotests.name("AttemptResult: значения enum")
    def test_values(self):
        """Проверяет значения enum AttemptResult."""

        with autotests.step("Проверяем значения pass, fail, partial"):
            assert AttemptResult.PASS == "pass"
            assert AttemptResult.FAIL == "fail"
            assert AttemptResult.PARTIAL == "partial"


class TestSessionStatus:
    @autotests.num("10")
    @autotests.external_id("38fbd87f-fc6d-4724-aa23-ad398e4b5451")
    @autotests.name("SessionStatus: значения enum")
    def test_values(self):
        """Проверяет значения enum SessionStatus."""

        with autotests.step("Проверяем значения active, completed, abandoned"):
            assert SessionStatus.ACTIVE == "active"
            assert SessionStatus.COMPLETED == "completed"
            assert SessionStatus.ABANDONED == "abandoned"


class TestEnvironmentType:
    @autotests.num("11")
    @autotests.external_id("61766fcf-9ddf-45c7-b4f1-9f12a15510b3")
    @autotests.name("EnvironmentType: значения enum")
    def test_values(self):
        """Проверяет значения enum EnvironmentType."""

        with autotests.step("Проверяем значения gns3, docker, none"):
            assert EnvironmentType.GNS3 == "gns3"
            assert EnvironmentType.DOCKER == "docker"
            assert EnvironmentType.NONE == "none"


class TestCourseModel:
    @autotests.num("12")
    @autotests.external_id("75d8bb3f-6b49-4402-ab53-590d1e9e7490")
    @autotests.name("Course: наличие основных полей")
    def test_has_fields(self):
        """Проверяет что модель Course содержит основные поля."""

        with autotests.step("Получаем список колонок модели Course"):
            columns = {c.name for c in Course.__table__.columns}

        with autotests.step("Проверяем наличие полей"):
            for field in (
                "slug",
                "title",
                "description",
                "difficulty",
                "order",
                "prerequisites",
                "meta",
                "created_at",
                "updated_at",
            ):
                assert field in columns, f"Поле {field} отсутствует"

    @autotests.num("13")
    @autotests.external_id("00e576c3-3ba6-4085-b28a-08b9d068da77")
    @autotests.name("Course: slug является первичным ключом")
    def test_slug_is_pk(self):
        """Проверяет что slug — первичный ключ Course."""

        with autotests.step("Проверяем primary key"):
            pk_cols = [c.name for c in Course.__table__.primary_key.columns]
            assert pk_cols == ["slug"]


class TestLabModel:
    @autotests.num("14")
    @autotests.external_id("cc91f354-b7e0-44f3-a575-2711383f17a3")
    @autotests.name("Lab: наличие основных полей")
    def test_has_fields(self):
        """Проверяет что модель Lab содержит основные поля."""

        with autotests.step("Получаем список колонок модели Lab"):
            columns = {c.name for c in Lab.__table__.columns}

        with autotests.step("Проверяем наличие полей"):
            for field in (
                "slug",
                "title",
                "description",
                "difficulty",
                "course_slug",
                "order_in_course",
                "environment_type",
                "meta",
                "created_at",
                "updated_at",
            ):
                assert field in columns, f"Поле {field} отсутствует"

    @autotests.num("15")
    @autotests.external_id("32ac527f-6965-45b7-bf6c-43a4db7d2750")
    @autotests.name("Lab: slug является первичным ключом")
    def test_slug_is_pk(self):
        """Проверяет что slug — первичный ключ Lab."""

        with autotests.step("Проверяем primary key"):
            pk_cols = [c.name for c in Lab.__table__.primary_key.columns]
            assert pk_cols == ["slug"]

    @autotests.num("16")
    @autotests.external_id("88b659f8-39c2-4ce6-be00-3c480897cacd")
    @autotests.name("Lab: course_slug допускает NULL")
    def test_course_slug_nullable(self):
        """Проверяет что course_slug может быть NULL."""

        with autotests.step("Проверяем nullable"):
            col = Lab.__table__.columns["course_slug"]
            assert col.nullable is True


class TestLabStepModel:
    @autotests.num("17")
    @autotests.external_id("409a2ac3-63c3-47fb-8a16-878bdafe9b0a")
    @autotests.name("LabStep: наличие основных полей")
    def test_has_fields(self):
        """Проверяет что модель LabStep содержит основные поля."""

        with autotests.step("Получаем список колонок модели LabStep"):
            columns = {c.name for c in LabStep.__table__.columns}

        with autotests.step("Проверяем наличие полей"):
            for field in (
                "id",
                "lab_slug",
                "step_order",
                "slug",
                "title",
                "validation_type",
            ):
                assert field in columns, f"Поле {field} отсутствует"


class TestCourseProgressModel:
    @autotests.num("18")
    @autotests.external_id("895aa1c6-066b-45da-8026-60a3eab9b2b3")
    @autotests.name("CourseProgress: наличие основных полей")
    def test_has_fields(self):
        """Проверяет что модель CourseProgress содержит основные поля."""

        with autotests.step("Получаем список колонок модели CourseProgress"):
            columns = {c.name for c in CourseProgress.__table__.columns}

        with autotests.step("Проверяем наличие полей"):
            for field in (
                "id",
                "user_id",
                "course_slug",
                "status",
                "score",
                "started_at",
                "completed_at",
                "updated_at",
            ):
                assert field in columns, f"Поле {field} отсутствует"

    @autotests.num("19")
    @autotests.external_id("21bb44c4-5aa2-4705-8614-caed9b0f9f44")
    @autotests.name("CourseProgress: уникальность user_id + course_slug")
    def test_unique_constraint(self):
        """Проверяет уникальный constraint на user_id + course_slug."""

        with autotests.step("Проверяем наличие unique constraint"):
            constraint_names = {c.name for c in CourseProgress.__table__.constraints}
            assert "uq_course_progress_user_course" in constraint_names


class TestLabProgressModel:
    @autotests.num("20")
    @autotests.external_id("d4a66e47-05be-462e-b0f2-d433cea8f34d")
    @autotests.name("LabProgress: наличие основных полей")
    def test_has_fields(self):
        """Проверяет что модель LabProgress содержит основные поля."""

        with autotests.step("Получаем список колонок модели LabProgress"):
            columns = {c.name for c in LabProgress.__table__.columns}

        with autotests.step("Проверяем наличие полей"):
            for field in (
                "id",
                "user_id",
                "lab_slug",
                "status",
                "score",
                "current_step",
                "started_at",
                "completed_at",
                "updated_at",
            ):
                assert field in columns, f"Поле {field} отсутствует"

    @autotests.num("21")
    @autotests.external_id("cbc5d938-3a7f-4e1f-92b3-74dfa69d4b49")
    @autotests.name("LabProgress: уникальность user_id + lab_slug")
    def test_unique_constraint(self):
        """Проверяет уникальный constraint на user_id + lab_slug."""

        with autotests.step("Проверяем наличие unique constraint"):
            constraint_names = {c.name for c in LabProgress.__table__.constraints}
            assert "uq_lab_progress_user_lab" in constraint_names


class TestStepAttemptModel:
    @autotests.num("22")
    @autotests.external_id("962a9e92-d690-4bdc-a41c-26933e8bf831")
    @autotests.name("StepAttempt: наличие основных полей")
    def test_has_fields(self):
        """Проверяет что модель StepAttempt содержит основные поля."""

        with autotests.step("Получаем список колонок модели StepAttempt"):
            columns = {c.name for c in StepAttempt.__table__.columns}

        with autotests.step("Проверяем наличие полей"):
            for field in (
                "id",
                "user_id",
                "lab_slug",
                "step_slug",
                "attempt_number",
                "result",
                "score",
                "error_details",
                "started_at",
                "ended_at",
            ):
                assert field in columns, f"Поле {field} отсутствует"


class TestLearningSessionModel:
    @autotests.num("23")
    @autotests.external_id("9a33c3d8-9924-4f9b-8f07-08dc57d2bbf5")
    @autotests.name("LearningSession: наличие основных полей")
    def test_has_fields(self):
        """Проверяет что модель LearningSession содержит основные поля."""

        with autotests.step("Получаем список колонок модели LearningSession"):
            columns = {c.name for c in LearningSession.__table__.columns}

        with autotests.step("Проверяем наличие полей"):
            for field in (
                "id",
                "user_id",
                "lab_slug",
                "status",
                "started_at",
                "ended_at",
                "meta",
            ):
                assert field in columns, f"Поле {field} отсутствует"
