"""BehavioralCollector — опрос MCP-сервера и сохранение поведенческих событий."""

import asyncio
import hashlib
import logging
from collections import OrderedDict
from datetime import datetime, timezone
from uuid import uuid4

from mcp_sdk.models import ErrorEntry, LogEntry, LogLevel, UserAction

from config.config_model import LearningAnalyticsConfig

logger = logging.getLogger(__name__)


class BehavioralCollector:
    """Периодический опрос MCP, нормализация, дедупликация, запись в DB."""

    def __init__(self, mcp_client, db_factory, learning_analytics_config: LearningAnalyticsConfig):
        """Инициализация с MCP-клиентом, фабрикой сессий БД и конфигом."""
        self._mcp = mcp_client
        self._db_factory = db_factory
        self._cfg = learning_analytics_config
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_error_poll: datetime | None = None
        self._last_console_poll: datetime | None = None
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._component_types: dict[str, str] = {}
        self._session_id: str | None = None
        self._user_id: str | None = None
        self._lab_slug: str | None = None
        self._ctx = None
        self._expected_vpcs: dict[str, dict] = {}
        self._console_mismatch: dict[str, bool] = {}

    @property
    def is_running(self) -> bool:
        """Запущен ли цикл опроса."""
        return self._running

    async def start(self, session_id: str, user_id: str, lab_slug: str, ctx) -> None:
        """Запуск цикла опроса как asyncio.Task."""
        from labs.spec import expected_vpcs_config, load_lab_spec

        self._session_id = session_id
        self._user_id = user_id
        self._lab_slug = lab_slug
        self._ctx = ctx
        self._expected_vpcs = expected_vpcs_config(load_lab_spec(lab_slug))
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Остановка цикла."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    # Цикл опроса

    async def _poll_loop(self) -> None:
        """Бесконечный цикл: опрос → пауза → повтор."""
        while self._running:
            try:
                await self._poll_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.warning("Цикл опроса: ошибка", exc_info=True)
            await asyncio.sleep(self._cfg.poll_interval)

    async def _poll_cycle(self) -> None:
        """Один цикл: actions + logs + errors + консольная сверка → persist."""
        events: list[dict] = []
        events.extend(await self._fetch_actions())
        events.extend(await self._fetch_logs())
        events.extend(await self._fetch_errors())
        events.extend(await self._check_console_config())
        if events:
            await self._persist(events)

    async def _fetch_actions(self) -> list[dict]:
        """Получить UserAction из MCP, дедуплицировать, нормализовать."""
        result: list[dict] = []
        try:
            actions = await self._mcp.list_user_actions(
                self._ctx, limit=self._cfg.mcp_actions_limit
            )
            for a in actions:
                key = self._dedup_key(a.timestamp, a.action, a.component_id)
                if self._is_new(key):
                    await self._resolve_type(a.component_id)
                    result.append(self.normalize_user_action(
                        a, self._session_id, self._user_id, self._lab_slug,
                        self._component_types,
                    ))
        except Exception:
            logger.warning("Не удалось получить user actions", exc_info=True)
        return result

    async def _fetch_logs(self) -> list[dict]:
        """Получить LogEntry из MCP, дедуплицировать, нормализовать."""
        result: list[dict] = []
        try:
            logs = await self._mcp.get_logs(
                self._ctx, level=LogLevel.ALL, limit=self._cfg.mcp_logs_limit
            )
            for log in logs:
                key = self._dedup_key(log.timestamp, "log", log.source)
                if self._is_new(key):
                    result.append(self.normalize_log_entry(
                        log, self._session_id, self._user_id, self._lab_slug,
                    ))
        except Exception:
            logger.warning("Не удалось получить логи", exc_info=True)
        return result

    async def _fetch_errors(self) -> list[dict]:
        """Получить ErrorEntry из MCP (с since), нормализовать."""
        result: list[dict] = []
        try:
            errors = await self._mcp.list_errors(
                self._ctx, since=self._last_error_poll
            )
            self._last_error_poll = datetime.now(tz=timezone.utc)
            for err in errors:
                result.append(self.normalize_error_entry(
                    err, self._session_id, self._user_id, self._lab_slug,
                ))
        except Exception:
            logger.warning("Не удалось получить ошибки", exc_info=True)
        return result

    async def _check_console_config(self) -> list[dict]:
        """Сверить фактический IP запущенных VPCS-узлов с заданием лабы.

        GNS3 не публикует консольный ввод студента (ip/ping в VPCS) ни в actions,
        ни в логи — без этой сверки аналитика слепа к ошибкам конфигурации и
        проактивные подсказки никогда не срабатывают. Несовпадение оформляется
        как синтетическое error-событие со стабильным message: повторы одного и
        того же несовпадения наращивают error_repeat_count до порога интервенции.
        """
        if not self._expected_vpcs:
            return []
        now = datetime.now(tz=timezone.utc)
        if (
            self._last_console_poll is not None
            and (now - self._last_console_poll).total_seconds() < self._cfg.console_poll_interval
        ):
            return []
        self._last_console_poll = now

        from chat.tools import _run_vpcs_show_ip

        result: list[dict] = []
        try:
            components = await self._mcp.list_components(self._ctx)
        except Exception:
            logger.warning("Консольная сверка: не удалось получить компоненты", exc_info=True)
            return []

        nodes = [
            c for c in components
            if c.type == "vpcs" and c.status == "started" and c.name in self._expected_vpcs
        ]
        for node in nodes:
            try:
                res = await _run_vpcs_show_ip(node.name, self._ctx, self._mcp)
            except Exception:
                logger.warning("Консольная сверка: show ip упал для %s", node.name, exc_info=True)
                continue
            if "error" in res:
                continue
            actual_ip = res.get("ip")
            expected_ip = self._expected_vpcs[node.name].get("ip")
            # Ненастроенный узел — не ошибка: студент мог ещё не дойти до шага.
            # Свежезагруженный VPCS отдаёт 0.0.0.0/0 вместо пустого значения.
            if not actual_ip or not expected_ip or actual_ip.startswith("0.0.0.0"):
                continue
            if actual_ip == expected_ip:
                # Переход «ошибка → исправлено»: одно config_ok-событие, чтобы
                # FeatureExtractor оборвал серию повторов и подсказки прекратились.
                if self._console_mismatch.get(node.name):
                    self._console_mismatch[node.name] = False
                    result.append({
                        "id": str(uuid4()),
                        "session_id": self._session_id,
                        "user_id": self._user_id,
                        "lab_slug": self._lab_slug,
                        "timestamp": now,
                        "event_type": "action",
                        "component_id": node.id,
                        "component_type": "vpcs",
                        "action": "config_ok",
                        "raw_command": None,
                        "success": True,
                        "severity": None,
                        "message": f"{node.name}: IP {actual_ip} совпадает с заданием",
                        "extra_data": None,
                    })
                continue
            self._console_mismatch[node.name] = True
            result.append({
                "id": str(uuid4()),
                "session_id": self._session_id,
                "user_id": self._user_id,
                "lab_slug": self._lab_slug,
                "timestamp": now,
                "event_type": "error",
                "component_id": node.id,
                "component_type": "vpcs",
                "action": "config_mismatch",
                "raw_command": None,
                "success": False,
                "severity": "warning",
                "message": (
                    f"{node.name}: настроен IP {actual_ip}, "
                    f"по заданию требуется {expected_ip}"
                ),
                "extra_data": {"actual_ip": actual_ip, "expected_ip": expected_ip},
            })
        return result

    # Запись в БД

    async def _persist(self, events: list[dict]) -> None:
        """Пакетная запись событий в DB."""
        from models.behavioral_event import BehavioralEvent
        try:
            async with self._db_factory() as session:
                for evt in events:
                    session.add(BehavioralEvent(**evt))
                await session.commit()
        except Exception:
            logger.error("Не удалось сохранить события", exc_info=True)

    # Вспомогательные

    async def _resolve_type(self, component_id: str | None) -> str | None:
        """Lazy-определение component_type через MCP."""
        if not component_id or component_id in self._component_types:
            return self._component_types.get(component_id)
        try:
            detail = await self._mcp.get_component(self._ctx, component_id)
            self._component_types[component_id] = detail.type
            return detail.type
        except Exception:
            return None

    def _dedup_key(self, ts: datetime, action: str, cid: str | None) -> str:
        """Стабильный ключ дедупликации из timestamp, action и component_id.

        MD5 для краткости, не для безопасности.
        """
        raw = f"{ts.isoformat()}:{action}:{cid or ''}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _is_new(self, key: str) -> bool:
        """True если событие новое. Ограниченный OrderedDict."""
        if key in self._seen:
            return False
        self._seen[key] = None
        while len(self._seen) > self._cfg.dedup_max_size:
            self._seen.popitem(last=False)  # вытесняем самый старый
        return True

    # Нормализация MCP-моделей → event dict

    @staticmethod
    def normalize_user_action(
        action: UserAction, session_id: str, user_id: str, lab_slug: str,
        component_types: dict[str, str] | None = None,
    ) -> dict:
        """UserAction → dict для BehavioralEvent."""
        return {
            "id": str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "lab_slug": lab_slug,
            "timestamp": action.timestamp,
            "event_type": "action",
            "component_id": action.component_id,
            "component_type": (component_types or {}).get(action.component_id),
            "action": action.action,
            "raw_command": action.raw_command,
            "success": action.success,
            "severity": None,
            "message": None,
            "extra_data": None,
        }

    @staticmethod
    def normalize_log_entry(
        log: LogEntry, session_id: str, user_id: str, lab_slug: str,
    ) -> dict:
        """LogEntry → dict для BehavioralEvent."""
        return {
            "id": str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "lab_slug": lab_slug,
            "timestamp": log.timestamp,
            "event_type": "log",
            "component_id": log.source,
            "component_type": None,
            "action": f"log_{log.level.value}",
            "raw_command": None,
            "success": True,
            "severity": log.level.value,
            "message": log.message,
            "extra_data": None,
        }

    @staticmethod
    def normalize_error_entry(
        error: ErrorEntry, session_id: str, user_id: str, lab_slug: str,
    ) -> dict:
        """ErrorEntry → dict для BehavioralEvent."""
        return {
            "id": str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "lab_slug": lab_slug,
            "timestamp": error.timestamp,
            "event_type": "error",
            "component_id": error.component_id,
            "component_type": None,
            "action": "error",
            "raw_command": None,
            "success": False,
            "severity": error.level.value,
            "message": error.message,
            "extra_data": {"details": error.details} if error.details else None,
        }
