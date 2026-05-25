"""Сервисный слой валидации — owner-guard, прогон runner'а, запись результата."""

from typing import AsyncIterator
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from gns3_service_client import Gns3ServiceClient
from sessions.services.query import get_owned_session
from validation.checks.registry import CheckContext
from validation.repository import create_run, finish_run
from validation.runner import load_lab_spec, run_validation
from validation.stream import Event


class ValidationError(Exception):
    """Базовая ошибка валидации лабы."""

    pass


class SessionNotFound(ValidationError):
    """Сессия не найдена или не принадлежит пользователю."""

    pass


class LabSpecNotFound(ValidationError):
    """Для лабы нет YAML-спецификации проверок."""

    pass


class GNS3SessionMissing(ValidationError):
    """У сессии нет активной GNS3-сессии для прогона проверок."""

    pass


def _gns3_host_from_settings(settings) -> str:
    """Определить хост GNS3 для исходящих соединений из настроек. По умолчанию localhost."""
    gns3 = getattr(settings, "gns3", None)
    if gns3 is not None:
        node_host = getattr(gns3, "node_host", "") or ""
        if node_host:
            return node_host
        for attr in ("internal_url", "public_url"):
            url = getattr(gns3, attr, "") or ""
            if url:
                host = urlparse(url).hostname or ""
                if host and host not in ("gns3-server",):
                    return host
    return "localhost"


async def prepare_validation(
    db: AsyncSession,
    session_id: str,
    lab_slug: str,
    user_id: str,
) -> tuple[dict, str]:
    """Pre-flight: owner-guard + загрузка YAML + проверка gns3 session.

    Returns: `(spec, gns3_service_session_id)`.
    Raises: SessionNotFound, LabSpecNotFound, GNS3SessionMissing.
    """
    session = await get_owned_session(db, session_id, user_id)
    if session is None:
        raise SessionNotFound(session_id)

    spec = load_lab_spec(lab_slug)
    if spec is None:
        raise LabSpecNotFound(lab_slug)

    gns3_sid = (session.meta or {}).get("gns3_service_session_id")
    if not gns3_sid:
        raise GNS3SessionMissing(session_id)

    return spec, gns3_sid


async def stream_validation(
    db: AsyncSession,
    session_id: str,
    lab_slug: str,
    spec: dict,
    gns3_sid: str,
    settings,
    gns3_client: Gns3ServiceClient,
) -> AsyncIterator[Event]:
    """Гонит runner и пишет финальный результат в БД."""
    state = await gns3_client.get_state(gns3_sid)
    nodes = state.get("nodes") or []
    nodes_by_name = {n.get("name"): n for n in nodes if n.get("name")}
    ctx = CheckContext(
        gns3_host=_gns3_host_from_settings(settings),
        nodes_by_name=nodes_by_name,
        gns3_project_id=state.get("project_id", ""),
        frr_client=gns3_client,
    )

    run_id = await create_run(db, session_id, lab_slug)

    final_status = "failed"
    final_steps: list = []
    try:
        async for event, steps_snapshot in run_validation(ctx, spec):
            if event.type == "run.start":
                event.data["runId"] = run_id
            elif event.type == "run.finish":
                event.data["runId"] = run_id
                final_status = "passed" if event.data.get("ok") else "failed"
                final_steps = list(steps_snapshot)
            yield event
    finally:
        await finish_run(db, run_id, final_status, final_steps)
