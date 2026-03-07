import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.report import autotests

pytestmark = [pytest.mark.unit, pytest.mark.service]


class TestSessionService:
    @pytest.fixture
    def admin_client(self):
        mock = AsyncMock()
        mock.create_user.return_value = {"user_id": "gns3-uid-1", "username": "student-abc12345"}
        mock.duplicate_project.return_value = {"project_id": "new-pid"}
        mock.open_project.return_value = {"project_id": "new-pid", "status": "opened"}
        mock.get_builtin_role.return_value = {"role_id": "builtin-user-role", "name": "User", "is_builtin": True}
        mock.create_acl.return_value = {"ace_id": "ace-1"}
        mock.get_user_token.return_value = "student-jwt"
        return mock

    @pytest.fixture
    def db_session(self):
        mock = AsyncMock()
        mock.add = MagicMock()
        mock.commit = AsyncMock()
        mock.refresh = AsyncMock()
        return mock

    @autotests.num("440")
    @autotests.external_id("f1a2b3c4-0001-4fff-aaaa-440000000001")
    @autotests.name("GNS3 Session Service: create_session полный цикл")
    async def test_create_session(self, admin_client, db_session):
        from src.service import SessionService

        svc = SessionService(admin_client=admin_client, gns3_url="http://gns3:3080")
        result = await svc.create_session(db=db_session, user_id="student-1", template_project_id="template-pid")
        assert result.gns3_jwt == "student-jwt"
        assert result.project_id == "new-pid"
        assert result.gns3_username.startswith("student-")
        assert result.gns3_password
        admin_client.create_user.assert_called_once()
        admin_client.duplicate_project.assert_called_once_with(
            "template-pid", name="session-student-student-",
        )
        admin_client.get_builtin_role.assert_called_once_with("User")
        admin_client.create_acl.assert_called_once_with(
            "/projects/new-pid", "builtin-user-role", "gns3-uid-1",
        )

    @autotests.num("441")
    @autotests.external_id("f1a2b3c4-0002-4fff-aaaa-441000000001")
    @autotests.name("GNS3 Session Service: delete_session очищает ресурсы")
    async def test_delete_session(self, admin_client, db_session):
        from src.db.models import Session
        from src.db.models import SessionStatus as DBStatus
        from src.service import SessionService

        mock_session = Session(
            id=uuid.uuid4(),
            gns3_user_id="gns3-uid-1",
            gns3_username="student-abc",
            gns3_password_hash="hash",
            gns3_project_id="pid",
            student_user_id="student-1",
        )
        db_session.get = AsyncMock(return_value=mock_session)
        svc = SessionService(admin_client=admin_client, gns3_url="http://gns3:3080")
        await svc.delete_session(db=db_session, session_id=str(mock_session.id))
        admin_client.delete_user.assert_called_once_with("gns3-uid-1")
        assert mock_session.status == DBStatus.CLOSED

    @autotests.num("442")
    @autotests.external_id("f1a2b3c4-0003-4fff-aaaa-442000000001")
    @autotests.name("GNS3 Session Service: create_session откат при ошибке duplicate")
    async def test_create_session_rollback(self, admin_client, db_session):
        from src.service import SessionService

        admin_client.duplicate_project.side_effect = Exception("GNS3 down")
        svc = SessionService(admin_client=admin_client, gns3_url="http://gns3:3080")
        with pytest.raises(Exception, match="GNS3 down"):
            await svc.create_session(db=db_session, user_id="s1", template_project_id="t1")
        admin_client.delete_user.assert_called_once()

    @autotests.num("443")
    @autotests.external_id("f1a2b3c4-0004-4fff-aaaa-443000000001")
    @autotests.name("GNS3 Session Service: откат удаляет project при ошибке ACL")
    async def test_create_session_rollback_after_acl_error(self, admin_client, db_session):
        from src.service import SessionService

        admin_client.create_acl.side_effect = Exception("ACL 422")
        svc = SessionService(admin_client=admin_client, gns3_url="http://gns3:3080")
        with pytest.raises(Exception, match="ACL 422"):
            await svc.create_session(db=db_session, user_id="s1", template_project_id="t1")
        admin_client.delete_project.assert_called_once_with("new-pid")
        admin_client.delete_user.assert_called_once()

    @autotests.num("444")
    @autotests.external_id("f1a2b3c4-0005-4fff-aaaa-444000000001")
    @autotests.name("GNS3 Session Service: delete_session несуществующей сессии бросает ValueError")
    async def test_delete_session_not_found(self, admin_client, db_session):
        from src.service import SessionService

        db_session.get = AsyncMock(return_value=None)
        svc = SessionService(admin_client=admin_client, gns3_url="http://gns3:3080")
        with pytest.raises(ValueError, match="not found"):
            await svc.delete_session(db=db_session, session_id=str(uuid.uuid4()))

    @autotests.num("445")
    @autotests.external_id("f1a2b3c4-0006-4fff-aaaa-445000000001")
    @autotests.name("GNS3 Session Service: reset_password генерирует новый пароль и JWT")
    async def test_reset_password(self, admin_client, db_session):
        from src.db.models import Session
        from src.service import SessionService

        with autotests.step("Подготовка — активная сессия"):
            mock_session = Session(
                id=uuid.uuid4(),
                gns3_user_id="gns3-uid-1",
                gns3_username="student-abc",
                gns3_password_hash="old-hash",
                gns3_project_id="pid",
                student_user_id="student-1",
            )
            db_session.get = AsyncMock(return_value=mock_session)
            admin_client.get_user_token.return_value = "new-jwt"

        with autotests.step("Вызываем reset_password"):
            svc = SessionService(admin_client=admin_client, gns3_url="http://gns3:3080")
            result = await svc.reset_password(db=db_session, session_id=str(mock_session.id))

        with autotests.step("Проверяем результат"):
            assert result.gns3_jwt == "new-jwt"
            assert result.gns3_username == "student-abc"
            assert result.gns3_password

        with autotests.step("Хеш обновлён в БД"):
            assert mock_session.gns3_password_hash != "old-hash"
            db_session.commit.assert_called()

        with autotests.step("Вызовы admin API корректны"):
            admin_client.update_user_password.assert_called_once_with("gns3-uid-1", result.gns3_password)
            admin_client.get_user_token.assert_called_with("student-abc", result.gns3_password)

    @autotests.num("446")
    @autotests.external_id("f1a2b3c4-0007-4fff-aaaa-446000000001")
    @autotests.name("GNS3 Session Service: reset_password несуществующей сессии бросает ValueError")
    async def test_reset_password_not_found(self, admin_client, db_session):
        from src.service import SessionService

        with autotests.step("Сессия не найдена в БД"):
            db_session.get = AsyncMock(return_value=None)

        with autotests.step("reset_password бросает ValueError"):
            svc = SessionService(admin_client=admin_client, gns3_url="http://gns3:3080")
            with pytest.raises(ValueError, match="not found"):
                await svc.reset_password(db=db_session, session_id=str(uuid.uuid4()))

    @autotests.num("447")
    @autotests.external_id("f1a2b3c4-0008-4fff-aaaa-447000000001")
    @autotests.name("GNS3 Session Service: reset_password закрытой сессии бросает ValueError")
    async def test_reset_password_closed_session(self, admin_client, db_session):
        from src.db.models import Session
        from src.db.models import SessionStatus as DBStatus
        from src.service import SessionService

        with autotests.step("Подготовка — закрытая сессия"):
            mock_session = Session(
                id=uuid.uuid4(),
                gns3_user_id="gns3-uid-1",
                gns3_username="student-abc",
                gns3_password_hash="hash",
                gns3_project_id="pid",
                student_user_id="student-1",
                status=DBStatus.CLOSED,
            )
            db_session.get = AsyncMock(return_value=mock_session)

        with autotests.step("reset_password бросает ValueError"):
            svc = SessionService(admin_client=admin_client, gns3_url="http://gns3:3080")
            with pytest.raises(ValueError, match="closed"):
                await svc.reset_password(db=db_session, session_id=str(mock_session.id))
