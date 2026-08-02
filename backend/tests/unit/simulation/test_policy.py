"""GenerativePolicy: the latent regime DRIVES actions (not derived from detector thresholds).

So the true regime is generated independently of the features the detector uses →
observer-ROC stays honest, not tautological.
"""

import random

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


def _run(profile, seed: int = 0, max_iters: int = 400):
    from simulation.policy import StudentState, next_step

    rng = random.Random(seed)
    state = StudentState(total_steps=5)
    actions, regimes = [], []
    for _ in range(max_iters):
        action, regime, state = next_step(profile, state, rng)
        actions.append(action)
        regimes.append(regime)
        if state.done:
            break
    return actions, regimes


def _low_skill_profile():
    from simulation.profiles import StudentProfile

    return StudentProfile(skill=0.1, persistence=0.2, strategy=0.15, pace=0.5, help_propensity=0.5)


def _high_skill_profile():
    from simulation.profiles import StudentProfile

    return StudentProfile(skill=0.95, persistence=0.9, strategy=0.9, pace=0.7, help_propensity=0.2)


class TestGenerativePolicy:
    @autotest.num("2033")
    @autotest.external_id("04793759-8892-4b2f-b378-4a5ee74618da")
    @autotest.name("policy: a weak student struggles more often than a strong one")
    async def test_04793759_low_skill_struggles_more_than_high(self):
        with autotest.step("Arrange: weak and strong profiles"):
            from simulation.policy import TrueRegime

            low, high = _low_skill_profile(), _high_skill_profile()

        with autotest.step("Act: run both on the same seed"):
            _, low_regimes = _run(low, seed=1)
            _, high_regimes = _run(high, seed=1)

        with autotest.step("Assert: the share of unproductive regimes is higher for the weak one"):
            low_share = sum(1 for r in low_regimes if r != TrueRegime.PRODUCTIVE) / len(low_regimes)
            high_share = sum(1 for r in high_regimes if r != TrueRegime.PRODUCTIVE) / len(
                high_regimes
            )
            assert_true(low_share > high_share, "weak student struggles more than strong")

    @autotest.num("2034")
    @autotest.external_id("412b5a3e-1ba8-42d3-b49d-086dd3301ca0")
    @autotest.name("policy: a strong student reaches submission (SUBMIT)")
    async def test_412b5a3e_high_skill_reaches_submit(self):
        with autotest.step("Arrange: strong profile"):
            from simulation.policy import Action

            profile = _high_skill_profile()

        with autotest.step("Act: run the trajectory"):
            actions, _ = _run(profile, seed=3)

        with autotest.step("Assert: submission appears in the trajectory"):
            assert_true(Action.SUBMIT in actions, "SUBMIT reached")

    @autotest.num("2035")
    @autotest.external_id("34544677-9d54-4d64-86c2-964692f72e06")
    @autotest.name("policy: trajectory is deterministic by seed (run is reproducible)")
    async def test_34544677_deterministic_by_rng_seed(self):
        with autotest.step("Arrange: one profile and one seed"):
            from simulation.profiles import sample_profile

            profile = sample_profile(9)

        with autotest.step("Act: run twice"):
            actions_1, regimes_1 = _run(profile, seed=5)
            actions_2, regimes_2 = _run(profile, seed=5)

        with autotest.step("Assert: actions and regimes match"):
            assert_equal(actions_1, actions_2, "actions")
            assert_equal(regimes_1, regimes_2, "regimes")

    @autotest.num("2036")
    @autotest.external_id("e68a9ba1-4ad1-46b2-9415-f4462170de34")
    @autotest.name("policy: the true regime is a latent mode, regimes are diverse")
    async def test_e68a9ba1_regime_is_latent_mode_diverse(self):
        with autotest.step("Arrange: weak profile (regimes should switch)"):
            from simulation.policy import TrueRegime

            profile = _low_skill_profile()

        with autotest.step("Act: run the trajectory"):
            _, regimes = _run(profile, seed=2)

        with autotest.step("Assert: regime isn't constant, productive and others appear"):
            kinds = set(regimes)
            assert_true(TrueRegime.PRODUCTIVE in kinds, "productive regime appears")
            assert_true(len(kinds) >= 2, "weak student shows diverse regimes")
