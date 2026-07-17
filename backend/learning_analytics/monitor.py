"""SessionMonitor runs the closed learning-analytics loop: collect, analyze, intervene."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from agents.analytics.agent import identify_regime
from agents.analytics.models import AnalyticsResult, SessionFeatures
from agents.orchestrator.models import InterventionInput
from config.config_model import LearningAnalyticsConfig
from control_interface.audit import record as audit_record
from experiment.assignment import ControlArm
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

# TutorInput requires a question, but proactive interventions don't have one,
# so we phrase it on the student's behalf based on the struggle type.
_STRUGGLE_QUESTIONS = {
    "stuck_on_step": "Я застрял на текущем шаге и не понимаю, как двигаться дальше. Подскажи направление.",
    "repeating_errors": "Я повторяю одну и ту же ошибку. Помоги понять, что я делаю не так.",
    "idle": "Я давно не предпринимаю действий и, похоже, застрял. С чего продолжить?",
    "trial_and_error": "Я перебираю действия наугад и делаю много ошибок. Помоги разобраться, что не так.",
}


@dataclass
class PendingIntervention:
    """Intervention decision ready for dispatch and persistence."""

    analysis: AnalyticsResult
    features: SessionFeatures
    payload: InterventionInput
    response: Any | None = None


class SessionMonitor:
    """One per session. Manages event collection, analysis, and interventions."""

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
        control_arm: ControlArm = ControlArm.CLOSED,
        control_interface=None,
    ):
        """Initialize with an MCP client, DB factory, orchestrator, and config."""
        self._mcp = mcp_client
        self._db_factory = db_factory
        self._orchestrator = orchestrator
        self._intervention_router = intervention_router
        self._learning_analytics_config = learning_analytics_config
        self._gateway = gateway
        self._activity = activity_log
        self._observer = observer
        self._control_arm = control_arm
        self._control_interface = control_interface  # seam P1 (Task 7)
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
        self._session_model_id: str | None = None
        self._dwell = DwellTracker()
        self._escalated_in_spell: bool = False
        # MRT: state of the current bad-spell (jittered T_k + decision point ids)
        self._spell_id: str | None = None
        self._spell_t_k: float | None = None
        self._open_decision_ids: list[str] = []

    async def start_session(
        self,
        session_id: str,
        user_id: str,
        lab_slug: str,
        ctx,
    ) -> None:
        """Start collection and analysis for the session."""
        from sqlalchemy import func, select

        from models.behavioral_event import BehavioralEvent

        self._session_id = session_id
        self._user_id = user_id
        self._lab_slug = lab_slug
        self._ctx = ctx
        self._running = True

        async with self._db_factory() as session:
            stmt = select(func.max(BehavioralEvent.timestamp)).where(
                BehavioralEvent.session_id == session_id
            )
            result = await session.execute(stmt)
            self._last_event_at = result.scalar_one_or_none()

            # Load the session's model_id to pass through into the intervention context.
            from models.session import LearningSession

            ls = await session.get(LearningSession, session_id)
            self._session_model_id = ls.model_id if ls else None

        self._collector = BehavioralCollector(
            self._mcp,
            self._db_factory,
            self._learning_analytics_config,
            control_interface=self._control_interface,
        )
        await self._collector.start(session_id, user_id, lab_slug, ctx)
        self._analysis_task = asyncio.create_task(self._analysis_loop())

    async def stop_session(self) -> None:
        """Stop collection and analysis."""
        self._running = False
        if self._collector:
            await self._collector.stop()
        if self._analysis_task and not self._analysis_task.done():
            self._analysis_task.cancel()
            try:
                await self._analysis_task
            except asyncio.CancelledError:
                pass

    # Analysis loop

    async def _analysis_loop(self) -> None:
        """Periodic analysis at the interval from config."""
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
        """Cycle orchestrator: load events, decide, dispatch, persist."""
        async with self._db_factory() as db:
            events = await self._load_new_events(db)
        if not events:
            return

        self._last_event_at = events[-1].timestamp
        import time

        _t0 = time.perf_counter()
        features = self._feature_extractor.compute(self._session_id, events)
        analysis = identify_regime(features, self._learning_analytics_config)
        regime, dwell = await self._log_process_state(analysis, datetime.now(tz=UTC))
        if self._learning_analytics_config.latency_capture_enabled:
            await self._record_latency("analysis", (time.perf_counter() - _t0) * 1000.0)

        # Objective escalation is arm-neutral, runs before the intervention branch
        from learning_analytics.process_state import is_bad

        if is_bad(regime):
            if self._is_escalation(dwell) and not self._escalated_in_spell:
                self._escalated_in_spell = True
                from escalation.service import record_escalation

                try:
                    async with self._db_factory() as db:
                        await record_escalation(
                            db,
                            self._session_id,
                            self._user_id,
                            self._lab_slug,
                            source="objective",
                        )
                except Exception:
                    logger.warning("Не удалось записать объективную эскалацию", exc_info=True)
        else:
            self._escalated_in_spell = False

        if self._learning_analytics_config.mrt_enabled:
            await self._mrt_step(
                analysis,
                features,
                regime,
                dwell,
                datetime.now(tz=UTC),
            )
            return

        if not self._dwell_ready(regime.value, dwell):
            return

        # Arm A (open): same cooldown gates as the closed arm
        if self._control_arm == ControlArm.OPEN:
            if not self._should_trigger_intervention():
                return
            await self._log_would_intervene(analysis)
            self._last_intervention_at = datetime.now(tz=UTC)
            return

        pending = await self._decide_intervention(analysis, features)
        if pending is None:
            return

        await self._dispatch_intervention(pending)
        async with self._db_factory() as db:
            await self._persist_intervention(db, pending)

        # act-audit: best-effort, doesn't break dispatch on error
        try:
            async with self._db_factory() as db:
                await audit_record(
                    db,
                    user_id=self._user_id,
                    session_id=self._session_id,
                    tool="intervention",
                    kind="act",
                    success=pending.response.success if pending.response else False,
                    lab_slug=self._lab_slug,
                )
        except Exception:
            logger.warning("Не удалось записать act-аудит интервенции", exc_info=True)

        logger.info(
            "Интервенция: type=%s struggle=%s success=%s",
            pending.analysis.suggested_intervention.value,
            pending.analysis.struggle_type,
            pending.response.success if pending.response else False,
        )

    async def _load_new_events(self, db) -> list:
        """Load new behavioral events by cursor.

        Our own interventions are excluded, otherwise every recorded intervention looks
        like a "new event", analysis restarts, and spawns the next one: a self-sustaining loop.
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
        """Record a process state sample (regime and dwell) each cycle."""
        from learning_analytics.process_state import analysis_to_regime
        from models.process_state_sample import ProcessStateSample

        regime = analysis_to_regime(analysis)
        dwell = self._dwell.observe(regime, now)
        async with self._db_factory() as db:
            db.add(
                ProcessStateSample(
                    session_id=self._session_id,
                    user_id=self._user_id,
                    lab_slug=self._lab_slug,
                    ts=now,
                    regime=regime.value,
                    dwell_seconds=dwell,
                )
            )
            await db.commit()
        return regime, dwell

    async def _decide_intervention(
        self, analysis: AnalyticsResult, features: SessionFeatures
    ) -> PendingIntervention | None:
        """Analyze features and assemble an intervention decision, or None."""
        if not analysis.struggle_detected:
            return None
        # struggle detected, emit event
        self._emit(
            event_struggle_detected(
                self._session_id,
                self._user_id,
                struggle_type=analysis.struggle_type.value if analysis.struggle_type else "unknown",
                confidence=analysis.confidence,
                crossed=[],
            )
        )
        if not self._should_trigger_intervention():
            # cooldown hasn't elapsed yet, skip the intervention
            elapsed = (
                (datetime.now(tz=UTC) - self._last_intervention_at).total_seconds()
                if self._last_intervention_at
                else 0
            )
            remaining = max(0.0, self._learning_analytics_config.cooldown_period - elapsed)
            self._emit(
                event_cooldown_skip(
                    self._session_id,
                    self._user_id,
                    reason="cooldown",
                    remaining_seconds=int(remaining),
                )
            )
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
        # Take the progress snapshot from the observer if one is attached
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
        """Run the intervention through the orchestrator and send it to the client via the gateway."""
        if self._intervention_router:
            response = await self._intervention_router.intervene(pending.payload)
        else:
            response = await self._orchestrator.intervene(pending.payload)
        pending.response = response
        self._last_intervention_at = datetime.now(tz=UTC)

        # Emit after receiving the agent's response
        self._emit(
            event_agent_invoked(
                self._session_id,
                self._user_id,
                agent_name=response.agent_used or "orchestrator",
                model_id=response.metadata.get("model", "unknown"),
                parameters_preview={"intervention_type": pending.payload.intervention_type},
            )
        )
        if response.success:
            self._emit(
                event_hint_generated(
                    self._session_id,
                    self._user_id,
                    level=response.data.get("hint_level", 1) if response.data else 1,
                    hint_type=pending.payload.intervention_type,
                    model_used=response.metadata.get("model", "unknown"),
                )
            )
            self._emit(
                event_dispatched(
                    self._session_id,
                    self._user_id,
                    intervention_type=pending.payload.intervention_type,
                    target_agent=response.agent_used or "orchestrator",
                    status="success",
                )
            )
        else:
            self._emit(
                event_error(
                    self._session_id,
                    self._user_id,
                    source=ActivitySource.INTERVENTION,
                    error=response.error or "unknown error",
                    agent=response.agent_used,
                )
            )

        if response.success and self._gateway:
            analysis = pending.analysis
            await self._gateway.send_intervention(
                self._session_id,
                {
                    "intervention_type": analysis.suggested_intervention.value,
                    "content": response.data.get("hint") or response.data.get("answer", ""),
                    "hint_level": response.data.get("hint_level"),
                    "struggle_type": analysis.struggle_type.value
                    if analysis.struggle_type
                    else None,
                    "dismissible": True,
                },
            )

        await self._maybe_grounding_ablation(pending)

    async def _maybe_grounding_ablation(self, pending: PendingIntervention) -> None:
        """Gated: generate an ungrounded variant (without MCP context) and record the pair.

        The grounded text comes from the dispatch already made; ungrounded is one extra
        call with agent_context cleared. Expensive → flag-gated, best-effort, after delivery.
        """
        if not self._learning_analytics_config.grounding_ablation_enabled:
            return
        if not (pending.response and pending.response.success):
            return
        from evaluation.grounding import record_grounding_comparison

        try:
            grounded_text = (pending.response.data or {}).get("hint", "")
            ungrounded_payload = pending.payload.model_copy(deep=True)
            ctx = dict(ungrounded_payload.context or {})
            ctx["agent_context"] = {}
            ungrounded_payload.context = ctx
            orch = self._intervention_router or self._orchestrator
            ungrounded_resp = await orch.intervene(ungrounded_payload)
            ungrounded_text = (ungrounded_resp.data or {}).get("hint", "")
            async with self._db_factory() as db:
                await record_grounding_comparison(
                    db, self._session_id, grounded_text, ungrounded_text
                )
        except Exception:
            logger.warning("Grounding-ablation не удалось", exc_info=True)

    async def _persist_intervention(self, db, pending: PendingIntervention) -> None:
        """Record the intervention as a behavioral event for later analysis."""
        if pending.response is None:
            return
        await self._log_intervention_in(db, pending.analysis, pending.response)

    # Intervention logging

    async def _log_would_intervene(self, analysis: AnalyticsResult) -> None:
        """Arm A: record would_intervene instead of a real intervention."""
        from models.behavioral_event import BehavioralEvent

        action = (
            analysis.suggested_intervention.value if analysis.suggested_intervention else "none"
        )
        try:
            async with self._db_factory() as db:
                db.add(
                    BehavioralEvent(
                        id=str(uuid4()),
                        session_id=self._session_id,
                        user_id=self._user_id,
                        lab_slug=self._lab_slug,
                        timestamp=datetime.now(tz=UTC),
                        event_type="would_intervene",
                        action=action,
                        success=False,
                        extra_data={
                            "struggle_type": analysis.struggle_type.value
                            if analysis.struggle_type
                            else None,
                            "confidence": analysis.confidence,
                            "control_arm": ControlArm.OPEN.value,
                        },
                    )
                )
                await db.commit()
            logger.debug("Arm A: would_intervene action=%s", action)
        except Exception:
            logger.warning("Не удалось записать would_intervene", exc_info=True)

    async def _log_intervention_in(self, db, analysis, response) -> None:
        """Record the intervention as a behavioral event for effect analysis."""
        from models.behavioral_event import BehavioralEvent

        try:
            db.add(
                BehavioralEvent(
                    id=str(uuid4()),
                    session_id=self._session_id,
                    user_id=self._user_id,
                    lab_slug=self._lab_slug,
                    timestamp=datetime.now(tz=UTC),
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
                        "experiment_group": response.metadata.get("experiment_group"),
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

    # Helper emit, never propagates an exception

    def _emit(self, event) -> None:
        if self._activity:
            self._activity.emit(event)

    # Intervention frequency control

    def _dwell_ready(self, regime_value: str, dwell: float) -> bool:
        """Control law: bad regime and dwell time >= threshold T_k."""
        from learning_analytics.process_state import ProcessRegime, is_bad

        regime = ProcessRegime(regime_value)
        if not is_bad(regime):
            return False
        t_k = self._learning_analytics_config.dwell_thresholds.get(regime_value, 0.0)
        return dwell >= t_k

    def _is_escalation(self, dwell: float) -> bool:
        """Objective escalation: bad regime longer than the threshold."""
        return dwell >= self._learning_analytics_config.escalation_max_dwell

    def _should_trigger_intervention(self) -> bool:
        """Interventions are enabled and the cooldown period has elapsed."""
        if not self._learning_analytics_config.enabled:
            return False
        if self._last_intervention_at is None:
            return True
        elapsed = (datetime.now(tz=UTC) - self._last_intervention_at).total_seconds()
        return elapsed >= self._learning_analytics_config.cooldown_period

    async def _record_latency(self, stage: str, duration_ms: float) -> None:
        """Record cycle stage latency (best-effort, gated by the caller)."""
        from learning_analytics.latency import record_stage_latency

        try:
            async with self._db_factory() as db:
                await record_stage_latency(db, self._session_id, stage, duration_ms)
        except Exception:
            logger.warning("Не удалось записать латентность стадии", exc_info=True)

    # ── MRT (micro-randomized trial) ─────────────────────────────
    async def _mrt_step(self, analysis, features, regime, dwell: float, now) -> None:
        """MRT branch: spell lifecycle + decision-point randomization.

        Replaces the OPEN/CLOSED branch when mrt_enabled. dwell==0.0 ⇔ regime changed:
        close the previous spell (set exit_ts) and open a new one on a bad regime.
        At an eligible point (dwell >= jittered T_k, cooldown elapsed) draw
        intervene/withhold and write the decision point.
        """
        import random

        from learning_analytics.process_state import is_bad

        if dwell == 0.0:
            if self._spell_id is not None:
                await self._mrt_close_spell(now)
            if is_bad(regime):
                self._mrt_open_spell(regime.value)

        if self._spell_id is None or self._spell_t_k is None:
            return
        if dwell < self._spell_t_k:
            return
        if not self._should_trigger_intervention():
            return

        withhold = random.random() < self._learning_analytics_config.mrt_hold_probability
        assignment = "withhold" if withhold else "intervene"
        await self._mrt_record_decision(regime.value, dwell, self._spell_t_k, assignment, now)

        if withhold:
            await self._log_would_intervene(analysis)
            self._last_intervention_at = now
            return

        pending = await self._decide_intervention(analysis, features)
        if pending is None:
            return
        await self._dispatch_intervention(pending)
        async with self._db_factory() as db:
            await self._persist_intervention(db, pending)
        self._last_intervention_at = now

    def _mrt_open_spell(self, regime_value: str) -> None:
        """Open a bad-spell: jittered T_k = base * U[1-f, 1+f], new spell_id."""
        import random
        from uuid import uuid4

        base = self._learning_analytics_config.dwell_thresholds.get(regime_value, 0.0)
        j = self._learning_analytics_config.mrt_t_k_jitter_frac
        self._spell_t_k = base * random.uniform(1.0 - j, 1.0 + j)
        self._spell_id = str(uuid4())
        self._open_decision_ids = []

    async def _mrt_record_decision(
        self, regime_value: str, dwell: float, t_k: float, assignment: str, now
    ) -> None:
        """Record an MRT decision point."""
        from uuid import uuid4

        from models.intervention_decision import InterventionDecision

        row = InterventionDecision(
            id=str(uuid4()),
            session_id=self._session_id,
            user_id=self._user_id,
            lab_slug=self._lab_slug,
            spell_id=self._spell_id,
            ts=now,
            regime=regime_value,
            dwell_seconds=dwell,
            t_k_applied=t_k,
            assignment=assignment,
        )
        self._open_decision_ids.append(row.id)
        async with self._db_factory() as db:
            db.add(row)
            await db.commit()

    async def _mrt_close_spell(self, now) -> None:
        """Close the spell: set subsequent_exit_ts on the open decision points."""
        from sqlalchemy import update

        from models.intervention_decision import InterventionDecision

        ids = self._open_decision_ids
        self._spell_id = None
        self._spell_t_k = None
        self._open_decision_ids = []
        if not ids:
            return
        async with self._db_factory() as db:
            await db.execute(
                update(InterventionDecision)
                .where(InterventionDecision.id.in_(ids))
                .values(subsequent_exit_ts=now)
            )
            await db.commit()
