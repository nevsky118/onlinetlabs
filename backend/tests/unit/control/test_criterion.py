import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from control.criterion import Costs, compute_J

pytestmark = [pytest.mark.unit]


class TestCriterion:
    @autotest.num("1422")
    @autotest.external_id("85394eae-b37b-49b3-8ad0-f3f25f784950")
    @autotest.name("compute_J: суммирует bad_duration и интервенции корректно")
    def test_85394eae_J_sums_duration_and_interventions(self):
        with autotest.step("Arrange: два сэмпла stuck_on_step, одна интервенция"):
            samples = [
                {"ts": 0, "regime": "stuck_on_step", "dwell": 0},
                {"ts": 30, "regime": "stuck_on_step", "dwell": 30},
                {"ts": 60, "regime": "productive", "dwell": 0},
            ]
            interventions = [{"ts": 45}]
            costs = Costs(c_stuck=1.0, c_intervention=2.0, c_false=0.5)

        with autotest.step("Act: compute_J"):
            res = compute_J(samples, interventions, costs)

        with autotest.step("Assert: bad_duration=60, n_interventions=1, n_false=0, J=62"):
            assert_equal(res.bad_duration, 60.0, "bad_duration == 60")
            assert_equal(res.n_interventions, 1, "n_interventions == 1")
            assert_equal(res.n_false, 0, "n_false == 0 (нет clean-выходов)")
            assert_equal(res.J, 60.0 * 1.0 + 1 * 2.0 + 0 * 0.5, "J == 62.0")

    @autotest.num("1423")
    @autotest.external_id("0c443323-2e38-477c-9aa4-53c2a5c15713")
    @autotest.name("compute_J: без интервенций J=0, n_false=0")
    def test_0c443323_no_interventions_zero_false(self):
        with autotest.step("Arrange: один продуктивный сэмпл, пустые интервенции"):
            samples = [{"ts": 0, "regime": "productive", "dwell": 0}]

        with autotest.step("Act: compute_J"):
            res = compute_J(samples, [], Costs(1.0, 1.0, 1.0))

        with autotest.step("Assert: J==0, n_interventions==0, n_false==0"):
            assert_equal(res.J, 0.0, "J == 0")
            assert_equal(res.n_interventions, 0, "n_interventions == 0")
            assert_equal(res.n_false, 0, "n_false == 0")

    @autotest.num("1424")
    @autotest.external_id("00208a1c-033f-47c9-9087-60a60de6b614")
    @autotest.name(
        "compute_J: ложное вмешательство засчитывается при преждевременном выходе из спелла"
    )
    def test_00208a1c_count_false_flags_premature_intervention(self):
        def _spell(start: int, duration: int, with_iv: bool) -> list[dict]:
            """Возвращает сэмплы одного спелла [start, start+duration]."""
            result = []
            t = start
            while t < start + duration:
                result.append({"ts": t, "regime": "stuck_on_step", "dwell": float(t - start)})
                t += 10
            result.append({"ts": t, "regime": "productive", "dwell": 0.0})
            return result

        with autotest.step("Arrange: три clean-спелла по 60с, один с интервенцией за 20с"):
            samples = (
                _spell(0, 60, with_iv=False)
                + _spell(70, 60, with_iv=False)
                + _spell(140, 60, with_iv=False)
                + _spell(210, 20, with_iv=True)
            )
            interventions = [{"ts": 215}]
            costs = Costs(c_stuck=1.0, c_intervention=1.0, c_false=10.0)

        with autotest.step("Act: compute_J"):
            res = compute_J(samples, interventions, costs)

        with autotest.step("Assert: n_false==1, J > bad_duration + n_interventions*c_int"):
            assert_equal(res.n_false, 1, f"ожидалось 1 ложное, получено {res.n_false}")
            assert_true(
                res.bad_duration + res.n_interventions * costs.c_intervention < res.J,
                "штраф за ложную интервенцию вошёл в J",
            )
