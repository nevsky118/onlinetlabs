"""Building LearnerOutcome from the DB and computing cohort metrics. A single source (endpoint/script/view)."""

from sqlalchemy import select

from cohort.metrics import LearnerOutcome, aggregate_cohort
from experiment.assignment import skill_tag
from models.experiment import ExperimentMetrics
from models.lab import Lab
from models.progress import LabProgress
from models.session import LearningSession


async def _skill_of(db, lab_slug: str, cache: dict) -> str | None:
    """Cached skill_tag by lab slug."""
    if lab_slug not in cache:
        lab = (await db.execute(select(Lab).where(Lab.slug == lab_slug))).scalar_one_or_none()
        cache[lab_slug] = skill_tag(lab) if lab else None
    return cache[lab_slug]


async def _sessions_for_skill(
    sessions: list, user_id: str, skill: str, skill_cache: dict, db
) -> list:
    """User's sessions for a skill (no await inside a list comprehension)."""
    result = []
    for s in sessions:
        if s.user_id != user_id:
            continue
        s_skill = await _skill_of(db, s.lab_slug, skill_cache)
        if s_skill == skill:
            result.append(s)
    return result


async def compute_cohort_metrics(db, horizon_seconds: float, by_arm: bool = False) -> dict:
    """Builds LearnerOutcome per (user, skill) from the DB and aggregates cohort metrics."""
    skill_cache: dict = {}
    progresses = (await db.execute(select(LabProgress))).scalars().all()
    sessions = (await db.execute(select(LearningSession))).scalars().all()
    metrics = (await db.execute(select(ExperimentMetrics))).scalars().all()

    # index: (user_id, lab_slug) -> the first ExperimentMetrics record
    em_by_user_lab: dict = {}
    for m in metrics:
        key = (m.user_id, m.lab_slug)
        if key not in em_by_user_lab:
            em_by_user_lab[key] = m

    # group progress by (user_id, skill)
    grouped: dict = {}
    for lp in progresses:
        skill = await _skill_of(db, lp.lab_slug, skill_cache)
        if not skill:
            continue
        grouped.setdefault((lp.user_id, skill), []).append(lp)

    records: list[LearnerOutcome] = []
    for (user_id, skill), labs in grouped.items():
        labs_sorted = sorted(labs, key=lambda x: (x.started_at or x.updated_at))
        l1 = labs_sorted[0]
        l1_start = l1.started_at

        # L2 = another lab of the same skill with l2_unassisted_pass=True
        l2_lp = None
        for lp in labs_sorted:
            if lp.lab_slug == l1.lab_slug:
                continue
            em = em_by_user_lab.get((user_id, lp.lab_slug))
            if em is not None and em.l2_unassisted_pass is True:
                l2_lp = lp
                break
        reached = l2_lp is not None

        user_skill_sessions = await _sessions_for_skill(sessions, user_id, skill, skill_cache, db)

        # sessions up to (and including) the L2-pass moment
        l2_time = l2_lp.completed_at if reached else None
        rel_sessions = [
            s
            for s in user_skill_sessions
            if l2_time is None or (s.started_at and s.started_at <= l2_time)
        ]
        active_sec = (
            sum(
                (s.ended_at - s.started_at).total_seconds()
                for s in rel_sessions
                if s.ended_at and s.started_at
            )
            or None
        )

        # observation time: last activity - l1_start. With no completed sessions,
        # falls back to L1's completion/update time (not l1_start -- avoids collapsing censoring to 0).
        last_end = max((s.ended_at for s in user_skill_sessions if s.ended_at), default=None)
        obs_ref = last_end or l1.completed_at or l1.updated_at or l1_start
        observation = (obs_ref - l1_start).total_seconds() if (obs_ref and l1_start) else 0.0

        em_l1 = em_by_user_lab.get((user_id, l1.lab_slug))
        em_l2 = em_by_user_lab.get((user_id, l2_lp.lab_slug)) if reached else None
        arm = (em_l1.base_arm if em_l1 else None) or (em_l2.base_arm if em_l2 else None)

        records.append(
            LearnerOutcome(
                user_id=user_id,
                skill=skill,
                arm=arm,
                reached_l2=reached,
                time_to_l2_seconds=(
                    (l2_time - l1_start).total_seconds()
                    if (reached and l1_start and l2_time)
                    else None
                ),
                active_seconds=active_sec,
                sessions_to_l2=(len(rel_sessions) if reached else None),
                l1_interventions=(em_l1.interventions_received if em_l1 else 0),
                l2_interventions=(em_l2.interventions_received if em_l2 else None),
                l1_escalations=(em_l1.escalations if em_l1 else 0),
                l2_escalations=(em_l2.escalations if em_l2 else None),
                l1_repeated_errors=(em_l1.repeated_errors if em_l1 else 0),
                l2_repeated_errors=(em_l2.repeated_errors if em_l2 else None),
                observation_seconds=observation,
                censored=not reached,
            )
        )

    return aggregate_cohort(records, horizon_seconds, by_arm=by_arm)
