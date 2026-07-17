"""Выгрузка когортных орг-метрик на защиту. Читает тот же сервис, что эндпоинт."""

import asyncio

from db.session import async_session
from config.env_config_loader import load_settings
from cohort.service import compute_cohort_metrics


def _fmt_days(seconds):
    return "—" if seconds is None else f"{seconds / 86400.0:.1f} дн"


async def main():
    cfg = load_settings().learning_analytics
    async with async_session() as db:
        out = await compute_cohort_metrics(
            db, horizon_seconds=cfg.cohort_horizon_days * 86400.0, by_arm=True
        )
    print(f"# Когортные орг-метрики (headline={out['headline_arm']})\n")
    print("| Страта | n | reach L2 | медиана календ. | медиана актив. | воздейств. L1→L2 |")
    print("|-|-|-|-|-|-|")
    for cell in out["by_skill"] + [out["pooled"]]:
        t, a = cell.time_to_competence, cell.autonomy
        label = cell.skill or "ПУЛ"
        l2i = "—" if a.mean_l2_interventions is None else f"{a.mean_l2_interventions:.1f}"
        print(
            f"| {label} | {t.n} | {t.reach_rate:.2f} (цензур {t.censored}) | "
            f"{_fmt_days(t.median_calendar_seconds)} | {_fmt_days(t.median_active_seconds)} | "
            f"{a.mean_l1_interventions:.1f}→{l2i} |"
        )
    print(f"\n_D4-тренд — описательный (survivorship). Дельта open↔closed = Задача 4._")


if __name__ == "__main__":
    asyncio.run(main())
