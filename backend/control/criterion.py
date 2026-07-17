"""Критерий управления J: стоимость политики на исторических логах состояния."""

import statistics
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Costs:
    """Стоимости в единых единицах: застревание, воздействие, ложное воздействие."""

    c_stuck: float
    c_intervention: float
    c_false: float


@dataclass
class JResult:
    """Разложение критерия: J и его слагаемые."""

    J: float
    bad_duration: float
    n_interventions: int
    n_false: int


BAD_REGIMES = {"stuck_on_step", "repeating_errors", "idle", "trial_and_error"}


def is_bad_regime(regime: str) -> bool:
    return regime in BAD_REGIMES


def _to_sec(x) -> float:
    """float — пропуск; datetime → Unix-секунды."""
    if isinstance(x, datetime):
        return x.timestamp()
    return float(x)


def _count_false(samples, interventions) -> int:
    """Ложное воздействие: интервенция, после которой плохой режим завершился
    быстрее медианного «чистого» самовыхода (без интервенции).

    Допущение спайна: состояние кусочно-постоянно между опросами.
    Если чистых выходов нет — ложных не засчитываем (консервативно).
    """
    if not interventions:
        return 0

    ts = [_to_sec(s["ts"]) for s in samples]
    intervention_ts = sorted(_to_sec(iv["ts"]) for iv in interventions)

    # Найти все интервалы пребывания в плохом режиме (непрерывные спеллы)
    # Спелл = последовательность соседних bad-сэмплов (по left-edge правилу).
    # Собираем спеллы как (start, end, had_intervention).
    spells = []
    i = 0
    n = len(samples)
    while i < n - 1:
        if is_bad_regime(samples[i]["regime"]):
            spell_start = ts[i]
            j = i
            while j < n - 1 and is_bad_regime(samples[j]["regime"]):
                j += 1
            spell_end = ts[j]  # момент выхода в продуктивный режим
            recovered = not is_bad_regime(samples[j]["regime"])
            # Есть ли интервенция внутри спелла [spell_start, spell_end)?
            had_iv = any(spell_start <= ivt < spell_end for ivt in intervention_ts)
            spells.append(
                {
                    "start": spell_start,
                    "end": spell_end,
                    "duration": spell_end - spell_start,
                    "recovered": recovered,  # завершился ли продуктивным переходом
                    "had_iv": had_iv,
                }
            )
            i = j
        else:
            i += 1

    # Медиана длительности «чистых» выходов (без интервенции, закончились продуктивно)
    clean_durations = [sp["duration"] for sp in spells if not sp["had_iv"] and sp["recovered"]]
    if not clean_durations:
        return 0  # нет базы для оценки — ложных не считаем

    median_clean = statistics.median(clean_durations)

    # Ложное воздействие: спелл с интервенцией, который завершился быстрее медианы
    n_false = sum(
        1 for sp in spells if sp["had_iv"] and sp["recovered"] and sp["duration"] < median_clean
    )
    return n_false


def compute_J(samples, interventions, costs, *, bad_duration_samples=None):
    """Стоимость политики по логу состояния сессии.

    samples: список dict {ts: float|datetime, regime: str, dwell: float}, по возрастанию ts.
    interventions: список dict {ts: float|datetime}.
    bad_duration_samples: если задан, bad_duration считается по нему (усечённые сэмплы
      для офлайн-оптимизатора), а n_false — по оригинальным samples.
    bad_duration = суммарная длительность интервалов между соседними выборками,
      где левая выборка в плохом режиме (кусочно-постоянное состояние между опросами).
    Ложное воздействие (дефолт-стратегия, задокументировано как допущение спайна):
      воздействие, после которого процесс вернулся в продуктивный режим раньше
      медианного времени самопроизвольного выхода из этого режима по интервалам
      БЕЗ воздействия. Если медиану нельзя оценить (нет «чистых» выходов) —
      ложных не засчитываем (консервативно).
    """
    dur_samples = bad_duration_samples if bad_duration_samples is not None else samples
    ts = [_to_sec(s["ts"]) for s in dur_samples]
    bad_duration = 0.0
    for i in range(len(dur_samples) - 1):
        if is_bad_regime(dur_samples[i]["regime"]):
            bad_duration += ts[i + 1] - ts[i]
    n_interventions = len(interventions)
    n_false = _count_false(samples, interventions)
    J = (
        costs.c_stuck * bad_duration
        + costs.c_intervention * n_interventions
        + costs.c_false * n_false
    )
    return JResult(J=J, bad_duration=bad_duration, n_interventions=n_interventions, n_false=n_false)
