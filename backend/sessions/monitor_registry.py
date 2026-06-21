"""Реестр SessionMonitor по session_id."""

import logging

from agents.analytics.agent import AnalyticsAgent
from config.config_model import ConfigModel
from experiment.arm_resolver import effective_arm
from learning_analytics.monitor import SessionMonitor

logger = logging.getLogger(__name__)


class SessionMonitorRegistry:
    """Реестр активных SessionMonitor по идентификатору сессии."""

    def __init__(self, config: ConfigModel, mcp_client, db_factory, orchestrator, gateway, activity_log=None, gns3_client=None):
        """Хранит зависимости для создания мониторов и словарь запущенных мониторов."""
        self._config = config
        self._mcp_client = mcp_client
        self._db_factory = db_factory
        self._orchestrator = orchestrator
        self._gateway = gateway
        self._activity_log = activity_log
        self._gns3_client = gns3_client
        self._monitors: dict[str, SessionMonitor] = {}
        # observer живёт дольше монитора — реестр владеет им
        self._observers: dict[str, object] = {}
        self._analytics_agent = AnalyticsAgent(config, None)

    async def start(self, session_id: str, user_id: str, lab_slug: str, ctx) -> None:
        """Создаёт и запускает монитор сессии. Повторный вызов для той же сессии ничего не делает."""
        if session_id in self._monitors:
            return

        # Пытаемся поднять LabProgressObserver если есть GNS3-сессия
        observer = None
        if self._gns3_client is not None:
            try:
                from db.session import async_session
                from models.session import LearningSession
                from learning_analytics.progress_observer import LabProgressObserver

                async with async_session() as db:
                    ls = await db.get(LearningSession, session_id)
                gns3_sid = (ls.meta or {}).get("gns3_service_session_id") if ls else None
                if gns3_sid:
                    observer = LabProgressObserver(
                        self._gns3_client, self._db_factory, self._config, self._config.learning_analytics
                    )
                    await observer.start(session_id, user_id, lab_slug, gns3_sid)
                    self._observers[session_id] = observer
                    logger.info("LabProgressObserver запущен для %s (gns3_sid=%s)", session_id, gns3_sid)
            except Exception:
                logger.warning("Не удалось запустить LabProgressObserver для %s", session_id, exc_info=True)
                observer = None

        async with self._db_factory() as db:
            arm = await effective_arm(db, user_id, lab_slug)

        monitor = SessionMonitor(
            mcp_client=self._mcp_client,
            db_factory=self._db_factory,
            orchestrator=self._orchestrator,
            learning_analytics_config=self._config.learning_analytics,
            gateway=self._gateway,
            activity_log=self._activity_log,
            observer=observer,
            control_arm=arm,
        )
        self._monitors[session_id] = monitor
        await monitor.start_session(session_id, user_id, lab_slug, ctx, self._analytics_agent)
        logger.info("SessionMonitor запущен для %s", session_id)

    async def stop(self, session_id: str) -> None:
        """Останавливает монитор сессии и убирает его из реестра."""
        monitor = self._monitors.pop(session_id, None)
        if monitor:
            await monitor.stop_session()
            logger.info("SessionMonitor остановлен для %s", session_id)
        # Останавливаем observer после монитора
        observer = self._observers.pop(session_id, None)
        if observer:
            try:
                await observer.stop()
            except Exception:
                logger.warning("Ошибка при остановке LabProgressObserver для %s", session_id, exc_info=True)

    async def stop_all(self) -> None:
        """Останавливает все запущенные мониторы сессий."""
        for sid in list(self._monitors):
            await self.stop(sid)
