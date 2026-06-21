"""Загрузка реальных сценариев из open-плеча + согласие разметчиков (Cohen's κ)."""
from datetime import datetime, timezone

from sqlalchemy import select

from evaluation.scenarios import LabeledScenario, Snapshot
from learning_analytics.process_state import ProcessRegime
from models.behavioral_event import BehavioralEvent
from models.experiment import ExperimentMetrics


def cohens_kappa(labeler_a: list[str], labeler_b: list[str]) -> float:
    """Согласие двух разметчиков по категориям: (po - pe) / (1 - pe)."""
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
    """Число сценариев source=='real' (реальные с разметкой)."""
    return sum(1 for s in scenarios if s.source == "real")


async def harvest_open_arm_sessions(db) -> list[str]:
    """session_id'ы, где base_arm == 'open' (без вмешательств)."""
    rows = (await db.execute(
        select(ExperimentMetrics.session_id).where(ExperimentMetrics.base_arm == "open")
    )).scalars().all()
    return list(rows)


async def load_scenario(db, session_id: str, labels: dict | None) -> LabeledScenario:
    """События сессии → LabeledScenario с реальными снапшотами фич."""
    from learning_analytics.features import FeatureExtractor

    rows = (await db.execute(
        select(BehavioralEvent)
        .where(BehavioralEvent.session_id == session_id)
        .order_by(BehavioralEvent.timestamp)
    )).scalars().all()

    extractor = FeatureExtractor()

    # Накапливаем события скользящим окном; один снапшот = префикс до i-го события
    snapshots: list[Snapshot] = []
    if rows:
        t0 = rows[0].timestamp
        for i, event in enumerate(rows):
            features = extractor.compute(session_id, rows[: i + 1])
            ts = (event.timestamp - t0).total_seconds()
            snapshots.append(Snapshot(ts=ts, features=features))

    duration = snapshots[-1].ts if snapshots else 0.0

    # Метки из внешней слепой разметки
    if labels is not None:
        onset_ts = labels.get("onset_ts")
        truth_regime = ProcessRegime(labels["truth_regime"]) if "truth_regime" in labels else ProcessRegime.PRODUCTIVE
        onset_window = labels.get("onset_window", 30.0)
    else:
        onset_ts = None
        truth_regime = ProcessRegime.PRODUCTIVE
        onset_window = 30.0

    return LabeledScenario(
        snapshots=snapshots,
        onset_ts=onset_ts,
        onset_window=onset_window,
        truth_regime=truth_regime,
        duration_seconds=duration,
        source="real",
    )
