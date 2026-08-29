"""StudentProfile: latent student traits, seed determinism, cohort diversity."""

import statistics

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class TestStudentProfile:
    @autotest.num("2029")
    @autotest.external_id("5bbf908d-dc8f-44c6-9a40-8e42e637385f")
    @autotest.name("profiles: profile is deterministic by seed (run is reproducible)")
    async def test_5bbf908d_profile_deterministic_by_seed(self):
        with autotest.step("Arrange: the same seed"):
            from simulation.profiles import sample_profile

            seed = 42

        with autotest.step("Act: sample the profile twice"):
            first, second = sample_profile(seed), sample_profile(seed)

        with autotest.step("Assert: profiles are identical"):
            assert_equal(first, second, "profile for the same seed")

    @autotest.num("2030")
    @autotest.external_id("37fcd5f9-8f2e-4d08-9fd8-0d2d24459eff")
    @autotest.name("profiles: all traits lie in [0, 1]")
    async def test_37fcd5f9_profile_traits_in_unit_range(self):
        with autotest.step("Arrange: arbitrary seed"):
            from simulation.profiles import sample_profile

        with autotest.step("Act: sample a profile"):
            profile = sample_profile(7)

        with autotest.step("Assert: each trait is in the unit range"):
            traits = (
                profile.skill,
                profile.persistence,
                profile.strategy,
                profile.pace,
                profile.help_propensity,
            )
            for trait in traits:
                assert_true(0.0 <= trait <= 1.0, f"trait {trait} outside [0,1]")

    @autotest.num("2031")
    @autotest.external_id("5c4d3e42-66f5-4421-85fa-deaeb48083fd")
    @autotest.name("profiles: cohort is diverse (not clones of one student)")
    async def test_5c4d3e42_cohort_is_diverse(self):
        with autotest.step("Arrange: a cohort of 50 students"):
            from simulation.profiles import sample_cohort

        with autotest.step("Act: sample the cohort"):
            cohort = sample_cohort(50, base_seed=0)

        with autotest.step("Assert: size is correct and each trait is spread out"):
            assert_equal(len(cohort), 50, "cohort size")
            for attr in ("skill", "persistence", "strategy", "pace", "help_propensity"):
                values = [getattr(learner, attr) for learner in cohort]
                assert_true(statistics.stdev(values) > 0.1, f"trait {attr} not diverse enough")
