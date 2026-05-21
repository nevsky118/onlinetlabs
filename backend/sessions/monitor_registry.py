"""Реестр SessionMonitor по session_id."""

import logging

from agents.analytics.agent import AnalyticsAgent
from config.config_model import ConfigModel
from learning_analytics.monitor import SessionMonitor

logger = logging.getLogger(__name__)


class SessionMonitorRegistry:
    """Реестр активных SessionMonitor по идентификатору сессии."""

    def __init__(self, config: ConfigModel, mcp_client, db_factory, orchestrator, gateway):
        """Хранит зависимости для создания мониторов и словарь запущенных мониторов."""
        self._config = config
        self._mcp_client = mcp_client
        self._db_factory = db_factory
        self._orchestrator = orchestrator
        self._gateway = gateway
        self._monitors: dict[str, SessionMonitor] = {}
        self._analytics_agent = AnalyticsAgent(config, None)

    async def start(self, session_id: str, user_id: str, lab_slug: str, ctx) -> None:
        """Создаёт и запускает монитор сессии. Повторный вызов для той же сессии ничего не делает."""
        if session_id in self._monitors:
            return
        monitor = SessionMonitor(
            mcp_client=self._mcp_client,
            db_factory=self._db_factory,
            orchestrator=self._orchestrator,
            learning_analytics_config=self._config.learning_analytics,
            gateway=self._gateway,
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

    async def stop_all(self) -> None:
        """Останавливает все запущенные мониторы сессий."""
        for sid in list(self._monitors):
            await self.stop(sid)
