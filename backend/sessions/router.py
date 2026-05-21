"""Агрегатор сессионных эндпоинтов под общим префиксом из main.py.

FastAPI запрещает include_router, когда у субмаршрута пустой путь и префикс
включения тоже пуст. Поэтому корневые `""` пути собираем через routes.extend,
сохраняя финальный путь от внешнего префикса.
"""

from fastapi import APIRouter

from sessions.routers import (
    activity,
    credentials,
    launch,
    lifecycle,
    node_actions,
    query,
    ws,
)

router = APIRouter()
router.routes.extend(launch.router.routes)
router.routes.extend(lifecycle.router.routes)
router.routes.extend(query.router.routes)
router.routes.extend(node_actions.router.routes)
router.routes.extend(ws.router.routes)
router.routes.extend(credentials.router.routes)
router.routes.extend(activity.router.routes)
