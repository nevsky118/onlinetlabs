"""Тесты error-декоратора `_tool_errors` в mcp_sdk.server.OnlinetlabsMCPServer.

Проверяют контракт ошибок tool-функций: невалидный SessionContext →
SessionContextError, доменная MCPServerError пробрасывается без изменений,
неожиданное исключение маскируется как "Internal server error". Плюс два
bonus-фикса: bad level/since больше не маскируются, а всплывают как
SessionContextError.
"""

import pytest
from mcp_sdk.errors import ComponentNotFoundError, MCPServerError, SessionContextError
from mcp_sdk.models import ActionResult, ComponentDetail, LogLevel, SystemOverview
from mcp_sdk.server import OnlinetlabsMCPServer
from mcp_sdk.testing import autotest

pytestmark = [pytest.mark.unit]

GNS3_URL = "http://gns3-test:3080"

ALL_TOOL_NAMES = [
    "list_components",
    "get_component",
    "get_system_overview",
    "list_errors",
    "get_logs",
    "list_user_actions",
    "list_available_actions",
    "execute_action",
]


def _ctx_dict(**overrides) -> dict:
    defaults = dict(user_id="u1", session_id="s1", environment_url=GNS3_URL, project_id="proj-1")
    return defaults | overrides


def _call_kwargs(name: str, ctx: dict) -> dict:
    """Именованные аргументы, достаточные для вызова каждой из 8 tool-функций."""
    if name == "get_component":
        return {"ctx": ctx, "component_id": "c1"}
    if name == "execute_action":
        return {"ctx": ctx, "action_name": "start_all_nodes", "params": {}}
    return {"ctx": ctx}


class _ProbeImpl:
    """Реализация всех 4 протоколов SDK с управляемым исключением из impl-методов."""

    def __init__(self, raise_error: Exception | None = None) -> None:
        self._raise_error = raise_error

    def _maybe_raise(self) -> None:
        if self._raise_error is not None:
            raise self._raise_error

    async def list_components(self, ctx):
        self._maybe_raise()
        return []

    async def get_component(self, ctx, component_id):
        self._maybe_raise()
        return ComponentDetail(
            id=component_id,
            name="n",
            type="t",
            status="s",
            summary="sum",
            properties={},
            relationships=[],
        )

    async def get_system_overview(self, ctx):
        self._maybe_raise()
        return SystemOverview(
            system_name="x",
            component_count=0,
            components_by_type={},
            components_by_status={},
            summary="s",
        )

    async def list_errors(self, ctx, since=None):
        self._maybe_raise()
        return []

    async def get_logs(self, ctx, level=LogLevel.ALL, limit=100):
        self._maybe_raise()
        return []

    async def list_user_actions(self, ctx, limit=50):
        self._maybe_raise()
        return []

    async def list_available_actions(self, ctx, component_id=None):
        self._maybe_raise()
        return []

    async def execute_action(self, ctx, action_name, params):
        self._maybe_raise()
        return ActionResult(success=True, message="ok")


class _FakeMCP:
    """Замена FastMCP: перехватывает зарегистрированные tool-функции по имени, без реального транспорта."""

    def __init__(self, name, **kwargs) -> None:
        self.tools: dict[str, callable] = {}

    def tool(self, **kwargs):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return decorator


@pytest.fixture()
def make_server(monkeypatch):
    """Строит OnlinetlabsMCPServer поверх _FakeMCP, возвращая фабрику по raise_error."""
    monkeypatch.setattr("mcp_sdk.server.FastMCP", _FakeMCP)

    def _make(raise_error: Exception | None = None) -> OnlinetlabsMCPServer:
        return OnlinetlabsMCPServer(
            name="probe", implementation=_ProbeImpl(raise_error=raise_error)
        )

    return _make


class TestToolErrorContract:
    @autotest.num("827")
    @autotest.external_id("356217db-a3bf-4373-b8af-d4b0a9a240ae")
    @autotest.name("_tool_errors: невалидный ctx → SessionContextError для всех 8 инструментов")
    async def test_invalid_ctx_raises_session_context_error(self, make_server):
        with autotest.step("Готовим сервер с полным набором протоколов"):
            server = make_server()

        with autotest.step("Для каждого инструмента вызываем с ctx без обязательных полей"):
            for name in ALL_TOOL_NAMES:
                fn = server.mcp.tools[name]
                kwargs = _call_kwargs(name, {"user_id": "u1"})
                with pytest.raises(SessionContextError):
                    await fn(**kwargs)

    @autotest.num("828")
    @autotest.external_id("760061cd-e6e3-485c-8cc5-c1789c17be3d")
    @autotest.name("_tool_errors: доменная MCPServerError пробрасывается без оборачивания")
    async def test_domain_error_passthrough(self, make_server):
        with autotest.step("impl бросает ComponentNotFoundError"):
            server = make_server(raise_error=ComponentNotFoundError(component_id="c1"))

        with autotest.step("Вызываем list_components"):
            fn = server.mcp.tools["list_components"]
            with pytest.raises(ComponentNotFoundError):
                await fn(ctx=_ctx_dict())

    @autotest.num("829")
    @autotest.external_id("881a7ba6-da1f-4346-9be1-389c25ffd515")
    @autotest.name("_tool_errors: неожиданное исключение → MCPServerError('Internal server error')")
    async def test_unexpected_error_masked(self, make_server):
        with autotest.step("impl бросает произвольный RuntimeError"):
            server = make_server(raise_error=RuntimeError("boom"))

        with autotest.step("Вызываем list_components и проверяем маскирование"):
            fn = server.mcp.tools["list_components"]
            with pytest.raises(MCPServerError) as exc_info:
                await fn(ctx=_ctx_dict())
            assert str(exc_info.value) == "Internal server error"


class TestBonusArgumentValidation:
    @autotest.num("830")
    @autotest.external_id("433369b4-ad0d-4c39-95bb-420c39c0b72c")
    @autotest.name("get_logs: невалидный level → SessionContextError, не Internal server error")
    async def test_get_logs_invalid_level_raises_session_context_error(self, make_server):
        with autotest.step("Готовим сервер"):
            server = make_server()
            fn = server.mcp.tools["get_logs"]

        with autotest.step("Вызываем с несуществующим level"):
            with pytest.raises(SessionContextError) as exc_info:
                await fn(ctx=_ctx_dict(), level="not-a-level")
            assert "not-a-level" in str(exc_info.value)

    @autotest.num("831")
    @autotest.external_id("a03f92dc-71cd-4332-92b1-e0678ec5f80e")
    @autotest.name("list_errors: невалидный since → SessionContextError, не Internal server error")
    async def test_list_errors_invalid_since_raises_session_context_error(self, make_server):
        with autotest.step("Готовим сервер"):
            server = make_server()
            fn = server.mcp.tools["list_errors"]

        with autotest.step("Вызываем с некорректным since"):
            with pytest.raises(SessionContextError) as exc_info:
                await fn(ctx=_ctx_dict(), since="not-a-date")
            assert "not-a-date" in str(exc_info.value)
