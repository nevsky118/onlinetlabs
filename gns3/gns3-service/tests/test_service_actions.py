"""Unit-тесты SessionService.node_action / bulk_node_action."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.db.models import Session, SessionStatus
from src.services.session_lifecycle import SessionService


class TestSessionServiceNodeAction:
    """Unit-тесты SessionService.node_action."""

    @pytest.fixture
    def admin(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, admin):
        return SessionService(admin_client=admin, gns3_url="http://gns3:3080")

    @pytest.mark.asyncio
    async def test_node_action_calls_admin_and_invalidates_cache(self, service, admin):
        service._state_cache["11111111-1111-1111-1111-111111111111"] = (1.0, "stale")

        session = MagicMock(spec=Session)
        session.id = "11111111-1111-1111-1111-111111111111"
        session.gns3_project_id = "p1"
        session.status = SessionStatus.ACTIVE
        db = AsyncMock()
        db.get.return_value = session

        await service.node_action(db, "11111111-1111-1111-1111-111111111111", "n1", "start")
        admin.node_action.assert_awaited_once_with("p1", "n1", "start")
        assert "11111111-1111-1111-1111-111111111111" not in service._state_cache

    @pytest.mark.asyncio
    async def test_node_action_raises_when_session_closed(self, service):
        session = MagicMock(spec=Session)
        session.status = SessionStatus.CLOSED
        db = AsyncMock()
        db.get.return_value = session

        with pytest.raises(ValueError, match="closed"):
            await service.node_action(db, "11111111-1111-1111-1111-111111111111", "n1", "start")

    @pytest.mark.asyncio
    async def test_node_action_raises_when_session_not_found(self, service):
        db = AsyncMock()
        db.get.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await service.node_action(db, "11111111-1111-1111-1111-111111111111", "n1", "start")


class TestSessionServiceBulkNodeAction:
    """Unit-тесты SessionService.bulk_node_action."""

    @pytest.mark.asyncio
    async def test_bulk_node_action_delegates_to_admin(self):
        admin = AsyncMock()
        service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")
        session = MagicMock(spec=Session)
        session.gns3_project_id = "p1"
        session.status = SessionStatus.ACTIVE
        db = AsyncMock()
        db.get.return_value = session

        await service.bulk_node_action(db, "11111111-1111-1111-1111-111111111111", "start")
        admin.bulk_node_action.assert_awaited_once_with("p1", "start")


class TestSessionServiceCreateSession:
    """Unit-тесты SessionService.create_session."""

    @pytest.mark.asyncio
    async def test_create_session_happy_path(self, gns3_project, gns3_user):
        admin = AsyncMock()
        admin.find_user_by_name.return_value = None
        user = gns3_user(user_id="u-42", username="student-abcdef12")
        project = gns3_project(project_id="proj-99")
        admin.create_user.return_value = user
        admin.duplicate_project.return_value = project
        admin.get_builtin_role.return_value = {"role_id": "role-user"}
        admin.get_user_token.return_value = "jwt-token-xyz"

        service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")

        # db.add — sync, db.commit/refresh — async.
        db = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        student_id = "abcdef12-3456-7890-abcd-ef1234567890"
        response = await service.create_session(db, student_id, "tmpl-1")

        # Имя GNS3-юзера — хеш ПОЛНОГО user_id (префикс id не уникален и приводил
        # к удалению чужого GNS3-пользователя при orphan-cleanup).
        from src.gns3_identity import gns3_username_for
        expected_username = gns3_username_for(student_id)

        admin.create_user.assert_awaited_once()
        username_arg, _password_arg = admin.create_user.await_args.args
        assert username_arg == expected_username
        admin.duplicate_project.assert_awaited_once_with(
            "tmpl-1", name=f"session-{expected_username}"
        )
        admin.open_project.assert_awaited_once_with("proj-99")
        # Два ACL: на сам проект (роль User) и на список проектов (роль Auditor) —
        # оба через RBAC-гейт и последовательно, GNS3 500-тит на параллельных записях.
        acl_calls = [c.args for c in admin.create_acl.await_args_list]
        assert acl_calls == [
            ("/projects/proj-99", "role-user", "u-42"),
            ("/projects", "role-user", "u-42"),
        ], f"ожидались ACL на проект и на /projects, получили {acl_calls}"
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once()
        assert response.project_id == "proj-99"
        assert response.gns3_user_id == "u-42"
        assert response.gns3_username == expected_username
        assert response.gns3_jwt == "jwt-token-xyz"
        assert response.gns3_url == "http://gns3:3080"
        assert "proj-99" in response.gns3_deep_url

    @pytest.mark.asyncio
    async def test_create_session_propagates_admin_error_and_rolls_back(
        self, gns3_project, gns3_user,
    ):
        admin = AsyncMock()
        admin.find_user_by_name.return_value = None
        admin.create_user.return_value = gns3_user(user_id="u-42")
        admin.duplicate_project.return_value = gns3_project(project_id="p-99")
        # open_project падает после успешного gather — оба ресурса уже созданы.
        admin.open_project.side_effect = RuntimeError("409 duplicate")

        service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")
        db = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        student_id = "abcdef12-3456-7890-abcd-ef1234567890"
        with pytest.raises(RuntimeError, match="409 duplicate"):
            await service.create_session(db, student_id, "tmpl-1")

        # Rollback должен снести и проект, и пользователя.
        admin.delete_project.assert_awaited_with("p-99")
        admin.delete_user.assert_awaited_with("u-42")
        db.commit.assert_not_awaited()


class TestSessionServiceDeleteSession:
    """Unit-тесты SessionService.delete_session."""

    @pytest.mark.asyncio
    async def test_delete_session_finally_marks_closed_even_on_admin_error(self):
        admin = AsyncMock()
        # delete_user падает; внутренний try/except его глотает.
        # Чтобы проверить finally, заставим упасть и delete_project тоже —
        # они оба обёрнуты, но finally в любом случае выставит статус.
        admin.delete_user.side_effect = RuntimeError("boom")
        admin.delete_project.side_effect = RuntimeError("kaboom")

        service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")

        session_uuid = uuid.UUID("22222222-2222-2222-2222-222222222222")
        session = MagicMock(spec=Session)
        session.id = session_uuid
        session.gns3_user_id = "u-42"
        session.gns3_project_id = "p-99"
        session.status = SessionStatus.ACTIVE
        db = AsyncMock()
        db.get.return_value = session

        # delete_session не должен выбросить наружу: внутренние ошибки логируются.
        await service.delete_session(db, str(session_uuid))

        assert session.status == SessionStatus.CLOSED
        assert session.closed_at is not None
        db.commit.assert_awaited_once()


class TestSessionServiceResetPassword:
    """Unit-тесты SessionService.reset_password."""

    @pytest.mark.asyncio
    async def test_reset_password_calls_admin_without_storing_hash(self):
        admin = AsyncMock()
        admin.update_user_password.return_value = None
        admin.get_user_token.return_value = "fresh-jwt"

        service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")

        session_uuid = uuid.UUID("33333333-3333-3333-3333-333333333333")
        session = MagicMock(spec=Session)
        session.id = session_uuid
        session.gns3_user_id = "u-42"
        session.gns3_username = "student-abcdef12"
        session.status = SessionStatus.ACTIVE
        db = AsyncMock()
        db.get.return_value = session

        response = await service.reset_password(db, str(session_uuid))

        admin.update_user_password.assert_awaited_once()
        called_user_id, called_password = admin.update_user_password.await_args.args
        assert called_user_id == "u-42"
        # Пароль должен быть свежим plaintext, не sha256-хэшем.
        assert isinstance(called_password, str) and len(called_password) > 0
        admin.get_user_token.assert_awaited_once_with(
            "student-abcdef12", called_password
        )
        # В БД ничего не пишем: commit не вызывается, hash-поля не трогаем.
        db.commit.assert_not_awaited()
        assert response.gns3_password == called_password
        assert response.gns3_jwt == "fresh-jwt"
        assert response.gns3_username == "student-abcdef12"
