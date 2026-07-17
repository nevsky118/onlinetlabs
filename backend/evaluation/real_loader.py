"""Loading real scenarios from the open arm + inter-rater agreement (Cohen's kappa)."""

from sqlalchemy import select

from models.experiment import ExperimentMetrics


def cohens_kappa(labeler_a: list[str], labeler_b: list[str]) -> float:
    """Agreement between two annotators over categories: (po - pe) / (1 - pe)."""
    n = len(labeler_a)
    if n == 0 or n != len(labeler_b):
        return 0.0
    po = sum(1 for x, y in zip(labeler_a, labeler_b) if x == y) / n
    cats = set(labeler_a) | set(labeler_b)
    pe = sum((labeler_a.count(c) / n) * (labeler_b.count(c) / n) for c in cats)
    if 1.0 - pe == 0.0:
        return 1.0
    return (po - pe) / (1.0 - pe)


def labeled_real_count(scenarios) -> int:
    """Count of scenarios with source=='real' (real, labeled)."""
    return sum(1 for s in scenarios if s.source == "real")


async def harvest_open_arm_sessions(db) -> list[str]:
    """session_ids where base_arm == 'open' (no interventions)."""
    rows = (
        (
            await db.execute(
                select(ExperimentMetrics.session_id).where(ExperimentMetrics.base_arm == "open")
            )
        )
        .scalars()
        .all()
    )
    return list(rows)
