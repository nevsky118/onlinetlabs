"""Builds SessionContext for MCP calls from LearningSession."""

from mcp_sdk.context import SessionContext

from config import settings
from models.session import LearningSession
from security.secrets import decrypt_secret


def build_session_context(session: LearningSession) -> SessionContext:
    """Builds SessionContext for MCP calls from a learning session, decrypting the gns3 JWT."""
    meta = session.meta or {}
    return SessionContext(
        user_id=session.user_id,
        session_id=session.id,
        environment_url=settings.gns3.internal_url,
        project_id=meta.get("gns3_project_id"),
        metadata={
            "gns3_jwt": decrypt_secret(meta["enc_jwt"]),
            # gns3-service session id — the actual history key (ctx.session_id = backend id).
            "gns3_session_id": meta.get("gns3_service_session_id"),
        },
    )
