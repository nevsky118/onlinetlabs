"""De-circularizing derive_thresholds: counterfactual is pluggable, ablation measured vs stipulated."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from analytics.criterion import Costs
from analytics.thresholds import derive_T_k, no_effect_counterfactual

pytestmark = [pytest.mark.unit]


def _stuck_session(length: int = 300, step: int = 15) -> dict:
    """One long stuck spell, then productive."""
    samples = []
    value, dwell = 0, 0.0
    while value <= length:
        samples.append({"ts": float(value), "regime": "stuck_on_step", "dwell": dwell})
        value += step
        dwell += float(step)
    samples.append({"ts": float(value), "regime": "productive", "dwell": 0.0})
    return {"samples": samples, "interventions": []}


class TestCounterfactualAblation:
    @autotest.num("1984")
    @autotest.external_id("8af2a47a-dd73-4a49-90cf-94d161c70f5d")
    @autotest.name("Ablation: no-effect counterfactual shifts the T_k optimum to «don't intervene»")
    def test_8af2a47a_no_effect_shifts_optimum(self):
        with autotest.step("Arrange: long stuck spells, c_stuck dominates"):
            sessions = [_stuck_session(300), _stuck_session(300), _stuck_session(180)]
            costs = Costs(c_stuck=1.0, c_intervention=1.0, c_false=2.0)
            grid = {"stuck_on_step": [0.0, 30.0, 60.0, 120.0, 300.0]}

        with autotest.step(
            "Act: derive_T_k under stipulated (default) and no-effect counterfactual"
        ):
            tk_stipulated = derive_T_k(sessions, costs, grid)
            tk_no_effect = derive_T_k(
                sessions, costs, grid, counterfactual=no_effect_counterfactual
            )

        with autotest.step(
            "Assert: with no intervention effect optimum = max T_k, with stipulation it's earlier"
        ):
            assert_equal(
                tk_no_effect["stuck_on_step"],
                300.0,
                f"no-effect → max T_k (don't intervene); got {tk_no_effect}",
            )
            assert_true(
                tk_stipulated["stuck_on_step"] < 300.0,
                f"stipulated → intervention pays off, T_k earlier; got {tk_stipulated}",
            )

    @autotest.num("1985")
    @autotest.external_id("8f458642-4360-4a33-941b-0d0ef1063f4c")
    @autotest.name("Backward-compat: default counterfactual == stipulated (truncation)")
    def test_8f458642_default_is_stipulated(self):
        with autotest.step("Arrange: sessions + grid"):
            from analytics.thresholds import _truncate_at_interventions

            sessions = [_stuck_session(300), _stuck_session(120)]
            costs = Costs(c_stuck=1.0, c_intervention=1.0, c_false=2.0)
            grid = {"stuck_on_step": [0.0, 30.0, 60.0, 120.0, 300.0]}

        with autotest.step("Act: default vs explicit truncation-counterfactual"):
            tk_default = derive_T_k(sessions, costs, grid)
            tk_explicit = derive_T_k(
                sessions, costs, grid, counterfactual=_truncate_at_interventions
            )

        with autotest.step("Assert: match (backward compatibility)"):
            assert_equal(tk_default, tk_explicit, "default == stipulated truncation")
