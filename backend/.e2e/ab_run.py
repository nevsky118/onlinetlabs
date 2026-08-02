"""Arm-analysis demo against a real database.

Only behavioral_events are seeded; everything downstream is production code:
end_session -> _finalize_experiment_metrics -> ExperimentMetrics -> compute_arm_analysis.
Outcomes are prescribed, so the numbers are a wiring check, not a result.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, select

from config.env_config_loader import load_settings
from db.session import async_session
from evaluation.arm_analysis import compute_arm_analysis
from models.behavioral_event import BehavioralEvent
from models.experiment import ExperimentMetrics
from models.progress import LabProgress
from models.session import LearningSession
from models.user import User
from sessions.services.lifecycle import end_session

PREFIX = "ab-demo-"
L1 = "lan-static-ip"  # skill: static-ip-addressing
L2 = "lan-static-ip-b"  # near-transfer, same skill


def _ev(session_id, user_id, lab, etype, action, msg, t):
    return BehavioralEvent(
        id=str(uuid4()),
        session_id=session_id,
        user_id=user_id,
        lab_slug=lab,
        timestamp=t,
        event_type=etype,
        action=action,
        success=False,
        severity="info",
        message=msg,
        created_at=t,
    )


async def _seed_session(db, user_id, lab, status_completed, events, base_t):
    """Creates a session, LabProgress and events. Left active for end_session to close."""
    sid = str(uuid4())
    db.add(
        LearningSession(
            id=sid,
            user_id=user_id,
            lab_slug=lab,
            status="active",
            started_at=base_t,
            ended_at=None,
        )
    )
    db.add(
        LabProgress(
            id=str(uuid4()),
            user_id=user_id,
            lab_slug=lab,
            status="completed" if status_completed else "in_progress",
            score=90 if status_completed else None,
            current_step=2 if status_completed else 1,
            started_at=base_t,
            completed_at=base_t + timedelta(minutes=10) if status_completed else None,
            updated_at=base_t + timedelta(minutes=10),
        )
    )
    for e in events:
        db.add(e)
    await db.commit()
    return sid


async def run():
    base = datetime(2026, 6, 21, 10, 0, tzinfo=UTC)
    # 4 closed + 4 open. Prescribed L2 pass: closed 3/4, open 1/4.
    cohort = (
        [(f"{PREFIX}c{i}", "closed", True) for i in range(4)]  # every arm passes L1
        + [(f"{PREFIX}o{i}", "open", True) for i in range(4)]
    )
    l2_pass = {
        f"{PREFIX}c0": True,
        f"{PREFIX}c1": True,
        f"{PREFIX}c2": True,
        f"{PREFIX}c3": False,
        f"{PREFIX}o0": True,
        f"{PREFIX}o1": False,
        f"{PREFIX}o2": False,
        f"{PREFIX}o3": False,
    }

    async with async_session() as db:
        for uid, arm, _ in cohort:
            db.add(
                User(
                    id=uid,
                    name=uid,
                    email=f"{uid}@demo.local",
                    role="student",
                    control_arm=arm,
                    experiment_group="unknown",
                )
            )
        await db.commit()

        for uid, arm, l1_done in cohort:
            # L1: closed gets one intervention; open gets would_intervene + 2 escalations
            if arm == "closed":
                evs = [
                    _ev("X", uid, L1, "intervention", "hint", "hint", base + timedelta(minutes=2))
                ]
            else:
                evs = [
                    _ev(
                        "X",
                        uid,
                        L1,
                        "would_intervene",
                        "hint",
                        "would have fired",
                        base + timedelta(minutes=2),
                    ),
                    _ev(
                        "X",
                        uid,
                        L1,
                        "escalation",
                        "objective",
                        "mentor needed",
                        base + timedelta(minutes=6),
                    ),
                    _ev(
                        "X",
                        uid,
                        L1,
                        "escalation",
                        "manual",
                        "mentor needed",
                        base + timedelta(minutes=9),
                    ),
                ]
            sid = await _seed_session(db, uid, L1, l1_done, [], base)
            for e in evs:  # bind to the real session_id
                e.session_id = sid
                db.add(e)
            await db.commit()
            await end_session(db, sid, uid, "ended")  # finalizes -> ExperimentMetrics(L1)

            # L2 holdout: no proactivity for anyone. l2_unassisted_pass = passed alone.
            sid2 = await _seed_session(db, uid, L2, l2_pass[uid], [], base + timedelta(hours=1))
            await end_session(db, sid2, uid, "ended")  # -> ExperimentMetrics(L2), is_l2=True

        # Analysis runs on the rows just written.
        rows = (
            (
                await db.execute(
                    select(ExperimentMetrics).where(ExperimentMetrics.user_id.like(f"{PREFIX}%"))
                )
            )
            .scalars()
            .all()
        )
        cfg = load_settings().learning_analytics
        res = compute_arm_analysis(rows, mentor_seconds=cfg.mentor_handling_seconds)

        print(f"\n=== ExperimentMetrics rows created: {len(rows)} ===")
        l2rows = [r for r in rows if r.l2_unassisted_pass is not None]
        print(f"L2 sessions: {len(l2rows)}; total escalations: {sum(r.escalations for r in rows)}")
        print("\n=== DEMO: events are seeded and outcomes prescribed - not a field result ===")
        print(
            f"  L2 unassisted pass rate:  closed={res.l2_pass_rate_closed:.2f}  open={res.l2_pass_rate_open:.2f}"
        )
        print(
            f"  Escalations per session:   closed={res.escalations_mean_closed:.2f}  open={res.escalations_mean_open:.2f}"
        )
        print(f"  Mentor hours saved by closed: {res.mentor_hours_saved:.2f} h")
        print(f"  repeated_errors comparison: {res.repeated_errors_comparison}")


async def cleanup():
    async with async_session() as db:
        await db.execute(delete(User).where(User.id.like(f"{PREFIX}%")))  # CASCADE removes the rest
        await db.commit()
    print("\n=== demo data removed (CASCADE) ===")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        asyncio.run(cleanup())
    else:
        asyncio.run(run())
