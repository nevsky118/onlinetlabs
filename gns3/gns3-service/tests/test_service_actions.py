"""Unit tests for SessionService.node_action / bulk_node_action."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_sdk.testing import autotest

from src.db.models import Session, SessionStatus
from src.services.session_lifecycle import SessionService


class TestSessionServiceNodeAction:
    """Unit tests for SessionService.node_action."""

    @pytest.fixture
    def admin(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, admin):
        return SessionService(admin_client=admin, gns3_url="http://gns3:3080")

    @pytest.mark.asyncio
    @autotest.num("3368")
    @autotest.external_id("6c7c2763-90ff-4c95-90c9-e4c2c6d30549")
    @autotest.name("SessionService.node_action: calls admin and invalidates the cached state")
    async def test_6c7c2763_node_action_calls_admin_and_invalidates_cache(self, service, admin):
        with autotest.step("Arrange: an active session with a stale cached state"):
            service._state_cache.set("11111111-1111-1111-1111-111111111111", "stale")

            session = MagicMock(spec=Session)
            session.id = "11111111-1111-1111-1111-111111111111"
            session.gns3_project_id = "p1"
            session.status = SessionStatus.ACTIVE
            db = AsyncMock()
            db.get.return_value = session

        with autotest.step("Act: run a node action on the session"):
            await service.node_action(db, "11111111-1111-1111-1111-111111111111", "n1", "start")

        with autotest.step("Assert: admin was called and the cached state was invalidated"):
            admin.node_action.assert_awaited_once_with("p1", "n1", "start")
            assert service._state_cache.get("11111111-1111-1111-1111-111111111111") is None

    @pytest.mark.asyncio
    @autotest.num("3369")
    @autotest.external_id("0b1bc7d9-2559-4d02-a45c-a992ea7fc157")
    @autotest.name("SessionService.node_action: raises when the session is closed")
    async def test_0b1bc7d9_node_action_raises_when_session_closed(self, service):
        with autotest.step("Arrange: a closed session"):
            session = MagicMock(spec=Session)
            session.status = SessionStatus.CLOSED
            db = AsyncMock()
            db.get.return_value = session

        with autotest.step("Act + Assert: a node action on a closed session raises"):
            with pytest.raises(ValueError, match="closed"):
                await service.node_action(db, "11111111-1111-1111-1111-111111111111", "n1", "start")

    @pytest.mark.asyncio
    @autotest.num("3370")
    @autotest.external_id("ec28a122-818e-497c-9679-dbb81e9d3eac")
    @autotest.name("SessionService.node_action: raises when the session is not found")
    async def test_ec28a122_node_action_raises_when_session_not_found(self, service):
        with autotest.step("Arrange: no session found for the id"):
            db = AsyncMock()
            db.get.return_value = None

        with autotest.step("Act + Assert: a node action on a missing session raises"):
            with pytest.raises(ValueError, match="not found"):
                await service.node_action(db, "11111111-1111-1111-1111-111111111111", "n1", "start")


class TestSessionServiceBulkNodeAction:
    """Unit tests for SessionService.bulk_node_action."""

    @pytest.mark.asyncio
    @autotest.num("3371")
    @autotest.external_id("17191d11-3526-40f0-9afd-6476c068f935")
    @autotest.name("SessionService.bulk_node_action: delegates to admin for the session's project")
    async def test_17191d11_bulk_node_action_delegates_to_admin(self):
        with autotest.step("Arrange: a service and an active session"):
            admin = AsyncMock()
            service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")
            session = MagicMock(spec=Session)
            session.gns3_project_id = "p1"
            session.status = SessionStatus.ACTIVE
            db = AsyncMock()
            db.get.return_value = session

        with autotest.step("Act: run a bulk node action on the session"):
            await service.bulk_node_action(db, "11111111-1111-1111-1111-111111111111", "start")

        with autotest.step("Assert: admin's bulk action was called for the session's project"):
            admin.bulk_node_action.assert_awaited_once_with("p1", "start")


class TestSessionServiceCreateSession:
    """Unit tests for SessionService.create_session."""

    @pytest.mark.asyncio
    @autotest.num("3372")
    @autotest.external_id("3f395441-c9e2-4de2-b51b-3553dc1a7979")
    @autotest.name(
        "SessionService.create_session: happy path creates user, project, ACLs and session"
    )
    async def test_3f395441_create_session_happy_path(self, gns3_project, gns3_user):
        with autotest.step("Arrange: admin stubs for a fresh user, project, role and token"):
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

        with autotest.step("Act: create a session for the student"):
            response = await service.create_session(db, student_id, "tmpl-1")

        with autotest.step("Assert: user, project, ACLs and session response are all correct"):
            # The GNS3 user name is a hash of the FULL user_id (the id prefix is not
            # unique and led to deleting someone else's GNS3 user during orphan cleanup).
            from src.gns3_identity import gns3_username_for

            expected_username = gns3_username_for(student_id)

            admin.create_user.assert_awaited_once()
            username_arg, _password_arg = admin.create_user.await_args.args
            assert username_arg == expected_username
            admin.duplicate_project.assert_awaited_once_with(
                "tmpl-1", name=f"session-{expected_username}"
            )
            admin.open_project.assert_awaited_once_with("proj-99")
            # Two ACLs, one on the project itself (User role) and one on the project list
            # (Auditor role). Both go through the RBAC gate sequentially, GNS3 returns 500
            # on concurrent writes.
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
    @autotest.num("3373")
    @autotest.external_id("7f17d6c0-52f7-42cb-a626-15ecc1730c05")
    @autotest.name(
        "SessionService.create_session: an admin error propagates and rolls back user and project"
    )
    async def test_7f17d6c0_create_session_propagates_admin_error_and_rolls_back(
        self,
        gns3_project,
        gns3_user,
    ):
        with autotest.step("Arrange: user and project succeed, opening the project fails"):
            admin = AsyncMock()
            admin.find_user_by_name.return_value = None
            admin.create_user.return_value = gns3_user(user_id="u-42")
            admin.duplicate_project.return_value = gns3_project(project_id="p-99")
            # open_project fails after a successful gather, both resources already exist.
            admin.open_project.side_effect = RuntimeError("409 duplicate")

            service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")
            db = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()

            student_id = "abcdef12-3456-7890-abcd-ef1234567890"

        with autotest.step("Act + Assert: create_session raises the admin error"):
            with pytest.raises(RuntimeError, match="409 duplicate"):
                await service.create_session(db, student_id, "tmpl-1")

        with autotest.step("Assert: the project and user are rolled back, no commit happens"):
            # Rollback must remove both the project and the user.
            admin.delete_project.assert_awaited_with("p-99")
            admin.delete_user.assert_awaited_with("u-42")
            db.commit.assert_not_awaited()


class TestSessionServiceDeleteSession:
    """Unit tests for SessionService.delete_session."""

    @pytest.mark.asyncio
    @autotest.num("3374")
    @autotest.external_id("46892655-2dd1-4305-92c5-907fae60530a")
    @autotest.name(
        "SessionService.delete_session: marks the session closed even when GNS3 teardown fails"
    )
    async def test_46892655_delete_session_finally_marks_closed_even_on_admin_error(self):
        with autotest.step("Arrange: an active session whose GNS3 teardown always fails"):
            admin = AsyncMock()
            # delete_user fails, the inner try/except swallows it.
            # To exercise finally we make delete_project fail as well. Both are
            # wrapped, but finally sets the status in any case.
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

        with autotest.step("Act: delete the session"):
            # delete_session must not raise outward, internal errors are logged.
            await service.delete_session(db, str(session_uuid))

        with autotest.step("Assert: the session is marked closed and committed regardless"):
            assert session.status == SessionStatus.CLOSED
            assert session.closed_at is not None
            db.commit.assert_awaited_once()


class TestSessionServiceDeleteStopsNodes:
    """Deleting a project does not stop docker-typed nodes, so the service must."""

    @pytest.mark.asyncio
    @autotest.num("3397")
    @autotest.external_id("57a08a06-0257-4fb0-9419-e6ecc8f468bc")
    @autotest.name("SessionService.delete_session: stops the nodes before deleting the project")
    async def test_57a08a06_delete_session_stops_nodes_first(self):
        with autotest.step("Arrange: an active session with a working GNS3 admin client"):
            admin = AsyncMock()
            order: list[str] = []
            admin.bulk_node_action.side_effect = lambda *a, **k: order.append("stop")
            admin.delete_project.side_effect = lambda *a, **k: order.append("delete_project")

            service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")
            session_uuid = uuid.UUID("33333333-3333-3333-3333-333333333333")
            session = MagicMock(spec=Session)
            session.id = session_uuid
            session.gns3_user_id = "u-1"
            session.gns3_project_id = "p-1"
            session.status = SessionStatus.ACTIVE
            db = AsyncMock()
            db.get.return_value = session

        with autotest.step("Act: delete the session"):
            await service.delete_session(db, str(session_uuid))

        with autotest.step("Assert: nodes were stopped, and before the project was deleted"):
            admin.bulk_node_action.assert_awaited_once_with("p-1", "stop")
            assert order == ["stop", "delete_project"]

    @pytest.mark.asyncio
    @autotest.num("3398")
    @autotest.external_id("bcb1d2f9-6f1a-4a1e-9d0a-3f52c1f0a7e4")
    @autotest.name("SessionService.delete_session: a failed node stop does not block teardown")
    async def test_bcb1d2f9_delete_session_survives_stop_failure(self):
        with autotest.step("Arrange: stopping the nodes fails"):
            admin = AsyncMock()
            admin.bulk_node_action.side_effect = RuntimeError("gns3 down")

            service = SessionService(admin_client=admin, gns3_url="http://gns3:3080")
            session_uuid = uuid.UUID("44444444-4444-4444-4444-444444444444")
            session = MagicMock(spec=Session)
            session.id = session_uuid
            session.gns3_user_id = "u-2"
            session.gns3_project_id = "p-2"
            session.status = SessionStatus.ACTIVE
            db = AsyncMock()
            db.get.return_value = session

        with autotest.step("Act: delete the session"):
            await service.delete_session(db, str(session_uuid))

        with autotest.step("Assert: the project is still deleted and the session closed"):
            admin.delete_project.assert_awaited_once_with("p-2")
            assert session.status == SessionStatus.CLOSED
