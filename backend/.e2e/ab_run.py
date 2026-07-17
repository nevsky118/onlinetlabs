"""Реальный прогон A/B: реальные модели + end_session-финализация + arm-анализ.

Seeded только behavioral_events (выход монитора — без живых студентов их не получить).
Всё ниже по потоку — реальный код на реальной БД: end_session → _finalize_experiment_metrics
→ ExperimentMetrics, затем compute_arm_analysis.
"""
import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, select

from config.env_config_loader import load_settings
from db.session import async_session
from experiment.analysis import compute_arm_analysis
from models.behavioral_event import BehavioralEvent
from models.experiment import ExperimentMetrics
from models.progress import LabProgress
from models.session import LearningSession
from models.user import User
from sessions.services.lifecycle import end_session

PREFIX = "ab-demo-"
L1 = "lan-static-ip"        # навык static-ip-addressing
L2 = "lan-static-ip-b"      # near-transfer, тот же навык


def _ev(session_id, user_id, lab, etype, action, msg, t):
    return BehavioralEvent(
        id=str(uuid4()), session_id=session_id, user_id=user_id, lab_slug=lab,
        timestamp=t, event_type=etype, action=action, success=False,
        severity="info", message=msg, created_at=t,
    )


async def _seed_session(db, user_id, lab, status_completed, events, base_t):
    """Создать сессию + LabProgress + события. Сессия остаётся active (закроем end_session'ом)."""
    sid = str(uuid4())
    db.add(LearningSession(
        id=sid, user_id=user_id, lab_slug=lab, status="active",
        started_at=base_t, ended_at=None,
    ))
    db.add(LabProgress(
        id=str(uuid4()), user_id=user_id, lab_slug=lab,
        status="completed" if status_completed else "in_progress",
        score=90 if status_completed else None,
        current_step=2 if status_completed else 1,
        started_at=base_t,
        completed_at=base_t + timedelta(minutes=10) if status_completed else None,
        updated_at=base_t + timedelta(minutes=10),
    ))
    for e in events:
        db.add(e)
    await db.commit()
    return sid


async def run():
    base = datetime(2026, 6, 21, 10, 0, tzinfo=UTC)
    # 4 closed (контур помог) + 4 open (без проактива). L2-проход: closed 3/4, open 1/4.
    cohort = (
        [(f"{PREFIX}c{i}", "closed", True) for i in range(4)] +   # все closed проходят L1
        [(f"{PREFIX}o{i}", "open", True) for i in range(4)]
    )
    l2_pass = {f"{PREFIX}c0": True, f"{PREFIX}c1": True, f"{PREFIX}c2": True, f"{PREFIX}c3": False,
               f"{PREFIX}o0": True, f"{PREFIX}o1": False, f"{PREFIX}o2": False, f"{PREFIX}o3": False}

    async with async_session() as db:
        for uid, arm, _ in cohort:
            db.add(User(id=uid, name=uid, email=f"{uid}@demo.local",
                        role="student", control_arm=arm, experiment_group="unknown"))
        await db.commit()

        for uid, arm, l1_done in cohort:
            # L1: closed → 1 интервенция (помогла), 0 эскалаций; open → would_intervene + 2 эскалации
            if arm == "closed":
                evs = [_ev("X", uid, L1, "intervention", "hint", "подсказка", base + timedelta(minutes=2))]
            else:
                evs = [
                    _ev("X", uid, L1, "would_intervene", "hint", "сработало бы", base + timedelta(minutes=2)),
                    _ev("X", uid, L1, "escalation", "objective", "нужен наставник", base + timedelta(minutes=6)),
                    _ev("X", uid, L1, "escalation", "manual", "нужен наставник", base + timedelta(minutes=9)),
                ]
            sid = await _seed_session(db, uid, L1, l1_done, [], base)
            for e in evs:  # привязать события к реальному session_id
                e.session_id = sid
                db.add(e)
            await db.commit()
            await end_session(db, sid, uid, "ended")  # реальная финализация → ExperimentMetrics(L1)

            # L2 (холдаут: проактива нет ни у кого). l2_unassisted_pass = прошёл сам.
            sid2 = await _seed_session(db, uid, L2, l2_pass[uid], [], base + timedelta(hours=1))
            await end_session(db, sid2, uid, "ended")  # финализация → ExperimentMetrics(L2), is_l2=True

        # === реальный анализ на реальных строках ===
        rows = (await db.execute(
            select(ExperimentMetrics).where(ExperimentMetrics.user_id.like(f"{PREFIX}%"))
        )).scalars().all()
        cfg = load_settings().learning_analytics
        res = compute_arm_analysis(rows, mentor_seconds=cfg.mentor_handling_seconds)

        print(f"\n=== ExperimentMetrics строк создано: {len(rows)} ===")
        l2rows = [r for r in rows if r.l2_unassisted_pass is not None]
        print(f"L2-сессий (is_l2): {len(l2rows)}; всего эскалаций: {sum(r.escalations for r in rows)}")
        print("\n=== ДЕМО: события ЗАСЕЯНЫ, исход предзадан — НЕ полевой результат ===")
        print(f"  L2 unassisted pass rate:  closed={res.l2_pass_rate_closed:.2f}  open={res.l2_pass_rate_open:.2f}")
        print(f"  Эскалаций на сессию (сред): closed={res.escalations_mean_closed:.2f}  open={res.escalations_mean_open:.2f}")
        print(f"  Контрфактуал часов наставника (closed экономит): {res.mentor_hours_saved:.2f} ч")
        print(f"  repeated_errors сравнение: {res.repeated_errors_comparison}")


async def cleanup():
    async with async_session() as db:
        await db.execute(delete(User).where(User.id.like(f"{PREFIX}%")))  # CASCADE снесёт всё
        await db.commit()
    print("\n=== demo-данные удалены (CASCADE) ===")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        asyncio.run(cleanup())
    else:
        asyncio.run(run())
