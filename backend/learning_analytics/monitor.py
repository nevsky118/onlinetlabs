"""SessionMonitor — замкнутый цикл аналитики обучения: сбор → анализ → интервенция."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from agents.analytics.agent import AnalyticsAgent
from agents.analytics.models import AnalyticsResult, SessionFeatures
from agents.orchestrator.models import InterventionInput
from config.config_model import LearningAnalyticsConfig
from learning_analytics.collector import BehavioralCollector
from learning_analytics.context import MCPContextBuilder
from learning_analytics.features import FeatureExtractor
from learning_analytics.process_state import DwellTracker
from observability.models import (
    ActivitySource,
    event_agent_invoked,
    event_cooldown_skip,
    event_dispatched,
    event_error,
    event_hint_generated,
    event_struggle_detected,
)

logger = logging.getLogger(__name__)

# Формулировка «вопроса студента» для tutor-интервенций: TutorInput требует
# question, но проактивная интервенция инициируется без вопроса — формулируем
# его от лица студента по типу затруднения.
_STRUGGLE_QUESTIONS = {
    "stuck_on_step": "Я застрял на текущем шаге и не понимаю, как двигаться дальше. Подскажи направление.",
    "repeating_errors": "Я повторяю одну и ту же ошибку. Помоги понять, что я делаю не так.",
    "idle": "Я давно не предпринимаю действий и, похоже, застрял. С чего продолжить?",
    "trial_and_error": "Я перебираю действия наугад и делаю много ошибок. Помоги разобраться, что не так.",
}


@dataclass
class PendingIntervention:
    """Решение об интервенции, готовое к отправке и записи."""

    analysis: AnalyticsResult
    features: SessionFeatures
    payload: InterventionInput
    response: Any | None = None


class SessionMonitor:
    """Один на сессию. Управляет сбором событий, анализом и интервенциями."""

    def __init__(
        self,
        mcp_client,
        db_factory,
        orchestrator,
        learning_analytics_config: LearningAnalyticsConfig,
        gateway=None,
        intervention_router=None,
        activity_log=None,
        observer=None,
    ):
        """Инициализация с MCP-клиентом, фабрикой БД, оркестратором и конфигом."""
        self._mcp = mcp_client
        self._db_factory = db_factory
        self._orchestrator = orchestrator
        self._intervention_router = intervention_router
        self._learning_analytics_config = learning_analytics_config
        self._gateway = gateway
        self._activity = activity_log
        self._observer = observer
        self._collector: BehavioralCollector | None = None
        self._feature_extractor = FeatureExtractor(learning_analytics_config)
        self._context_builder = MCPContextBuilder(mcp_client)
        self._analysis_task: asyncio.Task | None = None
        self._running = False
        self._last_intervention_at: datetime | None = None
        self._last_event_at: datetime | None = None
        self._session_id: str | None = None
        self._user_id: str | None = None
        self._lab_slug: str | None = None
        self._analytics_agent: AnalyticsAgent | None = None
        self._session_model_id: str | None = None
        self._dwell = DwellTracker()

    async def start_session(
        self,
        session_id: str,
        user_id: str,
        lab_slug: str,
        ctx,
        analytics_agent: AnalyticsAgent,
    ) -> None:
        """Запуск сбора и анализа для сессии."""
        from sqlalchemy import func, select
        from models.behavioral_event import BehavioralEvent

        self._session_id = session_id
        self._user_id = user_id
        self._lab_slug = lab_slug
        self._ctx = ctx
        self._analytics_agent = analytics_agent
        self._running = True

        async with self._db_factory() as session:
            stmt = select(func.max(BehavioralEvent.timestamp)).where(
                BehavioralEvent.session_id == session_id
            )
            result = await session.execute(stmt)
            self._last_event_at = result.scalar_one_or_none()

            # Загружаем model_id сессии для проброса в context интервенции.
            from models.session import LearningSession
            ls = await session.get(LearningSession, session_id)
            self._session_model_id = ls.model_id if ls else None

        self._collector = BehavioralCollector(
            self._mcp, self._db_factory, self._learning_analytics_config
        )
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
        """Оркестратор цикла: загрузка событий, решение, отправка, запись."""
        async with self._db_factory() as db:
            events = await self._load_new_events(db)
        if not events:
            return

        self._last_event_at = events[-1].timestamp
        features = self._feature_extractor.compute(self._session_id, events)
        analysis = self._analytics_agent.analyze_session(
            features, self._learning_analytics_config
        )
        regime, dwell = await self._log_process_state(analysis, datetime.now(tz=timezone.utc))

        if not self._dwell_ready(regime.value, dwell):
            return
        pending = await self._decide_intervention(analysis, features)
        if pending is None:
            return

        await self._dispatch_intervention(pending)
        async with self._db_factory() as db:
            await self._persist_intervention(db, pending)

        logger.info(
            "Интервенция: type=%s struggle=%s success=%s",
            pending.analysis.suggested_intervention.value,
            pending.analysis.struggle_type,
            pending.response.success if pending.response else False,
        )

    async def _load_new_events(self, db) -> list:
        """Загрузить новые поведенческие события по курсору.

        Собственные интервенции исключаются: иначе каждая записанная
        интервенция выглядит как «новое событие», анализ перезапускается
        и порождает следующую интервенцию — самоподдерживающийся цикл.
        """
        from sqlalchemy import func, select
        from models.behavioral_event import BehavioralEvent

        latest_stmt = select(func.max(BehavioralEvent.timestamp)).where(
            BehavioralEvent.session_id == self._session_id,
            BehavioralEvent.event_type != "intervention",
        )
        latest = (await db.execute(latest_stmt)).scalar_one_or_none()
        if latest is None:
            return []
        if self._last_event_at is not None and latest <= self._last_event_at:
            return []

        stmt = (
            select(BehavioralEvent)
            .where(
                BehavioralEvent.session_id == self._session_id,
                BehavioralEvent.event_type != "intervention",
            )
            .order_by(BehavioralEvent.timestamp.desc())
            .limit(500)
        )
        result = await db.execute(stmt)
        return list(reversed(result.scalars().all()))

    async def _log_process_state(self, analysis, now):
        """Записать выборку состояния процесса (режим + dwell) — каждый цикл."""
        from models.process_state_sample import ProcessStateSample
        from learning_analytics.process_state import analysis_to_regime
        regime = analysis_to_regime(analysis)
        dwell = self._dwell.observe(regime, now)
        async with self._db_factory() as db:
            db.add(ProcessStateSample(
                session_id=self._session_id, user_id=self._user_id,
                lab_slug=self._lab_slug, ts=now,
                regime=regime.value, dwell_seconds=dwell,
            ))
            await db.commit()
        return regime, dwell

    async def _decide_intervention(
        self, analysis: AnalyticsResult, features: SessionFeatures
    ) -> PendingIntervention | None:
        """Анализ фичей и сборка решения об интервенции, или None."""
        if not analysis.struggle_detected:
            return None
        # Затруднение обнаружено — эмитим событие
        self._emit(event_struggle_detected(
            self._session_id, self._user_id,
            struggle_type=analysis.struggle_type.value if analysis.struggle_type else "unknown",
            confidence=analysis.confidence,
            crossed=[],
        ))
        if not self._should_trigger_intervention():
            # Cooldown ещё не прошёл — пропускаем интервенцию
            elapsed = (
                (datetime.now(tz=timezone.utc) - self._last_intervention_at).total_seconds()
                if self._last_intervention_at else 0
            )
            remaining = max(0.0, self._learning_analytics_config.cooldown_period - elapsed)
            self._emit(event_cooldown_skip(
                self._session_id, self._user_id,
                reason="cooldown",
                remaining_seconds=int(remaining),
            ))
            return None

        context = await self._context_builder.build(
            self._ctx,
            features,
            analysis.struggle_type.value if analysis.struggle_type else None,
            features.dominant_error,
        )
        struggle_value = analysis.struggle_type.value if analysis.struggle_type else None
        question = _STRUGGLE_QUESTIONS.get(
            struggle_value, "Похоже, я застрял. Подскажи, что проверить."
        )
        if features.dominant_error:
            question += f" Последняя ошибка: {features.dominant_error}"
        # Берём снапшот прогресса из observer'а если он подключён
        st = self._observer.current_state() if self._observer else None
        payload = InterventionInput(
            session_id=self._session_id,
            user_id=self._user_id,
            intervention_type=analysis.suggested_intervention.value,
            context={
                "struggle_type": struggle_value,
                "dominant_error": features.dominant_error,
                "lab_slug": self._lab_slug,
                "step_slug": (st.current_step_id if st and st.current_step_id else "current"),
                "step_title": (st.current_step_title if st else ""),
                "failing_check": (st.failing_checks[0] if st and st.failing_checks else None),
                "attempts_count": features.error_repeat_count,
                "last_error": features.dominant_error,
                "question": question,
                "agent_context": context.model_dump(),
                "session_model_id": self._session_model_id,
            },
        )
        return PendingIntervention(analysis=analysis, features=features, payload=payload)

    async def _dispatch_intervention(self, pending: PendingIntervention) -> None:
        """Прогнать интервенцию через оркестратор и отправить клиенту через шлюз."""
        if self._intervention_router:
            response = await self._intervention_router.intervene(pending.payload)
        else:
            response = await self._orchestrator.intervene(pending.payload)
        pending.response = response
        self._last_intervention_at = datetime.now(tz=timezone.utc)

        # Эмит после получения ответа агента
        self._emit(event_agent_invoked(
            self._session_id, self._user_id,
            agent_name=response.agent_used or "orchestrator",
            model_id=response.metadata.get("model", "unknown"),
            parameters_preview={"intervention_type": pending.payload.intervention_type},
        ))
        if response.success:
            self._emit(event_hint_generated(
                self._session_id, self._user_id,
                level=response.data.get("hint_level", 1) if response.data else 1,
                hint_type=pending.payload.intervention_type,
                model_used=response.metadata.get("model", "unknown"),
            ))
            self._emit(event_dispatched(
                self._session_id, self._user_id,
                intervention_type=pending.payload.intervention_type,
                target_agent=response.agent_used or "orchestrator",
                status="success",
            ))
        else:
            self._emit(event_error(
                self._session_id, self._user_id,
                source=ActivitySource.INTERVENTION,
                error=response.error or "unknown error",
                agent=response.agent_used,
            ))

        if response.success and self._gateway:
            analysis = pending.analysis
            await self._gateway.send_intervention(
                self._session_id,
                {
                    "intervention_type": analysis.suggested_intervention.value,
                    "content": response.data.get("hint")
                    or response.data.get("answer", ""),
                    "hint_level": response.data.get("hint_level"),
                    "struggle_type": analysis.struggle_type.value
                    if analysis.struggle_type
                    else None,
                    "dismissible": True,
                },
            )

    async def _persist_intervention(self, db, pending: PendingIntervention) -> None:
        """Записать интервенцию в поведенческие события для последующего анализа."""
        if pending.response is None:
            return
        await self._log_intervention_in(db, pending.analysis, pending.response)

    # Логирование интервенций

    async def _log_intervention_in(self, db, analysis, response) -> None:
        """Записать интервенцию как поведенческое событие для анализа эффекта."""
        from models.behavioral_event import BehavioralEvent

        try:
            db.add(
                BehavioralEvent(
                    id=str(uuid4()),
                    session_id=self._session_id,
                    user_id=self._user_id,
                    lab_slug=self._lab_slug,
                    timestamp=datetime.now(tz=timezone.utc),
                    event_type="intervention",
                    action=f"intervene_{analysis.suggested_intervention.value}",
                    success=response.success,
                    message=str(response.data) if response.data else response.error,
                    extra_data={
                        "struggle_type": analysis.struggle_type.value
                        if analysis.struggle_type
                        else None,
                        "confidence": analysis.confidence,
                        "agent_used": response.agent_used,
                        "agent_backend": response.agent_backend,
                        "experiment_group": response.metadata.get(
                            "experiment_group"
                        ),
                        "latency_ms": response.latency_ms,
                        "error_code": response.metadata.get("error_code"),
                        "model": response.metadata.get("model"),
                        "provider": response.metadata.get("provider"),
                    },
                )
            )
            await db.commit()
        except Exception:
            logger.error("Не удалось записать интервенцию", exc_info=True)

    # Вспомогательный emit — никогда не пробрасывает исключение

    def _emit(self, event) -> None:
        if self._activity:
            self._activity.emit(event)

    # Контроль частоты интервенций

    def _dwell_ready(self, regime_value: str, dwell: float) -> bool:
        """Закон управления: плохой режим и время пребывания >= порога T_k."""
        from learning_analytics.process_state import ProcessRegime, is_bad
        regime = ProcessRegime(regime_value)
        if not is_bad(regime):
            return False
        t_k = self._learning_analytics_config.dwell_thresholds.get(regime_value, 0.0)
        return dwell >= t_k

    def _should_trigger_intervention(self) -> bool:
        """Интервенции включены и период охлаждения прошёл."""
        if not self._learning_analytics_config.enabled:
            return False
        if self._last_intervention_at is None:
            return True
        elapsed = (
            datetime.now(tz=timezone.utc) - self._last_intervention_at
        ).total_seconds()
        return elapsed >= self._learning_analytics_config.cooldown_period
