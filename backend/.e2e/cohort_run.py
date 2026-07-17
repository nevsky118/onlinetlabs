"""Реальный когортный прогон Задачи 3 на реальной БД: реальные модели + compute_cohort_metrics.

Seeded: прогресс/сессии/метрики (без живых студентов их не получить). Ниже по потоку —
реальный код: compute_cohort_metrics на реальной БД. Проверяем KM-фолбэк, цензурирование, страты.
"""
import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete

from cohort.service import compute_cohort_metrics
from db.session import async_session
from models.experiment import ExperimentMetrics
from models.progress import LabProgress
from models.session import LearningSession
from models.user import User

PREFIX = "coh-demo-"
BASE = datetime(2026, 5, 1, 9, 0, tzinfo=UTC)
DAY = 86400.0


async def _lab_progress(db, uid, slug, start_day, done_day):
    db.add(LabProgress(
        id=str(uuid4()), user_id=uid, lab_slug=slug,
        status="completed" if done_day is not None else "in_progress",
        score=90 if done_day is not None else None,
        current_step=2 if done_day is not None else 1,
        started_at=BASE + timedelta(days=start_day),
        completed_at=(BASE + timedelta(days=done_day)) if done_day is not None else None,
        updated_at=BASE + timedelta(days=(done_day if done_day is not None else start_day)),
    ))


async def _session(db, uid, slug, start_day, end_day):
    sid = str(uuid4())
    db.add(LearningSession(
        id=sid, user_id=uid, lab_slug=slug, status="ended",
        started_at=BASE + timedelta(days=start_day),
        ended_at=BASE + timedelta(days=end_day),
    ))
    return sid


async def _em(db, uid, slug, l2_pass, session_id):
    db.add(ExperimentMetrics(
        id=str(uuid4()), session_id=session_id, user_id=uid, lab_slug=slug,
        experiment_group="unknown", total_time_seconds=600.0, steps_completed=2,
        total_errors=1, repeated_errors=1, unique_error_types=1,
        interventions_received=1, interventions_succeeded=1, interventions_failed=0, interventions_accepted=0,
        base_arm="closed", control_arm="closed", escalations=0, would_interventions=0, l1_interventions=1,
        l2_unassisted_pass=l2_pass, final_score=90.0, completed=True,
    ))


async def run():
    async with async_session() as db:
        # 9 closed-студентов: static-ip (4 дошли L2, 2 цензур) + dhcp (3 цензур, нет L2-пары)
        ids = [f"{PREFIX}{i}" for i in range(9)]
        for uid in ids:
            db.add(User(id=uid, name=uid, email=f"{uid}@demo.local", role="student",
                        control_arm="closed", experiment_group="unknown"))
        await db.commit()

        em_specs = []  # (uid, slug, l2_pass, session_id) — EM создаём после коммита сессий (FK)
        # static-ip: дошедшие до L2 на днях 5,7,9,11
        for i, l2day in zip(range(4), [5, 7, 9, 11]):
            uid = ids[i]
            await _lab_progress(db, uid, "lan-static-ip", 0, 1)
            await _lab_progress(db, uid, "lan-static-ip-b", 2, l2day)
            s1 = await _session(db, uid, "lan-static-ip", 0, 1)
            s2 = await _session(db, uid, "lan-static-ip-b", 2, l2day)
            em_specs += [(uid, "lan-static-ip", None, s1), (uid, "lan-static-ip-b", True, s2)]
        # static-ip: цензурированные (только L1, наблюдали до дня 15)
        for i in range(4, 6):
            uid = ids[i]
            await _lab_progress(db, uid, "lan-static-ip", 0, 1)
            s = await _session(db, uid, "lan-static-ip", 0, 15)
            em_specs.append((uid, "lan-static-ip", None, s))
        # dhcp: нет L2-пары → все цензур (L1 dhcp-basics, наблюдали до дня 10)
        for i in range(6, 9):
            uid = ids[i]
            await _lab_progress(db, uid, "dhcp-basics", 0, 1)
            s = await _session(db, uid, "dhcp-basics", 0, 10)
            em_specs.append((uid, "dhcp-basics", None, s))
        await db.commit()  # сессии должны существовать до вставки EM (FK)
        for uid, slug, l2_pass, sid in em_specs:
            await _em(db, uid, slug, l2_pass, sid)
        await db.commit()

        out = await compute_cohort_metrics(db, horizon_seconds=30 * DAY, by_arm=True)

    def _d(sec):
        return "—" if sec is None else f"{sec / DAY:.1f}д"

    print(f"\n=== Когортные орг-метрики (headline={out['headline_arm']}) ===")
    print("| Страта | n | reach L2 | цензур | медиана календ. | reach@30д | воздейств. L1→L2 |")
    print("|-|-|-|-|-|-|-|")
    for cell in out["by_skill"] + [out["pooled"]]:
        t, a = cell.time_to_competence, cell.autonomy
        label = cell.skill or "ПУЛ"
        l2i = "—" if a.mean_l2_interventions is None else f"{a.mean_l2_interventions:.1f}"
        print(f"| {label} | {t.n} | {t.reach_rate:.2f} | {t.censored} | {_d(t.median_calendar_seconds)} "
              f"| {t.reach_rate_at_horizon:.2f} | {a.mean_l1_interventions:.1f}→{l2i} |")
    print(f"\nплечи (страта): {[c.arm for c in (out['by_arm'] or [])]}")


async def cleanup():
    async with async_session() as db:
        await db.execute(delete(User).where(User.id.like(f"{PREFIX}%")))
        await db.commit()
    print("=== demo удалены (CASCADE) ===")


if __name__ == "__main__":
    import sys
    asyncio.run(cleanup() if (len(sys.argv) > 1 and sys.argv[1] == "clean") else run())
