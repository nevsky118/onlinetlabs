"""LabProgressObserver — периодический прогон spec-проверок, текущий шаг."""

import asyncio
import json
import logging
from dataclasses import dataclass, field

from config.config_model import LearningAnalyticsConfig

logger = logging.getLogger(__name__)


@dataclass
class ProgressState:
    """Производное состояние прогресса: текущий шаг и провальные проверки."""

    current_step_id: str | None
    current_step_title: str
    failing_checks: list[dict] = field(default_factory=list)


def derive_current_step(snapshot: list[dict]) -> ProgressState:
    """Первый упавший шаг — текущий; нет упавших — лаба завершена."""
    for step in snapshot:
        if step.get("ok") is False:
            failing = [c for c in step.get("checks", []) if c.get("ok") is False]
            return ProgressState(
                current_step_id=step["id"],
                current_step_title=step.get("title", ""),
                failing_checks=failing,
            )
    return ProgressState(current_step_id=None, current_step_title="", failing_checks=[])


def diff_snapshots(prev: list[dict] | None, curr: list[dict]) -> list[dict]:
    """Дельта двух снапшотов → список event-dict для BehavioralEvent."""
    if prev is None:
        return []

    # индекс prev-проверок по стабильному ключу
    prev_index: dict[str, dict] = {}
    for step in prev:
        for c in step.get("checks", []):
            key = f"{c['kind']}@{json.dumps(c['params'], sort_keys=True)}"
            prev_index[key] = c

    events: list[dict] = []
    for step in curr:
        for c in step.get("checks", []):
            key = f"{c['kind']}@{json.dumps(c['params'], sort_keys=True)}"
            if key not in prev_index:
                continue
            pc = prev_index[key]
            p_ok, c_ok = pc.get("ok"), c.get("ok")
            p_actual, c_actual = pc.get("actual"), c.get("actual")
            params = c.get("params")
            component_id = (params.get("node") if isinstance(params, dict) else None) or c["kind"]

            if not p_ok and c_ok:
                # исправлено
                events.append(
                    {
                        "event_type": "action",
                        "action": "check_passed",
                        "component_id": component_id,
                        "message": key,
                        "success": True,
                        "extra_data": None,
                    }
                )
            elif p_ok and not c_ok:
                # регресс
                events.append(
                    {
                        "event_type": "error",
                        "action": "check_regressed",
                        "component_id": component_id,
                        "message": key,
                        "success": False,
                        "extra_data": {"actual": c_actual},
                    }
                )
            elif not p_ok and not c_ok:
                if p_actual == c_actual:
                    # без изменений
                    events.append(
                        {
                            "event_type": "error",
                            "action": "check_failing",
                            "component_id": component_id,
                            "message": key,
                            "success": False,
                            "extra_data": {"actual": c_actual},
                        }
                    )
                else:
                    # другая ошибка — студент пробует
                    events.append(
                        {
                            "event_type": "error",
                            "action": "check_retry",
                            "component_id": component_id,
                            "message": key,
                            "success": False,
                            "extra_data": {"prev_actual": p_actual, "actual": c_actual},
                        }
                    )
            # both ok → нет события
    return events


class LabProgressObserver:
    """Периодически прогоняет spec-проверки и хранит текущий шаг."""

    def __init__(
        self, gns3_client, db_factory, settings, learning_analytics_config: LearningAnalyticsConfig
    ):
        """Инициализация с GNS3-клиентом, фабрикой DB и конфигом."""
        self._gns3 = gns3_client
        self._db_factory = db_factory
        self._settings = settings
        self._cfg = learning_analytics_config
        self._task: asyncio.Task | None = None
        self._state: ProgressState | None = None
        self._prev_snapshot: list[dict] | None = None
        self._session_id: str | None = None
        self._user_id: str | None = None
        self._lab_slug: str | None = None
        self._gns3_sid: str | None = None

    async def start(self, session_id: str, user_id: str, lab_slug: str, gns3_sid: str) -> None:
        """Запуск цикла опроса как asyncio.Task."""
        self._session_id = session_id
        self._user_id = user_id
        self._lab_slug = lab_slug
        self._gns3_sid = gns3_sid
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Остановка цикла."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def current_state(self) -> ProgressState | None:
        """Последнее вычисленное состояние прогресса."""
        return self._state

    async def _poll_loop(self) -> None:
        """Бесконечный цикл: прогон → пауза → повтор."""
        while True:
            try:
                await self._poll_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.warning("LabProgressObserver: ошибка цикла", exc_info=True)
            await asyncio.sleep(self._cfg.progress_poll_interval)

    async def _poll_cycle(self) -> None:
        """Один цикл: загрузка spec → контекст → снапшот → текущий шаг."""
        from validation.runner import evaluate_spec, load_lab_spec
        from validation.service import build_check_context

        spec = load_lab_spec(self._lab_slug)
        if spec is None:
            return

        ctx = await build_check_context(self._gns3, self._gns3_sid, self._settings)
        snapshot = await evaluate_spec(ctx, spec)
        self._state = derive_current_step(snapshot)
        # дельты → поведенческие события
        events = diff_snapshots(self._prev_snapshot, snapshot)
        if events:
            from datetime import datetime, timezone
            from uuid import uuid4

            now = datetime.now(tz=timezone.utc)
            for evt in events:
                evt.update(
                    {
                        "id": str(uuid4()),
                        "session_id": self._session_id,
                        "user_id": self._user_id,
                        "lab_slug": self._lab_slug,
                        "timestamp": now,
                        "component_type": None,
                        "raw_command": None,
                        "severity": None,
                    }
                )
            await self._persist(events)
        self._prev_snapshot = snapshot

    async def _persist(self, events: list[dict]) -> None:
        """Пакетная запись событий в DB."""
        from models.behavioral_event import BehavioralEvent

        try:
            async with self._db_factory() as session:
                for evt in events:
                    session.add(BehavioralEvent(**evt))
                await session.commit()
        except Exception:
            logger.error("LabProgressObserver: не удалось сохранить события", exc_info=True)
