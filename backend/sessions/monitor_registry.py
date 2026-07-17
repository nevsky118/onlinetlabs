"""Registry of SessionMonitor instances by session_id."""

import logging

from config.config_model import ConfigModel
from control_interface.interface import ControlInterface
from experiment.assignment import effective_arm
from learning_analytics.monitor import SessionMonitor

logger = logging.getLogger(__name__)


class SessionMonitorRegistry:
    """Registry of active SessionMonitor instances by session id."""

    def __init__(
        self,
        config: ConfigModel,
        mcp_client,
        db_factory,
        orchestrator,
        gateway,
        activity_log=None,
        gns3_client=None,
    ):
        """Stores dependencies for creating monitors and a dict of running monitors."""
        self._config = config
        self._mcp_client = mcp_client
        self._db_factory = db_factory
        self._orchestrator = orchestrator
        self._gateway = gateway
        self._activity_log = activity_log
        self._gns3_client = gns3_client
        self._monitors: dict[str, SessionMonitor] = {}
        # the observer outlives the monitor, so the registry owns it directly
        self._observers: dict[str, object] = {}

    async def start(self, session_id: str, user_id: str, lab_slug: str, ctx) -> None:
        """Creates and starts a session monitor. A repeat call for the same session is a no-op."""
        if session_id in self._monitors:
            return

        # Try to bring up LabProgressObserver if a GNS3 session exists
        observer = None
        if self._gns3_client is not None:
            try:
                from db.session import async_session
                from learning_analytics.progress_observer import LabProgressObserver
                from models.session import LearningSession

                async with async_session() as db:
                    ls = await db.get(LearningSession, session_id)
                gns3_sid = (ls.meta or {}).get("gns3_service_session_id") if ls else None
                if gns3_sid:
                    observer = LabProgressObserver(
                        self._gns3_client,
                        self._db_factory,
                        self._config,
                        self._config.learning_analytics,
                    )
                    await observer.start(session_id, user_id, lab_slug, gns3_sid)
                    self._observers[session_id] = observer
                    logger.info(
                        "LabProgressObserver запущен для %s (gns3_sid=%s)", session_id, gns3_sid
                    )
            except Exception:
                logger.warning(
                    "Не удалось запустить LabProgressObserver для %s", session_id, exc_info=True
                )
                observer = None

        async with self._db_factory() as db:
            arm = await effective_arm(db, user_id, lab_slug)

        # control-loop seam; one instance per session, reusing the same dependencies
        control_interface = ControlInterface(
            self._mcp_client, self._db_factory, self._config.learning_analytics
        )
        monitor = SessionMonitor(
            mcp_client=self._mcp_client,
            db_factory=self._db_factory,
            orchestrator=self._orchestrator,
            learning_analytics_config=self._config.learning_analytics,
            gateway=self._gateway,
            activity_log=self._activity_log,
            observer=observer,
            control_arm=arm,
            control_interface=control_interface,
        )
        self._monitors[session_id] = monitor
        await monitor.start_session(session_id, user_id, lab_slug, ctx)
        logger.info("SessionMonitor запущен для %s", session_id)

    async def stop(self, session_id: str) -> None:
        """Stops the session monitor and removes it from the registry."""
        monitor = self._monitors.pop(session_id, None)
        if monitor:
            await monitor.stop_session()
            logger.info("SessionMonitor остановлен для %s", session_id)
        # Stop the observer after the monitor
        observer = self._observers.pop(session_id, None)
        if observer:
            try:
                await observer.stop()
            except Exception:
                logger.warning(
                    "Ошибка при остановке LabProgressObserver для %s", session_id, exc_info=True
                )

    async def stop_all(self) -> None:
        """Stops all running session monitors."""
        for sid in list(self._monitors):
            await self.stop(sid)
