"""Агрегатор сессионных эндпоинтов под общим префиксом из main.py.

commands.router и queries.router каждый содержат хендлер с корневым `""`
путём (POST-launch и GET-list соответственно). FastAPI запрещает
include_router, когда и префикс включения, и путь субмаршрута пустые
одновременно ("Prefix and path cannot be both empty") — поэтому для них
используем routes.extend (просто конкатенация списка Route, без валидации
FastAPI). Явный непустой путь (например "/") избавил бы от этого, но меняет
итоговый маршрут (появляется trailing slash → 307-редирект вместо прямого
200), что нарушает требование идентичной маршрутной таблицы — поэтому не
используется. У ws.router нет корневого пути, поэтому include_router для
него работает без обходных путей.

Порядок регистрации значим только внутри queries.py: там литеральный
`/queue-status` зарегистрирован раньше catch-all `/{session_id}`, иначе
последний проглотил бы его (Starlette матчит маршруты в порядке
регистрации). Порядок commands/ws/queries между собой на матчинг не влияет
(разные методы или разное число сегментов пути), но сохранён для читаемости.
"""

from fastapi import APIRouter

from sessions.routers import commands, queries, ws

router = APIRouter()
router.routes.extend(commands.router.routes)
router.include_router(ws.router)
router.routes.extend(queries.router.routes)
