"""Де-циркуляризация derive_thresholds: counterfactual пλагинный, ablation measured vs stipulated."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from control.criterion import Costs
from control.derive_thresholds import derive_T_k, no_effect_counterfactual

pytestmark = [pytest.mark.unit]


def _stuck_session(length: int = 300, step: int = 15) -> dict:
    """Один длинный stuck-спелл, затем продуктивный."""
    samples = []
    t, dwell = 0, 0.0
    while t <= length:
        samples.append({"ts": float(t), "regime": "stuck_on_step", "dwell": dwell})
        t += step
        dwell += float(step)
    samples.append({"ts": float(t), "regime": "productive", "dwell": 0.0})
    return {"samples": samples, "interventions": []}


class TestCounterfactualAblation:
    @autotest.num("1984")
    @autotest.external_id("8af2a47a-dd73-4a49-90cf-94d161c70f5d")
    @autotest.name("Ablation: no-effect counterfactual сдвигает оптимум T_k к «не вмешиваться»")
    def test_8af2a47a_no_effect_shifts_optimum(self):
        with autotest.step("Arrange: длинные stuck-спеллы, c_stuck доминирует"):
            sessions = [_stuck_session(300), _stuck_session(300), _stuck_session(180)]
            costs = Costs(c_stuck=1.0, c_intervention=1.0, c_false=2.0)
            grid = {"stuck_on_step": [0.0, 30.0, 60.0, 120.0, 300.0]}

        with autotest.step("Act: derive_T_k при stipulated (default) и no-effect counterfactual"):
            tk_stipulated = derive_T_k(sessions, costs, grid)
            tk_no_effect = derive_T_k(
                sessions, costs, grid, counterfactual=no_effect_counterfactual
            )

        with autotest.step("Assert: без эффекта вмешательства оптимум = max T_k; со стипуляцией — раньше"):
            assert_equal(
                tk_no_effect["stuck_on_step"], 300.0,
                f"no-effect → максимальный T_k (не вмешиваться); получено {tk_no_effect}",
            )
            assert_true(
                tk_stipulated["stuck_on_step"] < 300.0,
                f"stipulated → интервенция окупается, T_k раньше; получено {tk_stipulated}",
            )

    @autotest.num("1985")
    @autotest.external_id("8f458642-4360-4a33-941b-0d0ef1063f4c")
    @autotest.name("Backward-compat: default counterfactual == stipulated (truncation)")
    def test_8f458642_default_is_stipulated(self):
        with autotest.step("Arrange: сессии + сетка"):
            from control.derive_thresholds import _truncate_at_interventions
            sessions = [_stuck_session(300), _stuck_session(120)]
            costs = Costs(c_stuck=1.0, c_intervention=1.0, c_false=2.0)
            grid = {"stuck_on_step": [0.0, 30.0, 60.0, 120.0, 300.0]}

        with autotest.step("Act: default vs явный truncation-counterfactual"):
            tk_default = derive_T_k(sessions, costs, grid)
            tk_explicit = derive_T_k(
                sessions, costs, grid, counterfactual=_truncate_at_interventions
            )

        with autotest.step("Assert: совпадают (обратная совместимость)"):
            assert_equal(tk_default, tk_explicit, "default == stipulated truncation")
