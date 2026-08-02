"""Export of cohort org metrics for the defense. Reads the same service as the endpoint."""

import asyncio

from cohort.report import render_cohort_table
from cohort.service import compute_cohort_metrics
from config.env_config_loader import load_settings
from db.session import async_session


async def main():
    cfg = load_settings().learning_analytics
    async with async_session() as db:
        out = await compute_cohort_metrics(
            db, horizon_seconds=cfg.cohort_horizon_days * 86400.0, by_arm=True
        )
    print(f"# Когортные орг-метрики (headline={out['headline_arm']})\n")
    for line in render_cohort_table(
        out["by_skill"] + [out["pooled"]],
        ["stratum", "n", "reach_censored", "median_calendar", "median_active", "interventions"],
    ):
        print(line)
    print("\n_D4-тренд — описательный (survivorship). Дельта open↔closed = Задача 4._")


if __name__ == "__main__":
    asyncio.run(main())
