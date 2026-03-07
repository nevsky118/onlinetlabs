# Бизнес-логика gns3-service — session lifecycle.

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Session, SessionStatus
from src.models import PasswordResetResponse, SessionResponse

if TYPE_CHECKING:
    from src.gns3_admin_client import GNS3AdminClient

logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self, admin_client: GNS3AdminClient, gns3_url: str) -> None:
        self._admin = admin_client
        self._gns3_url = gns3_url

    async def create_session(self, db: AsyncSession, user_id: str, template_project_id: str) -> SessionResponse:
        username = f"student-{user_id[:8]}"
        password = secrets.token_urlsafe(16)
        created_user_id: str | None = None
        created_project_id: str | None = None

        try:
            user = await self._admin.create_user(username, password)
            created_user_id = user["user_id"]

            project = await self._admin.duplicate_project(
                template_project_id, name=f"session-{username}",
            )
            created_project_id = project["project_id"]
            await self._admin.open_project(created_project_id)

            user_role = await self._admin.get_builtin_role("User")
            await self._admin.create_acl(
                f"/projects/{created_project_id}", user_role["role_id"], created_user_id,
            )

            jwt = await self._admin.get_user_token(username, password)

            session = Session(
                gns3_user_id=created_user_id,
                gns3_username=username,
                gns3_password_hash=hashlib.sha256(password.encode()).hexdigest(),
                gns3_project_id=created_project_id,
                student_user_id=user_id,
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)

            return SessionResponse(
                session_id=str(session.id),
                gns3_jwt=jwt,
                project_id=created_project_id,
                gns3_user_id=created_user_id,
                gns3_username=username,
                gns3_password=password,
                gns3_url=self._gns3_url,
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
        import uuid as uuid_mod
        session = await db.get(Session, uuid_mod.UUID(session_id))
        if session is None:
            raise ValueError(f"Session {session_id} not found")
        if session.status == SessionStatus.CLOSED:
            raise ValueError(f"Session {session_id} is closed")

        new_password = secrets.token_urlsafe(16)
        await self._admin.update_user_password(session.gns3_user_id, new_password)
        jwt = await self._admin.get_user_token(session.gns3_username, new_password)

        session.gns3_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        await db.commit()

        return PasswordResetResponse(
            session_id=str(session.id),
            gns3_jwt=jwt,
            gns3_username=session.gns3_username,
            gns3_password=new_password,
        )

    async def delete_session(self, db: AsyncSession, session_id: str) -> None:
        import uuid as uuid_mod
        session = await db.get(Session, uuid_mod.UUID(session_id))
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        try:
            await self._admin.delete_user(session.gns3_user_id)
        except Exception:
            logger.exception("Failed to delete GNS3 user %s", session.gns3_user_id)

        session.status = SessionStatus.CLOSED
        session.closed_at = datetime.now(timezone.utc)
        await db.commit()
