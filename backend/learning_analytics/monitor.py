"""SessionMonitor — замкнутый цикл LA: сбор → анализ → интервенция."""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

from agents.analytics.agent import AnalyticsAgent
from agents.orchestrator.models import InterventionInput
from config.config_model import LearningAnalyticsConfig
from learning_analytics.collector import BehavioralCollector
from learning_analytics.features import FeatureExtractor

logger = logging.getLogger(__name__)


class SessionMonitor:
    """Один на сессию. Управляет сбором событий, анализом и интервенциями."""

    def __init__(self, mcp_client, db_factory, orchestrator, learning_analytics_config: LearningAnalyticsConfig):
        """Инициализация с MCP-клиентом, DB-фабрикой, оркестратором и конфигом."""
        self._mcp = mcp_client
        self._db_factory = db_factory
        self._orchestrator = orchestrator
        self._learning_analytics_config = learning_analytics_config
        self._collector: BehavioralCollector | None = None
        self._feature_extractor = FeatureExtractor(learning_analytics_config)
        self._analysis_task: asyncio.Task | None = None
        self._running = False
        self._last_intervention_at: datetime | None = None
        self._session_id: str | None = None
        self._user_id: str | None = None
        self._lab_slug: str | None = None
        self._analytics_agent: AnalyticsAgent | None = None

    async def start_session(
        self, session_id: str, user_id: str, lab_slug: str,
        ctx, analytics_agent: AnalyticsAgent,
    ) -> None:
        """Запуск сбора и анализа для сессии."""
        self._session_id = session_id
        self._user_id = user_id
        self._lab_slug = lab_slug
        self._analytics_agent = analytics_agent
        self._running = True

        self._collector = BehavioralCollector(self._mcp, self._db_factory, self._learning_analytics_config)
        await self._collector.start(session_id, user_id, lab_slug, ctx)
        self._analysis_task = asyncio.create_task(self._analysis_loop())

    async def stop_session(self) -> None:
        """Остановка сбора и анализа."""
        self._running = False
        if self._collector:
            await self._collector.stop()
        if self._analysis_task and not self._analysis_task.done():
            self._analysis_task.cancel()
            try:
                await self._analysis_task
            except asyncio.CancelledError:
                pass

    # Цикл анализа

    async def _analysis_loop(self) -> None:
        """Периодический анализ с интервалом из конфига."""
        while self._running:
            await asyncio.sleep(self._learning_analytics_config.analysis_interval)
            if not self._running:
                break
            try:
                await self._run_analysis()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.warning("Цикл анализа: ошибка", exc_info=True)

    async def _run_analysis(self) -> None:
        """Один цикл: загрузить события → фичи → struggle-детекция → интервенция."""
        from sqlalchemy import select
        from models.behavioral_event import BehavioralEvent

        async with self._db_factory() as session:
            stmt = (
                select(BehavioralEvent)
                .where(BehavioralEvent.session_id == self._session_id)
                .order_by(BehavioralEvent.timestamp)
            )
            result = await session.execute(stmt)
            events = list(result.scalars().all())

        if not events:
            return

        features = self._feature_extractor.compute(self._session_id, events)
        analysis = self._analytics_agent.analyze_session(features, self._learning_analytics_config)

        if not analysis.struggle_detected or not self._should_trigger_intervention():
            return

        response = await self._orchestrator.intervene(InterventionInput(
            session_id=self._session_id,
            user_id=self._user_id,
            intervention_type=analysis.suggested_intervention.value,
            context={
                "struggle_type": analysis.struggle_type.value if analysis.struggle_type else None,
                "dominant_error": features.dominant_error,
                "lab_slug": self._lab_slug,
                "step_slug": "current",
                "attempts_count": features.error_repeat_count,
                "last_error": features.dominant_error,
            },
        ))
        self._last_intervention_at = datetime.now(tz=timezone.utc)
        await self._log_intervention(analysis, response)

        logger.info(
            "Интервенция: type=%s struggle=%s success=%s",
            analysis.suggested_intervention.value,
            analysis.struggle_type,
            response.success,
        )

    # Логирование интервенций

    async def _log_intervention(self, analysis, response) -> None:
        """Записать интервенцию как BehavioralEvent для анализа эффекта."""
        from models.behavioral_event import BehavioralEvent

        try:
            async with self._db_factory() as session:
                session.add(BehavioralEvent(
                    id=str(uuid4()),
                    session_id=self._session_id,
                    user_id=self._user_id,
                    lab_slug=self._lab_slug,
                    timestamp=datetime.now(tz=timezone.utc),
                    event_type="intervention",
                    action=f"intervene_{analysis.suggested_intervention.value}",
                    success=response.success,
                    message=str(response.data) if response.data else None,
                    extra_data={
                        "struggle_type": analysis.struggle_type.value if analysis.struggle_type else None,
                        "confidence": analysis.confidence,
                        "agent_used": response.agent_used,
                    },
                ))
                await session.commit()
        except Exception:
            logger.error("Не удалось записать интервенцию", exc_info=True)

    # Контроль частоты интервенций

    def _should_intervene(self) -> bool:
        """Cooldown прошёл или первая интервенция."""
        if self._last_intervention_at is None:
            return True
        elapsed = (datetime.now(tz=timezone.utc) - self._last_intervention_at).total_seconds()
        return elapsed >= self._learning_analytics_config.cooldown_period

    def _should_trigger_intervention(self) -> bool:
        """Интервенции включены и cooldown прошёл."""
        return self._learning_analytics_config.enabled and self._should_intervene()
