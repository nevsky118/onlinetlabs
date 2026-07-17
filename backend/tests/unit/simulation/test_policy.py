"""GenerativePolicy: латентный режим ПРАВИТ действиями (а не выводится из порогов детектора).

Так истинный режим порождён независимо от признаков, которыми детектор пользуется →
observer-ROC остаётся честной, а не тавтологичной.
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
    return StudentProfile(
        skill=0.1, persistence=0.2, strategy=0.15, pace=0.5, help_propensity=0.5
    )


def _high_skill_profile():
    from simulation.profiles import StudentProfile
    return StudentProfile(
        skill=0.95, persistence=0.9, strategy=0.9, pace=0.7, help_propensity=0.2
    )


class TestGenerativePolicy:
    @autotest.num("2033")
    @autotest.external_id("04793759-8892-4b2f-b378-4a5ee74618da")
    @autotest.name("policy: слабый студент буксует чаще сильного")
    async def test_04793759_low_skill_struggles_more_than_high(self):
        with autotest.step("Arrange: слабый и сильный профили"):
            from simulation.policy import TrueRegime
            low, high = _low_skill_profile(), _high_skill_profile()

        with autotest.step("Act: прогоняем обоих на одном seed"):
            _, low_regimes = _run(low, seed=1)
            _, high_regimes = _run(high, seed=1)

        with autotest.step("Assert: доля непродуктивных режимов выше у слабого"):
            low_share = sum(
                1 for r in low_regimes if r != TrueRegime.PRODUCTIVE
            ) / len(low_regimes)
            high_share = sum(
                1 for r in high_regimes if r != TrueRegime.PRODUCTIVE
            ) / len(high_regimes)
            assert_true(low_share > high_share, "слабый буксует чаще сильного")

    @autotest.num("2034")
    @autotest.external_id("412b5a3e-1ba8-42d3-b49d-086dd3301ca0")
    @autotest.name("policy: сильный студент доходит до сдачи (SUBMIT)")
    async def test_412b5a3e_high_skill_reaches_submit(self):
        with autotest.step("Arrange: сильный профиль"):
            from simulation.policy import Action
            profile = _high_skill_profile()

        with autotest.step("Act: прогоняем траекторию"):
            actions, _ = _run(profile, seed=3)

        with autotest.step("Assert: в траектории есть сдача"):
            assert_true(Action.SUBMIT in actions, "SUBMIT достигнут")

    @autotest.num("2035")
    @autotest.external_id("34544677-9d54-4d64-86c2-964692f72e06")
    @autotest.name("policy: траектория детерминирована seed'ом (прогон воспроизводим)")
    async def test_34544677_deterministic_by_rng_seed(self):
        with autotest.step("Arrange: один профиль и один seed"):
            from simulation.profiles import sample_profile
            profile = sample_profile(9)

        with autotest.step("Act: прогоняем дважды"):
            actions_1, regimes_1 = _run(profile, seed=5)
            actions_2, regimes_2 = _run(profile, seed=5)

        with autotest.step("Assert: действия и режимы совпали"):
            assert_equal(actions_1, actions_2, "действия")
            assert_equal(regimes_1, regimes_2, "режимы")

    @autotest.num("2036")
    @autotest.external_id("e68a9ba1-4ad1-46b2-9415-f4462170de34")
    @autotest.name("policy: истинный режим — латентный mode, режимы разнообразны")
    async def test_e68a9ba1_regime_is_latent_mode_diverse(self):
        with autotest.step("Arrange: слабый профиль (режимы должны переключаться)"):
            from simulation.policy import TrueRegime
            profile = _low_skill_profile()

        with autotest.step("Act: прогоняем траекторию"):
            _, regimes = _run(profile, seed=2)

        with autotest.step("Assert: режим не константа — есть продуктивный и другие"):
            kinds = set(regimes)
            assert_true(TrueRegime.PRODUCTIVE in kinds, "продуктивный режим встречается")
            assert_true(len(kinds) >= 2, "у слабого студента режимы разнообразны")
