"""Characterization: cohort_response_from_result — полный model_dump() пиксель-в-пиксель."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from cohort.metrics import LearnerOutcome, aggregate_cohort
from instructor.schemas import cohort_response_from_result

pytestmark = [pytest.mark.unit]


class TestCohortResponseFullJson:
    @autotest.num("2509")
    @autotest.external_id("fab912be-943a-4d23-a650-d857d1a669c0")
    @autotest.name(
        "cohort_response_from_result: полный model_dump() двух записей пиксель-в-пиксель"
    )
    def test_fab912be_full_model_dump_exact(self):
        with autotest.step("Arrange: один достигший L2, один цензурированный, разные arm"):
            records = [
                LearnerOutcome(
                    user_id="u1",
                    skill="routing",
                    arm="closed",
                    reached_l2=True,
                    time_to_l2_seconds=3600.0,
                    active_seconds=1800.0,
                    sessions_to_l2=2,
                    l1_interventions=3,
                    l2_interventions=0,
                    l1_escalations=1,
                    l2_escalations=0,
                    l1_repeated_errors=2,
                    l2_repeated_errors=0,
                    observation_seconds=3600.0,
                    censored=False,
                ),
                LearnerOutcome(
                    user_id="u2",
                    skill="routing",
                    arm="open",
                    reached_l2=False,
                    time_to_l2_seconds=None,
                    active_seconds=None,
                    sessions_to_l2=None,
                    l1_interventions=5,
                    l2_interventions=None,
                    l1_escalations=2,
                    l2_escalations=None,
                    l1_repeated_errors=4,
                    l2_repeated_errors=None,
                    observation_seconds=1800.0,
                    censored=True,
                ),
            ]

        with autotest.step("Act: агрегировать (by_arm=True) и построить ответ"):
            out = aggregate_cohort(records, horizon_seconds=7200.0, by_arm=True)
            resp = cohort_response_from_result(out)

        with autotest.step("Assert: полный model_dump() равен ожидаемому"):
            assert_equal(
                resp.model_dump(),
                {
                    "by_skill": [
                        {
                            "skill": "routing",
                            "arm": None,
                            "n": 2,
                            "time_to_competence": {
                                "median_calendar_seconds": 3600.0,
                                "median_active_seconds": None,
                                "reach_rate": 0.5,
                                "reach_rate_at_horizon": 1.0,
                                "restricted_mean_calendar_seconds": 3600.0,
                                "n": 2,
                                "censored": 1,
                            },
                            "autonomy": {
                                "mean_l1_interventions": 4.0,
                                "mean_l2_interventions": 0.0,
                                "mean_sessions_to_l2": 2.0,
                            },
                            "org_effect": {
                                "l1_escalations_mean": 1.5,
                                "l2_escalations_mean": 0.0,
                                "l1_repeated_errors_mean": 3.0,
                                "l2_repeated_errors_mean": 0.0,
                                "note": (
                                    "Описательный/разведочный тренд: считается по дошедшим до "
                                    "L2 (= успешные), возможен survivorship bias + регрессия к "
                                    "среднему. НЕ доказательство снижения платформой. Каузальное "
                                    "снижение — Задача 4 (open vs closed)."
                                ),
                            },
                        }
                    ],
                    "pooled": {
                        "skill": None,
                        "arm": None,
                        "n": 2,
                        "time_to_competence": {
                            "median_calendar_seconds": 3600.0,
                            "median_active_seconds": None,
                            "reach_rate": 0.5,
                            "reach_rate_at_horizon": 1.0,
                            "restricted_mean_calendar_seconds": 3600.0,
                            "n": 2,
                            "censored": 1,
                        },
                        "autonomy": {
                            "mean_l1_interventions": 4.0,
                            "mean_l2_interventions": 0.0,
                            "mean_sessions_to_l2": 2.0,
                        },
                        "org_effect": {
                            "l1_escalations_mean": 1.5,
                            "l2_escalations_mean": 0.0,
                            "l1_repeated_errors_mean": 3.0,
                            "l2_repeated_errors_mean": 0.0,
                            "note": (
                                "Описательный/разведочный тренд: считается по дошедшим до "
                                "L2 (= успешные), возможен survivorship bias + регрессия к "
                                "среднему. НЕ доказательство снижения платформой. Каузальное "
                                "снижение — Задача 4 (open vs closed)."
                            ),
                        },
                    },
                    "by_arm": [
                        {
                            "skill": None,
                            "arm": "closed",
                            "n": 1,
                            "time_to_competence": {
                                "median_calendar_seconds": 3600.0,
                                "median_active_seconds": 1800.0,
                                "reach_rate": 1.0,
                                "reach_rate_at_horizon": 1.0,
                                "restricted_mean_calendar_seconds": 3600.0,
                                "n": 1,
                                "censored": 0,
                            },
                            "autonomy": {
                                "mean_l1_interventions": 3.0,
                                "mean_l2_interventions": 0.0,
                                "mean_sessions_to_l2": 2.0,
                            },
                            "org_effect": {
                                "l1_escalations_mean": 1.0,
                                "l2_escalations_mean": 0.0,
                                "l1_repeated_errors_mean": 2.0,
                                "l2_repeated_errors_mean": 0.0,
                                "note": (
                                    "Описательный/разведочный тренд: считается по дошедшим до "
                                    "L2 (= успешные), возможен survivorship bias + регрессия к "
                                    "среднему. НЕ доказательство снижения платформой. Каузальное "
                                    "снижение — Задача 4 (open vs closed)."
                                ),
                            },
                        },
                        {
                            "skill": None,
                            "arm": "open",
                            "n": 1,
                            "time_to_competence": {
                                "median_calendar_seconds": None,
                                "median_active_seconds": None,
                                "reach_rate": 0.0,
                                "reach_rate_at_horizon": 0.0,
                                "restricted_mean_calendar_seconds": 7200.0,
                                "n": 1,
                                "censored": 1,
                            },
                            "autonomy": {
                                "mean_l1_interventions": 5.0,
                                "mean_l2_interventions": None,
                                "mean_sessions_to_l2": None,
                            },
                            "org_effect": {
                                "l1_escalations_mean": 2.0,
                                "l2_escalations_mean": None,
                                "l1_repeated_errors_mean": 4.0,
                                "l2_repeated_errors_mean": None,
                                "note": (
                                    "Описательный/разведочный тренд: считается по дошедшим до "
                                    "L2 (= успешные), возможен survivorship bias + регрессия к "
                                    "среднему. НЕ доказательство снижения платформой. Каузальное "
                                    "снижение — Задача 4 (open vs closed)."
                                ),
                            },
                        },
                    ],
                    "headline_arm": "closed",
                },
                "полный model_dump() ответа",
            )
