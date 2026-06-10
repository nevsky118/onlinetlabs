# Жизненный цикл лабораторной сессии: create, reset_password, reset_project, delete.
#
# SessionService остаётся публичным фасадом для роутеров и тестов. Тяжёлые
# части (state-снапшот, действия над узлами) делегируются в соседние модули.

from __future__ import annotations

import asyncio
import logging
import secrets
import uuid as uuid_module
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Session, SessionStatus
from src.exceptions import SessionClosed, SessionNotFound
from src.models import (
    PasswordResetResponse,
    ProjectResetResponse,
    SessionResponse,
    SessionStateResponse,
)

from . import node_actions, state_snapshot
from .state_cache import StateCache

if TYPE_CHECKING:
    from src.gns3_admin_client import GNS3AdminClient
    from src.gns3_ws_proxy import Gns3WsProxy

logger = logging.getLogger(__name__)


class SessionService:
    def __init__(
        self,
        admin_client: GNS3AdminClient,
        gns3_url: str,
        gns3_public_url: str | None = None,
        ws_proxy: "Gns3WsProxy | None" = None,
    ) -> None:
        self._admin = admin_client
        self._gns3_url = gns3_url
        self._gns3_public_url = gns3_public_url or gns3_url
        self._ws_proxy = ws_proxy
        self._state_cache: StateCache[SessionStateResponse] = StateCache(ttl_seconds=5.0)

    @property
    def state_cache(self) -> StateCache[SessionStateResponse]:
        return self._state_cache

    def _build_deep_url(self, project_id: str) -> str:
        return f"{self._gns3_public_url.rstrip('/')}/static/web-ui/controller/1/project/{project_id}"

    async def create_session(
        self, db: AsyncSession, user_id: str, template_project_id: str,
    ) -> SessionResponse:
        username = f"student-{user_id[:8]}"
        password = secrets.token_urlsafe(16)
        created_user_id: str | None = None
        created_project_id: str | None = None

        try:
            # Удаляем висячего пользователя student-<uid> от прошлой пересборки.
            # Иначе GNS3 вернёт 400 already registered.
            orphan = await self._admin.find_user_by_name(username)
            if orphan is not None:
                logger.warning(
                    "Removing orphan GNS3 user %s (user_id=%s) before re-creating",
                    username, orphan["user_id"],
                )
                try:
                    await self._admin.delete_user(orphan["user_id"])
                except Exception:
                    logger.exception("Failed to delete orphan user %s", orphan["user_id"])

            # Параллельный запуск. Операции независимы.
            user_task = asyncio.create_task(self._admin.create_user(username, password))
            project_task = asyncio.create_task(
                self._admin.duplicate_project(template_project_id, name=f"session-{username}")
            )
            user, project = await asyncio.gather(user_task, project_task)
            created_user_id = user["user_id"]
            created_project_id = project["project_id"]

            await self._admin.open_project(created_project_id)

            user_role = await self._admin.get_builtin_role("User")
            auditor_role = await self._admin.get_builtin_role("Auditor")
            await asyncio.gather(
                # Доступ к конкретному проекту: полный User-набор (Node.Console и т.д.)
                self._admin.create_acl(
                    f"/projects/{created_project_id}", user_role["role_id"], created_user_id,
                ),
                # Доступ к глобальному списку проектов: только Project.Audit (Auditor).
                # GET /v3/projects возвращает проекты только при ACL на "/projects" —
                # per-project ACL ("/projects/{id}") в список не попадает (GNS3 3.x RBAC).
                self._admin.create_acl(
                    "/projects", auditor_role["role_id"], created_user_id,
                ),
            )

            jwt = await self._admin.get_user_token(username, password)

            session = Session(
                gns3_user_id=created_user_id,
                gns3_username=username,
                gns3_project_id=created_project_id,
                student_user_id=user_id,
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)

            if self._ws_proxy is not None:
                try:
                    await self._ws_proxy.start_project(created_project_id, str(session.id))
                except Exception:
                    logger.exception(
                        "ws_proxy.start_project failed for session %s", session.id
                    )

            return SessionResponse(
                session_id=str(session.id),
                gns3_jwt=jwt,
                project_id=created_project_id,
                gns3_user_id=created_user_id,
                gns3_username=username,
                gns3_password=password,
                gns3_url=self._gns3_public_url,
                gns3_deep_url=self._build_deep_url(created_project_id),
            )
        except Exception:
            await self._rollback_created_resources(created_user_id, created_project_id)
            raise

    async def _rollback_created_resources(
        self,
        user_id: str | None,
        project_id: str | None,
    ) -> None:
        if project_id:
            try:
                await self._admin.delete_project(project_id)
            except Exception:
                logger.exception("Cleanup failed for project %s", project_id)
        if user_id:
            try:
                await self._admin.delete_user(user_id)
            except Exception:
                logger.exception("Cleanup failed for user %s", user_id)

    async def reset_password(self, db: AsyncSession, session_id: str) -> PasswordResetResponse:
        session = await db.get(Session, uuid_module.UUID(session_id))
        if session is None:
            raise SessionNotFound(f"Session {session_id} not found")
        if session.status == SessionStatus.CLOSED:
            raise SessionClosed(f"Session {session_id} is closed")

        new_password = secrets.token_urlsafe(16)
        await self._admin.update_user_password(session.gns3_user_id, new_password)
        jwt = await self._admin.get_user_token(session.gns3_username, new_password)

        # Пароль не сохраняем: студенту он отдан выше через jwt и new_password.

        return PasswordResetResponse(
            session_id=str(session.id),
            gns3_jwt=jwt,
            gns3_username=session.gns3_username,
            gns3_password=new_password,
        )

    async def reset_project(
        self, db: AsyncSession, session_id: str, template_project_id: str,
    ) -> ProjectResetResponse:
        session = await db.get(Session, uuid_module.UUID(session_id))
        if session is None:
            raise SessionNotFound(f"Session {session_id} not found")
        if session.status == SessionStatus.CLOSED:
            raise SessionClosed(f"Session {session_id} is closed")

        old_project_id = session.gns3_project_id
        project = await self._admin.duplicate_project(
            template_project_id, name=f"session-{session.gns3_username}",
        )
        new_project_id = project["project_id"]
        await self._admin.open_project(new_project_id)

        user_role = await self._admin.get_builtin_role("User")
        await self._admin.create_acl(
            f"/projects/{new_project_id}", user_role["role_id"], session.gns3_user_id,
        )

        session.gns3_project_id = new_project_id
        await db.commit()

        if self._ws_proxy is not None:
            try:
                await self._ws_proxy.stop_project(old_project_id)
                await self._ws_proxy.start_project(new_project_id, str(session.id))
            except Exception:
                logger.exception("ws_proxy reset failed for session %s", session.id)

        try:
            await self._admin.delete_project(old_project_id)
        except Exception:
            logger.exception("Failed to delete old project %s", old_project_id)

        return ProjectResetResponse(session_id=str(session.id), project_id=new_project_id)

    async def delete_session(self, db: AsyncSession, session_id: str) -> None:
        session = await db.get(Session, uuid_module.UUID(session_id))
        if session is None:
            raise SessionNotFound(f"Session {session_id} not found")
        if session.status == SessionStatus.CLOSED:
            return

        self.invalidate_state_cache(session_id)

        try:
            if self._ws_proxy is not None:
                try:
                    await self._ws_proxy.stop_project(session.gns3_project_id)
                except Exception:
                    logger.exception(
                        "ws_proxy.stop_project failed for session %s", session.id
                    )

            try:
                await self._admin.delete_user(session.gns3_user_id)
            except Exception:
                logger.exception(
                    "Failed to delete GNS3 user %s", session.gns3_user_id
                )

            try:
                await self._admin.delete_project(session.gns3_project_id)
            except Exception:
                logger.exception(
                    "Failed to delete GNS3 project %s", session.gns3_project_id
                )
        finally:
            # Статус выставляем при любом исходе cleanup: при retry не пытаемся
            # дважды зачистить GNS3-ресурсы, а сама запись помечена закрытой.
            session.status = SessionStatus.CLOSED
            session.closed_at = datetime.now(timezone.utc)
            await db.commit()

    async def get_state(self, db: AsyncSession, session_id: str) -> SessionStateResponse:
        return await state_snapshot.fetch_state(
            self._admin, self._state_cache, db, session_id,
        )

    def invalidate_state_cache(self, session_id: str) -> None:
        self._state_cache.invalidate(session_id)

    async def node_action(self, db, session_id: str, node_id: str, action: str) -> None:
        await node_actions.run_node_action(self._admin, db, session_id, node_id, action)
        self.invalidate_state_cache(session_id)

    async def bulk_node_action(self, db, session_id: str, action: str) -> None:
        await node_actions.run_bulk_node_action(self._admin, db, session_id, action)
        self.invalidate_state_cache(session_id)
