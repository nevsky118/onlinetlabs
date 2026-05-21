"""Сборка SessionContext для MCP-вызовов из LearningSession."""

from mcp_sdk.context import SessionContext

from config import settings
from security.secrets import decrypt_secret
from models.session import LearningSession


def build_session_context(session: LearningSession) -> SessionContext:
    """Собирает SessionContext для MCP-вызовов из учебной сессии, расшифровывая JWT gns3."""
    meta = session.meta or {}
    return SessionContext(
        user_id=session.user_id,
        session_id=session.id,
        environment_url=settings.gns3.internal_url,
        project_id=meta.get("gns3_project_id"),
        metadata={"gns3_jwt": decrypt_secret(meta["enc_jwt"])},
    )
