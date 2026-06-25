"""FastAPI-зависимости из app.state."""

from fastapi import Request


def get_mcp_client(request: Request):
    """Отдаёт MCP-клиент из app.state."""
    return request.app.state.mcp_client


def get_gateway(request: Request):
    """Отдаёт WebSocket-шлюз из app.state."""
    return request.app.state.gateway


def get_orchestrator(request: Request):
    """Отдаёт оркестратор агентов из app.state."""
    return request.app.state.orchestrator


def get_gns3_client(request: Request):
    """Отдаёт клиент gns3-service из app.state."""
    return request.app.state.gns3_client


def get_session_factory():
    """Отдаёт фабрику сессий БД (переопределяется в тестах)."""
    from db.session import async_session
    return async_session


def get_monitor_registry(request: Request):
    """Отдаёт реестр мониторов сессий из app.state."""
    return request.app.state.monitor_registry


def get_state_cache(request: Request):
    """Отдаёт кэш состояния сессий из app.state."""
    return request.app.state.state_cache


def get_activity_log(request: Request):
    """Отдаёт лог активности агентов из app.state."""
    return request.app.state.activity_log
