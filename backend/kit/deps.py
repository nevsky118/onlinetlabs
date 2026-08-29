"""FastAPI dependencies pulled from app.state."""

from fastapi import Request

from i18n import Locale, negotiate
from kit.db import async_session


def get_mcp_client(request: Request):
    """Returns the MCP client from app.state."""
    return request.app.state.mcp_client


def get_gns3_client(request: Request):
    """Returns the gns3-service client from app.state."""
    return request.app.state.gns3_client


def get_session_factory():
    """Returns the DB session factory (overridden in tests)."""

    return async_session


def get_monitor_registry(request: Request):
    """Returns the session monitor registry from app.state."""
    return request.app.state.monitor_registry


def get_state_cache(request: Request):
    """Returns the session state cache from app.state."""
    return request.app.state.state_cache


def get_activity_log(request: Request):
    """Returns the agent activity log from app.state."""
    return request.app.state.activity_log


def get_locale(request: Request) -> Locale:
    """Request locale from the X-Locale header set by the frontend BFF."""
    return negotiate(request.headers.get("x-locale"))
