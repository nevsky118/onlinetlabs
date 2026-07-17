"""StudentProfile: latent student traits, seed determinism, cohort diversity."""

import statistics

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class TestStudentProfile:
    @autotest.num("2029")
    @autotest.external_id("5bbf908d-dc8f-44c6-9a40-8e42e637385f")
    @autotest.name("profiles: профиль детерминирован seed'ом (прогон воспроизводим)")
    async def test_5bbf908d_profile_deterministic_by_seed(self):
        with autotest.step("Arrange: один и тот же seed"):
            from simulation.profiles import sample_profile

            seed = 42

        with autotest.step("Act: сэмплируем профиль дважды"):
            first, second = sample_profile(seed), sample_profile(seed)

        with autotest.step("Assert: профили идентичны"):
            assert_equal(first, second, "профиль по одному seed")

    @autotest.num("2030")
    @autotest.external_id("37fcd5f9-8f2e-4d08-9fd8-0d2d24459eff")
    @autotest.name("profiles: все черты лежат в [0, 1]")
    async def test_37fcd5f9_profile_traits_in_unit_range(self):
        with autotest.step("Arrange: произвольный seed"):
            from simulation.profiles import sample_profile

        with autotest.step("Act: сэмплируем профиль"):
            profile = sample_profile(7)

        with autotest.step("Assert: каждая черта в единичном диапазоне"):
            traits = (
                profile.skill,
                profile.persistence,
                profile.strategy,
                profile.pace,
                profile.help_propensity,
            )
            for value in traits:
                assert_true(0.0 <= value <= 1.0, f"черта {value} вне [0,1]")

    @autotest.num("2031")
    @autotest.external_id("5c4d3e42-66f5-4421-85fa-deaeb48083fd")
    @autotest.name("profiles: когорта разнообразна (не клоны одного студента)")
    async def test_5c4d3e42_cohort_is_diverse(self):
        with autotest.step("Arrange: когорта на 50 студентов"):
            from simulation.profiles import sample_cohort

        with autotest.step("Act: сэмплируем когорту"):
            cohort = sample_cohort(50, base_seed=0)

        with autotest.step("Assert: размер верный и каждая черта разбросана"):
            assert_equal(len(cohort), 50, "размер когорты")
            for attr in ("skill", "persistence", "strategy", "pace", "help_propensity"):
                values = [getattr(p, attr) for p in cohort]
                assert_true(
                    statistics.stdev(values) > 0.1, f"черта {attr} недостаточно разнообразна"
                )
