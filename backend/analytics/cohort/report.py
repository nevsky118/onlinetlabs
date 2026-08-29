"""Markdown rendering of cohort cells, shared by the export scripts."""

from analytics.cohort.metrics import CohortCell

# Column key -> (header, cell renderer). Callers pick the columns they want;
# the two exporters used to render the same rows with drifted column sets.
_COLUMNS = {
    "stratum": ("Страта", lambda c: c.skill or "ПУЛ"),
    "n": ("n", lambda c: str(c.time_to_competence.n)),
    "censored": ("цензур", lambda c: str(c.time_to_competence.censored)),
    "reach": ("reach L2", lambda c: f"{c.time_to_competence.reach_rate:.2f}"),
    "reach_censored": (
        "reach L2",
        lambda c: f"{c.time_to_competence.reach_rate:.2f} (цензур {c.time_to_competence.censored})",
    ),
    "median_calendar": (
        "медиана кал.",
        lambda c: fmt_days(c.time_to_competence.median_calendar_seconds),
    ),
    "median_active": (
        "медиана акт.",
        lambda c: fmt_days(c.time_to_competence.median_active_seconds),
    ),
    "interventions": ("возд. L1→L2", lambda c: _interventions(c)),
}


def fmt_days(seconds: float | None) -> str:
    """Seconds as days, em dash when unknown."""
    return "—" if seconds is None else f"{seconds / 86400.0:.1f} дн"


def _interventions(cell: CohortCell) -> str:
    l2 = cell.autonomy.mean_l2_interventions
    l2_text = "—" if l2 is None else f"{l2:.1f}"
    return f"{cell.autonomy.mean_l1_interventions:.1f}→{l2_text}"


def render_cohort_table(cells: list[CohortCell], columns: list[str]) -> list[str]:
    """Markdown table lines: header, separator, one row per cell."""
    headers = [_COLUMNS[key][0] for key in columns]
    lines = ["| " + " | ".join(headers) + " |", "|" + "-|" * len(columns)]
    for cell in cells:
        lines.append("| " + " | ".join(_COLUMNS[key][1](cell) for key in columns) + " |")
    return lines
